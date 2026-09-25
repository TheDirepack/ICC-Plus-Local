from __future__ import annotations

import copy
import hashlib
import json
import math
import random
from functools import cmp_to_key
from dataclasses import asdict, dataclass, field
from typing import Any

from .expressions import evaluate as eval_expr
from .model import Entity, ProjectIndex
from .requirements import RequirementEngine, RequirementTrace
from .js_compat import parse_int
from .version import __version__
from .build_string import NativeBuildEntry, parse_build_string, serialize_build_entries
from .creator_helpers import browser_text_content


@dataclass(slots=True)
class Event:
    action: str
    choice_id: str
    ok: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChoiceStatus:
    id: str
    selectable: bool
    active: bool
    count: int
    reasons: list[str]
    requirements: list[dict[str, Any]]
    point_preview: dict[str, float]
    would_deselect: list[str]
    unsupported_effects: list[str]
    visible: bool = True
    semantic_errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STATE_FORMAT = "iccplus-cyoa-runtime-state"
STATE_FORMAT_VERSION = 1


def project_fingerprint(project: dict[str, Any]) -> str:
    payload = json.dumps(project, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _rng_to_json(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_rng_to_json(x) for x in value]
    return value


def _rng_from_json(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_rng_from_json(x) for x in value)
    return value


@dataclass(slots=True)
class RuntimeState:
    activations: dict[str, int]
    points: dict[str, float]
    variables: dict[str, bool]
    words: dict[str, str]
    row_counts: dict[str, int]
    selected_order: list[str] = field(default_factory=list)
    # ICC Plus getSelectedObjectId() iterates activatedMap insertion order. This
    # includes Choices, Variables, and Row-button Point records. Keep that order
    # separately from selected_order, which contains only selectable entities.
    build_order: list[str] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    forced_by: dict[str, set[str]] = field(default_factory=dict)
    activated_by: dict[str, set[str]] = field(default_factory=dict)
    score_ledger: dict[str, list[dict[str, float]]] = field(default_factory=dict)
    # Per-selection random Score values use the upstream Score-array index as the key.
    # ICC Plus stores these in its native Build Form string as /RS#index:value.
    random_score_ledger: dict[str, list[dict[int, float]]] = field(default_factory=dict)
    # Per-selection random forced-activation results. Tokens use ICC Plus's normal
    # ID or ID/ON#N form; export converts /ON# to /RON# inside /RND# payloads.
    random_activation_ledger: dict[str, list[list[str]]] = field(default_factory=dict)
    # Build Form payloads that are player-entered rather than derivable from project data.
    custom_words: dict[str, str] = field(default_factory=dict)
    uploaded_images: dict[str, str] = field(default_factory=dict)
    # Row-button random point results imported from a native Build Form string.
    row_button_random_points: dict[str, tuple[str, int]] = field(default_factory=dict)
    allowed_deltas: dict[str, int] = field(default_factory=dict)
    point_effect_ledger: dict[str, list[dict[str, tuple[float, float]]]] = field(default_factory=dict)
    hidden_content: dict[str, set[str]] = field(default_factory=dict)
    show_all_addons: int = 0

    def clone(self) -> 'RuntimeState':
        return copy.deepcopy(self)


class Simulator:
    """Deterministic headless ICC Plus selection simulator.

    It follows the viewer's requirement checks, point affordability rule,
    row selection caps, variable effects, score costs, direct forced
    activation/deactivation, and requirement-driven cleanup. Browser-only
    presentation effects are reported but intentionally ignored.
    """

    ADVANCED = {
        'discountOther', 'changeTemplates', 'changeWidth',
        'setBgmIsOn', 'isFadeTransition', 'customTextfieldIsOn', 'confirmIsOn',
        'changePointBar', 'changeBackground', 'scrollToRow', 'scrollToObject', 'isImageUpload',
    }

    def __init__(self, project: dict[str, Any], *, seed: int = 0, clean: bool = True):
        self._base_project = copy.deepcopy(project)
        self._base_project_fingerprint = project_fingerprint(self._base_project)
        self._dynamic_rows: list[dict[str, Any]] = []
        self.project = copy.deepcopy(self._base_project)
        self.index = ProjectIndex(self.project)
        self.req = RequirementEngine(self.index)
        self.rng = random.Random(seed)
        self.seed = seed
        # Temporary native-build restore overrides. They are consumed only while
        # one entry is being replayed and are never serialized as runtime state.
        self._score_value_overrides: dict[str, dict[int, float]] = {}
        self._random_activation_overrides: dict[str, list[str]] = {}
        points = {x.id: float(x.value.get('startingSum', 0) or 0) for x in self.index.by_kind.get('point', [])}
        variables = {x.id: x.value.get('isTrue') is True for x in self.index.by_kind.get('variable', [])}
        words = {x.id: str(x.value.get('replaceText', '')) for x in self.index.by_kind.get('word', [])}
        activations = {k: 0 for k, v in variables.items() if v}
        row_counts = {x.id: 0 for x in self.index.by_kind.get('row', []) + self.index.by_kind.get('backpack_row', [])}
        self.state = RuntimeState(activations, points, variables, words, row_counts)
        self.state.build_order = list(activations)
        if clean:
            self._activate_defaults()
        else:
            self._import_runtime_flags()

    def _import_runtime_flags(self) -> None:
        for ent in self.index.selectables():
            if ent.value.get('isActive'):
                n = int(ent.value.get('multipleUseVariable', 0) or 0)
                self.state.activations[ent.id] = n
                self.state.selected_order.append(ent.id)
                self._build_order_add(ent.id)
                if self._counts_for_row(ent):
                    self.state.row_counts[ent.row_id or ''] = self.state.row_counts.get(ent.row_id or '', 0) + 1

    def _activate_defaults(self) -> None:
        """Activate Viewer-style ``isAutoActive`` defaults in a clean game state.

        The Viewer queues these after reset and retries them as other defaults make
        requirements available. Successful defaults are forced active. Initial
        activation events are runtime setup, so they are not kept in player event
        history.
        """
        pending = [ent.id for ent in self.index.selectables() if ent.value.get('isAutoActive')]
        made_progress = True
        while pending and made_progress:
            made_progress = False
            remaining: list[str] = []
            for ident in pending:
                event = self.select(ident, force=True, source='__auto__', _internal=True)
                if event.ok and self._active(ident):
                    self.state.forced_by.setdefault(ident, set()).add('__auto__')
                    made_progress = True
                else:
                    remaining.append(ident)
            pending = remaining
        self.state.events.clear()

    def reset(self) -> None:
        # Viewer cleanActivated() resets Point Types to initValue, queues
        # isAutoActive entries, then replays active notDeselectedByClean items.
        preserved: list[tuple[str, int]] = []
        for ident in list(self.state.selected_order):
            ent = self._entity(ident)
            if ent and self._active(ident) and ent.value.get('notDeselectedByClean'):
                preserved.append((ident, self._count(ident)))

        fresh = Simulator(self.project, seed=self.seed, clean=False)
        fresh.state.points = {
            x.id: float(x.value.get('initValue', x.value.get('startingSum', 0)) or 0)
            for x in fresh.index.by_kind.get('point', [])
        }
        # cleanActivated clears runtime activity before defaults are queued.
        fresh.state.activations = {k: 0 for k, v in fresh.state.variables.items() if v}
        fresh.state.selected_order.clear()
        fresh.state.row_counts = {k: 0 for k in fresh.state.row_counts}
        fresh._activate_defaults()
        for ident, count in preserved:
            ent = fresh._entity(ident)
            if ent and fresh._multiple_mode(ent) is None:
                fresh.select(ident, force=True, source='__clean_preserve__', _internal=True)
            elif count > 0:
                fresh.select(ident, times=count, force=True, source='__clean_preserve__', _internal=True)
            elif count < 0:
                for _ in range(abs(count)):
                    fresh.deselect(ident, reason='clean preserve', _internal=True)
        fresh.state.events.clear()
        self.state = fresh.state
        self.rng.setstate(fresh.rng.getstate())

    def export_build_string(self) -> str:
        """Return ICC Plus 2.10.6's native Build Form string for this state."""
        entries: list[NativeBuildEntry] = []
        selectable_ids = {x.id for x in self.index.selectables()}
        variable_ids = {x.id for x in self.index.by_kind.get('variable', [])}
        ordered = list(self.state.build_order)
        expected = list(self.state.activations) + list(self.state.row_button_random_points)
        for ident in expected:
            if ident not in ordered:
                ordered.append(ident)
        for ident in ordered:
            if ident in self.state.row_button_random_points:
                point_id, amount = self.state.row_button_random_points[ident]
                entries.append(NativeBuildEntry(
                    raw='', id=ident, row_button_point=point_id, row_button_value=int(amount),
                ))
                continue
            count = int(self.state.activations.get(ident, 0))
            if ident in variable_ids:
                if self.state.variables.get(ident, False):
                    entries.append(NativeBuildEntry(raw='', id=ident))
                continue
            if ident not in selectable_ids or not self._active(ident):
                continue
            ent = self._entity(ident)
            if not ent:
                continue
            random_scores: dict[int, float] = {}
            score_history = self.state.random_score_ledger.get(ident, [])
            if score_history:
                random_scores = dict(score_history[-1])
            random_activations: list[str] = []
            random_history = self.state.random_activation_ledger.get(ident, [])
            if random_history:
                if count == 0:
                    random_activations = list(random_history[-1])
                else:
                    random_activations = [token for step in random_history for token in step]
            word = self.state.custom_words.get(ident)
            image = self.state.uploaded_images.get(ident)
            entries.append(NativeBuildEntry(
                raw='', id=ident, count=count, random_scores=random_scores,
                random_activations=random_activations, word=word, image=image,
            ))
        return serialize_build_entries(entries)

    def load_build_string(self, value: str) -> None:
        """Load an ICC Plus 2.10.6 Build Form string into the local runtime.

        The replay uses the native random Score and random-activation payloads as
        deterministic overrides. This makes a browser-produced build reproducible
        even though the local runner uses a seeded RNG and the browser uses
        ``Math.random()``.
        """
        entries = parse_build_string(value)
        self.reset()
        self.state.events.clear()
        # Install every random override before replay. A source choice can force a
        # later entry active before that entry is reached in the comma list.
        self._score_value_overrides = {
            entry.id: dict(entry.random_scores) for entry in entries if entry.random_scores
        }
        self._random_activation_overrides = {
            entry.id: list(entry.random_activations) for entry in entries if entry.random_activations
        }
        try:
            for entry in entries:
                if entry.is_row_button:
                    point_id = entry.row_button_point or ''
                    amount = int(entry.row_button_value or 0)
                    if point_id in self.state.points:
                        self.state.points[point_id] += amount
                    self.state.row_button_random_points[entry.id] = (point_id, amount)
                    self._build_order_add(entry.id)
                    continue
                variable = self.index.one(entry.id, 'variable')
                if variable:
                    self.state.variables[entry.id] = True
                    self.state.activations[entry.id] = 0
                    self._build_order_add(entry.id)
                    continue
                ent = self._entity(entry.id)
                if not ent:
                    continue
                mode = self._multiple_mode(ent)
                if mode == 'variable':
                    desired = int(entry.count)
                    guard = 0
                    while self._count(entry.id) < desired and guard < 10000:
                        before = self._count(entry.id)
                        self.select(entry.id, force=True, source='__build_load__', _internal=True)
                        guard += 1
                        if self._count(entry.id) == before:
                            break
                    while self._count(entry.id) > desired and guard < 20000:
                        before = self._count(entry.id)
                        self.deselect(entry.id, reason='native build load', force_cleanup=True, _internal=True)
                        guard += 1
                        if self._count(entry.id) == before:
                            break
                elif not self._active(entry.id):
                    self.select(entry.id, force=True, source='__build_load__', _internal=True)

                if entry.word is not None:
                    self.state.custom_words[entry.id] = entry.word
                    word_id = ent.value.get('idOfTheTextfieldWord')
                    if isinstance(word_id, str) and word_id in self.state.words:
                        self.state.words[word_id] = entry.word
                if entry.image is not None:
                    self.state.uploaded_images[entry.id] = entry.image
        finally:
            self._score_value_overrides = {}
            self._random_activation_overrides = {}
        self.state.events.clear()

    def export_state(self, *, include_events: bool = False) -> dict[str, Any]:
        """Return a portable JSON-safe runtime state for exact continuation."""
        issues = self.runtime_state_issues()
        if issues:
            raise ValueError('runtime state is internally inconsistent: ' + '; '.join(issues))
        runtime: dict[str, Any] = {
            'activations': dict(self.state.activations),
            'points': {k: _clean_num(v) for k, v in self.state.points.items()},
            'variables': dict(self.state.variables),
            'words': dict(self.state.words),
            'row_counts': dict(self.state.row_counts),
            'selected_order': list(self.state.selected_order),
            'build_order': list(self.state.build_order),
            'forced_by': {k: sorted(v) for k, v in self.state.forced_by.items()},
            'activated_by': {k: sorted(v) for k, v in self.state.activated_by.items()},
            'score_ledger': copy.deepcopy(self.state.score_ledger),
            'random_score_ledger': {
                owner: [{str(index): value for index, value in entry.items()} for entry in entries]
                for owner, entries in self.state.random_score_ledger.items()
            },
            'random_activation_ledger': copy.deepcopy(self.state.random_activation_ledger),
            'custom_words': dict(self.state.custom_words),
            'uploaded_images': dict(self.state.uploaded_images),
            'row_button_random_points': {
                row_id: [point_id, int(value)]
                for row_id, (point_id, value) in self.state.row_button_random_points.items()
            },
            'allowed_deltas': dict(self.state.allowed_deltas),
            'hidden_content': {k: sorted(v) for k, v in self.state.hidden_content.items()},
            'show_all_addons': int(self.state.show_all_addons),
            'dynamic_rows': copy.deepcopy(self._dynamic_rows),
            'point_effect_ledger': {
                owner: [
                    {pid: [before, after] for pid, (before, after) in entry.items()}
                    for entry in entries
                ]
                for owner, entries in self.state.point_effect_ledger.items()
            },
        }
        if include_events:
            runtime['events'] = [event.to_dict() for event in self.state.events]
        return {
            'format': STATE_FORMAT,
            'format_version': STATE_FORMAT_VERSION,
            'tool_version': __version__,
            'project_fingerprint': self._base_project_fingerprint,
            'project_version': self.project.get('version'),
            'seed': self.seed,
            'rng_state': _rng_to_json(self.rng.getstate()),
            'runtime': runtime,
        }

    def runtime_state_issues(self, state: RuntimeState | None = None) -> list[str]:
        """Return structural inconsistencies that cannot be produced by a healthy run.

        This does not try to prove gameplay correctness. It checks the portable
        continuation bookkeeping so corrupted or hand-edited state files fail at
        the load boundary instead of causing delayed, hard-to-explain behavior.
        """
        value = state or self.state
        issues: list[str] = []

        selectables = {x.id: x for x in self.index.selectables()}
        selectable_ids = set(selectables)
        variable_ids = {x.id for x in self.index.by_kind.get('variable', [])}
        point_ids = {x.id for x in self.index.by_kind.get('point', [])}
        word_ids = {x.id for x in self.index.by_kind.get('word', [])}
        row_ids = {x.id for x in self.index.by_kind.get('row', []) + self.index.by_kind.get('backpack_row', [])}

        if set(value.points) != point_ids:
            missing = sorted(point_ids - set(value.points))
            extra = sorted(set(value.points) - point_ids)
            issues.append(f'point map does not match project (missing={missing}, extra={extra})')
        if set(value.variables) != variable_ids:
            missing = sorted(variable_ids - set(value.variables))
            extra = sorted(set(value.variables) - variable_ids)
            issues.append(f'variable map does not match project (missing={missing}, extra={extra})')
        if set(value.words) != word_ids:
            missing = sorted(word_ids - set(value.words))
            extra = sorted(set(value.words) - word_ids)
            issues.append(f'word map does not match project (missing={missing}, extra={extra})')
        if set(value.row_counts) != row_ids:
            missing = sorted(row_ids - set(value.row_counts))
            extra = sorted(set(value.row_counts) - row_ids)
            issues.append(f'row-count map does not match project (missing={missing}, extra={extra})')

        unknown_active = sorted(set(value.activations) - selectable_ids - variable_ids)
        if unknown_active:
            issues.append(f'activations contain unknown IDs: {unknown_active}')

        if len(value.selected_order) != len(set(value.selected_order)):
            issues.append('selected_order contains duplicate IDs')
        unknown_selected = sorted(set(value.selected_order) - selectable_ids)
        if unknown_selected:
            issues.append(f'selected_order contains unknown selectable IDs: {unknown_selected}')

        active_selectables = set(value.activations) & selectable_ids
        if set(value.selected_order) != active_selectables:
            missing = sorted(active_selectables - set(value.selected_order))
            extra = sorted(set(value.selected_order) - active_selectables)
            issues.append(f'selected_order does not match active selectables (missing={missing}, extra={extra})')

        expected_build = active_selectables | {ident for ident, enabled in value.variables.items() if enabled} | set(value.row_button_random_points)
        if len(value.build_order) != len(set(value.build_order)):
            issues.append('build_order contains duplicate IDs')
        if set(value.build_order) != expected_build:
            missing = sorted(expected_build - set(value.build_order))
            extra = sorted(set(value.build_order) - expected_build)
            issues.append(f'build_order does not match native activated entries (missing={missing}, extra={extra})')

        expected_rows = {rid: 0 for rid in row_ids}
        for ident in active_selectables:
            ent = selectables[ident]
            if self._counts_for_row(ent):
                expected_rows[ent.row_id or ''] = expected_rows.get(ent.row_id or '', 0) + 1
        if value.row_counts != expected_rows:
            issues.append(f'row_counts do not match active row-counted selections (expected={expected_rows}, actual={value.row_counts})')

        for ident, enabled in value.variables.items():
            if (ident in value.activations) != bool(enabled):
                issues.append(f'variable {ident!r} activation does not match its boolean value')

        for target, providers in value.forced_by.items():
            if target not in selectable_ids:
                issues.append(f'forced_by contains unknown target {target!r}')
            unknown = sorted(x for x in providers if x != '__auto__' and x not in selectable_ids)
            if unknown:
                issues.append(f'forced_by target {target!r} has unknown providers: {unknown}')

        for target, providers in value.activated_by.items():
            if target not in selectable_ids:
                issues.append(f'activated_by contains unknown target {target!r}')
            unknown = sorted(x for x in providers if x not in selectable_ids)
            if unknown:
                issues.append(f'activated_by target {target!r} has unknown providers: {unknown}')

        for owner, entries in value.score_ledger.items():
            if owner not in selectable_ids:
                issues.append(f'score_ledger contains unknown owner {owner!r}')
            for entry in entries:
                unknown = sorted(set(entry) - point_ids)
                if unknown:
                    issues.append(f'score_ledger owner {owner!r} references unknown Point IDs: {unknown}')

        for owner, entries in value.random_score_ledger.items():
            ent = selectables.get(owner)
            if ent is None:
                issues.append(f'random_score_ledger contains unknown owner {owner!r}')
                continue
            scores = ent.value.get('scores', []) if isinstance(ent.value, dict) else []
            if owner in value.score_ledger and len(entries) != len(value.score_ledger[owner]):
                issues.append(
                    f'random_score_ledger owner {owner!r} has {len(entries)} entries but score_ledger has {len(value.score_ledger[owner])}'
                )
            for entry_index, entry in enumerate(entries):
                for score_index in entry:
                    if score_index < 0 or score_index >= len(scores):
                        issues.append(
                            f'random_score_ledger owner {owner!r} entry {entry_index} references invalid Score index {score_index}'
                        )
                    elif not bool(scores[score_index].get('isRandom')):
                        issues.append(
                            f'random_score_ledger owner {owner!r} entry {entry_index} references non-random Score index {score_index}'
                        )

        for owner, entries in value.random_activation_ledger.items():
            ent = selectables.get(owner)
            if ent is None:
                issues.append(f'random_activation_ledger contains unknown owner {owner!r}')
                continue
            if not bool(ent.value.get('isActivateRandom')):
                issues.append(f'random_activation_ledger owner {owner!r} is not a random-activation source')
            for entry_index, entry in enumerate(entries):
                for token in entry:
                    target = token.split('/ON#', 1)[0]
                    if target not in selectable_ids:
                        issues.append(
                            f'random_activation_ledger owner {owner!r} entry {entry_index} references unknown target {target!r}'
                        )

        for owner in value.custom_words:
            if owner not in selectable_ids:
                issues.append(f'custom_words contains unknown owner {owner!r}')
        for owner in value.uploaded_images:
            if owner not in selectable_ids:
                issues.append(f'uploaded_images contains unknown owner {owner!r}')
        for row_id, (point_id, _) in value.row_button_random_points.items():
            if row_id not in row_ids:
                issues.append(f'row_button_random_points contains unknown Row {row_id!r}')
            if point_id not in point_ids:
                issues.append(f'row_button_random_points row {row_id!r} references unknown Point ID {point_id!r}')

        for owner, entries in value.point_effect_ledger.items():
            if owner not in selectable_ids:
                issues.append(f'point_effect_ledger contains unknown owner {owner!r}')
            if owner not in active_selectables:
                issues.append(f'point_effect_ledger owner {owner!r} is not active')
            for entry in entries:
                unknown = sorted(set(entry) - point_ids)
                if unknown:
                    issues.append(f'point_effect_ledger owner {owner!r} references unknown Point IDs: {unknown}')

        unknown_hidden = sorted(set(value.hidden_content) - row_ids)
        if unknown_hidden:
            issues.append(f'hidden_content contains unknown row IDs: {unknown_hidden}')
        if value.show_all_addons < 0:
            issues.append('show_all_addons cannot be negative')
        return issues

    def _project_from_dynamic_rows(self, records: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        if records is None:
            records = []
        if not isinstance(records, list):
            raise ValueError('runtime.dynamic_rows must be an array')
        project = copy.deepcopy(self._base_project)
        accepted: list[dict[str, Any]] = []
        for n, record in enumerate(records):
            if not isinstance(record, dict):
                raise ValueError(f'runtime.dynamic_rows[{n}] must be an object')
            if set(record) != {'collection', 'index', 'row'}:
                raise ValueError(f'runtime.dynamic_rows[{n}] must contain only collection, index, and row')
            collection_key = record.get('collection')
            index = record.get('index')
            row = record.get('row')
            if collection_key not in {'rows', 'backpack'}:
                raise ValueError(f'runtime.dynamic_rows[{n}].collection must be rows or backpack')
            if isinstance(index, bool) or not isinstance(index, int):
                raise ValueError(f'runtime.dynamic_rows[{n}].index must be an integer')
            if not isinstance(row, dict) or not isinstance(row.get('id'), str) or '/D#' not in row['id']:
                raise ValueError(f'runtime.dynamic_rows[{n}].row must be a duplicated ICC Plus Row')
            collection = project.setdefault(collection_key, [])
            if not isinstance(collection, list) or index < 0 or index > len(collection):
                raise ValueError(f'runtime.dynamic_rows[{n}].index is outside the target collection')
            existing_ids = {
                str(item.get('id')) for key in ('rows','backpack')
                for item in project.get(key, []) if isinstance(item, dict) and item.get('id')
            }
            if row['id'] in existing_ids:
                raise ValueError(f'runtime.dynamic_rows[{n}] duplicates existing Row ID {row["id"]!r}')
            clone = copy.deepcopy(row)
            collection.insert(index, clone)
            for i, item in enumerate(collection):
                if isinstance(item, dict):
                    item['index'] = i
            # duplicateRow() adds cloned Choice IDs to ordinary Groups and
            # Choice Design Groups. Reconstruct those reciprocal lists from the
            # stored Row without trusting extra project mutations in the state.
            for choice in clone.get('objects', []) if isinstance(clone.get('objects'), list) else []:
                if not isinstance(choice, dict) or not isinstance(choice.get('id'), str):
                    continue
                for group_id in choice.get('groups', []) if isinstance(choice.get('groups'), list) else []:
                    group = next((g for g in project.get('groups', []) if isinstance(g, dict) and g.get('id') == group_id), None)
                    if group is not None:
                        group.setdefault('elements', [])
                        if choice['id'] not in group['elements']:
                            group['elements'].append(choice['id'])
                for design_id in choice.get('objectDesignGroups', []) if isinstance(choice.get('objectDesignGroups'), list) else []:
                    group = next((g for g in project.get('objectDesignGroups', []) if isinstance(g, dict) and g.get('id') == design_id), None)
                    if group is not None:
                        group.setdefault('elements', [])
                        if choice['id'] not in group['elements']:
                            group['elements'].append(choice['id'])
            accepted.append({'collection': collection_key, 'index': index, 'row': copy.deepcopy(clone)})
        return project, accepted

    def import_state(self, document: dict[str, Any], *, strict_project: bool = True) -> None:
        """Replace the current runtime with a state produced by export_state."""
        if document.get('format') != STATE_FORMAT:
            raise ValueError(f"unsupported runtime state format: {document.get('format')!r}")
        if int(document.get('format_version', -1)) != STATE_FORMAT_VERSION:
            raise ValueError(f"unsupported runtime state version: {document.get('format_version')!r}")
        expected = self._base_project_fingerprint
        actual = str(document.get('project_fingerprint', ''))
        if strict_project and actual != expected:
            raise ValueError(f'runtime state belongs to a different project ({actual or "missing fingerprint"}; expected {expected})')
        runtime = document.get('runtime')
        if not isinstance(runtime, dict):
            raise ValueError('runtime state is missing the runtime object')

        candidate_project, dynamic_rows = self._project_from_dynamic_rows(runtime.get('dynamic_rows', []))
        candidate_index = ProjectIndex(candidate_project)
        candidate_req = RequirementEngine(candidate_index)

        def num_map(name: str) -> dict[str, float]:
            value = runtime.get(name, {})
            if not isinstance(value, dict):
                raise ValueError(f'runtime.{name} must be an object')
            out: dict[str, float] = {}
            for k, v in value.items():
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise ValueError(f'runtime.{name}.{k} must be a finite number')
                number = float(v)
                if not math.isfinite(number):
                    raise ValueError(f'runtime.{name}.{k} must be a finite number')
                out[str(k)] = number
            return out

        def int_map(name: str) -> dict[str, int]:
            value = runtime.get(name, {})
            if not isinstance(value, dict):
                raise ValueError(f'runtime.{name} must be an object')
            out: dict[str, int] = {}
            for k, v in value.items():
                if isinstance(v, bool) or not isinstance(v, int):
                    raise ValueError(f'runtime.{name}.{k} must be an integer')
                out[str(k)] = v
            return out

        variables_raw = runtime.get('variables', {})
        words_raw = runtime.get('words', {})
        if not isinstance(variables_raw, dict) or not isinstance(words_raw, dict):
            raise ValueError('runtime.variables and runtime.words must be objects')
        for key, value in variables_raw.items():
            if not isinstance(value, bool):
                raise ValueError(f'runtime.variables.{key} must be a boolean')
        for key, value in words_raw.items():
            if not isinstance(value, str):
                raise ValueError(f'runtime.words.{key} must be a string')
        selected_order = runtime.get('selected_order', [])
        if not isinstance(selected_order, list):
            raise ValueError('runtime.selected_order must be an array')
        if any(not isinstance(x, str) for x in selected_order):
            raise ValueError('runtime.selected_order must contain only strings')
        build_order_raw = runtime.get('build_order')
        if build_order_raw is not None:
            if not isinstance(build_order_raw, list) or any(not isinstance(x, str) for x in build_order_raw):
                raise ValueError('runtime.build_order must be an array of strings')
            if len(build_order_raw) != len(set(build_order_raw)):
                raise ValueError('runtime.build_order must not contain duplicate IDs')
        forced_raw = runtime.get('forced_by', {})
        activated_raw = runtime.get('activated_by', forced_raw)
        score_ledger_raw = runtime.get('score_ledger', {})
        random_score_raw = runtime.get('random_score_ledger', {})
        random_activation_raw = runtime.get('random_activation_ledger', {})
        custom_words_raw = runtime.get('custom_words', {})
        uploaded_images_raw = runtime.get('uploaded_images', {})
        row_button_raw = runtime.get('row_button_random_points', {})
        point_ledger_raw = runtime.get('point_effect_ledger', {})
        hidden_raw = runtime.get('hidden_content', {})
        if not all(isinstance(x, dict) for x in (forced_raw, activated_raw, score_ledger_raw, random_score_raw, random_activation_raw, custom_words_raw, uploaded_images_raw, row_button_raw, point_ledger_raw, hidden_raw)):
            raise ValueError('runtime ledgers must be objects')

        def string_set_map(name: str, raw: dict[str, Any]) -> dict[str, set[str]]:
            out: dict[str, set[str]] = {}
            for key, values in raw.items():
                if not isinstance(values, list) or any(not isinstance(x, str) for x in values):
                    raise ValueError(f'runtime.{name}.{key} must be an array of strings')
                out[str(key)] = set(values)
            return out

        def score_ledger() -> dict[str, list[dict[str, float]]]:
            out: dict[str, list[dict[str, float]]] = {}
            for owner, entries in score_ledger_raw.items():
                if not isinstance(entries, list):
                    raise ValueError(f'runtime.score_ledger.{owner} must be an array')
                converted: list[dict[str, float]] = []
                for index, entry in enumerate(entries):
                    if not isinstance(entry, dict):
                        raise ValueError(f'runtime.score_ledger.{owner}[{index}] must be an object')
                    one: dict[str, float] = {}
                    for pid, raw_value in entry.items():
                        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)) or not math.isfinite(float(raw_value)):
                            raise ValueError(f'runtime.score_ledger.{owner}[{index}].{pid} must be a finite number')
                        one[str(pid)] = float(raw_value)
                    converted.append(one)
                out[str(owner)] = converted
            return out

        def random_score_ledger() -> dict[str, list[dict[int, float]]]:
            out: dict[str, list[dict[int, float]]] = {}
            for owner, entries in random_score_raw.items():
                if not isinstance(entries, list):
                    raise ValueError(f'runtime.random_score_ledger.{owner} must be an array')
                converted: list[dict[int, float]] = []
                for entry_index, entry in enumerate(entries):
                    if not isinstance(entry, dict):
                        raise ValueError(f'runtime.random_score_ledger.{owner}[{entry_index}] must be an object')
                    one: dict[int, float] = {}
                    for raw_index, raw_value in entry.items():
                        try:
                            score_index = int(raw_index)
                        except (TypeError, ValueError) as exc:
                            raise ValueError(f'runtime.random_score_ledger.{owner}[{entry_index}] has a non-integer score index') from exc
                        if score_index < 0 or isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)) or not math.isfinite(float(raw_value)):
                            raise ValueError(f'runtime.random_score_ledger.{owner}[{entry_index}].{raw_index} must be a finite number')
                        one[score_index] = float(raw_value)
                    converted.append(one)
                out[str(owner)] = converted
            return out

        def random_activation_ledger() -> dict[str, list[list[str]]]:
            out: dict[str, list[list[str]]] = {}
            for owner, entries in random_activation_raw.items():
                if not isinstance(entries, list):
                    raise ValueError(f'runtime.random_activation_ledger.{owner} must be an array')
                converted: list[list[str]] = []
                for entry_index, entry in enumerate(entries):
                    if not isinstance(entry, list) or any(not isinstance(x, str) for x in entry):
                        raise ValueError(f'runtime.random_activation_ledger.{owner}[{entry_index}] must be an array of strings')
                    converted.append(list(entry))
                out[str(owner)] = converted
            return out

        def string_map(name: str, raw: dict[str, Any]) -> dict[str, str]:
            out: dict[str, str] = {}
            for key, value in raw.items():
                if not isinstance(value, str):
                    raise ValueError(f'runtime.{name}.{key} must be a string')
                out[str(key)] = value
            return out

        def row_button_points() -> dict[str, tuple[str, int]]:
            out: dict[str, tuple[str, int]] = {}
            for row_id, value in row_button_raw.items():
                if not isinstance(value, list) or len(value) != 2 or not isinstance(value[0], str) or isinstance(value[1], bool) or not isinstance(value[1], int):
                    raise ValueError(f'runtime.row_button_random_points.{row_id} must be [point_id, integer]')
                out[str(row_id)] = (value[0], value[1])
            return out

        state = RuntimeState(
            activations=int_map('activations'),
            points=num_map('points'),
            variables={str(k): bool(v) for k, v in variables_raw.items()},
            words={str(k): str(v) for k, v in words_raw.items()},
            row_counts=int_map('row_counts'),
            selected_order=[str(x) for x in selected_order],
            build_order=[str(x) for x in build_order_raw] if build_order_raw is not None else [],
            forced_by=string_set_map('forced_by', forced_raw),
            activated_by=string_set_map('activated_by', activated_raw),
            score_ledger=score_ledger(),
            random_score_ledger=random_score_ledger(),
            random_activation_ledger=random_activation_ledger(),
            custom_words=string_map('custom_words', custom_words_raw),
            uploaded_images=string_map('uploaded_images', uploaded_images_raw),
            row_button_random_points=row_button_points(),
            allowed_deltas=int_map('allowed_deltas'),
            point_effect_ledger={},
            hidden_content=string_set_map('hidden_content', hidden_raw),
            show_all_addons=0,
        )
        show_all_addons_raw = runtime.get('show_all_addons', 0)
        if isinstance(show_all_addons_raw, bool) or not isinstance(show_all_addons_raw, int):
            raise ValueError('runtime.show_all_addons must be an integer')
        state.show_all_addons = show_all_addons_raw
        for owner, entries in point_ledger_raw.items():
            if not isinstance(entries, list):
                raise ValueError(f'runtime.point_effect_ledger.{owner} must be an array')
            converted: list[dict[str, tuple[float, float]]] = []
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    raise ValueError(f'runtime.point_effect_ledger.{owner}[{index}] must be an object')
                one: dict[str, tuple[float, float]] = {}
                for pid, pair in entry.items():
                    if not isinstance(pair, list) or len(pair) != 2:
                        raise ValueError(f'runtime.point_effect_ledger.{owner}[{index}].{pid} must contain two numbers')
                    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(float(x)) for x in pair):
                        raise ValueError(f'runtime.point_effect_ledger.{owner}[{index}].{pid} must contain two finite numbers')
                    one[str(pid)] = (float(pair[0]), float(pair[1]))
                converted.append(one)
            state.point_effect_ledger[str(owner)] = converted
        events_raw = runtime.get('events', [])
        if isinstance(events_raw, list):
            for raw in events_raw:
                if not isinstance(raw, dict):
                    continue
                state.events.append(Event(
                    action=str(raw.get('action', '')),
                    choice_id=str(raw.get('choice_id', '')),
                    ok=bool(raw.get('ok')),
                    message=str(raw.get('message', '')),
                    details=raw.get('details', {}) if isinstance(raw.get('details', {}), dict) else {},
                    code=str(raw['code']) if raw.get('code') is not None else None,
                ))
        if build_order_raw is None:
            # States written before build_order existed remain loadable. Their
            # exact mixed Variable/Row-button insertion order was never stored,
            # so use the most faithful deterministic reconstruction available.
            state.build_order = list(state.selected_order)
            for ident, enabled in state.variables.items():
                if enabled and ident not in state.build_order:
                    state.build_order.append(ident)
            for row_id in state.row_button_random_points:
                if row_id not in state.build_order:
                    state.build_order.append(row_id)
        old_project, old_index, old_req, old_dynamic = self.project, self.index, self.req, self._dynamic_rows
        self.project, self.index, self.req, self._dynamic_rows = candidate_project, candidate_index, candidate_req, dynamic_rows
        try:
            issues = self.runtime_state_issues(state)
            if issues:
                raise ValueError('runtime state is inconsistent: ' + '; '.join(issues))

            seed_raw = document.get('seed', self.seed)
            if isinstance(seed_raw, bool) or not isinstance(seed_raw, int):
                raise ValueError('runtime state seed must be an integer')
            new_seed = seed_raw
            new_rng = random.Random()
            rng_state = document.get('rng_state')
            if rng_state is not None:
                try:
                    new_rng.setstate(_rng_from_json(rng_state))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f'invalid rng_state: {exc}') from exc
            else:
                new_rng.seed(new_seed)
        except Exception:
            self.project, self.index, self.req, self._dynamic_rows = old_project, old_index, old_req, old_dynamic
            raise

        # Commit only after every part of the document has validated. Callers may
        # catch a load error and keep using the existing simulator safely.
        self.state = state
        self.seed = new_seed
        self.rng.setstate(new_rng.getstate())

    @classmethod
    def from_state(cls, project: dict[str, Any], document: dict[str, Any], *, strict_project: bool = True) -> 'Simulator':
        sim = cls(project, seed=int(document.get('seed', 0) or 0), clean=True)
        sim.import_state(document, strict_project=strict_project)
        return sim

    @staticmethod
    def _validate_dialog_responses(value: Any, *, label: str) -> dict[str, dict[str, Any]]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError(f'{label} must be an object keyed by Choice/Add-on ID')
        out: dict[str, dict[str, Any]] = {}
        allowed = {'word', 'image', 'confirm', 'deselect_action'}
        for raw_id, raw in value.items():
            if not isinstance(raw_id, str) or not raw_id:
                raise ValueError(f'{label} keys must be non-empty strings')
            if not isinstance(raw, dict):
                raise ValueError(f'{label}.{raw_id} must be an object')
            unknown = sorted(set(raw) - allowed)
            if unknown:
                raise ValueError(f'{label}.{raw_id} has unknown field(s): {", ".join(unknown)}')
            if 'word' in raw and raw['word'] is not None and not isinstance(raw['word'], str):
                raise ValueError(f'{label}.{raw_id}.word must be a string or null')
            if 'image' in raw and raw['image'] is not None and not isinstance(raw['image'], str):
                raise ValueError(f'{label}.{raw_id}.image must be a string or null')
            if 'confirm' in raw and raw['confirm'] is not None and not isinstance(raw['confirm'], bool):
                raise ValueError(f'{label}.{raw_id}.confirm must be a boolean or null')
            if 'deselect_action' in raw and raw['deselect_action'] not in {'deselect', 'accept', 'cancel'}:
                raise ValueError(f'{label}.{raw_id}.deselect_action must be deselect, accept, or cancel')
            out[raw_id] = dict(raw)
        return out

    @classmethod
    def _validated_action(cls, action: Any, index: int) -> dict[str, Any]:
        if not isinstance(action, dict):
            raise ValueError(f'action {index} must be an object')
        kind = action.get('action')
        if not isinstance(kind, str) or not kind:
            raise ValueError(f'action {index}.action must be a non-empty string')
        allowed_by_kind = {
            'select': {'action', 'id', 'times', 'force', 'source', 'word', 'image', 'confirm', 'dialogs'},
            'deselect': {'action', 'id', 'reason', 'dialog_action', 'word', 'image'},
            'row_button': {'action', 'id', 'dialogs'},
            'status': {'action', 'id'},
            'snapshot': {'action', 'include_choice_status'},
            'view': {'action', 'verbose', 'include_backpack'},
            'reset': {'action'},
        }
        if kind not in allowed_by_kind:
            raise ValueError(f'action {index} has unsupported action {kind!r}')
        unknown = sorted(set(action) - allowed_by_kind[kind])
        if unknown:
            raise ValueError(f'action {index} {kind} has unknown field(s): {", ".join(unknown)}')
        if kind in {'select', 'deselect', 'row_button', 'status'}:
            ident = action.get('id')
            if not isinstance(ident, str) or not ident:
                raise ValueError(f'action {index} {kind} requires non-empty string id')
        if kind == 'select':
            times = action.get('times', 1)
            if isinstance(times, bool) or not isinstance(times, int) or times < 1:
                raise ValueError(f'action {index}.times must be an integer >= 1')
            if 'force' in action and not isinstance(action['force'], bool):
                raise ValueError(f'action {index}.force must be a boolean')
            if 'source' in action and action['source'] is not None and not isinstance(action['source'], str):
                raise ValueError(f'action {index}.source must be a string or null')
            for field in ('word', 'image'):
                if field in action and action[field] is not None and not isinstance(action[field], str):
                    raise ValueError(f'action {index}.{field} must be a string or null')
            if 'confirm' in action and action['confirm'] is not None and not isinstance(action['confirm'], bool):
                raise ValueError(f'action {index}.confirm must be a boolean or null')
            cls._validate_dialog_responses(action.get('dialogs'), label=f'action {index}.dialogs')
        elif kind == 'deselect':
            if 'reason' in action and action['reason'] is not None and not isinstance(action['reason'], str):
                raise ValueError(f'action {index}.reason must be a string or null')
            if action.get('dialog_action', 'deselect') not in {'deselect', 'accept', 'cancel'}:
                raise ValueError(f'action {index}.dialog_action must be deselect, accept, or cancel')
            for field in ('word', 'image'):
                if field in action and action[field] is not None and not isinstance(action[field], str):
                    raise ValueError(f'action {index}.{field} must be a string or null')
        elif kind == 'row_button':
            cls._validate_dialog_responses(action.get('dialogs'), label=f'action {index}.dialogs')
        elif kind == 'snapshot':
            if 'include_choice_status' in action and not isinstance(action['include_choice_status'], bool):
                raise ValueError(f'action {index}.include_choice_status must be a boolean')
        elif kind == 'view':
            for field in ('verbose', 'include_backpack'):
                if field in action and not isinstance(action[field], bool):
                    raise ValueError(f'action {index}.{field} must be a boolean')
        return action

    def apply_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply a machine-friendly action list and return one result per action."""
        results: list[dict[str, Any]] = []
        for index, raw_action in enumerate(actions):
            action = self._validated_action(raw_action, index)
            kind = action['action']
            if kind == 'select':
                ident = action['id']
                event = self.select(
                    ident,
                    times=action.get('times', 1),
                    force=action.get('force', False),
                    source=action.get('source'),
                    word=action.get('word'),
                    image=action.get('image'),
                    confirm=action.get('confirm'),
                    dialogs=action.get('dialogs'),
                )
                results.append({'index': index, 'action': kind, 'event': event.to_dict()})
                if not event.ok:
                    break
            elif kind == 'deselect':
                ident = action['id']
                event = self.deselect(
                    ident, reason=action.get('reason'), dialog_action=action.get('dialog_action', 'deselect'),
                    word=action.get('word'), image=action.get('image'),
                )
                results.append({'index': index, 'action': kind, 'event': event.to_dict()})
                if not event.ok:
                    break
            elif kind == 'row_button':
                ident = action['id']
                event = self.press_row_button(ident, dialogs=action.get('dialogs'))
                results.append({'index': index, 'action': kind, 'event': event.to_dict()})
                if not event.ok:
                    break
            elif kind == 'status':
                ident = action['id']
                results.append({'index': index, 'action': kind, 'status': self.choice_status(ident).to_dict()})
            elif kind == 'snapshot':
                results.append({'index': index, 'action': kind, 'snapshot': self.snapshot(action.get('include_choice_status', False))})
            elif kind == 'view':
                results.append({'index': index, 'action': kind, 'view': self.player_view(verbose=action.get('verbose', False), include_backpack=action.get('include_backpack', False))})
            elif kind == 'reset':
                self.reset()
                results.append({'index': index, 'action': kind, 'ok': True})
            else:
                raise ValueError(f'action {index} has unsupported action {kind!r}')
        return results

    def _entity(self, ident: str) -> Entity | None:
        found = [x for x in self.index.find(ident) if x.kind in {'choice', 'selectable_addon'}]
        return found[0] if len(found) == 1 else None

    def _row(self, ent: Entity) -> Entity | None:
        return self.index.row(ent)

    def _counts_for_row(self, ent: Entity) -> bool:
        if ent.kind == 'choice':
            return ent.value.get('isCountDisabled') is not True
        return ent.value.get('countAsChoice') is True

    def _active(self, ident: str) -> bool:
        return ident in self.state.activations

    def _count(self, ident: str) -> int:
        return int(self.state.activations.get(ident, 0))

    def _build_order_add(self, ident: str) -> None:
        if ident not in self.state.build_order:
            self.state.build_order.append(ident)

    def _build_order_remove(self, ident: str) -> None:
        self.state.build_order = [x for x in self.state.build_order if x != ident]

    @staticmethod
    def _multiple_mode(ent: Entity) -> str | None:
        if not ent.value.get('isSelectableMultiple'):
            return None
        if ent.value.get('isMultipleUseVariable') is True:
            return 'variable'
        if isinstance(ent.value.get('multipleScoreId'), str) and ent.value.get('multipleScoreId'):
            return 'point'
        return 'none'

    def _activation_ref_met(self, ref: str, state: RuntimeState | None = None) -> bool:
        """Mirror Viewer ``checkActivated`` including ``/ON#N`` counts."""
        current = state or self.state
        key, marker, raw = str(ref).partition('/ON#')
        if marker:
            needed = parse_int(raw)
            if needed is not None and needed > 0:
                return int(current.activations.get(key, 0)) >= needed
        return key in current.activations

    def _row_allowed(self, row: Entity) -> int:
        return int(row.value.get('allowedChoices', 0) or 0) + int(self.state.allowed_deltas.get(row.id, 0))

    @staticmethod
    def _semantic(code: str, message: str, **details: Any) -> dict[str, Any]:
        value: dict[str, Any] = {'code': code, 'message': message}
        if details:
            value['details'] = details
        return value

    def _requirements_met(self, value: Any, path: str, state: RuntimeState | None = None) -> tuple[bool, list[RequirementTrace]]:
        return self.req.evaluate(value if isinstance(value, list) else [], state or self.state, path)

    def _design_gate(self, ent: Entity) -> bool:
        gate = str(ent.value.get('activatedId', '') or '')
        if not gate:
            return True
        global_req = self.index.one(gate, 'global_requirement')
        if global_req:
            met, _ = self._requirements_met(global_req.value.get('requireds', []), global_req.path + '/requireds')
            return met
        variable = self.index.one(gate, 'variable')
        if variable:
            return bool(self.state.variables.get(gate, False))
        return self._activation_ref_met(gate)

    def _design_style(self, ids: Any, kind: str, prop: str) -> dict[str, Any] | None:
        if not isinstance(ids, list):
            return None
        for raw in ids:
            ent = self.index.one(str(raw), kind)
            if ent and ent.value.get(prop) and self._design_gate(ent):
                styling = ent.value.get('styling')
                if isinstance(styling, dict):
                    return styling
        return None

    def _group_design_style(self, group_ids: Any, kind: str, prop: str) -> dict[str, Any] | None:
        if not isinstance(group_ids, list):
            return None
        for raw in group_ids:
            group = self.index.one(str(raw), 'group')
            if not group:
                continue
            style = self._design_style(group.value.get('designGroups', []), kind, prop)
            if style is not None:
                return style
        return None

    def _effective_filter_style(self, ent: Entity) -> dict[str, Any]:
        row = self._row(ent)
        if ent.kind in {'choice', 'selectable_addon'}:
            choice = ent if ent.kind == 'choice' else self.index.parent_choice(ent)
            if choice:
                if choice.value.get('isPrivateStyling') and choice.value.get('privateFilterIsOn') and isinstance(choice.value.get('styling'), dict):
                    return choice.value['styling']
                style = self._design_style(choice.value.get('objectDesignGroups', []), 'choice_design_group', 'privateFilterIsOn')
                if style is not None:
                    return style
                style = self._group_design_style(choice.value.get('groups', []), 'choice_design_group', 'privateFilterIsOn')
                if style is not None:
                    return style
        if row:
            if row.value.get('isPrivateStyling') and row.value.get('privateFilterIsOn') and isinstance(row.value.get('styling'), dict):
                return row.value['styling']
            style = self._design_style(row.value.get('rowDesignGroups', []), 'row_design_group', 'privateFilterIsOn')
            if style is not None:
                return style
            style = self._group_design_style(row.value.get('groups', []), 'row_design_group', 'privateFilterIsOn')
            if style is not None:
                return style
        styling = self.project.get('styling')
        return styling if isinstance(styling, dict) else {}

    def _row_visible(self, row: Entity | None) -> bool:
        if not row:
            return False
        met, _ = self._requirements_met(row.value.get('requireds', []), row.path + '/requireds')
        return met

    def _row_flag(self, row: Entity | None, name: str) -> bool:
        if not row:
            return False
        return bool(row.value.get(name) or name in self.state.hidden_content.get(row.id, set()))

    def _choice_visible(self, ent: Entity) -> bool:
        row = self._row(ent)
        if not self._row_visible(row):
            return False
        met, _ = self._requirements_met(ent.value.get('requireds', []), ent.path + '/requireds')
        style = self._effective_filter_style(ent)
        if self._active(ent.id):
            return not bool(style.get('selFilterVisibleIsOn'))
        if not met:
            return not bool(style.get('reqFilterVisibleIsOn'))
        return not bool(style.get('unselFilterVisibleIsOn'))

    def _addon_visible(self, ent: Entity) -> bool:
        row = self._row(ent)
        parent = self.index.parent_choice(ent)
        if not row or not parent or not self._choice_visible(parent):
            return False
        addon_met, _ = self._requirements_met(ent.value.get('requireds', []), ent.path + '/requireds')
        show_all = self.state.show_all_addons > 0
        parent_active = self._active(parent.id)
        ordinary_gate = show_all or ((not ent.value.get('hideAddon') or parent_active) and (ent.value.get('showAddon') or addon_met))
        if not ordinary_gate:
            return False
        if ent.kind == 'selectable_addon':
            if self._row_flag(row, 'unselAddonRemoved') and not self._active(ent.id):
                return False
            if row.value.get('isResultRow') and not self._active(ent.id):
                return False
            return True
        if self._row_flag(row, 'unmetAddonRemoved') and not addon_met:
            return False
        return True

    def entity_visible(self, ident: str) -> bool:
        ent = self._entity(ident)
        if not ent:
            return False
        return self._choice_visible(ent) if ent.kind == 'choice' else self._addon_visible(ent)

    def export_build_summary(self, *, separate_rows: bool = False) -> str:
        """Mirror Creator AppBuildForm ``getSelectedObjectName()`` text output."""
        ordered = []
        seen: set[str] = set()
        for ident in [*self.state.build_order, *self.state.selected_order]:
            if ident in seen or not self._active(ident):
                continue
            ent = self._entity(ident)
            if ent is None or ent.kind not in {'choice', 'selectable_addon'}:
                continue
            seen.add(ident)
            ordered.append(ent)

        def compare(a: Entity, b: Entity) -> int:
            a_row = self._row(a)
            b_row = self._row(b)
            if a_row is not None and b_row is not None:
                ai = a_row.value.get('index')
                bi = b_row.value.get('index')
                if isinstance(ai, (int, float)) and isinstance(bi, (int, float)) and ai != bi:
                    return -1 if ai < bi else 1
            ai = a.value.get('index')
            bi = b.value.get('index')
            # JavaScript's comparator returns NaN when an Addon has no index.
            # Array.sort treats that as zero and keeps the stable input order.
            if not isinstance(ai, (int, float)) or not isinstance(bi, (int, float)) or ai == bi:
                return 0
            return -1 if ai < bi else 1

        ordered.sort(key=cmp_to_key(compare))

        def title(ent: Entity) -> str:
            if ent.value.get('isNotBuild'):
                return ''
            values = []
            if ent.value.get('showDebugTitle') and ent.value.get('debugTitle'):
                values.append(str(ent.value.get('debugTitle')))
            if ent.value.get('title'):
                values.append(str(ent.value.get('title')))
            text = ' '.join(values)
            if text and ent.value.get('isSelectableMultiple'):
                text += f'(x{self._count(ent.id)})'
            return text

        if separate_rows:
            parts: list[str] = []
            previous = ''
            for ent in ordered:
                value = title(ent)
                if not value:
                    continue
                row = self._row(ent)
                row_id = row.id if row is not None else ''
                if row_id != previous:
                    if previous:
                        parts.append('\n')
                    row_title = ''
                    if row is not None:
                        row_title = str(row.value.get('title') or row.value.get('debugTitle') or '')
                    parts.append(f'**{row_title}**\n')
                    parts.append(value)
                    previous = row_id
                else:
                    parts.append(', ' + value)
            raw = ''.join(parts)
        else:
            raw = ', '.join(value for ent in ordered if (value := title(ent)))
        return self._replace_text(browser_text_content(raw))

    def _replace_text(self, raw: Any) -> str:
        """Mirror Viewer ``replaceText()`` without evaluating HTML.

        ICC Plus builds the replacement regex from ``app.words`` IDs. A matching
        ID is then resolved as a Point Type first, a multi-select Choice second,
        and a Word last. Restricting replacement to Word IDs is important: replacing
        every project ID as a raw substring would corrupt ordinary prose.
        """
        text = str(raw or '')
        for key in sorted(self.state.words, key=len, reverse=True):
            if not key:
                continue
            replacement = self.state.words[key]
            point = self.index.one(key, 'point')
            if point is not None:
                value = float(self.state.points.get(key, 0.0))
                places = int(point.value.get('decimalPlaces', 2) or 2)
                replacement = str(_clean_num(round(value, places)))
            else:
                choice = self._entity(key)
                if choice is not None and choice.value.get('isSelectableMultiple') and choice.value.get('isMultipleUseVariable'):
                    replacement = str(self._count(key))
            text = text.replace(key, replacement)
        return text

    def _content_value(self, row: Entity, obj: dict[str, Any], field: str, hidden_flag: str) -> str | None:
        if self._row_flag(row, hidden_flag):
            return None
        value = self._replace_text(obj.get(field, ''))
        return value if value else None

    def _trace_reasons(self, traces: list[RequirementTrace]) -> list[str]:
        out: list[str] = []
        def visit(t: RequirementTrace) -> None:
            if not t.result:
                out.append(f'{t.type}: {t.detail}')
            for child in t.children:
                visit(child)
        for trace in traces: visit(trace)
        # stable de-dup
        return list(dict.fromkeys(out))

    def _score_value(
        self,
        score: dict[str, Any],
        ent: Entity,
        points: dict[str, float],
        *,
        score_index: int,
        repeat_ordinal: int | None = None,
    ) -> tuple[float, float | None]:
        """Return the applied score and the raw random value, if any.

        ICC Plus stores the raw random Score value in its Build Form string before
        discounts and multiplyByTimes change the amount applied to the Point Type.
        Keeping both values is required for lossless Build Form interchange.
        """
        point = self.index.one(str(score.get('id', '')), 'point')
        allow_float = bool(point and point.value.get('allowFloat'))
        value = float(score.get('value', 0) or 0)
        random_value: float | None = None
        override = self._score_value_overrides.get(ent.id, {}).get(score_index)
        if score.get('useExpression'):
            try:
                if score.get('isRandom') and score.get('expMinValue') is not None and score.get('expMaxValue') is not None:
                    if override is not None:
                        value = float(override)
                    else:
                        low = eval_expr(str(score['expMinValue']), points)
                        high = eval_expr(str(score['expMaxValue']), points)
                        lo, hi = math.floor(min(low, high)), math.floor(max(low, high))
                        value = float(self.rng.randint(lo, hi))
                    random_value = value
                elif score.get('expValue'):
                    value = eval_expr(str(score['expValue']), points)
            except (ValueError, KeyError, SyntaxError):
                value = float(score.get('value', 0) or 0)
        elif score.get('isRandom'):
            if override is not None:
                value = float(override)
            else:
                lo = int(score.get('minValue', value) or 0)
                hi = int(score.get('maxValue', value) or 0)
                if lo > hi:
                    lo, hi = hi, lo
                value = float(self.rng.randint(lo, hi))
            random_value = value
        # setScoreValue follows the Point Type's integer policy before later score
        # transforms. Random values are integers in upstream, but keep this generic
        # for imported builds and expression-based values.
        if not allow_float:
            value = float(math.floor(value))
            if random_value is not None:
                random_value = float(math.floor(random_value))
        if score.get('discountIsOn') and score.get('appliedDiscount') and score.get('discountScore') is not None:
            value = float(score['discountScore'])
            if not allow_float:
                value = float(math.floor(value))
        if score.get('multiplyByTimes'):
            ordinal = repeat_ordinal if repeat_ordinal is not None else abs(self._count(ent.id)) + 1
            value *= max(1, int(ordinal))
        return value, random_value

    def _preview_scores(
        self,
        ent: Entity,
        hypothetical: RuntimeState,
        *,
        repeat_ordinal: int | None = None,
    ) -> tuple[dict[str, float], dict[str, float], list[str], dict[int, float]]:
        preview = dict(hypothetical.points)
        ledger: dict[str, float] = {}
        random_values: dict[int, float] = {}
        reasons: list[str] = []
        for i, score in enumerate(ent.value.get('scores', []) if isinstance(ent.value.get('scores'), list) else []):
            if not isinstance(score, dict):
                continue
            pid = str(score.get('id', ''))
            if pid not in preview:
                continue
            met, _ = self.req.evaluate(score.get('requireds', []), hypothetical, f'{ent.path}/scores/{i}/requireds')
            if not met:
                continue
            value, random_value = self._score_value(score, ent, preview, score_index=i, repeat_ordinal=repeat_ordinal)
            preview[pid] -= value
            ledger[pid] = ledger.get(pid, 0.0) + value
            if random_value is not None:
                random_values[i] = random_value
        for pid, value in preview.items():
            point = self.index.one(pid, 'point')
            if point and point.value.get('belowZeroNotAllowed') and value < 0:
                reasons.append(f'point {pid} would fall below zero ({value:g})')
        return preview, ledger, reasons, random_values

    def _hypothetical_with_selection(self, ent: Entity, base: RuntimeState | None = None) -> RuntimeState:
        temp = (base or self.state).clone()
        current = int(temp.activations.get(ent.id, 0))
        mode = self._multiple_mode(ent)
        if mode == 'variable':
            new_count = current + 1
            if new_count == 0:
                temp.activations.pop(ent.id, None)
            else:
                temp.activations[ent.id] = new_count
        elif mode in {'point', 'none'}:
            # selectedOneMore() does not activate the entity in these modes.
            return temp
        else:
            temp.activations[ent.id] = 0
        was_active = ent.id in (base or self.state).activations
        is_active = ent.id in temp.activations
        if self._counts_for_row(ent) and not was_active and is_active:
            temp.row_counts[ent.row_id or ''] = temp.row_counts.get(ent.row_id or '', 0) + 1
        elif self._counts_for_row(ent) and was_active and not is_active:
            temp.row_counts[ent.row_id or ''] = max(0, temp.row_counts.get(ent.row_id or '', 0) - 1)
        self._set_variables_on(temp, ent, True, first=not was_active and is_active)
        return temp

    def _row_replacement_candidates(self, ent: Entity) -> list[str]:
        row = self._row(ent)
        if not row or not self._counts_for_row(ent):
            return []
        allowed = self._row_allowed(row)
        if allowed <= 0 or self.state.row_counts.get(row.id, 0) < allowed or self._active(ent.id):
            return []
        candidates: list[str] = []
        for ident in self.state.selected_order:
            other = self._entity(ident)
            if not other or other.row_id != row.id or other.id == ent.parent_id:
                continue
            if not self._counts_for_row(other):
                continue
            if other.value.get('selectOnce') or self.state.forced_by.get(other.id):
                continue
            # ICC Plus row-cap replacement handles multiple choices by calling
            # selectedOneLess once for each *positive* current repeat. A zero or
            # negative repeat therefore cannot free the row slot here.
            if other.value.get('isSelectableMultiple') and self._count(other.id) <= 0:
                continue
            candidates.append(other.id)
        return candidates

    def choice_status(self, ident: str, *, internal: bool = False, _seen: set[str] | None = None) -> ChoiceStatus:
        """Return current selection eligibility.

        Player-facing status enforces what the Viewer lets a user click. Internal
        status mirrors checkSelectable() and deliberately ignores UI-only
        isNotSelectable/visibility restrictions used by forced activation and
        selectable-Addon parent activation.
        """
        rng_state = self.rng.getstate()
        try:
            ent = self._entity(ident)
            if not ent:
                error = self._semantic('entity.not_found', 'choice/selectable addon not found or ID is ambiguous', id=ident)
                return ChoiceStatus(ident, False, False, 0, [error['message']], [], {}, [], [], False, [error])

            seen = set(_seen or ())
            if ent.id in seen:
                error = self._semantic('selection.parent_cycle', f'parent activation cycle reaches {ent.id}')
                return ChoiceStatus(ent.id, False, self._active(ent.id), self._count(ent.id), [error['message']], [], dict(self.state.points), [], [], True, [error])
            seen.add(ent.id)

            reasons: list[str] = []
            semantic: list[dict[str, Any]] = []
            unsupported = sorted(k for k in self.ADVANCED if ent.value.get(k))
            row = self._row(ent)
            visible = True if internal else self.entity_visible(ent.id)

            def fail(code: str, message: str, **details: Any) -> None:
                reasons.append(message)
                semantic.append(self._semantic(code, message, **details))

            if not internal and not visible:
                fail('visibility.hidden', f'{ent.id} is not visible to the player in the current state', id=ent.id, row_id=ent.row_id)
            if not internal and ent.value.get('isNotSelectable'):
                fail('selection.not_selectable', 'isNotSelectable is true; the Viewer does not allow direct player selection')
            if row and row.value.get('isInfoRow'):
                fail('row.info', f'parent row {row.id} is an info row')

            if not isinstance(ent.value.get('requireds', []), list):
                traces: list[dict[str, Any]] = []
                fail('requirements.invalid', 'requireds is not an array')
            else:
                req_met, trace_objects = self._requirements_met(ent.value.get('requireds', []), ent.path + '/requireds')
                traces = [x.to_dict() for x in trace_objects]
                if not req_met:
                    messages = self._trace_reasons(trace_objects) or ['requirements are not met']
                    reasons.extend(messages)
                    semantic.append(self._semantic('requirements.unmet', 'requirements are not met', reasons=messages, traces=traces))

            base_state = self.state.clone()
            if ent.kind == 'selectable_addon':
                parent = self.index.parent_choice(ent)
                if not parent:
                    fail('addon.parent_missing', f'selectable Addon {ent.id} has no resolvable parent Choice')
                else:
                    if not internal:
                        parent_met, parent_traces = self._requirements_met(parent.value.get('requireds', []), parent.path + '/requireds')
                        if not parent_met:
                            fail(
                                'addon.parent_requirements_unmet',
                                f'parent choice {parent.id} requirements are not met, so the Addon cannot be clicked',
                                parent_id=parent.id,
                                traces=[x.to_dict() for x in parent_traces],
                            )
                    if not self._active(parent.id):
                        parent_status = self.choice_status(parent.id, internal=True, _seen=seen)
                        if not parent_status.selectable:
                            fail(
                                'addon.parent_activation_failed',
                                f'parent choice {parent.id} cannot be internally activated',
                                parent_id=parent.id,
                                parent_errors=parent_status.semantic_errors,
                            )
                        else:
                            parent_hyp = self._hypothetical_with_selection(parent, base_state)
                            parent_ordinal = abs(int(base_state.activations.get(parent.id, 0))) + 1
                            parent_points, _, parent_point_reasons, _ = self._preview_scores(parent, parent_hyp, repeat_ordinal=parent_ordinal)
                            if parent_point_reasons:
                                fail('addon.parent_points', f'parent choice {parent.id} cannot be afforded', parent_id=parent.id, reasons=parent_point_reasons)
                            parent_hyp.points = parent_points
                            base_state = parent_hyp

            if self._active(ent.id) and not ent.value.get('isSelectableMultiple'):
                fail('selection.already_active', 'already selected and not a multiple-selection choice')
            mode = self._multiple_mode(ent)
            if mode == 'variable':
                maximum = ent.value.get('numMultipleTimesPluss', self.project.get('defaultChoiceMaxNum', 99))
                if isinstance(maximum, (int, float)) and self._count(ent.id) >= int(maximum):
                    fail('selection.maximum_reached', f'multiple-selection maximum {int(maximum)} reached', maximum=int(maximum))
            elif mode == 'point':
                pid = str(ent.value.get('multipleScoreId'))
                maximum = ent.value.get('numMultipleTimesPluss', 0)
                if pid in base_state.points and isinstance(maximum, (int, float)) and base_state.points[pid] >= float(maximum):
                    fail('selection.maximum_reached', f'point-backed counter maximum {int(maximum)} reached', maximum=int(maximum))

            hypothetical = self._hypothetical_with_selection(ent, base_state)
            ordinal = abs(int(base_state.activations.get(ent.id, 0))) + 1
            # checkPoints() checks score affordability before dispatching the
            # repeat mode, but point modify effects run later only in selectObject.
            preview, _, point_reasons, _ = self._preview_scores(ent, hypothetical, repeat_ordinal=ordinal)
            if point_reasons:
                reasons.extend(point_reasons)
                semantic.append(self._semantic('points.below_zero_not_allowed', 'selection would violate a Point Type configured with belowZeroNotAllowed', reasons=point_reasons, preview={k: _clean_num(v) for k, v in preview.items()}))

            replacements = self._row_replacement_candidates(ent)
            if row and self._counts_for_row(ent):
                allowed = self._row_allowed(row)
                if allowed > 0 and self.state.row_counts.get(row.id, 0) >= allowed and not self._active(ent.id) and not replacements:
                    fail('row.capacity', f'row {row.id} is at its allowedChoices limit ({allowed}) and has no deselectable occupant', row_id=row.id, allowed=allowed)

            return ChoiceStatus(
                ent.id, not reasons, self._active(ent.id), self._count(ent.id), reasons, traces,
                {k: _clean_num(v) for k, v in preview.items()}, replacements[:1], unsupported, visible, semantic,
            )
        finally:
            # Status must be observational. Random score previews use the same RNG
            # values the subsequent real selection will see without consuming them.
            self.rng.setstate(rng_state)

    def _set_variables_on(self, state: RuntimeState, ent: Entity, selecting: bool, *, first: bool) -> None:
        if not first or not ent.value.get('isChangeVariables'):
            return
        ids = ent.value.get('changedVariables', [])
        if not isinstance(ids, list): return
        mode = str(ent.value.get('changeType', '1'))
        for raw in ids:
            ident = str(raw)
            if ident not in state.variables: continue
            if mode == '1': state.variables[ident] = selecting
            elif mode == '2': state.variables[ident] = not selecting
            elif mode == '3': state.variables[ident] = not state.variables[ident]
            if state.variables[ident]: state.activations[ident] = 0
            else: state.activations.pop(ident, None)

    def _set_variables(self, ent: Entity, selecting: bool, *, first: bool) -> None:
        before = {ident for ident, enabled in self.state.variables.items() if enabled}
        self._set_variables_on(self.state, ent, selecting, first=first)
        after = {ident for ident, enabled in self.state.variables.items() if enabled}
        for ident in self.state.variables:
            if ident in after and ident not in before:
                self._build_order_add(ident)
            elif ident in before and ident not in after:
                self._build_order_remove(ident)

    def _apply_scores(self, ent: Entity) -> None:
        hypothetical = self.state.clone()
        ordinal = abs(self._count(ent.id)) if ent.value.get('isSelectableMultiple') else 1
        preview, ledger, _, random_values = self._preview_scores(ent, hypothetical, repeat_ordinal=max(1, ordinal))
        self.state.points = preview
        self.state.score_ledger.setdefault(ent.id, []).append(ledger)
        self.state.random_score_ledger.setdefault(ent.id, []).append(random_values)

    def _undo_scores(self, ent: Entity) -> None:
        history = self.state.score_ledger.get(ent.id, [])
        if not history: return
        ledger = history.pop()
        for pid, value in ledger.items():
            if pid in self.state.points: self.state.points[pid] += value
        if not history: self.state.score_ledger.pop(ent.id, None)
        random_history = self.state.random_score_ledger.get(ent.id, [])
        if random_history:
            random_history.pop()
            if not random_history:
                self.state.random_score_ledger.pop(ent.id, None)

    @staticmethod
    def _dup_suffix_ref(token: str, suffix: str) -> str:
        parts = token.split('/ON#', 1)
        base = parts[0].split('/D#', 1)[0] + suffix
        return base + ('/ON#' + parts[1] if len(parts) > 1 else '')

    def _duplicate_row_requirements(self, value: Any, suffix: str) -> None:
        """Apply the 2.10.6 duplicateRow ID suffix rule to native Requirement data."""
        if not isinstance(value, list):
            return
        for req in value:
            if not isinstance(req, dict):
                continue
            typ = req.get('type')
            if typ == 'id' and isinstance(req.get('reqId'), str):
                req['reqId'] = self._dup_suffix_ref(req['reqId'], suffix)
            elif typ == 'or' and isinstance(req.get('orRequired'), list):
                for item in req['orRequired']:
                    if isinstance(item, dict) and isinstance(item.get('req'), str):
                        item['req'] = self._dup_suffix_ref(item['req'], suffix)
            # The pinned 2.10.6 source does not successfully descend into nested
            # requirements here. Keep that behavior instead of repairing it.

    def _duplicate_row_functions(self, choice: dict[str, Any], suffix: str) -> None:
        for enabled, key in (
            ('activateOtherChoice', 'activateThisChoice'),
            ('deactivateOtherChoice', 'deactivateThisChoice'),
        ):
            raw = choice.get(key)
            if choice.get(enabled) and isinstance(raw, str):
                # Upstream builds this string by concatenating each rewritten
                # token plus a comma, including the trailing comma.
                choice[key] = ''.join(self._dup_suffix_ref(token, suffix) + ',' for token in raw.split(','))
        if choice.get('duplicateRow') and isinstance(choice.get('duplicateRowId'), str) and isinstance(choice.get('duplicateRowPlace'), str):
            source = choice['duplicateRowId'].split('/D', 1)[0]
            target = choice['duplicateRowPlace'].split('/D', 1)[0]
            choice['duplicateRowId'] = source + suffix
            choice['duplicateRowPlace'] = target + suffix

    def _new_duplicate_score_idx(self, old: str, suffix: str, used: set[str]) -> str:
        # Upstream generateId() is random, so exact Score idx bytes are not
        # deterministic. Keep the same uniqueness guarantee with a stable ID.
        digest = hashlib.sha256((old + suffix).encode('utf-8')).hexdigest()[:5]
        candidate = 's-' + digest
        n = 1
        while candidate in used:
            digest = hashlib.sha256((old + suffix + f':{n}').encode('utf-8')).hexdigest()[:5]
            candidate = 's-' + digest
            n += 1
        used.add(candidate)
        return candidate

    def _duplicate_row_effect(self, ent: Entity) -> str | None:
        """Mirror ICC Plus 2.10.6 ``duplicateRow()`` for a selected entity."""
        choice = ent.value
        if not choice.get('duplicateRow'):
            return None
        source_id = choice.get('duplicateRowId')
        target_id = choice.get('duplicateRowPlace')
        if not isinstance(source_id, str) or not isinstance(target_id, str):
            return None
        source = self.index.one(source_id, 'row') or self.index.one(source_id, 'backpack_row')
        target = self.index.one(target_id, 'row') or self.index.one(target_id, 'backpack_row')
        if source is None or target is None:
            return None

        source_base = source_id.split('/D#', 1)[0]
        count = 0
        for row in self.index.by_kind.get('row', []) + self.index.by_kind.get('backpack_row', []):
            if row.id.split('/D#', 1)[0] == source_base:
                count += 1
        suffix = f'/D#{count}'
        new_row = copy.deepcopy(source.value)
        new_row['id'] = new_row.get('id', source_id).split('/D#', 1)[0] + suffix

        collection_key = 'backpack' if target.kind == 'backpack_row' else 'rows'
        collection = self.project.setdefault(collection_key, [])
        target_index = next((i for i, row in enumerate(collection) if isinstance(row, dict) and row.get('id') == target.id), None)
        if target_index is None:
            return None
        collection.insert(target_index + 1, new_row)
        for i, row in enumerate(collection):
            if isinstance(row, dict):
                row['index'] = i

        used_score_ids = {
            str(score.value.get('idx'))
            for score in self.index.by_kind.get('score', [])
            if score.value.get('idx')
        }
        for new_choice in new_row.get('objects', []) if isinstance(new_row.get('objects'), list) else []:
            if not isinstance(new_choice, dict):
                continue
            new_choice['id'] = str(new_choice.get('id', '')).split('/D#', 1)[0] + suffix
            new_choice['isActive'] = False
            new_choice.pop('forcedActivated', None)
            new_choice.pop('appliedDisChoices', None)
            for score in new_choice.get('scores', []) if isinstance(new_choice.get('scores'), list) else []:
                if not isinstance(score, dict):
                    continue
                old_idx = str(score.get('idx', ''))
                score['idx'] = self._new_duplicate_score_idx(old_idx, suffix, used_score_ids)
                for key in (
                    'isActive','isActiveMul','isActiveMulMinus','setValue','tmpDiscount',
                    'discountTextA','discountTextB','dupTextA','dupTextB','discountedFrom',
                    'discountIsOn','discountScore','discountScoreCal','notStackableDiscount',
                    'discountShow','discountBeforeText','discountAfterText','isChangeDiscount',
                    'tmpDisScore','appliedDiscount','replaceText','hideDisValue','hideDisIcon',
                    'discountNum','discounts',
                ):
                    score.pop(key, None)
            for addon in new_choice.get('addons', []) if isinstance(new_choice.get('addons'), list) else []:
                if isinstance(addon, dict):
                    addon['parentId'] = new_choice['id']

            if not choice.get('dRowAddSufReq'):
                self._duplicate_row_requirements(new_choice.get('requireds'), suffix)
                for score in new_choice.get('scores', []) if isinstance(new_choice.get('scores'), list) else []:
                    if isinstance(score, dict):
                        self._duplicate_row_requirements(score.get('requireds'), suffix)
                for addon in new_choice.get('addons', []) if isinstance(new_choice.get('addons'), list) else []:
                    if isinstance(addon, dict):
                        self._duplicate_row_requirements(addon.get('requireds'), suffix)

            if not choice.get('dRowAddSufFunc'):
                self._duplicate_row_functions(new_choice, suffix)

            if new_choice.get('backpackBtnRequirement'):
                if isinstance(self.project.get('hideBackpackBtn'), (int, float)) and not isinstance(self.project.get('hideBackpackBtn'), bool):
                    self.project['hideBackpackBtn'] += 1
                else:
                    new_choice.pop('backpackBtnRequirement', None)
            for group_id in new_choice.get('groups', []) if isinstance(new_choice.get('groups'), list) else []:
                group = next((g for g in self.project.get('groups', []) if isinstance(g, dict) and g.get('id') == group_id), None)
                if group is not None:
                    group.setdefault('elements', [])
                    if new_choice['id'] not in group['elements']:
                        group['elements'].append(new_choice['id'])
            for design_id in new_choice.get('objectDesignGroups', []) if isinstance(new_choice.get('objectDesignGroups'), list) else []:
                group = next((g for g in self.project.get('objectDesignGroups', []) if isinstance(g, dict) and g.get('id') == design_id), None)
                if group is not None:
                    group.setdefault('elements', [])
                    if new_choice['id'] not in group['elements']:
                        group['elements'].append(new_choice['id'])

        self._dynamic_rows.append({
            'collection': collection_key,
            'index': target_index + 1,
            'row': copy.deepcopy(new_row),
        })
        # ProjectIndex and RequirementEngine contain references into the project.
        # Rebuild them after the structural mutation and add the new Row's
        # runtime counter without touching existing state.
        self.index = ProjectIndex(self.project)
        self.req = RequirementEngine(self.index)
        self.state.row_counts[new_row['id']] = 0
        return str(new_row['id'])

    def _apply_point_effects(self, ent: Entity) -> None:
        changed: dict[str, tuple[float, float]] = {}
        for field, targets_field, value_field in [
            ('multiplyPointtypeIsOn', 'pointTypeToMultiply', 'multiplyWithThis'),
            ('dividePointtypeIsOn', 'pointTypeToDivide', 'divideWithThis'),
            ('setPointtypeIsOn', 'pointTypeToSet', 'setWithThis'),
        ]:
            if not ent.value.get(field): continue
            targets = ent.value.get(targets_field, [])
            if not isinstance(targets, list): continue
            for raw in targets:
                pid = str(raw)
                if pid not in self.state.points: continue
                before = self.state.points[pid]
                try:
                    if field == 'multiplyPointtypeIsOn':
                        factor_raw = ent.value.get(value_field, 1)
                        factor = eval_expr(str(factor_raw), self.state.points) if isinstance(factor_raw, str) else float(factor_raw or 0)
                        after = before * factor
                    elif field == 'dividePointtypeIsOn':
                        divisor = float(ent.value.get(value_field, 1) or 1)
                        after = before if divisor == 0 else before / divisor
                    else:
                        after = eval_expr(str(ent.value.get(value_field, '0')), self.state.points)
                except (ValueError, KeyError, SyntaxError):
                    continue
                point = self.index.one(pid, 'point')
                if point and not point.value.get('allowFloat'): after = float(math.floor(after))
                changed[pid] = (before, after); self.state.points[pid] = after
        if changed: self.state.point_effect_ledger.setdefault(ent.id, []).append(changed)

    def _undo_point_effects(self, ent: Entity) -> None:
        entries = self.state.point_effect_ledger.get(ent.id, [])
        if not entries: return
        changed = entries.pop()
        # This matches simple LIFO use. Validation reports complicated stacking as an advanced case.
        for pid, (before, _) in changed.items(): self.state.points[pid] = before
        if not entries: self.state.point_effect_ledger.pop(ent.id, None)

    def _change_allowed(self, ent: Entity, direction: int) -> None:
        if not ent.value.get('addToAllowChoice'): return
        targets = ent.value.get('idOfAllowChoice', [])
        amount = int(ent.value.get('numbAddToAllowChoice', 0) or 0)
        if not isinstance(targets, list): return
        for raw in targets:
            rid = str(raw)
            self.state.allowed_deltas[rid] = self.state.allowed_deltas.get(rid, 0) + amount * direction

    def _change_hidden_content(self, ent: Entity, selecting: bool) -> None:
        if not ent.value.get('isContentHidden'):
            return
        rows = ent.value.get('hiddenContentsRow', [])
        types = ent.value.get('hiddenContentsType', [])
        if not isinstance(rows, list) or not isinstance(types, list):
            return
        # Image-only hide codes (2 and 7) have no gameplay consequence in the
        # headless runner. The Viewer also sets textIsRemoved for any hide-content
        # effect, so that non-image behavior is still modeled below.
        names = {
            '1': 'objectTitleRemoved',
            '3': 'objectTextRemoved',
            '4': 'objectScoreRemoved',
            '5': 'objectRequirementRemoved',
            '6': 'addonTitleRemoved',
            '8': 'addonTextRemoved',
            '9': 'unselAddonRemoved',
            '10': 'unmetAddonRemoved',
        }
        for raw_row in rows:
            rid = str(raw_row)
            if not (self.index.one(rid, 'row') or self.index.one(rid, 'backpack_row')):
                continue
            flags = self.state.hidden_content.setdefault(rid, set())
            if selecting:
                flags.add('textIsRemoved')
            for raw_type in types:
                name = names.get(str(raw_type))
                if not name:
                    continue
                if selecting:
                    flags.add(name)
                else:
                    flags.discard(name)
            if not flags:
                self.state.hidden_content.pop(rid, None)

    def _change_show_all_addons(self, ent: Entity, direction: int) -> None:
        if ent.value.get('showAllAddons'):
            self.state.show_all_addons = max(0, self.state.show_all_addons + direction)

    def _targets(self, raw: Any) -> list[tuple[str, int | None]]:
        if not isinstance(raw, str):
            return []
        out: list[tuple[str, int | None]] = []
        for token in raw.split(','):
            # ICC Plus uses split(',') literally; surrounding whitespace is part
            # of the ID and therefore prevents a match.
            if not token:
                continue
            if '/ON#' in token:
                base, num = token.split('/ON#', 1)
                n = parse_int(num)
            else:
                base, n = token, None
            direct = self._entity(base)
            if direct:
                out.append((direct.id, n))
                continue
            for ident in self.index.group_members(base):
                if self._entity(ident):
                    out.append((ident, n))
        # ICC Plus processes repeated entries and overlapping groups in order.
        return out

    def _force_activate_one(self, source: Entity, target: str, n: int | None, depth: int, dialogs: dict[str, dict[str, Any]] | None = None) -> tuple[bool, bool]:
        """Apply one upstream force-activation token.

        Returns ``(registered, changed)``. ``registered`` means the source is a
        provider for an active target. ``changed`` means this token actually
        changed target activation/count, which ICC Plus uses when choosing a
        replacement candidate for random activation.
        """
        target_ent = self._entity(target)
        if not target_ent:
            return False, False
        if target_ent.value.get('isNotSelectable') and source.value.get('isNotActiveUnselectable'):
            return False, False

        before_active = self._active(target)
        before_count = self._count(target)
        registered = False
        if target_ent.value.get('isSelectableMultiple'):
            # Preserve the 2.10.6 source behavior. A bare multiple target has a
            # force count of zero and the negative loop is unreachable.
            if n is not None and n > 0:
                for _ in range(n):
                    event = self.select(target, force=True, source=source.id, _depth=depth + 1, _internal=True, _dialogs=dialogs)
                    if not event.ok:
                        break
                registered = self._active(target)
            elif n is not None and n < 0:
                registered = False
        else:
            if before_active:
                registered = True
            else:
                event = self.select(target, force=True, source=source.id, _depth=depth + 1, _internal=True, _dialogs=dialogs)
                registered = event.ok and self._active(target)

        if registered and self._active(target):
            self.state.activated_by.setdefault(target, set()).add(source.id)
            if not source.value.get('isAllowDeselect'):
                self.state.forced_by.setdefault(target, set()).add(source.id)
        changed = before_active != self._active(target) or before_count != self._count(target)
        return registered, changed

    def _random_activation_candidates(self, ent: Entity) -> list[tuple[str, int]]:
        """Build the ordered candidate map used by selectForceRandomActivate()."""
        raw = ent.value.get('activateThisChoice')
        if not isinstance(raw, str):
            return []
        # JS Map keeps first insertion position while later set() calls replace the
        # value, so an ordinary dict has the same behavior here.
        candidate_map: dict[str, int] = {}
        for token in raw.split(','):
            if not token:
                continue
            if '/ON#' in token:
                key, number = token.split('/ON#', 1)
                parsed = parse_int(number)
                num = 0 if parsed is None else parsed
            else:
                key, num = token, 0
            group_members = self.index.group_members(key)
            ids = group_members if group_members else [key]
            for ident in ids:
                choice = self._entity(ident)
                if not choice:
                    continue
                count = self._count(ident)
                maximum = choice.value.get('numMultipleTimesPluss')
                repeat_ok = bool(
                    choice.value.get('isSelectableMultiple')
                    and choice.value.get('isMultipleUseVariable')
                    and isinstance(maximum, (int, float))
                    and float(maximum) >= count + num
                    and not (self._row(choice) and self._row(choice).value.get('isInfoRow'))
                    and not choice.value.get('isNotSelectable')
                    and self._requirements_met(choice.value.get('requireds', []), choice.path + '/requireds')[0]
                )
                if not self._active(ident) or repeat_ok:
                    candidate_map[ident] = num
        return list(candidate_map.items())

    def _force_activate_targets(self, ent: Entity, depth: int, dialogs: dict[str, dict[str, Any]] | None = None) -> None:
        if not ent.value.get('activateOtherChoice'):
            return
        if ent.value.get('isActivateRandom'):
            override = self._random_activation_overrides.get(ent.id)
            result: list[str] = []
            if override is not None:
                candidates: list[tuple[str, int]] = []
                for token in override:
                    if '/ON#' in token:
                        ident, raw_n = token.split('/ON#', 1)
                        parsed = parse_int(raw_n)
                        candidates.append((ident, 0 if parsed is None else parsed))
                    else:
                        candidates.append((token, 0))
                desired = len(candidates)
            else:
                candidates = self._random_activation_candidates(ent)
                # Exact Fisher-Yates shape from ICC Plus. Python's RNG is seeded
                # for deterministic local tests; the original browser uses
                # Math.random(), so build strings store the chosen result.
                shuffled = list(candidates)
                for i in range(len(shuffled) - 1, 0, -1):
                    j = self.rng.randrange(i + 1)
                    shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
                candidates = shuffled
                try:
                    requested = int(ent.value.get('numActivateRandom', 0) or 0)
                except (TypeError, ValueError):
                    requested = 0
                desired = min(len(candidates), max(0, requested))

            i = 0
            while i < len(candidates) and len(result) < desired:
                ident, num = candidates[i]
                registered, changed = self._force_activate_one(ent, ident, num, depth, dialogs)
                if registered and changed:
                    result.append(f'{ident}/ON#{num}' if num > 0 else ident)
                i += 1
            self.state.random_activation_ledger.setdefault(ent.id, []).append(result)
            return

        for target, n in self._targets(ent.value.get('activateThisChoice')):
            self._force_activate_one(ent, target, n, depth, dialogs)

    def _deactivate_targets(self, ent: Entity, depth: int) -> int | None:
        if not ent.value.get('deactivateOtherChoice'):
            return None
        self_count: int | None = None
        for target, n in self._targets(ent.value.get('deactivateThisChoice')):
            if target == ent.id:
                # Viewer defers self-deactivation until selection processing ends.
                self_count = -1 if n is None else n
                continue
            target_ent = self._entity(target)
            if not target_ent or not self._active(target) or self.state.forced_by.get(target):
                continue
            if self._multiple_mode(target_ent) == 'variable':
                current = max(0, self._count(target))
                if n is None or n == -1:
                    times = current
                elif n > 0:
                    times = n
                else:
                    times = 0
            else:
                times = 1
            for _ in range(times):
                if not self._active(target):
                    break
                self.deselect(target, _depth=depth + 1, _internal=True)
        return self_count

    def _cleanup_unmet(self, changed_id: str, depth: int) -> None:
        if depth > 30: return
        for ident in list(self.state.selected_order):
            if ident == changed_id or not self._active(ident): continue
            ent = self._entity(ident)
            if not ent: continue
            met, _ = self.req.evaluate(ent.value.get('requireds', []), self.state, ent.path + '/requireds')
            if not met:
                self.deselect(ident, reason=f'requirements became unmet after {changed_id}', _depth=depth + 1, force_cleanup=True, _internal=True)

    def _point_effect_preview(self, ent: Entity, points: dict[str, float]) -> tuple[dict[str, float], list[str]]:
        """Preview post-selection point modifiers without changing runtime state."""
        preview = dict(points)
        reasons: list[str] = []
        for field, targets_field, value_field in [
            ('multiplyPointtypeIsOn', 'pointTypeToMultiply', 'multiplyWithThis'),
            ('dividePointtypeIsOn', 'pointTypeToDivide', 'divideWithThis'),
            ('setPointtypeIsOn', 'pointTypeToSet', 'setWithThis'),
        ]:
            if not ent.value.get(field):
                continue
            targets = ent.value.get(targets_field, [])
            if not isinstance(targets, list):
                continue
            for raw in targets:
                pid = str(raw)
                if pid not in preview:
                    continue
                before = preview[pid]
                try:
                    if field == 'multiplyPointtypeIsOn':
                        raw_value = ent.value.get(value_field, 1)
                        factor = eval_expr(str(raw_value), preview) if isinstance(raw_value, str) else float(raw_value or 0)
                        after = before * factor
                    elif field == 'dividePointtypeIsOn':
                        raw_value = ent.value.get(value_field, 1)
                        divisor = eval_expr(str(raw_value), preview) if isinstance(raw_value, str) else float(raw_value or 0)
                        after = before if divisor == 0 else before / divisor
                    else:
                        raw_value = ent.value.get(value_field, '0')
                        after = eval_expr(str(raw_value), preview) if isinstance(raw_value, str) else float(raw_value or 0)
                except (ValueError, KeyError, SyntaxError, ZeroDivisionError):
                    continue
                point = self.index.one(pid, 'point')
                if point and not point.value.get('allowFloat'):
                    after = float(math.floor(after))
                preview[pid] = after
                if point and point.value.get('belowZeroNotAllowed') and after < 0:
                    reasons.append(f'point {pid} would fall below zero ({after:g}) after point modification')
        return preview, reasons

    def _requirement_direct_result(self, req: dict[str, Any], path: str) -> bool:
        # ICC Plus ObjectRequired.svelte uses checkReq(required) for hideRequired.
        # That evaluates the requirement itself, while nested requireds are handled
        # separately as display prerequisites.
        return bool(self.req._one(req, self.state, path, []).result)

    def _requirement_shown_in_view(self, req: dict[str, Any], path: str) -> bool:
        if req.get('showRequired') is not True:
            return False
        result = True
        nested = req.get('requireds', [])
        nested_list = nested if isinstance(nested, list) else []
        if req.get('hideRequired2'):
            result, _ = self._requirements_met(nested_list, path + '/requireds')
        if req.get('hideRequired'):
            direct = self._requirement_direct_result(req, path)
            if nested_list:
                prereqs, _ = self._requirements_met(nested_list, path + '/requireds')
                result = prereqs and not direct
            else:
                result = not direct
        return bool(result)

    def _requirement_core_text(self, req: dict[str, Any]) -> str:
        typ = str(req.get('type', ''))
        if typ == 'id':
            raw = str(req.get('reqId', ''))
            ident, sep, count = raw.partition('/ON#')
            target = self._entity(ident)
            title = self._replace_text(target.value.get('title', '')) if target else ''
            if not title:
                return ''
            return f'{count} {title}' if sep else title
        if typ == 'points':
            point = self.index.one(str(req.get('reqId', '')), 'point')
            if not point:
                return ''
            return f"{req.get('reqPoints', 0)} {self._replace_text(point.value.get('name', ''))}"
        if typ == 'or':
            values = [self._requirement_core_text(x) for x in req.get('orRequireds', []) if isinstance(x, dict)] if isinstance(req.get('orRequireds'), list) else []
            values = [x for x in values if x]
            word = str(self.project.get('defaultOrReq', 'of'))
            need = req.get('orNum', 1)
            if str(self.project.get('orderOrReqText', '0')) == '1':
                return f"{', '.join(values)} {word} {need}".strip()
            return f"{need} {word} {', '.join(values)}".strip()
        if typ == 'selFromGroups':
            names = []
            for raw in req.get('selGroups', []) if isinstance(req.get('selGroups'), list) else []:
                group = self.index.one(str(raw), 'group')
                if group:
                    names.append(self._replace_text(group.value.get('name', '')))
            word = str(self.project.get('defaultOrReq', 'of'))
            need = req.get('selNum', 1)
            if str(self.project.get('orderSelReqText', '0')) == '1':
                return f"{', '.join(names)} {word} {need}".strip()
            return f"{need} {word} {', '.join(names)}".strip()
        if typ == 'selFromRows':
            names = []
            for raw in req.get('selRows', []) if isinstance(req.get('selRows'), list) else []:
                row = self.index.one(str(raw), 'row') or self.index.one(str(raw), 'backpack_row')
                if row:
                    names.append(self._replace_text(row.value.get('title', '')))
            word = str(self.project.get('defaultOrReq', 'of'))
            need = req.get('selNum', 1)
            if str(self.project.get('orderSelReqText', '0')) == '1':
                return f"{', '.join(names)} {word} {need}".strip()
            return f"{need} {word} {', '.join(names)}".strip()
        if typ == 'selFromWhole':
            word = str(self.project.get('defaultOrReq', 'of'))
            need = req.get('selNum', 1)
            if str(self.project.get('orderSelReqText', '0')) == '1':
                return f'{word} {need}'.strip()
            return f'{need} {word}'.strip()
        return ''

    def _requirement_text(self, req: dict[str, Any]) -> str:
        if req.get('customTextIsOn'):
            return self._replace_text(req.get('customText', ''))
        before = self._replace_text(req.get('beforeText', ''))
        core = self._requirement_core_text(req)
        after = self._replace_text(req.get('afterText', ''))
        return ' '.join(x for x in (before, core, after) if x).strip()

    def _visible_requirement_texts(self, requirements: Any, base_path: str) -> list[str]:
        if not isinstance(requirements, list):
            return []
        out: list[str] = []
        for i, req in enumerate(requirements):
            if not isinstance(req, dict):
                continue
            path = f'{base_path}/{i}'
            if not self._requirement_shown_in_view(req, path):
                continue
            if str(req.get('type', '')) == 'gid':
                global_req = self.index.one(str(req.get('reqId', '')), 'global_requirement')
                if global_req and isinstance(global_req.value.get('requireds'), list):
                    for child in global_req.value['requireds']:
                        if isinstance(child, dict) and child.get('showRequired') is True:
                            text = self._requirement_text(child)
                            if text:
                                out.append(text)
                continue
            text = self._requirement_text(req)
            if text:
                out.append(text)
        return out

    @staticmethod
    def _player_message(code: str, *, ok: bool = False) -> tuple[str, str]:
        # Player-facing output must never fall back to an internal event/status
        # message. New runtime codes therefore degrade to a generic safe message
        # until an explicit player wording is added here.
        normalized = 'player.unavailable' if code in {'visibility.hidden', 'entity.not_found'} else code
        safe_messages = {
            'player.unavailable': 'content is not available to the player in the current state',
            'requirements.unmet': 'requirements are not met',
            'requirements.invalid': 'requirements are malformed',
            'points.below_zero_not_allowed': 'selection would violate a Point Type that cannot go below zero',
            'deselection.forced': 'choice is forced active',
            'deselection.select_once': 'this choice cannot be deselected after selection',
            'deselection.not_active': 'choice is not active',
            'deselection.counter_decremented': 'selection count decreased',
            'deselection.deselected': 'deselected',
            'deselection.no_effect': 'deselection made no state change',
            'selection.not_selectable': 'this content cannot be selected directly',
            'selection.parent_cycle': 'selection cannot be completed',
            'selection.recursion_limit': 'selection cannot be completed',
            'selection.not_attempted': 'selection was not attempted',
            'selection.invalid': 'selection is not available',
            'selection.invalid_after_parent': 'selection is not available',
            'selection.already_active': 'choice is already selected',
            'selection.maximum_reached': 'maximum selection count reached',
            'selection.counter_incremented': 'selection count increased',
            'selection.no_effect': 'selection made no state change',
            'selection.processed': 'selection processed',
            'selection.selected': 'selected',
            'row.info': 'the parent row is informational',
            'row.capacity': 'the row has reached its selection limit',
            'row.replacement_failed': 'the row could not replace an existing selection',
            'addon.parent_missing': 'this Addon cannot be selected',
            'addon.parent_requirements_unmet': 'parent choice requirements are not met',
            'addon.parent_activation_failed': 'parent choice cannot be activated',
            'addon.parent_points': 'parent choice cannot be afforded',
            'row_button.not_found': 'row button is not available',
            'row_button.not_button': 'row button is not available',
            'row_button.unavailable': 'row button is not available in the current state',
            'row_button.disabled': 'row button is currently disabled',
            'row_button.pressed': 'row button pressed',
            'row_button.point_changed': 'row button pressed',
            'row_button.no_effect': 'row button made no state change',
        }
        return normalized, safe_messages.get(normalized, 'action completed' if ok else 'action is not available')

    def _player_semantic_errors(self, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Keep stable machine-readable codes when they do not distinguish hidden
        # from nonexistent content. Never echo raw internal messages or details.
        out: list[dict[str, Any]] = []
        for error in errors:
            code, message = self._player_message(str(error.get('code', '')), ok=False)
            out.append({'code': code, 'message': message})
        return out

    def player_event(self, event: Event | dict[str, Any]) -> dict[str, Any]:
        raw = event.to_dict() if isinstance(event, Event) else event
        ok = bool(raw.get('ok'))
        code, message = self._player_message(str(raw.get('code') or ''), ok=ok)
        out = {
            'action': str(raw.get('action', '')),
            'ok': ok,
            'code': code or None,
            'message': message,
        }
        target_key = 'row_id' if out['action'] == 'row_button' else 'choice_id'
        out[target_key] = str(raw.get('choice_id', ''))
        return out

    def player_action_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sanitize session action results for an LM acting only as the player.

        This deliberately drops snapshots, raw status traces, event details, and
        all continuation bookkeeping. A caller that needs continuation should
        keep runtime state in a file with ``session --state-out``.
        """
        out: list[dict[str, Any]] = []
        for item in results:
            action = str(item.get('action', ''))
            clean: dict[str, Any] = {'index': int(item.get('index', len(out))), 'action': action}
            if action in {'select', 'deselect', 'row_button'} and isinstance(item.get('event'), dict):
                clean['event'] = self.player_event(item['event'])
            elif action == 'view' and isinstance(item.get('view'), dict):
                clean['view'] = item['view']
            elif action == 'status' and isinstance(item.get('status'), dict):
                status = item['status']
                visible = bool(status.get('visible'))
                safe_status: dict[str, Any] = {
                    'id': str(status.get('id', '')),
                    'visible': visible,
                }
                if visible:
                    safe_status.update({
                        'active': bool(status.get('active')),
                        'count': int(status.get('count', 0) or 0),
                        'can_select': bool(status.get('selectable')),
                    })
                    errors = status.get('semantic_errors')
                    if isinstance(errors, list) and errors:
                        safe_status['selection_errors'] = self._player_semantic_errors([x for x in errors if isinstance(x, dict)])
                clean['status'] = safe_status
            elif action == 'reset':
                clean['ok'] = bool(item.get('ok', True))
            # snapshot is intentionally not representable in player-safe output.
            out.append(clean)
        return out

    def _score_visible_in_view(self, score: dict[str, Any], ent: Entity) -> bool:
        if score.get('showScore') is not True:
            return False
        point = self.index.one(str(score.get('id', '')), 'point')
        if point and point.value.get('isNotShownObjects'):
            gate = str(point.value.get('activatedId', '') or '')
            if not gate:
                return False
            global_req = self.index.one(gate, 'global_requirement')
            variable = self.index.one(gate, 'variable')
            if global_req:
                met, _ = self._requirements_met(global_req.value.get('requireds', []), global_req.path + '/requireds')
                if not met:
                    return False
            elif variable:
                if not self.state.variables.get(gate, False):
                    return False
            elif not self._active(gate):
                return False
        met, _ = self._requirements_met(score.get('requireds', []), ent.path + '/scores/requireds')
        return met

    def _score_view(self, score: dict[str, Any], ent: Entity) -> dict[str, Any]:
        pid = str(score.get('id', ''))
        point = self.index.one(pid, 'point')
        before = self._replace_text(score.get('beforeText', ''))
        after = self._replace_text(score.get('afterText', ''))
        value: Any
        if score.get('isRandom') and not score.get('setValue'):
            if score.get('useExpression'):
                value = {'random_expression': True, 'min': score.get('expMinValue'), 'max': score.get('expMaxValue')}
            else:
                value = {'random': True, 'min': score.get('minValue'), 'max': score.get('maxValue')}
        elif score.get('useExpression') and not score.get('setValue'):
            value = {'expression': score.get('expValue')}
        else:
            value = _clean_num(float(score.get('discountScore') if score.get('discountIsOn') and score.get('appliedDiscount') and score.get('discountScore') is not None else score.get('value', 0) or 0))
        out: dict[str, Any] = {
            'point_id': pid,
            'point_name': str(point.value.get('name') or pid) if point else pid,
            'value': value,
        }
        if before:
            out['before'] = before
        if after:
            out['after'] = after
        if score.get('multiplyByTimes'):
            out['multiply_by_times'] = True
            out['next_multiplier'] = abs(self._count(ent.id)) + 1
        return out

    def _deselect_status(self, ent: Entity, *, internal: bool = False) -> tuple[bool, list[dict[str, Any]]]:
        errors: list[dict[str, Any]] = []
        mode = self._multiple_mode(ent)
        can_cross_zero = mode == 'variable' and self._count(ent.id) == 0 and int(ent.value.get('numMultipleTimesMinus', 0) or 0) < 0
        if not self._active(ent.id) and not can_cross_zero:
            errors.append(self._semantic('deselection.not_active', f'{ent.id} is not active'))
            return False, errors
        if not internal and not self.entity_visible(ent.id):
            errors.append(self._semantic('visibility.hidden', f'{ent.id} is not visible to the player in the current state', id=ent.id))
        if not internal and ent.value.get('selectOnce'):
            errors.append(self._semantic('deselection.select_once', 'selectOnce prevents player deselection'))
        providers = self.state.forced_by.get(ent.id, set())
        if not internal and providers:
            errors.append(self._semantic('deselection.forced', f'choice is forced active by {sorted(providers)!r}', providers=sorted(providers)))
        return not errors, errors

    def _view_addon(
        self,
        ent: Entity,
        row: Entity,
        parent: Entity,
        *,
        verbose: bool,
        position: int | None = None,
    ) -> dict[str, Any]:
        value = ent.value
        out: dict[str, Any] = {
            'id': ent.id,
            'kind': ent.kind,
            'row_id': row.id,
            'choice_id': parent.id,
            'active': self._active(ent.id),
        }
        if position is not None:
            out['index'] = int(position)
        if not self._row_flag(row, 'addonTitleRemoved'):
            title = self._replace_text(value.get('title', ''))
            if title:
                out['title'] = title
        if not self._row_flag(row, 'addonTextRemoved'):
            description = self._replace_text(value.get('text', ''))
            if description:
                out['description'] = description
        if ent.kind == 'selectable_addon':
            status = self.choice_status(ent.id)
            out['count'] = self._count(ent.id)
            out['can_select'] = status.selectable
            can_deselect, de_errors = self._deselect_status(ent)
            out['can_deselect'] = can_deselect
            if verbose:
                if status.semantic_errors:
                    out['selection_errors'] = self._player_semantic_errors(status.semantic_errors)
                if de_errors and self._active(ent.id):
                    out['deselection_errors'] = self._player_semantic_errors(de_errors)
                if not self._row_flag(row, 'objectScoreRemoved'):
                    scores = [self._score_view(s, ent) for s in value.get('scores', []) if isinstance(s, dict) and self._score_visible_in_view(s, ent)]
                    if scores:
                        out['scores'] = scores
                if not self._row_flag(row, 'objectRequirementRemoved'):
                    requirements = self._visible_requirement_texts(value.get('requireds', []), ent.path + '/requireds')
                    if requirements:
                        out['requirements'] = requirements
        return out

    def _view_choice(
        self,
        ent: Entity,
        row: Entity,
        *,
        verbose: bool,
        position: int | None = None,
    ) -> dict[str, Any]:
        value = ent.value
        status = self.choice_status(ent.id)
        out: dict[str, Any] = {
            'id': ent.id,
            'kind': 'choice',
            'row_id': row.id,
            'active': self._active(ent.id),
            'count': self._count(ent.id),
            'can_select': status.selectable,
        }
        if position is not None:
            out['index'] = int(position)
        can_deselect, de_errors = self._deselect_status(ent)
        out['can_deselect'] = can_deselect
        if not self._row_flag(row, 'objectTitleRemoved'):
            title = self._replace_text(value.get('title', ''))
            if title:
                out['title'] = title
        if not self._row_flag(row, 'objectTextRemoved'):
            description = self._replace_text(value.get('text', ''))
            if description:
                out['description'] = description
        addons: list[dict[str, Any]] = []
        for addon in self.index.by_kind.get('addon', []) + self.index.by_kind.get('selectable_addon', []):
            if addon.parent_id == ent.id and self._addon_visible(addon):
                addons.append(self._view_addon(addon, row, ent, verbose=verbose, position=len(addons)))
        out['addon_ids'] = [addon['id'] for addon in addons]
        out['selectable_addon_ids'] = [addon['id'] for addon in addons if addon.get('kind') == 'selectable_addon']
        out['informational_addon_ids'] = [addon['id'] for addon in addons if addon.get('kind') == 'addon']
        if addons:
            out['addons'] = addons
        if verbose:
            if status.semantic_errors:
                out['selection_errors'] = self._player_semantic_errors(status.semantic_errors)
            if de_errors and self._active(ent.id):
                out['deselection_errors'] = self._player_semantic_errors(de_errors)
            if not self._row_flag(row, 'objectScoreRemoved') and not value.get('showScoreInAddon'):
                scores = [self._score_view(s, ent) for s in value.get('scores', []) if isinstance(s, dict) and self._score_visible_in_view(s, ent)]
                if scores:
                    out['scores'] = scores
            if not self._row_flag(row, 'objectRequirementRemoved') and not value.get('showReqInAddon'):
                requirements = self._visible_requirement_texts(value.get('requireds', []), ent.path + '/requireds')
                if requirements:
                    out['requirements'] = requirements
        return out

    def _point_bar_visible(self, point: Entity) -> bool:
        if not point.value.get('isNotShownPointBar'):
            return True
        gate = str(point.value.get('activatedId', '') or '')
        if not gate:
            return False
        global_req = self.index.one(gate, 'global_requirement')
        if global_req:
            met, _ = self._requirements_met(global_req.value.get('requireds', []), global_req.path + '/requireds')
            return met
        variable = self.index.one(gate, 'variable')
        if variable:
            return bool(self.state.variables.get(gate, False))
        return self._activation_ref_met(gate)

    def player_view(self, *, verbose: bool = False, include_backpack: bool = False) -> dict[str, Any]:
        """Return a script-friendly representation of what the Viewer currently exposes.

        Rows, direct Choices, and Addons are exposed as distinct visible entity lists,
        with explicit parent/child IDs. The legacy nested ``rows[].choices`` shape is
        retained for compatibility. Images and layout/CSS are intentionally omitted.
        Hidden rows, hidden choices, and hidden Addons are absent rather than listed as
        inaccessible content. Ordering indices are relative to the visible entities and
        therefore do not reveal hidden project positions.
        """
        point_view = []
        for point in self.index.by_kind.get('point', []):
            if not self._point_bar_visible(point):
                continue
            point_view.append({
                'id': point.id,
                'name': str(point.value.get('name') or point.id),
                'value': _clean_num(self.state.points.get(point.id, 0.0)),
            })

        flat_choices: list[dict[str, Any]] = []
        flat_addons: list[dict[str, Any]] = []

        def rows_of(kind: str) -> list[dict[str, Any]]:
            rows: list[dict[str, Any]] = []
            for row in self.index.by_kind.get(kind, []):
                if not self._row_visible(row):
                    continue
                row_out: dict[str, Any] = {
                    'id': row.id,
                    'kind': kind,
                    'index': len(rows),
                    'current_choices': int(self.state.row_counts.get(row.id, 0)),
                    'allowed_choices': self._row_allowed(row),
                }
                title = self._replace_text(row.value.get('title', ''))
                if title:
                    row_out['title'] = title
                if not self._row_flag(row, 'textIsRemoved'):
                    description = self._replace_text(row.value.get('titleText', ''))
                    if description:
                        row_out['description'] = description
                choices: list[dict[str, Any]] = []
                for choice in self.index.by_kind.get('choice', []):
                    if choice.row_id == row.id and self._choice_visible(choice):
                        choice_view = self._view_choice(choice, row, verbose=verbose, position=len(choices))
                        choices.append(choice_view)
                        flat_choices.append(choice_view)
                        flat_addons.extend(choice_view.get('addons', []))
                choice_ids = [choice['id'] for choice in choices]
                row_out['choice_ids'] = choice_ids
                row_out['selected_choice_ids'] = [choice['id'] for choice in choices if choice.get('active')]
                row_out['available_choice_ids'] = [choice['id'] for choice in choices if choice.get('can_select')]
                row_out['deselectable_choice_ids'] = [choice['id'] for choice in choices if choice.get('can_deselect')]
                # Compatibility surface: verbose views keep full nested Choice objects;
                # compact views keep the historical list of Choice IDs.
                row_out['choices'] = choices if verbose else choice_ids
                rows.append(row_out)
            return rows

        rows = rows_of('row')
        backpack_rows = rows_of('backpack_row') if include_backpack else []

        visible_selectables = [ent for ent in self.index.selectables(include_backpack=include_backpack) if self.entity_visible(ent.id)]
        available_selection_ids: list[str] = []
        deselectable_selection_ids: list[str] = []
        available_direct_choice_ids: list[str] = []
        deselectable_direct_choice_ids: list[str] = []
        available_selectable_addon_ids: list[str] = []
        deselectable_selectable_addon_ids: list[str] = []
        for ent in visible_selectables:
            status = self.choice_status(ent.id)
            if status.visible and status.selectable:
                available_selection_ids.append(ent.id)
                if ent.kind == 'choice':
                    available_direct_choice_ids.append(ent.id)
                elif ent.kind == 'selectable_addon':
                    available_selectable_addon_ids.append(ent.id)
            can_deselect, _ = self._deselect_status(ent)
            if can_deselect:
                deselectable_selection_ids.append(ent.id)
                if ent.kind == 'choice':
                    deselectable_direct_choice_ids.append(ent.id)
                elif ent.kind == 'selectable_addon':
                    deselectable_selectable_addon_ids.append(ent.id)

        selected_ids = [x for x in self.state.selected_order if self._active(x) and self.entity_visible(x)]
        visible_choice_ids = [choice['id'] for choice in flat_choices]
        visible_addon_ids = [addon['id'] for addon in flat_addons]
        visible_selectable_addon_ids = [addon['id'] for addon in flat_addons if addon.get('kind') == 'selectable_addon']
        visible_informational_addon_ids = [addon['id'] for addon in flat_addons if addon.get('kind') == 'addon']
        visible_choice_set = set(visible_choice_ids)
        visible_selectable_addon_set = {
            addon['id'] for addon in flat_addons if addon.get('kind') == 'selectable_addon'
        }

        out: dict[str, Any] = {
            'mode': 'player_view',
            'verbose': bool(verbose),
            'points': point_view,
            'row_ids': [row['id'] for row in rows],
            'choice_ids': visible_choice_ids,
            'addon_ids': visible_addon_ids,
            'selectable_addon_ids': visible_selectable_addon_ids,
            'informational_addon_ids': visible_informational_addon_ids,
            'rows': rows,
            'choices': flat_choices,
            'addons': flat_addons,
            'selected_ids': selected_ids,
            'selected_choice_ids': [x for x in selected_ids if x in visible_choice_set],
            'selected_selectable_addon_ids': [x for x in selected_ids if x in visible_selectable_addon_set],
            # These two names are the historical compatibility aliases. They have
            # always included selectable Addons as well as direct Choices.
            'available_choice_ids': available_selection_ids,
            'deselectable_choice_ids': deselectable_selection_ids,
            # New explicit names distinguish all selectable entities from direct
            # Choices and selectable Addons without changing the old contract.
            'available_selection_ids': available_selection_ids,
            'deselectable_selection_ids': deselectable_selection_ids,
            'available_direct_choice_ids': available_direct_choice_ids,
            'deselectable_direct_choice_ids': deselectable_direct_choice_ids,
            'available_selectable_addon_ids': available_selectable_addon_ids,
            'deselectable_selectable_addon_ids': deselectable_selectable_addon_ids,
        }
        if include_backpack:
            out['backpack_row_ids'] = [row['id'] for row in backpack_rows]
            out['backpack'] = backpack_rows
        return out

    def _rollback_event(self, before: RuntimeState, rng_state: object, action: str, ident: str, message: str, *, code: str, details: dict[str, Any] | None = None) -> Event:
        self.state = before
        self.rng.setstate(rng_state)
        event = Event(action, ident, False, message, details or {}, code)
        self.state.events.append(event)
        return event

    def _row_button_choices(self, row: Entity) -> list[Entity]:
        return [x for x in self.index.by_kind.get('choice', []) if x.row_id == row.id]

    def _row_button_valid_choices(self, row: Entity) -> list[Entity]:
        out: list[Entity] = []
        for choice in self._row_button_choices(row):
            met, _ = self._requirements_met(choice.value.get('requireds', []), choice.path + '/requireds')
            if not met:
                continue
            if choice.value.get('isNotSelectable') and not row.value.get('allowActivateUnselectable'):
                continue
            if self._active(choice.id) and row.value.get('onlyUnselectedChoices'):
                continue
            out.append(choice)
        return out

    def _row_button_toggle_choice(self, choice: Entity, row: Entity, dialogs: dict[str, dict[str, Any]] | None = None) -> Event:
        if choice.value.get('isSelectableMultiple') and choice.value.get('isMultipleUseVariable') and choice.value.get('numMultipleTimesPluss'):
            maximum = int(choice.value.get('numMultipleTimesPluss') or 0)
            if maximum > self._count(choice.id):
                return self.select(choice.id, _internal=True, _dialogs=dialogs)
            return self.deselect(choice.id, reason=f'row button {row.id} random toggle', _internal=True)
        if self._active(choice.id):
            return self.deselect(choice.id, reason=f'row button {row.id} random toggle', _internal=True)
        return self.select(choice.id, _internal=True, _dialogs=dialogs)

    def press_row_button(self, row_id: str, *, dialogs: dict[str, dict[str, Any]] | None = None) -> Event:
        """Press an ICC Plus Row button using Viewer 2.10.6 buttonActivate rules."""
        before = self.state.clone()
        rng_before = self.rng.getstate()
        row = self.index.one(row_id, 'row') or self.index.one(row_id, 'backpack_row')
        if not row:
            return self._rollback_event(before, rng_before, 'row_button', row_id, 'row not found', code='row_button.not_found')
        if not row.value.get('isButtonRow'):
            return self._rollback_event(before, rng_before, 'row_button', row_id, 'row is not a button row', code='row_button.not_button')
        met, _ = self._requirements_met(row.value.get('requireds', []), row.path + '/requireds')
        if not met:
            return self._rollback_event(before, rng_before, 'row_button', row_id, 'row button is not available because row requirements are unmet', code='row_button.unavailable')
        if row.value.get('onlyIfNoChoices') and self.state.row_counts.get(row.id, 0) != 0:
            return self._rollback_event(before, rng_before, 'row_button', row_id, 'row button is disabled while the row has selected choices', code='row_button.disabled')

        button_id = row.value.get('buttonId')
        if not row.value.get('buttonType') and isinstance(button_id, str) and button_id in self.state.activations:
            return self._rollback_event(before, rng_before, 'row_button', row_id, 'row button is disabled while its target Variable is active', code='row_button.disabled')

        if row.value.get('btnPointAddon') and row.value.get('buttonTypeRadio') == 'sumaddon' and isinstance(row.value.get('pointTypeRandom'), str):
            point_id = str(row.value.get('pointTypeRandom'))
            point = self.index.one(point_id, 'point')
            if not point or point_id not in self.state.points:
                event = Event('row_button', row_id, True, 'row button made no state change', {'point_id': point_id}, 'row_button.no_effect')
                self.state.events.append(event)
                return event
            rnd_max = float(row.value.get('randomMax', 0) or 0)
            rnd_min = float(row.value.get('randomMin', 0) or 0)
            amount = math.floor(self.rng.random() * (rnd_max - rnd_min) + rnd_min)
            if point.value.get('belowZeroNotAllowed') and self.state.points[point_id] + amount < 0:
                event = Event('row_button', row_id, True, 'random Point result was blocked by belowZeroNotAllowed', {'point_id': point_id, 'amount': amount}, 'row_button.no_effect')
                self.state.events.append(event)
                return event
            self.state.points[point_id] += amount
            previous = self.state.row_button_random_points.get(row.id)
            previous_total = int(previous[1]) if previous else 0
            self.state.row_button_random_points[row.id] = (point_id, previous_total + amount)
            self._build_order_add(row.id)
            self._cleanup_unmet(row.id, 0)
            event = Event('row_button', row_id, True, 'row button changed a Point Type', {
                'point_id': point_id,
                'amount': amount,
                'point_value': _clean_num(self.state.points[point_id]),
            }, 'row_button.point_changed')
            self.state.events.append(event)
            return event

        if row.value.get('buttonRandom'):
            raw_num = row.value.get('buttonRandomNumber')
            if not isinstance(raw_num, (int, float)) or isinstance(raw_num, bool):
                event = Event('row_button', row_id, True, 'row button has no random-choice count', {}, 'row_button.no_effect')
                self.state.events.append(event)
                return event
            iterations = max(0, math.ceil(float(raw_num)))
            changed: list[str] = []
            if row.value.get('isWeightedRandom'):
                valid = self._row_button_valid_choices(row)
                if not valid:
                    event = Event('row_button', row_id, True, 'row button had no eligible choices', {}, 'row_button.no_effect')
                    self.state.events.append(event)
                    return event
                weights = [float(choice.value.get('randomWeight') or 100) for choice in valid]
                total = sum(weights)
                for _ in range(iterations):
                    rnd = math.floor(self.rng.random() * total) if total else 0
                    running = 0.0
                    for choice, weight in zip(valid, weights):
                        running += weight
                        if rnd < running:
                            before_count = self._count(choice.id) if self._active(choice.id) else None
                            event = self._row_button_toggle_choice(choice, row, dialogs)
                            after_count = self._count(choice.id) if self._active(choice.id) else None
                            if event.ok and before_count != after_count:
                                changed.append(choice.id)
                            break
            else:
                selected_indexes: list[int] = []
                for _ in range(iterations):
                    valid = self._row_button_valid_choices(row)
                    if not valid:
                        break
                    index = math.floor(self.rng.random() * len(valid))
                    if index in selected_indexes:
                        continue
                    selected_indexes.append(index)
                    choice = valid[index]
                    before_count = self._count(choice.id) if self._active(choice.id) else None
                    event = self._row_button_toggle_choice(choice, row, dialogs)
                    after_count = self._count(choice.id) if self._active(choice.id) else None
                    if event.ok and before_count != after_count:
                        changed.append(choice.id)
            event = Event('row_button', row_id, True, 'row random-choice button processed', {'changed_ids': changed}, 'row_button.pressed' if changed else 'row_button.no_effect')
            self.state.events.append(event)
            return event

        if isinstance(button_id, str):
            variable = self.index.one(button_id, 'variable')
            if variable:
                if button_id in self.state.activations:
                    if row.value.get('buttonType'):
                        self.state.variables[button_id] = False
                        self.state.activations.pop(button_id, None)
                        self._build_order_remove(button_id)
                else:
                    self.state.variables[button_id] = True
                    self.state.activations[button_id] = 0
                    self._build_order_add(button_id)
                event = Event('row_button', row_id, True, 'row Variable button processed', {'variable_id': button_id, 'value': self.state.variables.get(button_id, False)}, 'row_button.pressed')
                self.state.events.append(event)
                return event

        event = Event('row_button', row_id, True, 'row button made no state change', {}, 'row_button.no_effect')
        self.state.events.append(event)
        return event

    def select(
        self,
        ident: str,
        *,
        times: int = 1,
        force: bool = False,
        source: str | None = None,
        word: str | None = None,
        image: str | None = None,
        confirm: bool | None = None,
        dialogs: dict[str, dict[str, Any]] | None = None,
        _dialogs: dict[str, dict[str, Any]] | None = None,
        _depth: int = 0,
        _internal: bool = False,
    ) -> Event:
        if isinstance(times, bool) or not isinstance(times, int) or times < 1:
            raise ValueError('times must be an integer >= 1')
        if not isinstance(force, bool):
            raise ValueError('force must be a boolean')
        if source is not None and not isinstance(source, str):
            raise ValueError('source must be a string or null')
        if word is not None and not isinstance(word, str):
            raise ValueError('word must be a string or null')
        if image is not None and not isinstance(image, str):
            raise ValueError('image must be a string or null')
        if confirm is not None and not isinstance(confirm, bool):
            raise ValueError('confirm must be a boolean or null')
        if dialogs is not None and _dialogs is not None:
            raise ValueError('dialogs and _dialogs cannot both be supplied')
        active_dialogs = _dialogs if _dialogs is not None else self._validate_dialog_responses(dialogs, label='dialogs')
        target_response = dict(active_dialogs.get(ident, {}))
        if word is not None:
            target_response['word'] = word
        if image is not None:
            target_response['image'] = image
        if confirm is not None:
            target_response['confirm'] = confirm

        before = self.state.clone()
        rng_before = self.rng.getstate()
        if _depth > 30:
            return self._rollback_event(before, rng_before, 'select', ident, 'effect recursion limit reached', code='selection.recursion_limit')

        last = Event('select', ident, False, 'no selection attempted', code='selection.not_attempted')
        for _ in range(max(1, times)):
            ent = self._entity(ident)
            if not ent:
                return self._rollback_event(before, rng_before, 'select', ident, 'choice/selectable addon not found or ambiguous', code='entity.not_found')
            if word is not None and not ent.value.get('customTextfieldIsOn'):
                return self._rollback_event(before, rng_before, 'select', ident, 'word input was supplied but this choice has no custom text dialog', code='interaction.word_not_supported')
            if image is not None and not ent.value.get('isImageUpload'):
                return self._rollback_event(before, rng_before, 'select', ident, 'image input was supplied but this choice has no player image upload', code='interaction.image_not_supported')
            if confirm is not None and not ent.value.get('confirmIsOn'):
                return self._rollback_event(before, rng_before, 'select', ident, 'confirmation input was supplied but this choice has no confirmation dialog', code='interaction.confirm_not_supported')
            status = self.choice_status(ident, internal=_internal)
            if not status.selectable:
                code = status.semantic_errors[0]['code'] if status.semantic_errors else 'selection.invalid'
                return self._rollback_event(
                    before, rng_before, 'select', ident, '; '.join(status.reasons) or 'selection is not valid',
                    code=code, details={'status': status.to_dict(), 'forced': force, 'internal': _internal},
                )

            parent = self.index.parent_choice(ent)
            if parent and not self._active(parent.id):
                p_event = self.select(parent.id, force=force, source=ident, _depth=_depth + 1, _internal=True, _dialogs=active_dialogs)
                if not p_event.ok or not self._active(parent.id):
                    return self._rollback_event(
                        before, rng_before, 'select', ident, f'parent choice {parent.id} could not be internally activated',
                        code='addon.parent_activation_failed', details={'parent_event': p_event.to_dict()},
                    )

            status = self.choice_status(ident, internal=_internal)
            if not status.selectable:
                code = status.semantic_errors[0]['code'] if status.semantic_errors else 'selection.invalid_after_parent'
                return self._rollback_event(
                    before, rng_before, 'select', ident, '; '.join(status.reasons) or 'selection became invalid',
                    code=code, details={'status': status.to_dict(), 'after_parent_activation': True},
                )

            for victim in status.would_deselect:
                victim_ent = self._entity(victim)
                events: list[Event] = []
                if victim_ent and victim_ent.value.get('isSelectableMultiple'):
                    # Viewer loops over the repeat count captured before the loop
                    # and calls selectedOneLess that many times. This fully clears
                    # positive repeatables instead of removing only one step.
                    counter = self._count(victim)
                    for _ in range(max(0, counter)):
                        events.append(self.deselect(victim, reason=f'row capacity replacement by {ident}', _depth=_depth + 1, _internal=True))
                        if not self._active(victim):
                            break
                else:
                    events.append(self.deselect(victim, reason=f'row capacity replacement by {ident}', _depth=_depth + 1, _internal=True))
                event = events[-1] if events else Event('deselect', victim, False, 'row-capacity replacement made no progress', code='row.replacement_failed')
                if self._active(victim):
                    return self._rollback_event(
                        before, rng_before, 'select', ident, f'row-capacity replacement could not deselect {victim}',
                        code='row.replacement_failed', details={'victim_event': event.to_dict()},
                    )

            mode = self._multiple_mode(ent)
            was_active_before_step = self._active(ent.id)
            selected_word: str | None = None
            # Viewer opens custom-word and confirmation dialogs for ordinary
            # selectObject calls and variable-backed selectedOneMore calls. The
            # custom-word dialog only appears on the first activation, while the
            # confirmation dialog appears for every repeat increment.
            if mode in {None, 'variable'}:
                if ent.value.get('customTextfieldIsOn') and not was_active_before_step:
                    selected_word = str(target_response.get(
                        'word', self.state.custom_words.get(ent.id, ent.value.get('wordChangeSelect', '') or '')
                    ))
                if ent.value.get('confirmIsOn') and target_response.get('confirm') is False and not force:
                    last = Event('select', ident, True, 'selection cancelled in confirmation dialog', {
                        'internal': _internal, 'active_after': self._active(ent.id),
                    }, 'selection.cancelled')
                    self.state.events.append(last)
                    return last

            if mode == 'point':
                pid = str(ent.value.get('multipleScoreId'))
                point = self.index.one(pid, 'point')
                changed = False
                if point and pid in self.state.points:
                    maximum = float(ent.value.get('numMultipleTimesPluss', 0) or 0)
                    if maximum > self.state.points[pid]:
                        self.state.points[pid] += 1
                        changed = True
                last = Event('select', ident, True, 'point-backed counter incremented' if changed else 'point-backed counter unchanged', {
                    'point_id': pid, 'point_value': _clean_num(self.state.points.get(pid, 0)), 'internal': _internal,
                }, 'selection.counter_incremented' if changed else 'selection.no_effect')
                self.state.events.append(last)
                continue
            if mode == 'none':
                # ICC Plus renders the multiple counter, but selectedOneMore has no
                # applicable branch when neither repeat mode is configured.
                last = Event('select', ident, True, 'multiple counter has no configured repeat mode; no state change', {
                    'count': self._count(ent.id), 'internal': _internal,
                }, 'selection.no_effect')
                self.state.events.append(last)
                continue

            current = self._count(ent.id)
            if mode == 'variable':
                maximum = int(ent.value.get('numMultipleTimesPluss', self.project.get('defaultChoiceMaxNum', 99)) or 0)
                if current >= maximum:
                    last = Event('select', ident, True, 'multiple-selection maximum reached; no state change', {'count': current, 'maximum': maximum}, 'selection.no_effect')
                    self.state.events.append(last)
                    continue

            was_active = self._active(ent.id)
            if mode == 'variable':
                new_count = current + 1
                if new_count == 0:
                    self.state.activations.pop(ent.id, None)
                else:
                    self.state.activations[ent.id] = new_count
            else:
                self.state.activations[ent.id] = 0
            is_active = self._active(ent.id)

            if not was_active and is_active:
                self.state.selected_order.append(ent.id)
                self._build_order_add(ent.id)
                if self._counts_for_row(ent):
                    self.state.row_counts[ent.row_id or ''] = self.state.row_counts.get(ent.row_id or '', 0) + 1
            elif was_active and not is_active:
                self.state.selected_order = [x for x in self.state.selected_order if x != ent.id]
                self._build_order_remove(ent.id)
                if self._counts_for_row(ent):
                    self.state.row_counts[ent.row_id or ''] = max(0, self.state.row_counts.get(ent.row_id or '', 0) - 1)

            self._set_variables(ent, True, first=not was_active and is_active)
            self._apply_scores(ent)
            duplicated_row = None
            if mode is None or current >= 0:
                duplicated_row = self._duplicate_row_effect(ent)
            # Viewer applies addToAllowChoice on every selectedOneMore step.
            self._change_allowed(ent, +1)

            self_deactivate: int | None = None
            # For an ordinary selectObject, ICC Plus processes linked activation,
            # deactivation, and requirement cleanup *before* point modifiers. This
            # ordering matters when replacing an active point-setting preset: the
            # old preset is reverted first, then the new preset is applied.
            # Negative repeat counts moving toward zero do not run linked choice
            # activation/deactivation in selectedOneMore.
            if mode is None or current >= 0:
                self._force_activate_targets(ent, _depth, active_dialogs)
                self_deactivate = self._deactivate_targets(ent, _depth)
            self._cleanup_unmet(ent.id, _depth)

            if not was_active and is_active:
                # Point multiply/divide/set functions belong to selectObject and
                # are deliberately absent from selectedOneMore.
                if mode is None:
                    self._apply_point_effects(ent)
                self._change_hidden_content(ent, True)
                self._change_show_all_addons(ent, +1)
                word_id = ent.value.get('idOfTheTextfieldWord')
                if ent.value.get('textfieldIsOn') and isinstance(word_id, str) and word_id in self.state.words:
                    if ent.value.get('customTextfieldIsOn'):
                        if selected_word is None:
                            selected_word = self.state.custom_words.get(ent.id, str(ent.value.get('wordChangeSelect', '') or ''))
                        self.state.custom_words[ent.id] = selected_word
                        self.state.words[word_id] = selected_word
                    else:
                        self.state.words[word_id] = str(ent.value.get('wordChangeSelect', ''))
                if ent.value.get('isImageUpload') and 'image' in target_response:
                    uploaded = target_response.get('image')
                    if isinstance(uploaded, str) and uploaded != str(ent.value.get('image', '') or ''):
                        self.state.uploaded_images[ent.id] = uploaded
                    else:
                        self.state.uploaded_images.pop(ent.id, None)

            met, traces = self.req.evaluate(ent.value.get('requireds', []), self.state, ent.path + '/requireds')
            if not met and self._active(ent.id):
                # Viewer re-checks after effects and actively deselects the item;
                # it does not roll the click back as an error transaction.
                self.deselect(ent.id, reason='requirements became unmet after selection', _depth=_depth + 1, force_cleanup=True, _internal=True)

            if self_deactivate is not None and self._active(ent.id):
                if mode == 'variable':
                    if self_deactivate > 0:
                        for _ in range(self_deactivate):
                            if not self._active(ent.id):
                                break
                            self.deselect(ent.id, reason='self-deactivation', _depth=_depth + 1, force_cleanup=True, _internal=True)
                else:
                    self.deselect(ent.id, reason='self-deactivation', _depth=_depth + 1, force_cleanup=True, _internal=True)

            final_active = self._active(ent.id)
            last = Event('select', ident, True, 'selected' if final_active else 'selection processed; entity is not active', {
                'count': self._count(ent.id), 'forced': force, 'source': source, 'internal': _internal,
                'would_deselect': status.would_deselect, 'unsupported_effects': status.unsupported_effects,
                'duplicated_row': duplicated_row,
                'active_after': final_active,
            }, 'selection.selected' if final_active else 'selection.processed')
            self.state.events.append(last)
        return last

    def _maybe_deselect_parent_after_addon(self, ent: Entity, depth: int) -> None:
        """Mirror Viewer selectable-Addon parent cleanup after the Addon becomes inactive."""
        parent = self.index.parent_choice(ent)
        if not parent or self._active(ent.id) or not self._active(parent.id):
            return

        should_deselect = bool(ent.value.get('deselectParent'))
        if parent.value.get('deselectWhenNoAddon'):
            active_addons = 0
            for addon in self.index.by_kind.get('selectable_addon', []):
                if addon.parent_id == parent.id and self._active(addon.id):
                    active_addons += 1
            if active_addons == 0:
                should_deselect = True

        if not should_deselect:
            return

        if self._multiple_mode(parent) == 'variable':
            count = self._count(parent.id)
            # Viewer captures the parent count and walks it back to zero.
            if count > 0:
                for _ in range(count):
                    if not self._active(parent.id):
                        break
                    self.deselect(parent.id, reason=f'addon {ent.id} deselected parent', _depth=depth + 1, _internal=True)
            elif count < 0:
                for _ in range(abs(count)):
                    if not self._active(parent.id):
                        break
                    self.select(parent.id, force=True, source=ent.id, _depth=depth + 1, _internal=True)
        else:
            self.deselect(parent.id, reason=f'addon {ent.id} deselected parent', _depth=depth + 1, _internal=True)

    def _token_target(self, token: str) -> tuple[str, int]:
        if '/ON#' in token:
            ident, raw = token.split('/ON#', 1)
            parsed = parse_int(raw)
            return ident, 0 if parsed is None else parsed
        return token, 0

    def _provider_still_targets(self, source: Entity, target: str, *, remaining_count: int) -> bool:
        if remaining_count <= 0:
            return False
        if source.value.get('isActivateRandom'):
            for step in self.state.random_activation_ledger.get(source.id, []):
                if any(self._token_target(token)[0] == target for token in step):
                    return True
            return False
        # Non-random repeat selections run the same activation list on every
        # positive selectedOneMore step. If the source remains positive, it is
        # still a provider for every configured target.
        return any(ident == target for ident, _ in self._targets(source.value.get('activateThisChoice')))

    def _undo_activation_token(self, source: Entity, token: str, depth: int, *, remaining_count: int) -> None:
        target, num = self._token_target(token)
        target_ent = self._entity(target)
        if not target_ent:
            return
        if target_ent.value.get('isSelectableMultiple'):
            if num > 0 and not source.value.get('isNotDeactivate'):
                for _ in range(num):
                    if not self._active(target):
                        break
                    self.deselect(target, reason=f'activation provider {source.id} was decremented', _depth=depth + 1, force_cleanup=True, _internal=True)
            return

        still = self._provider_still_targets(source, target, remaining_count=remaining_count)
        if not still:
            providers = self.state.activated_by.get(target)
            if providers is not None:
                providers.discard(source.id)
                if not providers:
                    self.state.activated_by.pop(target, None)
            forced = self.state.forced_by.get(target)
            if forced is not None:
                forced.discard(source.id)
                if not forced:
                    self.state.forced_by.pop(target, None)
        if not source.value.get('isNotDeactivate') and not self.state.activated_by.get(target) and self._active(target):
            self.deselect(target, reason=f'activation provider {source.id} was deselected', _depth=depth + 1, force_cleanup=True, _internal=True)

    def _undo_activation_step(self, source: Entity, depth: int, *, current_count: int | None = None) -> None:
        if not source.value.get('activateOtherChoice'):
            return
        remaining_count = 0 if current_count is None else max(0, current_count - 1)
        tokens: list[str] = []
        if source.value.get('isActivateRandom'):
            history = self.state.random_activation_ledger.get(source.id, [])
            if history:
                index = 0 if current_count is None else abs(current_count - 1)
                if 0 <= index < len(history):
                    tokens = list(history[index])
                    history.pop(index)
                elif current_count is None:
                    tokens = list(history[-1])
                    history.pop()
                if not history:
                    self.state.random_activation_ledger.pop(source.id, None)
        else:
            # Upstream builds a Map on deselection, so duplicate/overlapping
            # targets collapse to one target with the last force count.
            dedup: dict[str, int | None] = {}
            for target, num in self._targets(source.value.get('activateThisChoice')):
                dedup[target] = num
            tokens = [f'{target}/ON#{num}' if num is not None else target for target, num in dedup.items()]
        for token in tokens:
            self._undo_activation_token(source, token, depth, remaining_count=remaining_count)

    def _release_activation_provider(self, ent: Entity, depth: int) -> None:
        if ent.value.get('activateOtherChoice'):
            return
        targets: set[str] = set()
        for target, provider_set in list(self.state.activated_by.items()):
            if ent.id not in provider_set:
                continue
            provider_set.discard(ent.id)
            targets.add(target)
            if not provider_set:
                self.state.activated_by.pop(target, None)
        for target, provider_set in list(self.state.forced_by.items()):
            if ent.id in provider_set:
                provider_set.discard(ent.id)
                if not provider_set:
                    self.state.forced_by.pop(target, None)
        if not ent.value.get('isNotDeactivate'):
            for target in targets:
                if target not in self.state.activated_by and self._active(target):
                    self.deselect(target, reason=f'activation provider {ent.id} was deselected', _depth=depth + 1, force_cleanup=True, _internal=True)

    def deselect(
        self,
        ident: str,
        *,
        reason: str | None = None,
        dialog_action: str = 'deselect',
        word: str | None = None,
        image: str | None = None,
        _depth: int = 0,
        force_cleanup: bool = False,
        _internal: bool = False,
    ) -> Event:
        if reason is not None and not isinstance(reason, str):
            raise ValueError('reason must be a string or null')
        if dialog_action not in {'deselect', 'accept', 'cancel'}:
            raise ValueError('dialog_action must be deselect, accept, or cancel')
        if word is not None and not isinstance(word, str):
            raise ValueError('word must be a string or null')
        if image is not None and not isinstance(image, str):
            raise ValueError('image must be a string or null')
        before = self.state.clone()
        rng_before = self.rng.getstate()
        ent = self._entity(ident)
        if not ent:
            return self._rollback_event(before, rng_before, 'deselect', ident, 'choice/selectable addon not found or ambiguous', code='entity.not_found')

        mode = self._multiple_mode(ent)
        if mode == 'point':
            if not (_internal or force_cleanup) and ent.value.get('selectOnce'):
                return self._rollback_event(before, rng_before, 'deselect', ident, 'selectOnce prevents player decrement', code='deselection.select_once')
            pid = str(ent.value.get('multipleScoreId'))
            point = self.index.one(pid, 'point')
            changed = False
            if point and pid in self.state.points:
                minimum = float(ent.value.get('numMultipleTimesMinus', 0) or 0)
                if self.state.points[pid] > minimum:
                    self.state.points[pid] -= 1
                    changed = True
            event = Event('deselect', ident, True, 'point-backed counter decremented' if changed else 'point-backed counter unchanged', {
                'point_id': pid, 'point_value': _clean_num(self.state.points.get(pid, 0)), 'internal': _internal,
            }, 'deselection.counter_decremented' if changed else 'deselection.no_effect')
            self.state.events.append(event)
            return event
        if mode == 'none':
            if not (_internal or force_cleanup) and ent.value.get('selectOnce'):
                return self._rollback_event(before, rng_before, 'deselect', ident, 'selectOnce prevents player decrement', code='deselection.select_once')
            event = Event('deselect', ident, True, 'multiple counter has no configured repeat mode; no state change', {'internal': _internal}, 'deselection.no_effect')
            self.state.events.append(event)
            return event

        can_deselect, errors = self._deselect_status(ent, internal=_internal or force_cleanup)
        if not can_deselect:
            first = errors[0]
            return self._rollback_event(before, rng_before, 'deselect', ident, first['message'], code=first['code'], details={'semantic_errors': errors})

        if not (_internal or force_cleanup) and mode in {None, 'variable'}:
            current = self._count(ent.id)
            minimum = int(ent.value.get('numMultipleTimesMinus', 0) or 0) if mode == 'variable' else 0
            prompt_now = mode is None or current == minimum + 1
            if prompt_now:
                has_word_dialog = bool(ent.value.get('customTextfieldIsOn'))
                has_image_dialog = bool(ent.value.get('isImageUpload'))
                if word is not None and not has_word_dialog:
                    return self._rollback_event(before, rng_before, 'deselect', ident, 'word input was supplied but this choice has no custom text dialog', code='interaction.word_not_supported')
                if image is not None and not has_image_dialog:
                    return self._rollback_event(before, rng_before, 'deselect', ident, 'image input was supplied but this choice has no player image upload', code='interaction.image_not_supported')
                if dialog_action == 'accept':
                    if not has_word_dialog:
                        return self._rollback_event(before, rng_before, 'deselect', ident, 'accept is only available for a custom text dialog', code='interaction.deselect_action_not_supported')
                    selected_word = word if word is not None else self.state.custom_words.get(ent.id, str(ent.value.get('wordChangeSelect', '') or ''))
                    self.state.custom_words[ent.id] = selected_word
                    word_id = ent.value.get('idOfTheTextfieldWord')
                    if isinstance(word_id, str) and word_id in self.state.words:
                        self.state.words[word_id] = selected_word
                    event = Event('deselect', ident, True, 'custom text updated; choice remains selected', {'internal': _internal}, 'deselection.word_updated')
                    self.state.events.append(event)
                    return event
                if dialog_action == 'cancel':
                    if has_image_dialog and image is not None:
                        if image != str(ent.value.get('image', '') or ''):
                            self.state.uploaded_images[ent.id] = image
                        else:
                            self.state.uploaded_images.pop(ent.id, None)
                        event = Event('deselect', ident, True, 'image updated; deselection cancelled', {'internal': _internal}, 'deselection.image_updated')
                    else:
                        event = Event('deselect', ident, True, 'deselection cancelled in dialog', {'internal': _internal}, 'deselection.cancelled')
                    self.state.events.append(event)
                    return event
            elif word is not None or image is not None or dialog_action != 'deselect':
                return self._rollback_event(before, rng_before, 'deselect', ident, 'this repeat decrement does not open a Viewer dialog', code='interaction.dialog_not_available')

        if mode == 'variable':
            current = self._count(ent.id)
            minimum = int(ent.value.get('numMultipleTimesMinus', 0) or 0)
            if current <= minimum:
                event = Event('deselect', ident, True, 'multiple-selection minimum reached; no state change', {'count': current, 'minimum': minimum}, 'deselection.no_effect')
                self.state.events.append(event)
                return event

            was_active = self._active(ent.id)
            new_count = current - 1
            if current > 0:
                self._undo_activation_step(ent, _depth, current_count=current)
            # Positive-side decrement reverses the most recent score ledger. The
            # negative-side score arrays are source-specific runtime metadata; the
            # count/activation behavior is still reproduced exactly here.
            if current > 0:
                self._undo_scores(ent)
            if new_count == 0:
                self.state.activations.pop(ent.id, None)
            else:
                self.state.activations[ent.id] = new_count
            is_active = self._active(ent.id)

            if was_active and not is_active:
                if self._counts_for_row(ent):
                    self.state.row_counts[ent.row_id or ''] = max(0, self.state.row_counts.get(ent.row_id or '', 0) - 1)
                self.state.selected_order = [x for x in self.state.selected_order if x != ent.id]
                self._build_order_remove(ent.id)
                self._set_variables(ent, False, first=True)
                self._change_hidden_content(ent, False)
                self._change_show_all_addons(ent, -1)
                word_id = ent.value.get('idOfTheTextfieldWord')
                if ent.value.get('textfieldIsOn') and isinstance(word_id, str) and word_id in self.state.words:
                    self.state.words[word_id] = str(ent.value.get('wordChangeDeselect', ''))
                if ent.value.get('isImageUpload'):
                    self.state.uploaded_images.pop(ent.id, None)
            elif not was_active and is_active:
                self.state.selected_order.append(ent.id)
                self._build_order_add(ent.id)
                if self._counts_for_row(ent):
                    self.state.row_counts[ent.row_id or ''] = self.state.row_counts.get(ent.row_id or '', 0) + 1

            # Viewer subtracts addToAllowChoice on every selectedOneLess step.
            self._change_allowed(ent, -1)
            if current > 0 and not is_active:
                self._release_activation_provider(ent, _depth)
            self._cleanup_unmet(ent.id, _depth)
            if not self._active(ent.id):
                self._maybe_deselect_parent_after_addon(ent, _depth)
            event = Event('deselect', ident, True, reason or 'decremented', {'remaining_count': self._count(ent.id), 'internal': _internal}, 'deselection.deselected')
            self.state.events.append(event)
            return event

        # Ordinary (non-multiple) deselection.
        self._undo_activation_step(ent, _depth)
        self._undo_scores(ent)
        self.state.activations.pop(ent.id, None)
        if self._counts_for_row(ent):
            self.state.row_counts[ent.row_id or ''] = max(0, self.state.row_counts.get(ent.row_id or '', 0) - 1)
        self.state.selected_order = [x for x in self.state.selected_order if x != ent.id]
        self._build_order_remove(ent.id)
        self._set_variables(ent, False, first=True)
        self._change_allowed(ent, -1)
        self._undo_point_effects(ent)
        self._change_hidden_content(ent, False)
        self._change_show_all_addons(ent, -1)
        word_id = ent.value.get('idOfTheTextfieldWord')
        if ent.value.get('textfieldIsOn') and isinstance(word_id, str) and word_id in self.state.words:
            self.state.words[word_id] = str(ent.value.get('wordChangeDeselect', ''))
        if ent.value.get('isImageUpload'):
            self.state.uploaded_images.pop(ent.id, None)

        self._release_activation_provider(ent, _depth)
        self._cleanup_unmet(ent.id, _depth)
        self._maybe_deselect_parent_after_addon(ent, _depth)
        event = Event('deselect', ident, True, reason or 'deselected', {'remaining_count': self._count(ent.id), 'internal': _internal}, 'deselection.deselected')
        self.state.events.append(event)
        return event

    def snapshot(self, include_choice_status: bool = True) -> dict[str, Any]:
        active_ids = [x for x in self.state.selected_order if self._active(x)]
        result: dict[str, Any] = {
            'points': {k: _clean_num(v) for k, v in self.state.points.items()},
            'selected_ids': active_ids,
            'selection_counts': {k: v for k, v in self.state.activations.items() if k in {x.id for x in self.index.selectables()}},
            'active_ids_including_variables': list(self.state.activations),
            'variables': dict(self.state.variables),
            'words': dict(self.state.words),
            'row_selection_counts': dict(self.state.row_counts),
            'row_allowed_choices': {r.id: self._row_allowed(r) for r in self.index.by_kind.get('row', []) + self.index.by_kind.get('backpack_row', [])},
            'events': [x.to_dict() for x in self.state.events],
        }
        if include_choice_status:
            possible: list[str] = []
            invalid: dict[str, list[str]] = {}
            hidden_count = 0
            for ent in self.index.selectables(include_backpack=False):
                if not self.entity_visible(ent.id):
                    hidden_count += 1
                    continue
                if self._active(ent.id) and not ent.value.get('isSelectableMultiple'):
                    continue
                st = self.choice_status(ent.id)
                if st.selectable:
                    possible.append(ent.id)
                else:
                    invalid[ent.id] = st.reasons
            result['selectable_ids'] = possible
            result['invalid_choices'] = invalid
            result['hidden_choice_count'] = hidden_count
        return result

    def run(self, selections: list[str]) -> dict[str, Any]:
        failed: Event | None = None
        for token in selections:
            ident, times = _parse_selection_token(token)
            event = self.select(ident, times=times)
            if not event.ok:
                failed = event
                break
        out = self.snapshot()
        out['ok'] = failed is None
        if failed is not None:
            out['error'] = failed.to_dict()
        return out

    def pair(self, first: str, second: str) -> dict[str, Any]:
        self.reset()
        a = self.select(first)
        before_second = self.snapshot(include_choice_status=False)
        status = self.choice_status(second).to_dict()
        b = self.select(second)
        final = self.snapshot(include_choice_status=False)
        active = set(final['selected_ids'])
        return {
            'order': [first, second], 'first_event': a.to_dict(), 'second_status_before_select': status,
            'second_event': b.to_dict(), 'state_before_second': before_second, 'final': final,
            'coexist': first in active and second in active,
            'first_survives': first in active, 'second_survives': second in active,
        }

    def compatibility_matrix(self, ids: list[str] | None = None, *, both_orders: bool = True) -> dict[str, Any]:
        ids = ids or [x.id for x in self.index.selectables(include_backpack=False) if not x.value.get('isNotSelectable') and self.entity_visible(x.id)]
        pairs: list[dict[str, Any]] = []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                ab = self.pair(a, b)
                ba = self.pair(b, a) if both_orders else None
                if ab['coexist'] and (ba is None or ba['coexist']): outcome = 'coexist'
                elif ab['second_survives'] and not ab['first_survives']: outcome = f'{b}_displaces_{a}'
                elif ba and ba['second_survives'] and not ba['first_survives']: outcome = 'order_dependent_displacement'
                else: outcome = 'incompatible_or_blocked'
                pairs.append({'a': a, 'b': b, 'outcome': outcome, 'a_then_b': _pair_compact(ab), **({'b_then_a': _pair_compact(ba)} if ba else {})})
        self.reset()
        return {'ids': ids, 'pair_count': len(pairs), 'pairs': pairs}


def _parse_selection_token(token: str) -> tuple[str, int]:
    if '/ON#' in token:
        ident, raw = token.split('/ON#', 1)
        try: return ident, max(1, int(raw))
        except ValueError: return ident, 1
    return token, 1


def _clean_num(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


def _pair_compact(value: dict[str, Any]) -> dict[str, Any]:
    return {
        'coexist': value['coexist'], 'first_survives': value['first_survives'], 'second_survives': value['second_survives'],
        'second_selectable_before': value['second_status_before_select']['selectable'],
        'second_reasons': value['second_status_before_select']['reasons'],
        'selected_final': value['final']['selected_ids'], 'points_final': value['final']['points'],
    }


def explore(project: dict[str, Any], *, max_depth: int = 8, max_states: int = 5000, seed: int = 0, max_multiple: int = 3) -> dict[str, Any]:
    """Bounded state-space exploration for regression and reachability testing."""
    root = Simulator(project, seed=seed)
    selectable_ids = [x.id for x in root.index.selectables(include_backpack=False) if not x.value.get('isNotSelectable')]

    def key(sim: Simulator) -> tuple[Any, ...]:
        s = sim.state
        return (
            tuple(sorted(s.activations.items())),
            tuple(sorted((k, round(v, 10)) for k, v in s.points.items())),
            tuple(sorted(s.variables.items())),
            tuple(sorted(s.words.items())),
            tuple(sorted(s.row_counts.items())),
            tuple(sorted(s.allowed_deltas.items())),
        )

    queue: list[tuple[Simulator, int, list[str]]] = [(root, 0, [])]
    seen = {key(root)}
    reachable: set[str] = set()
    terminal: list[dict[str, Any]] = []
    point_ranges: dict[str, list[float]] = {k: [v, v] for k, v in root.state.points.items()}
    transitions = 0
    truncated = False
    shortest: dict[str, list[str]] = {}

    while queue:
        sim, depth, path = queue.pop(0)
        for pid, value in sim.state.points.items():
            rng = point_ranges.setdefault(pid, [value, value]); rng[0] = min(rng[0], value); rng[1] = max(rng[1], value)
        if depth >= max_depth:
            continue
        available: list[str] = []
        for ident in selectable_ids:
            ent = sim._entity(ident)
            if not ent: continue
            if sim._active(ident) and not ent.value.get('isSelectableMultiple'): continue
            if ent.value.get('isSelectableMultiple') and abs(sim._count(ident)) >= max_multiple: continue
            st = sim.choice_status(ident)
            if st.selectable: available.append(ident)
        if not available:
            terminal.append({'depth': depth, 'path': path, 'selected_ids': sim.snapshot(False)['selected_ids'], 'points': sim.snapshot(False)['points']})
            continue
        for ident in available:
            child = Simulator(project, seed=seed)
            child.state = sim.state.clone()
            event = child.select(ident)
            transitions += 1
            if not event.ok and not child._active(ident):
                continue
            reachable.add(ident); shortest.setdefault(ident, [*path, ident])
            k = key(child)
            if k in seen: continue
            if len(seen) >= max_states:
                truncated = True; queue.clear(); break
            seen.add(k); queue.append((child, depth + 1, [*path, ident]))
        if truncated: break

    return {
        'states_visited': len(seen),
        'transitions_tested': transitions,
        'max_depth': max_depth,
        'max_states': max_states,
        'truncated': truncated,
        'reachable_choice_ids': sorted(reachable),
        'unreached_choice_ids': sorted(set(selectable_ids) - reachable),
        'shortest_known_path': shortest,
        'point_ranges': {k: {'min': _clean_num(v[0]), 'max': _clean_num(v[1])} for k, v in point_ranges.items()},
        'terminal_states': terminal[:200],
        'terminal_states_truncated': len(terminal) > 200,
    }
