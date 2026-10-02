from __future__ import annotations

"""Generate isolated ICC Plus 2.10.7 Viewer omission verification artifacts.

Ordinary omission cases contain a Creator-complete baseline and a candidate
that differs by one omission under test. Import-cleanup cases deliberately put
the null/empty member under test in the baseline and use the cleaned project as
the valid control. The suite is browser-facing: unknown cases must not be
promoted into the default sparse serializer until the pinned Viewer has shown
equivalent behavior.
"""

import copy
import json
from pathlib import Path
from typing import Any

from .editor import make_entity
from .upstream_2106 import ICCPLUS_COMMIT, ICCPLUS_VERSION, default_export_project, json_stringify
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

ROW_PRIVATE_FLAGS = (
    'privateFilterIsOn',
    'privateTextIsOn',
    'privateObjectImageIsOn',
    'privateObjectIsOn',
    'privateRowImageIsOn',
    'privateRowIsOn',
    'privateAddonImageIsOn',
    'privateAddonIsOn',
    'privateBackgroundIsOn',
    'privateMultiChoiceIsOn',
)

CHOICE_PRIVATE_FLAGS = (
    'privateFilterIsOn',
    'privateTextIsOn',
    'privateObjectImageIsOn',
    'privateObjectIsOn',
    'privateAddonImageIsOn',
    'privateAddonIsOn',
    'privateBackgroundIsOn',
    'privateMultiChoiceIsOn',
)


def _base_project() -> dict[str, Any]:
    project = default_export_project()
    row = make_entity(project, 'row', {'id': 'probe-row', 'title': 'Omission Probe Row'})
    project['rows'].append(row)
    choice = make_entity(project, 'choice', {'id': 'probe-choice', 'title': 'Omission Probe Choice', 'text': 'Compare this card visually and interactively.'})
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


def omission_probe_cases() -> list[dict[str, Any]]:
    """Return isolated baseline/candidate pairs for every unresolved omission."""
    cases: list[dict[str, Any]] = []

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

    return cases


def _readme(case_count: int) -> str:
    return f"""# ICC Plus 2.10.7 omission verification kit

This directory contains {case_count} isolated browser-verification cases generated against ICC Plus {ICCPLUS_VERSION} commit `{ICCPLUS_COMMIT}`.

For ordinary omission cases, load `baseline.json` and `candidate.json` separately in the pinned Viewer and compare load success, visible layout/text/style, selection behavior, counters/scores, and browser console errors. For `remove-nulls-array-filtering` cases, the baseline deliberately contains the pre-import null/empty array member and the candidate is the cleaned control; compare the post-load result and console behavior.

A candidate may be promoted into the default sparse serializer only when its behavior is indistinguishable from the baseline/control for the behavior the omitted field controls. Load success alone is not sufficient.

The `behavior-change-likely` case is deliberately included as a negative control. It should remain explicit unless testing proves the source-derived mismatch irrelevant.
"""


def write_omission_probe_suite(output: str | Path) -> dict[str, Any]:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    cases = omission_probe_cases()
    manifest_cases: list[dict[str, Any]] = []

    for case in cases:
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

    manifest = {
        'format': 'iccplus-omission-verification-kit',
        'format_version': 1,
        'target': {'icc_plus_version': ICCPLUS_VERSION, 'source_commit': ICCPLUS_COMMIT},
        'case_count': len(manifest_cases),
        'promotion_rule': 'Only promote an omission after pinned-Viewer behavior matches the baseline/control; load success alone is insufficient.',
        'cases': manifest_cases,
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (output / 'README.md').write_text(_readme(len(cases)), encoding='utf-8')
    return manifest


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='Generate ICC Plus 2.10.7 sparse-omission Viewer verification artifacts.')
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args(argv)
    manifest = write_omission_probe_suite(args.output)
    print(json.dumps({'ok': True, 'output': str(Path(args.output)), 'case_count': manifest['case_count']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
