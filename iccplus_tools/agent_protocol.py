from __future__ import annotations

import copy
import json
from functools import lru_cache
from importlib import resources
from typing import Any

PROTOCOL_SCHEMAS: dict[str, str] = {
    'operations': 'operation-script.schema.json',
    'agent-operations': 'agent-operation-script.schema.json',
    'inspect-request': 'inspect-request.schema.json',
    'session-request': 'session-request.schema.json',
    'runtime-state': 'runtime-state.schema.json',
    'build-manifest': 'build-manifest.schema.json',
    'structure-ops': 'structure-operation-script.schema.json',
    'rules-ops': 'rules-operation-script.schema.json',
    'style-manifest': 'visual-manifest.schema.json',
    'visual-manifest': 'visual-manifest.schema.json',
}

CANONICAL_AGENT_COMMANDS = {
    'discover': 'reference capabilities --brief',
    'command_tree': 'reference commands',
    'schema_index': 'reference schema list',
    'create_blank': 'generate -o PROJECT',
    'build': 'build BUILD.json -o PROJECT',
    'structure': 'structure PROJECT [SCRIPT]',
    'rules': 'rules PROJECT [SCRIPT]',
    'style': 'style PROJECT [MANIFEST]',
    'inspect': 'inspect PROJECT [REQUEST]',
    'play': 'play PROJECT [REQUEST] [--state STATE]',
    'templates': 'template entity|style|design ...',
    'media': 'media image|crop|font|sound|probe ...',
    'project_io': 'project format|export|fragment|ids|build-summary|build-string ...',
}

COMMAND_EXAMPLES: dict[str, list[str]] = {
    'reference': [
        'iccplus-local reference commands',
        'iccplus-local reference capabilities --brief',
        'iccplus-local reference schema structure-ops',
        'iccplus-local reference fields choice --details --contains activate',
    ],
    'template': [
        'iccplus-local template entity choice',
        'iccplus-local template style list',
        'iccplus-local template design export project.json global',
    ],
    'media': [
        'iccplus-local media image import project.json choice_a image.png',
        'iccplus-local media probe image.png',
    ],
    'project': [
        'iccplus-local project format project.json --style creator -o project.creator.json',
        'iccplus-local project export project.json -o project.zip',
    ],
    'inspect': [
        "printf '%s\\n' '{\"queries\":[{\"op\":\"check\"},{\"op\":\"search\",\"query\":\"fire\",\"kind\":\"choice\"}]}' | iccplus-local inspect project.json",
    ],
    'play': [
        'iccplus-local play project.json',
        'iccplus-local play project.json --state .state/run.json --select choice_a',
        'iccplus-local play project.json @audit.json --state .state/run.json',
    ],
}

COMMAND_SCHEMA_REFS: dict[str, list[str]] = {
    'reference': ['structure-ops', 'rules-ops', 'style-manifest', 'inspect-request', 'runtime-state'],
    'inspect': ['inspect-request'],
    'play': ['runtime-state'],
    'build': ['build-manifest', 'structure-ops', 'rules-ops', 'style-manifest', 'agent-operations'],
    'structure': ['structure-ops'],
    'rules': ['rules-ops'],
    'style': ['style-manifest'],
}

_MUTATING = {'template','media','project','generate','build','structure','rules','style','play'}

_CATEGORIES: dict[str, set[str]] = {
    'reference': {'reference'},
    'inspection': {'inspect'},
    'authoring': {'generate','build','structure','rules','style'},
    'resources': {'template','media'},
    'runtime': {'play'},
    'project_io': {'project'},
}


def protocol_schema_names() -> list[str]:
    return list(PROTOCOL_SCHEMAS)


def load_protocol_schema(name: str) -> dict[str, Any]:
    filename = PROTOCOL_SCHEMAS.get(name)
    if filename is None:
        raise ValueError(f'unknown protocol schema: {name}; choices: {", ".join(PROTOCOL_SCHEMAS)}')
    text = resources.files('iccplus_tools').joinpath('schemas', filename).read_text(encoding='utf-8')
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f'packaged protocol schema is not an object: {filename}')
    return value


