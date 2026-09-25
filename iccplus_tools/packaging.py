from __future__ import annotations

import base64
import copy
import html
from html.parser import HTMLParser
import io
import re
import zipfile
from pathlib import Path
from typing import Any

from .upstream_2106 import ICCPLUS_VERSION, json_stringify

_DATA_URL = re.compile(r'^data:(image/[^;]+);base64,(.+)$', re.DOTALL)
_EXTENSIONS = {
    'svg+xml': 'svg',
    'vnd.microsoft.icon': 'ico',
    'x-icon': 'ico',
}


def _remove_nulls(value: Any) -> Any:
    """Match ICC Plus 2.10.7 removeNulls for JSON-compatible values."""
    if isinstance(value, list):
        out = []
        for item in value:
            cleaned = _remove_nulls(item)
            if cleaned is None:
                continue
            if isinstance(cleaned, dict) and not cleaned:
                continue
            out.append(cleaned)
        return out
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            cleaned = _remove_nulls(item)
            if cleaned is not None:
                out[key] = cleaned
        return out or None
    return value


def _image_payload(data_url: str) -> tuple[str, bytes] | None:
    match = _DATA_URL.match(data_url)
    if not match:
        return None
    mime = match.group(1)
    subtype = mime.split('/', 1)[1]
    ext = _EXTENSIONS.get(subtype, subtype)
    try:
        data = base64.b64decode(match.group(2), validate=False)
    except Exception as exc:
        raise ValueError('invalid base64 image data URL') from exc
    return ext, data


def _add_image(path: str, data_url: str, seen: dict[str, str], assets: dict[str, bytes]) -> str:
    previous = seen.get(data_url)
    if previous is not None:
        return previous
    parsed = _image_payload(data_url)
    if parsed is None:
        return data_url
    _ext, data = parsed
    seen[data_url] = path
    assets[path] = data
    return path


def _separate_field(obj: dict[str, Any], key: str, stem: str, seen: dict[str, str], assets: dict[str, bytes]) -> None:
    value = obj.get(key)
    if not isinstance(value, str) or not value or _DATA_URL.match(value) is None:
        return
    parsed = _image_payload(value)
    assert parsed is not None
    ext, _ = parsed
    obj[key] = _add_image(f'images/{stem}.{ext}', value, seen, assets)


