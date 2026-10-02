from __future__ import annotations

"""Generate isolated ICC Plus 2.10.7 Viewer omission verification artifacts.

Ordinary omission cases contain a Creator-complete baseline and a candidate
that differs by one omission under test. Import-cleanup cases deliberately put
the null/empty member under test in the baseline and use the cleaned project as
the valid control. Unknown cases are browser-facing and must not be promoted
into the default sparse serializer until the pinned Viewer proves equivalent
behavior.
"""

import copy
import json
from pathlib import Path
from typing import Any

from .editor import make_entity
from .sparse_project import PRIVATE_FILTER_DEFAULTS, RETAINED_STYLING_DEFAULTS
from .upstream_2106 import (
    ADDON_IMAGE_STYLING,
    ADDON_STYLING,
    BACKGROUND_STYLING,
    DEFAULT_APP,
    FILTER_STYLING,
    ICCPLUS_COMMIT,
    ICCPLUS_VERSION,
    MULTI_CHOICE_STYLING,
    OBJECT_IMAGE_STYLING,
    OBJECT_STYLING,
    ROW_IMAGE_STYLING,
    ROW_STYLING,
    TEXT_STYLING,
    default_export_project,
    json_stringify,
)
from .validation import validate_complete


PRIVATE_FLAG_STYLES: dict[str, dict[str, Any]] = {
    'privateFilterIsOn': {'selFilterBlurIsOn': True, 'selFilterBlur': 2},
    'privateTextIsOn': {'customObjectTitle': True, 'objectTitle': 'Arial'},
    'privateObjectImageIsOn': {'objectImgBorderIsOn': True, 'objectImgBorderWidth': 7},
    'privateObjectIsOn': {'objectBorderIsOn': True, 'objectBorderWidth': 7},
    'privateRowImageIsOn': {'rowImgBorderIsOn': True, 'rowImgBorderWidth': 7},
    'privateRowIsOn': {'rowBorderIsOn': True, 'rowBorderWidth': 7},
    'privateAddonImageIsOn': {'useAddonImage': True, 'addonImgBorderIsOn': True, 'addonImgBorderWidth': 7},
    'privateAddonIsOn': {'useAddonDesign': True, 'addonBorderIsOn': True, 'addonBorderWidth': 7},
    'privateBackgroundIsOn': {'objectBgColorIsOn': True, 'objectBgColor': '#123456FF'},
    'privateMultiChoiceIsOn': {'customMultiTextFont': True, 'multiChoiceTextFont': 'Arial'},
}

PRIVATE_STYLE_FAMILIES: tuple[tuple[str, dict[str, Any], tuple[str, ...]], ...] = (
    ('privateFilterIsOn', FILTER_STYLING, ('row', 'choice')),
    ('privateTextIsOn', TEXT_STYLING, ('row', 'choice')),
    ('privateObjectImageIsOn', OBJECT_IMAGE_STYLING, ('row', 'choice')),
    ('privateObjectIsOn', OBJECT_STYLING, ('row', 'choice')),
    ('privateRowImageIsOn', ROW_IMAGE_STYLING, ('row',)),
    ('privateRowIsOn', ROW_STYLING, ('row',)),
    ('privateAddonImageIsOn', ADDON_IMAGE_STYLING, ('row', 'choice')),
    ('privateAddonIsOn', ADDON_STYLING, ('row', 'choice')),
    ('privateBackgroundIsOn', BACKGROUND_STYLING, ('row', 'choice')),
    ('privateMultiChoiceIsOn', MULTI_CHOICE_STYLING, ('row', 'choice')),
)

ROW_PRIVATE_FLAGS = tuple(flag for flag, _, scopes in PRIVATE_STYLE_FAMILIES if 'row' in scopes)
CHOICE_PRIVATE_FLAGS = tuple(flag for flag, _, scopes in PRIVATE_STYLE_FAMILIES if 'choice' in scopes)

