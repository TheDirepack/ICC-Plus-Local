from __future__ import annotations

from typing import Any

_GUIDES: dict[str, dict[str, Any]] = {
    'automation': {
        'goal': 'Use the smallest stable JSON-first interface for an LLM or automation agent.',
        'commands': [
            'reference capabilities --brief', 'reference commands', 'inspect PROJECT',
            'structure PROJECT', 'rules PROJECT', 'style PROJECT', 'play PROJECT --state STATE',
        ],
        'rules': [
            'Use inspect for batched read-only discovery.',
            'Use structure, rules, and style for normal writes; each validates before writing.',
            'Use reference fields/schema/guide instead of guessing field names or syntax.',
            'Keep related writes in one phase transaction and use expect counts on broad selectors.',
            'Use play for progressive player-visible auditing, including multi-step audit requests.',
        ],
    },
    'start': {
        'goal': 'Create or inspect a project without guessing field names.',
        'commands': [
            'reference capabilities --brief', 'reference schema list', 'reference fields choice --details',
            'template entity choice', 'generate -o project.json', 'inspect project.json',
        ],
        'rules': [
            'Use stable IDs for every identity-bearing entity.',
            'Use structure, rules, and style as the normal edit path.',
            'Validation runs automatically after normal edits.',
        ],
    },
    'typed-authoring': {
        'goal': 'Use pinned 2.10.7 field names and value types.',
        'commands': [
            'reference fields KIND --details', 'reference schema KIND',
            'reference types --format typescript|python', 'template entity KIND',
        ],
        'rules': ['Known native fields are type-checked.', 'Use the phase schemas before low-level compatibility paths.'],
    },
    'structure': {
        'goal': 'Create and organize Rows, Choices, Addons, IDs, titles, and text without mixing mechanics or styling.',
        'commands': ['reference schema structure-ops', 'structure PROJECT SCRIPT', 'inspect PROJECT'],
        'rules': [
            'Put Requirements, Scores, selection limits, and effects in rules.',
            'Put images, templates, widths, and styling in style.',
            'Bulk add/update/delete uses the same structure operation path as single-item edits.',
            'Validation runs automatically before the project is written.',
        ],
    },
    'rules': {
        'goal': 'Add gameplay mechanics without rewriting content or presentation.',
        'commands': ['reference schema rules-ops', 'rules PROJECT SCRIPT', 'inspect PROJECT', 'play PROJECT'],
        'rules': [
            'Prefer require/exclude/gate/score_many/group_members/effects for common mechanics.',
            'Use expect counts for broad generated selectors.',
            'Audit the resulting behavior through player-visible play output.',
        ],
    },
    'batch': {
        'goal': 'Apply many changes atomically without switching to separate bulk commands.',
        'commands': ['reference schema structure-ops', 'reference schema rules-ops', 'structure PROJECT', 'rules PROJECT', 'style PROJECT'],
        'rules': [
            'Single and bulk edits use the same phase commands.',
            'Use items, refs, or where selectors as appropriate.',
            'Use expect counts on broad selectors.',
            'A failed phase operation aborts the whole transaction.',
        ],
    },
    'requirements': {
        'goal': 'Author gates and requirements through the rules phase.',
        'commands': ['reference fields requirement --details', 'reference schema requirement', 'rules PROJECT SCRIPT', 'play PROJECT'],
        'rules': ['Use rules helper operations for ordinary gates.', 'Use native requirement fields for advanced types.', 'Verify behavior through play rather than hidden runtime inspection.'],
    },
    'visuals': {
        'goal': 'Assign images and native ICC Plus styling in bulk.',
        'commands': ['reference schema style-manifest', 'inspect PROJECT', 'style PROJECT MANIFEST', 'media image import', 'media probe'],
        'rules': [
            'Local and embedded images are compressed automatically when assigned.',
            'A style manifest may target one item, explicit refs, selectors, or many independent items.',
            'Keep source/license notes in the authoring manifest, not project.json.',
        ],
    },
    'playtest': {
        'goal': 'Audit gameplay progressively without exposing hidden mechanics.',
        'commands': ['play PROJECT', 'play PROJECT --state STATE', 'play PROJECT @audit.json --state STATE'],
        'rules': [
            'Player output includes only player-visible state.',
            'Multi-step audit requests can assert visible points, selections, availability, and visibility after each step.',
            'Hidden and nonexistent guessed IDs remain indistinguishable.',
            'Keep the state file outside the LM context.',
        ],
    },
    'templates': {
        'goal': 'Keep every template/design operation in one predictable namespace.',
        'commands': ['template entity KIND', 'template style list|show|apply', 'template design export|import'],
        'rules': ['Entity defaults, style presets, and Creator design-file operations all live under template.'],
    },
    'project': {
        'goal': 'Handle project serialization and interchange without cluttering the authoring surface.',
        'commands': ['project format', 'project export', 'project fragment export|import', 'project ids export|from-titles', 'project build-summary', 'project build-string'],
        'rules': ['These are project I/O helpers, not alternate authoring paths.'],
    },
    'parity': {
        'goal': 'Check what is source-pinned and what still needs browser verification.',
        'commands': ['reference parity', 'run-upstream-parity-tests'],
        'rules': [
            'The local runtime is pinned to source commit 1ea9db888cde2286d18d0d5de50933cb8773b739.',
            'A real Chromium differential remains the final runtime parity check.',
        ],
    },
}


def guide(topic: str | None = None) -> dict[str, Any]:
    if topic is None:
        return {'format': 'iccplus-guide-index', 'topics': [{'topic': k, 'goal': v['goal']} for k, v in _GUIDES.items()]}
    if topic not in _GUIDES:
        raise ValueError(f'unknown guide topic: {topic}; choices: {", ".join(_GUIDES)}')
    return {'format': 'iccplus-guide', 'topic': topic, **_GUIDES[topic]}


def guide_topics() -> list[str]:
    return list(_GUIDES)
