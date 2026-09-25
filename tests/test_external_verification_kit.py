from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from iccplus_tools.style_templates import apply_style_template
from iccplus_tools.upstream_2106 import default_project

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / 'verification' / 'scripts' / 'generate_verification_kit.py'


def _load_generator():
    spec = importlib.util.spec_from_file_location('iccplus_verification_kit', GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_style_presets_compile_to_native_styling_only():
    p = default_project()
    apply_style_template(p, 1)
    assert 'styleTemplate' not in p
    assert 'styleTemplates' not in p
    assert 'creatorComponent' not in p
    assert 'creatorComponents' not in p
    assert isinstance(p['styling'], dict)
    assert p['styling']['rowTitle'] == 'Courier'


def test_field_retention_fixture_contains_every_declared_field_and_no_tool_metadata():
    kit = _load_generator()
    p = kit.field_retention_project()
    coverage = kit.field_coverage(p)
    assert coverage['ok'], coverage
    assert kit.scan_tool_only_keys(p) == []


def test_generated_project_fixtures_never_embed_verification_or_component_templates():
    kit = _load_generator()
    projects = [
        kit.field_retention_project(),
        kit._merge_runtime_cases()[0],
        kit.advanced_interaction_project()[0],
    ]
    for project in projects:
        assert kit.scan_tool_only_keys(project) == []
        raw = json.dumps(project, ensure_ascii=False)
        for forbidden in ('creatorComponents', 'componentTemplates', 'styleTemplates', 'templateProvenance', '$iccplusLocal'):
            assert forbidden not in raw


def test_external_verification_case_counts_are_stable():
    kit = _load_generator()
    _, runtime, _ = kit._merge_runtime_cases()
    _, advanced = kit.advanced_interaction_project()
    creator = json.loads((ROOT / 'verification' / 'expected' / 'creator_cases.json').read_text())
    assert len(runtime) == 32
    assert len(advanced) == 12
    assert len(creator) == 12



def test_each_runtime_case_has_an_isolated_fixture_with_all_mapped_ids():
    kit = _load_generator()
    _, runtime, isolated = kit._merge_runtime_cases()
    from iccplus_tools.model import ProjectIndex
    for case in runtime:
        project = isolated[case['id']]
        idx = ProjectIndex(project)
        present = set()
        for kind, entities in idx.by_kind.items():
            for ent in entities:
                key = 'idx' if kind == 'score' else 'id'
                value = ent.value.get(key)
                if value:
                    present.add(str(value))
        for mapped in case['original_ids'].values():
            assert mapped in present, (case['id'], mapped)


def test_advanced_row_button_fixture_matches_pinned_button_modes():
    kit = _load_generator()
    project, _ = kit.advanced_interaction_project()
    rows = {row['id']: row for row in project['rows']}
    point = rows['adv_button_point']
    assert point['btnPointAddon'] is True
    assert point['buttonTypeRadio'] == 'sumaddon'
    weighted = rows['adv_button_choice']
    assert weighted['buttonRandom'] is True
    assert weighted['isWeightedRandom'] is True
    assert len(weighted['objects']) == 2
    assert {c['randomWeight'] for c in weighted['objects']} == {1, 9}


def test_all_audited_gui_features_have_explicit_verification_mapping():
    kit = _load_generator()
    _, runtime, _ = kit._merge_runtime_cases()
    _, advanced = kit.advanced_interaction_project()
    manifest = kit.build_manifest(runtime, advanced)
    mapped = {item['feature']: item['tests'] for item in manifest['creator_actions']}
    gui = kit.gui_parity_report()
    assert set(mapped) == {item['feature'] for item in gui['features']}
    assert all(tests for tests in mapped.values())
    # The mapping must be specific enough that the old catch-all F01/C01 pair
    # is not being used as a substitute for actual workflow verification.
    assert all(tests != ['F01', 'C01'] for tests in mapped.values())


def test_every_isolated_runtime_fixture_has_no_tool_only_template_metadata():
    kit = _load_generator()
    _, runtime, isolated = kit._merge_runtime_cases()
    assert len(runtime) == len(isolated) == 32
    for case_id, project in isolated.items():
        assert kit.scan_tool_only_keys(project) == [], case_id