def viewer_image_separation(project: dict[str, Any], *, seen: dict[str, str] | None = None, assets: dict[str, bytes] | None = None) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Mirror AppSaveLoad.svelte viewerImgSeparation()."""
    temp = project
    seen = {} if seen is None else seen
    assets = {} if assets is None else assets
    viewer = temp.get('viewerConfig')
    if isinstance(viewer, dict):
        _separate_field(viewer, 'loadingBgImage', 'Loading', seen, assets)
        _separate_field(viewer, 'favicon', 'favi', seen, assets)
    return temp, assets


def image_separation(project: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Mirror ICC Plus 2.10.7 Creator imageSeparation().

    The input is not mutated. Paths intentionally preserve source quirks,
    including backpack change-background names that use the R prefix.
    """
    temp = copy.deepcopy(project)
    temp['version'] = ICCPLUS_VERSION
    seen: dict[str, str] = {}
    assets: dict[str, bytes] = {}

    root_style = temp.get('styling')
    if isinstance(root_style, dict):
        for key, stem in (
            ('backgroundImage', 'Bg'), ('rowBackgroundImage', 'RBg'),
            ('objectBackgroundImage', 'OBg'), ('addonBackgroundImage', 'ABg'),
            ('rowBorderImage', 'RB'), ('objectBorderImage', 'OB'), ('addonBorderImage', 'AB'),
        ):
            _separate_field(root_style, key, stem, seen, assets)

    def process_rows(rows: Any, *, backpack: bool) -> None:
        if not isinstance(rows, list):
            return
        for ri, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            rp = f'BR{ri + 1}' if backpack else f'R{ri + 1}'
            styling = row.get('styling')
            if isinstance(styling, dict):
                for key, suffix in (
                    ('rowBackgroundImage', 'RBg'), ('objectBackgroundImage', 'OBg'),
                    ('addonBackgroundImage', 'ABg'), ('rowBorderImage', 'RB'),
                    ('objectBorderImage', 'OB'), ('addonBorderImage', 'AB'),
                ):
                    _separate_field(styling, key, f'{rp}_{suffix}', seen, assets)
            _separate_field(row, 'image', rp, seen, assets)
            objects = row.get('objects')
            if not isinstance(objects, list):
                continue
            for ci, choice in enumerate(objects):
                if not isinstance(choice, dict):
                    continue
                cp = f'{rp}C{ci + 1}'
                styling = choice.get('styling')
                if isinstance(styling, dict):
                    for key, suffix in (
                        ('objectBackgroundImage', 'OBg'), ('objectBorderImage', 'OB'),
                        ('addonBackgroundImage', 'ABg'), ('addonBorderImage', 'AB'),
                    ):
                        _separate_field(styling, key, f'{cp}_{suffix}', seen, assets)
                _separate_field(choice, 'image', cp, seen, assets)
                if choice.get('changeBgImage'):
                    # Source uses R rather than BR here even for backpack rows.
                    change_prefix = f'R{ri + 1}C{ci + 1}' if backpack else cp
                    _separate_field(choice, 'bgImage', f'{change_prefix}_Change', seen, assets)
                addons = choice.get('addons')
                if not isinstance(addons, list):
                    continue
                for ai, addon in enumerate(addons):
                    if not isinstance(addon, dict):
                        continue
                    ap = f'{cp}A{ai + 1}'
                    _separate_field(addon, 'image', ap, seen, assets)
                    if addon.get('changeBgImage'):
                        change_prefix = f'R{ri + 1}C{ci + 1}A{ai + 1}' if backpack else ap
                        _separate_field(addon, 'bgImage', f'{change_prefix}_Change', seen, assets)

    process_rows(temp.get('rows'), backpack=False)
    process_rows(temp.get('backpack'), backpack=True)

    row_groups = temp.get('rowDesignGroups')
    if isinstance(row_groups, list):
        for i, group in enumerate(row_groups):
            if not isinstance(group, dict) or not isinstance(group.get('styling'), dict):
                continue
            styling = group['styling']
            for key, suffix in (
                ('rowBackgroundImage', 'RBg'), ('objectBackgroundImage', 'OBg'),
                ('addonBackgroundImage', 'ABg'), ('rowBorderImage', 'RB'),
                ('objectBorderImage', 'OB'), ('addonBorderImage', 'AB'),
            ):
                _separate_field(styling, key, f'RD{i + 1}_{suffix}', seen, assets)

    object_groups = temp.get('objectDesignGroups')
    if isinstance(object_groups, list):
        for i, group in enumerate(object_groups):
            if not isinstance(group, dict) or not isinstance(group.get('styling'), dict):
                continue
            styling = group['styling']
            for key, suffix in (
                ('objectBackgroundImage', 'OBg'), ('addonBackgroundImage', 'ABg'),
                ('objectBorderImage', 'OB'), ('addonBorderImage', 'AB'),
            ):
                _separate_field(styling, key, f'OD{i + 1}_{suffix}', seen, assets)

    viewer_image_separation(temp, seen=seen, assets=assets)
    return temp, assets


def _fill_creator_load_defaults(project: dict[str, Any]) -> dict[str, Any]:
    """Apply load-time defaults that materially change Creator Save-to-Disk output.

    This intentionally stays narrow. It mirrors defaults proven by the pinned
    2.10.7 initializeApp path and the external Creator round-trip fixture rather
    than inventing a second full project migrator.
    """
    default_addon_justify = project.get('defaultAddonJustify')
    if not isinstance(default_addon_justify, str) or not default_addon_justify:
        default_addon_justify = 'start'
    for key in ('rows', 'backpack'):
        rows = project.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            objects = row.get('objects')
            if not isinstance(objects, list):
                continue
            for choice in objects:
                if isinstance(choice, dict) and not choice.get('addonJustify'):
                    choice['addonJustify'] = default_addon_justify
    return project


