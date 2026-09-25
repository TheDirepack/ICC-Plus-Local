from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import stat
import struct
import subprocess
import zlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'examples' / 'demo_project.json'




def rgba_png(width=128, height=128):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(((x * 2) & 255, (y * 2) & 255, (x + y) & 255, 128 if (x + y) % 3 else 255))
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xffffffff)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )

class CliResult:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_cli(*args: str, stdin: str | None = None) -> CliResult:
    # Exercise the real argparse/main dispatch without paying for a fresh Python
    # interpreter for every test. Module-entry-point parity is covered by the
    # exact default-export subprocess test in tests/test_upstream_parity.py.
    from iccplus_tools.cli import main

    out = io.StringIO()
    err = io.StringIO()
    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(stdin or '')
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main(list(args))
            except SystemExit as exc:
                code = int(exc.code or 0)
    finally:
        sys.stdin = old_stdin
    return CliResult(int(code), out.getvalue(), err.getvalue())


class CliTests(unittest.TestCase):
    def test_capabilities_command_is_json(self):
        result = run_cli('capabilities', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['interface'], 'command-line')
        self.assertIn('generate', value['command_kinds'])
        self.assertIn('gate', value['operation_kinds'])

    def test_capabilities_uses_smart_output_default(self):
        result = run_cli('capabilities')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('\n', result.stdout.strip())
        self.assertEqual(json.loads(result.stdout)['tool'], 'iccplus-local')

    def test_fields_command_filters_native_fields(self):
        result = run_cli('fields', 'choice', '--contains', 'discount', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['kind'], 'choice')
        self.assertGreater(value['count'], 10)
        self.assertTrue(all('discount' in name.lower() for name in value['fields']))
        self.assertIn('discountOther', value['fields'])
        self.assertEqual(value['source']['icc_plus_version'], '2.10.7')

    def test_fields_command_suggests_close_names_when_filter_misses(self):
        result = run_cli('fields', 'choice', '--contains', 'titel')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['count'], 0)
        self.assertIn('title', value['suggestions'])

    def test_fields_command_supports_styling_subgroups(self):
        result = run_cli('fields', 'styling', '--style-group', 'filter', '--contains', 'visible', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['style_group'], 'filter')
        self.assertIn('selFilterVisibleIsOn', value['fields'])
        self.assertIn('reqFilterVisibleIsOn', value['fields'])
        self.assertIn('unselFilterVisibleIsOn', value['fields'])

    def test_fields_details_exposes_types(self):
        result = run_cli('fields', 'choice', '--contains', 'randomWeight', '--details', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['fields'][0]['name'], 'randomWeight')
        self.assertEqual(value['fields'][0]['type'], 'number')

    def test_schema_command_emits_native_field_schema(self):
        result = run_cli('schema', 'choice', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertFalse(value['additionalProperties'])
        self.assertEqual(value['properties']['isAutoActive']['type'], 'boolean')

    def test_types_command_generates_typescript(self):
        result = run_cli('types', '--format', 'typescript', '--kind', 'choice')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('export interface ChoicePatch', result.stdout)
        self.assertIn('randomWeight?: number;', result.stdout)

    def test_native_schema_and_types_preserve_requiredness(self):
        schema = run_cli('schema', 'choice', '--mode', 'native', '--compact')
        self.assertEqual(schema.returncode, 0, schema.stderr)
        value = json.loads(schema.stdout)
        self.assertEqual(value['x-iccplus-mode'], 'native')
        self.assertIn('id', value['required'])
        self.assertIn('scores', value['required'])
        self.assertNotIn('randomWeight', value['required'])

        ts = run_cli('types', '--format', 'typescript', '--mode', 'native', '--kind', 'choice')
        self.assertEqual(ts.returncode, 0, ts.stderr)
        self.assertIn('export interface ChoiceNative', ts.stdout)
        self.assertIn('id: string;', ts.stdout)
        self.assertIn('randomWeight?: number;', ts.stdout)
        self.assertIn('scores: ScoreNative[];', ts.stdout)

        py = run_cli('types', '--format', 'python', '--mode', 'native', '--kind', 'choice')
        self.assertEqual(py.returncode, 0, py.stderr)
        self.assertIn('class ChoiceNative(TypedDict, total=True):', py.stdout)
        self.assertIn('id: str', py.stdout)
        self.assertIn('randomWeight: NotRequired[float]', py.stdout)

    def test_narrowed_types_include_transitive_dependencies(self):
        ts = run_cli('types', '--format', 'typescript', '--mode', 'native', '--kind', 'choice')
        self.assertEqual(ts.returncode, 0, ts.stderr)
        for name in ('RequirementNative', 'AddonNative', 'ScoreNative', 'SelectableAddonNative', 'StylingNative', 'ChoiceNative'):
            self.assertIn(f'export interface {name}', ts.stdout)
        self.assertLess(ts.stdout.index('export interface ScoreNative'), ts.stdout.index('export interface ChoiceNative'))

        py = run_cli('types', '--format', 'python', '--mode', 'native', '--kind', 'choice')
        self.assertEqual(py.returncode, 0, py.stderr)
        for name in ('RequirementNative', 'AddonNative', 'ScoreNative', 'SelectableAddonNative', 'StylingNative', 'ChoiceNative'):
            self.assertIn(f'class {name}', py.stdout)
        compile(py.stdout, '<generated-iccplus-types>', 'exec')

    def test_native_styling_schema_accepts_pinned_default_wire_spellings(self):
        result = run_cli('schema', 'styling', '--mode', 'native', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertIn('barBackgroundImage', value['properties'])
        self.assertIn('barBacktroundImage', value['properties'])
        self.assertTrue(value['properties']['barBacktroundImage']['deprecated'])
        self.assertEqual(value['x-iccplus-wire-compat-aliases']['barBacktroundImage'], 'barBackgroundImage')
        self.assertIn('reqImgFilterBorderColor', value['properties'])

    def test_direct_known_field_value_type_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            result = run_cli('update', str(project), 'sword', '--field', 'randomWeight="two"', '--compact')
            self.assertEqual(result.returncode, 1)
            self.assertIn('expects number', json.loads(result.stderr)['error'])

    def test_generate_creates_exact_blank_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'project.json'
            result = run_cli('generate', '-o', str(out), '--compact')
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertTrue(value['ok'])
            self.assertTrue(value['blank'])
            self.assertEqual(out.stat().st_size, 13414)
            self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(), '10e9b3ba3ccee2a9ca7e2ce2753e2f61fc2e289549629f2c2d6235cc0705f68d')
            self.assertFalse(out.read_bytes().endswith(b'\n'))

    def test_apply_jsonl_from_stdin(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            script = '\n'.join([
                json.dumps({'op': 'update', 'reference': 'sword', 'values': {'title': 'Blade'}}),
                json.dumps({'op': 'gate', 'source': 'sword', 'targets': ['elite']}),
            ]) + '\n'
            result = run_cli('apply', str(project), '-', '--require-valid', '--compact', stdin=script)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['ok'])
            show = json.loads(run_cli('show', str(project), 'sword').stdout)
            self.assertEqual(show['value']['title'], 'Blade')

    def test_duplicate_direct_write_leaves_file_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            before = hashlib.sha256(project.read_bytes()).hexdigest()
            result = run_cli('set', str(project), '/rows/0/objects/1/id', json.dumps('sword'))
            after = hashlib.sha256(project.read_bytes()).hexdigest()
            self.assertEqual(result.returncode, 1)
            self.assertEqual(before, after)
            error = json.loads(result.stderr)
            self.assertIn('duplicate identities', error['error'])

    def test_normalize_output_writes_requested_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source.json'
            output = Path(tmp) / 'normalized.json'
            value = json.loads(DEMO.read_text())
            value['rows'][0]['index'] = 99
            source.write_text(json.dumps(value))
            result = run_cli('normalize', str(source), '-o', str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())
            self.assertEqual(json.loads(output.read_text())['rows'][0]['index'], 0)
            self.assertEqual(json.loads(source.read_text())['rows'][0]['index'], 99)

    def test_summary_and_ids_reject_non_iccplus_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'structured.json'
            project.write_text(json.dumps({'project': {}, 'groups': {'schema_version': 1}, 'choices': []}))
            summary = run_cli('summary', str(project))
            self.assertEqual(summary.returncode, 2, summary.stderr)
            summary_value = json.loads(summary.stdout)
            self.assertFalse(summary_value['format_valid'])
            self.assertTrue(any(d['code'] == 'structure.missing_rows' for d in summary_value['format_diagnostics']))
            ids = run_cli('ids', str(project))
            self.assertEqual(ids.returncode, 2, ids.stderr)
            ids_value = json.loads(ids.stdout)
            self.assertFalse(ids_value['ok'])
            self.assertFalse(ids_value['format_valid'])
            self.assertTrue(any(d['code'] == 'structure.expected_array' for d in ids_value['format_diagnostics']))



    def test_compact_is_available_on_read_only_commands(self):
        for command in [('summary', str(DEMO)), ('validate', str(DEMO)), ('ids', str(DEMO)), ('list', str(DEMO), 'choice')]:
            result = run_cli(*command, '--compact')
            self.assertIn(result.returncode, (0, 2), result.stderr)
            self.assertTrue(result.stdout.strip())
            self.assertNotIn('\n', result.stdout.strip())
            json.loads(result.stdout)

    def test_non_iccplus_shape_is_rejected_by_normal_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'structured.json'
            project.write_text(json.dumps({'project': {}, 'groups': {'schema_version': 1}, 'choices': []}))
            result = run_cli('list', str(project), 'choice', '--compact')
            self.assertEqual(result.returncode, 1)
            error = json.loads(result.stderr)
            self.assertIn('not an ICC Plus project', error['error'])
            self.assertIn('structure.missing_rows', error['error'])


    def test_check_combines_preflight_checks(self):
        result = run_cli('check', str(DEMO))
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertTrue(value['ok'])
        self.assertTrue(value['identities']['ok'])
        self.assertTrue(value['validation']['valid'])
        self.assertIn('rows', value['summary'])

    def test_non_tty_output_is_compact_by_default(self):
        result = run_cli('summary', str(DEMO))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('\n', result.stdout.strip())
        json.loads(result.stdout)

    def test_pretty_flag_forces_multiline_json(self):
        result = run_cli('summary', str(DEMO), '--pretty')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('\n', result.stdout.strip())
        json.loads(result.stdout)

    def test_usage_errors_are_structured_json(self):
        result = run_cli('update', str(DEMO))
        self.assertEqual(result.returncode, 1)
        value = json.loads(result.stderr)
        self.assertFalse(value['ok'])
        self.assertEqual(value['error_type'], 'usage')

    def test_direct_field_syntax_and_relaxed_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            result = run_cli('update', str(project), 'sword', '--field', 'title=Blade', '--field', 'template=2')
            self.assertEqual(result.returncode, 0, result.stderr)
            show = json.loads(run_cli('show', str(project), 'sword').stdout)
            self.assertEqual(show['value']['title'], 'Blade')
            self.assertEqual(show['value']['template'], 2)
            result = run_cli('set', str(project), '/rows/0/objects/0/title', 'Plain text title')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(run_cli('get', str(project), '/rows/0/objects/0/title').stdout), 'Plain text title')

    def test_direct_field_syntax_rejects_misspelled_native_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            before = hashlib.sha256(project.read_bytes()).hexdigest()
            result = run_cli('update', str(project), 'sword', '--field', 'titel=Blade')
            self.assertEqual(result.returncode, 1)
            self.assertEqual(before, hashlib.sha256(project.read_bytes()).hexdigest())
            value = json.loads(result.stderr)
            self.assertIn('unknown native field', value['error'])
            self.assertIn('fields KIND', value['error'])
            self.assertIn('title', value['error'])

    def test_generate_rejects_old_fragment_argument(self):
        result = run_cli('generate', '{"rows":[]}')
        self.assertEqual(result.returncode, 1)
        value = json.loads(result.stderr)
        self.assertEqual(value['error_type'], 'usage')

    def test_apply_accepts_inline_json_and_at_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            inline = json.dumps({'op': 'update', 'ref': 'sword', 'title': 'Blade'})
            result = run_cli('apply', str(project), inline)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(run_cli('show', str(project), 'sword').stdout)['value']['title'], 'Blade')
            ops = Path(tmp) / 'ops.json'
            ops.write_text(json.dumps({'op': 'update', 'ref': 'sword', 'title': 'Saber'}), encoding='utf-8')
            result = run_cli('apply', str(project), '@' + str(ops))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(run_cli('show', str(project), 'sword').stdout)['value']['title'], 'Saber')

    def test_show_missing_id_suggests_search_matches(self):
        result = run_cli('show', str(DEMO), 'sowrd')
        self.assertEqual(result.returncode, 1)
        value = json.loads(result.stderr)
        self.assertIn('sword', value['error'])
        self.assertIn('search PROJECT QUERY', value['error'])

    def test_apply_defaults_script_to_stdin_and_ref_shorthand(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            script = json.dumps({'op': 'update', 'ref': 'sword', 'title': 'Blade'}) + '\n'
            result = run_cli('apply', str(project), stdin=script)
            self.assertEqual(result.returncode, 0, result.stderr)
            show = json.loads(run_cli('show', str(project), 'sword').stdout)
            self.assertEqual(show['value']['title'], 'Blade')

    def test_invalid_direct_write_is_blocked_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            before = hashlib.sha256(project.read_bytes()).hexdigest()
            result = run_cli('set', str(project), '/rows/0/objects/0/scores/0/id', 'missing_point')
            after = hashlib.sha256(project.read_bytes()).hexdigest()
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(before, after)
            value = json.loads(result.stdout)
            self.assertIsNone(value['written'])

    def test_session_can_resume_complete_previous_response(self):
        first = run_cli('session', str(DEMO), '--select', 'sword', '--compact')
        self.assertEqual(first.returncode, 0, first.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            response = Path(tmp) / 'response.json'
            response.write_text(first.stdout)
            second = run_cli('session', str(DEMO), '--state-in', str(response), '--status', 'elite', '--compact')
            self.assertEqual(second.returncode, 0, second.stderr)
            value = json.loads(second.stdout)
            status = value['results'][0]['status']
            self.assertTrue(status['selectable'])
            self.assertIn('sword', value['snapshot']['selected_ids'])


    def test_describe_is_machine_readable(self):
        result = run_cli('describe', 'update')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['command'], 'update')
        names = {arg['name'] for arg in value['arguments']}
        self.assertIn('project', names)
        self.assertIn('field', names)
        self.assertIn('allow_invalid', names)

    def test_search_finds_title_and_fuzzy_id(self):
        result = run_cli('search', str(DEMO), 'Elite')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['matches'][0]['id'], 'elite')
        fuzzy = run_cli('search', str(DEMO), 'sowrd', '--kind', 'choice')
        self.assertEqual(fuzzy.returncode, 0, fuzzy.stderr)
        self.assertTrue(any(x['id'] == 'sword' for x in json.loads(fuzzy.stdout)['matches']))

    def test_fields_support_project_and_backpack_row(self):
        project = json.loads(run_cli('fields', 'project', '--contains', 'customCSS').stdout)
        self.assertEqual(project['fields'], ['customCSS'])
        backpack = json.loads(run_cli('fields', 'backpack_row', '--contains', 'allowedChoices').stdout)
        self.assertEqual(backpack['fields'], ['allowedChoices'])

    def test_new_default_does_not_clobber_existing_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = Path.cwd()
            try:
                # run the module with cwd=tmp so the implicit default path is local to the temp directory
                first = subprocess.run([sys.executable, '-m', 'iccplus_tools', 'new'], cwd=tmp, env={**__import__('os').environ, 'PYTHONPATH': str(ROOT)}, text=True, capture_output=True)
                second = subprocess.run([sys.executable, '-m', 'iccplus_tools', 'new'], cwd=tmp, env={**__import__('os').environ, 'PYTHONPATH': str(ROOT)}, text=True, capture_output=True)
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertTrue((Path(tmp) / 'project.json').exists())
                self.assertTrue((Path(tmp) / 'project-2.json').exists())
            finally:
                pass

    def test_generate_can_choose_safe_output_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = subprocess.run([sys.executable, '-m', 'iccplus_tools', 'generate'], cwd=tmp, env={**__import__('os').environ, 'PYTHONPATH': str(ROOT)}, text=True, capture_output=True)
            second = subprocess.run([sys.executable, '-m', 'iccplus_tools', 'generate'], cwd=tmp, env={**__import__('os').environ, 'PYTHONPATH': str(ROOT)}, text=True, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(Path(json.loads(first.stdout)['written']).name, 'project.json')
            self.assertEqual(Path(json.loads(second.stdout)['written']).name, 'project-2.json')
            self.assertTrue((Path(tmp) / 'project.json').exists())
            self.assertTrue((Path(tmp) / 'project-2.json').exists())

    def test_build_replays_strict_apply_scripts_from_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'iccplus.build.json'
            ops1 = root / '01.ops.json'
            ops2 = root / '02.ops.json'
            out = root / 'project.json'
            ops1.write_text(json.dumps({
                'format': 'iccplus-agent-ops', 'format_version': 1, 'strict_fields': True,
                'operations': [
                    {'op': 'add', 'kind': 'point', 'values': {'id': 'budget', 'name': 'Budget', 'startingSum': 10}},
                    {'op': 'add', 'kind': 'row', 'values': {'id': 'row_a', 'title': 'A'}},
                ],
            }), encoding='utf-8')
            ops2.write_text(json.dumps({
                'format': 'iccplus-agent-ops', 'format_version': 1, 'strict_fields': True,
                'operations': [{'op': 'add', 'kind': 'choice', 'parent': 'row_a', 'values': {'id': 'choice_a', 'title': 'Choice'}}],
            }), encoding='utf-8')
            manifest.write_text(json.dumps({'format': 'iccplus-build', 'format_version': 1, 'steps': [{'script': '01.ops.json'}, {'script': '02.ops.json'}]}), encoding='utf-8')
            result = run_cli('build', str(manifest), '-o', str(out), '--compact')
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertTrue(receipt['ok'])
            self.assertEqual(len(receipt['steps']), 2)
            self.assertTrue(receipt['build_fingerprint'].startswith('sha256:'))
            self.assertEqual(json.loads(run_cli('show', str(out), 'choice_a').stdout)['value']['title'], 'Choice')

    def test_build_rejects_non_strict_script_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'iccplus.build.json'
            ops = root / 'bad.ops.json'
            out = root / 'project.json'
            ops.write_text(json.dumps({'operations': [{'op': 'add', 'kind': 'row', 'values': {'id': 'r', 'title': 'R'}}]}), encoding='utf-8')
            manifest.write_text(json.dumps({'format': 'iccplus-build', 'format_version': 1, 'steps': [{'script': 'bad.ops.json'}]}), encoding='utf-8')
            result = run_cli('build', str(manifest), '-o', str(out))
            self.assertEqual(result.returncode, 1)
            self.assertFalse(out.exists())
            self.assertIn('canonical iccplus-agent-ops', json.loads(result.stderr)['error'])

    def test_scenario_defaults_to_stdin(self):
        scenario = (ROOT / 'examples' / 'demo_scenario.json').read_text()
        result = run_cli('scenario', str(DEMO), stdin=scenario)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['passed'])

    def test_session_state_in_accepts_inline_json(self):
        first = run_cli('session', str(DEMO), '--select', 'sword')
        self.assertEqual(first.returncode, 0, first.stderr)
        state = json.loads(first.stdout)['runtime_state']
        second = run_cli('session', str(DEMO), '--state-in', json.dumps(state), '--status', 'elite')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(json.loads(second.stdout)['results'][0]['status']['selectable'])



    def test_view_command_returns_player_visible_descriptions_without_images(self):
        result = run_cli('view', str(DEMO), '--verbose', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['mode'], 'player_view')
        self.assertTrue(value['verbose'])
        sword = next(c for r in value['rows'] for c in r['choices'] if c['id'] == 'sword')
        self.assertEqual(sword['title'], 'Sword')
        self.assertIn('scores', sword)
        self.assertNotIn('image', json.dumps(value).lower())

    def test_session_verbose_view_action(self):
        result = run_cli('session', str(DEMO), '--select', 'sword', '--verbose-view', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        view_result = value['results'][-1]
        self.assertEqual(view_result['action'], 'view')
        self.assertTrue(view_result['view']['verbose'])
        self.assertIn('sword', view_result['view']['selected_ids'])

    def test_player_safe_session_hides_internal_state_and_persists_continuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'run.json'
            first = run_cli('session', str(DEMO), '--select', 'sword', '--verbose-view', '--player-safe', '--state-out', str(state), '--compact')
            self.assertEqual(first.returncode, 0, first.stderr)
            value = json.loads(first.stdout)
            self.assertEqual(value['mode'], 'player_safe_session')
            self.assertEqual(value['state_written'], str(state))
            self.assertTrue(state.exists())
            self.assertNotIn('runtime_state', value)
            self.assertNotIn('snapshot', value)
            self.assertNotIn('project_fingerprint', value)
            self.assertNotIn('details', json.dumps(value))
            self.assertIn('sword', value['results'][-1]['view']['selected_ids'])

            second = run_cli('session', str(DEMO), '--state-in', str(state), '--status', 'elite', '--player-safe', '--state-out', str(state), '--compact')
            self.assertEqual(second.returncode, 0, second.stderr)
            resumed = json.loads(second.stdout)
            self.assertTrue(resumed['results'][0]['status']['visible'])
            self.assertTrue(resumed['results'][0]['status']['can_select'])
            self.assertNotIn('requirements', json.dumps(resumed['results'][0]['status']))
            self.assertNotIn('point_preview', json.dumps(resumed))

    def test_player_safe_session_normalizes_hidden_and_missing_targets(self):
        project = {
            'version': '2.10.7', 'styling': {'reqFilterVisibleIsOn': True}, 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'hidden_secret_id', 'title': 'Hidden', 'text': 'Secret text',
                'requireds': [{'id': '', 'type': 'id', 'required': True, 'reqId': 'missing_gate'}],
                'scores': [], 'addons': [],
            }]}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'p.json'
            path.write_text(json.dumps(project), encoding='utf-8')
            hidden = run_cli('session', str(path), '--select', 'hidden_secret_id', '--player-safe', '--compact')
            missing = run_cli('session', str(path), '--select', 'totally_missing', '--player-safe', '--compact')
            self.assertEqual(hidden.returncode, 3, hidden.stderr)
            self.assertEqual(missing.returncode, 3, missing.stderr)
            h = json.loads(hidden.stdout)['results'][0]['event']
            m = json.loads(missing.stdout)['results'][0]['event']
            self.assertEqual((h['code'], h['message']), ('player.unavailable', 'content is not available to the player in the current state'))
            self.assertEqual((m['code'], m['message']), ('player.unavailable', 'content is not available to the player in the current state'))
            self.assertNotIn('missing_gate', hidden.stdout)
            self.assertNotIn('Secret text', hidden.stdout)

    def test_player_safe_session_rejects_snapshot_action(self):
        request = json.dumps({'player_safe': True, 'actions': [{'action': 'snapshot'}]})
        result = run_cli('session', str(DEMO), '--request', request, '--compact')
        self.assertEqual(result.returncode, 1)
        self.assertIn('snapshot action is not available in player-safe mode', result.stderr)

    def test_play_command_keeps_state_private_and_resumes_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'play-state.json'
            first = run_cli('play', str(DEMO), '--state', str(state), '--select', 'sword', '--compact')
            self.assertEqual(first.returncode, 0, first.stderr)
            value = json.loads(first.stdout)
            self.assertEqual(value['mode'], 'player_safe_play')
            self.assertEqual(value['state_written'], str(state))
            self.assertTrue(state.exists())
            if os.name != 'nt':
                self.assertEqual(stat.S_IMODE(state.stat().st_mode), 0o600)
            self.assertEqual(list(Path(tmp).glob(f'.{state.name}.*.tmp')), [])
            self.assertIn('sword', value['view']['selected_ids'])
            self.assertNotIn('runtime_state', value)
            self.assertNotIn('snapshot', value)
            self.assertNotIn('project_fingerprint', value)
            self.assertNotIn('details', json.dumps(value))

            second = run_cli('play', str(DEMO), '--state', str(state), '--status', 'elite', '--compact')
            self.assertEqual(second.returncode, 0, second.stderr)
            resumed = json.loads(second.stdout)
            self.assertIn('sword', resumed['view']['selected_ids'])
            self.assertTrue(resumed['results'][0]['status']['can_select'])

    def test_play_command_can_open_or_reset_without_exposing_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'play-state.json'
            opened = run_cli('play', str(DEMO), '--state', str(state), '--compact-view', '--compact')
            self.assertEqual(opened.returncode, 0, opened.stderr)
            first = json.loads(opened.stdout)
            self.assertEqual(first['results'], [])
            self.assertFalse(first['view']['verbose'])
            self.assertTrue(state.exists())

            selected = run_cli('play', str(DEMO), '--state', str(state), '--select', 'sword', '--compact')
            self.assertEqual(selected.returncode, 0, selected.stderr)
            reset = run_cli('play', str(DEMO), '--state', str(state), '--reset', '--compact')
            self.assertEqual(reset.returncode, 0, reset.stderr)
            value = json.loads(reset.stdout)
            self.assertEqual(value['results'][0], {'index': 0, 'action': 'reset', 'ok': True})
            self.assertNotIn('sword', value['view']['selected_ids'])

    def test_state_check_reports_valid_and_corrupt_state_without_mutating_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'run.json'
            made = run_cli('play', str(DEMO), '--state', str(state), '--select', 'sword', '--compact')
            self.assertEqual(made.returncode, 0, made.stderr)
            original = state.read_bytes()

            valid = run_cli('state-check', str(DEMO), str(state), '--compact')
            self.assertEqual(valid.returncode, 0, valid.stderr)
            report = json.loads(valid.stdout)
            self.assertTrue(report['valid'])
            self.assertEqual(report['selected_count'], 1)
            self.assertEqual(state.read_bytes(), original)

            broken = json.loads(state.read_text())
            broken['runtime']['selected_order'] = []
            state.write_text(json.dumps(broken), encoding='utf-8')
            corrupt_bytes = state.read_bytes()
            invalid = run_cli('state-check', str(DEMO), str(state), '--compact')
            self.assertEqual(invalid.returncode, 2, invalid.stderr)
            bad = json.loads(invalid.stdout)
            self.assertFalse(bad['valid'])
            self.assertIn('selected_order does not match active selectables', bad['error'])
            self.assertEqual(state.read_bytes(), corrupt_bytes)

    def test_state_check_handles_truncated_json_and_play_reset_recovers_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'broken.json'
            state.write_text('{"format":"iccplus-cyoa-runtime-state",', encoding='utf-8')
            before = state.read_bytes()

            checked = run_cli('state-check', str(DEMO), str(state), '--compact')
            self.assertEqual(checked.returncode, 2, checked.stderr)
            report = json.loads(checked.stdout)
            self.assertFalse(report['valid'])
            self.assertEqual(state.read_bytes(), before)

            refused = run_cli('play', str(DEMO), '--state', str(state), '--select', 'sword', '--compact')
            self.assertEqual(refused.returncode, 2, refused.stderr)
            value = json.loads(refused.stdout)
            self.assertEqual(value['mode'], 'player_safe_play')
            self.assertEqual(value['error']['code'], 'state.invalid')
            self.assertNotIn('runtime_state', value)
            self.assertEqual(state.read_bytes(), before)

            reset = run_cli('play', str(DEMO), '--state', str(state), '--reset', '--compact')
            self.assertEqual(reset.returncode, 0, reset.stderr)
            recovered = json.loads(reset.stdout)
            self.assertTrue(recovered['ok'])
            self.assertEqual(recovered['results'][0], {'index': 0, 'action': 'reset', 'ok': True})
            self.assertNotIn('sword', recovered['view']['selected_ids'])
            parsed = json.loads(state.read_text(encoding='utf-8'))
            self.assertEqual(parsed['format'], 'iccplus-cyoa-runtime-state')

    def test_session_invalid_selection_returns_semantic_error_and_no_partial_state(self):
        project = {
            'version': '2.10.7',
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 1, 'belowZeroNotAllowed': True}],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'x', 'title': 'X', 'text': '', 'requireds': [], 'addons': [],
                'scores': [{'idx': 's', 'id': 'p', 'value': 5, 'requireds': [], 'showScore': True}],
            }]}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'p.json'
            path.write_text(json.dumps(project), encoding='utf-8')
            result = run_cli('session', str(path), '--select', 'x', '--compact')
            self.assertEqual(result.returncode, 3, result.stderr)
            value = json.loads(result.stdout)
            event = value['results'][0]['event']
            self.assertEqual(event['code'], 'points.below_zero_not_allowed')
            self.assertEqual(value['snapshot']['points']['p'], 1)
            self.assertNotIn('x', value['snapshot']['selected_ids'])

    def test_run_invalid_selection_exits_three_with_semantic_error(self):
        project = {
            'version': '2.10.7', 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'blocked', 'title': 'Blocked', 'text': '', 'isNotSelectable': True,
                'requireds': [], 'scores': [], 'addons': [],
            }]}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'p.json'
            path.write_text(json.dumps(project), encoding='utf-8')
            result = run_cli('run', str(path), '--select', 'blocked', '--compact')
            self.assertEqual(result.returncode, 3, result.stderr)
            value = json.loads(result.stdout)
            self.assertFalse(value['ok'])
            self.assertEqual(value['error']['code'], 'selection.not_selectable')

    def test_view_after_invalid_selection_exits_three_without_leaking_state(self):
        project = {
            'version': '2.10.7', 'styling': {'reqFilterVisibleIsOn': True}, 'pointTypes': [],
            'rows': [{'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [{
                'id': 'hidden', 'title': 'Hidden', 'text': 'Secret',
                'requireds': [{'id': 'req', 'type': 'id', 'required': True, 'reqId': 'missing'}],
                'scores': [], 'addons': [],
            }]}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'p.json'
            path.write_text(json.dumps(project), encoding='utf-8')
            result = run_cli('view', str(path), '--after', 'hidden', '--verbose', '--compact')
            self.assertEqual(result.returncode, 3, result.stderr)
            value = json.loads(result.stdout)
            self.assertFalse(value['ok'])
            self.assertEqual(value['error']['code'], 'player.unavailable')
            self.assertEqual(value['view']['selected_ids'], [])
            self.assertNotIn('Secret', json.dumps(value))
            self.assertNotIn('missing', json.dumps(value))

    def test_match_previews_exact_bulk_selector_and_expect(self):
        where = json.dumps({'kind': 'choice', 'row': 'element'})
        result = run_cli('match', str(DEMO), where, '--expect', '4', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['count'], 4)
        self.assertEqual([x['id'] for x in value['matches']], ['fire', 'water', 'switcher', 'flagged'])

        mismatch = run_cli('match', str(DEMO), where, '--expect', '3', '--compact')
        self.assertEqual(mismatch.returncode, 1)
        self.assertIn('expected 3 matches', json.loads(mismatch.stderr)['error'])



    def test_structural_cli_reorder_clone_and_fragment_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            listed = json.loads(run_cli('list', str(project), 'choice').stdout)
            row = listed[0]['row_id']
            row_choices = [x['id'] for x in listed if x['row_id'] == row]
            if len(row_choices) >= 2:
                result = run_cli('reorder', str(project), 'choice', json.dumps(list(reversed(row_choices))), '--parent', row, '--compact')
                self.assertEqual(result.returncode, 0, result.stderr)
            source = row_choices[0]
            clone = run_cli('clone', str(project), source, '--parent', row, '--compact')
            self.assertEqual(clone.returncode, 0, clone.stderr)
            cloned_id = json.loads(clone.stdout)['cloned']['id']
            self.assertNotEqual(cloned_id, source)
            fragment = Path(tmp) / 'choice.json'
            exported = run_cli('export-fragment', str(project), source, '-o', str(fragment), '--compact')
            self.assertEqual(exported.returncode, 0, exported.stderr)
            self.assertTrue(fragment.exists())
            imported = run_cli('import-fragment', str(project), 'choice', str(fragment), '--parent', row, '--compact')
            self.assertEqual(imported.returncode, 0, imported.stderr)
            self.assertNotEqual(json.loads(imported.stdout)['imported']['id'], source)


