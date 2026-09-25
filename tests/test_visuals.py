from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import pytest

from iccplus_tools.model import ProjectIndex
from iccplus_tools.visuals import apply_visual_manifest, visual_audit

ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / 'examples' / 'demo_project.json').read_text())


def test_visual_audit_builds_compact_missing_image_queue():
    project = copy.deepcopy(PROJECT)
    sword = ProjectIndex(project).one('sword', 'choice')
    assert sword is not None
    sword.value['image'] = 'assets/sword.webp'
    report = visual_audit(project, kinds=['choice'], missing_images=True)
    refs = {item['ref'] for item in report['items']}
    assert 'sword' not in refs
    assert 'shield' in refs
    assert all(item['kind'] == 'choice' for item in report['items'])
    assert all('text_excerpt' in item for item in report['items'])


def test_visual_audit_can_check_local_asset_presence():
    project = copy.deepcopy(PROJECT)
    sword = ProjectIndex(project).one('sword', 'choice')
    assert sword is not None
    sword.value['image'] = 'assets/sword.webp'
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'assets').mkdir()
        (root / 'assets' / 'sword.webp').write_bytes(b'fake')
        report = visual_audit(project, kinds=['choice'], row='gear', asset_root=root)
        item = next(x for x in report['items'] if x['ref'] == 'sword')
        assert item['asset_exists'] is True
        assert item['asset_bytes'] == 4


def test_apply_visual_manifest_uses_presets_native_styles_and_source_sidecar():
    project = copy.deepcopy(PROJECT)
    manifest = {
        'format': 'iccplus-visual-manifest',
        'format_version': 1,
        'project': {
            'styling': {'background': {'bgColorIsOn': True, 'backgroundColor': '#101010FF'}},
            'customCSSAppend': '.choice-note { opacity: .9; }',
        },
        'presets': {
            'portrait-card': {
                'template': 2,
                'width': 'col-md-4',
                'styling': {
                    'object_image': {'objectImageWidth': 100, 'objectImgOverflowIsOn': True},
                    'text': {'objectTitleAlign': 'center'},
                },
            }
        },
        'items': [{
            'id': 'sword',
            'preset': 'portrait-card',
            'image': 'assets/sword.webp',
            'source': {'url': 'https://example.invalid/sword', 'creator': 'Example'},
            'credit': 'Example',
        }],
    }
    updated, report = apply_visual_manifest(project, manifest)
    sword = ProjectIndex(updated).one('sword', 'choice')
    assert sword is not None
    assert sword.value['image'] == 'assets/sword.webp'
    assert sword.value['template'] == 2
    assert sword.value['objectWidth'] == 'col-md-4'
    assert sword.value['styling']['objectImageWidth'] == 100
    assert sword.value['styling']['objectTitleAlign'] == 'center'
    assert updated['styling']['backgroundColor'] == '#101010FF'
    assert '.choice-note' in updated['customCSS']
    assert report['source_records'][0]['ref'] == 'sword'


def test_apply_visual_manifest_copy_from_copies_treatment_not_image_by_default():
    project = copy.deepcopy(PROJECT)
    idx = ProjectIndex(project)
    sword = idx.one('sword', 'choice'); shield = idx.one('shield', 'choice')
    assert sword is not None and shield is not None
    sword.value.update({'image': 'assets/sword.webp', 'template': 3, 'objectWidth': 'col-md-6'})
    sword.value['styling'] = {'objectBorderIsOn': True, 'objectBorderWidth': 2}
    shield.value['image'] = 'assets/shield.webp'
    updated, _ = apply_visual_manifest(project, {'items': [{'id': 'shield', 'copy_from': 'sword'}]})
    target = ProjectIndex(updated).one('shield', 'choice')
    assert target is not None
    assert target.value['image'] == 'assets/shield.webp'
    assert target.value['template'] == 3
    assert target.value['objectWidth'] == 'col-md-6'
    assert target.value['styling']['objectBorderWidth'] == 2


def test_apply_visual_manifest_uses_official_design_groups_for_reusable_choice_style():
    updated, report = apply_visual_manifest(copy.deepcopy(PROJECT), {
        'design_groups': {
            'shared-card': {
                'kind': 'choice',
                'name': 'Shared card',
                'styling': {
                    'object': {'objectBorderIsOn': True, 'objectBorderWidth': 2},
                    'text': {'objectTitleAlign': 'center'},
                },
            },
        },
        'items': [{
            'refs': ['sword', 'shield'],
            'design_group': 'shared-card',
        }],
    })
    idx = ProjectIndex(updated)
    group = idx.one('shared-card', 'choice_design_group')
    assert group is not None
    assert group.value['styling']['objectBorderWidth'] == 2
    assert group.value['privateObjectIsOn'] is True
    assert group.value['privateTextIsOn'] is True
    assert set(group.value['elements']) >= {'sword', 'shield'}
    for ident in ('sword', 'shield'):
        choice = idx.one(ident, 'choice')
        assert choice is not None
        assert 'shared-card' in choice.value['objectDesignGroups']
        assert choice.value.get('styling', {}) == {}
    assert report['design_groups'][0]['id'] == 'shared-card'
    assert report['changed_items'] == 2


