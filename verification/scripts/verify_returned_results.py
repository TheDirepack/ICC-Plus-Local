from __future__ import annotations

import argparse
import json
import posixpath
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = ROOT / 'verification' / 'expected'


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


class ResultBundle:
    def __init__(self, results_path: str, data: dict[str, Any], kind: str, *, base_dir: Path | None = None, zip_path: Path | None = None, zip_members: set[str] | None = None) -> None:
        self.results_path = results_path
        self.data = data
        self.kind = kind
        self.base_dir = base_dir
        self.zip_path = zip_path
        self.zip_members = zip_members

    def artifact_exists(self, relative: str) -> bool:
        rel = relative.replace('\\', '/')
        norm = posixpath.normpath(rel)
        if not rel or norm.startswith('../') or norm == '..' or norm.startswith('/'):
            return False
        if self.kind == 'zip':
            assert self.zip_members is not None
            parent = posixpath.dirname(self.results_path)
            candidate = posixpath.normpath(posixpath.join(parent, norm))
            return candidate in self.zip_members
        assert self.base_dir is not None
        candidate = (self.base_dir / Path(norm)).resolve()
        try:
            candidate.relative_to(self.base_dir.resolve())
        except ValueError:
            return False
        return candidate.is_file()


def _find_result_json_in_directory(path: Path) -> Path:
    direct = path / 'official_results.json'
    if direct.is_file():
        return direct
    matches = sorted(path.rglob('official_results.json'))
    if len(matches) != 1:
        raise ValueError(f'directory must contain exactly one official_results.json; found {len(matches)}')
    return matches[0]


def open_bundle(path: Path) -> ResultBundle:
    if path.is_dir():
        rp = _find_result_json_in_directory(path)
        return ResultBundle(str(rp.relative_to(path)).replace('\\', '/'), load(rp), 'directory', base_dir=rp.parent)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            members = {x.filename.rstrip('/') for x in zf.infolist() if not x.is_dir()}
            matches = sorted(x for x in members if posixpath.basename(x) == 'official_results.json')
            if len(matches) != 1:
                raise ValueError(f'ZIP must contain exactly one official_results.json; found {len(matches)}')
            data = json.loads(zf.read(matches[0]).decode('utf-8'))
        return ResultBundle(matches[0], data, 'zip', zip_path=path, zip_members=members)
    data = load(path)
    if not isinstance(data, dict):
        raise ValueError('result JSON must be an object')
    return ResultBundle(path.name, data, 'json', base_dir=path.parent)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Validate an ICC Plus official-GUI verification result JSON, directory, or ZIP bundle.')
    p.add_argument('results')
    p.add_argument('--allow-incomplete', action='store_true', help='Return success for a structurally valid result even when tests are still pending, blocked, or not applicable.')
    return p


def _expected_steps(spec: dict[str, Any]) -> list[int]:
    return list(range(1, len(spec.get('steps', [])) + 1))


def _check_step_evidence(section: str, ident: str, spec: dict[str, Any], observed: dict[str, Any], status: str, artifacts: list[str], bundle: ResultBundle, issues: list[str]) -> None:
    expected_steps = _expected_steps(spec)
    completed = observed.get('completed_steps')
    if completed != expected_steps:
        issues.append(f'{section}.{ident}.observed.completed_steps must exactly cover {expected_steps}')
    checks = observed.get('checks')
    if not isinstance(checks, list) or not checks:
        issues.append(f'{section}.{ident}.observed.checks must be a non-empty array of official-GUI evidence')
        return
    seen: set[int] = set()
    check_statuses: list[str] = []
    for n, check in enumerate(checks):
        if not isinstance(check, dict):
            issues.append(f'{section}.{ident}.observed.checks[{n}] must be an object')
            continue
        step = check.get('step')
        if not isinstance(step, int) or step not in expected_steps:
            issues.append(f'{section}.{ident}.observed.checks[{n}].step must identify a prescribed step')
        else:
            seen.add(step)
        cstatus = check.get('status')
        if cstatus not in {'pass', 'fail'}:
            issues.append(f'{section}.{ident}.observed.checks[{n}].status must be pass or fail')
        else:
            check_statuses.append(cstatus)
        evidence = check.get('evidence')
        values = check.get('values')
        artifact = check.get('artifact')
        if not str(evidence or '').strip() and not (isinstance(values, dict) and values) and not str(artifact or '').strip():
            issues.append(f'{section}.{ident}.observed.checks[{n}] needs evidence, values, or an artifact')
        if str(artifact or '').strip():
            if artifact not in artifacts:
                issues.append(f'{section}.{ident}.observed.checks[{n}].artifact must also appear in the entry artifacts array')
            elif not bundle.artifact_exists(str(artifact)):
                issues.append(f'{section}.{ident}.observed.checks[{n}].artifact is missing from the returned bundle: {artifact}')
    if set(expected_steps) - seen:
        issues.append(f'{section}.{ident}.observed.checks does not cover every prescribed step')
    if status == 'pass' and any(x != 'pass' for x in check_statuses):
        issues.append(f'{section}.{ident} cannot be pass while an official-GUI step check failed')
    if status == 'fail' and 'fail' not in check_statuses:
        issues.append(f'{section}.{ident} fail needs at least one failed official-GUI step check')


