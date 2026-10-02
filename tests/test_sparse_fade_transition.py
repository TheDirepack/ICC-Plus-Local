from __future__ import annotations

from iccplus_tools.sparse_project import sparsify_project
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION


def _project_with_choice(choice: dict) -> dict:
    return {
        'version': ICCPLUS_VERSION,
        'rows': [{'id': 'row', 'objects': [choice]}],
    }


def test_choice_legacy_fade_fields_strip_when_loader_has_no_effect() -> None:
    source = _project_with_choice({
        'id': 'choice',
        'isFadeTransition': True,
        'fadeTransitionIsOn': False,
        'fadeTransitionTime': 900,
        'fadeInTransitionTime': 250,
        'fadeOutTransitionTime': 350,
    })

    sparse, report = sparsify_project(source, require_complete=False)
    choice = sparse['rows'][0]['objects'][0]

    assert 'fadeTransitionIsOn' not in choice
    assert 'fadeTransitionTime' not in choice
    assert choice['isFadeTransition'] is True
    assert choice['fadeInTransitionTime'] == 250
    assert choice['fadeOutTransitionTime'] == 350
    assert report['removed_by_rule']['legacy_fade_transition_no_loader_effect'] == 2


def test_choice_legacy_fade_fields_strip_when_they_match_modern_times() -> None:
    source = _project_with_choice({
        'id': 'choice',
        'isFadeTransition': True,
        'fadeTransitionIsOn': True,
        'fadeTransitionTime': 250,
        'fadeInTransitionTime': 250,
        'fadeOutTransitionTime': 250,
    })

    sparse, report = sparsify_project(source, require_complete=False)
    choice = sparse['rows'][0]['objects'][0]

    assert 'fadeTransitionIsOn' not in choice
    assert 'fadeTransitionTime' not in choice
    assert choice['fadeInTransitionTime'] == 250
    assert choice['fadeOutTransitionTime'] == 250
    assert report['removed_by_rule']['legacy_fade_transition_matches_modern_times'] == 2


def test_choice_legacy_fade_fields_remain_when_loader_would_override_modern_times() -> None:
    source = _project_with_choice({
        'id': 'choice',
        'isFadeTransition': True,
        'fadeTransitionIsOn': True,
        'fadeTransitionTime': 900,
        'fadeInTransitionTime': 250,
        'fadeOutTransitionTime': 350,
    })

    sparse, report = sparsify_project(source, require_complete=False)
    choice = sparse['rows'][0]['objects'][0]

    assert choice['fadeTransitionIsOn'] is True
    assert choice['fadeTransitionTime'] == 900
    assert choice['fadeInTransitionTime'] == 250
    assert choice['fadeOutTransitionTime'] == 350
    assert 'legacy_fade_transition_matches_modern_times' not in report['removed_by_rule']


def test_addon_legacy_fade_fields_are_unused_by_pinned_loader() -> None:
    source = _project_with_choice({
        'id': 'choice',
        'addons': [{
            'id': '',
            'template': 2,
            'fadeTransitionIsOn': True,
            'fadeTransitionTime': 900,
            'isFadeTransition': True,
            'fadeInTransitionTime': 250,
            'fadeOutTransitionTime': 350,
        }],
    })

    sparse, report = sparsify_project(source, require_complete=False)
    addon = sparse['rows'][0]['objects'][0]['addons'][0]

    assert 'fadeTransitionIsOn' not in addon
    assert 'fadeTransitionTime' not in addon
    assert addon['isFadeTransition'] is True
    assert addon['fadeInTransitionTime'] == 250
    assert addon['fadeOutTransitionTime'] == 350
    assert report['removed_by_rule']['legacy_fade_transition_unused_on_addon'] == 2
