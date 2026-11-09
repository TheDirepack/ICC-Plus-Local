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
                       card_capture=False, failed_run=False, scroll_finished=True,
                       partial_card_frame=False, wrong_card_row=False, duplicate_card=False):
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
            if wrong_card_row:
                frames[0]['dom_choice_cards'][0]['row_id'] = 'wrong_display_row'
            if duplicate_card:
                frames[0]['dom_choice_cards'].append(copy.deepcopy(frames[0]['dom_choice_cards'][0]))
            if partial_card_frame:
                frames.append({'status': 'captured', 'visible_row_ids': rows})
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

    def write_index(self, inputs, races, *, extra_race=False, bad_members=False, all_passed=True):
        def archive_record(path):
            data = path.read_bytes()
            return {'file': path.name, 'sha256': hashlib.sha256(data).hexdigest(),
                    'bytes': len(data), 'files': 1}
        records = {'inputs': archive_record(inputs), 'races-0001': archive_record(races),
                   'regular': {'file': 'regular.zip', 'sha256': '0' * 64, 'bytes': 0}}
        if extra_race:
            records['races-0002'] = {
                'file': 'races-0002.zip', 'sha256': 'f' * 64, 'bytes': 100}
        index = {
            'format': 'cyra-sharded-package-v3', 'run_id': 'official-run',
            'source_project_sha256': self.sha,
            'run_status': {'all_passed': all_passed}, 'archives': records,
            'races': {'wrong_key' if bad_members else 'test_race': ['races-0001.zip']},
        }
        path = self.root / 'PACKAGE_INDEX.json'
        path.write_text(json.dumps(index))
        return path

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
        self.assertFalse(report['fully_verified'])  # a single provided ZIP is not proof of all shards
        index = self.write_index(inputs, races)
        report = compare_archives(inputs, [races], require_choice_cards=True, package_index=index)
        self.assertTrue(report['race_inventory_verified'])
        self.assertTrue(report['fully_verified'])

    def test_partial_dom_inventory_is_not_counted_complete(self):
        inputs, races = self.write_archives(card_capture=True, partial_card_frame=True)
        report = compare_archives(inputs, [races], require_choice_cards=True)
        self.assertEqual(report['incomplete'], 1)
        self.assertIn('partial per-card', report['details'][0]['reason'])

    def test_card_row_misplacement_is_detected(self):
        inputs, races = self.write_archives(card_capture=True, wrong_card_row=True)
        report = compare_archives(inputs, [races])
        self.assertEqual(report['mismatched'], 1)
        self.assertTrue(report['details'][0]['unexpected_choice_cards'])
        self.assertTrue(report['details'][0]['missing_choice_cards'])

    def test_duplicate_card_in_single_frame_is_detected(self):
        inputs, races = self.write_archives(card_capture=True, duplicate_card=True)
        report = compare_archives(inputs, [races])
        self.assertEqual(report['mismatched'], 1)
        self.assertIn('duplicate mounted', str(report['details'][0]['mismatches']))

    def test_unmodeled_result_row_card_differential_is_incomplete_not_mismatch(self):
        row = copy.deepcopy(self.project['rows'][0])
        row.update(id='result_summary', title='Results', objects=[], isResultRow=True)
        self.project['rows'].append(row)
        self.project_bytes = json.dumps(self.project).encode()
        self.sha = hashlib.sha256(self.project_bytes).hexdigest()
        self.sim = Simulator(self.project)
        inputs, races = self.write_archives(card_capture=True)
        report = compare_archives(inputs, [races])
        self.assertEqual(report['incomplete'], 1)
        self.assertIn('Result/Group Row', report['details'][0]['reason'])

    def test_indexed_missing_race_shard_cannot_pass(self):

        inputs, races = self.write_archives(card_capture=True)
        index = self.write_index(inputs, races, extra_race=True)
        with self.assertRaisesRegex(EvidenceError, 'incomplete or noncontiguous'):
            compare_archives(inputs, [races], package_index=index)

    def test_indexed_archive_hash_mismatch_cannot_pass(self):
        inputs, races = self.write_archives(card_capture=True)
        index = self.write_index(inputs, races)
        with races.open('ab') as archive:
            archive.write(b'tampered after archive manifest')
        with self.assertRaisesRegex(EvidenceError, 'whole-archive size/SHA-256 mismatch'):
            compare_archives(inputs, [races], package_index=index)

    def test_indexed_wrong_race_membership_cannot_pass(self):
        inputs, races = self.write_archives(card_capture=True)
        index = self.write_index(inputs, races, bad_members=True)
        with self.assertRaisesRegex(EvidenceError, 'race-to-ZIP inventory differs'):
            compare_archives(inputs, [races], package_index=index)

    def test_index_run_status_blocks_full_verification(self):
        inputs, races = self.write_archives(card_capture=True)
        index = self.write_index(inputs, races, all_passed=False)
        report = compare_archives(inputs, [races], package_index=index)
        self.assertTrue(report['race_inventory_verified'])
        self.assertFalse(report['fully_verified'])
        self.assertFalse(report['overall_capture_run_passed'])

    def test_unlisted_zip_member_rejected(self):
        inputs, races = self.write_archives()
        with ZipFile(races, 'a') as archive:
            archive.writestr('unlisted.txt', 'this was added after the manifest')
        with self.assertRaisesRegex(EvidenceError, 'unlisted'):
            compare_archives(inputs, [races])

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
