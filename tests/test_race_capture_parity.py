"""Offline race-capture parity checks using small synthetic official-evidence ZIPs."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from iccplus_tools.simulator import Simulator
from verification.scripts.check_race_capture_parity import EvidenceError, compare_archives

DEMO = json.loads((Path(__file__).resolve().parents[1] / 'examples' / 'demo_project.json').read_text())


class RaceCaptureParityTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.project = copy.deepcopy(DEMO)
        self.sim = Simulator(self.project)
        self.project_bytes = json.dumps(self.project).encode()
        self.sha = hashlib.sha256(self.project_bytes).hexdigest()

    @staticmethod
    def _package(path, kind, files, *, run='official-run', source=None, good=True):
        manifest = {'kind': kind, 'run_id': run,
                    'notes': {'status': {'all_passed': good}},
                    'files': {name: {'sha256': hashlib.sha256(data).hexdigest(),
                                     'size': len(data)} for name, data in files.items()}}
        if source is not None:
            manifest['source_project_sha256'] = source
        with ZipFile(path, 'w') as archive:
            for name, value in files.items():
                archive.writestr(name, value)
            archive.writestr('PACKAGE_MANIFEST.json', json.dumps(manifest))

    def write_archives(self, *, wrong_row=False, wrong_build=False, wrong_run=False,
                       card_capture=False, failed_run=False, scroll_finished=True):
        inputs = self.root / 'inputs.zip'
        races = self.root / 'races-0001.zip'
        self._package(inputs, 'inputs', {'inputs/project.json': self.project_bytes}, source=self.sha)
        base = 'results/roster/races/test_race/'
        rows = self.sim.visible_row_ids()
        if wrong_row:
            rows = rows[:-1]
        frames = [{'status': 'captured', 'visible_row_ids': rows}]
        if card_capture:
            frames[0]['dom_choice_cards'] = [
                {'choice_id': c.id, 'row_id': c.row_id, 'rendered': True,
                 'selected': self.sim._active(c.id)}
                for c in self.sim.index.by_kind.get('choice', []) if self.sim.entity_visible(c.id)
            ]
        export = self.sim.export_build_string()
        if wrong_build:
            export += '/not_official'
        data = {
            base + 'build/normalized_profile.state.json': json.dumps(self.sim.export_state()).encode(),
            base + 'viewer_attempt_001/import_verification.json': json.dumps({
                'verified_by': "native Viewer's own Build Form export",
                'expected_build_form': {}, 'viewer_native_export': {},
                'missing_after_import': [], 'extra_after_import': [],
                'count_mismatches': [], 'text_mismatches': [],
                'missing_requested_after_import': []}).encode(),
            base + 'viewer_attempt_001/select_scroll_summary.json': json.dumps({
                'state': 'finished', 'scroll_reached_end': scroll_finished,
                'project_sha256': self.sha}).encode(),
            base + 'viewer_attempt_001/scroll_frames.jsonl': '\n'.join(json.dumps(f) for f in frames).encode(),
            base + 'viewer_attempt_001/viewer_build_form_after_scroll.txt': export.encode(),
        }
        self._package(races, 'races', data, run='other-run' if wrong_run else 'official-run',
                      source=self.sha, good=not failed_run)
        return inputs, races

    def test_complete_observed_rows_and_native_export(self):
        inputs, races = self.write_archives()
        report = compare_archives(inputs, [races])
        self.assertEqual((report['passed'], report['mismatched'], report['incomplete']), (1, 0, 0))
        self.assertTrue(report['checked_dimensions_passed'])
        self.assertFalse(report['fully_verified'])
        self.assertEqual(report['details'][0]['choice_card_coverage'], 'not_recorded')

    def test_native_build_form_difference_is_not_silently_accepted(self):
        inputs, races = self.write_archives(wrong_build=True)
        report = compare_archives(inputs, [races])
        self.assertEqual(report['mismatched'], 1)
        self.assertIn('local Build Form', str(report['details'][0]['mismatches']))

    def test_missing_browser_row_is_not_claimed_as_parity(self):
        inputs, races = self.write_archives(wrong_row=True)
        report = compare_archives(inputs, [races])
        self.assertEqual(report['mismatched'], 1)
        self.assertTrue(report['details'][0]['missing_rows'])

    def test_missing_card_evidence_requires_explicit_partial_status(self):
        inputs, races = self.write_archives()
        report = compare_archives(inputs, [races], require_choice_cards=True)
        self.assertEqual(report['incomplete'], 1)
        self.assertFalse(report['fully_verified'])
        inputs, races = self.write_archives(card_capture=True)
        report = compare_archives(inputs, [races], require_choice_cards=True)
        self.assertEqual(report['passed'], 1)
        self.assertTrue(report['fully_verified'])

    def test_source_run_mismatch_is_blocking_not_a_parity_fail(self):
        inputs, races = self.write_archives(wrong_run=True)
        with self.assertRaisesRegex(EvidenceError, 'mismatched run ID'):
            compare_archives(inputs, [races])

    def test_failed_or_unfinished_evidence_is_not_certified(self):
        inputs, races = self.write_archives(failed_run=True)
        report = compare_archives(inputs, [races])
        self.assertEqual(report['passed'], 1)
        self.assertFalse(report['fully_verified'])
        inputs, races = self.write_archives(scroll_finished=False)
        report = compare_archives(inputs, [races])
        self.assertEqual(report['incomplete'], 1)
        self.assertFalse(report['fully_verified'])


if __name__ == '__main__':
    unittest.main()
