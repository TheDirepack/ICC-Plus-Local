from __future__ import annotations

import argparse
import base64
import difflib
import json
import mimetypes
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .editor import ProjectEditor, make_entity, new_project, pointer_get
from .upstream_2106 import default_export_project, json_stringify
from .operations import apply_operation_script, load_operation_script
from .phase_ops import apply_phase_script, load_phase_script
from .build_pipeline import build_from_manifest, load_build_manifest
from .model import ProjectIndex
from .selectors import select_entities, check_expected_count
from .scenario import run_scenario
from .simulator import Simulator, explore, project_fingerprint
from .analysis import dependency_graph, direct_conflicts
from .capabilities import capabilities, COMMAND_KINDS
from .agent_protocol import brief_capabilities, command_metadata, load_protocol_schema, protocol_schema_names
from .field_catalog import FIELD_CATALOG, catalog_kinds, fields_for, suggest_fields, STYLE_FIELD_GROUPS
from .field_types import fields_details, json_schema_for_kind, python_typeddicts, typescript_declarations, validate_known_values, validate_field_value
from .assets import Config as AssetConfig, Totals as AssetTotals, ToolError as AssetToolError, compact_result as compact_asset_result, compact_totals as compact_asset_totals, doctor as asset_doctor, process_directory, process_single_file, probe_path, quality_from_cq, unique_output_path
from .validation import project_shape_diagnostics, validate
from .visuals import VISUAL_KINDS, apply_visual_manifest, visual_audit
from .packaging import build_viewer_package, creator_save_payload, export_project_zip
from .gui_parity import gui_parity_report
from .guides import guide, guide_topics
from .image_edit import crop_webp, webp_data_url
from .image_assets import prepare_image_reference
from .build_string import entry_to_dict, parse_build_string
from .creator_helpers import (
    CREATOR_SYMBOLS, ROW_SORT_MODES, clean_private_styling, creator_id_csv, export_design, font_inventory, ids_from_titles, import_design,
    project_stats, sort_row_choices, update_font,
)
from .style_templates import STYLE_TEMPLATE_NAMES, SOURCE_COMMIT as STYLE_TEMPLATE_SOURCE_COMMIT, apply_style_template, resolve_style_template, style_templates
from .version import __version__


def load(path: str, *, require_iccplus: bool = True) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('project JSON must be an object')
    if require_iccplus:
        shape = project_shape_diagnostics(value)
        if shape:
            details = '; '.join(f'{d.code} at {d.path or "/"}: {d.message}' for d in shape)
            raise ValueError('not an ICC Plus project: ' + details)
    return value


def save(path: str, value: Any, *, compact: bool = False, trailing_newline: bool = True) -> None:
    """Atomically replace a JSON/text artifact in the destination directory."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json_stringify(value) if compact else json.dumps(value, indent=2, ensure_ascii=False)
    if trailing_newline:
        text += '\n'
    old_mode = None
    try:
        old_mode = target.stat().st_mode & 0o777
    except OSError:
        pass
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{target.name}.', suffix='.tmp', dir=target.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if old_mode is not None:
            try:
                tmp.chmod(old_mode)
            except OSError:
                pass
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def save_runtime_state(path: str, value: Any) -> None:
    """Atomically replace a continuation state file with owner-only permissions."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{target.name}.', suffix='.tmp', dir=target.parent)
    tmp = Path(tmp_name)
    try:
        try:
            os.fchmod(fd, 0o600)
        except (AttributeError, OSError):
            pass
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
        try:
            target.chmod(0o600)
        except OSError:
            pass
    finally:
        if tmp.exists():
            tmp.unlink()



class CliUsageError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


_DEFAULT_PRETTY = sys.stdout.isatty()

def emit(value: Any, *, pretty: bool | None = None) -> None:
    if pretty is None:
        pretty = _DEFAULT_PRETTY
    print(json.dumps(value, indent=2 if pretty else None, ensure_ascii=False, separators=None if pretty else (',', ':')))


def _json_file_candidate(raw: str) -> Path | None:
    try:
        candidate = Path(raw)
        return candidate if candidate.exists() and candidate.is_file() else None
    except OSError:
        return None


def parse_json_value(raw: str) -> Any:
    if raw == '-':
        return json.loads(sys.stdin.read())
    if raw.startswith('@'):
        return json.loads(Path(raw[1:]).read_text(encoding='utf-8'))
    try:
        return json.loads(raw)
    except json.JSONDecodeError as json_error:
        candidate = _json_file_candidate(raw)
        if candidate is not None:
            return json.loads(candidate.read_text(encoding='utf-8'))
        raise json_error


def parse_relaxed_value(raw: str) -> Any:
    """Parse JSON scalars/containers, otherwise keep the text as a string."""
    if raw == '-' or raw.startswith('@'):
        return parse_json_value(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        candidate = _json_file_candidate(raw)
        if candidate is not None:
            return json.loads(candidate.read_text(encoding='utf-8'))
        return raw


def text_source(raw: str) -> str:
    if raw == '-':
        return sys.stdin.read()
    if raw.startswith('@'):
        return Path(raw[1:]).read_text(encoding='utf-8').strip()
    try:
        candidate = Path(raw)
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding='utf-8').strip()
    except OSError:
        pass
    return raw