# Alternate visible style anchors keep a private style family active while the
# target member is removed. Options are ordered and the first option that does
# not contain the target key is used.
PRIVATE_STYLE_ANCHORS: dict[str, tuple[dict[str, Any], ...]] = {
    'privateFilterIsOn': (
        {'selFilterBlurIsOn': True, 'selFilterBlur': 2},
        {'selBorderColorIsOn': True, 'selFilterBorderColor': '#123456FF'},
    ),
    'privateTextIsOn': (
        {'customObjectTitle': True, 'objectTitle': 'Arial'},
        {'customObjectText': True, 'objectText': 'Arial'},
        {'objectTitleTextSize': 177},
    ),
    'privateObjectImageIsOn': (
        {'objectImgBorderIsOn': True, 'objectImgBorderWidth': 7},
        {'objectImageWidth': 73},
    ),
    'privateObjectIsOn': (
        {'objectBorderIsOn': True, 'objectBorderWidth': 7},
        {'objectMargin': 23},
    ),
    'privateRowImageIsOn': (
        {'rowImgBorderIsOn': True, 'rowImgBorderWidth': 7},
        {'rowImageWidth': 73},
    ),
    'privateRowIsOn': (
        {'rowBorderIsOn': True, 'rowBorderWidth': 7},
        {'rowMargin': 23},
    ),
    'privateAddonImageIsOn': (
        {'useAddonImage': True, 'addonImgBorderIsOn': True, 'addonImgBorderWidth': 7},
        {'addonImageWidth': 73},
    ),
    'privateAddonIsOn': (
        {'useAddonDesign': True, 'addonBorderIsOn': True, 'addonBorderWidth': 7},
        {'addonMargin': 23},
    ),
    'privateBackgroundIsOn': (
        {'objectBgColorIsOn': True, 'objectBgColor': '#123456FF'},
        {'rowBgColorIsOn': True, 'rowBgColor': '#234567FF'},
    ),
    'privateMultiChoiceIsOn': (
        {'customMultiTextFont': True, 'multiChoiceTextFont': 'Arial'},
        {'multiChoiceCounterSize': 199},
    ),
}


def _base_project() -> dict[str, Any]:
    project = default_export_project()
    row = make_entity(project, 'row', {'id': 'probe-row', 'title': 'Omission Probe Row'})
    project['rows'].append(row)
    choice = make_entity(
        project,
        'choice',
        {'id': 'probe-choice', 'title': 'Omission Probe Choice', 'text': 'Compare this card visually and interactively.'},
    )
    row['objects'].append(choice)
    report = validate_complete(project)
    if report.get('valid') is not True:
        raise ValueError('internal omission-probe baseline is not Creator-complete')
    return project


def _case(
    case_id: str,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    path: str,
    category: str,
    note: str,
    expected: str = 'unknown',
) -> dict[str, Any]:
    return {
        'id': case_id,
        'category': category,
        'path': path,
        'expected': expected,
        'note': note,
        'baseline': baseline,
        'candidate': candidate,
    }


def _private_anchor(flag: str, target_key: str) -> dict[str, Any]:
    for option in PRIVATE_STYLE_ANCHORS[flag]:
        if target_key not in option:
            return copy.deepcopy(option)
    raise ValueError(f'no independent private-style anchor for {flag}.{target_key}')