def creator_save_payload(project: dict[str, Any], *, target_version: str = ICCPLUS_VERSION) -> dict[str, Any]:
    """Mirror loading a project in Creator 2.10.7 and then Save to Disk.

    The Creator removes null/empty object values on file import, runs its load
    initialization, updates ``activated`` from the live Build Form state, then
    writes compact JSON. For a static file with no active build, JavaScript's
    ``''.split(',')`` produces ``['']``. Non-empty activated arrays are retained
    because reconstructing a live browser state from stale project flags would
    be less faithful than preserving the explicit native build entries.
    """
    temp = _remove_nulls(copy.deepcopy(project))
    if not isinstance(temp, dict):
        raise ValueError('project became empty after Creator import normalization')
    _fill_creator_load_defaults(temp)
    activated = temp.get('activated')
    if not isinstance(activated, list) or len(activated) == 0:
        temp['activated'] = ['']
    temp['version'] = target_version
    return temp


def creator_export_payload(project: dict[str, Any], *, separate_images: bool = True) -> tuple[dict[str, Any], dict[str, bytes]]:
    # exportZip/exportWithViewer start from the already initialized app, set the
    # current Build Form entries, then removeNulls before separating images. A
    # file-driven script must first reproduce the Creator's import normalization.
    temp = creator_save_payload(project)
    temp = _remove_nulls(temp)
    if not isinstance(temp, dict):
        raise ValueError('project became empty after removeNulls')
    if separate_images:
        return image_separation(temp)
    return temp, {}


