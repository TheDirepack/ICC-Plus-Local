from __future__ import annotations

from typing import Any

from .version import __version__
from .field_catalog import catalog_kinds

COMMAND_KINDS = [
    'reference', 'template', 'media', 'project',
    'inspect', 'generate', 'build', 'structure', 'rules', 'style', 'play',
]

ENTITY_KINDS = [
    'row', 'backpack_row', 'choice', 'addon', 'selectable_addon', 'score',
    'requirement', 'point', 'variable', 'word', 'group', 'global_requirement',
    'row_design_group', 'choice_design_group', 'sound_effect', 'category',
]

OPERATION_KINDS = [
    'add', 'upsert', 'update', 'update_many', 'require', 'exclude', 'gate',
    'ungate', 'score_many', 'group_members', 'design_group_members', 'effects',
    'hide_contents', 'clear_hide_contents', 'project_update', 'delete', 'delete_many', 'rename',
    'set', 'remove', 'assert', 'normalize', 'row_sort', 'row_copy_choices', 'row_move_choices', 'design_import', 'reorder', 'move', 'clone',
]

REQUIREMENT_TYPES = [
    'id', 'points', 'or', 'pointCompare', 'selFromGroups', 'selFromRows',
    'selFromWhole', 'gid', 'word',
]

HIDE_CONTENT_CODES = {
    'choice_title': '1',
    'choice_image': '2',
    'choice_text': '3',
    'choice_score': '4',
    'choice_requirement': '5',
    'addon_title': '6',
    'addon_image': '7',
    'addon_text': '8',
    'unselected_addon': '9',
    'unmet_addon': '10',
}

SESSION_ACTIONS = ['select', 'deselect', 'row_button', 'status', 'snapshot', 'view', 'reset']