def test_apply_visual_manifest_can_link_design_group_to_normal_group():
    updated, report = apply_visual_manifest(copy.deepcopy(PROJECT), {
        'design_groups': {
            'element-card': {
                'kind': 'choice',
                'groups': ['elements'],
                'styling': {'text': {'objectTitleAlign': 'center'}},
            },
        },
        'items': [],
    })
    idx = ProjectIndex(updated)
    design = idx.one('element-card', 'choice_design_group')
    normal = idx.one('elements', 'group')
    assert design is not None and normal is not None
    assert 'elements' in design.value['groupElements']
    assert 'element-card' in normal.value['designGroups']
    assert idx.one('fire', 'choice').value.get('objectDesignGroups', []) == []
    assert report['design_groups'][0]['id'] == 'element-card'


def test_apply_visual_manifest_rejects_wrong_design_group_family():
    with pytest.raises(ValueError, match='not a row design group'):
        apply_visual_manifest(copy.deepcopy(PROJECT), {
            'design_groups': {
                'choice-style': {
                    'kind': 'choice',
                    'styling': {'text': {'objectTitleAlign': 'center'}},
                },
            },
            'items': [{
                'id': 'gear',
                'design_group': 'choice-style',
            }],
        })


def test_apply_visual_manifest_rejects_shared_private_inline_styling():
    with pytest.raises(ValueError, match='define an official Design Group'):
        apply_visual_manifest(copy.deepcopy(PROJECT), {
            'items': [{
                'refs': ['sword', 'shield'],
                'styling': {'text': {'objectTitleAlign': 'center'}},
            }],
        })


def test_apply_visual_manifest_rejects_unknown_style_field():
    with pytest.raises(ValueError, match='unknown styling field'):
        apply_visual_manifest(copy.deepcopy(PROJECT), {
            'items': [{'id': 'sword', 'styling': {'definitelyNotAField': 1}}]
        })


def test_visual_audit_limit_reports_full_match_count_and_manifest_stub():
    report = visual_audit(copy.deepcopy(PROJECT), kinds=['choice'], limit=2, manifest_stub=True)
    assert report['summary']['total'] > 2
    assert report['summary']['returned'] == 2
    assert report['summary']['truncated'] is True
    assert len(report['manifest_stub']['items']) == 2


def test_visual_audit_missing_assets_filters_broken_local_refs():
    project = copy.deepcopy(PROJECT)
    idx = ProjectIndex(project)
    sword = idx.one('sword', 'choice'); shield = idx.one('shield', 'choice')
    assert sword is not None and shield is not None
    sword.value['image'] = 'assets/sword.webp'
    shield.value['image'] = 'https://example.invalid/shield.webp'
    with tempfile.TemporaryDirectory() as tmp:
        report = visual_audit(project, kinds=['choice'], asset_root=tmp, missing_assets=True)
    assert [x['ref'] for x in report['items']] == ['sword']
    assert report['items'][0]['image_kind'] == 'local'
    assert report['items'][0]['asset_exists'] is False
    assert report['summary']['missing_local_assets'] == 1


def test_visual_audit_missing_assets_requires_asset_root():
    with pytest.raises(ValueError, match='requires --asset-root'):
        visual_audit(copy.deepcopy(PROJECT), missing_assets=True)


def test_apply_visual_manifest_supports_explicit_refs_batch():
    updated, report = apply_visual_manifest(copy.deepcopy(PROJECT), {
        'presets': {'wide': {'width': 'col-md-6'}},
        'items': [{'refs': ['sword', 'shield'], 'preset': 'wide'}],
    })
    idx = ProjectIndex(updated)
    assert idx.one('sword', 'choice').value['objectWidth'] == 'col-md-6'
    assert idx.one('shield', 'choice').value['objectWidth'] == 'col-md-6'
    assert report['changed_items'] == 2


def test_apply_visual_manifest_rejects_unknown_visual_key_instead_of_ignoring_it():
    with pytest.raises(ValueError, match='unknown visual manifest items\\[0\\] field'):
        apply_visual_manifest(copy.deepcopy(PROJECT), {
            'items': [{'id': 'sword', 'widht': 'col-md-6'}],
        })


def test_apply_visual_manifest_custom_css_append_is_idempotent():
    manifest = {'project': {'customCSSAppend': '.visual-note { opacity: .9; }'}, 'items': []}
    once, first = apply_visual_manifest(copy.deepcopy(PROJECT), manifest)
    twice, second = apply_visual_manifest(once, manifest)
    assert twice['customCSS'].count('.visual-note { opacity: .9; }') == 1
    assert 'customCSS' in first['project_changes']
    assert 'customCSS' not in second['project_changes']