def build_agent_operation_schema(base: dict[str, Any]) -> dict[str, Any]:
    """Return the strict canonical agent form of the compatibility operation schema.

    Compatibility scripts allow several shorthand shapes and unknown future
    native fields under ``values``. The canonical agent form uses one explicit
    wrapper, disallows unknown operation keys, and enables runtime strict field
    checking so a misspelling is never treated as a future field.
    """
    operation = copy.deepcopy(base.get('$defs', {}).get('operation', {}))
    for branch in operation.get('oneOf', []):
        if not isinstance(branch, dict):
            continue
        branch['additionalProperties'] = False
        op = branch.get('properties', {}).get('op', {}).get('const')
        if op in {'update','update_many','delete','delete_many'} and 'kind' in branch.get('properties', {}):
            required = list(branch.get('required', []))
            if 'kind' not in required:
                required.append('kind')
            branch['required'] = required
        if op in {'add','upsert','project_update','update','update_many'}:
            branch['description'] = (
                'Canonical agent form: place native ICC Plus fields under values. '
                'The runtime rejects unknown field names and type-checks every pinned field. '
                'Use `schema KIND` to validate a values object before execution when desired.'
            )
    return {
        '$schema':'https://json-schema.org/draft/2020-12/schema',
        '$id':'https://openai.local/iccplus/agent-operation-script.schema.json',
        'title':'ICC Plus canonical agent operation script',
        'description':(
            'Strict JSON-first authoring contract for LLMs and automation. This wrapper enables strict field checking. '
            'Use the compatibility `operations` schema only when intentionally targeting an unknown future ICC Plus field.'
        ),
        'type':'object',
        'additionalProperties':False,
        'properties':{
            'format':{'const':'iccplus-agent-ops'},
            'format_version':{'const':1},
            'strict_fields':{'const':True},
            'operations':{'type':'array','minItems':1,'items':{'$ref':'#/$defs/operation'}},
        },
        'required':['format','format_version','strict_fields','operations'],
        '$defs':{'operation':operation, **{k:copy.deepcopy(v) for k,v in base.get('$defs',{}).items() if k != 'operation'}},
        'x-iccplus-canonical-agent':True,
    }


def build_inspect_request_schema() -> dict[str, Any]:
    entity_kind = {
        'type': 'string',
        'description': 'Use an exact indexed entity kind, or all where supported.',
    }
    query_defs: list[dict[str, Any]] = [
        {'type':'object','additionalProperties':False,'properties':{'op':{'const':'check'}},'required':['op']},
        {'type':'object','additionalProperties':False,'properties':{'op':{'const':'summary'}},'required':['op']},
        {'type':'object','additionalProperties':False,'properties':{'op':{'const':'ids'},'all':{'type':'boolean','default':False}},'required':['op']},
        {'type':'object','additionalProperties':False,'properties':{
            'op':{'const':'list'},'kind':entity_kind,'row':{'type':'string'},'parent':{'type':'string'},'group':{'type':'string'},'id_prefix':{'type':'string'}
        },'required':['op']},
        {'type':'object','additionalProperties':False,'properties':{
            'op':{'const':'search'},'query':{'type':'string','minLength':1},'kind':entity_kind,'limit':{'type':'integer','minimum':1,'maximum':500,'default':20}
        },'required':['op','query']},
        {'type':'object','additionalProperties':False,'properties':{
            'op':{'const':'show'},'ref':{'type':'string','minLength':1},'kind':entity_kind
        },'required':['op','ref']},
        {'type':'object','additionalProperties':False,'properties':{
            'op':{'const':'get'},'pointer':{'type':'string'}
        },'required':['op','pointer']},
        {'type':'object','additionalProperties':False,'properties':{
            'op':{'const':'match'},'where':{'type':'object'},'expect':{},'allow_empty':{'type':'boolean','default':False}
        },'required':['op','where']},
        {'type':'object','additionalProperties':False,'properties':{'op':{'const':'stats'}},'required':['op']},
        {'type':'object','additionalProperties':False,'properties':{
            'op':{'const':'visual'},
            'kind':{'type':'string'},
            'kinds':{'type':'array','items':{'type':'string'},'uniqueItems':True},
            'row':{'type':'string'},'group':{'type':'string'},
            'missing_images':{'type':'boolean','default':False},
            'missing_assets':{'type':'boolean','default':False},
            'unstyled':{'type':'boolean','default':False},
            'limit':{'type':'integer','minimum':0},
            'asset_root':{'type':'string'},
            'manifest_stub':{'type':'boolean','default':False},
            'style_values':{'type':'boolean','default':False}
        },'required':['op']},
    ]
    query = {'oneOf': query_defs}
    return {
        '$schema':'https://json-schema.org/draft/2020-12/schema',
        '$id':'https://openai.local/iccplus/inspect-request.schema.json',
        'title':'ICC Plus batched inspection request',
        'description':'Read-only batch query contract for LLMs and automation. No query mutates the project.',
        'oneOf':[
            query,
            {'type':'array','minItems':1,'items':query},
            {'type':'object','additionalProperties':False,'properties':{
                'queries':{'type':'array','minItems':1,'items':query},
                'stop_on_error':{'type':'boolean','default':False},
            },'required':['queries']},
        ],
    }