def _add_core_cases(cases: list[dict[str, Any]]) -> None:
    viewer_defaults = default_export_project()['viewerConfig']
    for key in viewer_defaults:
        baseline = _base_project()
        anchor = 'loadingText' if key == 'title' else 'title'
        baseline['viewerConfig'][anchor] = 'OMISSION PROBE CUSTOM VALUE'
        candidate = copy.deepcopy(baseline)
        candidate['viewerConfig'].pop(key, None)
        cases.append(_case(
            f'viewer-config-{key}',
            baseline,
            candidate,
            path=f'/viewerConfig/{key}',
            category='custom-viewer-config-member',
            note='Whole stock viewerConfig omission is proven safe, but individual members of a retained custom object are not.',
        ))

    for scope, flags in (('row', ROW_PRIVATE_FLAGS), ('choice', CHOICE_PRIVATE_FLAGS)):
        for flag in flags:
            baseline = _base_project()
            entity = baseline['rows'][0] if scope == 'row' else baseline['rows'][0]['objects'][0]
            entity['isPrivateStyling'] = True
            entity[flag] = True
            entity['styling'] = copy.deepcopy(PRIVATE_FLAG_STYLES[flag])
            candidate = copy.deepcopy(baseline)
            target = candidate['rows'][0] if scope == 'row' else candidate['rows'][0]['objects'][0]
            target.pop(flag, None)
            cases.append(_case(
                f'{scope}-{flag}',
                baseline,
                candidate,
                path=f'/rows/0' + ('' if scope == 'row' else '/objects/0') + f'/{flag}',
                category='private-style-enable-inference',
                note='Verify that omitting the explicit enable flag leaves the same private-style source, rendering, and interaction behavior.',
            ))

    baseline = _base_project()
    choice = baseline['rows'][0]['objects'][0]
    choice['isPrivateStyling'] = True
    choice['privateFilterIsOn'] = True
    choice['styling'] = {'unselFilterSaturIsOn': True, 'unselFilterSatur': 1}
    candidate = copy.deepcopy(baseline)
    candidate['rows'][0]['objects'][0]['styling'].pop('unselFilterSatur')
    cases.append(_case(
        'private-filter-unsel-satur-one',
        baseline,
        candidate,
        path='/rows/0/objects/0/styling/unselFilterSatur',
        category='known-private-default-mismatch',
        expected='behavior-change-likely',
        note='Pinned global default is 1 while the private missing-field initializer is 0. Keep explicit 1 unless Viewer testing disproves the source-derived mismatch.',
    ))

    # mdObjects is a native string array. The dirty baseline deliberately adds
    # the null/empty-object entry that removeNulls is expected to discard, while
    # the candidate remains schema-valid with the same surviving string entry.
    for case_id, array_value, label in (
        ('array-null-entry', [None, 'probe-md'], 'null array member'),
        ('array-empty-object-entry', [{}, 'probe-md'], 'empty-object array member'),
    ):
        baseline = _base_project()
        baseline['mdObjects'] = copy.deepcopy(array_value)
        candidate = copy.deepcopy(baseline)
        candidate['mdObjects'].pop(0)
        cases.append(_case(
            case_id,
            baseline,
            candidate,
            path='/mdObjects/0',
            category='remove-nulls-array-filtering',
            note=f'Confirm that the Viewer import path filters a {label} from native mdObjects exactly as if it had been omitted before serialization.',
        ))


def _add_exhaustive_style_cases(cases: list[dict[str, Any]]) -> None:
    # A retained custom global styling object is not known to merge every missing
    # member with built-in styling. Probe each not-yet-proven member individually.
    stock_styling = DEFAULT_APP['styling']
    for key, value in stock_styling.items():
        if key in RETAINED_STYLING_DEFAULTS:
            continue
        baseline = _base_project()
        anchor_key = 'rowMargin' if key == 'objectMargin' else 'objectMargin'
        baseline['styling'][anchor_key] = 23
        baseline['styling'][key] = copy.deepcopy(value)
        candidate = copy.deepcopy(baseline)
        candidate['styling'].pop(key, None)
        cases.append(_case(
            f'global-styling-{key}',
            baseline,
            candidate,
            path=f'/styling/{key}',
            category='retained-global-styling-member',
            note='Verify whether this stock-valued member may be omitted from an otherwise custom global styling object without changing rendering.',
        ))

    # Private style objects may fall back to project/Design-Group styling, infer
    # local defaults, or leave a directly consumed value undefined. Probe every
    # family member whose omission is not already source-proven safe.
    for flag, defaults, scopes in PRIVATE_STYLE_FAMILIES:
        for key, value in defaults.items():
            if flag == 'privateFilterIsOn' and key in PRIVATE_FILTER_DEFAULTS:
                continue
            for scope in scopes:
                baseline = _base_project()
                entity = baseline['rows'][0] if scope == 'row' else baseline['rows'][0]['objects'][0]
                entity['isPrivateStyling'] = True
                entity[flag] = True
                entity['styling'] = {key: copy.deepcopy(value), **_private_anchor(flag, key)}
                candidate = copy.deepcopy(baseline)
                target = candidate['rows'][0] if scope == 'row' else candidate['rows'][0]['objects'][0]
                target['styling'].pop(key, None)
                cases.append(_case(
                    f'private-{scope}-{flag}-{key}',
                    baseline,
                    candidate,
                    path=f'/rows/0' + ('' if scope == 'row' else '/objects/0') + f'/styling/{key}',
                    category='private-style-member-fallback',
                    note='Verify whether this private stock-valued style member may be omitted while the private style family remains explicitly enabled.',
                ))

    # Creator Save-to-Disk represents an empty live build as [""], while the
    # built-in Viewer app begins with activated=[]. Whether omission is fully
    # equivalent for import/save behavior is worth pinning in the actual Viewer.
    baseline = _base_project()
    baseline['activated'] = ['']
    candidate = copy.deepcopy(baseline)
    candidate.pop('activated', None)
    cases.append(_case(
        'top-level-activated-empty-build',
        baseline,
        candidate,
        path='/activated',
        category='runtime-state-empty-build',
        note='Verify whether omitting Creator Save-to-Disk activated=[""] is behavior-equivalent to the pinned Viewer built-in empty activated state.',
    ))