def test_apply_visual_manifest_can_replace_and_unset_inline_styling():
    project = copy.deepcopy(PROJECT)
    sword = ProjectIndex(project).one('sword', 'choice')
    assert sword is not None
    sword.value['styling'] = {'objectBorderIsOn': True, 'objectBorderWidth': 7, 'objectTitleAlign': 'left'}
    updated, _ = apply_visual_manifest(project, {
        'items': [{
            'id': 'sword',
            'replace_styling': True,
            'styling': {'object': {'objectBorderIsOn': True, 'objectBorderWidth': 2}, 'text': {'objectTitleAlign': 'center'}},
            'unset_styling': ['objectBorderIsOn'],
        }],
    })
    style = ProjectIndex(updated).one('sword', 'choice').value['styling']
    assert style == {'objectBorderWidth': 2, 'objectTitleAlign': 'center'}


def test_apply_visual_manifest_rejects_duplicate_target_entries():
    with pytest.raises(ValueError, match='appears more than once'):
        apply_visual_manifest(copy.deepcopy(PROJECT), {
            'items': [{'id': 'sword', 'template': 2}, {'ref': 'sword', 'width': 'col-md-6'}],
        })


def test_bundled_visual_manifest_example_applies_to_demo_project():
    manifest = json.loads((ROOT / 'examples' / 'visual_manifest.json').read_text())
    updated, report = apply_visual_manifest(copy.deepcopy(PROJECT), manifest)
    assert report['changed_items'] == 4
    idx = ProjectIndex(updated)
    assert idx.one('sword', 'choice').value['image'] == 'assets/sword.webp'
    assert idx.one('shield', 'choice').value['image'] == 'assets/shield.webp'
    assert idx.one('fire', 'choice').value['objectWidth'] == 'col-md-4'
    assert idx.one('water', 'choice').value['objectWidth'] == 'col-md-4'
    design = idx.one('portrait-card', 'choice_design_group')
    assert design is not None
    assert design.value['styling']['objectImageWidth'] == 100
    assert set(design.value['elements']) >= {'sword', 'shield', 'fire', 'water'}
    assert idx.one('sword', 'choice').value.get('styling', {}) == {}


def test_visual_audit_style_values_are_opt_in():
    project = copy.deepcopy(PROJECT)
    sword = ProjectIndex(project).one('sword', 'choice')
    assert sword is not None
    sword.value['styling'] = {'objectBorderIsOn': True, 'objectBorderWidth': 2}
    compact = visual_audit(project, kinds=['choice'], row='gear')
    detailed = visual_audit(project, kinds=['choice'], row='gear', style_values=True)
    compact_sword = next(x for x in compact['items'] if x['ref'] == 'sword')
    detailed_sword = next(x for x in detailed['items'] if x['ref'] == 'sword')
    assert 'styling' not in compact_sword
    assert detailed_sword['styling']['objectBorderWidth'] == 2
    assert detailed['filters']['style_values'] is True


def test_style_automatically_compresses_embedded_images(monkeypatch):
    from iccplus_tools.assets import BlobResult
    import iccplus_tools.image_assets as image_assets
    import base64

    source = b'original-image-bytes' * 100
    replacement = b'compressed-avif'

    def fake_compress(data, declared_mime, cfg):
        assert data == source
        return BlobResult(True, replacement, 'image/avif', '.avif', declared_mime or 'image/png', encoder='test', reason='converted')

    monkeypatch.setattr(image_assets, 'compress_blob', fake_compress)
    data_url = 'data:image/png;base64,' + base64.b64encode(source).decode('ascii')
    updated, report = apply_visual_manifest(copy.deepcopy(PROJECT), {
        'items': [{'id': 'sword', 'image': data_url}],
    })
    sword = ProjectIndex(updated).one('sword', 'choice')
    assert sword is not None
    assert sword.value['image'].startswith('data:image/avif;base64,')
    item = report['items'][0]
    assert item['image_compression']['automatic'] is True
    assert item['image_compression']['changed'] is True
    assert item['image_compression']['output_mime'] == 'image/avif'


def test_style_automatically_compresses_local_image_and_rewrites_reference(monkeypatch, tmp_path):
    from iccplus_tools.assets import BlobResult
    import iccplus_tools.image_assets as image_assets

    source = tmp_path / 'portrait.png'
    source.write_bytes(b'png-source' * 100)
    replacement = b'avif-output'

    def fake_compress(data, declared_mime, cfg):
        return BlobResult(True, replacement, 'image/avif', '.avif', declared_mime or 'image/png', encoder='test', reason='converted')

    monkeypatch.setattr(image_assets, 'compress_blob', fake_compress)
    updated, report = apply_visual_manifest(copy.deepcopy(PROJECT), {
        'items': [{'id': 'sword', 'image': 'portrait.png'}],
    }, asset_base=tmp_path)
    sword = ProjectIndex(updated).one('sword', 'choice')
    assert sword is not None
    assert sword.value['image'] == 'portrait.avif'
    assert (tmp_path / 'portrait.avif').read_bytes() == replacement
    assert report['items'][0]['image_compression']['changed'] is True