def _subset_mismatches(actual: Any, expected: Any, path: str = '') -> list[str]:
    out: list[str] = []
    if isinstance(actual, dict):
        if not isinstance(expected, dict):
            return [f'{path or "snapshot"}: expected non-object {expected!r}, observed object']
        for key, value in actual.items():
            sub = f'{path}.{key}' if path else str(key)
            if key not in expected:
                out.append(f'{sub}: field is not part of the packaged expected runtime state')
            else:
                out.extend(_subset_mismatches(value, expected[key], sub))
        return out
    if isinstance(actual, list):
        if actual != expected:
            out.append(f'{path}: observed {actual!r} != expected {expected!r}')
        return out
    if actual != expected:
        out.append(f'{path}: observed {actual!r} != expected {expected!r}')
    return out


def _has_snapshot_path(snapshot: dict[str, Any], path: str) -> bool:
    value: Any = snapshot
    for part in path.split('.'):
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return True


def _check_runtime_evidence(section: str, ident: str, spec: dict[str, Any], observed: dict[str, Any], status: str, issues: list[str]) -> None:
    actions = spec.get('actions', [])
    action_observations = observed.get('action_observations')
    if not isinstance(action_observations, list) or len(action_observations) != len(actions):
        issues.append(f'{section}.{ident}.observed.action_observations must contain exactly {len(actions)} entries')
        action_observations = []
    mismatches_all: list[str] = []
    expected_steps = spec.get('expected_after_actions', [])
    required_steps = spec.get('required_after_actions', [])
    for n, action_obs in enumerate(action_observations, 1):
        if not isinstance(action_obs, dict):
            issues.append(f'{section}.{ident}.observed.action_observations[{n-1}] must be an object')
            continue
        if action_obs.get('step') != n:
            issues.append(f'{section}.{ident}.observed.action_observations[{n-1}].step must be {n}')
        snap = action_obs.get('snapshot')
        if not isinstance(snap, dict) or not snap:
            issues.append(f'{section}.{ident}.observed.action_observations[{n-1}].snapshot must contain concrete official-Viewer state')
            continue
        expected = expected_steps[n-1] if n-1 < len(expected_steps) else {}
        mismatches = _subset_mismatches(snap, expected)
        mismatches_all.extend(f'action {n}: {x}' for x in mismatches)
        required = required_steps[n-1] if n-1 < len(required_steps) else []
        for path in required:
            if not _has_snapshot_path(snap, path):
                issues.append(f'{section}.{ident}.observed.action_observations[{n-1}].snapshot must include changed field {path!r}')
    snapshot = observed.get('snapshot')
    if not isinstance(snapshot, dict) or not snapshot:
        issues.append(f'{section}.{ident}.observed.snapshot must contain concrete final official-Viewer state')
    else:
        mismatches_all.extend(f'final: {x}' for x in _subset_mismatches(snapshot, spec.get('expected', {})))
        if not actions:
            for req_id in spec.get('check_requirements', []):
                path = f'requirements.{req_id}'
                if not _has_snapshot_path(snapshot, path):
                    issues.append(f'{section}.{ident}.observed.snapshot must include required observation {path!r}')
    if status == 'pass' and mismatches_all:
        issues.extend(f'{section}.{ident}.observed runtime mismatch: {x}' for x in mismatches_all)
    if status == 'fail' and not mismatches_all and not str(observed.get('failure', '')).strip():
        issues.append(f'{section}.{ident} fail needs an observed state mismatch or observed.failure')


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        bundle = open_bundle(Path(args.results))
    except Exception as exc:
        print(json.dumps({'schema_ok': False, 'complete': False, 'ok': False, 'issues': [str(exc)], 'incomplete': []}, indent=2))
        return 1
    data = bundle.data
    runtime = load(EXPECTED / 'runtime_cases.json')
    creator = load(EXPECTED / 'creator_cases.json')
    advanced = load(EXPECTED / 'advanced_cases.json')
    issues: list[str] = []
    incomplete: list[str] = []

    if data.get('format') != 'iccplus-official-gui-results-v2':
        issues.append('wrong or missing result format; expected iccplus-official-gui-results-v2')
    expected_version = (ROOT / 'VERSION').read_text().strip()
    if data.get('tested_tool_version') != expected_version:
        issues.append(f"tested_tool_version must be {expected_version!r}")
    if data.get('official_gui_version') != '2.10.6':
        issues.append("official_gui_version must be '2.10.6'")
    if not str(data.get('official_gui_url_or_build', '')).strip():
        incomplete.append('official_gui_url_or_build is empty')
    if not str(data.get('browser', '')).strip():
        incomplete.append('browser is empty')
    if not str(data.get('finished_at', '')).strip():
        incomplete.append('finished_at is empty')

    fixture_hashes = load(EXPECTED / 'fixture_hashes.json')
    sections = [
        ('runtime_results', runtime, True),
        ('creator_results', creator, True),
        ('advanced_results', advanced, True),
    ]
    allowed_status = {'pass','fail','blocked','not_applicable','pending'}
    allowed_sources = {'official_gui','local_tool','source_only'}
    for section, specs, require_gui in sections:
        got = data.get(section)
        if not isinstance(got, dict):
            issues.append(f'{section} must be an object')
            continue
        ids = [x['id'] for x in specs]
        missing = [x for x in ids if x not in got]
        if missing:
            issues.append(f'{section} missing: {", ".join(missing)}')
        for spec in specs:
            ident = spec['id']
            item = got.get(ident)
            if not isinstance(item, dict):
                continue
            status = item.get('status')
            if status not in allowed_status:
                issues.append(f'{section}.{ident}.status must be pass/fail/blocked/not_applicable/pending')
                continue
            source = item.get('observation_source')
            if source not in allowed_sources:
                issues.append(f'{section}.{ident}.observation_source must be official_gui/local_tool/source_only')
            if require_gui and status in {'pass','fail'} and source != 'official_gui':
                issues.append(f'{section}.{ident} may only be pass/fail when observation_source is official_gui')
            fixture = spec.get('fixture') or ('fixtures/03_advanced_interaction_export.json' if section == 'advanced_results' else None)
            if fixture:
                if item.get('fixture') != fixture:
                    issues.append(f'{section}.{ident}.fixture must be {fixture!r}')
                expected_hash = spec.get('fixture_sha256') or fixture_hashes.get(fixture, {}).get('sha256')
                if expected_hash and item.get('fixture_sha256') != expected_hash:
                    issues.append(f'{section}.{ident}.fixture_sha256 must match the packaged fixture')
            observed = item.get('observed')
            artifacts = item.get('artifacts')
            if not isinstance(observed, dict):
                issues.append(f'{section}.{ident}.observed must be an object')
                observed = {}
            if not isinstance(artifacts, list):
                issues.append(f'{section}.{ident}.artifacts must be an array')
                artifacts = []
            for n, artifact in enumerate(artifacts):
                if not isinstance(artifact, str) or not artifact.strip():
                    issues.append(f'{section}.{ident}.artifacts[{n}] must be a non-empty relative path')
                elif not bundle.artifact_exists(artifact):
                    issues.append(f'{section}.{ident}.artifacts[{n}] is missing from the returned bundle: {artifact}')
            required_artifacts = int(spec.get('required_artifacts_min', 0) or 0)
            if status in {'pass','fail'} and len(artifacts) < required_artifacts:
                issues.append(f'{section}.{ident} requires at least {required_artifacts} returned artifact(s)')
            if status in {'pass','fail'}:
                if section == 'runtime_results':
                    _check_runtime_evidence(section, ident, spec, observed, status, issues)
                else:
                    _check_step_evidence(section, ident, spec, observed, status, artifacts, bundle, issues)
            if status in {'fail','blocked','not_applicable'} and not str(item.get('notes','')).strip():
                issues.append(f'{section}.{ident} needs notes for {status}')
            if status in {'pending','blocked','not_applicable'}:
                incomplete.append(f'{section}.{ident} is {status}')

    schema_ok = not issues
    complete = schema_ok and not incomplete
    report = {
        'schema_ok': schema_ok,
        'complete': complete,
        'ok': complete,
        'bundle_kind': bundle.kind,
        'results_path': bundle.results_path,
        'issues': issues,
        'incomplete': incomplete,
    }
    print(json.dumps(report, indent=2))
    if issues:
        return 1
    if incomplete and not args.allow_incomplete:
        return 3
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
