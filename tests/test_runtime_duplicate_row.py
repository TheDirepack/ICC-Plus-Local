from __future__ import annotations

import copy

from iccplus_tools.editor import make_entity
from iccplus_tools.simulator import Simulator
from iccplus_tools.upstream_2106 import default_project


def _project(*, suffix_requirements: bool = False, suffix_functions: bool = False):
    p = default_project()
    p['rows'] = []
    p['groups'] = [{'id':'g','name':'g','category':-1,'elements':['inner','other'],'rowElements':[]}]
    source = make_entity(p, 'row', {'id':'source','title':'Source','objects':[]})
    inner = make_entity(p, 'choice', {
        'id':'inner','title':'Inner','groups':['g'],
        'requireds':[{'required':True,'type':'id','reqId':'other','requireds':[]}],
        'scores':[{'idx':'s-old','id':'','value':0,'requireds':[],'discounts':[{'id':'x','state':1}]}],
        'activateOtherChoice':True,'activateThisChoice':'other/ON#2',
    }, parent='source')
    other = make_entity(p, 'choice', {'id':'other','title':'Other','groups':['g']}, parent='source')
    source['objects'] = [inner, other]
    for i,c in enumerate(source['objects']): c['index']=i
    controls = make_entity(p, 'row', {'id':'controls','title':'Controls','objects':[]})
    trigger = make_entity(p, 'choice', {
        'id':'trigger','title':'Trigger','duplicateRow':True,
        'duplicateRowId':'source','duplicateRowPlace':'controls',
        'dRowAddSufReq':suffix_requirements,
        'dRowAddSufFunc':suffix_functions,
    }, parent='controls')
    controls['objects']=[trigger]
    p['rows']=[source,controls]
    for i,r in enumerate(p['rows']): r['index']=i
    return p


def test_runtime_duplicate_row_inserts_after_target_and_resets_runtime_fields():
    sim = Simulator(_project(suffix_requirements=True, suffix_functions=True))
    event = sim.select('trigger')
    assert event.ok
    assert event.details['duplicated_row'] == 'source/D#1'
    assert [r.id for r in sim.index.by_kind['row']] == ['source','controls','source/D#1']
    clone = sim.index.one('inner/D#1','choice')
    assert clone is not None
    assert clone.value['isActive'] is False
    assert clone.value['scores'][0]['idx'] != 's-old'
    assert 'discounts' not in clone.value['scores'][0]
    group = sim.index.one('g','group')
    assert group is not None
    assert 'inner/D#1' in group.value['elements']
    assert 'duplicateRow' not in sim.choice_status('trigger').unsupported_effects


def test_runtime_duplicate_row_rewrites_requirements_and_functions_when_source_flags_request_it():
    sim = Simulator(_project(suffix_requirements=False, suffix_functions=False))
    sim.select('trigger')
    clone = sim.index.one('inner/D#1','choice')
    assert clone is not None
    assert clone.value['requireds'][0]['reqId'] == 'other/D#1'
    assert clone.value['activateThisChoice'] == 'other/D#1/ON#2,'


def test_runtime_duplicate_row_survives_serialized_session_continuation():
    base = _project(suffix_requirements=True, suffix_functions=True)
    sim = Simulator(base)
    sim.select('trigger')
    state = sim.export_state()
    assert state['project_fingerprint'] != ''
    assert state['runtime']['dynamic_rows'][0]['row']['id'] == 'source/D#1'

    resumed = Simulator(copy.deepcopy(base))
    resumed.import_state(state)
    assert resumed.index.one('source/D#1','row') is not None
    assert resumed.index.one('inner/D#1','choice') is not None
    assert resumed.export_build_string() == sim.export_build_string()
    assert resumed.state.row_counts == sim.state.row_counts


def test_bad_dynamic_row_state_is_transactional():
    base = _project(suffix_requirements=True, suffix_functions=True)
    sim = Simulator(base)
    original_ids = [r.id for r in sim.index.by_kind['row']]
    state = sim.export_state()
    state['runtime']['dynamic_rows'] = [{'collection':'rows','index':0,'row':{'id':'not-a-duplicate'}}]
    try:
        sim.import_state(state)
    except ValueError as exc:
        assert 'dynamic_rows' in str(exc)
    else:
        raise AssertionError('invalid dynamic row state should fail')
    assert [r.id for r in sim.index.by_kind['row']] == original_ids
