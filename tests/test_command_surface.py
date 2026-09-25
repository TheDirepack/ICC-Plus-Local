from __future__ import annotations

from iccplus_tools.capabilities import COMMAND_KINDS
from iccplus_tools.cli import parser, command_tree


def test_canonical_top_level_surface_is_workflow_centered():
    assert COMMAND_KINDS == [
        'reference', 'template', 'media', 'project',
        'inspect', 'generate', 'build', 'structure', 'rules', 'style', 'play',
    ]
    for retired in (
        'creator', 'test', 'check', 'build-viewer', 'session', 'state-check',
        'apply', 'format', 'export-project', 'build-summary', 'build-string',
    ):
        assert retired not in COMMAND_KINDS


def test_hidden_compatibility_aliases_do_not_pollute_help():
    help_text = parser().format_help()
    assert '==SUPPRESS==' not in help_text
    for canonical in ('reference', 'template', 'media', 'project', 'inspect', 'play'):
        assert canonical in help_text
    retired_tokens = ('{creator,', ',test,', ',check,', ',build-viewer,', ',session,', ',state-check,')
    for retired in retired_tokens:
        assert retired not in help_text


def test_template_media_project_and_reference_own_the_old_creator_workflows():
    p = parser()
    assert p.parse_args(['template', 'style', 'list']).func.__name__ == 'cmd_style_template'
    assert p.parse_args(['template', 'design', 'export', 'project.json', 'global']).func.__name__ == 'cmd_design'
    assert p.parse_args(['media', 'font', 'list', 'project.json']).func.__name__ == 'cmd_fonts'
    assert p.parse_args(['media', 'sound', 'import', 'project.json', 'ding.mp3']).func.__name__ == 'cmd_sound_effect'
    assert p.parse_args(['project', 'ids', 'export', 'project.json']).func.__name__ == 'cmd_id_csv'
    assert p.parse_args(['project', 'fragment', 'export', 'project.json', 'choice_a']).func.__name__ == 'cmd_export_fragment'
    assert p.parse_args(['reference', 'parity']).func.__name__ == 'cmd_gui_parity'
    assert p.parse_args(['reference', 'commands']).func.__name__ == 'cmd_command_tree'


def test_row_helpers_are_not_readvertised_because_structure_owns_them():
    paths = {item['path'] for item in command_tree()['paths']}
    assert not any(path.startswith('creator row') for path in paths)
    assert 'structure' in paths


def test_recursive_command_inventory_is_organized_and_complete():
    inventory = command_tree()
    paths = {item['path'] for item in inventory['paths']}
    assert inventory['top_level_count'] == 11
    assert inventory['max_depth'] >= 3
    assert 'template style apply' in paths
    assert 'template design import' in paths
    assert 'media image import' in paths
    assert 'media crop field' in paths
    assert 'media font add' in paths
    assert 'media sound import' in paths
    assert 'project fragment import' in paths
    assert 'project ids from-titles' in paths
    assert 'reference schema' in paths
    assert 'reference commands' in paths
    for removed in ('creator', 'test', 'check', 'build-viewer', 'media compress'):
        assert removed not in paths


def test_normal_phase_help_does_not_offer_validation_bypass_flags():
    p = parser()
    for command in ('structure', 'rules', 'style'):
        sub = p._subparsers._group_actions[0].choices[command]
        text = sub.format_help()
        assert '--no-validate' not in text
        assert '--allow-invalid' not in text