def capabilities() -> dict[str, Any]:
    """Return stable machine-readable discovery data for scripts and LLMs."""
    return {
        'tool': 'iccplus-local',
        'tool_version': __version__,
        'target': {
            'icc_plus_version': '2.10.7',
            'source_repository': 'wahaha303/ICC-Plus-Svelte',
            'source_commit': '1ea9db888cde2286d18d0d5de50933cb8773b739',
        },
        'interface': 'command-line',
        'output': {
            'normal_results': 'JSON on stdout',
            'errors': 'structured JSON on stderr',
            'default': 'compact when stdout is not a TTY; pretty in an interactive terminal',
            'compact_flag_available_on_all_commands': True,
            'pretty_flag_available_on_all_commands': True,
        },
        'project_input': {
            'shape_guard': True,
            'required_top_level': {'rows': 'array'},
            'standard_collection_fields_must_be_arrays_when_present': True,
        },
        'field_catalog': {
            'command': 'iccplus-local reference fields KIND --details --contains TEXT',
            'kinds': catalog_kinds(),
            'source': 'ICCPlus/src/lib/store/types.ts at the pinned source commit',
            'miss_suggestions': True,
            'types': 'source-derived from the pinned TypeScript declarations',
            'json_schema_command': 'iccplus-local reference schema KIND --mode patch|native',
            'generated_types_command': 'iccplus-local reference types --format typescript|python --mode patch|native',
            'project_top_level_kind': 'project',
            'backpack_row_alias': True,
        },
        'command_kinds': COMMAND_KINDS,
        'entity_kinds': ENTITY_KINDS,
        'operation_kinds': OPERATION_KINDS,
        'requirement_types_modeled': REQUIREMENT_TYPES,
        'hide_content_codes': HIDE_CONTENT_CODES,
        'session_actions': SESSION_ACTIONS,
        'identity': {
            'namespace': 'project-wide for string identities',
            'score_identity_field': 'idx',
            'category_identity': '(type, idx)',
            'missing_ids': 'generated deterministically',
            'duplicate_explicit_ids': 'rejected before write',
        },
        'write_model': {
            'apply_is_atomic': True,
            'normal_writes_require_unique_identities': True,
            'validation_errors_write_by_default': False,
            'canonical_writes_validate_automatically': True,
            'validation_bypass_is_compatibility_only': True,
        },
        'authoring': {
            'typed_native_fields': True,
            'phased_authoring_commands': ['structure', 'rules', 'style'],
            'normal_edit_validation': 'automatic before write',
            'low_level_escape_hatch': 'hidden compatibility command apply; not part of the canonical surface',
            'row_bulk_operations': 'structure phase operations row_sort, row_copy_choices, row_move_choices',
            'entity_templates': 'template entity KIND',
            'style_templates': 'template style list|show|apply',
            'design_templates': 'template design export|import',
            'id_tools': 'project ids export|from-titles',
            'font_tools': 'media font list|add|remove',
            'sound_tools': 'media sound import',
            'image_tools': 'media image import|clear; compression is automatic',
            'project_io': 'project format|export|fragment|build-summary|build-string',
        },
        'help_system': {
            'command_inventory': 'reference commands',
            'capabilities': 'reference capabilities [--brief]',
            'field_help': 'reference fields KIND --details',
            'schema_help': 'reference schema list; reference schema KIND --mode patch|native',
            'typed_declarations': 'reference types --format typescript|python --mode patch|native',
            'workflow_guides': 'reference guide [TOPIC]',
            'creator_parity': 'reference parity',
        },
        'gameplay_runner': {
            'command': 'play PROJECT [REQUEST] [--state FILE]',
            'single_action': 'use --select, --deselect, --row-button, --status, or --reset',
            'multi_step_audit': 'pass a JSON request with steps/actions and optional player-visible expect assertions',
            'player_visible_expectations': ['points','selected','not_selected','available','not_available','deselectable','not_deselectable','visible','hidden','row_choices','choice_rows'],
            'normalized_player_structure': 'view exposes visible rows, direct choices, and Addons as separate top-level lists with explicit parent/child IDs and visible-order indices',
            'row_choice_links': 'rows expose choice_ids; choices expose row_id; choices expose addon_ids; Addons expose choice_id and row_id',
            'selection_type_split': 'new explicit availability/deselectability fields distinguish direct Choices from selectable Addons; historical available_choice_ids/deselectable_choice_ids remain compatibility aliases for all selectable entities',
            'images': 'ignored; never loaded or returned by the gameplay runner',
            'hidden_content': 'not returned in player view; hidden and nonexistent guessed IDs remain indistinguishable',
            'invalid_actions': 'transactional failure with sanitized player error; state and RNG are rolled back',
            'player_state_can_stay_private': True,
        },
        'continuation': {
            'player_command': 'play',
            'state_file': 'play PROJECT --state FILE',
            'project_fingerprint_checked': True,
            'simple_player_loop': 'play automatically loads and atomically rewrites the private state file without returning runtime internals',
            'state_integrity': 'invalid state is rejected; --reset replaces a damaged state without loading it',
        },
        'bulk_selectors': {
            'preview_command': 'iccplus-local inspect PROJECT with {op:"match", where:{...}, expect:N}',
            'filters': ['kind','kinds','id','ids','id_prefix','row','rows','parent','parents','group','groups','title_contains','text_contains','path_prefix','backpack'],
            'matching': 'exact except explicit title_contains/text_contains filters',
            'expect': 'integer or {min,max}; mutation aborts on mismatch',
            'empty_matches': 'rejected by mutating operations unless allow_empty is true',
        },
        'semantic_effects': {
            'generation_field': 'effects',
            'bulk_operation': 'effects',
            'keys': ['activate','deactivate','hide_contents','row_limit','variables','points','word','multiple','discount','random_activate','scroll_to','template','width','sfx','delay','background','point_bar','confirm','selection','duplicate_row','addons','bgm','transition','random_weight','backpack_button_requirement','default_image'],
            'output': 'ordinary native ICC Plus fields; no alternate runtime format',
            'conflicts': 'shorthand/native conflicts are rejected',
        },
        'build_system': {
            'blank_command': 'iccplus-local generate -o project.json',
            'blank_source': 'exact ICC Plus 2.10.7 Creator default export',
            'mutation_commands': ['iccplus-local structure PROJECT SCRIPT', 'iccplus-local rules PROJECT SCRIPT', 'iccplus-local style PROJECT MANIFEST'],
            'repeatable_build_command': 'iccplus-local build BUILD.json -o project.json',
            'build_manifest_schema': 'iccplus-local reference schema build-manifest',
            'build_v2_phases': ['structure', 'rules', 'style', 'raw'],
            'structure_command': 'iccplus-local structure PROJECT [SCRIPT]',
            'rules_command': 'iccplus-local rules PROJECT [SCRIPT]',
            'style_command': 'iccplus-local style PROJECT [MANIFEST]',
            'raw_apply_command': 'compatibility-only; normal authoring uses structure/rules/style',
            'build_is_atomic_at_output': True,
            'build_validates_final_project': True,
        },
        'scripting': {
            'generate_creates_blank_project_only': True,
            'generate_output_can_be_omitted': True,
            'generated_default_output_is_non_destructive': True,
            'inspect_request_defaults_to_stdin': True,
            'inspect_batches_read_only_queries': True,
            'agent_operation_format': {'format': 'iccplus-agent-ops', 'format_version': 1, 'strict_fields': True, 'default_result_mode': 'compact'},
            'agent_operation_schema': 'iccplus-local reference schema agent-operations',
            'inspect_request_schema': 'iccplus-local reference schema inspect-request',
            'apply_script_defaults_to_stdin': True,
            'apply_script_accepts_inline_json_jsonl_or_at_file': True,
            'scenario_defaults_to_stdin': True,
            'session_state_in_accepts_json_or_file': True,
            'phase_scripts_are_json_first': True,
            'known_field_value_types_checked': True,
            'typed_schema_command': 'iccplus-local reference schema KIND --mode patch|native',
            'typed_interface_command': 'iccplus-local reference types --format typescript|python --mode patch|native',
            'field_typo_suggestions': True,
            'operation_inline_native_fields': True,
            'operation_ref_alias': 'ref',
            'one_or_many_fields': ['target/targets', 'member/members', 'row/rows', 'content/contents'],
            'safe_writes_default': True,
            'compact_json_uses_minimal_separators': True,
        },
        'visual_authoring': {
            'audit_command': 'iccplus-local inspect PROJECT with op=visual',
            'apply_command': 'iccplus-local style PROJECT MANIFEST',
            'image_compression': 'automatic for local files and embedded data URLs; remote URLs remain remote',
            'manifest_format': 'iccplus-visual-manifest v1',
            'supports': [
                'project styling', 'customCSS', 'image assignment', 'template', 'width',
                'grouped native styling', 'reusable presets', 'explicit refs batches', 'selector batches with expected counts', 'many distinct image assignments in one manifest',
                'copy_from visual treatment', 'replace/unset inline styling',
                'source/credit sidecar records',
            ],
            'unknown_manifest_keys_rejected': True,
            'custom_css_append_idempotent': True,
            'native_output': True,
            'browser_rendering': 'not emulated; verify final visuals in the ICC Plus Viewer',
        },
        'assets': {
            'automatic_image_compression': True,
            'automatic_paths': ['style image assignment', 'media image import', 'crop-field', 'style build steps'],
            'remote_urls': 'kept as remote URLs; they are not downloaded just to compress them',
            'probe_command': 'iccplus-local media probe PATH',
            'environment_command': 'iccplus-local reference doctor',
            'legacy_manual_compressor': 'hidden compatibility command only; normal authoring never needs it',
            'default_min_savings_bytes': 256,
            'default_min_savings_percent': 2.0,
        },
        'discovery': {
            'preflight': 'automatic on normal edits; use inspect op=check for a read-only report',
            'native_entity_shape': 'iccplus-local template entity KIND',
            'batched_read_only': 'iccplus-local inspect PROJECT [REQUEST]',
            'entity_details': 'inspect op=show',
            'identity_audit': 'inspect op=ids',
            'filtered_inventory': 'inspect op=list',
            'text_search': 'inspect op=search',
            'bulk_selector_preview': 'inspect op=match',
            'visual_audit': 'inspect op=visual',
            'project_stats': 'inspect op=stats',
            'command_schema': 'iccplus-local reference commands',
            'batched_read_only': 'iccplus-local inspect PROJECT [REQUEST]',
        },
    }
