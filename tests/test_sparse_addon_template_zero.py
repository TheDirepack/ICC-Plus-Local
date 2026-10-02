from __future__ import annotations

from iccplus_tools.sparse_project import sparsify_project
from iccplus_tools.upstream_2106 import ICCPLUS_VERSION


def test_addon_template_zero_is_omitted_because_viewer_normalizes_it_to_one() -> None:
    source = {
        'version': ICCPLUS_VERSION,
        'rows': [{
            'id': 'r',
            'objects': [{
                'id': 'c',
                'addons': [
                    {'id': '', 'template': 0, 'requireds': [], 'parentId': 'c'},
                    {'id': '', 'template': 1, 'requireds': [], 'parentId': 'c'},
                    {'id': '', 'template': 2, 'requireds': [], 'parentId': 'c'},
                ],
            }],
        }],
    }

    sparse, report = sparsify_project(source, require_complete=False)
    addons = sparse['rows'][0]['objects'][0]['addons']
    assert 'template' not in addons[0]
    assert 'template' not in addons[1]
    assert addons[2]['template'] == 2
    assert report['removed_by_rule']['addon_template_normalizes_to_one'] == 2
