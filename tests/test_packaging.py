from __future__ import annotations

import base64
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from iccplus_tools.editor import new_project
from iccplus_tools.packaging import build_viewer_package, export_project_zip, image_separation


def data_url(payload: bytes, mime: str = 'image/png') -> str:
    return f'data:{mime};base64,' + base64.b64encode(payload).decode('ascii')


class PackagingTests(unittest.TestCase):
    def test_image_separation_uses_creator_names_and_deduplicates(self):
        p = new_project()
        same = data_url(b'PNGDATA')
        other = data_url(b'OTHER')
        p['styling']['backgroundImage'] = same
        p['rows'] = [{
            'id': 'r', 'index': 0, 'title': 'R', 'titleText': '', 'debugTitle': '',
            'objectWidth': '', 'image': other, 'template': 1, 'isButtonRow': False,
            'isResultRow': False, 'resultGroupId': '', 'isInfoRow': False,
            'defaultAspectWidth': 1, 'defaultAspectHeight': 1, 'allowedChoices': 0,
            'currentChoices': 0, 'requireds': [], 'isEditModeOn': False,
            'isRequirementOpen': False, 'objects': [{
                'id': 'c', 'index': 0, 'title': 'C', 'text': '', 'debugTitle': '',
                'image': same, 'template': 1, 'objectWidth': '', 'isActive': False,
                'multipleUseVariable': 0, 'initMultipleTimesMinus': 0,
                'selectedThisManyTimesProp': 0, 'requireds': [], 'addons': [{
                    'id': '', 'title': 'A', 'text': '', 'template': 1, 'image': other,
                    'requireds': [], 'parentId': 'c', 'addonWidth': 'col-12'
                }], 'scores': [], 'groups': [], 'objectDesignGroups': []
            }], 'rowDesignGroups': []
        }]
        out, assets = image_separation(p)
        self.assertEqual(out['version'], '2.10.7')
        self.assertEqual(out['styling']['backgroundImage'], 'images/Bg.png')
        self.assertEqual(out['rows'][0]['objects'][0]['image'], 'images/Bg.png')
        self.assertEqual(out['rows'][0]['image'], 'images/R1.png')
        self.assertEqual(out['rows'][0]['objects'][0]['addons'][0]['image'], 'images/R1.png')
        self.assertEqual(list(assets), ['images/Bg.png', 'images/R1.png'])
        self.assertEqual(assets['images/Bg.png'], b'PNGDATA')

    def test_export_project_zip_contains_compact_project_and_assets(self):
        p = new_project()
        p['viewerConfig']['loadingBgImage'] = data_url(b'BG')
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'project.zip'
            report = export_project_zip(p, out)
            self.assertEqual(report['image_count'], 1)
            with zipfile.ZipFile(out) as zf:
                self.assertIn('project.json', zf.namelist())
                self.assertIn('images/Loading.png', zf.namelist())
                raw = zf.read('project.json')
                self.assertFalse(raw.endswith(b'\n'))
                project = json.loads(raw)
                self.assertEqual(project['viewerConfig']['loadingBgImage'], 'images/Loading.png')
                self.assertEqual(project['version'], '2.10.7')

    def _template(self, path: Path, *, local: bool = False) -> None:
        html = '<!doctype html><html><head><title>Old</title></head><body><span id="projectSize">0</span><div id="indicator" class="old">old</div></body></html>'
        css = ':root { --bg: old; --color: old; }\nbody{}'
        with zipfile.ZipFile(path, 'w') as zf:
            zf.writestr('index.html', html)
            zf.writestr('css/loading.css', css)
            if local:
                zf.writestr('js/app.js', 'x\n/*! Delete and replace project below */\n{}\n/*! End */\ny')

    def test_build_web_viewer_writes_project_and_loading_config(self):
        p = new_project()
        p['viewerConfig']['title'] = 'My CYOA'
        p['viewerConfig']['loadingText'] = '<b>Loading</b><script>bad()</script>'
        p['viewerConfig']['loadingType'] = 'spinner'
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            template = td / 'web.zip'; self._template(template)
            out = td / 'built.zip'
            report = build_viewer_package(p, template, out, mode='web', separate_images=False)
            self.assertEqual(report['mode'], 'web')
            with zipfile.ZipFile(out) as zf:
                self.assertIn('project.json', zf.namelist())
                html_text = zf.read('index.html').decode()
                self.assertIn('<title>My CYOA</title>', html_text)
                self.assertIn('class="spinner"', html_text)
                self.assertIn('<b>Loading</b>', html_text)
                self.assertNotIn('<script>', html_text)
                self.assertIn('--bg:', zf.read('css/loading.css').decode())

    def test_build_local_viewer_embeds_project_marker(self):
        p = new_project()
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            template = td / 'local.zip'; self._template(template, local=True)
            out = td / 'built.zip'
            build_viewer_package(p, template, out, mode='local', separate_images=False)
            with zipfile.ZipFile(out) as zf:
                self.assertNotIn('project.json', zf.namelist())
                js = zf.read('js/app.js').decode()
                self.assertIn('"version":"2.10.7"', js)
                self.assertIn('/*! End */', js)


if __name__ == '__main__':
    unittest.main()


def test_creator_save_payload_matches_returned_official_2106_field_roundtrip():
    from iccplus_tools.packaging import creator_save_payload
    root = Path(__file__).resolve().parents[1]
    source = json.loads((root / 'verification' / 'fixtures' / '01_field_retention.json').read_text(encoding='utf-8'))
    expected = json.loads((root / 'tests' / 'fixtures' / 'official_2106_field_roundtrip.json').read_text(encoding='utf-8'))
    assert creator_save_payload(source, target_version='2.10.6') == expected