def values_arg(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    value = parse_json_value(raw)
    if not isinstance(value, dict):
        raise ValueError('--values must be a JSON object')
    return value


def field_values(raw_values: str | None, fields: list[str] | None, *, field_kind: str | None = None) -> dict[str, Any]:
    values = values_arg(raw_values)
    catalog_kind = {'backpack_row': 'row'}.get(field_kind or '', field_kind or '')
    allowed = set(FIELD_CATALOG.get(catalog_kind, [])) if catalog_kind else None
    if catalog_kind:
        # --values remains the forward-compatible escape hatch for unknown
        # future fields, but values for pinned 2.10.6 fields are still type
        # checked. A known field should never accept a known-wrong JSON type.
        validate_known_values(catalog_kind, values)
    for item in fields or []:
        if '=' not in item:
            raise ValueError(f'--field must be NAME=VALUE, got {item!r}')
        name, raw = item.split('=', 1)
        name = name.strip()
        if not name:
            raise ValueError('--field name cannot be empty')
        if allowed is not None and name not in allowed:
            suggestions = suggest_fields(catalog_kind, name, limit=3)
            hint = f'; did you mean {", ".join(repr(x) for x in suggestions)}?' if suggestions else ''
            raise ValueError(
                f'unknown native field {name!r} for {catalog_kind}{hint}; '
                'use `fields KIND` to discover field names, or --values for an intentional forward-compatible field'
            )
        parsed = parse_relaxed_value(raw)
        if catalog_kind and allowed is not None and name in allowed:
            validate_field_value(catalog_kind, name, parsed)
        values[name] = parsed
    return values


def cli_strings(values: list[str] | None) -> list[str]:
    out: list[str] = []
    for raw in values or []:
        out.extend(x.strip() for x in raw.split(',') if x.strip())
    return list(dict.fromkeys(out))


def write_checked(project: dict[str, Any], target: str, *, allow_invalid: bool = False) -> tuple[dict[str, Any], str | None]:
    report = validate(project)
    if report['valid'] or allow_invalid:
        save(target, project)
        return report, target
    return report, None

def _strings_for_cli(value: Any) -> list[str]:
    return [x for x in value if isinstance(x, str)] if isinstance(value, list) else []

def json_source(raw: str) -> Any:
    return parse_json_value(raw)


def json_source_base(raw: str, *, fallback: Path) -> Path:
    if raw.startswith('@'):
        return Path(raw[1:]).expanduser().resolve().parent
    try:
        candidate = Path(raw).expanduser()
        if candidate.exists() and candidate.is_file():
            return candidate.resolve().parent
    except OSError:
        pass
    return fallback.resolve()


def unwrap_runtime_state(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError('runtime state must be a JSON object')
    if value.get('format') == 'iccplus-cyoa-runtime-state':
        return value
    nested = value.get('runtime_state')
    if isinstance(nested, dict):
        return nested
    raise ValueError('state input is not an ICC Plus runtime state or a session response containing runtime_state')


def action_tokens(kind: str, values: list[str] | None) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for raw in values or []:
        for token in raw.split(','):
            token = token.strip()
            if not token:
                continue
            if kind == 'select' and '/ON#' in token:
                ident, count = token.split('/ON#', 1)
                try:
                    times = max(1, int(count))
                except ValueError:
                    times = 1
                actions.append({'action': 'select', 'id': ident, 'times': times})
            else:
                actions.append({'action': kind, 'id': token})
    return actions



def cmd_show(a: argparse.Namespace) -> int:
    project = load(a.project)
    idx = ProjectIndex(project)
    ent = idx.one(a.reference, a.kind)
    if not ent:
        matches = idx.find(a.reference, a.kind)
        if not matches:
            suggestions = search_index(idx, a.reference, kind=a.kind or 'all', limit=5)
            hint = '; close matches: ' + ', '.join(x['id'] for x in suggestions) if suggestions else ''
            raise ValueError(f'entity not found: {a.reference}{hint}; use `search PROJECT QUERY` to find IDs')
        raise ValueError(f'entity reference is ambiguous ({len(matches)} matches): {a.reference}')
    report = validate(project)
    diagnostics = [d for d in report['diagnostics'] if d.get('entity_id') == ent.id or str(d.get('path', '')).startswith(ent.path)]
    graph = dependency_graph(project)
    dependencies = graph.get(ent.id)
    dependents = [cid for cid, deps in graph.items() if ent.id in deps.get('requires_ids', []) or ent.id in deps.get('excludes_ids', [])]
    emit({
        'id': ent.id,
        'kind': ent.kind,
        'path': ent.path,
        'parent_id': ent.parent_id,
        'row_id': ent.row_id,
        'value': ent.value,
        'dependencies': dependencies,
        'dependents': dependents,
        'diagnostics': diagnostics,
    })
    return 0


def cmd_project_update(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    values = field_values(a.values, a.field, field_kind='project')
    unset = cli_strings(a.unset)
    if not values and not unset:
        raise ValueError('project-update needs --values, --field, or --unset')
    editor.update_project(values=values, unset=unset, normalize=False)
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'updated_fields': sorted(values), 'unset': unset, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_update(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    ent = editor.resolve(a.reference, a.kind)
    values = field_values(a.values, a.field, field_kind=ent.kind)
    unset = cli_strings(a.unset)
    if not values and not unset:
        raise ValueError('update needs --values, --field, or --unset')
    value = editor.update(a.reference, kind=a.kind, values=values, unset=unset, normalize=False)
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'entity': value, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_delete(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    removed = editor.delete(a.reference, kind=a.kind, normalize=False)
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'removed': removed, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_generate(a: argparse.Namespace) -> int:
    """Create the exact blank ICC Plus Creator project used as the build starting point."""
    project = default_export_project()
    output = a.output or str(unique_output_path(Path('project.json')))
    written = None
    if not a.dry_run:
        # Keep the Creator's exact blank-export byte shape. Later authoring goes
        # through apply/direct mutation tools, not a second generation format.
        save(output, project, compact=True, trailing_newline=False)
        written = output
    emit({
        'ok': True,
        'blank': True,
        'written': written,
        'dry_run': bool(a.dry_run),
        'version': project['version'],
        'summary': ProjectIndex(project).summary(),
        'next': f'iccplus-local structure {output} SCRIPT' if written else 'iccplus-local structure PROJECT SCRIPT',
    })
    return 0


def cmd_build(a: argparse.Namespace) -> int:
    manifest, base, manifest_source = load_build_manifest(a.manifest)
    project, result = build_from_manifest(manifest, base=base)
    result['manifest_source'] = manifest_source
    result['written'] = None
    result['dry_run'] = bool(a.dry_run)
    if not result.get('ok'):
        emit(result)
        return 4 if result.get('stage') == 'step' else 2
    if not a.dry_run:
        save(a.output, project)
        result['written'] = a.output
    emit(result)
    return 0


def _compact_apply_payload(result: dict[str, Any]) -> dict[str, Any]:
    def compact_item(item: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in item.items():
            if key in {'value', 'entity', 'cloned', 'design'}:
                continue
            if key in {'entities', 'removed'} and isinstance(value, list) and any(isinstance(x, (dict, list)) for x in value):
                out[f'{key}_count'] = len(value)
                ids = []
                for entry in value:
                    if isinstance(entry, dict):
                        ident = entry.get('id', entry.get('idx'))
                        if isinstance(ident, str):
                            ids.append(ident)
                if ids:
                    out[f'{key}_ids'] = ids
                continue
            out[key] = value
        return out

    out: dict[str, Any] = {}
    for key, value in result.items():
        if key == 'results' and isinstance(value, list):
            out[key] = [compact_item(x) if isinstance(x, dict) else x for x in value]
        elif key == 'validation' and isinstance(value, dict):
            compact_validation = {k: value.get(k) for k in ('valid', 'errors', 'warnings') if k in value}
            if not value.get('valid', True) or value.get('warnings', 0):
                compact_validation['diagnostics'] = value.get('diagnostics', [])
            out[key] = compact_validation
        elif key == 'normalization_changes' and isinstance(value, list):
            out['normalization_change_count'] = len(value)
        else:
            out[key] = value
    out['result_mode'] = 'compact'
    return out


def _cmd_phase_apply(a: argparse.Namespace, phase: str) -> int:
    project = load(a.project)
    script = load_phase_script(a.script, phase)
    updated, result = apply_phase_script(project, script, phase, validate_after=not a.no_validate)
    if not result.get('ok'):
        emit(_compact_apply_payload(result))
        return 4
    report = result.get('validation')
    valid = report is None or report.get('valid') is True
    written = None
    if not a.dry_run and (valid or a.allow_invalid):
        save(a.output or a.project, updated)
        written = a.output or a.project
    result['written'] = written
    result['dry_run'] = bool(a.dry_run)
    result['summary'] = ProjectIndex(updated).summary()
    emit(_compact_apply_payload(result))
    return 0 if valid else 2


def cmd_structure(a: argparse.Namespace) -> int:
    return _cmd_phase_apply(a, 'structure')


def cmd_rules(a: argparse.Namespace) -> int:
    return _cmd_phase_apply(a, 'rules')


def cmd_apply(a: argparse.Namespace) -> int:
    project = load(a.project)
    script = load_operation_script(a.script)
    result_mode = a.result_mode or ('compact' if script.get('format') == 'iccplus-agent-ops' else 'full')
    updated, result = apply_operation_script(project, script, validate_after=not a.no_validate)
    if not result.get('ok'):
        emit(_compact_apply_payload(result) if result_mode == 'compact' else result)
        return 4
    report = result.get('validation')
    valid = report is None or report.get('valid') is True
    written = None
    if not a.dry_run and (valid or a.allow_invalid):
        save(a.output or a.project, updated)
        written = a.output or a.project
    result['written'] = written
    result['dry_run'] = bool(a.dry_run)
    result['summary'] = ProjectIndex(updated).summary()
    emit(_compact_apply_payload(result) if result_mode == 'compact' else result)
    return 0 if valid else 2



def _entity_search_fields(ent: Any) -> dict[str, str]:
    values = ent.value if isinstance(ent.value, dict) else {}
    out = {
        'id': str(ent.id),
        'title': str(values.get('title') or values.get('name') or ''),
        'debugTitle': str(values.get('debugTitle') or ''),
        'text': str(values.get('text') or values.get('titleText') or values.get('replaceText') or ''),
    }
    return {k: v for k, v in out.items() if v}


def search_index(idx: ProjectIndex, query: str, *, kind: str = 'all', limit: int = 20) -> list[dict[str, Any]]:
    needle = query.strip().lower()
    if not needle:
        raise ValueError('search query cannot be empty')
    entities = idx.entities if kind == 'all' else idx.by_kind.get(kind, [])
    matches: list[tuple[int, float, str, Any, list[str]]] = []
    for ent in entities:
        fields = _entity_search_fields(ent)
        direct = [name for name, value in fields.items() if needle in value.lower()]
        if direct:
            best_len = min(len(fields[name]) for name in direct)
            matches.append((1, 1.0 - min(best_len, 10000) / 100000.0, ent.id, ent, direct))
            continue
        fuzzy = 0.0
        fuzzy_fields: list[str] = []
        for name, value in fields.items():
            ratio = difflib.SequenceMatcher(None, needle, value.lower()).ratio()
            if ratio > fuzzy:
                fuzzy = ratio
                fuzzy_fields = [name]
            elif ratio == fuzzy:
                fuzzy_fields.append(name)
        if fuzzy >= 0.52:
            matches.append((0, fuzzy, ent.id, ent, fuzzy_fields))
    matches.sort(key=lambda x: (-x[0], -x[1], x[2]))
    out = []
    for direct, score, _, ent, matched_fields in matches[:max(1, limit)]:
        out.append({
            'id': ent.id,
            'kind': ent.kind,
            'title': ent.title,
            'path': ent.path,
            'parent_id': ent.parent_id,
            'row_id': ent.row_id,
            'match': 'substring' if direct else 'fuzzy',
            'matched_fields': matched_fields,
            'score': 1.0 if direct else round(score, 3),
        })
    return out


def _argparse_action_spec(action: argparse.Action) -> dict[str, Any] | None:
    if action.dest in {'help', 'func'}:
        return None
    out: dict[str, Any] = {
        'name': action.dest,
        'kind': 'option' if action.option_strings else 'positional',
        'required': bool(getattr(action, 'required', False)),
    }
    if action.option_strings:
        out['flags'] = list(action.option_strings)
    if action.nargs is not None:
        out['nargs'] = action.nargs
    if action.choices is not None:
        out['choices'] = list(action.choices)
    typ = getattr(action, 'type', None)
    if typ is not None:
        out['type'] = getattr(typ, '__name__', str(typ))
    default = getattr(action, 'default', argparse.SUPPRESS)
    if default is not argparse.SUPPRESS and not callable(default):
        try:
            json.dumps(default)
            out['default'] = default
        except TypeError:
            pass
    help_text = getattr(action, 'help', None)
    if help_text and help_text is not argparse.SUPPRESS:
        out['help'] = help_text
    return out


def _subparser_summary(sub_action: argparse._SubParsersAction, name: str) -> str | None:
    pseudo = next((x for x in getattr(sub_action, '_choices_actions', []) if getattr(x, 'dest', None) == name), None)
    return getattr(pseudo, 'help', None) if pseudo is not None else None


def command_tree() -> dict[str, Any]:
    """Return every advertised command path recursively."""
    root = parser()
    flat: list[dict[str, Any]] = []

    def walk(current: argparse.ArgumentParser, path: list[str]) -> list[dict[str, Any]]:
        sub_action = next((x for x in current._actions if isinstance(x, argparse._SubParsersAction)), None)
        if sub_action is None:
            return []
        visible = {getattr(x, 'dest', None): getattr(x, 'help', None) for x in getattr(sub_action, '_choices_actions', [])}
        nodes: list[dict[str, Any]] = []
        for name in visible:
            if not name or name not in sub_action.choices:
                continue
            child = sub_action.choices[name]
            child_path = [*path, name]
            summary = child.description or visible.get(name) or f'ICC Plus command: {" ".join(child_path)}'
            node = {
                'name': name,
                'path': ' '.join(child_path),
                'depth': len(child_path),
                'summary': summary,
            }
            children = walk(child, child_path)
            if children:
                node['children'] = children
            nodes.append(node)
            flat.append({'path': node['path'], 'depth': node['depth'], 'summary': summary})
        return nodes

    tree = walk(root, [])
    flat.sort(key=lambda item: item['path'])
    return {
        'format': 'iccplus-command-tree',
        'format_version': 1,
        'top_level_count': len(tree),
        'path_count': len(flat),
        'max_depth': max((item['depth'] for item in flat), default=0),
        'paths': flat,
        'tree': tree,
    }


def command_description(name: str | list[str]) -> dict[str, Any]:
    parts = [name] if isinstance(name, str) else list(name)
    if not parts:
        raise ValueError('describe needs a command name')
    current: argparse.ArgumentParser = parser()
    summaries: list[str] = []
    for depth, part in enumerate(parts):
        sub_action = next((x for x in current._actions if isinstance(x, argparse._SubParsersAction)), None)
        if sub_action is None or part not in sub_action.choices:
            choices = sorted(sub_action.choices) if sub_action is not None else []
            suggestions = difflib.get_close_matches(part, choices, n=5, cutoff=0.4)
            hint = f'; close matches: {", ".join(suggestions)}' if suggestions else ''
            prefix = ' '.join(parts[:depth])
            where = f' under {prefix}' if prefix else ''
            raise ValueError(f'unknown command: {part}{where}{hint}')
        summaries.append(_subparser_summary(sub_action, part) or '')
        current = sub_action.choices[part]
    args = [x for x in (_argparse_action_spec(a) for a in current._actions) if x is not None]
    command_path = ' '.join(parts)
    summary = current.description or summaries[-1] or f'ICC Plus command: {command_path}'
    meta = command_metadata(parts[0])
    return {
        'command': command_path,
        'top_level_command': parts[0],
        'usage': current.format_usage().strip(),
        'summary': summary,
        'description': current.description or summary,
        'arguments': args,
        **meta,
    }


def _asset_config(a: argparse.Namespace) -> AssetConfig:
    quality = quality_from_cq(a.cq) if a.cq is not None else a.quality
    if not 0 <= a.quality <= 100:
        raise ValueError('--quality must be between 0 and 100')
    if a.cq is not None and not 0 <= a.cq <= 63:
        raise ValueError('--cq must be between 0 and 63')
    if a.workers < 1:
        raise ValueError('--workers must be at least 1')
    return AssetConfig(
        quality=quality,
        workers=a.workers,
        encoder=a.encoder,
        assets=a.assets,
        gif_mode=a.gif_mode,
        recompress_avif=a.recompress_avif,
        min_savings_bytes=max(1, a.min_savings_bytes),
        min_savings_percent=max(0.0, a.min_savings_percent),
        dry_run=a.dry_run,
        pretty=False,
        use_convert_any=not a.no_convert_any,
    )


def cmd_compress(a: argparse.Namespace) -> int:
    inputs = list(a.inputs)
    cfg = _asset_config(a)
    totals = AssetTotals()
    results = []
    output_root = Path(a.output).expanduser().resolve() if a.output else None
    if output_root and len(inputs) > 1 and not output_root.exists() and output_root.suffix:
        raise ValueError('with multiple inputs, --output must be a directory')
    for raw_input in inputs:
        src = Path(raw_input).expanduser().resolve()
        if not src.exists():
            raise ValueError(f'input does not exist: {src}')
        out = output_root
        if output_root and len(inputs) > 1:
            out = output_root / (src.name + ('-compressed' if src.is_dir() else ''))
        try:
            if src.is_dir():
                results.append(process_directory(src, out, cfg, totals, a.in_place))
            else:
                results.append(process_single_file(src, out, cfg, totals, a.in_place))
        except AssetToolError as exc:
            raise ValueError(str(exc)) from exc
    payload: dict[str, Any] = {
        'ok': True,
        'totals': compact_asset_totals(totals),
        'results': [compact_asset_result(x) for x in results],
    }
    if a.details:
        payload['settings'] = {
            'quality': cfg.quality,
            'cq_compat': a.cq,
            'workers': cfg.workers,
            'encoder': cfg.encoder,
            'assets': cfg.assets,
            'gif': cfg.gif_mode,
            'recompress_avif': cfg.recompress_avif,
            'min_savings_bytes': cfg.min_savings_bytes,
            'min_savings_percent': cfg.min_savings_percent,
            'dry_run': cfg.dry_run,
        }
        payload['results'] = results
    emit(payload)
    return 0


def cmd_asset_probe(a: argparse.Namespace) -> int:
    emit({'ok': True, 'results': [probe_path(Path(x).expanduser().resolve()) for x in a.inputs]})
    return 0


def cmd_visual_audit(a: argparse.Namespace) -> int:
    project = load(a.project)
    kinds = cli_strings(a.kind) if a.kind else None
    report = visual_audit(
        project,
        kinds=kinds,
        row=a.row,
        group=a.group,
        missing_images=a.missing_images,
        missing_assets=a.missing_assets,
        unstyled=a.unstyled,
        limit=a.limit,
        asset_root=a.asset_root,
        manifest_stub=a.manifest_stub,
        style_values=a.style_values,
    )
    emit(report)
    return 0


def cmd_apply_visuals(a: argparse.Namespace) -> int:
    project = load(a.project)
    manifest = json_source(a.manifest)
    if not isinstance(manifest, dict):
        raise ValueError('visual manifest must be a JSON object')
    asset_base = json_source_base(a.manifest, fallback=Path(a.project).resolve().parent)
    updated, result = apply_visual_manifest(project, manifest, asset_base=asset_base)
    editor = ProjectEditor(updated)
    changes = editor.normalize_and_check()
    report = validate(updated) if not a.no_validate else None
    valid = report is None or report.get('valid') is True
    written = None
    if not a.dry_run and (valid or a.allow_invalid):
        written = a.output or a.project
        save(written, updated)
    result['ok'] = valid
    if getattr(a, 'canonical_style', False):
        result['phase'] = 'style'
    result['written'] = written
    result['dry_run'] = bool(a.dry_run)
    result['normalization_changes'] = changes
    result['summary'] = ProjectIndex(updated).summary()
    if report is not None:
        result['validation'] = report
    if a.report_out:
        save(a.report_out, result)
        result['report_written'] = a.report_out
    emit(result)
    return 0 if valid else 2


def cmd_doctor(a: argparse.Namespace) -> int:
    image = asset_doctor()
    emit({
        'ok': True,
        'tool': 'iccplus-local',
        'tool_version': __version__,
        'python': sys.version.split()[0],
        'image_compression': image,
    })
    return 0


def cmd_search(a: argparse.Namespace) -> int:
    idx = ProjectIndex(load(a.project))
    matches = search_index(idx, a.query, kind=a.kind, limit=a.limit)
    emit({'query': a.query, 'kind': a.kind, 'count': len(matches), 'matches': matches})
    return 0 if matches else 3


def cmd_match(a: argparse.Namespace) -> int:
    project = load(a.project)
    where = json_source(a.where)
    if not isinstance(where, dict):
        raise ValueError('WHERE must be a JSON object')
    matches = select_entities(project, where)
    expect = parse_relaxed_value(a.expect) if a.expect is not None else None
    check_expected_count(len(matches), expect, label='match')
    payload = {
        'where': where,
        'count': len(matches),
        'matches': [
            {'id': e.id, 'kind': e.kind, 'title': e.title, 'path': e.path, 'parent_id': e.parent_id, 'row_id': e.row_id}
            for e in matches
        ],
    }
    emit(payload)
    return 0 if matches or a.allow_empty else 3


_INSPECT_KEYS: dict[str, set[str]] = {
    'check': {'op'},
    'summary': {'op'},
    'ids': {'op', 'all'},
    'list': {'op', 'kind', 'row', 'parent', 'group', 'id_prefix'},
    'search': {'op', 'query', 'kind', 'limit'},
    'show': {'op', 'ref', 'kind'},
    'get': {'op', 'pointer'},
    'match': {'op', 'where', 'expect', 'allow_empty'},
    'stats': {'op'},
    'visual': {'op', 'kind', 'kinds', 'row', 'group', 'missing_images', 'missing_assets', 'unstyled', 'limit', 'asset_root', 'manifest_stub', 'style_values'},
}


def _validate_inspect_query_keys(query: dict[str, Any]) -> None:
    op = query.get('op')
    if not isinstance(op, str):
        raise ValueError('inspect query needs string op')
    allowed = _INSPECT_KEYS.get(op)
    if allowed is None:
        raise ValueError(f'unknown inspect op: {op}; choices: {", ".join(_INSPECT_KEYS)}')
    unknown = sorted(set(query) - allowed)
    if unknown:
        hints = []
        for key in unknown:
            matches = difflib.get_close_matches(key, sorted(allowed), n=2, cutoff=0.45)
            if matches:
                hints.append(f'{key} -> {"/".join(matches)}')
        suffix = f'; suggestions: {", ".join(hints)}' if hints else ''
        raise ValueError(f'inspect {op} has unknown field(s): {", ".join(unknown)}{suffix}')


def _inspect_kind(idx: ProjectIndex, value: Any, *, default: str = 'all') -> str:
    kind = default if value is None else str(value)
    choices = ['all', *sorted(idx.by_kind)]
    if kind not in choices:
        suggestions = difflib.get_close_matches(kind, choices, n=3, cutoff=0.4)
        hint = f'; close matches: {", ".join(suggestions)}' if suggestions else ''
        raise ValueError(f'unknown entity kind: {kind}{hint}')
    return kind


def _inspect_list(idx: ProjectIndex, query: dict[str, Any]) -> list[dict[str, Any]]:
    kind = _inspect_kind(idx, query.get('kind'))
    ents = list(idx.entities if kind == 'all' else idx.by_kind.get(kind, []))
    row = query.get('row')
    if isinstance(row, str) and row:
        ents = [e for e in ents if e.row_id == row or (e.kind in {'row', 'backpack_row'} and e.id == row)]
    parent = query.get('parent')
    if isinstance(parent, str) and parent:
        ents = [e for e in ents if e.parent_id == parent]
    group_id = query.get('group')
    if isinstance(group_id, str) and group_id:
        group = idx.one(group_id, 'group')
        if not group:
            raise ValueError(f'group not found: {group_id}')
        members = set(_strings_for_cli(group.value.get('elements'))) | set(_strings_for_cli(group.value.get('rowElements')))
        ents = [e for e in ents if e.id in members or group_id in _strings_for_cli(e.value.get('groups'))]
    prefix = query.get('id_prefix')
    if isinstance(prefix, str) and prefix:
        ents = [e for e in ents if e.id.startswith(prefix)]
    return [
        {'id': e.id, 'kind': e.kind, 'title': e.title, 'path': e.path, 'parent_id': e.parent_id, 'row_id': e.row_id}
        for e in ents
    ]


def _inspect_show(project: dict[str, Any], idx: ProjectIndex, reference: str, kind: str | None) -> dict[str, Any]:
    ent = idx.one(reference, kind)
    if not ent:
        matches = idx.find(reference, kind)
        if not matches:
            suggestions = search_index(idx, reference, kind=kind or 'all', limit=5)
            hint = '; close matches: ' + ', '.join(x['id'] for x in suggestions) if suggestions else ''
            raise ValueError(f'entity not found: {reference}{hint}')
        raise ValueError(f'entity reference is ambiguous ({len(matches)} matches): {reference}')
    report = validate(project)
    diagnostics = [d for d in report['diagnostics'] if d.get('entity_id') == ent.id or str(d.get('path', '')).startswith(ent.path)]
    graph = dependency_graph(project)
    dependencies = graph.get(ent.id)
    dependents = [cid for cid, deps in graph.items() if ent.id in deps.get('requires_ids', []) or ent.id in deps.get('excludes_ids', [])]
    return {
        'id': ent.id,
        'kind': ent.kind,
        'path': ent.path,
        'parent_id': ent.parent_id,
        'row_id': ent.row_id,
        'value': ent.value,
        'dependencies': dependencies,
        'dependents': dependents,
        'diagnostics': diagnostics,
    }


def _inspect_query(project: dict[str, Any], idx: ProjectIndex, query: dict[str, Any]) -> Any:
    _validate_inspect_query_keys(query)
    op = str(query['op'])
    if op == 'check':
        ids = identity_report(project, include_all=False)
        validation = validate(project)
        return {'ok': bool(ids['ok'] and validation['valid']), 'summary': idx.summary(), 'identities': ids, 'validation': validation}
    if op == 'summary':
        out = idx.summary()
        shape = project_shape_diagnostics(project)
        out['format_valid'] = not shape
        if shape:
            out['format_diagnostics'] = [x.to_dict() for x in shape]
        return out
    if op == 'ids':
        return identity_report(project, include_all=bool(query.get('all', False)))
    if op == 'list':
        return _inspect_list(idx, query)
    if op == 'search':
        text = query.get('query')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('inspect search needs non-empty query')
        kind = _inspect_kind(idx, query.get('kind'))
        limit = query.get('limit', 20)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError('inspect search limit must be a positive integer')
        return {'query': text, 'kind': kind, 'matches': search_index(idx, text, kind=kind, limit=limit)}
    if op == 'show':
        ref = query.get('ref')
        if not isinstance(ref, str) or not ref:
            raise ValueError('inspect show needs ref')
        kind = None if query.get('kind') is None else _inspect_kind(idx, query.get('kind'), default='all')
        if kind == 'all':
            kind = None
        return _inspect_show(project, idx, ref, kind)
    if op == 'get':
        pointer = query.get('pointer')
        if not isinstance(pointer, str):
            raise ValueError('inspect get needs pointer')
        return pointer_get(project, pointer)
    if op == 'match':
        where = query.get('where')
        if not isinstance(where, dict):
            raise ValueError('inspect match needs object where')
        matches = select_entities(project, where)
        expect = query.get('expect')
        if expect is not None:
            check_expected_count(len(matches), expect, label='inspect match')
        if not matches and not bool(query.get('allow_empty', False)):
            raise ValueError('inspect match selected 0 entities; set allow_empty=true only when that is intentional')
        return {
            'where': where,
            'count': len(matches),
            'matches': [
                {'id': e.id, 'kind': e.kind, 'title': e.title, 'path': e.path, 'parent_id': e.parent_id, 'row_id': e.row_id}
                for e in matches
            ],
        }
    if op == 'stats':
        return project_stats(project)
    if op == 'visual':
        raw_kinds = query.get('kinds', query.get('kind'))
        if raw_kinds is None:
            kinds = None
        elif isinstance(raw_kinds, str):
            kinds = [x.strip() for x in raw_kinds.split(',') if x.strip()]
        elif isinstance(raw_kinds, list) and all(isinstance(x, str) for x in raw_kinds):
            kinds = list(raw_kinds)
        else:
            raise ValueError('inspect visual kind/kinds must be a string or string array')
        return visual_audit(
            project, kinds=kinds, row=query.get('row'), group=query.get('group'),
            missing_images=bool(query.get('missing_images', False)),
            missing_assets=bool(query.get('missing_assets', False)),
            unstyled=bool(query.get('unstyled', False)),
            limit=query.get('limit'), asset_root=query.get('asset_root'),
            manifest_stub=bool(query.get('manifest_stub', False)),
            style_values=bool(query.get('style_values', False)),
        )
    raise ValueError(f'unknown inspect op: {op}; choices: {", ".join(_INSPECT_KEYS)}')


def cmd_inspect(a: argparse.Namespace) -> int:
    project = load(a.project, require_iccplus=False)
    request = json_source(a.request)
    stop_on_error = False
    if isinstance(request, list):
        queries = request
    elif isinstance(request, dict) and 'queries' in request:
        unknown = sorted(set(request) - {'queries', 'stop_on_error'})
        if unknown:
            raise ValueError(f'inspect request has unknown field(s): {", ".join(unknown)}')
        queries = request.get('queries')
        stop_on_error = bool(request.get('stop_on_error', False))
    elif isinstance(request, dict) and 'op' in request:
        queries = [request]
    else:
        raise ValueError('inspect request must be one query object, an array of queries, or {queries:[...]}')
    if not isinstance(queries, list) or not queries:
        raise ValueError('inspect request needs at least one query')
    idx = ProjectIndex(project)
    results: list[dict[str, Any]] = []
    all_ok = True
    for index, query in enumerate(queries):
        if not isinstance(query, dict):
            result = {'index': index, 'ok': False, 'error': {'code': 'query.invalid', 'message': 'query must be a JSON object'}}
            results.append(result)
            all_ok = False
            if stop_on_error:
                break
            continue
        try:
            value = _inspect_query(project, idx, query)
            results.append({'index': index, 'op': query.get('op'), 'ok': True, 'result': value})
        except (ValueError, KeyError) as exc:
            results.append({'index': index, 'op': query.get('op'), 'ok': False, 'error': {'code': 'query.invalid', 'message': str(exc)}})
            all_ok = False
            if stop_on_error:
                break
    emit({'ok': all_ok, 'query_count': len(queries), 'executed': len(results), 'results': results})
    return 0 if all_ok else 3


def cmd_describe(a: argparse.Namespace) -> int:
    if not a.command_name:
        emit(command_tree())
    else:
        emit(command_description(a.command_name))
    return 0


def cmd_command_tree(a: argparse.Namespace) -> int:
    emit(command_tree())
    return 0


def cmd_capabilities(a: argparse.Namespace) -> int:
    full = capabilities()
    full['command_tree'] = command_tree()
    if getattr(a, 'brief', False):
        emit(brief_capabilities(full))
        return 0
    section = getattr(a, 'section', None)
    if section:
        if section not in full:
            suggestions = difflib.get_close_matches(section, list(full), n=5, cutoff=0.4)
            hint = f'; close matches: {", ".join(suggestions)}' if suggestions else ''
            raise ValueError(f'unknown capability section: {section}{hint}')
        emit({'section': section, 'value': full[section]})
        return 0
    emit(full)
    return 0


def cmd_guide(a: argparse.Namespace) -> int:
    emit(guide(a.topic))
    return 0


def cmd_gui_parity(a: argparse.Namespace) -> int:
    report = gui_parity_report()
    if a.gaps:
        report = {**report, 'features': report['gaps']}
    emit(report)
    return 0 if not report['gaps'] else 2


def cmd_fields(a: argparse.Namespace) -> int:
    result = fields_for(a.kind, contains=a.contains, style_group=a.style_group)
    if a.details:
        result['fields'] = fields_details(a.kind, result['fields'])
    emit(result)
    return 0


def cmd_schema(a: argparse.Namespace) -> int:
    if a.kind == 'list':
        emit({
            'native_kinds': catalog_kinds(),
            'protocol_schemas': protocol_schema_names(),
            'note': 'Use native schemas for ICC Plus values and agent-operations/inspect-request for the canonical JSON-first automation contract.',
        })
        return 0
    if a.kind in protocol_schema_names():
        if a.allow_unknown:
            raise ValueError('--allow-unknown applies only to native ICC Plus field schemas')
        emit(load_protocol_schema(a.kind))
        return 0
    emit(json_schema_for_kind(a.kind, additional_properties=a.allow_unknown, mode=a.mode))
    return 0


def cmd_types(a: argparse.Namespace) -> int:
    kinds = cli_strings(a.kind) if a.kind else None
    text = typescript_declarations(kinds, mode=a.mode) if a.format == 'typescript' else python_typeddicts(kinds, mode=a.mode)
    if a.output:
        Path(a.output).write_text(text, encoding='utf-8')
        emit({'ok': True, 'format': a.format, 'mode': a.mode, 'kinds': kinds or 'all', 'written': a.output})
    else:
        # This command intentionally emits source text rather than JSON when no
        # output file is requested, so it can feed tsc/mypy directly.
        print(text)
    return 0


def cmd_project_stats(a: argparse.Namespace) -> int:
    emit({'ok': True, 'source': 'ICC Plus 2.10.6 AppProjectStats.svelte', **project_stats(load(a.project))})
    return 0


def cmd_clean_private_styling(a: argparse.Namespace) -> int:
    project = load(a.project)
    changed = clean_private_styling(project)
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'changed': changed, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_style_template(a: argparse.Namespace) -> int:
    if a.style_action == 'list':
        templates = style_templates()
        emit({
            'ok': True,
            'source_commit': STYLE_TEMPLATE_SOURCE_COMMIT,
            'templates': [
                {'index': i + 1, 'name': name, 'field_count': len(templates[i])}
                for i, name in enumerate(STYLE_TEMPLATE_NAMES)
            ],
        })
        return 0
    if a.style_action == 'show':
        index, name, values = resolve_style_template(a.preset)
        emit({'ok': True, 'index': index + 1, 'name': name, 'source_commit': STYLE_TEMPLATE_SOURCE_COMMIT, 'styling': values})
        return 0

    project = load(a.project)
    index, name = apply_style_template(project, a.preset)
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({
        'ok': report['valid'],
        'written': written,
        'template': {'index': index + 1, 'name': name},
        'source_commit': STYLE_TEMPLATE_SOURCE_COMMIT,
        'validation': report,
    })
    return 0 if report['valid'] else 2



def cmd_row_choices(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    source = editor.resolve(a.row, 'row') if ProjectIndex(project).one(a.row, 'row') else editor.resolve(a.row, 'backpack_row')
    if a.row_action == 'sort':
        order = sort_row_choices(project, source.id, a.by)
        return _finish_structural_write(project, a, {
            'action': 'sort', 'row': source.id, 'by': a.by, 'order': order,
            'source': 'ICC Plus 2.10.6 AppRowSettings.svelte sortObjects',
        })

    target = editor.resolve(a.target)
    if target.kind not in {'row', 'backpack_row'}:
        raise ValueError('row-choices destination must be a Row')
    if target.id == source.id:
        raise ValueError('source and destination Rows must be different')
    choice_ids = [
        str(choice.get('id'))
        for choice in source.value.get('objects', [])
        if isinstance(choice, dict) and isinstance(choice.get('id'), str) and choice.get('id')
    ]
    results: list[dict[str, Any]] = []
    if a.row_action == 'copy':
        for ident in choice_ids:
            results.append(editor.clone(ident, parent=target.id, normalize=False))
        action = 'copy'
    else:
        for ident in choice_ids:
            results.append(editor.move(ident, parent=target.id, normalize=False))
        action = 'copy_and_delete'
    return _finish_structural_write(project, a, {
        'action': action,
        'source_row': source.id,
        'target_row': target.id,
        'choice_count': len(choice_ids),
        'results': results,
        'note': 'Uses the structural editor so nested selectable Addon and Score identities remain valid.',
    })


def cmd_symbols(a: argparse.Namespace) -> int:
    emit({'ok': True, 'source': 'ICC Plus 2.10.6 Features/AppSymbols.svelte', 'count': len(CREATOR_SYMBOLS), 'symbols': CREATOR_SYMBOLS})
    return 0


def cmd_id_csv(a: argparse.Namespace) -> int:
    value = creator_id_csv(load(a.project))
    if a.output:
        Path(a.output).write_text(value, encoding='utf-8')
        emit({'ok': True, 'written': a.output, 'bytes_utf8': len(value.encode('utf-8')), 'includes_backpack': False})
    else:
        emit({'ok': True, 'csv': value, 'includes_backpack': False})
    return 0


def cmd_ids_from_titles(a: argparse.Namespace) -> int:
    project = load(a.project)
    info = ids_from_titles(project)
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'renames': info, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_fonts(a: argparse.Namespace) -> int:
    project = load(a.project)
    if a.font_action == 'list':
        emit({'ok': True, **font_inventory(project)})
        return 0
    info = update_font(project, a.source, a.value, remove=a.font_action == 'remove')
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'font': info, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_build_summary(a: argparse.Namespace) -> int:
    project = load(a.project)
    sim = Simulator(project, seed=a.seed)
    if a.state:
        state_value = json_source(a.state)
        sim.import_state(unwrap_runtime_state(state_value), strict_project=not a.allow_project_mismatch)
    value = sim.export_build_summary(separate_rows=a.separate_rows)
    if a.output:
        Path(a.output).write_text(value, encoding='utf-8')
        emit({'ok': True, 'written': a.output, 'separate_rows': a.separate_rows})
    else:
        emit({'ok': True, 'summary': value, 'separate_rows': a.separate_rows})
    return 0


def cmd_sound_effect(a: argparse.Namespace) -> int:
    project = load(a.project)
    if a.sound_action != 'import':
        raise ValueError(f'unknown sound-effect action: {a.sound_action}')
    src = Path(a.file)
    if not src.is_file():
        raise ValueError(f'sound file does not exist: {src}')
    ext = src.suffix.lower().lstrip('.')
    mime = {'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg', 'm4a': 'audio/mp4', 'aac': 'audio/aac'}.get(ext)
    if mime is None:
        raise ValueError('sound-effect import supports mp3, wav, ogg, m4a, and aac, matching the Creator')
    audio = f'data:{mime};base64,' + base64.b64encode(src.read_bytes()).decode('ascii')
    editor = ProjectEditor(project)
    values = {
        'name': a.name if a.name is not None else src.stem,
        'audio': audio,
        'volume': a.volume,
        'pitch': a.pitch,
        'isDefault': False,
        'onSelected': False,
        'onDeselected': False,
        'requireds': [],
        'groups': [],
    }
    created = editor.add('sound_effect', values=values, normalize=False)
    return _finish_structural_write(project, a, {
        'action': 'import', 'id': created.get('id'), 'name': created.get('name'),
        'mime': mime, 'source_bytes': src.stat().st_size,
    })


def cmd_design(a: argparse.Namespace) -> int:
    project = load(a.project)
    if a.design_action == 'export':
        value = export_design(project, a.target)
        text = json_stringify(value)
        if a.output:
            Path(a.output).write_text(text, encoding='utf-8')
            emit({'ok': True, 'target': a.target, 'written': a.output, 'field_count': len(value['styling'])})
        else:
            emit(value)
        return 0

    value = parse_json_value(a.design)
    info = import_design(project, a.target, value)
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'design': info, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_summary(a: argparse.Namespace) -> int:
    project = load(a.project, require_iccplus=False)
    out = ProjectIndex(project).summary()
    shape = project_shape_diagnostics(project)
    out['format_valid'] = not shape
    if shape:
        out['format_diagnostics'] = [x.to_dict() for x in shape]
    emit(out)
    return 0 if not shape else 2


def cmd_validate(a: argparse.Namespace) -> int:
    report = validate(load(a.project, require_iccplus=False)); emit(report); return 0 if report['valid'] else 2


def cmd_list(a: argparse.Namespace) -> int:
    idx = ProjectIndex(load(a.project))
    ents = list(idx.entities if a.kind == 'all' else idx.by_kind.get(a.kind, []))
    if a.row:
        ents = [e for e in ents if e.row_id == a.row or (e.kind in {'row', 'backpack_row'} and e.id == a.row)]
    if a.parent:
        ents = [e for e in ents if e.parent_id == a.parent]
    if a.group:
        group = idx.one(a.group, 'group')
        if not group:
            raise ValueError(f'group not found: {a.group}')
        members = set(_strings_for_cli(group.value.get('elements'))) | set(_strings_for_cli(group.value.get('rowElements')))
        ents = [e for e in ents if e.id in members or a.group in _strings_for_cli(e.value.get('groups'))]
    if a.id_prefix:
        ents = [e for e in ents if e.id.startswith(a.id_prefix)]
    emit([{'id': e.id, 'kind': e.kind, 'title': e.title, 'path': e.path, 'parent_id': e.parent_id, 'row_id': e.row_id} for e in ents]); return 0


def cmd_get(a: argparse.Namespace) -> int:
    emit(pointer_get(load(a.project), a.pointer)); return 0



def cmd_new(a: argparse.Namespace) -> int:
    output = a.output or str(unique_output_path(Path('project.json')))
    # ICC Plus Save to Disk writes compact JSON with no trailing newline and
    # turns an empty build into activated=[""] via ''.split(',').
    project = default_export_project()
    save(output, project, compact=True, trailing_newline=False)
    emit({'written': output, 'version': project['version']})
    return 0


def cmd_template(a: argparse.Namespace) -> int:
    project = new_project()
    if a.kind == 'category':
        value = make_entity(project, 'category', {'type': 'point', 'name': 'Slot 1'})
    else:
        value = make_entity(project, a.kind, {}, parent=a.parent)
    emit({'kind': a.kind, 'value': value})
    return 0


def cmd_format(a: argparse.Namespace) -> int:
    project = load(a.project)
    creator = a.style == 'creator'
    formatted = creator_save_payload(project) if creator else project
    expected = json_stringify(formatted) if creator else json.dumps(formatted, indent=2, ensure_ascii=False) + '\n'
    source = Path(a.project).read_text(encoding='utf-8')
    if a.check:
        ok = source == expected
        emit({'ok': ok, 'style': a.style, 'project': a.project, 'would_change': not ok})
        return 0 if ok else 2
    target = Path(a.output or a.project)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(expected, encoding='utf-8')
    emit({'ok': True, 'style': a.style, 'written': str(target), 'bytes': len(expected.encode('utf-8'))})
    return 0


def cmd_export_project(a: argparse.Namespace) -> int:
    project = load(a.project)
    report = export_project_zip(project, a.output)
    emit({'ok': True, **report})
    return 0


def cmd_build_viewer(a: argparse.Namespace) -> int:
    project = load(a.project)
    separate = None
    if a.separate_images:
        separate = True
    elif a.embedded_images:
        separate = False
    report = build_viewer_package(project, a.template, a.output, mode=a.mode, separate_images=separate)
    emit({'ok': True, **report})
    return 0


def cmd_crop_image(a: argparse.Namespace) -> int:
    if not a.output and not a.data_url:
        raise ValueError('crop-image requires -o/--output or --data-url so the cropped image is not discarded')
    data, meta = crop_webp(a.source, box=a.box, aspect=a.aspect, position=a.position, quality=a.quality)
    report = {'ok': True, **meta}
    if a.output:
        target = Path(a.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        report['written'] = str(target)
        report['bytes'] = len(data)
    if a.data_url:
        report['data_url'] = webp_data_url(data)
    emit(report)
    return 0


def cmd_image_field(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    ent = editor.resolve(a.reference, a.kind)
    if a.field not in set(fields_for(ent.kind)):
        raise ValueError(f'unknown native field {a.field!r} for {ent.kind}')
    compression = None
    if a.image_action == 'clear':
        value = ''
        source_kind = 'clear'
    else:
        raw = a.source
        if raw.startswith(('http://', 'https://', '//')):
            value = raw
            source_kind = 'remote'
            compression = {'automatic': True, 'changed': False, 'reason': 'remote-url-kept'}
        else:
            value, compression = prepare_image_reference(
                raw,
                base_dir=Path.cwd(),
                embed_local=not bool(a.as_path),
            )
            if raw.startswith('data:'):
                source_kind = 'embedded'
            else:
                source_kind = 'path' if a.as_path else 'embedded'
    editor.update(ent.id, kind=ent.kind, values={a.field: value}, normalize=False)
    payload = {
        'action': a.image_action, 'entity': ent.id, 'kind': ent.kind, 'field': a.field,
        'source_kind': source_kind, 'value_chars': len(value),
    }
    if compression is not None:
        payload['image_compression'] = compression
    return _finish_structural_write(project, a, payload)


def cmd_crop_field(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    ent = editor.resolve(a.reference, a.kind)
    source = ent.value.get(a.field)
    if not isinstance(source, str) or not source:
        raise ValueError(f'{ent.id}.{a.field} is not a non-empty image string')
    if not source.startswith(('data:', 'http://', 'https://')):
        candidate = Path(source)
        if not candidate.is_absolute():
            candidate = Path(a.project).resolve().parent / candidate
        source = str(candidate)
    data, meta = crop_webp(source, box=a.box, aspect=a.aspect, position=a.position, quality=a.quality)
    value, compression = prepare_image_reference(webp_data_url(data), base_dir=Path(a.project).resolve().parent, embed_local=False)
    editor.update(ent.id, kind=ent.kind, values={a.field: value}, normalize=False)
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'entity': ent.id, 'field': a.field, 'crop': meta, 'image_compression': compression, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_add(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    count = int(a.count)
    if count < 1:
        raise ValueError('--count must be at least 1')
    values = field_values(a.values, a.field, field_kind=a.kind)
    created = [editor.add(a.kind, parent=a.parent, values=values, normalize=False) for _ in range(count)]
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    payload: dict[str, Any] = {'ok': report['valid'], 'written': written, 'validation': report}
    if count == 1:
        payload['entity'] = created[0]
    else:
        payload['count'] = count
        payload['entities'] = created
    emit(payload)
    return 0 if report['valid'] else 2


def cmd_set(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    editor.set(a.pointer, parse_relaxed_value(a.value))
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'pointer': a.pointer, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_remove(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    removed = editor.remove(a.pointer)
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'removed': removed, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_rename(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    editor.rename(a.old, a.new, normalize=False)
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'old': a.old, 'new': a.new, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_normalize(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    changes = editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, 'changes': changes, 'validation': report})
    return 0 if report['valid'] else 2


def _finish_structural_write(project: dict[str, Any], a: argparse.Namespace, result: dict[str, Any]) -> int:
    editor = ProjectEditor(project)
    editor.normalize_and_check()
    target = a.output or a.project
    report, written = write_checked(project, target, allow_invalid=a.allow_invalid)
    emit({'ok': report['valid'], 'written': written, **result, 'validation': report})
    return 0 if report['valid'] else 2


def cmd_reorder(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    raw = parse_json_value(a.order) if a.order.strip().startswith(('[','@')) or a.order == '-' else cli_strings([a.order])
    if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
        raise ValueError('ORDER must be a JSON string array, @file, stdin, or comma-separated IDs')
    final = editor.reorder(a.kind, raw, parent=a.parent, partial=a.partial)
    return _finish_structural_write(project, a, {'kind': a.kind, 'parent': a.parent, 'order': final})


def cmd_move(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    moved = editor.move(a.reference, parent=a.parent, index=a.index, normalize=False)
    return _finish_structural_write(project, a, {'moved': moved})


def cmd_clone(a: argparse.Namespace) -> int:
    project = load(a.project)
    editor = ProjectEditor(project)
    cloned = editor.clone(a.reference, parent=a.parent, index=a.index, normalize=False)
    return _finish_structural_write(project, a, {'cloned': cloned})


def cmd_export_fragment(a: argparse.Namespace) -> int:
    project = load(a.project)
    ent = ProjectEditor(project).resolve(a.reference, a.kind)
    value = ent.value
    if a.output:
        text = json_stringify(value) if a.compact_fragment else json.dumps(value, indent=2, ensure_ascii=False)
        if not a.compact_fragment:
            text += '\n'
        Path(a.output).write_text(text, encoding='utf-8')
        emit({'ok': True, 'id': ent.id, 'kind': ent.kind, 'written': a.output})
    else:
        emit(value)
    return 0


def cmd_import_fragment(a: argparse.Namespace) -> int:
    project = load(a.project)
    raw = json_source(a.source)
    if not isinstance(raw, dict):
        raise ValueError('fragment source must be a JSON object')
    editor = ProjectEditor(project)
    imported = editor.import_fragment(a.kind, raw, parent=a.parent, index=a.index, normalize=False)
    return _finish_structural_write(project, a, {'imported': imported})


def identity_report(project: dict[str, Any], *, include_all: bool = False) -> dict[str, Any]:
    idx = ProjectIndex(project)
    entities: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    normal_seen: dict[str, list[dict[str, Any]]] = {}
    category_seen: dict[str, list[dict[str, Any]]] = {}

    identity_kinds = {
        'row', 'backpack_row', 'choice', 'selectable_addon', 'score',
        'point', 'variable', 'word', 'group', 'row_design_group',
        'choice_design_group', 'global_requirement', 'sound_effect', 'category',
    }
    for ent in idx.entities:
        # Ordinary Requirements and non-selectable Addons are structural records in
        # ICC Plus 2.10.6. Their creator defaults intentionally use id: "", so
        # they must not make an otherwise valid project fail an identity audit.
        if ent.kind not in identity_kinds:
            continue
        if ent.kind == 'category':
            present = isinstance(ent.value.get('idx'), int)
            ident = ent.id if present else ''
        else:
            key = 'idx' if ent.kind == 'score' else 'id'
            raw = ent.value.get(key)
            present = raw is not None and bool(str(raw).strip())
            ident = str(raw) if present else ''
        item = {'id': ident, 'kind': ent.kind, 'path': ent.path, 'parent_id': ent.parent_id}
        entities.append(item)
        if not present:
            missing.append(item)
        elif ent.kind == 'category':
            category_seen.setdefault(ident, []).append(item)
        else:
            normal_seen.setdefault(ident, []).append(item)

    duplicates = [items for items in normal_seen.values() if len(items) > 1]
    duplicates.extend(items for items in category_seen.values() if len(items) > 1)
    shape = project_shape_diagnostics(project)
    out: dict[str, Any] = {
        'ok': not missing and not duplicates and not shape,
        'format_valid': not shape,
        'total': len(entities),
        'missing': missing,
        'duplicates': duplicates,
    }
    if shape:
        out['format_diagnostics'] = [x.to_dict() for x in shape]
    if include_all:
        out['entities'] = entities
    return out


def cmd_ids(a: argparse.Namespace) -> int:
    out = identity_report(load(a.project, require_iccplus=False), include_all=a.all)
    emit(out)
    return 0 if out['ok'] else 2


def cmd_check(a: argparse.Namespace) -> int:
    project = load(a.project, require_iccplus=False)
    ids = identity_report(project, include_all=False)
    validation = validate(project)
    summary = ProjectIndex(project).summary()
    out = {
        'ok': bool(ids['ok'] and validation['valid']),
        'summary': summary,
        'identities': ids,
        'validation': validation,
    }
    emit(out)
    return 0 if out['ok'] else 2


def make_sim(a: argparse.Namespace) -> Simulator:
    return Simulator(load(a.project), seed=getattr(a, 'seed', 0), clean=not getattr(a, 'honor_runtime', False))


def apply_after(sim: Simulator, values: list[str] | None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for raw in values or []:
        for token in raw.split(','):
            token = token.strip()
            if not token:
                continue
            ident, times = (token.split('/ON#', 1) + ['1'])[:2] if '/ON#' in token else (token, '1')
            try:
                n = int(times)
            except ValueError:
                n = 1
            event = sim.select(ident, times=max(1, n))
            results.append(event.to_dict())
            if not event.ok:
                return results
    return results


def cmd_status(a: argparse.Namespace) -> int:
    sim = make_sim(a)
    pre = apply_after(sim, a.after)
    failed = next((event for event in pre if not event.get('ok')), None)
    out = {'ok': failed is None, 'pre_actions': pre, 'status': sim.choice_status(a.id).to_dict(), 'state': sim.snapshot(include_choice_status=False)}
    if failed is not None:
        out['error'] = failed
    emit(out)
    return 3 if failed is not None else 0


def cmd_view(a: argparse.Namespace) -> int:
    sim = make_sim(a)
    pre = apply_after(sim, a.after)
    failed = next((event for event in pre if not event.get('ok')), None)
    view = sim.player_view(verbose=bool(a.verbose), include_backpack=bool(a.include_backpack))
    if failed is None:
        emit(view)
        return 0
    safe_pre = [sim.player_event(event) for event in pre]
    safe_failed = next((event for event in safe_pre if not event.get('ok')), sim.player_event(failed))
    emit({'ok': False, 'error': safe_failed, 'pre_actions': safe_pre, 'view': view})
    return 3


def cmd_run(a: argparse.Namespace) -> int:
    sim = make_sim(a); tokens: list[str] = []
    for raw in a.select or []: tokens.extend(x.strip() for x in raw.split(',') if x.strip())
    out = sim.run(tokens)
    emit(out)
    return 0 if out.get('ok') else 3


def cmd_row_button(a: argparse.Namespace) -> int:
    sim = make_sim(a)
    pre = apply_after(sim, a.after)
    failed = next((event for event in pre if not event.get('ok')), None)
    if failed is not None:
        emit({'ok': False, 'pre_actions': pre, 'event': None, 'state': sim.snapshot(include_choice_status=False)})
        return 3
    event = sim.press_row_button(a.id)
    emit({'ok': event.ok, 'pre_actions': pre, 'event': event.to_dict(), 'state': sim.snapshot(include_choice_status=False)})
    return 0 if event.ok else 3


def cmd_pair(a: argparse.Namespace) -> int:
    emit(make_sim(a).pair(a.first, a.second)); return 0


def cmd_matrix(a: argparse.Namespace) -> int:
    ids = None
    if a.ids:
        ids = [x.strip() for raw in a.ids for x in raw.split(',') if x.strip()]
    emit(make_sim(a).compatibility_matrix(ids, both_orders=not a.one_order)); return 0


def cmd_graph(a: argparse.Namespace) -> int:
    project = load(a.project)
    emit({"dependencies": dependency_graph(project), "direct_conflicts": direct_conflicts(project)})
    return 0


def cmd_explore(a: argparse.Namespace) -> int:
    emit(explore(load(a.project), max_depth=a.max_depth, max_states=a.max_states, seed=a.seed, max_multiple=a.max_multiple))
    return 0


def cmd_analyze(a: argparse.Namespace) -> int:
    project = load(a.project)
    sim = Simulator(project, seed=a.seed)
    initial = {}
    for ent in sim.index.selectables(include_backpack=False):
        st = sim.choice_status(ent.id)
        initial[ent.id] = {"selectable": st.selectable, "reasons": st.reasons, "unsupported_effects": st.unsupported_effects}
    out = {
        "validation": validate(project),
        "dependencies": dependency_graph(project),
        "direct_conflicts": direct_conflicts(project),
        "initial_choice_status": initial,
    }
    if a.explore:
        out["exploration"] = explore(project, max_depth=a.max_depth, max_states=a.max_states, seed=a.seed, max_multiple=a.max_multiple)
    emit(out)
    return 0 if out["validation"]["valid"] else 2


def cmd_scenario(a: argparse.Namespace) -> int:
    spec = json_source(a.scenario)
    if not isinstance(spec, dict): raise ValueError('scenario must be a JSON object')
    result = run_scenario(load(a.project), spec, seed=a.seed); emit(result); return 0 if result['passed'] else 3


def cmd_build_string(a: argparse.Namespace) -> int:
    project = load(a.project)
    sim = Simulator(project, seed=a.seed)
    if a.state:
        state_value = json_source(a.state)
        sim.import_state(unwrap_runtime_state(state_value), strict_project=not a.allow_project_mismatch)

    if a.action == 'export':
        value = sim.export_build_string()
        out: dict[str, Any] = {
            'ok': True,
            'format': 'iccplus-2.10.6-build-string',
            'build_string': value,
            'entry_count': len(parse_build_string(value)),
        }
        if a.output:
            Path(a.output).write_text(value, encoding='utf-8')
            out['written'] = a.output
        emit(out)
        return 0

    if a.value is None:
        raise ValueError('build-string import requires VALUE, @file, file path, or - for stdin')
    value = text_source(a.value).strip()
    parsed = parse_build_string(value)
    sim.load_build_string(value)
    runtime_state = sim.export_state(include_events=False)
    if a.state_out:
        save_runtime_state(a.state_out, runtime_state)
    out = {
        'ok': True,
        'format': 'iccplus-2.10.6-build-string',
        'entry_count': len(parsed),
        'entries': [entry_to_dict(entry) for entry in parsed],
        'canonical_build_string': sim.export_build_string(),
        'snapshot': sim.snapshot(include_choice_status=False),
    }
    if a.state_out:
        out['state_written'] = a.state_out
    emit(out)
    return 0


def cmd_session(a: argparse.Namespace) -> int:
    project = load(a.project)
    request: dict[str, Any] = {}
    if a.request is not None:
        loaded = json_source(a.request)
        if not isinstance(loaded, dict):
            raise ValueError('--request must resolve to a JSON object')
        request = loaded

    state_value: Any = request.get('state')
    if state_value is None and a.state_in:
        state_value = json_source(a.state_in)

    seed = int(request.get('seed', a.seed) or 0)
    sim = Simulator(project, seed=seed)
    if state_value is not None:
        sim.import_state(unwrap_runtime_state(state_value), strict_project=not a.allow_project_mismatch)

    actions_value = request.get('actions')
    if actions_value is None:
        actions: list[dict[str, Any]] = []
        actions.extend(action_tokens('select', a.select))
        actions.extend(action_tokens('deselect', a.deselect))
        actions.extend(action_tokens('row_button', a.row_button))
        actions.extend(action_tokens('status', a.status))
        if a.view or a.verbose_view:
            actions.append({'action': 'view', 'verbose': bool(a.verbose_view), 'include_backpack': bool(a.include_backpack)})
    else:
        if not isinstance(actions_value, list):
            raise ValueError('request.actions must be an array')
        actions = actions_value

    player_safe = bool(request.get('player_safe', a.player_safe))
    if player_safe and any(isinstance(x, dict) and x.get('action') == 'snapshot' for x in actions):
        raise ValueError('snapshot action is not available in player-safe mode; use a view action')

    results = sim.apply_actions(actions)
    include_choice_status = bool(request.get('include_choice_status', a.include_choice_status))
    include_events = bool(request.get('include_events_in_state', a.include_events_in_state))
    runtime_state = sim.export_state(include_events=include_events)

    failed = any(
        isinstance(item, dict)
        and isinstance(item.get('event'), dict)
        and item['event'].get('ok') is False
        for item in results
    )
    if a.state_out:
        save_runtime_state(a.state_out, runtime_state)

    if player_safe:
        out: dict[str, Any] = {
            'ok': not failed,
            'mode': 'player_safe_session',
            'results': sim.player_action_results(results),
        }
        if a.state_out:
            out['state_written'] = a.state_out
    else:
        snapshot = sim.snapshot(include_choice_status=include_choice_status)
        out = {
            'ok': not failed,
            'project_fingerprint': project_fingerprint(project),
            'results': results,
            'snapshot': snapshot,
            'runtime_state': runtime_state,
        }
        if a.state_out:
            out['state_written'] = a.state_out
    emit(out)
    return 3 if failed else 0


def _player_visible_ids(view: dict[str, Any]) -> set[str]:
    visible: set[str] = set()
    for key in ('row_ids', 'backpack_row_ids', 'choice_ids', 'addon_ids'):
        values = view.get(key)
        if isinstance(values, list):
            visible.update(str(x) for x in values if isinstance(x, str))
    for key in ('rows', 'backpack'):
        for row in view.get(key, []) if isinstance(view.get(key), list) else []:
            if not isinstance(row, dict):
                continue
            if isinstance(row.get('id'), str):
                visible.add(row['id'])
            for choice in row.get('choices', []) if isinstance(row.get('choices'), list) else []:
                if isinstance(choice, str):
                    visible.add(choice)
                    continue
                if not isinstance(choice, dict):
                    continue
                if isinstance(choice.get('id'), str):
                    visible.add(choice['id'])
                for addon in choice.get('addons', []) if isinstance(choice.get('addons'), list) else []:
                    if isinstance(addon, dict) and isinstance(addon.get('id'), str):
                        visible.add(addon['id'])
    for key in ('choices', 'addons'):
        for item in view.get(key, []) if isinstance(view.get(key), list) else []:
            if isinstance(item, dict) and isinstance(item.get('id'), str):
                visible.add(item['id'])
    return visible


def _player_expectations(view: dict[str, Any], expect: Any) -> list[dict[str, Any]]:
    if expect is None:
        return []
    if not isinstance(expect, dict):
        raise ValueError('play step expect must be a JSON object')
    checks: list[dict[str, Any]] = []

    def add(name: str, actual: Any, expected: Any, ok: bool) -> None:
        checks.append({'name': name, 'ok': bool(ok), 'actual': actual, 'expected': expected})

    point_map = {
        item.get('id'): item.get('value')
        for item in view.get('points', [])
        if isinstance(item, dict) and isinstance(item.get('id'), str)
    }
    for point_id, expected in expect.get('points', {}).items() if isinstance(expect.get('points'), dict) else []:
        add(f'point:{point_id}', point_map.get(point_id), expected, point_map.get(point_id) == expected)

    list_checks = {
        'selected': 'selected_ids',
        'available': 'available_choice_ids',
        'deselectable': 'deselectable_choice_ids',
    }
    for request_key, view_key in list_checks.items():
        wanted = expect.get(request_key)
        if isinstance(wanted, list):
            actual = view.get(view_key, []) if isinstance(view.get(view_key), list) else []
            expected = [str(x) for x in wanted]
            add(request_key, actual, expected, all(x in actual for x in expected))
        not_wanted = expect.get('not_' + request_key)
        if isinstance(not_wanted, list):
            actual = view.get(view_key, []) if isinstance(view.get(view_key), list) else []
            expected = [str(x) for x in not_wanted]
            add('not_' + request_key, actual, expected, all(x not in actual for x in expected))

    visible_ids = _player_visible_ids(view)
    wanted_visible = expect.get('visible')
    if isinstance(wanted_visible, list):
        expected = [str(x) for x in wanted_visible]
        add('visible', sorted(visible_ids), expected, all(x in visible_ids for x in expected))
    wanted_hidden = expect.get('hidden')
    if isinstance(wanted_hidden, list):
        expected = [str(x) for x in wanted_hidden]
        # Hidden and nonexistent IDs are intentionally indistinguishable here.
        add('hidden', sorted(visible_ids), expected, all(x not in visible_ids for x in expected))

    row_choices = expect.get('row_choices')
    if isinstance(row_choices, dict):
        row_map: dict[str, list[str]] = {}
        for key in ('rows', 'backpack'):
            for row in view.get(key, []) if isinstance(view.get(key), list) else []:
                if not isinstance(row, dict) or not isinstance(row.get('id'), str):
                    continue
                ids = row.get('choice_ids')
                if isinstance(ids, list):
                    row_map[row['id']] = [str(x) for x in ids]
                else:
                    nested = row.get('choices') if isinstance(row.get('choices'), list) else []
                    row_map[row['id']] = [
                        str(x if isinstance(x, str) else x.get('id'))
                        for x in nested
                        if isinstance(x, str) or (isinstance(x, dict) and isinstance(x.get('id'), str))
                    ]
        for row_id, wanted in row_choices.items():
            if not isinstance(wanted, list):
                raise ValueError('play expect.row_choices values must be JSON arrays')
            expected = [str(x) for x in wanted]
            actual = row_map.get(str(row_id))
            add(f'row_choices:{row_id}', actual, expected, actual == expected)

    choice_rows = expect.get('choice_rows')
    if isinstance(choice_rows, dict):
        choice_map = {
            item.get('id'): item.get('row_id')
            for item in view.get('choices', [])
            if isinstance(item, dict) and isinstance(item.get('id'), str) and isinstance(item.get('row_id'), str)
        }
        for choice_id, wanted_row in choice_rows.items():
            expected = str(wanted_row)
            actual = choice_map.get(str(choice_id))
            add(f'choice_row:{choice_id}', actual, expected, actual == expected)
    return checks


def _normalize_player_step(step: Any) -> tuple[dict[str, Any], Any]:
    if not isinstance(step, dict):
        raise ValueError('play request steps must be JSON objects')
    expect = step.get('expect')
    if isinstance(step.get('action'), str):
        action = {'action': step['action']}
        if 'id' in step:
            action['id'] = str(step['id'])
        if 'times' in step:
            action['times'] = max(1, int(step['times']))
        return action, expect
    for key in ('select', 'deselect', 'row_button', 'status'):
        if key in step:
            action = {'action': key, 'id': str(step[key])}
            if key == 'select' and 'times' in step:
                action['times'] = max(1, int(step['times']))
            return action, expect
    if step.get('reset') is True:
        return {'action': 'reset'}, expect
    if step.get('view') is True:
        return {'action': 'view'}, expect
    raise ValueError('play step requires action/id, select, deselect, row_button, status, reset, or view')


def _run_player_request(sim: Simulator, spec: dict[str, Any], *, compact_view: bool, include_backpack: bool) -> tuple[dict[str, Any], bool]:
    steps = spec.get('steps', spec.get('actions', []))
    if not isinstance(steps, list):
        raise ValueError('play request steps/actions must be a JSON array')
    verbose = not bool(spec.get('compact_view', compact_view))
    include_bp = bool(spec.get('include_backpack', include_backpack))
    step_results: list[dict[str, Any]] = []
    passed = True
    for index, raw in enumerate(steps):
        action, expect = _normalize_player_step(raw)
        if action['action'] == 'view':
            safe_result: list[dict[str, Any]] = []
            failed = False
        else:
            result = sim.apply_actions([action])
            safe_result = sim.player_action_results(result)
            failed = any(
                isinstance(item, dict)
                and isinstance(item.get('event'), dict)
                and item['event'].get('ok') is False
                for item in result
            )
        view = sim.player_view(verbose=verbose, include_backpack=include_bp)
        checks = _player_expectations(view, expect)
        checks_ok = all(item['ok'] for item in checks)
        ok = not failed and checks_ok
        passed = passed and ok
        item: dict[str, Any] = {'step': index, 'ok': ok, 'action': action, 'results': safe_result, 'view': view}
        if checks:
            item['checks'] = checks
        step_results.append(item)
    final_view = sim.player_view(verbose=verbose, include_backpack=include_bp)
    return {'ok': passed, 'passed': passed, 'mode': 'player_safe_play', 'steps': step_results, 'view': final_view}, passed


def cmd_play(a: argparse.Namespace) -> int:
    """Run player-safe interactions or a multi-step audit request."""
    project = load(a.project)
    state_path = Path(a.state) if a.state else None
    sim = Simulator(project, seed=a.seed)
    if state_path is not None and state_path.exists() and not a.reset:
        try:
            state_value = json.loads(state_path.read_text(encoding='utf-8'))
            sim.import_state(unwrap_runtime_state(state_value), strict_project=not a.allow_project_mismatch)
        except (ValueError, OSError, UnicodeError):
            emit({
                'ok': False,
                'mode': 'player_safe_play',
                'error': {
                    'code': 'state.invalid',
                    'message': 'saved player state is invalid; use --reset or provide a valid state',
                },
            })
            return 2

    if a.request is not None:
        if any((a.select is not None, a.deselect is not None, a.row_button is not None, a.status is not None, a.reset)):
            raise ValueError('play request JSON cannot be combined with direct action flags')
        spec = json_source(a.request)
        if not isinstance(spec, dict):
            raise ValueError('play request must be a JSON object')
        out, passed = _run_player_request(
            sim,
            spec,
            compact_view=bool(a.compact_view),
            include_backpack=bool(a.include_backpack),
        )
        if state_path is not None:
            save_runtime_state(str(state_path), sim.export_state())
            out['state_written'] = str(state_path)
        emit(out)
        return 0 if passed else 3

    actions: list[dict[str, Any]] = []
    if a.select is not None:
        actions.append({'action': 'select', 'id': a.select, 'times': max(1, int(a.times))})
    elif a.deselect is not None:
        actions.append({'action': 'deselect', 'id': a.deselect})
    elif a.row_button is not None:
        actions.append({'action': 'row_button', 'id': a.row_button})
    elif a.status is not None:
        actions.append({'action': 'status', 'id': a.status})
    elif a.reset:
        actions.append({'action': 'reset'})

    results = sim.apply_actions(actions)
    failed = any(
        isinstance(item, dict)
        and isinstance(item.get('event'), dict)
        and item['event'].get('ok') is False
        for item in results
    )
    if state_path is not None:
        save_runtime_state(str(state_path), sim.export_state())
    safe_results = sim.player_action_results(results)
    out: dict[str, Any] = {
        'ok': not failed,
        'mode': 'player_safe_play',
        'results': safe_results,
        'view': sim.player_view(verbose=not a.compact_view, include_backpack=bool(a.include_backpack)),
    }
    if state_path is not None:
        out['state_written'] = str(state_path)
    emit(out)
    return 3 if failed else 0


def cmd_state_check(a: argparse.Namespace) -> int:
    project = load(a.project)
    try:
        value = json_source(a.state)
        document = unwrap_runtime_state(value)
        seed = document.get('seed', 0)
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError('runtime state seed must be an integer')
        sim = Simulator(project, seed=seed)
        sim.import_state(document, strict_project=not a.allow_project_mismatch)
    except (ValueError, OSError, UnicodeError) as exc:
        emit({'valid': False, 'error': str(exc)})
        return 2
    emit({
        'valid': True,
        'format': document.get('format'),
        'format_version': document.get('format_version'),
        'tool_version': document.get('tool_version'),
        'project_fingerprint': document.get('project_fingerprint'),
        'selected_count': len(sim.state.selected_order),
        'point_count': len(sim.state.points),
        'variable_count': len(sim.state.variables),
        'word_count': len(sim.state.words),
    })
    return 0


def add_output_flags(p: argparse.ArgumentParser) -> None:
    group = p.add_mutually_exclusive_group()
    group.add_argument('--compact', action='store_true', default=argparse.SUPPRESS, help='Emit one-line JSON.')
    group.add_argument('--pretty', action='store_true', default=argparse.SUPPRESS, help='Pretty-print JSON even when stdout is not a terminal.')


def add_safe_write_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument('--allow-invalid', action='store_true', help='Write even when validation reports errors. Default is to leave the target unchanged.')



def add_compress_args(p: argparse.ArgumentParser) -> None:
    p.add_argument('inputs', nargs='+', help='Image, text CYOA file, or project directory. Multiple inputs are allowed.')
    p.add_argument('-o', '--output', help='Output file or directory. Omit for a non-destructive sibling output.')
    p.add_argument('--in-place', action='store_true', help='Rewrite supported text files in place. Directory asset rewriting remains copy-based.')
    p.add_argument('--quality', type=int, default=60, help='Image quality from 0 to 100. Default: 60.')
    p.add_argument('--cq', type=int, help='Browser-compressor compatibility quality from 0 to 63. Lower is better. Overrides --quality.')
    p.add_argument('--workers', type=int, default=AssetConfig().workers)
    p.add_argument('--encoder', choices=['auto', 'ffmpeg', 'magick'], default='auto')
    p.add_argument('--assets', choices=['rewrite', 'embedded'], default='rewrite', help='For directories, rewrite local image assets too, or only embedded data URLs.')
    p.add_argument('--gif', dest='gif_mode', choices=['webp', 'keep'], default='webp')
    p.add_argument('--recompress-avif', action='store_true')
    p.add_argument('--min-savings-bytes', type=int, default=256, help='Keep a lossy conversion only when it saves at least this many bytes. Default: 256.')
    p.add_argument('--min-savings-percent', type=float, default=2.0, help='Keep a lossy conversion only when it saves at least this percentage. Default: 2.')
    p.add_argument('--no-convert-any', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--details', action='store_true', help='Include per-file decisions and settings.')



def add_compatibility_commands(sub: argparse._SubParsersAction) -> None:
    """Register retired top-level aliases without advertising them to agents or humans.

    These preserve older scripts while the public interface uses inspect, phased
    authoring, style, and play. New code should not depend on these names.
    """
    hidden = argparse.SUPPRESS
    q = sub.add_parser('project-stats', help=hidden); q.add_argument('project'); q.set_defaults(func=cmd_project_stats)
    q = sub.add_parser('summary', help=hidden); q.add_argument('project'); q.set_defaults(func=cmd_summary)
    q = sub.add_parser('validate', help=hidden); q.add_argument('project'); q.set_defaults(func=cmd_validate)
    q = sub.add_parser('ids', help=hidden); q.add_argument('project'); q.add_argument('--all', action='store_true'); q.set_defaults(func=cmd_ids)
    q = sub.add_parser('list', help=hidden); q.add_argument('project'); q.add_argument('kind', nargs='?', default='choice', choices=['all','row','backpack_row','choice','selectable_addon','addon','score','requirement','point','variable','word','group','row_design_group','choice_design_group','global_requirement','sound_effect','category']); q.add_argument('--row'); q.add_argument('--parent'); q.add_argument('--group'); q.add_argument('--id-prefix'); q.set_defaults(func=cmd_list)
    q = sub.add_parser('search', help=hidden); q.add_argument('project'); q.add_argument('query'); q.add_argument('--kind', default='all', choices=['all','row','backpack_row','choice','selectable_addon','addon','score','requirement','point','variable','word','group','row_design_group','choice_design_group','global_requirement','sound_effect','category']); q.add_argument('--limit', type=int, default=20); q.set_defaults(func=cmd_search)
    q = sub.add_parser('match', help=hidden); q.add_argument('project'); q.add_argument('where'); q.add_argument('--expect'); q.add_argument('--allow-empty', action='store_true'); q.set_defaults(func=cmd_match)
    q = sub.add_parser('get', help=hidden); q.add_argument('project'); q.add_argument('pointer'); q.set_defaults(func=cmd_get)
    q = sub.add_parser('show', help=hidden); q.add_argument('project'); q.add_argument('reference'); q.add_argument('--kind'); q.set_defaults(func=cmd_show)
    q = sub.add_parser('new', help=hidden); q.add_argument('output', nargs='?'); q.set_defaults(func=cmd_new)

    q = sub.add_parser('visual-audit', help=hidden)
    q.add_argument('project'); q.add_argument('--kind', action='append', choices=sorted(VISUAL_KINDS)); q.add_argument('--row'); q.add_argument('--group'); q.add_argument('--missing-images', action='store_true'); q.add_argument('--missing-assets', action='store_true'); q.add_argument('--unstyled', action='store_true'); q.add_argument('--asset-root'); q.add_argument('--limit', type=int); q.add_argument('--manifest-stub', action='store_true'); q.add_argument('--style-values', action='store_true'); q.set_defaults(func=cmd_visual_audit)
    q = sub.add_parser('apply-visuals', help=hidden)
    q.add_argument('project'); q.add_argument('manifest', nargs='?', default='-'); q.add_argument('-o','--output'); q.add_argument('--report-out'); q.add_argument('--no-validate', action='store_true'); q.add_argument('--allow-invalid', action='store_true'); q.add_argument('--dry-run', action='store_true'); q.set_defaults(func=cmd_apply_visuals)

    q = sub.add_parser('add', help=hidden); q.add_argument('project'); q.add_argument('kind', choices=['row','backpack_row','choice','addon','selectable_addon','score','requirement','point','variable','word','group','global_requirement','row_design_group','choice_design_group','sound_effect','category']); q.add_argument('--parent'); q.add_argument('--count', type=int, default=1); q.add_argument('--values'); q.add_argument('-f','--field', action='append'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_add)
    q = sub.add_parser('set', help=hidden); q.add_argument('project'); q.add_argument('pointer'); q.add_argument('value'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_set)
    q = sub.add_parser('remove', help=hidden); q.add_argument('project'); q.add_argument('pointer'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_remove)
    q = sub.add_parser('rename', help=hidden); q.add_argument('project'); q.add_argument('old'); q.add_argument('new'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_rename)
    q = sub.add_parser('normalize', help=hidden); q.add_argument('project'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_normalize)
    q = sub.add_parser('reorder', help=hidden); q.add_argument('project'); q.add_argument('kind', choices=['row','backpack_row','choice','addon','selectable_addon','score','requirement','point','variable','word','group','global_requirement','row_design_group','choice_design_group','sound_effect','category']); q.add_argument('order'); q.add_argument('--parent'); q.add_argument('--partial', action='store_true'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_reorder)
    q = sub.add_parser('move', help=hidden); q.add_argument('project'); q.add_argument('reference'); q.add_argument('--parent', required=True); q.add_argument('--index', type=int); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_move)
    q = sub.add_parser('clone', help=hidden); q.add_argument('project'); q.add_argument('reference'); q.add_argument('--parent'); q.add_argument('--index', type=int); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_clone)
    q = sub.add_parser('project-update', help=hidden); q.add_argument('project'); q.add_argument('--values'); q.add_argument('-f','--field', action='append'); q.add_argument('--unset', action='append'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_project_update)
    q = sub.add_parser('update', help=hidden); q.add_argument('project'); q.add_argument('reference'); q.add_argument('--kind'); q.add_argument('--values'); q.add_argument('-f','--field', action='append'); q.add_argument('--unset', action='append'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_update)
    q = sub.add_parser('delete', help=hidden); q.add_argument('project'); q.add_argument('reference'); q.add_argument('--kind'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_delete)

    for name in ('status', 'run'):
        q = sub.add_parser(name, help=hidden); q.add_argument('project'); q.add_argument('--seed', type=int, default=0); q.add_argument('--honor-runtime', action='store_true')
        if name == 'status': q.add_argument('id'); q.add_argument('--after', action='append'); q.set_defaults(func=cmd_status)
        else: q.add_argument('--select', action='append', required=True); q.set_defaults(func=cmd_run)
    q = sub.add_parser('row-button', help=hidden); q.add_argument('project'); q.add_argument('id'); q.add_argument('--seed', type=int, default=0); q.add_argument('--honor-runtime', action='store_true'); q.add_argument('--after', action='append'); q.set_defaults(func=cmd_row_button)
    q = sub.add_parser('view', help=hidden); q.add_argument('project'); q.add_argument('--seed', type=int, default=0); q.add_argument('--honor-runtime', action='store_true'); q.add_argument('--after', action='append'); q.add_argument('--verbose', action='store_true'); q.add_argument('--include-backpack', action='store_true'); q.set_defaults(func=cmd_view)



def add_creator_namespace(sub: argparse._SubParsersAction) -> None:
    """Register the consolidated Creator-only helper namespace."""
    q = sub.add_parser('creator', help='Creator-specific utilities that are not part of normal phased authoring')
    ct = q.add_subparsers(dest='creator_action', required=True)

    r = ct.add_parser('commands', help='List every advertised CLI command recursively, including nested second- and third-level paths')
    add_output_flags(r); r.set_defaults(func=cmd_command_tree)

    r = ct.add_parser('parity', help='Report ICC Plus 2.10.6 Creator actions and scripting equivalents')
    r.add_argument('--gaps', action='store_true', help='Return only remaining first-class scripting gaps in features.')
    add_output_flags(r); r.set_defaults(func=cmd_gui_parity)

    r = ct.add_parser('clean-style', help='Mirror Creator Clean All Private Styling')
    r.add_argument('project'); r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_clean_private_styling)

    r = ct.add_parser('style-template', help='List, inspect, or apply the eight pinned ICC Plus Creator style templates')
    st = r.add_subparsers(dest='style_action', required=True)
    x = st.add_parser('list', help='List the eight ICC Plus 2.10.6 style templates'); add_output_flags(x); x.set_defaults(func=cmd_style_template)
    x = st.add_parser('show', help='Show one exact pinned style template'); x.add_argument('preset', help='1-based index or exact preset name'); add_output_flags(x); x.set_defaults(func=cmd_style_template)
    x = st.add_parser('apply', help='Apply one pinned style template'); x.add_argument('project'); x.add_argument('preset', help='1-based index or exact preset name'); x.add_argument('-o','--output'); add_safe_write_flags(x); add_output_flags(x); x.set_defaults(func=cmd_style_template)

    r = ct.add_parser('symbols', help='Print the exact Creator Symbols panel list'); add_output_flags(r); r.set_defaults(func=cmd_symbols)
    r = ct.add_parser('id-csv', help='Export the Creator ID / Name List CSV'); r.add_argument('project'); r.add_argument('-o','--output'); add_output_flags(r); r.set_defaults(func=cmd_id_csv)
    r = ct.add_parser('ids-from-titles', help='Apply Creator Change Ids to titles conversion with safe reference rewriting'); r.add_argument('project'); r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_ids_from_titles)

    r = ct.add_parser('fonts', help='Manage project Google Font names and custom stylesheet URLs')
    ft = r.add_subparsers(dest='font_action', required=True)
    x = ft.add_parser('list', help='List project font imports'); x.add_argument('project'); add_output_flags(x); x.set_defaults(func=cmd_fonts)
    for action_name in ('add', 'remove'):
        x = ft.add_parser(action_name, help=f'{action_name.title()} a Google Font name or custom stylesheet URL')
        x.add_argument('project'); x.add_argument('source', choices=['google','url']); x.add_argument('value'); x.add_argument('-o','--output'); add_safe_write_flags(x); add_output_flags(x); x.set_defaults(func=cmd_fonts)

    r = ct.add_parser('sound', help='Manage Creator Sound Effects')
    st = r.add_subparsers(dest='sound_action', required=True)
    x = st.add_parser('import', help='Import an audio file as a data-URL Sound Effect')
    x.add_argument('project'); x.add_argument('file'); x.add_argument('--name'); x.add_argument('--volume', type=float, default=1.0); x.add_argument('--pitch', type=float, default=0.0); x.add_argument('-o','--output'); add_safe_write_flags(x); add_output_flags(x); x.set_defaults(func=cmd_sound_effect)

    r = ct.add_parser('row', help='Creator Row Settings sort/copy/copy-and-delete workflows')
    rt = r.add_subparsers(dest='row_action', required=True)
    x = rt.add_parser('sort', help='Sort one Row exactly like Row Settings'); x.add_argument('project'); x.add_argument('row'); x.add_argument('--by', required=True, choices=ROW_SORT_MODES); x.add_argument('-o','--output'); add_safe_write_flags(x); add_output_flags(x); x.set_defaults(func=cmd_row_choices)
    x = rt.add_parser('copy', help='Copy every Choice in one Row into another Row'); x.add_argument('project'); x.add_argument('row'); x.add_argument('target'); x.add_argument('-o','--output'); add_safe_write_flags(x); add_output_flags(x); x.set_defaults(func=cmd_row_choices)
    x = rt.add_parser('copy-and-delete', help='Move every Choice from one Row into another Row'); x.add_argument('project'); x.add_argument('row'); x.add_argument('target'); x.add_argument('-o','--output'); add_safe_write_flags(x); add_output_flags(x); x.set_defaults(func=cmd_row_choices)

    r = ct.add_parser('design', help='Import or export Creator design JSON')
    dt = r.add_subparsers(dest='design_action', required=True)
    x = dt.add_parser('export', help='Export {version, styling} in Creator design-file format'); x.add_argument('project'); x.add_argument('target', help='global, Row ID, or Choice ID'); x.add_argument('-o','--output'); add_output_flags(x); x.set_defaults(func=cmd_design)
    x = dt.add_parser('import', help='Import Creator design JSON'); x.add_argument('project'); x.add_argument('target', help='global, Row ID, or Choice ID'); x.add_argument('design', help='JSON object, file path, @file, or - for stdin'); x.add_argument('-o','--output'); add_safe_write_flags(x); add_output_flags(x); x.set_defaults(func=cmd_design)



def add_reference_namespace(sub: argparse._SubParsersAction) -> None:
    """Register discovery/reference commands away from the authoring surface."""
    q = sub.add_parser('reference', help='Command discovery, schemas, field references, parity, and environment information')
    rt = q.add_subparsers(dest='reference_action', required=True)

    r = rt.add_parser('commands', help='List the complete canonical command tree recursively'); add_output_flags(r); r.set_defaults(func=cmd_command_tree)
    r = rt.add_parser('capabilities', help='Print machine-readable tool capabilities'); r.add_argument('--brief', action='store_true'); r.add_argument('--section'); add_output_flags(r); r.set_defaults(func=cmd_capabilities)
    r = rt.add_parser('doctor', help='Check optional local tooling and image encoders'); add_output_flags(r); r.set_defaults(func=cmd_doctor)
    r = rt.add_parser('fields', help='List pinned native ICC Plus fields and value types'); r.add_argument('kind', choices=catalog_kinds()); r.add_argument('--contains'); r.add_argument('--style-group', choices=sorted(STYLE_FIELD_GROUPS)); r.add_argument('--details', action='store_true'); add_output_flags(r); r.set_defaults(func=cmd_fields)
    r = rt.add_parser('schema', help='Emit native or automation JSON Schemas'); r.add_argument('kind', choices=['list', *catalog_kinds(), *protocol_schema_names()]); r.add_argument('--mode', choices=['patch','native'], default='patch'); r.add_argument('--allow-unknown', action='store_true'); add_output_flags(r); r.set_defaults(func=cmd_schema)
    r = rt.add_parser('types', help='Generate type-safe declarations from the pinned field catalog'); r.add_argument('--format', choices=['typescript','python'], default='typescript'); r.add_argument('--mode', choices=['patch','native'], default='patch'); r.add_argument('--kind', action='append', choices=catalog_kinds()); r.add_argument('-o','--output'); add_output_flags(r); r.set_defaults(func=cmd_types)
    r = rt.add_parser('guide', help='Print a compact machine-readable workflow guide'); r.add_argument('topic', nargs='?', choices=guide_topics()); add_output_flags(r); r.set_defaults(func=cmd_guide)
    r = rt.add_parser('parity', help='Report ICC Plus Creator actions and scripting equivalents'); r.add_argument('--gaps', action='store_true'); add_output_flags(r); r.set_defaults(func=cmd_gui_parity)
    r = rt.add_parser('symbols', help='Print the exact Creator Symbols panel list'); add_output_flags(r); r.set_defaults(func=cmd_symbols)


def add_template_namespace(sub: argparse._SubParsersAction) -> None:
    """Keep every template/design operation under one template namespace."""
    q = sub.add_parser('template', help='Entity defaults, style presets, and Creator design templates')
    tt = q.add_subparsers(dest='template_action', required=True)

    r = tt.add_parser('entity', help='Print the native default shape for one entity kind')
    r.add_argument('kind', choices=['row','backpack_row','choice','addon','selectable_addon','score','requirement','point','variable','word','group','global_requirement','row_design_group','choice_design_group','sound_effect','category'])
    r.add_argument('--parent', help='Optional parent ID used when generating a sample nested ID'); add_output_flags(r); r.set_defaults(func=cmd_template)

    r = tt.add_parser('style', help='List, inspect, or apply pinned Creator style templates')
    st = r.add_subparsers(dest='style_action', required=True)
    x = st.add_parser('list', help='List the eight ICC Plus 2.10.6 style templates'); add_output_flags(x); x.set_defaults(func=cmd_style_template)
    x = st.add_parser('show', help='Show one exact pinned style template'); x.add_argument('preset'); add_output_flags(x); x.set_defaults(func=cmd_style_template)
    x = st.add_parser('apply', help='Apply one pinned style template'); x.add_argument('project'); x.add_argument('preset'); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_style_template)

    r = tt.add_parser('design', help='Import or export Creator design JSON')
    dt = r.add_subparsers(dest='design_action', required=True)
    x = dt.add_parser('export', help='Export global, Row, or Choice design JSON'); x.add_argument('project'); x.add_argument('target'); x.add_argument('-o','--output'); add_output_flags(x); x.set_defaults(func=cmd_design)
    x = dt.add_parser('import', help='Import global, Row, or Choice design JSON'); x.add_argument('project'); x.add_argument('target'); x.add_argument('design'); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_design)


def add_project_namespace(sub: argparse._SubParsersAction) -> None:
    """Register project serialization/import/export utilities."""
    q = sub.add_parser('project', help='Project formatting, import/export, IDs, fragments, and Build Form serialization')
    pt = q.add_subparsers(dest='project_action', required=True)

    r = pt.add_parser('format', help='Write Creator-compatible or pretty project JSON'); r.add_argument('project'); r.add_argument('--style', choices=['creator','pretty'], default='creator'); r.add_argument('-o','--output'); r.add_argument('--check', action='store_true'); add_output_flags(r); r.set_defaults(func=cmd_format)
    r = pt.add_parser('export', help='Export Project with Separate Images'); r.add_argument('project'); r.add_argument('-o','--output', required=True); add_output_flags(r); r.set_defaults(func=cmd_export_project)

    r = pt.add_parser('fragment', help='Import or export one Creator entity as ordinary ICC Plus JSON')
    ft = r.add_subparsers(dest='fragment_action', required=True)
    x = ft.add_parser('export', help='Export one entity fragment'); x.add_argument('project'); x.add_argument('reference'); x.add_argument('--kind'); x.add_argument('-o','--output'); x.add_argument('--compact-fragment', action='store_true'); add_output_flags(x); x.set_defaults(func=cmd_export_fragment)
    x = ft.add_parser('import', help='Import one entity fragment with safe ID remapping'); x.add_argument('project'); x.add_argument('kind', choices=['row','backpack_row','choice','addon','selectable_addon','score','requirement','point','variable','word','group','global_requirement','row_design_group','choice_design_group','sound_effect','category']); x.add_argument('source'); x.add_argument('--parent'); x.add_argument('--index', type=int); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_import_fragment)

    r = pt.add_parser('ids', help='Export IDs or safely derive IDs from titles')
    it = r.add_subparsers(dest='ids_action', required=True)
    x = it.add_parser('export', help='Export the Creator ID / Name List CSV'); x.add_argument('project'); x.add_argument('-o','--output'); add_output_flags(x); x.set_defaults(func=cmd_id_csv)
    x = it.add_parser('from-titles', help='Change IDs to title-derived IDs with reference rewriting'); x.add_argument('project'); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_ids_from_titles)

    r = pt.add_parser('build-summary', help='Render the Creator Build Form human-readable selected-choice summary'); r.add_argument('project'); r.add_argument('--state'); r.add_argument('--separate-rows', action='store_true'); r.add_argument('-o','--output'); r.add_argument('--seed', type=int, default=0); r.add_argument('--allow-project-mismatch', action='store_true'); add_output_flags(r); r.set_defaults(func=cmd_build_summary)

    r = pt.add_parser('build-string', help='Import or export ICC Plus native Build Form strings')
    r.add_argument('project'); r.add_argument('action', choices=['export','import']); r.add_argument('value', nargs='?'); r.add_argument('--state'); r.add_argument('--state-out'); r.add_argument('-o','--output'); r.add_argument('--seed', type=int, default=0); r.add_argument('--allow-project-mismatch', action='store_true'); add_output_flags(r); r.set_defaults(func=cmd_build_string)

def add_media_namespace(sub: argparse._SubParsersAction) -> None:
    """Register project media resources. Image compression is automatic."""
    q = sub.add_parser('media', help='Images, crops, fonts, sound, and asset inspection; image compression is automatic')
    mt = q.add_subparsers(dest='media_action', required=True)

    r = mt.add_parser('image', help='Import, assign, or clear an entity image field')
    it = r.add_subparsers(dest='image_action', required=True)
    x = it.add_parser('import', help='Import or assign an image'); x.add_argument('project'); x.add_argument('reference'); x.add_argument('source'); x.add_argument('--kind'); x.add_argument('--field', default='image'); x.add_argument('--as-path', action='store_true'); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_image_field)
    x = it.add_parser('clear', help='Clear an entity image field'); x.add_argument('project'); x.add_argument('reference'); x.add_argument('--kind'); x.add_argument('--field', default='image'); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_image_field)

    r = mt.add_parser('crop', help='Crop a standalone image or an entity image field')
    ct = r.add_subparsers(dest='crop_action', required=True)
    x = ct.add_parser('image', help='Crop an image to WebP'); x.add_argument('source'); g=x.add_mutually_exclusive_group(required=True); g.add_argument('--box'); g.add_argument('--aspect'); x.add_argument('--position', type=int, choices=range(9), default=4); x.add_argument('--quality', type=int, default=92); x.add_argument('-o','--output'); x.add_argument('--data-url', action='store_true'); add_output_flags(x); x.set_defaults(func=cmd_crop_image)
    x = ct.add_parser('field', help='Crop an entity image field and write it back'); x.add_argument('project'); x.add_argument('reference'); x.add_argument('--kind'); x.add_argument('--field', default='image'); g=x.add_mutually_exclusive_group(required=True); g.add_argument('--box'); g.add_argument('--aspect'); x.add_argument('--position', type=int, choices=range(9), default=4); x.add_argument('--quality', type=int, default=92); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_crop_field)

    r = mt.add_parser('font', help='Manage project Google Font names and custom stylesheet URLs')
    ft = r.add_subparsers(dest='font_action', required=True)
    x = ft.add_parser('list', help='List project font imports'); x.add_argument('project'); add_output_flags(x); x.set_defaults(func=cmd_fonts)
    for action_name in ('add', 'remove'):
        x = ft.add_parser(action_name, help=f'{action_name.title()} a Google Font name or custom stylesheet URL'); x.add_argument('project'); x.add_argument('source', choices=['google','url']); x.add_argument('value'); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_fonts)

    r = mt.add_parser('sound', help='Manage project sound effects')
    st = r.add_subparsers(dest='sound_action', required=True)
    x = st.add_parser('import', help='Import an audio file as a data-URL Sound Effect'); x.add_argument('project'); x.add_argument('file'); x.add_argument('--name'); x.add_argument('--volume', type=float, default=1.0); x.add_argument('--pitch', type=float, default=0.0); x.add_argument('-o','--output'); x.set_defaults(allow_invalid=False); add_output_flags(x); x.set_defaults(func=cmd_sound_effect)

    r = mt.add_parser('probe', help='Inspect image and embedded-image content without changing files'); r.add_argument('inputs', nargs='+'); add_output_flags(r); r.set_defaults(func=cmd_asset_probe)


def add_test_namespace(sub: argparse._SubParsersAction) -> None:
    """Register deeper runtime analysis under one testing namespace."""
    q = sub.add_parser('test', help='Deep simulator analysis and scenario testing')
    tt = q.add_subparsers(dest='test_action', required=True)

    r = tt.add_parser('pair', help='Analyze selection-order interaction for two choices'); r.add_argument('project'); r.add_argument('first'); r.add_argument('second'); r.add_argument('--seed', type=int, default=0); r.add_argument('--honor-runtime', action='store_true'); add_output_flags(r); r.set_defaults(func=cmd_pair)
    r = tt.add_parser('matrix', help='Analyze pairwise interactions for a set of choices'); r.add_argument('project'); r.add_argument('--ids', action='append'); r.add_argument('--one-order', action='store_true'); r.add_argument('--seed', type=int, default=0); r.add_argument('--honor-runtime', action='store_true'); add_output_flags(r); r.set_defaults(func=cmd_matrix)
    r = tt.add_parser('graph', help='Build the static project interaction graph'); r.add_argument('project'); add_output_flags(r); r.set_defaults(func=cmd_graph)
    r = tt.add_parser('explore', help='Bounded state-space exploration'); r.add_argument('project'); r.add_argument('--max-depth', type=int, default=8); r.add_argument('--max-states', type=int, default=5000); r.add_argument('--max-multiple', type=int, default=3); r.add_argument('--seed', type=int, default=0); add_output_flags(r); r.set_defaults(func=cmd_explore)
    r = tt.add_parser('project', help='Run the combined project analysis report'); r.add_argument('project'); r.add_argument('--seed', type=int, default=0); r.add_argument('--explore', action='store_true'); r.add_argument('--max-depth', type=int, default=8); r.add_argument('--max-states', type=int, default=5000); r.add_argument('--max-multiple', type=int, default=3); add_output_flags(r); r.set_defaults(func=cmd_analyze)
    r = tt.add_parser('scenario', help='Run a deterministic scenario assertion script'); r.add_argument('project'); r.add_argument('scenario', nargs='?', default='-', help='Scenario JSON, @file.json, file path, or - for stdin. Defaults to stdin.'); r.add_argument('--seed', type=int, default=0); add_output_flags(r); r.set_defaults(func=cmd_scenario)


def hide_noncanonical_subcommands(sub: argparse._SubParsersAction) -> None:
    """Keep compatibility aliases parseable without printing them in help."""
    visible = set(COMMAND_KINDS)
    sub._choices_actions[:] = [a for a in sub._choices_actions if getattr(a, 'dest', None) in visible]

def parser() -> argparse.ArgumentParser:
    p = JsonArgumentParser(prog='iccplus-local', description='Author, inspect, validate and headlessly test ICC Plus CYOA JSON.')
    add_output_flags(p)
    p.add_argument('--version', action='version', version=__version__)
    sub = p.add_subparsers(dest='command', required=True, metavar='{' + ','.join(COMMAND_KINDS) + '}')

    q = sub.add_parser('capabilities', help='Print machine-readable CLI capabilities for scripts and LLMs'); q.add_argument('--brief', action='store_true', help='Return the small canonical agent contract instead of the full inventory.'); q.add_argument('--section', help='Return one top-level capability section.'); q.set_defaults(func=cmd_capabilities)
    q = sub.add_parser('describe', help='List the complete recursive command tree or describe one command path'); q.add_argument('command_name', nargs='*', help='Optional command path, for example: creator style-template apply. Omit to list every advertised command at every depth.'); q.set_defaults(func=cmd_describe)
    q = sub.add_parser('doctor', help='Check local optional tooling, including image encoders'); q.set_defaults(func=cmd_doctor)
    q = sub.add_parser('fields', help='List pinned native ICC Plus fields and optionally their value types'); q.add_argument('kind', choices=catalog_kinds()); q.add_argument('--contains', help='Case-insensitive substring filter for field names'); q.add_argument('--style-group', choices=sorted(STYLE_FIELD_GROUPS), help='Limit kind=styling to one styling subgroup'); q.add_argument('--details', action='store_true', help='Include the pinned TypeScript value shape and default when known.'); q.set_defaults(func=cmd_fields)
    q = sub.add_parser('schema', help='Emit native ICC Plus or automation protocol JSON Schemas'); q.add_argument('kind', choices=['list', *catalog_kinds(), *protocol_schema_names()]); q.add_argument('--mode', choices=['patch','native'], default='patch', help='For native kinds: patch allows partial updates; native preserves pinned TypeScript requiredness.'); q.add_argument('--allow-unknown', action='store_true', help='For native kinds only, allow fields outside the pinned 2.10.6 catalog.'); q.set_defaults(func=cmd_schema)
    q = sub.add_parser('types', help='Generate type-safe declarations from the pinned field catalog'); q.add_argument('--format', choices=['typescript','python'], default='typescript'); q.add_argument('--mode', choices=['patch','native'], default='patch', help='patch generates partial-update types; native preserves pinned TypeScript requiredness.'); q.add_argument('--kind', action='append', choices=catalog_kinds(), help='Limit output to a kind. Repeat or comma-separate.'); q.add_argument('-o','--output', help='Write declarations to a file instead of stdout.'); q.set_defaults(func=cmd_types)
    q = sub.add_parser('guide', help='Print a compact machine-readable workflow guide'); q.add_argument('topic', nargs='?', choices=guide_topics()); q.set_defaults(func=cmd_guide)
    add_reference_namespace(sub)
    add_template_namespace(sub)
    add_media_namespace(sub)
    add_project_namespace(sub)
    # Retired grouped surfaces remain parseable for compatibility but are hidden.
    add_creator_namespace(sub)
    add_test_namespace(sub)
    q = sub.add_parser('gui-parity', help='Report ICC Plus 2.10.6 Creator actions and their scripting equivalents'); q.add_argument('--gaps', action='store_true', help='Return only remaining first-class scripting gaps in features.'); q.set_defaults(func=cmd_gui_parity)
    q = sub.add_parser('clean-private-styling', help='Mirror Creator Clean All Private Styling'); q.add_argument('project'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_clean_private_styling)
    q = sub.add_parser('style-template', help='List, inspect, or apply the eight pinned ICC Plus Creator style templates')
    st = q.add_subparsers(dest='style_action', required=True)
    r = st.add_parser('list', help='List the eight ICC Plus 2.10.6 style templates'); add_output_flags(r); r.set_defaults(func=cmd_style_template)
    r = st.add_parser('show', help='Show one exact pinned style template'); r.add_argument('preset', help='1-based index or exact preset name'); add_output_flags(r); r.set_defaults(func=cmd_style_template)
    r = st.add_parser('apply', help='Apply one preset like Object.assign(app.styling, preset) in the Creator'); r.add_argument('project'); r.add_argument('preset', help='1-based index or exact preset name'); r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_style_template)
    q = sub.add_parser('symbols', help='Print the exact symbol list shown by the Creator Symbols panel'); q.set_defaults(func=cmd_symbols)

    q = sub.add_parser('id-csv', help='Export the Creator ID / Name List as its exact CSV shape')
    q.add_argument('project'); q.add_argument('-o','--output'); q.set_defaults(func=cmd_id_csv)

    q = sub.add_parser('ids-from-titles', help='Apply Creator Change Ids to titles conversion with safe reference rewriting')
    q.add_argument('project'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_ids_from_titles)

    q = sub.add_parser('fonts', help='Manage project Google Font names and custom stylesheet URLs')
    ft = q.add_subparsers(dest='font_action', required=True)
    r = ft.add_parser('list', help='List project font imports'); r.add_argument('project'); add_output_flags(r); r.set_defaults(func=cmd_fonts)
    for action_name in ('add', 'remove'):
        r = ft.add_parser(action_name, help=f'{action_name.title()} a Google Font name or custom stylesheet URL')
        r.add_argument('project'); r.add_argument('source', choices=['google','url']); r.add_argument('value'); r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_fonts)

    q = sub.add_parser('sound-effect', help='Manage Creator Sound Effects')
    st = q.add_subparsers(dest='sound_action', required=True)
    r = st.add_parser('import', help='Import an mp3, wav, ogg, m4a, or aac file as a data-URL Sound Effect')
    r.add_argument('project'); r.add_argument('file'); r.add_argument('--name'); r.add_argument('--volume', type=float, default=1.0); r.add_argument('--pitch', type=float, default=0.0); r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_sound_effect)

    q = sub.add_parser('row-choices', help='Mirror Row Settings sort/copy/copy-and-delete workflows')
    rt = q.add_subparsers(dest='row_action', required=True)
    r = rt.add_parser('sort', help='Sort one Row exactly like Row Settings')
    r.add_argument('project'); r.add_argument('row'); r.add_argument('--by', required=True, choices=ROW_SORT_MODES)
    r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_row_choices)
    r = rt.add_parser('copy', help='Copy every Choice in one Row into another Row with safe identity remapping')
    r.add_argument('project'); r.add_argument('row'); r.add_argument('target')
    r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_row_choices)
    r = rt.add_parser('copy-and-delete', help='Move every Choice from one Row into another Row')
    r.add_argument('project'); r.add_argument('row'); r.add_argument('target')
    r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_row_choices)

    q = sub.add_parser('design', help='Import or export global, Row, or Choice design JSON like Creator design dialogs')
    dt = q.add_subparsers(dest='design_action', required=True)
    r = dt.add_parser('export', help='Export {version, styling} in Creator design-file format')
    r.add_argument('project'); r.add_argument('target', help='global, Row ID, or Choice ID'); r.add_argument('-o','--output'); add_output_flags(r); r.set_defaults(func=cmd_design)
    r = dt.add_parser('import', help='Import Creator design JSON and apply scope-specific styling filters')
    r.add_argument('project'); r.add_argument('target', help='global, Row ID, or Choice ID'); r.add_argument('design', help='JSON object, file path, @file, or - for stdin')
    r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_design)

    q = sub.add_parser('inspect', help='Run one or more read-only project queries from a single JSON request'); q.add_argument('project'); q.add_argument('request', nargs='?', default='-', help='Query JSON, @file, file path, or - for stdin. Defaults to stdin.'); q.set_defaults(func=cmd_inspect)
    q = sub.add_parser('check', help='Run shape, identity, and validation checks in one call'); q.add_argument('project'); q.set_defaults(func=cmd_check)


    # `template` is registered above as the consolidated template namespace.
    q = sub.add_parser('format', help='Write project JSON in Creator-compatible or pretty form'); q.add_argument('project'); q.add_argument('--style', choices=['creator','pretty'], default='creator', help='creator reproduces file-import load normalization plus Save to Disk compact JSON with no trailing newline; pretty changes whitespace only.'); q.add_argument('-o','--output'); q.add_argument('--check', action='store_true', help='Do not write; exit 2 when formatting differs.'); q.set_defaults(func=cmd_format)
    q = sub.add_parser('export-project', help='Mirror Creator Export Project with Separate Images'); q.add_argument('project'); q.add_argument('-o','--output', required=True, help='Output ZIP path'); q.set_defaults(func=cmd_export_project)
    q = sub.add_parser('build-viewer', help='Build a playable package from an official ICC Plus viewer template ZIP'); q.add_argument('project'); q.add_argument('--template', required=True, help='Official web_viewer.zip or local_viewer.zip matching the target ICC Plus version'); q.add_argument('-o','--output', required=True, help='Output ZIP path'); q.add_argument('--mode', choices=['web','local'], help='Default comes from viewerConfig.useLocalViewer'); g=q.add_mutually_exclusive_group(); g.add_argument('--separate-images', action='store_true'); g.add_argument('--embedded-images', action='store_true'); q.set_defaults(func=cmd_build_viewer)
    q = sub.add_parser('image-field', help='Import, assign, or clear an entity image field without manual data-URL encoding')
    it = q.add_subparsers(dest='image_action', required=True)
    r = it.add_parser('import', help='Import a local image as a Creator-style data URL, or assign a URL/data URL directly'); r.add_argument('project'); r.add_argument('reference'); r.add_argument('source'); r.add_argument('--kind'); r.add_argument('--field', default='image'); r.add_argument('--as-path', action='store_true', help='Store the supplied local path instead of embedding it'); r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_image_field)
    r = it.add_parser('clear', help='Clear an entity image field'); r.add_argument('project'); r.add_argument('reference'); r.add_argument('--kind'); r.add_argument('--field', default='image'); r.add_argument('-o','--output'); add_safe_write_flags(r); add_output_flags(r); r.set_defaults(func=cmd_image_field)

    q = sub.add_parser('crop-image', help='Crop an image to WebP like the Creator crop action'); q.add_argument('source', help='Image file, URL, or base64 data URL'); g=q.add_mutually_exclusive_group(required=True); g.add_argument('--box', help='Exact x,y,width,height crop in source pixels'); g.add_argument('--aspect', help='Largest crop with WIDTH:HEIGHT aspect'); q.add_argument('--position', type=int, choices=range(9), default=4, help='3x3 Creator crop position, 0 top-left through 8 bottom-right; default 4'); q.add_argument('--quality', type=int, default=92); q.add_argument('-o','--output', help='Write cropped WebP file'); q.add_argument('--data-url', action='store_true', help='Also return the WebP data URL in JSON'); q.set_defaults(func=cmd_crop_image)
    q = sub.add_parser('crop-field', help='Crop an entity image field and write the WebP data URL back into project JSON'); q.add_argument('project'); q.add_argument('reference'); q.add_argument('--kind'); q.add_argument('--field', default='image', help='Top-level string field on the entity, default image'); g=q.add_mutually_exclusive_group(required=True); g.add_argument('--box'); g.add_argument('--aspect'); q.add_argument('--position', type=int, choices=range(9), default=4); q.add_argument('--quality', type=int, default=92); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_crop_field)
    q = sub.add_parser('compress', help='Compress embedded CYOA images and local project image assets'); add_compress_args(q); q.set_defaults(func=cmd_compress)
    q = sub.add_parser('asset-probe', help='Inspect image and embedded-image content without changing files'); q.add_argument('inputs', nargs='+'); q.set_defaults(func=cmd_asset_probe)

    q = sub.add_parser('export-fragment', help='Export one Creator entity as ordinary ICC Plus JSON'); q.add_argument('project'); q.add_argument('reference'); q.add_argument('--kind'); q.add_argument('-o','--output'); q.add_argument('--compact-fragment', action='store_true', help='Write compact fragment JSON when -o is used'); q.set_defaults(func=cmd_export_fragment)
    q = sub.add_parser('import-fragment', help='Import Creator entity JSON, preserving unique IDs and remapping collisions'); q.add_argument('project'); q.add_argument('kind', choices=['row','backpack_row','choice','addon','selectable_addon','score','requirement','point','variable','word','group','global_requirement','row_design_group','choice_design_group','sound_effect','category']); q.add_argument('source', help='Fragment JSON, @file, file path, or - for stdin'); q.add_argument('--parent', help='Destination parent for nested entities'); q.add_argument('--index', type=int, help='Zero-based insertion index; default appends'); q.add_argument('-o','--output'); add_safe_write_flags(q); q.set_defaults(func=cmd_import_fragment)

    q = sub.add_parser('generate', help='Create the exact blank ICC Plus Creator project used as the authoring/build starting point')
    q.add_argument('-o','--output', help='Output project path. Omit for a non-destructive project.json name.')
    q.add_argument('--dry-run', action='store_true', help='Return the blank-project receipt without writing a file.')
    q.set_defaults(func=cmd_generate)

    q = sub.add_parser('build', help='Rebuild project.json from the blank Creator project plus ordered phased authoring steps')
    q.add_argument('manifest', help='Build manifest JSON file, @file, inline JSON, or - for stdin.')
    q.add_argument('-o','--output', required=True, help='Output project.json path. The file is written only after every step and final validation succeed.')
    q.add_argument('--dry-run', action='store_true', help='Execute and validate the full build without writing the output file.')
    q.set_defaults(func=cmd_build)

    for phase_name, phase_help, phase_func in (
        ('structure', 'Apply only structure/content edits such as Rows, Choices, Addons, ordering, moving, cloning, IDs, and text', cmd_structure),
        ('rules', 'Apply only gameplay-rule edits such as Points, Requirements, Scores, Groups, gating, costs, and effects', cmd_rules),
    ):
        q = sub.add_parser(phase_name, help=phase_help)
        q.add_argument('project')
        q.add_argument('script', nargs='?', default='-', help=f'{phase_name} phase JSON, @file, file path, or - for stdin. Defaults to stdin.')
        q.add_argument('-o','--output')
        q.add_argument('--no-validate', action='store_true', help=argparse.SUPPRESS)
        q.add_argument('--allow-invalid', action='store_true', help=argparse.SUPPRESS)
        q.add_argument('--dry-run', action='store_true')
        q.set_defaults(func=phase_func)

    q = sub.add_parser('style', help='Apply presentation/style edits using the visual-manifest format')
    q.add_argument('project')
    q.add_argument('manifest', nargs='?', default='-', help='Style manifest JSON, @file.json, file path, or - for stdin. Defaults to stdin.')
    q.add_argument('-o','--output')
    q.add_argument('--report-out', help='Write the style/source-credit report as JSON')
    q.add_argument('--no-validate', action='store_true', help=argparse.SUPPRESS)
    q.add_argument('--allow-invalid', action='store_true', help=argparse.SUPPRESS)
    q.add_argument('--dry-run', action='store_true')
    q.set_defaults(func=cmd_apply_visuals, canonical_style=True)

    q = sub.add_parser('apply', help='Low-level escape hatch: apply a generic JSON or JSONL batch edit script atomically')
    q.add_argument('project')
    q.add_argument('script', nargs='?', default='-', help='Operation JSON/JSONL, @file, file path, or - for stdin. Defaults to stdin.')
    q.add_argument('-o','--output')
    q.add_argument('--no-validate', action='store_true')
    q.add_argument('--require-valid', action='store_true', help=argparse.SUPPRESS)
    q.add_argument('--allow-invalid', action='store_true', help='Write the batch result even when validation has errors. Default is no write.')
    q.add_argument('--dry-run', action='store_true'); q.add_argument('--result-mode', choices=['full','compact'], help='Response detail. Canonical iccplus-agent-ops scripts default to compact; compatibility scripts default to full.')
    q.set_defaults(func=cmd_apply)

    q = sub.add_parser('pair', help='Analyze selection-order interaction for two choices')
    q.add_argument('project'); q.add_argument('first'); q.add_argument('second'); q.add_argument('--seed', type=int, default=0); q.add_argument('--honor-runtime', action='store_true'); q.set_defaults(func=cmd_pair)
    q = sub.add_parser('matrix', help='Analyze pairwise interactions for a set of choices')
    q.add_argument('project'); q.add_argument('--ids', action='append'); q.add_argument('--one-order', action='store_true'); q.add_argument('--seed', type=int, default=0); q.add_argument('--honor-runtime', action='store_true'); q.set_defaults(func=cmd_matrix)


    q = sub.add_parser('graph'); q.add_argument('project'); q.set_defaults(func=cmd_graph)
    q = sub.add_parser('explore'); q.add_argument('project'); q.add_argument('--max-depth', type=int, default=8); q.add_argument('--max-states', type=int, default=5000); q.add_argument('--max-multiple', type=int, default=3); q.add_argument('--seed', type=int, default=0); q.set_defaults(func=cmd_explore)
    q = sub.add_parser('analyze'); q.add_argument('project'); q.add_argument('--seed', type=int, default=0); q.add_argument('--explore', action='store_true'); q.add_argument('--max-depth', type=int, default=8); q.add_argument('--max-states', type=int, default=5000); q.add_argument('--max-multiple', type=int, default=3); q.set_defaults(func=cmd_analyze)
    q = sub.add_parser('scenario'); q.add_argument('project'); q.add_argument('scenario', nargs='?', default='-', help='Scenario JSON, @file.json, file path, or - for stdin. Defaults to stdin.'); q.add_argument('--seed', type=int, default=0); q.set_defaults(func=cmd_scenario)

    q = sub.add_parser('build-summary', help='Render the Creator Build Form human-readable selected-choice summary')
    q.add_argument('project'); q.add_argument('--state', help='Portable runtime-state/session-response JSON to summarize.'); q.add_argument('--separate-rows', action='store_true', help='Group selections under Row headings like the Creator switch.'); q.add_argument('-o','--output'); q.add_argument('--seed', type=int, default=0); q.add_argument('--allow-project-mismatch', action='store_true'); q.set_defaults(func=cmd_build_summary)

    q = sub.add_parser('build-string', help='Import or export ICC Plus 2.10.6 native Build Form strings')
    q.add_argument('project')
    q.add_argument('action', choices=['export', 'import'])
    q.add_argument('value', nargs='?', help='For import: raw Build Form string, @file, file path, or - for stdin.')
    q.add_argument('--state', help='For export: portable runtime-state/session-response JSON to serialize.')
    q.add_argument('--state-out', help='For import: write the restored portable runtime state here.')
    q.add_argument('-o', '--output', help='For export: write only the raw Build Form string here.')
    q.add_argument('--seed', type=int, default=0, help='Seed for clean state or replay. Build strings carry random outcomes explicitly.')
    q.add_argument('--allow-project-mismatch', action='store_true', help='Allow --state from another project fingerprint for deliberate compatibility testing.')
    q.set_defaults(func=cmd_build_string)

    q = sub.add_parser('session', help='Run or continue a serializable headless CYOA session')
    q.add_argument('project')
    q.add_argument('--state-in', help='Runtime-state/session-response JSON, @file.json, file path, or - for stdin')
    q.add_argument('--state-out', help='Write the resulting portable runtime state here')
    q.add_argument('--request', help='JSON request, @request.json, or - for stdin. Supports state, actions, seed and output flags.')
    q.add_argument('--select', action='append', help='Quick select action. IDs may be comma-separated; use ID/ON#N for repeated selection.')
    q.add_argument('--deselect', action='append', help='Quick deselect action. IDs may be comma-separated or repeated.')
    q.add_argument('--row-button', action='append', help='Press one or more Viewer Row buttons by Row ID.')
    q.add_argument('--status', action='append', help='Query one or more choice IDs after the preceding actions.')
    q.add_argument('--view', action='store_true', help='Append a compact player-visible view after the preceding actions.')
    q.add_argument('--verbose-view', action='store_true', help='Append a verbose player-visible view with titles, descriptions, scores, requirements, Addons, and semantic errors.')
    q.add_argument('--include-backpack', action='store_true', help='Include backpack/result rows in --view or --verbose-view output.')
    q.add_argument('--seed', type=int, default=0)
    q.add_argument('--allow-project-mismatch', action='store_true', help='Load a state whose project fingerprint differs. Use only for deliberate compatibility testing.')
    q.add_argument('--include-choice-status', action='store_true', help='Include selectable_ids and invalid_choices in the final snapshot.')
    q.add_argument('--include-events-in-state', action='store_true', help='Persist event history in the portable state. Runtime continuation does not require it.')
    q.add_argument('--player-safe', action='store_true', help='Emit only sanitized player action results and views. Suppresses snapshot, runtime_state, fingerprint, and raw event details from stdout.')
    q.set_defaults(func=cmd_session)

    q = sub.add_parser('play', help='Run player-safe interactions or a multi-step player-visible audit')
    q.add_argument('project')
    q.add_argument('request', nargs='?', help='Optional player-safe audit JSON, @file, file path, or - for stdin. Supports multiple steps and visible-state expectations.')
    q.add_argument('--state', help='Optional private runtime-state file. When omitted, run ephemerally without saving continuation.')
    action = q.add_mutually_exclusive_group()
    action.add_argument('--select', metavar='ID', help='Select one visible Choice or selectable Addon.')
    action.add_argument('--deselect', metavar='ID', help='Deselect one active Choice or selectable Addon.')
    action.add_argument('--row-button', metavar='ROW_ID', help='Press one visible Viewer Row button.')
    action.add_argument('--status', metavar='ID', help='Query one Choice or selectable Addon through the player-safe status boundary.')
    action.add_argument('--reset', action='store_true', help='Reset the session using Viewer-style clean/reset behavior.')
    q.add_argument('--times', type=int, default=1, help='Repeat count for --select. Default: 1.')
    q.add_argument('--compact-view', action='store_true', help='Return the compact player view instead of titles, descriptions, visible requirements, scores, and Addons.')
    q.add_argument('--include-backpack', action='store_true', help='Include player-visible backpack/result rows in the returned view.')
    q.add_argument('--seed', type=int, default=0, help='Seed for a new state file. A resumed state keeps its saved RNG state.')
    q.add_argument('--allow-project-mismatch', action='store_true', help='Load a state whose project fingerprint differs. Use only for deliberate compatibility testing.')
    q.set_defaults(func=cmd_play)

    q = sub.add_parser('state-check', help='Validate a portable runtime-state file against a project without changing it')
    q.add_argument('project')
    q.add_argument('state', help='Runtime-state/session-response JSON, @file.json, file path, or - for stdin')
    q.add_argument('--allow-project-mismatch', action='store_true', help='Ignore only the project fingerprint mismatch. Structural state checks still apply.')
    q.set_defaults(func=cmd_state_check)


    add_compatibility_commands(sub)
    hide_noncanonical_subcommands(sub)

    # Output switches work before or after the subcommand. Non-interactive stdout
    # defaults to compact JSON, while a terminal defaults to readable JSON.
    for command_parser in sub.choices.values():
        if not any(action.dest == 'compact' for action in command_parser._actions):
            add_output_flags(command_parser)
    return p


def _error_payload(exc: Exception, argv: list[str] | None) -> dict[str, Any]:
    if isinstance(exc, CliUsageError):
        error_type = 'usage'
    elif isinstance(exc, json.JSONDecodeError):
        error_type = 'invalid_json'
    elif isinstance(exc, OSError):
        error_type = 'io'
    elif isinstance(exc, KeyError):
        error_type = 'missing_key'
    else:
        error_type = 'invalid_input'
    args = list(sys.argv[1:] if argv is None else argv)
    command = next((x for x in args if not x.startswith('-')), None)
    return {'ok': False, 'error_type': error_type, 'command': command, 'error': str(exc)}


def main(argv: list[str] | None = None) -> int:
    global _DEFAULT_PRETTY
    try:
        a = parser().parse_args(argv)
        compact = bool(getattr(a, 'compact', False))
        pretty = bool(getattr(a, 'pretty', False))
        _DEFAULT_PRETTY = True if pretty else False if compact else sys.stdout.isatty()
        return int(a.func(a))
    except (CliUsageError, ValueError, KeyError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps(_error_payload(exc, argv), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
