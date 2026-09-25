from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from iccplus_tools.editor import ProjectEditor, make_entity, rewrite_references
from iccplus_tools.field_catalog import FIELD_CATALOG
from iccplus_tools.field_types import FIELD_TYPE_CODES
from iccplus_tools.gui_parity import gui_parity_report
from iccplus_tools.live_parity import live_cases
from iccplus_tools.model import ProjectIndex
from iccplus_tools.simulator import Simulator
from iccplus_tools.upstream_2106 import default_project
from iccplus_tools.validation import validate
from iccplus_tools.version import __version__

OUT = ROOT / 'verification'
FIXTURES = OUT / 'fixtures'
EXPECTED = OUT / 'expected'

TOOL_ONLY_KEYS = {
    'creatorComponent', 'creatorComponents', 'componentTemplate', 'componentTemplates',
    'styleTemplate', 'styleTemplates', 'templateProvenance', '$iccplusLocal',
    '_iccplusLocal', '_creatorTemplate', '_component', '_templateSource',
}


def dump(path: Path, value: Any, *, pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    else:
        text = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    path.write_text(text, encoding='utf-8')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def neutral(code: str) -> Any:
    if code == 'b': return False
    if code == 'true': return True
    if code == 'false': return False
    if code == 'n': return 0
    if code == 'ns': return 0
    if code == 's': return ''
    if code in {'sa','na','ba','ssa','oa'}: return []
    if code == 'o': return {}
    raise ValueError(f'no neutral value for type code {code!r}')


def fill_fields(kind: str, base: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for field, code in FIELD_TYPE_CODES[kind].items():
        if field not in out:
            out[field] = neutral(code)
    return out


def field_retention_project() -> dict[str, Any]:
    p = default_project()
    # Keep real default top-level arrays/settings, then add every declared project field
    # that is not already present. This is a retention fixture, not a gameplay fixture.
    for field, code in FIELD_TYPE_CODES['project'].items():
        p.setdefault(field, neutral(code))

    point = fill_fields('point', make_entity(p, 'point', {'id':'field_point','name':'Field point','startingSum':5,'initValue':5}))
    variable = fill_fields('variable', make_entity(p, 'variable', {'id':'field_variable','name':'Field variable','isTrue':False}))
    word = fill_fields('word', make_entity(p, 'word', {'id':'field_word','name':'Field word','replaceText':'Field word value'}))
    group = fill_fields('group', make_entity(p, 'group', {'id':'field_group','name':'Field group','elements':[],'rowElements':[]}))
    rdesign = fill_fields('row_design_group', make_entity(p, 'row_design_group', {'id':'field_rdesign','name':'Field row design','elements':[]}))
    cdesign = fill_fields('choice_design_group', make_entity(p, 'choice_design_group', {'id':'field_cdesign','name':'Field choice design','elements':[]}))
    greq = fill_fields('global_requirement', make_entity(p, 'global_requirement', {'id':'field_greq','name':'Field global requirement','requireds':[]}))
    sfx = fill_fields('sound_effect', make_entity(p, 'sound_effect', {'id':'field_sfx','name':'Field SFX','audio':'','volume':1,'pitch':0,'requireds':[],'groups':[]}))
    cat = fill_fields('category', {'idx':0,'name':'Field category','type':'point'})

    req = fill_fields('requirement', make_entity(p, 'requirement', {}))
    req.update({'required':False,'type':'id','reqId':'field_choice','id':'','requireds':[],'orRequired':[],'orRequireds':[],'more':[]})
    score = fill_fields('score', make_entity(p, 'score', {'id':'field_point','value':0,'requireds':[]}))
    score.update({'id':'field_point','requireds':[],'discounts':[]})

    addon = fill_fields('addon', make_entity(p, 'addon', {'title':'Field addon'}, parent='field_choice'))
    addon.update({'id':'','parentId':'field_choice','isSelectable':False,'requireds':[]})
    saddon = fill_fields('selectable_addon', make_entity(p, 'selectable_addon', {'title':'Field selectable addon'}, parent='field_choice'))
    saddon.update({'id':'field_saddon','parentId':'field_choice','isSelectable':True,'requireds':[],'scores':[],'groups':[]})

    choice = fill_fields('choice', make_entity(p, 'choice', {'id':'field_choice','title':'Field choice','text':'Field retention object'}))
    choice.update({
        'id':'field_choice','index':0,'title':'Field choice','text':'Field retention object',
        'requireds':[req],'scores':[score],'addons':[addon,saddon],
        'groups':['field_group'],'objectDesignGroups':['field_cdesign'],
        'isActive':False,'linkedObjects':[], 'activatedRandom':[], 'activatedRandomMul':[],
    })
    row = fill_fields('row', make_entity(p, 'row', {'id':'field_row','title':'Field row','titleText':'Every Row field is present here.'}))
    row.update({
        'id':'field_row','index':0,'title':'Field row','titleText':'Every Row field is present here.',
        'objects':[choice], 'requireds':[], 'groups':['field_group'], 'rowDesignGroups':['field_rdesign'],
        'currentChoices':0,
    })
    backpack_row = fill_fields('backpack_row', make_entity(p, 'backpack_row', {'id':'field_backpack','title':'Field backpack'}))
    backpack_row.update({'id':'field_backpack','index':0,'objects':[],'requireds':[],'groups':[],'rowDesignGroups':[],'isBackpack':True,'currentChoices':0})

    rdesign['styling'] = {k: neutral(FIELD_TYPE_CODES['styling'][k]) for k in FIELD_CATALOG['styling']}
    cdesign['styling'] = {k: neutral(FIELD_TYPE_CODES['styling'][k]) for k in FIELD_CATALOG['styling']}
    p['rows'] = [row]
    p['backpack'] = [backpack_row]
    p['pointTypes'] = [point]
    p['variables'] = [variable]
    p['words'] = [word]
    p['groups'] = [group]
    p['rowDesignGroups'] = [rdesign]
    p['objectDesignGroups'] = [cdesign]
    p['globalRequirements'] = [greq]
    p['soundEffects'] = [sfx]
    p['categories'] = [cat]
    p['activated'] = []
    p['viewerConfig'] = fill_fields('viewer_config', p.get('viewerConfig', {}))
    p['styling'] = {k: p.get('styling', {}).get(k, neutral(FIELD_TYPE_CODES['styling'][k])) for k in FIELD_CATALOG['styling']}
    return p


def _collect_identity_ids(project: dict[str, Any]) -> list[str]:
    idx = ProjectIndex(project)
    order = [
        'row','backpack_row','choice','selectable_addon','point','variable','word','group',
        'global_requirement','row_design_group','choice_design_group','sound_effect','score',
    ]
    values: list[str] = []
    for kind in order:
        for ent in idx.by_kind.get(kind, []):
            ident = str(ent.value.get('idx' if kind == 'score' else 'id', ''))
            if ident and ident not in values:
                values.append(ident)
    return values


def _namespace_project(project: dict[str, Any], prefix: str) -> tuple[dict[str, Any], dict[str, str]]:
    p = copy.deepcopy(project)
    mapping: dict[str, str] = {}
    # Rename through the editor because it knows ICC Plus reference fields.
    for old in _collect_identity_ids(p):
        if old in mapping:
            continue
        new = f'{prefix}__{old}'
        try:
            ProjectEditor(p).rename(old, new, normalize=False)
            mapping[old] = new
        except ValueError:
            # Structural score IDs or intentionally blank/ambiguous runtime fields do not
            # need to be exposed to the external action script. Keep them as-is.
            pass
    ProjectEditor(p).normalize()
    return p, mapping


def _runtime_snapshot(sim: Simulator, test: dict[str, Any]) -> dict[str, Any]:
    prefix = test['prefix'] + '__'
    expected = {
        'entities': {e.id:{'active':sim._active(e.id),'multiple':sim._count(e.id)} for e in sim.index.selectables() if e.id.startswith(prefix)},
        'points': {k:float(v) for k,v in sorted(sim.state.points.items()) if k.startswith(prefix)},
        'variables': {k:v for k,v in sorted(sim.state.variables.items()) if k.startswith(prefix)},
        'words': {k:v for k,v in sorted(sim.state.words.items()) if k.startswith(prefix)},
        'rows': {e.id:{'currentChoices':int(sim.state.row_counts.get(e.id,0)),'allowedChoices':int(sim._row_allowed(e))} for e in sim.index.by_kind.get('row',[]) if e.id.startswith(prefix)},
        'requirements': {},
        'build_string': sim.export_build_string(),
    }
    for ident in test['check_requirements']:
        ent = sim.index.one(ident,'choice') or sim.index.one(ident,'selectable_addon')
        if ent is not None:
            expected['requirements'][ident] = sim.req.evaluate(ent.value.get('requireds',[]),sim.state)[0]
    return expected


def _apply_runtime_action(sim: Simulator, action: dict[str, Any]) -> None:
    if action['op'] == 'select':
        sim.select(str(action['id']))
    elif action['op'] == 'deselect':
        sim.deselect(str(action['id']))
    elif action['op'] == 'set_point':
        sim.state.points[str(action['id'])] = float(action['value'])
    elif action['op'] == 'row_button':
        sim.press_row_button(str(action['id']))
    elif action['op'] == 'reset':
        sim.reset()
    else:
        raise ValueError(action)


def _flatten_runtime(value: Any, prefix: str = '') -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            path = f'{prefix}.{key}' if prefix else str(key)
            out.update(_flatten_runtime(item, path))
    else:
        out[prefix] = value
    return out


def _changed_runtime_paths(before: dict[str, Any], after: dict[str, Any], action: dict[str, Any]) -> list[str]:
    a = _flatten_runtime(before)
    b = _flatten_runtime(after)
    changed = sorted(path for path, value in b.items() if a.get(path, object()) != value)
    if changed:
        return changed
    ident = str(action.get('id', ''))
    fallbacks = [f'entities.{ident}.active', f'entities.{ident}.multiple', f'points.{ident}', f'rows.{ident}.currentChoices']
    return [path for path in fallbacks if path in b] or ['build_string']


def _runtime_expectations(project: dict[str, Any], test: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[list[str]]]:
    sim = Simulator(copy.deepcopy(project), clean=False)
    previous = _runtime_snapshot(sim, test)
    steps: list[dict[str, Any]] = []
    required: list[list[str]] = []
    for action in test['actions']:
        _apply_runtime_action(sim, action)
        current = _runtime_snapshot(sim, test)
        steps.append(current)
        required.append(_changed_runtime_paths(previous, current, action))
        previous = current
    return _runtime_snapshot(sim, test), steps, required


def _merge_runtime_cases() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    base = default_project()
    base['rows'] = []
    base['backpack'] = [copy.deepcopy(default_project()['backpack'][0])]
    for key in ('pointTypes','variables','words','groups','rowDesignGroups','objectDesignGroups','globalRequirements','soundEffects','categories'):
        base[key] = []
    base['activated'] = []
    tests: list[dict[str, Any]] = []
    isolated: dict[str, dict[str, Any]] = {}

    for n, case in enumerate(live_cases(), 1):
        ident = f'R{n:02d}'
        prefix = f't{n:02d}'
        p, mapping = _namespace_project(case['project'], prefix)
        ProjectEditor(p).normalize()
        mapped_actions = []
        for action in case.get('actions', []):
            item = copy.deepcopy(action)
            if 'id' in item:
                item['id'] = mapping.get(str(item['id']), str(item['id']))
            mapped_actions.append(item)
        mapped_checks = [mapping.get(str(x), str(x)) for x in case.get('check_requirements', [])]
        # R32 originally dirties a Point directly inside the differential harness.
        # The official Viewer needs a normal GUI action, so the external fixture
        # adds a native fixed-value random-Point Row button that reaches the same
        # pre-reset value without browser internals.
        if ident == 'R32':
            point_id = mapping.get('p', 'p')
            helper_id = f'{prefix}__set_point_button'
            helper = make_entity(p, 'row', {
                'id': helper_id,
                'title': 'External test: set Point before reset',
                'titleText': 'Press once before Reset.',
                'isButtonRow': True,
                'buttonType': True,
                'buttonText': 'Set test Point',
                'btnPointAddon': True,
                'buttonTypeRadio': 'sumaddon',
                'pointTypeRandom': point_id,
                'randomMin': 92,
                'randomMax': 92,
                'objects': [],
            })
            helper['index'] = len(p.get('rows', []))
            p.setdefault('rows', []).append(helper)
            mapped_actions = [
                {'op': 'row_button', 'id': helper_id} if action.get('op') == 'set_point' else action
                for action in mapped_actions
            ]
            ProjectEditor(p).normalize()
        test = {
            'id': ident,
            'name': case['name'],
            'prefix': prefix,
            'fixture': f'fixtures/runtime_cases/{ident}.json',
            'actions': mapped_actions,
            'check_requirements': mapped_checks,
            'original_ids': mapping,
        }
        test['expected'], test['expected_after_actions'], test['required_after_actions'] = _runtime_expectations(p, test)
        tests.append(test)
        isolated[ident] = p

        for key in ('rows','pointTypes','variables','words','groups','rowDesignGroups','objectDesignGroups','globalRequirements','soundEffects','categories'):
            base[key].extend(copy.deepcopy(p.get(key, []) or []))

    for i, row in enumerate(base['rows']):
        if isinstance(row, dict):
            row['index'] = i
    ProjectEditor(base).normalize()
    return base, tests, isolated

def advanced_interaction_project() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    p = default_project()
    p['rows'] = []
    p['pointTypes'] = [
        {'id':'adv_budget','name':'Budget','startingSum':20,'initValue':20,'activatedId':'','beforeText':'','afterText':'','category':-1,'belowZeroNotAllowed':True},
        {'id':'adv_power','name':'Power','startingSum':4,'initValue':4,'activatedId':'','beforeText':'','afterText':'','category':-1},
    ]
    p['variables'] = [{'id':'adv_flag','name':'Flag','isTrue':False}]
    p['words'] = [{'id':'adv_name','name':'Name','replaceText':'Unset'}]
    p['groups'] = [{'id':'adv_group','name':'Advanced group','category':-1,'elements':['adv_target_a','adv_target_b'],'rowElements':[]}]
    p['globalRequirements'] = []
    p['soundEffects'] = [{'id':'adv_sfx','name':'Silent test SFX','audio':'','volume':1,'pitch':0,'isDefault':False,'onSelected':False,'onDeselected':False,'requireds':[],'groups':[]}]

    def c(i: str, title: str, **x: Any) -> dict[str, Any]:
        v = {'id':i,'index':0,'title':title,'text':'','debugTitle':'','image':'','template':1,'objectWidth':'','isActive':False,'multipleUseVariable':0,'requireds':[],'addons':[],'scores':[],'groups':[],'objectDesignGroups':[]}
        v.update(x); return v
    def r(i: str, title: str, objs: list[dict[str, Any]], **x: Any) -> dict[str, Any]:
        v={'id':i,'index':0,'title':title,'titleText':'','debugTitle':'','objectWidth':'col-md-3','image':'','template':1,'isButtonRow':False,'isResultRow':False,'resultGroupId':'','isInfoRow':False,'defaultAspectWidth':1,'defaultAspectHeight':1,'allowedChoices':0,'currentChoices':0,'requireds':[],'objects':objs,'rowDesignGroups':[]}
        v.update(x); return v

    rows: list[dict[str, Any]] = []
    rows.append(r('adv_row_targets','Targets',[
        c('adv_target_a','Target A',scores=[{'idx':'adv_s_a','id':'adv_budget','value':5,'requireds':[],'showScore':True}]),
        c('adv_target_b','Target B',scores=[{'idx':'adv_s_b','id':'adv_budget','value':5,'requireds':[],'showScore':True}]),
        c('adv_multi','Multi target',isSelectableMultiple=True,isMultipleUseVariable=True,numMultipleTimesMinus=0,numMultipleTimesPluss=4,
          scores=[{'idx':'adv_s_m','id':'adv_budget','value':2,'requireds':[],'showScore':True,'multiplyByTimes':True}]),
    ], allowedChoices=0))
    rows.append(r('adv_row_effects','Effects',[
        c('adv_discount','Discount combo',discountOther=True,isDisChoices=True,discountChoices=['adv_target_a','adv_multi'],discountPointTypes=['adv_budget'],discountOperator='2',discountValue=2,stackableDiscount=True,discountLowLimitIsOn=True,discountLowLimit=0,discountShow=True,useDiscountCount=True,countPerSelection=True,discountCount=2),
        c('adv_random','Random force',activateOtherChoice=True,activateThisChoice='adv_target_a,adv_target_b,adv_multi/ON#1',isActivateRandom=True,numActivateRandom=2),
        c('adv_visual','Template width visual',changeTemplates=True,changeTemplatesList=['adv_target_a','adv_target_b'],changeToThisTemplate=2,changeAddonTemplate=True,changeWidth=True,changeWidthList=['adv_target_a','adv_target_b'],changeToThisWidth='col-sm-6',changePointBar=True,changeBarBgColorIsOn=True,changedBarBgColor='#123456FF',changeBackground=True,changedBgColorCode='#334455FF'),
        c('adv_prompt','Prompt and upload',textfieldIsOn=True,customTextfieldIsOn=True,idOfTheTextfieldWord='adv_name',wordPromptText='Enter test name',isImageUpload=True,confirmIsOn=True),
        c('adv_audio','Audio delay transition',useSfx=True,sfxIdOnSelect='adv_sfx',sfxIdOnDeselect='adv_sfx',setBgmIsOn=True,bgmId='test_video_id',bgmFadeIn=True,bgmFadeInSec=0.1,bgmFadeOut=True,bgmFadeOutSec=0.1,isSelectDelayed=True,selectDelayTime=50,isDeselectDelayed=True,deselectDelayTime=50,isFadeTransition=True,fadeTransitionColor='#112233FF',fadeInTransitionTime=50,fadeOutTransitionTime=50),
    ]))
    rows.append(r('adv_row_dup_src','Duplicate source',[c('adv_dup_inner','Duplicated inner',groups=['adv_group'])]))
    rows.append(r('adv_row_dup_ctl','Duplicate controller',[
        c('adv_duplicate','Duplicate row',duplicateRow=True,duplicateRowId='adv_row_dup_src',duplicateRowPlace='adv_row_dup_ctl',dRowAddSufReq=True,dRowAddSufFunc=True),
        c('adv_var_point','Variable and point effects',isChangeVariables=True,changedVariables=['adv_flag'],changeType='1',multiplyPointtypeIsOn=True,pointTypeToMultiply=['adv_power'],multiplyWithThis=2,setPointtypeIsOn=True,pointTypeToSet=['adv_budget'],setWithThis='10'),
    ]))
    rows.append(r('adv_row_addon','Selectable addon parent',[
        c('adv_parent','Parent',deselectWhenNoAddon=True,addons=[{
            'id':'adv_addon','title':'Selectable addon','text':'','template':1,'addonWidth':'col-12','image':'','requireds':[],
            'parentId':'adv_parent','isSelectable':True,'scores':[{'idx':'adv_s_add','id':'adv_budget','value':1,'requireds':[],'showScore':True}],
            'groups':['adv_group'],'multipleUseVariable':0,'isActive':False,'deselectParent':True,'countAsChoice':True,
        }])
    ]))
    rows.append(r('adv_result','Result row',[],isResultRow=True,resultGroupId='adv_group',isInfoRow=True))
    rows.append(r('adv_button_var','Variable button',[],isButtonRow=True,buttonType=False,buttonId='adv_flag',buttonText='Toggle flag'))
    rows.append(r('adv_button_point','Random point button',[],isButtonRow=True,buttonType=True,btnPointAddon=True,buttonTypeRadio='sumaddon',pointTypeRandom='adv_power',randomMin=1,randomMax=3,buttonText='Random power'))
    rows.append(r('adv_button_choice','Weighted random choice',[
        c('adv_weight_light','Weighted light',randomWeight=1),
        c('adv_weight_heavy','Weighted heavy',randomWeight=9),
    ],isButtonRow=True,buttonType=True,buttonRandom=True,buttonRandomNumber=1,isWeightedRandom=True,onlyUnselectedChoices=True,buttonText='Random target'))

    for i,row in enumerate(rows):
        row['index']=i
        for j,obj in enumerate(row.get('objects',[])): obj['index']=j
    p['rows']=rows
    p['backpack']=[copy.deepcopy(default_project()['backpack'][0])]
    p['backpack'][0]['objects']=[c('adv_backpack_choice','Backpack choice',backpackBtnRequirement=True)]
    p['backpack'][0]['objects'][0]['index']=0
    p['customCSS']='.choice-adv_target_a { outline: 1px solid rgb(1, 2, 3); }'
    p['googleFonts']=['Roboto']
    p['viewerConfig']['title']='ICC Plus Local external verification'
    p['viewerConfig']['useSeparateImages']=True
    p['styling']['selFilterBgColor']='#55AA55FF'
    p['styling']['reqFilterOpacIsOn']=True
    p['styling']['reqFilterOpac']=40
    p['activated']=[]
    ProjectEditor(p).normalize()

    tests = [
        {'id':'A01','name':'discount plus multi-select plus score','reload':True,'steps':['Select adv_discount.','Select adv_target_a.','Select adv_multi twice.','Record Budget after each step, displayed discounted scores, active choices, and Build Form string.','Deselect in reverse order and record restoration.']},
        {'id':'A02','name':'random activation plus native build string','reload':True,'steps':['Select adv_random.','Record exactly which two targets activate and the Build Form string.','Copy the Build Form string. Reload the fixture. Import that string in Build Form.','Confirm the same random targets and repeat counts restore.','Deselect adv_random and confirm its random targets release.']},
        {'id':'A03','name':'template width background and point bar effects','reload':True,'steps':['Record templates, widths, project background and point bar colors for adv_target_a and adv_target_b.','Select adv_visual.','Record all changed values and a screenshot.','Deselect adv_visual and record whether each value restores.']},
        {'id':'A04','name':'text prompt image upload confirmation build restore','reload':True,'steps':['Select adv_prompt. Accept confirmation. Enter a comma-containing text value such as Alpha,Beta. Upload a small image.','Record the visible word substitution/image and Build Form string.','Reload and import the Build Form string.','Confirm text and uploaded image restore.']},
        {'id':'A05','name':'SFX BGM delay and fade','reload':True,'steps':['Select and deselect adv_audio.','Record whether select/deselect delay, fade transition, SFX trigger, and BGM state match the configured fields.','Record console/runtime errors if audio cannot play because the fixture intentionally uses a placeholder media ID.']},
        {'id':'A06','name':'row duplication and ID suffix behavior','reload':True,'steps':['Select adv_duplicate.','Record the inserted Row position, all generated Row/Choice IDs, group membership, and any rewritten function/Requirement references.','Deselect if the GUI supports reversal and record resulting Rows.']},
        {'id':'A07','name':'variable point transforms and reversal','reload':True,'steps':['Record Flag, Power and Budget.','Select adv_var_point. Record values.','Deselect it. Record values again.']},
        {'id':'A08','name':'selectable addon parent cleanup','reload':True,'steps':['Select adv_addon directly.','Confirm parent activates and addon score applies.','Deselect adv_addon.','Confirm deselectParent/deselectWhenNoAddon cleanup and score reversal.']},
        {'id':'A09','name':'result row group backpack search','reload':True,'steps':['Select adv_target_a and adv_target_b.','Open result row/view and confirm group-filtered entries.','Open Backpack and verify adv_backpack_choice behavior.','Use search to find searchable entries and record exclusions.']},
        {'id':'A10','name':'row button modes','reload':True,'steps':['Use adv_button_var twice and record Flag each time.','Use adv_button_point several times and record Power values remain within configured increments.','Use adv_button_choice after reloading several times and record weighted/random selection behavior and only-unselected handling.']},
        {'id':'A11','name':'styling inheritance and custom CSS','reload':True,'steps':['Record global selected/unmet styling and the custom CSS outline on adv_target_a.','Temporarily use Creator private styling/design-group controls on a copy of the fixture and record precedence global -> design group -> Row private -> Choice private.','Export the edited project and preserve it in returned artifacts.']},
        {'id':'A12','name':'separate images and playable viewer export','reload':True,'steps':['Set or upload at least one Row image, Choice image, favicon, and loading background.','Export Project with Separate Images.','Export Playable Web Package.','Return both ZIPs unchanged and record their file lists.']},
    ]
    required_artifacts = {'A03': 1, 'A11': 2, 'A12': 2}
    for test in tests:
        test['required_artifacts_min'] = required_artifacts.get(test['id'], 0)
    return p, tests



def field_coverage(project: dict[str, Any]) -> dict[str, Any]:
    row = project['rows'][0]
    choice = row['objects'][0]
    addon = choice['addons'][0]
    saddon = choice['addons'][1]
    score = choice['scores'][0]
    req = choice['requireds'][0]
    samples = {
        'project': project,
        'styling': project['styling'],
        'viewer_config': project['viewerConfig'],
        'defaults': project,
        'row': row,
        'backpack_row': project['backpack'][0],
        'choice': choice,
        'addon': addon,
        'selectable_addon': saddon,
        'score': score,
        'requirement': req,
        'point': project['pointTypes'][0],
        'variable': project['variables'][0],
        'word': project['words'][0],
        'group': project['groups'][0],
        'row_design_group': project['rowDesignGroups'][0],
        'choice_design_group': project['objectDesignGroups'][0],
        'global_requirement': project['globalRequirements'][0],
        'sound_effect': project['soundEffects'][0],
        'category': project['categories'][0],
    }
    report: dict[str, Any] = {}
    missing_total = 0
    for kind, fields in FIELD_CATALOG.items():
        if kind not in samples:
            continue
        present = set(samples[kind].keys())
        missing = [f for f in fields if f not in present]
        missing_total += len(missing)
        report[kind] = {
            'declared': len(fields),
            'present': len(fields) - len(missing),
            'missing': missing,
        }
    return {'ok': missing_total == 0, 'missing_total': missing_total, 'kinds': report}

def scan_tool_only_keys(value: Any, path: str = '') -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for k,v in value.items():
            here = f'{path}/{k}'
            if k in TOOL_ONLY_KEYS or k.startswith('$iccplus') or k.startswith('_iccplus'):
                hits.append(here)
            hits.extend(scan_tool_only_keys(v, here))
    elif isinstance(value, list):
        for i,v in enumerate(value): hits.extend(scan_tool_only_keys(v, f'{path}/{i}'))
    return hits


def build_manifest(runtime_tests: list[dict[str, Any]], advanced_tests: list[dict[str, Any]]) -> dict[str, Any]:
    gui = gui_parity_report()
    # Map every audited GUI feature to a concrete verification case. Keep this
    # explicit so a newly added parity feature cannot silently inherit a generic
    # catch-all test that never exercises it.
    test_map: dict[str, list[str]] = {
        'project.save_json': ['C01', 'C12'],
        'project.load_json': ['C01', 'C12'],
        'project.save_slots': ['C12'],
        'project.autosave': ['C12'],
        'project.project_stats': ['C11'],
        'project.defaults': ['C11'],
        'project.ids_from_titles': ['C08'],
        'project.viewer_config': ['C11', 'A12'],
        'project.global_styling': ['C07', 'A11'],
        'project.style_templates': ['C07'],
        'project.custom_css': ['C09', 'A11'],
        'project.fonts': ['C09'],
        'project.id_name_csv': ['C08'],
        'project.search_navigation': ['C11', 'A09'],
        'project.symbol_reference': ['C11'],
        'rows.create_edit_delete': ['C02', 'C04'],
        'backpack_rows.create_edit_delete': ['C10', 'A09'],
        'choices.create_edit_delete': ['C02', 'C04'],
        'addons.create_edit_delete': ['C02', 'C05', 'A08'],
        'scores.create_edit_delete': ['C02', 'C05', 'A01'],
        'requirements.create_edit_delete': ['C02', 'C05', 'R01-R32'],
        'points.create_edit_delete': ['C03', 'A07', 'A10'],
        'variables.create_edit_delete': ['C03', 'A07', 'A10'],
        'words.create_edit_delete': ['C03', 'A04'],
        'groups.create_edit_delete': ['C03', 'A09'],
        'row_design_groups.create_edit_delete': ['C03', 'C07', 'A11'],
        'choice_design_groups.create_edit_delete': ['C03', 'C07', 'A11'],
        'global_requirements.create_edit_delete': ['C03', 'R01-R32'],
        'sound_effects.create_edit_delete': ['C03', 'C09', 'A05'],
        'categories.create_rename_delete': ['C06'],
        'rows.drag_reorder': ['C02', 'C04'],
        'features.move_up_down': ['C03'],
        'choices.drag_reorder': ['C02', 'C04'],
        'nested.reorder': ['C02', 'C05'],
        'nested.move': ['C02', 'C05'],
        'copy_paste.deep_clone': ['C04', 'C05'],
        'fragment.export_import': ['C05'],
        'row_settings.sort_choices': ['C04'],
        'row_settings.copy_choices': ['C04'],
        'row_settings.copy_and_delete': ['C04'],
        'choice_settings.copy_to_row': ['C04'],
        'rich_text.result': ['C11', 'A09'],
        'images.assign_data_url_or_path': ['C11', 'A04', 'A12'],
        'styling.clean_all_private': ['C11', 'A11'],
        'styling.design_import_export': ['C07'],
        'images.compress_convert': ['C11', 'A12'],
        'images.interactive_crop': ['C11'],
        'export.separate_images_zip': ['C12', 'A12'],
        'export.playable_web_package': ['C12', 'A12'],
        'build.native_build_form_import_export': ['R01-R32', 'A02', 'A04'],
        'build.human_summary': ['A02', 'A04'],
        'viewer.row_buttons': ['A10', 'R32'],
        'viewer.download_rendered_image': ['A09'],
        'preview.audio_media_controls': ['A05'],
        'preview.browser_rendering': ['A03', 'A09', 'A11'],
        'browser.theme_and_dialog_state': ['C11'],
    }
    gui_ids = {item['feature'] for item in gui['features']}
    missing_map = sorted(gui_ids - test_map.keys())
    stale_map = sorted(test_map.keys() - gui_ids)
    if missing_map or stale_map:
        raise RuntimeError(f'GUI verification map out of sync: missing={missing_map}, stale={stale_map}')
    mappings = [
        {
            'feature': item['feature'],
            'status': item['status'],
            'tests': test_map[item['feature']],
            'source': item['source'],
        }
        for item in gui['features']
    ]
    return {
        'format':'iccplus-external-verification-manifest-v2',
        'tool_version':__version__,
        'target':gui['target'],
        'creator_template_boundary':{
            'rule':'Authoring templates, compact effects, presets, and verification metadata must compile to native ICC Plus fields. They are never inserted into project.json as tool-specific objects.',
            'forbidden_tool_keys':sorted(TOOL_ONLY_KEYS),
            'fixture_scan':'expected/template_boundary.json',
        },
        'fixtures':[
            {'id':'F01','file':'fixtures/01_field_retention.json','purpose':'Every declared native field is present at least once with a type-correct neutral or fixture value. Load and export without gameplay.'},
            {'id':'R01-R32','file':'fixtures/02_runtime_matrix.json','purpose':'Compact reference matrix only. Official runtime execution uses one isolated fixture per case under fixtures/runtime_cases/.','case_manifest':'expected/runtime_cases.json'},
            {'id':'A01-A12','file':'fixtures/03_advanced_interaction_export.json','purpose':'Browser-owned and high-interaction combinations that require the official GUI.','case_manifest':'expected/advanced_cases.json'},
        ],
        'creator_actions':mappings,
        'runtime_case_count':len(runtime_tests),
        'creator_case_count':12,
        'advanced_case_count':len(advanced_tests),
        'completion_rule':'Every audited GUI feature has an explicit test mapping. A pass/fail only counts when it records an official-GUI observation from the packaged fixture and hash. Browser-only features require a direct GUI observation or an explicit blocked result with evidence.',
    }


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    EXPECTED.mkdir(parents=True, exist_ok=True)

    field = field_retention_project()
    runtime, runtime_tests, isolated_runtime = _merge_runtime_cases()
    advanced, advanced_tests = advanced_interaction_project()

    runtime_dir = FIXTURES / 'runtime_cases'
    runtime_dir.mkdir(parents=True, exist_ok=True)
    for stale in runtime_dir.glob('R*.json'):
        stale.unlink()
    for test in runtime_tests:
        case_path = OUT / test['fixture']
        dump(case_path, isolated_runtime[test['id']])
        test['fixture_sha256'] = sha256(case_path)

    dump(FIXTURES/'01_field_retention.json', field)
    dump(FIXTURES/'02_runtime_matrix.json', runtime)
    dump(FIXTURES/'03_advanced_interaction_export.json', advanced)
    dump(EXPECTED/'runtime_cases.json', runtime_tests)
    dump(EXPECTED/'advanced_cases.json', advanced_tests)

    boundaries = {}
    validations = {}
    projects_to_check = [
        ('01_field_retention', field),
        ('02_runtime_matrix', runtime),
        ('03_advanced_interaction_export', advanced),
    ]
    projects_to_check.extend((f'runtime_cases/{case_id}', project) for case_id, project in sorted(isolated_runtime.items()))
    for name,project in projects_to_check:
        hits = scan_tool_only_keys(project)
        boundaries[name] = {'ok':not hits,'hits':hits}
        report = validate(project)
        validations[name] = {
            'ok': report['valid'],
            'errors':[x for x in report['diagnostics'] if x.get('severity')=='error'],
            'warnings':[x for x in report['diagnostics'] if x.get('severity')=='warning'],
        }
    dump(EXPECTED/'template_boundary.json', boundaries)
    fcoverage = field_coverage(field)
    dump(EXPECTED/'field_coverage.json', fcoverage)
    if not fcoverage['ok']:
        raise SystemExit('field-retention fixture is missing declared native fields: ' + json.dumps(fcoverage, indent=2))
    dump(EXPECTED/'fixture_validation.json', validations)
    dump(EXPECTED/'coverage_manifest.json', build_manifest(runtime_tests, advanced_tests))

    creator_tests = json.loads((EXPECTED/'creator_cases.json').read_text(encoding='utf-8'))
    def pending_entry(name: str, fixture: str, *, fixture_sha256: str | None = None) -> dict[str, Any]:
        path = OUT / fixture
        return {
            'name': name,
            'status': 'pending',
            'observation_source': 'official_gui',
            'fixture': fixture,
            'fixture_sha256': fixture_sha256 or sha256(path),
            'observed': {},
            'notes': '',
            'artifacts': [],
        }
    result_template = {
        'format': 'iccplus-official-gui-results-v2',
        'tested_tool_version': __version__,
        'official_gui_version': '2.10.6',
        'official_gui_url_or_build': '',
        'browser': '',
        'tester': '',
        'started_at': '',
        'finished_at': '',
        'runtime_results': {x['id']: pending_entry(x['name'], x['fixture'], fixture_sha256=x['fixture_sha256']) for x in runtime_tests},
        'creator_results': {x['id']: pending_entry(x['name'], x['fixture']) for x in creator_tests},
        'advanced_results': {x['id']: pending_entry(x['name'], 'fixtures/03_advanced_interaction_export.json') for x in advanced_tests},
        'returned_artifacts': [],
        'global_notes': '',
    }
    dump(OUT/'results_template'/'official_results.json', result_template)

    hashes = {}
    for path in sorted(FIXTURES.rglob('*.json')) + [p for p in sorted(EXPECTED.glob('*.json')) if p.name != 'fixture_hashes.json']:
        hashes[str(path.relative_to(OUT))] = {'sha256':sha256(path),'bytes':path.stat().st_size}
    dump(EXPECTED/'fixture_hashes.json', hashes)

    bad = {k:v for k,v in boundaries.items() if not v['ok']}
    if bad:
        raise SystemExit('tool-only template metadata leaked into project JSON: ' + json.dumps(bad))
    # The runtime matrix deliberately contains negative parity cases. Keep their
    # validator diagnostics as test evidence. The two general-purpose fixtures
    # must be clean because the official Creator should accept them as authored
    # projects without relying on malformed-input behavior.
    # The compact runtime matrix contains deliberate negative/malformed cases,
    # and the corresponding isolated fixtures keep those exact source-parity
    # inputs. General-purpose fixtures must be clean.
    errors = {
        k:v['errors'] for k,v in validations.items()
        if not (k == '02_runtime_matrix' or k.startswith('runtime_cases/')) and v['errors']
    }
    if errors:
        raise SystemExit('verification fixtures have unexpected validation errors: ' + json.dumps(errors, indent=2))

    print(json.dumps({
        'ok':True,
        'tool_version':__version__,
        'runtime_cases':len(runtime_tests),
        'advanced_cases':len(advanced_tests),
        'fixture_hashes':hashes,
    }, indent=2))

if __name__ == '__main__':
    main()