def _zip_write_bytes(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def export_project_zip(project: dict[str, Any], output: str | Path) -> dict[str, Any]:
    """Create the Creator's 'Export Project with Separate Images' package."""
    temp, assets = creator_export_payload(project, separate_images=True)
    project_bytes = json_stringify(temp).encode('utf-8')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as zf:
        for path, data in assets.items():
            _zip_write_bytes(zf, path, data)
        _zip_write_bytes(zf, 'project.json', project_bytes)
    return {
        'output': str(output),
        'project_bytes': len(project_bytes),
        'image_count': len(assets),
        'images': list(assets),
        'icc_plus_version': ICCPLUS_VERSION,
        'content_parity': 'AppSaveLoad.svelte exportZip/imageSeparation',
        'zip_byte_parity': False,
    }


_LOADING_ALLOWED_TAGS = {'b', 'strong', 'i', 'em', 'u', 'span', 'br', 'div', 'p', 'small', 'sub', 'sup'}
_LOADING_DROP_CONTENT_TAGS = {'script', 'style', 'iframe', 'object', 'embed', 'svg', 'math'}


class _LoadingHTMLSanitizer(HTMLParser):
    """Small dependency-free sanitizer for Viewer loading text.

    ICC Plus uses DOMPurify before assigning loadingText through innerHTML.
    This fallback preserves a conservative formatting allowlist while dropping
    active/embedded content entirely.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.out: list[str] = []
        self.drop_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _LOADING_DROP_CONTENT_TAGS:
            self.drop_depth += 1
            return
        if self.drop_depth or tag not in _LOADING_ALLOWED_TAGS:
            return
        safe_attrs: list[str] = []
        for key, value in attrs:
            key = key.lower()
            # Keep only inert class metadata in the stdlib fallback. DOMPurify
            # handles a broader set when bleach is available.
            if key == 'class' and value is not None and tag in {'span', 'div', 'p'}:
                safe_attrs.append(f'class="{html.escape(value, quote=True)}"')
        suffix = (' ' + ' '.join(safe_attrs)) if safe_attrs else ''
        self.out.append(f'<{tag}{suffix}>')

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if not self.drop_depth and tag == 'br':
            self.out.append('<br>')

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _LOADING_DROP_CONTENT_TAGS:
            if self.drop_depth:
                self.drop_depth -= 1
            return
        if not self.drop_depth and tag in _LOADING_ALLOWED_TAGS and tag != 'br':
            self.out.append(f'</{tag}>')

    def handle_data(self, data: str) -> None:
        if not self.drop_depth:
            self.out.append(html.escape(data))

    def handle_entityref(self, name: str) -> None:
        if not self.drop_depth:
            self.out.append(f'&{name};')

    def handle_charref(self, name: str) -> None:
        if not self.drop_depth:
            self.out.append(f'&#{name};')


def _sanitize_loading_html(value: str) -> str:
    """Sanitize loading text with DOMPurify-like safe formatting semantics."""
    try:
        import bleach  # type: ignore
        return bleach.clean(
            value,
            tags=sorted(_LOADING_ALLOWED_TAGS),
            attributes={'span': ['class'], 'div': ['class'], 'p': ['class']},
            strip=True,
        )
    except Exception:
        parser = _LoadingHTMLSanitizer()
        parser.feed(value)
        parser.close()
        return ''.join(parser.out)


def _replace_tag_text(source: str, tag: str, element_id: str, value: str) -> str:
    pattern = re.compile(rf'(<{tag}\b[^>]*\bid=["\']{re.escape(element_id)}["\'][^>]*>)(.*?)(</{tag}>)', re.I | re.S)
    return pattern.sub(lambda m: m.group(1) + value + m.group(3), source, count=1)


def _replace_indicator(source: str, css_class: str, inner: str) -> str:
    pattern = re.compile(r'(<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bid=["\']indicator["\'][^>]*)(>)(.*?)(</(?P=tag)>)', re.I | re.S)
    match = pattern.search(source)
    if not match:
        return source
    start = match.group(1)
    if re.search(r'\bclass=["\'][^"\']*["\']', start, flags=re.I):
        start = re.sub(r'\bclass=["\'][^"\']*["\']', f'class="{html.escape(css_class, quote=True)}"', start, count=1, flags=re.I)
    else:
        start += f' class="{html.escape(css_class, quote=True)}"'
    replacement = start + '>' + inner + match.group(5)
    return source[:match.start()] + replacement + source[match.end():]


def _inject_head_links(source: str, viewer: dict[str, Any], project: dict[str, Any]) -> str:
    links: list[str] = []
    favicon = viewer.get('favicon')
    if isinstance(favicon, str) and favicon:
        links.append(f'<link rel="icon" href="{html.escape(favicon, quote=True)}">')
    for font in project.get('googleFonts', []) if isinstance(project.get('googleFonts'), list) else []:
        if not isinstance(font, str):
            continue
        font_id = font.replace(' ', '+')
        links.append(f'<link id="{html.escape(font_id, quote=True)}" rel="stylesheet" href="https://fonts.googleapis.com/css2?family={html.escape(font_id, quote=True)}&display=swap" crossorigin="anonymous">')
    for url in project.get('customFonts', []) if isinstance(project.get('customFonts'), list) else []:
        if isinstance(url, str):
            esc = html.escape(url, quote=True)
            links.append(f'<link id="{esc}" rel="stylesheet" href="{esc}" crossorigin="anonymous">')
    if not links:
        return source
    return re.sub(r'</head\s*>', '\n' + '\n'.join(links) + '\n</head>', source, count=1, flags=re.I)


def _rewrite_loading_css(css: str, viewer: dict[str, Any]) -> str:
    bg_image = viewer.get('loadingBgImage', '')
    bg_img = 'none' if bg_image == '' else f'url("../{bg_image}")'
    root = ":root {\n" + '\n'.join([
        f"    --bg: {viewer.get('loadingBgColor', '')};",
        f"    --bgImg: {bg_img};",
        f"    --track: {viewer.get('loadingTrackColor', '')};",
        f"    --shadow: {viewer.get('loadingTextShadow', '')};",
        f"    --color: {viewer.get('loadingTextColor', '')};",
        f"    --circle: {viewer.get('loadingCircleColor', '')};",
        f"    --font: {viewer.get('loadingTextFont', '')};",
    ]) + "\n}"
    return re.sub(r':root\s*\{[\s\S]*?\}', root, css, count=1)


def build_viewer_package(project: dict[str, Any], template_zip: str | Path, output: str | Path, *, mode: str | None = None, separate_images: bool | None = None) -> dict[str, Any]:
    """Reproduce Creator exportWithViewer using an official viewer template ZIP.

    The official template is an explicit input so its version can be pinned.
    Project/image transformations follow 2.10.7 source. HTML formatting and
    loading-text sanitization are semantic rather than byte-identical to the
    browser's DOMPurify + js-beautify pass.
    """
    base = _remove_nulls(creator_save_payload(project))
    if not isinstance(base, dict):
        raise ValueError('invalid project')
    viewer = base.get('viewerConfig') if isinstance(base.get('viewerConfig'), dict) else {}
    if mode is None:
        mode = 'local' if viewer.get('useLocalViewer') else 'web'
    if mode not in {'web','local'}:
        raise ValueError('mode must be web or local')
    if separate_images is None:
        separate_images = bool(viewer.get('useSeparateImages'))
    if separate_images:
        temp, assets = image_separation(base)
    else:
        base['version'] = ICCPLUS_VERSION
        temp, assets = viewer_image_separation(base)
    viewer = temp.get('viewerConfig') if isinstance(temp.get('viewerConfig'), dict) else {}
    save_data = json_stringify(temp)
    save_bytes = save_data.encode('utf-8')

    template_zip = Path(template_zip)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(template_zip, 'r') as src:
        names = set(src.namelist())
        if 'index.html' not in names or 'css/loading.css' not in names:
            raise ValueError('viewer template must contain index.html and css/loading.css')
        if mode == 'local' and 'js/app.js' not in names:
            raise ValueError('local viewer template must contain js/app.js')
        entries = {name: src.read(name) for name in src.namelist() if not name.endswith('/')}

    html_text = entries['index.html'].decode('utf-8')
    css_text = entries['css/loading.css'].decode('utf-8')
    title = str(viewer.get('title', ''))
    html_text = re.sub(r'<title\b[^>]*>.*?</title>', f'<title>{html.escape(title)}</title>', html_text, count=1, flags=re.I | re.S)
    html_text = _replace_tag_text(html_text, 'span', 'projectSize', str(len(save_bytes)))
    # Some templates use a div or another element for projectSize.
    if 'projectSize' in html_text and str(len(save_bytes)) not in html_text:
        html_text = re.sub(r'(<[A-Za-z0-9]+\b[^>]*\bid=["\']projectSize["\'][^>]*>).*?(</[A-Za-z0-9]+>)', lambda m: m.group(1)+str(len(save_bytes))+m.group(2), html_text, count=1, flags=re.I|re.S)
    loading_text = _sanitize_loading_html(str(viewer.get('loadingText', '')))
    html_text = _replace_indicator(html_text, str(viewer.get('loadingType', '')), f'<div>{loading_text}</div>')
    html_text = _inject_head_links(html_text, viewer, temp)
    css_text = _rewrite_loading_css(css_text, viewer)
    entries['index.html'] = html_text.encode('utf-8')
    entries['css/loading.css'] = css_text.encode('utf-8')

    if mode == 'local':
        js = entries['js/app.js'].decode('utf-8')
        pattern = re.compile(r'(\n/\*![\s\S]*?Delete and replace[\s\S]*?\*/\n)(\{[\s\S]*?\})(\n/\*! End \*/)', re.S)
        js, count = pattern.subn(lambda m: m.group(1) + save_data + m.group(3), js, count=1)
        if count != 1:
            raise ValueError('local viewer template does not contain the ICC Plus project replacement marker')
        entries['js/app.js'] = js.encode('utf-8')
        entries.pop('project.json', None)
    else:
        entries['project.json'] = save_bytes

    entries.update(assets)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as zf:
        for name, data in entries.items():
            _zip_write_bytes(zf, name, data)
    return {
        'output': str(output),
        'mode': mode,
        'separate_images': bool(separate_images),
        'project_bytes': len(save_bytes),
        'image_count': len(assets),
        'icc_plus_version': ICCPLUS_VERSION,
        'template': str(template_zip),
        'content_parity': '2.10.7 exportWithViewer project/image/local-embed logic',
        'html_byte_parity': False,
        'html_note': 'HTML keeps template formatting; loading sanitization is conservative rather than DOMPurify byte parity.',
    }
