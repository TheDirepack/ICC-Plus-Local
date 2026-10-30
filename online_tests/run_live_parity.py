#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import html
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iccplus_tools.live_parity import live_cases, local_results, run_local_case_trace, sparse_equivalence_cases
from iccplus_tools.upstream_2106 import ICCPLUS_COMMIT, ICCPLUS_VERSION, default_export_text
from online_tests.source_format_check import compare_type_catalog

REPO = 'https://github.com/wahaha303/ICC-Plus-Svelte.git'


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if check and cp.returncode != 0:
        raise RuntimeError(f"command failed ({cp.returncode}): {' '.join(cmd)}\nstdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
    return cp


def locate_chromium(explicit: str | None) -> str:
    candidates = [explicit, os.environ.get('CHROMIUM'), 'chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable']
    for candidate in candidates:
        if candidate and shutil.which(candidate):
            return shutil.which(candidate) or candidate
    raise RuntimeError('Chromium/Chrome not found; set CHROMIUM=/path/to/browser')


def prepare_checkout(base: Path, upstream_dir: Path | None) -> Path:
    if upstream_dir is None:
        checkout = base / 'ICC-Plus-Svelte'
        run(['git', 'clone', '--filter=blob:none', REPO, str(checkout)], timeout=300)
    else:
        source = upstream_dir.resolve()
        if not (source / '.git').exists():
            raise RuntimeError(f'--upstream-dir is not a git checkout: {source}')
        checkout = base / 'ICC-Plus-Svelte'
        run(['git', 'clone', '--no-hardlinks', str(source), str(checkout)], timeout=180)
    run(['git', 'checkout', '--detach', ICCPLUS_COMMIT], cwd=checkout, timeout=120)
    actual = run(['git', 'rev-parse', 'HEAD'], cwd=checkout).stdout.strip()
    if actual != ICCPLUS_COMMIT:
        raise RuntimeError(f'wrong upstream commit: {actual}')
    return checkout


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        pass


def serve(directory: Path):
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    handler = lambda *a, **kw: QuietHandler(*a, directory=str(directory), **kw)
    server = ThreadingHTTPServer(('127.0.0.1', port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def extract_payload(dom: str) -> dict:
    marker = '<pre id="parity-results">'
    start = dom.find(marker)
    if start < 0:
        raise RuntimeError('parity result element not found in Chromium output')
    start += len(marker)
    end = dom.find('</pre>', start)
    if end < 0:
        raise RuntimeError('unterminated parity result element')
    text = html.unescape(dom[start:end]).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        title_start = dom.find('<title>')
        title_end = dom.find('</title>', title_start + 7) if title_start >= 0 else -1
        title = dom[title_start + 7:title_end] if title_end >= 0 else '(unknown)'
        raise RuntimeError(
            f'Viewer parity harness produced non-JSON output (title={title!r}, '
            f'pre={text[:700]!r}, dom_bytes={len(dom)}): {exc}'
        ) from exc


def compare(upstream: dict) -> list[str]:
    errors: list[str] = []
    if upstream.get('appVersion') != ICCPLUS_VERSION:
        errors.append(f"appVersion: upstream={upstream.get('appVersion')!r}, expected={ICCPLUS_VERSION!r}")
    if upstream.get('defaultExport') != default_export_text():
        errors.append('default exported project bytes differ from ICC Plus 2.10.16 source runtime')
    if upstream.get('emptySelectedObjectId') != '':
        errors.append(f"empty getSelectedObjectId() returned {upstream.get('emptySelectedObjectId')!r}")
    local = local_results()
    remote = upstream.get('results', {})
    for name in sorted(set(local) | set(remote)):
        if name not in local:
            errors.append(f'{name}: exists only upstream')
        elif name not in remote:
            errors.append(f'{name}: missing upstream result')
        elif local[name] != remote[name]:
            errors.append(f'{name}: local != upstream\n  local={json.dumps(local[name], sort_keys=True)}\n  upstream={json.dumps(remote[name], sort_keys=True)}')
    expected_action_cases = {c['name']: c for c in live_cases() if c.get('check_action_trace')}
    actual_traces = upstream.get('actionTraces', {})
    if set(actual_traces) != set(expected_action_cases):
        errors.append(
            f'action trace inventory differs: local={sorted(expected_action_cases)} '
            f'upstream={sorted(actual_traces)}'
        )
    for name, case in sorted(expected_action_cases.items()):
        remote_trace = actual_traces.get(name)
        if not isinstance(remote_trace, list):
            continue
        local_trace = run_local_case_trace(case)
        if len(local_trace) != len(remote_trace):
            errors.append(f'{name}: action checkpoints differ in length: local={len(local_trace)} upstream={len(remote_trace)}')
        for step, (local_snap, remote_snap) in enumerate(zip(local_trace, remote_trace)):
            if local_snap != remote_snap:
                errors.append(
                    f'{name}/step-{step}: local != upstream '
                    f'local={json.dumps(local_snap, sort_keys=True)} '
                    f'upstream={json.dumps(remote_snap, sort_keys=True)}'
                )
    sparse_local = {c['name'] for c in sparse_equivalence_cases()}
    sparse_remote = upstream.get('sparseResults', {})
    if set(sparse_remote) != sparse_local:
        errors.append(f'sparse fixture inventory differs: local={sorted(sparse_local)} upstream={sorted(sparse_remote)}')
    for name, runs in sorted(sparse_remote.items()):
        if runs.get('baseline') != runs.get('candidate'):
            errors.append(
                f'sparse/{name}: official Viewer outcomes differ between full and sparse project '
                f'baseline={json.dumps(runs.get("baseline"), sort_keys=True)} '
                f'candidate={json.dumps(runs.get("candidate"), sort_keys=True)}'
            )
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description='Run live differential tests against pinned ICC Plus 2.10.16 source')
    ap.add_argument('--upstream-dir', type=Path, help='existing ICC-Plus-Svelte git checkout; avoids cloning from GitHub')
    ap.add_argument('--chromium', help='Chromium/Chrome executable')
    ap.add_argument('--keep-workdir', action='store_true')
    args = ap.parse_args()

    temp = Path(tempfile.mkdtemp(prefix='iccplus-live-parity-'))
    try:
        checkout = prepare_checkout(temp, args.upstream_dir)
        viewer = checkout / 'ICCPlus_Viewer'
        harness = ROOT / 'online_tests' / 'ParityHarness.svelte'
        shutil.copy2(harness, viewer / 'src' / 'App.svelte')
        fixtures = {'commit': ICCPLUS_COMMIT, 'cases': live_cases(), 'sparse_cases': sparse_equivalence_cases()}
        (viewer / 'public' / 'parity-fixtures.json').write_text(json.dumps(fixtures, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

        install = run(['npm', 'ci', '--no-audit', '--no-fund'], cwd=viewer, check=False, timeout=900)
        if install.returncode != 0:
            # Official 2.10.16 Viewer lockfile is missing picomatch@4.0.7.
            # Repair it only in this disposable checkout, never in the pinned source.
            if 'EUSAGE' not in install.stderr or 'Missing:' not in install.stderr:
                raise RuntimeError('pinned Viewer npm ci failed: ' + install.stderr)
            print('Upstream Viewer lockfile incomplete; repairing disposable checkout', file=sys.stderr)
            run(['npm', 'install', '--package-lock-only', '--ignore-scripts', '--no-audit', '--no-fund'],
                cwd=viewer, timeout=900)
            run(['npm', 'ci', '--no-audit', '--no-fund'], cwd=viewer, timeout=900)
        run(['npx', 'vite', 'build', '--outDir', 'parity-dist', '--emptyOutDir'], cwd=viewer, timeout=600)

        browser = locate_chromium(args.chromium)
        server, port = serve(viewer / 'parity-dist')
        try:
            cp = run([
                browser, '--headless', '--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage',
                '--virtual-time-budget=60000', '--dump-dom', f'http://127.0.0.1:{port}/',
            ], check=True, timeout=90)
        finally:
            server.shutdown()
            server.server_close()
        payload = extract_payload(cp.stdout)
        if payload.get('error'):
            raise RuntimeError(f"upstream harness failed: {payload['error']}\n{payload.get('stack', '')}")
        errors = compare(payload)
        errors.extend(f'format: {msg}' for msg in compare_type_catalog(checkout))
        report = {
            'ok': not errors,
            'source_commit': ICCPLUS_COMMIT,
            'version': ICCPLUS_VERSION,
            'cases': len(live_cases()),
            'action_trace_cases': sum(bool(c.get('check_action_trace')) for c in live_cases()),
            'sparse_equivalence_cases': len(sparse_equivalence_cases()),
            'errors': errors,
        }
        print(json.dumps(report, indent=2))
        return 0 if not errors else 1
    finally:
        if args.keep_workdir:
            print(f'kept workdir: {temp}', file=sys.stderr)
        else:
            shutil.rmtree(temp, ignore_errors=True)


if __name__ == '__main__':
    raise SystemExit(main())
