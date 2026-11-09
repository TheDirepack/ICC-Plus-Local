#!/usr/bin/env python3
"""Compare external ICC Plus Viewer race captures with ICC Plus Local replay.

Use matching inputs.zip and races-XXXX.zip archives from one capture run.
Checks observed Viewer row visibility and native Build Form exports, not
screenshots or the correctness of authored prerequisites. Newer captures
may also provide independent main-choice DOM identities.

A match cannot certify uncaptured interactions, Creator GUI behavior,
layout, or an overall race run whose own status is failed/incomplete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iccplus_tools.simulator import Simulator  # noqa: E402


class EvidenceError(ValueError):
    """Missing, inconsistent, or corrupted evidence (not an engine mismatch)."""


def checked_member(archive: ZipFile, manifest: dict, path: str) -> bytes:
    """Only trust files declared in the run's package manifest."""
    entry = (manifest.get('files') or {}).get(path)
    if not isinstance(entry, dict) or 'sha256' not in entry or 'size' not in entry:
        raise EvidenceError(f'undeclared member: {path}')
    try:
        data = archive.read(path)
    except KeyError as exc:
        raise EvidenceError(f'missing member: {path}') from exc
    if len(data) != entry['size'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise EvidenceError(f'checksum/size mismatch: {path}')
    return data


def json_member(archive: ZipFile, manifest: dict, path: str) -> dict:
    value = json.loads(checked_member(archive, manifest, path))
    if not isinstance(value, dict):
        raise EvidenceError(f'expected JSON object: {path}')
    return value


def package_manifest(archive: ZipFile, kind: str) -> dict:
    try:
        manifest = json.loads(archive.read('PACKAGE_MANIFEST.json'))
    except (KeyError, ValueError) as exc:
        raise EvidenceError('missing or invalid PACKAGE_MANIFEST.json') from exc
    if manifest.get('kind') != kind or not manifest.get('run_id'):
        raise EvidenceError(f'wrong package kind/run ID: expected {kind}')
    names = archive.namelist()
    files = manifest.get('files')
    if len(names) != len(set(names)) or not isinstance(files, dict) or (
            set(files) != set(names) - {'PACKAGE_MANIFEST.json'}):
        raise EvidenceError('duplicate/unlisted/missing ZIP members')
    return manifest



_RACE_PART = re.compile(r'^races-(\d{4})\.zip$')


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_run_index(index_path: Path, inputs: Path, races: list[Path],
                     *, run_id: str, source_sha256: str,
                     observed_members: dict[str, list[str]]) -> dict:
    """Verify complete race shard set against Dev220 PACKAGE_INDEX.json.

    This checks full archive digests and exact race-to-part membership.
    Regular ZIPs are inventoried but not verified by this race-only tool;
    use Dev220's verify_evidence_bundle.py for the complete bundle.
    """
    try:
        index = json.loads(index_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f'unreadable PACKAGE_INDEX.json: {exc}') from exc
    if not isinstance(index, dict) or index.get('format') != 'cyra-sharded-package-v3':
        raise EvidenceError('invalid/unsupported PACKAGE_INDEX.json format')
    if index.get('run_id') != run_id or index.get('source_project_sha256') != source_sha256:
        raise EvidenceError('PACKAGE_INDEX.json run/source mismatch')
    archive_records = index.get('archives')
    if not isinstance(archive_records, dict):
        raise EvidenceError('PACKAGE_INDEX.json has no archive inventory')
    records: dict[str, dict] = {}
    for key, record in archive_records.items():
        if not isinstance(record, dict) or record.get('file') != key + '.zip':
            raise EvidenceError(f'invalid index archive record: {key}')
        name = record['file']
        if name in records or not (name == 'inputs.zip' or name == 'regular.zip'
                                   or re.fullmatch(r'(regular|races)-\d{4}\.zip', name)):
            raise EvidenceError(f'unsafe/duplicate index archive name: {name}')
        records[name] = record
    indexed_parts = sorted(name for name in records if _RACE_PART.fullmatch(name))
    supplied_parts = sorted(part.name for part in races)
    expected_parts = [f'races-{n:04d}.zip' for n in range(1, len(indexed_parts) + 1)]
    if (not indexed_parts or indexed_parts != expected_parts or
            supplied_parts != indexed_parts or len(supplied_parts) != len(set(supplied_parts))):
        raise EvidenceError(
            f'incomplete or noncontiguous race ZIP inventory: expected={indexed_parts}, supplied={supplied_parts}')
    if 'inputs.zip' not in records or not any(name.startswith('regular') for name in records):
        raise EvidenceError('index lacks required inputs or regular capture inventory')
    for path in [inputs, *races]:
        if path.name not in records:
            raise EvidenceError(f'archive not in index: {path.name}')
        record = records[path.name]
        if path.stat().st_size != record.get('bytes') or _file_sha256(path) != record.get('sha256'):
            raise EvidenceError(f'whole-archive size/SHA-256 mismatch: {path.name}')
    expected_members = index.get('races')
    if not isinstance(expected_members, dict) or expected_members != observed_members:
        raise EvidenceError('race-to-ZIP inventory differs from PACKAGE_INDEX.json')
    return index


def compare_race(archive: ZipFile, manifest: dict, key: str, project: dict,
                 *, source_sha256: str, require_choice_cards: bool = False) -> dict:
    prefix = f'results/roster/races/{key}/'
    result = {'race': key, 'status': 'pass', 'mismatches': [],
              'choice_card_coverage': 'not_recorded'}
    try:
        state = json_member(archive, manifest, prefix + 'build/normalized_profile.state.json')
        sim = Simulator.from_state(project, state)
        proof = json_member(archive, manifest, prefix + 'viewer_attempt_001/import_verification.json')
        summary = json_member(archive, manifest, prefix + 'viewer_attempt_001/select_scroll_summary.json')
        frames_text = checked_member(archive, manifest, prefix + 'viewer_attempt_001/scroll_frames.jsonl')
        viewer_build = checked_member(archive, manifest, prefix + 'viewer_attempt_001/viewer_build_form_after_scroll.txt').decode('utf-8')
        frames = [json.loads(line) for line in frames_text.decode('utf-8').splitlines() if line.strip()]
        if not frames or summary.get('state') != 'finished' or not summary.get('scroll_reached_end'):
            raise EvidenceError('Viewer scroll is missing or unfinished')
        if summary.get('project_sha256') != source_sha256:
            raise EvidenceError('Viewer capture project SHA-256 differs from inputs')
        if not all(frame.get('status') == 'captured' for frame in frames):
            raise EvidenceError('failed/uncaptured scroll frame')
        if 'native Viewer' not in str(proof.get('verified_by', '')):
            raise EvidenceError('no official Viewer Build Form provenance')
        if not isinstance(proof.get('viewer_native_export'), dict) or not isinstance(proof.get('expected_build_form'), dict):
            raise EvidenceError('missing native and expected Build Form data')
        if proof['viewer_native_export'] != proof['expected_build_form']:
            result['mismatches'].append('native Viewer export differs from headless expected Build Form')
        for field in ('missing_after_import', 'extra_after_import', 'count_mismatches',
                      'text_mismatches', 'missing_requested_after_import'):
            if proof.get(field):
                result['mismatches'].append(f'official Viewer import: {field}')
        if viewer_build.rstrip('\r\n') != sim.export_build_string().rstrip('\r\n'):
            result['mismatches'].append('local Build Form export differs from official Viewer')
        observed_rows = {ident for f in frames for ident in f.get('visible_row_ids', [])}
        expected_rows = set(sim.visible_row_ids())
        result['visible_row_count'] = len(observed_rows)
        result['missing_rows'] = sorted(expected_rows - observed_rows)
        result['unexpected_rows'] = sorted(observed_rows - expected_rows)
        if result['missing_rows'] or result['unexpected_rows']:
            result['mismatches'].append('Viewer DOM row IDs differ from local replay')
        if any('dom_choice_cards' in frame for frame in frames):
            if not all(isinstance(frame.get('dom_choice_cards'), list) for frame in frames):
                raise EvidenceError('partial per-card DOM coverage: some captured frames lack card arrays')
            # Source-only replay on this branch does not model dynamic Result/Group Row
            # card projection. Do not mislabel such displays as a Viewer mismatch.
            if any(row.value.get('isResultRow') or row.value.get('isGroupRow')
                   for row in sim.index.by_kind.get('row', [])):
                raise EvidenceError('dynamic Result/Group Row card projection not available in this checker')
            result['choice_card_coverage'] = 'observed_all_frames'
            observed_pairs: set[tuple[str, str]] = set()
            for frame in frames:
                rendered_here = []
                for card in frame['dom_choice_cards']:
                    if not isinstance(card, dict) or not isinstance(card.get('rendered'), bool):
                        raise EvidenceError('malformed per-card DOM record')
                    if not card['rendered']:
                        continue
                    row_id, choice_id = card.get('row_id'), card.get('choice_id')
                    if not isinstance(row_id, str) or not isinstance(choice_id, str):
                        raise EvidenceError('missing DOM row/choice identity')
                    rendered_here.append((row_id, choice_id))
                    if card.get('selected') != sim._active(choice_id):
                        result['mismatches'].append(f'selected state differs: {choice_id}')
                if len(rendered_here) != len(set(rendered_here)):
                    result['mismatches'].append('duplicate mounted Choice card in one DOM frame')
                observed_pairs.update(rendered_here)
            expected_pairs = {
                (row.id, choice.id)
                for row in sim.index.by_kind.get('row', []) if row.id in expected_rows
                for choice in sim.index.row_choices(row.id) if sim.entity_visible(choice.id)
            }
            result['missing_choice_cards'] = sorted(
                f'{row_id}/{choice_id}' for row_id, choice_id in expected_pairs - observed_pairs)
            result['unexpected_choice_cards'] = sorted(
                f'{row_id}/{choice_id}' for row_id, choice_id in observed_pairs - expected_pairs)
            if result['missing_choice_cards'] or result['unexpected_choice_cards']:
                result['mismatches'].append('Viewer DOM row/Choice pairs differ from local replay')
        elif require_choice_cards:
            raise EvidenceError('per-card DOM capture missing; cannot certify choice visibility')
    except (EvidenceError, KeyError, TypeError, ValueError, RuntimeError, BadZipFile) as exc:
        result['status'] = 'incomplete'
        result['reason'] = str(exc)
        return result
    if result['mismatches']:
        result['status'] = 'mismatch'
    return result


def compare_archives(inputs: Path, races: list[Path], *, require_choice_cards: bool = False,
                     package_index: Path | None = None) -> dict:
    result = {'source': str(inputs), 'races': [str(x) for x in races],
              'passed': 0, 'mismatched': 0, 'incomplete': 0, 'details': [],
              'warnings': [], 'overall_capture_run_passed': True,
              'race_inventory_verified': False}
    seen: set[str] = set()
    observed_members: dict[str, list[str]] = {}
    with ZipFile(inputs) as archive:
        manifest = package_manifest(archive, 'inputs')
        project_bytes = checked_member(archive, manifest, 'inputs/project.json')
        project = json.loads(project_bytes)
        source_sha = hashlib.sha256(project_bytes).hexdigest()
        result['run_id'], result['source_sha256'] = manifest['run_id'], source_sha
        if manifest.get('source_project_sha256') not in (None, source_sha):
            raise EvidenceError('inputs package source hash mismatch')
    for path in races:
        with ZipFile(path) as archive:
            manifest = package_manifest(archive, 'races')
            if manifest['run_id'] != result['run_id']:
                raise EvidenceError(f'{path}: mismatched run ID')
            pinned_source = manifest.get('source_project_sha256')
            if pinned_source is not None and pinned_source != source_sha:
                raise EvidenceError(f'{path}: mismatched source project SHA-256')
            if pinned_source is None:
                result['warnings'].append(f'{path}: legacy archive has no per-part source pin')
            run_status = (manifest.get('notes') or {}).get('status', {}).get('all_passed')
            if run_status is not True:
                result['overall_capture_run_passed'] = False
                if run_status is None:
                    result['warnings'].append(f'{path}: overall run status not recorded')
            keys = sorted({name.split('/')[3] for name in manifest.get('files', {})
                           if name.startswith('results/roster/races/') and len(name.split('/')) > 4})
            if not keys:
                raise EvidenceError(f'{path}: no declared race evidence')
            notes = manifest.get('notes') or {}
            if notes.get('race_keys') is not None and sorted(notes['race_keys']) != keys:
                raise EvidenceError(f'{path}: manifest race keys differ from ZIP members')
            part_match = _RACE_PART.fullmatch(path.name)
            if not part_match:
                raise EvidenceError(f'{path}: noncanonical race ZIP filename')
            if notes.get('part') is not None and notes['part'] != int(part_match.group(1)):
                raise EvidenceError(f'{path}: race-part position differs from filename')
            for key in keys:
                observed_members.setdefault(key, []).append(path.name)
                if key in seen:
                    raise EvidenceError(f'{path}: duplicate race key {key}')
                seen.add(key)
                row = compare_race(archive, manifest, key, project,
                                   source_sha256=source_sha, require_choice_cards=require_choice_cards)
                result['details'].append(row)
                result[{'pass': 'passed', 'mismatch': 'mismatched', 'incomplete': 'incomplete'}[row['status']]] += 1
    if package_index is not None:
        index = verify_run_index(package_index, inputs, races, run_id=result['run_id'],
                                 source_sha256=source_sha, observed_members=observed_members)
        result['race_inventory_verified'] = True
        if (index.get('run_status') or {}).get('all_passed') is not True:
            result['overall_capture_run_passed'] = False
    else:
        result['warnings'].append('PACKAGE_INDEX.json not supplied; race shard completeness unverified')
    result['checked_dimensions_passed'] = bool(result['passed'] and not result['mismatched']
                                                and not result['incomplete'])
    result['fully_verified'] = bool(result['checked_dimensions_passed']
                                    and result['overall_capture_run_passed']
                                    and result['race_inventory_verified']
                                    and not result['warnings']
                                    and all(d['choice_card_coverage'] == 'observed_all_frames'
                                            for d in result['details']))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True, help='matching inputs.zip')
    parser.add_argument('races', nargs='+', type=Path, help='one or more races-XXXX.zip')
    parser.add_argument('--package-index', type=Path,
                        help='Dev220 PACKAGE_INDEX.json; required for full race-inventory verification')
    parser.add_argument('--require-choice-cards', action='store_true',
                        help='mark legacy row-only captures incomplete')
    parser.add_argument('--output', type=Path, help='write full JSON including race-level failures')
    args = parser.parse_args()
    try:
        result = compare_archives(args.inputs, args.races,
                                  require_choice_cards=args.require_choice_cards,
                                  package_index=args.package_index)
    except (EvidenceError, OSError, BadZipFile, ValueError) as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        return 2
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('run_id', 'source_sha256', 'passed',
         'mismatched', 'incomplete', 'race_inventory_verified', 'checked_dimensions_passed', 'fully_verified',
         'overall_capture_run_passed', 'warnings')}, indent=2))
    return 0 if result['fully_verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