class PackagingCliTests(unittest.TestCase):
    def test_format_creator_matches_compact_json_and_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            value = json.loads(DEMO.read_text(encoding='utf-8'))
            project.write_text(json.dumps(value, indent=4) + '\n', encoding='utf-8')
            check = run_cli('format', str(project), '--style', 'creator', '--check', '--compact')
            self.assertEqual(check.returncode, 2)
            result = run_cli('format', str(project), '--style', 'creator', '--compact')
            self.assertEqual(result.returncode, 0, result.stderr)
            raw = project.read_bytes()
            self.assertFalse(raw.endswith(b'\n'))
            self.assertNotIn(b'\n', raw)
            check2 = run_cli('format', str(project), '--style', 'creator', '--check', '--compact')
            self.assertEqual(check2.returncode, 0, check2.stderr)

    def test_export_project_and_build_viewer_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            project = tmp / 'project.json'; project.write_bytes(DEMO.read_bytes())
            exported = tmp / 'export.zip'
            result = run_cli('export-project', str(project), '-o', str(exported), '--compact')
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(exported) as zf:
                self.assertIn('project.json', zf.namelist())

            template = tmp / 'web.zip'
            with zipfile.ZipFile(template, 'w') as zf:
                zf.writestr('index.html', '<html><head><title>X</title></head><body><span id="projectSize">0</span><div id="indicator">x</div></body></html>')
                zf.writestr('css/loading.css', ':root { --bg: old; }')
            built = tmp / 'viewer.zip'
            result = run_cli('build-viewer', str(project), '--template', str(template), '-o', str(built), '--mode', 'web', '--embedded-images', '--compact')
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(built) as zf:
                self.assertIn('project.json', zf.namelist())
                self.assertIn('index.html', zf.namelist())
    def test_build_string_import_export_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            state = Path(tmp) / 'state.json'
            project.write_text(DEMO.read_text(encoding='utf-8'), encoding='utf-8')
            played = run_cli('session', str(project), '--select', 'sword', '--state-out', str(state), '--compact')
            self.assertEqual(played.returncode, 0, played.stderr)
            exported = run_cli('build-string', str(project), 'export', '--state', str(state), '--compact')
            self.assertEqual(exported.returncode, 0, exported.stderr)
            build = json.loads(exported.stdout)['build_string']
            self.assertIn('sword', build)
            restored_state = Path(tmp) / 'restored.json'
            imported = run_cli('build-string', str(project), 'import', build, '--state-out', str(restored_state), '--compact')
            self.assertEqual(imported.returncode, 0, imported.stderr)
            value = json.loads(imported.stdout)
            self.assertEqual(value['canonical_build_string'], build)
            self.assertIn('sword', value['snapshot']['selected_ids'])
            self.assertTrue(restored_state.exists())

    def test_build_string_import_accepts_stdin(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_text(DEMO.read_text(encoding='utf-8'), encoding='utf-8')
            imported = run_cli('build-string', str(project), 'import', '-', '--compact', stdin='sword')
            self.assertEqual(imported.returncode, 0, imported.stderr)
            self.assertEqual(json.loads(imported.stdout)['canonical_build_string'], 'sword')

    def test_build_string_preserves_mixed_native_entry_order(self):
        project_value = {
            'version': '2.10.7', 'styling': {},
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 0, 'allowFloat': False}],
            'variables': [{'id': 'v', 'name': 'V', 'isTrue': False}],
            'rows': [
                {'id': 'r', 'title': 'R', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [
                    {'id': 'c', 'title': 'C', 'text': '', 'requireds': [], 'scores': [], 'addons': []}
                ]},
                {'id': 'rb', 'title': 'RB', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [], 'isButtonRow': True, 'btnPointAddon': True, 'buttonTypeRadio': 'sumaddon', 'pointTypeRandom': 'p', 'randomMin': 3, 'randomMax': 4},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            state = Path(tmp) / 'state.json'
            project.write_text(json.dumps(project_value), encoding='utf-8')
            original = 'v,rb/RP#p/NUM#3,c'
            imported = run_cli('build-string', str(project), 'import', original, '--state-out', str(state), '--compact')
            self.assertEqual(imported.returncode, 0, imported.stderr)
            self.assertEqual(json.loads(imported.stdout)['canonical_build_string'], original)
            exported = run_cli('build-string', str(project), 'export', '--state', str(state), '--compact')
            self.assertEqual(exported.returncode, 0, exported.stderr)
            self.assertEqual(json.loads(exported.stdout)['build_string'], original)
            runtime = json.loads(state.read_text())['runtime']
            self.assertEqual(runtime['build_order'], ['v', 'rb', 'c'])

    def test_project_stats_matches_creator_counting_rules(self):
        result = run_cli('project-stats', str(DEMO), '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertGreater(value['character_count'], 0)
        self.assertGreater(value['choice_count'], 0)
        self.assertGreaterEqual(value['row_count'], 1)
        self.assertEqual(value['assumptions']['characters_per_minute'], 175)
        self.assertEqual(value['assumptions']['minutes_per_picture'], 5)

    def test_clean_private_styling_removes_creator_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            value = json.loads(DEMO.read_text(encoding='utf-8'))
            row = value['rows'][0]
            row['isPrivateStyling'] = True
            row['privateRowIsOn'] = True
            row['styling'] = {'rowMargin': 99}
            choice = row['objects'][0]
            choice['isPrivateStyling'] = True
            choice['privateTextIsOn'] = True
            choice['styling'] = {'objectMargin': 99}
            project.write_text(json.dumps(value), encoding='utf-8')
            result = run_cli('clean-private-styling', str(project), '--compact')
            self.assertEqual(result.returncode, 0, result.stderr)
            cleaned = json.loads(project.read_text(encoding='utf-8'))
            self.assertNotIn('styling', cleaned['rows'][0])
            self.assertNotIn('privateRowIsOn', cleaned['rows'][0])
            self.assertNotIn('styling', cleaned['rows'][0]['objects'][0])
            self.assertNotIn('privateTextIsOn', cleaned['rows'][0]['objects'][0])

    def test_style_template_list_show_and_apply_match_pinned_creator(self):
        listed = run_cli('style-template', 'list', '--compact')
        self.assertEqual(listed.returncode, 0, listed.stderr)
        templates = json.loads(listed.stdout)['templates']
        self.assertEqual([x['name'] for x in templates], ['Fall', 'Book', 'Bone', 'Dark', 'Hello 2021', 'Black & Gold', 'Rainbow', 'Seeing Greens'])
        self.assertEqual([x['field_count'] for x in templates], [191, 193, 193, 191, 198, 200, 200, 200])

        shown = run_cli('style-template', 'show', '6', '--compact')
        self.assertEqual(shown.returncode, 0, shown.stderr)
        preset = json.loads(shown.stdout)
        self.assertEqual(preset['name'], 'Black & Gold')
        self.assertEqual(preset['styling']['backgroundColor'], '#B8860BFF')
        self.assertEqual(len(preset['styling']), 200)

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            value = json.loads(DEMO.read_text(encoding='utf-8'))
            value.setdefault('styling', {})['customFutureField'] = 'preserve-me'
            project.write_text(json.dumps(value), encoding='utf-8')
            applied = run_cli('style-template', 'apply', str(project), 'Black & Gold', '--allow-invalid', '--compact')
            self.assertEqual(applied.returncode, 0, applied.stderr)
            updated = json.loads(project.read_text(encoding='utf-8'))
            self.assertEqual(updated['styling']['backgroundColor'], '#B8860BFF')
            self.assertEqual(updated['styling']['customFutureField'], 'preserve-me')

    def test_row_choices_sort_copy_and_copy_delete_cover_row_settings_bulk_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            value = json.loads(DEMO.read_text(encoding='utf-8'))
            gear = next(row for row in value['rows'] if row['id'] == 'gear')
            gear['objects'][0]['objectWidth'] = 'col-12'
            gear['objects'][0]['text'] = '12345'
            gear['objects'][1]['objectWidth'] = 'col-xl-1'
            gear['objects'][1]['text'] = '1'
            gear['objects'][2]['objectWidth'] = 'col-md-4'
            gear['objects'][2]['text'] = '123'
            project.write_text(json.dumps(value), encoding='utf-8')

            sorted_result = run_cli('row-choices', 'sort', str(project), 'gear', '--by', 'text-longest', '--compact')
            self.assertEqual(sorted_result.returncode, 0, sorted_result.stderr)
            self.assertEqual(json.loads(sorted_result.stdout)['order'], ['sword', 'elite', 'shield'])

            copied = run_cli('row-choices', 'copy', str(project), 'gear', 'element', '--compact')
            self.assertEqual(copied.returncode, 0, copied.stderr)
            copied_value = json.loads(copied.stdout)
            self.assertEqual(copied_value['choice_count'], 3)
            after_copy = json.loads(project.read_text(encoding='utf-8'))
            element = next(row for row in after_copy['rows'] if row['id'] == 'element')
            self.assertEqual(len(element['objects']), 7)
            copied_ids = [choice['id'] for choice in element['objects'][-3:]]
            self.assertEqual(len(set(copied_ids)), 3)
            self.assertTrue(set(copied_ids).isdisjoint({'sword', 'elite', 'shield'}))

            moved = run_cli('row-choices', 'copy-and-delete', str(project), 'onepick', 'element', '--compact')
            self.assertEqual(moved.returncode, 0, moved.stderr)
            after_move = json.loads(project.read_text(encoding='utf-8'))
            onepick = next(row for row in after_move['rows'] if row['id'] == 'onepick')
            element = next(row for row in after_move['rows'] if row['id'] == 'element')
            self.assertEqual(onepick['objects'], [])
            self.assertTrue({'a', 'b'}.issubset({choice['id'] for choice in element['objects']}))

    def test_design_import_export_matches_creator_file_shape_and_scope_filters(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            design = Path(tmp) / 'design.json'
            exported = Path(tmp) / 'exported.json'
            value = json.loads(DEMO.read_text(encoding='utf-8'))
            project.write_text(json.dumps(value), encoding='utf-8')
            design.write_text(json.dumps({
                'version': '2.10.7',
                'styling': {
                    'rowMargin': '12',
                    'objectMargin': '7',
                    'barTextSize': '18',
                    'backgroundColor': '#112233FF',
                    'objectTitleColor': {'hexa': '#AABBCCFF'},
                },
            }), encoding='utf-8')

            imported = run_cli('design', 'import', str(project), 'gear', str(design), '--compact')
            self.assertEqual(imported.returncode, 0, imported.stderr)
            result = json.loads(imported.stdout)['design']
            self.assertIn('barTextSize', result['removed_fields'])
            self.assertIn('backgroundColor', result['removed_fields'])
            self.assertIn('rowMargin', result['numeric_coercions'])
            updated = json.loads(project.read_text(encoding='utf-8'))
            gear = next(row for row in updated['rows'] if row['id'] == 'gear')
            self.assertTrue(gear['isPrivateStyling'])
            self.assertEqual(gear['styling']['rowMargin'], 12)
            self.assertEqual(gear['styling']['objectMargin'], 7)
            self.assertEqual(gear['styling']['objectTitleColor'], '#AABBCCFF')
            self.assertNotIn('barTextSize', gear['styling'])
            self.assertNotIn('backgroundColor', gear['styling'])
            self.assertTrue(gear['privateRowIsOn'])
            self.assertTrue(gear['privateObjectIsOn'])
            self.assertTrue(gear['privateTextIsOn'])

            exported_result = run_cli('design', 'export', str(project), 'gear', '-o', str(exported), '--compact')
            self.assertEqual(exported_result.returncode, 0, exported_result.stderr)
            self.assertFalse(exported.read_bytes().endswith(b'\n'))
            exported_value = json.loads(exported.read_text(encoding='utf-8'))
            self.assertEqual(exported_value['version'], '2.10.7')
            self.assertEqual(exported_value['styling'], gear['styling'])

    def test_design_import_export_supports_design_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            design = Path(tmp) / 'design.json'
            value = json.loads(DEMO.read_text(encoding='utf-8'))
            value['rowDesignGroups'] = [{'id': 'rdg', 'name': 'Row design', 'elements': [], 'backpackElements': [], 'groupElements': [], 'styling': {}}]
            value['objectDesignGroups'] = [{'id': 'cdg', 'name': 'Choice design', 'elements': [], 'backpackElements': [], 'groupElements': [], 'styling': {}}]
            project.write_text(json.dumps(value), encoding='utf-8')
            design.write_text(json.dumps({'version': '2.10.7', 'styling': {'rowMargin': 8, 'objectMargin': 5, 'barTextSize': 99}}), encoding='utf-8')
            row_result = run_cli('design', 'import', str(project), 'rdg', str(design), '--compact')
            self.assertEqual(row_result.returncode, 0, row_result.stderr)
            choice_result = run_cli('design', 'import', str(project), 'cdg', str(design), '--compact')
            self.assertEqual(choice_result.returncode, 0, choice_result.stderr)
            updated = json.loads(project.read_text(encoding='utf-8'))
            rdg = updated['rowDesignGroups'][0]
            cdg = updated['objectDesignGroups'][0]
            self.assertEqual(rdg['styling']['rowMargin'], 8)
            self.assertNotIn('barTextSize', rdg['styling'])
            self.assertNotIn('rowMargin', cdg['styling'])
            self.assertEqual(cdg['styling']['objectMargin'], 5)

    def test_creator_id_csv_and_safe_ids_from_titles(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            csv_path = Path(tmp) / 'ids.csv'
            value = json.loads(DEMO.read_text(encoding='utf-8'))
            value['rows'][0]['title'] = '<b>Main Gear</b>'
            value['rows'][0]['objects'][0]['title'] = 'Sword, Plus'
            # Prove the safe scripting version rewrites a real reference.
            value['rows'][0]['objects'][2]['requireds'] = [{'type': 'id', 'required': True, 'reqId': 'sword'}]
            project.write_text(json.dumps(value), encoding='utf-8')
            csv_result = run_cli('id-csv', str(project), '-o', str(csv_path), '--compact')
            self.assertEqual(csv_result.returncode, 0, csv_result.stderr)
            raw = csv_path.read_bytes()
            self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
            text = raw.decode('utf-8-sig')
            self.assertTrue(text.startswith('id,title,debugTitle\n'))
            self.assertIn('gear,<b>Main Gear</b>,', text)
            renamed = run_cli('ids-from-titles', str(project), '--compact')
            self.assertEqual(renamed.returncode, 0, renamed.stderr)
            updated = json.loads(project.read_text(encoding='utf-8'))
            gear = updated['rows'][0]
            self.assertEqual(gear['id'], 'Main_Gear')
            self.assertEqual(gear['objects'][0]['id'], 'Sword__Plus')
            self.assertEqual(gear['objects'][2]['requireds'][0]['reqId'], 'Sword__Plus')

    def test_fonts_sound_effect_import_and_build_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            state = Path(tmp) / 'state.json'
            audio = Path(tmp) / 'click.mp3'
            value = json.loads(DEMO.read_text(encoding='utf-8'))
            project.write_text(json.dumps(value), encoding='utf-8')
            audio.write_bytes(b'ID3fake')

            added = run_cli('fonts', 'add', str(project), 'google', 'Noto Serif', '--compact')
            self.assertEqual(added.returncode, 0, added.stderr)
            listed = run_cli('fonts', 'list', str(project), '--compact')
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn('Noto Serif', json.loads(listed.stdout)['google'])
            removed = run_cli('fonts', 'remove', str(project), 'google', 'Noto Serif', '--compact')
            self.assertEqual(removed.returncode, 0, removed.stderr)

            sfx = run_cli('sound-effect', 'import', str(project), str(audio), '--compact')
            self.assertEqual(sfx.returncode, 0, sfx.stderr)
            updated = json.loads(project.read_text(encoding='utf-8'))
            self.assertEqual(updated['soundEffects'][-1]['name'], 'click')
            self.assertTrue(updated['soundEffects'][-1]['audio'].startswith('data:audio/mpeg;base64,'))

            session = run_cli('session', str(project), '--select', 'sword', '--state-out', str(state), '--compact')
            self.assertEqual(session.returncode, 0, session.stderr)
            summary = run_cli('build-summary', str(project), '--state', str(state), '--compact')
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertEqual(json.loads(summary.stdout)['summary'], 'Sword')
            grouped = run_cli('build-summary', str(project), '--state', str(state), '--separate-rows', '--compact')
            self.assertEqual(grouped.returncode, 0, grouped.stderr)
            self.assertEqual(json.loads(grouped.stdout)['summary'], '**Gear**\nSword')

    def test_row_button_runtime_covers_variable_random_and_point_modes(self):
        def choice(ident):
            return {'id': ident, 'title': ident, 'text': '', 'requireds': [], 'scores': [], 'addons': []}
        project_value = {
            'version': '2.10.7',
            'styling': {},
            'pointTypes': [{'id': 'p', 'name': 'P', 'startingSum': 0, 'allowFloat': False}],
            'variables': [{'id': 'v', 'name': 'V', 'isTrue': False}],
            'rows': [
                {'id': 'varrow', 'title': 'Variable', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [], 'isButtonRow': True, 'buttonId': 'v', 'buttonType': True},
                {'id': 'randrow', 'title': 'Random', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [choice('a'), choice('b'), choice('c')], 'isButtonRow': True, 'buttonRandom': True, 'buttonRandomNumber': 2, 'onlyUnselectedChoices': True},
                {'id': 'pointrow', 'title': 'Point', 'titleText': '', 'allowedChoices': 0, 'requireds': [], 'objects': [], 'isButtonRow': True, 'btnPointAddon': True, 'buttonTypeRadio': 'sumaddon', 'pointTypeRandom': 'p', 'randomMin': 3, 'randomMax': 4},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            state = Path(tmp) / 'state.json'
            project.write_text(json.dumps(project_value), encoding='utf-8')

            direct = run_cli('row-button', str(project), 'pointrow', '--compact')
            self.assertEqual(direct.returncode, 0, direct.stderr)
            self.assertEqual(json.loads(direct.stdout)['state']['points']['p'], 3)

            session = run_cli('session', str(project), '--row-button', 'varrow', '--row-button', 'randrow', '--row-button', 'pointrow', '--state-out', str(state), '--compact')
            self.assertEqual(session.returncode, 0, session.stderr)
            value = json.loads(session.stdout)
            self.assertTrue(value['snapshot']['variables']['v'])
            self.assertEqual(value['snapshot']['points']['p'], 3)
            self.assertEqual(len([x for x in value['snapshot']['selected_ids'] if x in {'a','b','c'}]), 2)
            self.assertIn('/RP#p/NUM#3', run_cli('build-string', str(project), 'export', '--state', str(state), '--compact').stdout)

            safe = run_cli('play', str(project), '--state', str(Path(tmp) / 'play.json'), '--row-button', 'varrow', '--compact')
            self.assertEqual(safe.returncode, 0, safe.stderr)
            safe_value = json.loads(safe.stdout)
            event = safe_value['results'][0]['event']
            self.assertEqual(event['action'], 'row_button')
            self.assertEqual(event['row_id'], 'varrow')
            self.assertNotIn('choice_id', event)

    def test_add_count_creates_multiple_choices(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_text(DEMO.read_text(encoding='utf-8'), encoding='utf-8')
            result = run_cli('add', str(project), 'choice', '--parent', 'gear', '--count', '3', '--field', 'title=Batch', '--compact')
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value['count'], 3)
            ids = [entity['id'] for entity in value['entities']]
            self.assertEqual(len(ids), len(set(ids)))


if __name__ == '__main__':
    unittest.main()

class VisualCliTests(unittest.TestCase):
    def test_visual_audit_missing_images(self):
        result = run_cli('visual-audit', str(DEMO), '--kind', 'choice', '--missing-images', '--limit', '2', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['format'], 'iccplus-visual-audit')
        self.assertEqual(len(value['items']), 2)
        self.assertTrue(all(not item['has_image'] for item in value['items']))

    def test_apply_visuals_dry_run(self):
        manifest = {
            'format': 'iccplus-visual-manifest',
            'items': [{'id': 'sword', 'image': 'assets/sword.webp', 'styling': {'object_image': {'objectImageWidth': 100}}}],
        }
        result = run_cli('apply-visuals', str(DEMO), '-', '--dry-run', '--compact', stdin=json.dumps(manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertTrue(value['ok'])
        self.assertEqual(value['changed_items'], 1)
        self.assertIsNone(value['written'])


class Visual091CliTests(unittest.TestCase):
    def test_visual_audit_manifest_stub_flag(self):
        result = run_cli('visual-audit', str(DEMO), '--kind', 'choice', '--missing-images', '--limit', '2', '--manifest-stub', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['summary']['returned'], 2)
        self.assertTrue(value['summary']['truncated'])
        self.assertEqual(len(value['manifest_stub']['items']), 2)

    def test_bundled_visual_manifest_example_dry_runs_through_cli(self):
        manifest = ROOT / 'examples' / 'visual_manifest.json'
        result = run_cli('apply-visuals', str(DEMO), str(manifest), '--dry-run', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertTrue(value['ok'])
        self.assertEqual(value['changed_items'], 4)
        self.assertIsNone(value['written'])

class AgentAutomationCliTests(unittest.TestCase):
    def test_capabilities_brief_is_small_canonical_contract(self):
        result = run_cli('capabilities', '--brief', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['interface'], 'json-first CLI')
        self.assertEqual(value['canonical_commands']['inspect'], 'inspect PROJECT [REQUEST]')
        self.assertIn('agent-operations', value['schemas']['canonical_write'])
        self.assertLess(len(result.stdout), 6000)

    def test_capabilities_can_return_one_section(self):
        result = run_cli('capabilities', '--section', 'scripting', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['section'], 'scripting')
        self.assertTrue(value['value']['inspect_batches_read_only_queries'])

    def test_schema_index_and_protocol_schema_discovery(self):
        index = run_cli('schema', 'list', '--compact')
        self.assertEqual(index.returncode, 0, index.stderr)
        value = json.loads(index.stdout)
        self.assertIn('agent-operations', value['protocol_schemas'])
        self.assertIn('inspect-request', value['protocol_schemas'])
        schema = run_cli('schema', 'agent-operations', '--compact')
        self.assertEqual(schema.returncode, 0, schema.stderr)
        doc = json.loads(schema.stdout)
        self.assertEqual(doc['properties']['format']['const'], 'iccplus-agent-ops')
        self.assertFalse(doc['additionalProperties'])

    def test_describe_supports_nested_subcommands_and_semantic_summary(self):
        result = run_cli('describe', 'style-template', 'apply', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['command'], 'style-template apply')
        self.assertIn('preset', value['summary'].lower())
        self.assertIsInstance(value['arguments'], list)

    def test_every_top_level_command_has_machine_summary(self):
        from iccplus_tools.capabilities import COMMAND_KINDS
        from iccplus_tools.cli import command_description
        for command in COMMAND_KINDS:
            self.assertTrue(command_description(command)['summary'], command)

    def test_inspect_batches_read_only_queries(self):
        request = {
            'queries': [
                {'op': 'check'},
                {'op': 'search', 'query': 'gear', 'kind': 'row'},
                {'op': 'show', 'ref': 'sword', 'kind': 'choice'},
                {'op': 'match', 'where': {'kind': 'choice', 'row': 'gear'}, 'expect': 3},
            ]
        }
        result = run_cli('inspect', str(DEMO), '-', '--compact', stdin=json.dumps(request))
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertTrue(value['ok'])
        self.assertEqual(value['executed'], 4)
        self.assertEqual(value['results'][1]['result']['matches'][0]['id'], 'gear')
        self.assertEqual(value['results'][2]['result']['id'], 'sword')
        self.assertEqual(value['results'][3]['result']['count'], 3)

    def test_inspect_returns_per_query_errors_without_mutation(self):
        request = {'queries': [{'op': 'show', 'ref': 'missing'}, {'op': 'summary'}]}
        result = run_cli('inspect', str(DEMO), '-', '--compact', stdin=json.dumps(request))
        self.assertEqual(result.returncode, 3, result.stderr)
        value = json.loads(result.stdout)
        self.assertFalse(value['ok'])
        self.assertFalse(value['results'][0]['ok'])
        self.assertTrue(value['results'][1]['ok'])

    def test_agent_operation_format_rejects_unknown_nested_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            before = project.read_bytes()
            script = {
                'format': 'iccplus-agent-ops',
                'format_version': 1,
                'strict_fields': True,
                'operations': [
                    {'op': 'update', 'kind': 'choice', 'ref': 'sword', 'values': {'titlle': 'Blade'}},
                ],
            }
            result = run_cli('apply', str(project), '-', '--compact', stdin=json.dumps(script))
            self.assertEqual(result.returncode, 4, result.stderr)
            self.assertEqual(project.read_bytes(), before)
            value = json.loads(result.stdout)
            self.assertIn('unknown native field', value['error'])
            self.assertIn('title', value['error'])

    def test_compat_operation_format_keeps_explicit_future_field_escape_hatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            script = {'operations': [{'op': 'update', 'kind': 'choice', 'ref': 'sword', 'values': {'futureField': 7}}]}
            result = run_cli('apply', str(project), '-', '--compact', '--dry-run', stdin=json.dumps(script))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['ok'])

    def test_packaged_protocol_schema_copies_match_root_files(self):
        for name in ('agent-operation-script.schema.json', 'inspect-request.schema.json', 'session-request.schema.json', 'runtime-state.schema.json'):
            self.assertEqual((ROOT / 'schemas' / name).read_bytes(), (ROOT / 'iccplus_tools' / 'schemas' / name).read_bytes(), name)

class AgentCompactReceiptTests(unittest.TestCase):
    def test_agent_operation_format_defaults_to_compact_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            script = {
                'format': 'iccplus-agent-ops',
                'format_version': 1,
                'strict_fields': True,
                'operations': [
                    {'op': 'update', 'kind': 'choice', 'ref': 'sword', 'values': {'title': 'Blade'}},
                ],
            }
            result = run_cli('apply', str(project), '-', '--dry-run', '--compact', stdin=json.dumps(script))
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value['result_mode'], 'compact')
            self.assertEqual(value['results'][0]['id'], 'sword')
            self.assertNotIn('value', value['results'][0])
            self.assertEqual(value['validation'], {'valid': True, 'errors': 0, 'warnings': 0})

    def test_agent_operation_format_can_request_full_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            script = {
                'format': 'iccplus-agent-ops',
                'format_version': 1,
                'strict_fields': True,
                'operations': [
                    {'op': 'update', 'kind': 'choice', 'ref': 'sword', 'values': {'title': 'Blade'}},
                ],
            }
            result = run_cli('apply', str(project), '-', '--dry-run', '--result-mode', 'full', '--compact', stdin=json.dumps(script))
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value['results'][0]['value']['title'], 'Blade')

class InspectStrictnessTests(unittest.TestCase):
    def test_inspect_runtime_rejects_unknown_query_keys_with_suggestion(self):
        result = run_cli('inspect', str(DEMO), '-', '--compact', stdin=json.dumps({'op': 'search', 'querry': 'gear'}))
        self.assertEqual(result.returncode, 3, result.stderr)
        value = json.loads(result.stdout)
        message = value['results'][0]['error']['message']
        self.assertIn('querry', message)
        self.assertIn('query', message)

class AgentSchemaRuntimeParityTests(unittest.TestCase):
    def test_agent_wrapper_requires_strict_fields_true(self):
        script = {
            'format': 'iccplus-agent-ops',
            'format_version': 1,
            'strict_fields': False,
            'operations': [{'op': 'update', 'kind': 'choice', 'ref': 'sword', 'values': {'title': 'Blade'}}],
        }
        result = run_cli('apply', str(DEMO), '-', '--dry-run', '--compact', stdin=json.dumps(script))
        self.assertEqual(result.returncode, 1)
        self.assertIn('strict_fields=true', json.loads(result.stderr)['error'])

    def test_agent_runtime_rejects_unknown_non_edit_operation_keys(self):
        script = {
            'format': 'iccplus-agent-ops',
            'format_version': 1,
            'strict_fields': True,
            'operations': [{'op': 'require', 'source': 'sword', 'targt': 'elite'}],
        }
        result = run_cli('apply', str(DEMO), '-', '--dry-run', '--compact', stdin=json.dumps(script))
        self.assertEqual(result.returncode, 4, result.stderr)
        value = json.loads(result.stdout)
        self.assertIn('target', value['error'])

class AgentAutomationExampleTests(unittest.TestCase):
    def test_agent_automation_example_runs_from_source_without_installed_entry_point(self):
        env = os.environ.copy()
        env['PATH'] = ''
        env.pop('PYTHONPATH', None)
        proc = subprocess.run(
            [sys.executable, str(ROOT / 'examples' / 'agent_automation.py')],
            cwd=tempfile.gettempdir(),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(proc.stdout)
        self.assertEqual(value['capabilities']['tool_version'], '0.10.0rc12')
        self.assertTrue(value['inspection']['ok'])
        self.assertTrue(value['dry_run']['ok'])
        self.assertTrue(value['dry_run']['dry_run'])

class Rc7SimplifiedSurfaceTests(unittest.TestCase):
    def test_help_advertises_consolidated_surface_not_compat_aliases(self):
        result = run_cli('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        first = result.stdout.split('Author, inspect', 1)[0]
        self.assertIn('structure', first)
        self.assertIn('rules', first)
        self.assertIn('style', first)
        self.assertIn('inspect', first)
        self.assertIn('play', first)
        self.assertNotIn('apply-visuals', first)
        self.assertNotIn('visual-audit', first)
        self.assertNotIn(',new,', first.replace(' ', ''))

    def test_inspect_visual_replaces_visual_audit_for_agents(self):
        request = {'op': 'visual', 'kind': 'choice', 'missing_images': True, 'limit': 2, 'manifest_stub': True}
        result = run_cli('inspect', str(DEMO), '-', '--compact', stdin=json.dumps(request))
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        report = value['results'][0]['result']
        self.assertEqual(report['format'], 'iccplus-visual-audit')
        self.assertEqual(report['summary']['returned'], 2)
        self.assertEqual(len(report['manifest_stub']['items']), 2)

    def test_play_without_state_is_ephemeral_player_view(self):
        result = run_cli('play', str(DEMO), '--compact-view', '--compact')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertTrue(value['ok'])
        self.assertIn('available_choice_ids', value['view'])
        self.assertNotIn('state_written', value)
        self.assertNotIn('runtime_state', value)

    def test_style_cli_applies_many_distinct_images_in_one_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            project.write_bytes(DEMO.read_bytes())
            refs = ['sword', 'shield', 'elite']
            manifest = {'items': [{'id': ref, 'image': f'assets/{ref}.webp'} for ref in refs]}
            result = run_cli('style', str(project), '-', '--compact', stdin=json.dumps(manifest))
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value['changed_items'], 3)
            saved = json.loads(project.read_text(encoding='utf-8'))
            from iccplus_tools.model import ProjectIndex
            idx = ProjectIndex(saved)
            for ref in refs:
                self.assertEqual(idx.one(ref, 'choice').value['image'], f'assets/{ref}.webp')