def omission_probe_cases(*, exhaustive: bool = True) -> list[dict[str, Any]]:
    """Return one-omission-at-a-time Viewer verification cases.

    ``exhaustive=False`` returns the compact high-risk smoke set used by tests.
    The default includes the full global/private styling fallback matrix and is
    what the user-facing generator writes.
    """
    cases: list[dict[str, Any]] = []
    _add_core_cases(cases)
    if exhaustive:
        _add_exhaustive_style_cases(cases)
    return cases


def _readme(case_count: int) -> str:
    return f"""# ICC Plus 2.10.7 omission verification kit

This directory contains {case_count} isolated browser-verification cases generated against ICC Plus {ICCPLUS_VERSION} commit `{ICCPLUS_COMMIT}`.

The default generator includes individual retained-`viewerConfig` members, retained global-style members, private-style enable flags, private-style fallback members, import array cleanup, the empty `activated` state, and a known private-filter negative control. Fields already proven unsafe by direct Viewer consumption/schema behavior are not duplicated merely to make the kit larger.

For ordinary omission cases, load `baseline.json` and `candidate.json` separately in the pinned Viewer and compare load success, visible layout/text/style, selection behavior, counters/scores, save/reload behavior where relevant, and browser console errors. For `remove-nulls-array-filtering` cases, the baseline deliberately contains the pre-import null/empty array member and the candidate is the cleaned control; compare the post-load result and console behavior.

A candidate may be promoted into the default sparse serializer only when its behavior is indistinguishable from the baseline/control for the behavior the omitted field controls. Load success alone is not sufficient.

The `behavior-change-likely` case is deliberately included as a negative control. It should remain explicit unless testing proves the source-derived mismatch irrelevant.
"""


def write_omission_probe_suite(
    output: str | Path,
    *,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    selected = omission_probe_cases(exhaustive=True) if cases is None else cases
    manifest_cases: list[dict[str, Any]] = []

    for case in selected:
        case_dir = output / case['id']
        case_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = case_dir / 'baseline.json'
        candidate_path = case_dir / 'candidate.json'
        baseline_path.write_text(json_stringify(case['baseline']), encoding='utf-8')
        candidate_path.write_text(json_stringify(case['candidate']), encoding='utf-8')
        manifest_cases.append({k: v for k, v in case.items() if k not in {'baseline', 'candidate'}} | {
            'baseline_file': f"{case['id']}/baseline.json",
            'candidate_file': f"{case['id']}/candidate.json",
        })

    counts: dict[str, int] = {}
    for case in manifest_cases:
        counts[case['category']] = counts.get(case['category'], 0) + 1
    manifest = {
        'format': 'iccplus-omission-verification-kit',
        'format_version': 2,
        'target': {'icc_plus_version': ICCPLUS_VERSION, 'source_commit': ICCPLUS_COMMIT},
        'case_count': len(manifest_cases),
        'category_counts': dict(sorted(counts.items())),
        'promotion_rule': 'Only promote an omission after pinned-Viewer behavior matches the baseline/control; load success alone is insufficient.',
        'cases': manifest_cases,
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (output / 'README.md').write_text(_readme(len(selected)), encoding='utf-8')
    return manifest


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='Generate ICC Plus 2.10.7 sparse-omission Viewer verification artifacts.')
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args(argv)
    manifest = write_omission_probe_suite(args.output)
    print(json.dumps({
        'ok': True,
        'output': str(Path(args.output)),
        'case_count': manifest['case_count'],
        'category_counts': manifest['category_counts'],
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
