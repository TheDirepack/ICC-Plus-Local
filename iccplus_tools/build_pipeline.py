from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .editor import ProjectEditor
from .model import ProjectIndex
from .operations import apply_operation_script, load_operation_script
from .phase_ops import PHASE_FORMATS, apply_phase_script, load_phase_script
from .simulator import project_fingerprint
from .upstream_2106 import default_export_project
from .validation import validate_complete
from .project_integrity import hydrate_project
from .version import __version__
from .visuals import apply_visual_manifest

BUILD_FORMAT = 'iccplus-build'
BUILD_FORMAT_VERSION = 2
TARGET_VERSION = '2.10.7'
TARGET_COMMIT = '1ea9db888cde2286d18d0d5de50933cb8773b739'
BUILD_PHASES = {'structure', 'rules', 'style', 'raw'}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def load_build_manifest(source: str) -> tuple[dict[str, Any], Path, str]:
    if source == '-':
        import sys
        text = sys.stdin.read()
        base = Path.cwd().resolve()
        label = '<stdin>'
    elif source.startswith('@'):
        path = Path(source[1:]).expanduser().resolve()
        text = path.read_text(encoding='utf-8')
        base = path.parent
        label = str(path)
    else:
        stripped = source.lstrip()
        if stripped.startswith('{'):
            text = source
            base = Path.cwd().resolve()
            label = '<inline>'
        else:
            path = Path(source).expanduser().resolve()
            text = path.read_text(encoding='utf-8')
            base = path.parent
            label = str(path)

    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('build manifest must be a JSON object')
    return value, base, label


def _validate_manifest(manifest: dict[str, Any]) -> tuple[int, list[dict[str, str]]]:
    allowed = {'format', 'format_version', 'steps'}
    unknown = sorted(set(manifest) - allowed)
    if unknown:
        raise ValueError(f'build manifest has unknown top-level field(s): {", ".join(unknown)}')
    if manifest.get('format') != BUILD_FORMAT:
        raise ValueError(f'build manifest format must be {BUILD_FORMAT!r}')
    version = manifest.get('format_version')
    if version not in {1, 2}:
        raise ValueError('build manifest format_version must be 1 or 2')
    steps = manifest.get('steps')
    if not isinstance(steps, list) or not steps:
        raise ValueError('build manifest steps must be a non-empty array')

    out: list[dict[str, str]] = []
    seen_scripts: set[str] = set()
    for index, raw in enumerate(steps):
        if not isinstance(raw, dict):
            raise ValueError(f'build step {index} must be an object')
        step_allowed = {'name', 'script'} if version == 1 else {'name', 'phase', 'script'}
        extra = sorted(set(raw) - step_allowed)
        if extra:
            raise ValueError(f'build step {index} has unknown field(s): {", ".join(extra)}')
        script = raw.get('script')
        if not isinstance(script, str) or not script.strip():
            raise ValueError(f'build step {index}.script must be a non-empty relative path')
        script = script.strip()
        if script in seen_scripts:
            raise ValueError(f'build step {index} repeats script {script!r}')
        seen_scripts.add(script)
        name = raw.get('name')
        if name is not None and (not isinstance(name, str) or not name.strip()):
            raise ValueError(f'build step {index}.name must be a non-empty string when present')
        phase = 'raw' if version == 1 else raw.get('phase')
        if not isinstance(phase, str) or phase not in BUILD_PHASES:
            raise ValueError(f'build step {index}.phase must be one of: {", ".join(sorted(BUILD_PHASES))}')
        out.append({'name': name.strip() if isinstance(name, str) else script, 'phase': phase, 'script': script})
    return int(version), out


def _resolve_step_path(base: Path, relative: str) -> Path:
    raw = Path(relative)
    if raw.is_absolute():
        raise ValueError(f'build step script must be relative to the manifest: {relative!r}')
    candidate = (base / raw).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError(f'build step script escapes the manifest directory: {relative!r}') from exc
    if not candidate.is_file():
        raise ValueError(f'build step script does not exist: {relative!r}')
    return candidate


def _apply_build_step(project: dict[str, Any], phase: str, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if phase in {'structure', 'rules'}:
        script = load_phase_script(str(path), phase)
        return apply_phase_script(project, script, phase, validate_after=False)

    if phase == 'style':
        value = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value, dict):
            raise ValueError('style build step must be a JSON object')
        if value.get('format') != 'iccplus-visual-manifest' or value.get('format_version') != 1:
            raise ValueError('style build step must use iccplus-visual-manifest v1')
        updated, result = apply_visual_manifest(project, value, asset_base=path.parent)
        changes = ProjectEditor(updated).normalize_and_check()
        result['normalization_changes'] = changes
        result['phase'] = 'style'
        return updated, result

    script = load_operation_script(str(path))
    if script.get('format') != 'iccplus-agent-ops' or script.get('format_version') != 1 or script.get('strict_fields') is not True:
        raise ValueError('raw build step must use canonical iccplus-agent-ops v1 with strict_fields=true')
    updated, result = apply_operation_script(project, script, validate_after=False)
    result['phase'] = 'raw'
    return updated, result


def build_from_manifest(manifest: dict[str, Any], *, base: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_version, steps = _validate_manifest(manifest)
    project = default_export_project()
    receipts: list[dict[str, Any]] = []
    fingerprint_parts: list[dict[str, str]] = []

    for index, step in enumerate(steps):
        path = _resolve_step_path(base, step['script'])
        raw = path.read_bytes()
        script_sha = _sha256_bytes(raw)
        updated, result = _apply_build_step(project, step['phase'], path)
        if not result.get('ok', True):
            return project, {
                'ok': False,
                'stage': 'step',
                'step_index': index,
                'step_name': step['name'],
                'phase': step['phase'],
                'script': step['script'],
                'script_sha256': script_sha,
                'error': result.get('error', 'phase step failed'),
                'operation_stage': result.get('stage'),
                'operation_index': result.get('operation_index'),
                'completed_steps': receipts,
            }
        project = updated
        changes = result.get('normalization_changes')
        receipts.append({
            'index': index,
            'name': step['name'],
            'phase': step['phase'],
            'script': step['script'],
            'script_sha256': script_sha,
            'operations_applied': result.get('operations_applied'),
            'normalization_changes': len(changes) if isinstance(changes, list) else 0,
        })
        fingerprint_parts.append({'phase': step['phase'], 'script': step['script'], 'sha256': script_sha})

    hydration_changes = hydrate_project(project)
    validation = validate_complete(project)
    build_fingerprint = 'sha256:' + _sha256_bytes(_canonical_json({
        'format': BUILD_FORMAT,
        'format_version': manifest_version,
        'tool_version': __version__,
        'target_version': TARGET_VERSION,
        'target_commit': TARGET_COMMIT,
        'manifest': manifest,
        'inputs': fingerprint_parts,
    }))
    return project, {
        'ok': validation.get('valid') is True,
        'format': BUILD_FORMAT,
        'format_version': manifest_version,
        'tool_version': __version__,
        'target': {'icc_plus_version': TARGET_VERSION, 'source_commit': TARGET_COMMIT},
        'build_fingerprint': build_fingerprint,
        'project_fingerprint': project_fingerprint(project),
        'steps': receipts,
        'hydration_changes': hydration_changes,
        'summary': ProjectIndex(project).summary(),
        'validation': validation,
    }