@lru_cache(maxsize=1)
def strict_agent_operation_keys() -> dict[str, frozenset[str]]:
    schema = load_protocol_schema('agent-operations')
    out: dict[str, frozenset[str]] = {}
    operation = schema.get('$defs', {}).get('operation', {})
    for branch in operation.get('oneOf', []):
        if not isinstance(branch, dict):
            continue
        properties = branch.get('properties', {})
        op = properties.get('op', {}).get('const') if isinstance(properties, dict) else None
        if isinstance(op, str):
            out[op] = frozenset(properties)
    return out


AGENT_SCRIPT_KEYS = frozenset({'format', 'format_version', 'strict_fields', 'operations'})

def brief_capabilities(full: dict[str, Any]) -> dict[str, Any]:
    return {
        'tool': full.get('tool'),
        'tool_version': full.get('tool_version'),
        'target': full.get('target'),
        'interface': 'json-first CLI',
        'canonical_commands': CANONICAL_AGENT_COMMANDS,
        'command_inventory': 'Use `reference commands` for the complete recursive canonical tree.',
        'recommended_loop': [
            'Create a new project with `generate -o PROJECT`; generate only writes the exact blank Creator project.',
            'Use `structure PROJECT`, `rules PROJECT`, and `style PROJECT` for normal edits. Each validates before writing.',
            'Use `inspect PROJECT` for batched read-only discovery.',
            'Use `play PROJECT [REQUEST] --state FILE` for progressive player-visible testing and audit assertions.',
            'Use `template`, `media`, and `project` only for their focused resource/I/O jobs.',
            'Use `reference commands`, `reference fields`, and `reference schema` instead of guessing.',
        ],
        'canonical_write_formats': {
            'structure': {'format':'iccplus-structure-ops','format_version':1,'strict_fields':True},
            'rules': {'format':'iccplus-rules-ops','format_version':1,'strict_fields':True},
            'style': {'format':'iccplus-visual-manifest','format_version':1},
        },
        'schemas': {
            'index': 'iccplus-local reference schema list',
            'structure': 'iccplus-local reference schema structure-ops',
            'rules': 'iccplus-local reference schema rules-ops',
            'style': 'iccplus-local reference schema style-manifest',
            'canonical_write': 'iccplus-local reference schema agent-operations',
            'low_level_write': 'iccplus-local reference schema agent-operations',
            'build_manifest': 'iccplus-local reference schema build-manifest',
            'canonical_read': 'iccplus-local reference schema inspect-request',
            'runtime_state': 'iccplus-local reference schema runtime-state',
        },
        'safety': {
            'writes_validate_before_commit': True,
            'normal_edit_validation_is_automatic': True,
            'phase_writes_are_atomic': True,
            'phase_tools_reject_cross_phase_fields': True,
            'build_starts_from_exact_blank': True,
            'bulk_selectors_support_expect_counts': True,
            'phase_add_update_delete_accept_one_or_many': True,
            'image_compression_is_automatic': True,
            'player_audit_is_player_visible_only': True,
            'player_state_can_stay_out_of_model_context': True,
        },
        'error_contract': {
            'success': 0,
            'input_or_io': 1,
            'validation': 2,
            'runtime_or_query_rejection': 3,
            'atomic_batch_failure': 4,
            'stderr': 'top-level usage/input errors are JSON',
            'stdout': 'normal command results are JSON except generated type declarations',
        },
    }


def command_metadata(name: str) -> dict[str, Any]:
    category = next((cat for cat, names in _CATEGORIES.items() if name in names), 'other')
    return {
        'category': category,
        'mutates_project': name in _MUTATING,
        'recommended_for_agents': name in {'reference','template','media','project','generate','build','structure','rules','style','inspect','play'},
        'examples': COMMAND_EXAMPLES.get(name, []),
        'schema_refs': COMMAND_SCHEMA_REFS.get(name, []),
    }
