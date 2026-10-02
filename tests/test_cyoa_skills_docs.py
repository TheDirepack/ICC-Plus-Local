from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CURRENT_TOOL_VERSION = "0.10.0rc15"
CURRENT_ICCPLUS_VERSION = "2.10.7"

RETAINED = {
    "iccplus-local",
    "cyoa-plan",
    "cyoa-review",
    "cyoa-migrate",
    "cyoa-develop",
    "cyoa-ship",
    "cyoa-compress",
}
RETIRED = {"cyoa-create", "cyoa-edit", "cyoa-look", "cyoa-test"}


def test_compressed_cyoa_skill_set_is_packaged():
    for name in RETAINED:
        assert (SKILLS / name / "SKILL.md").is_file(), name
    for name in RETIRED:
        assert not (SKILLS / name).exists(), name


def test_retained_skill_dependencies_are_packaged():
    assert (ROOT / "docs/cyoa/guide/00-index.md").is_file()
    assert (ROOT / "docs/cyoa/guide/20-troubleshooting.md").is_file()
    assert (ROOT / "docs/cyoa/guide/21-large-project-normalization.md").is_file()
    assert (ROOT / "docs/COMPILER_BOUNDARY.md").is_file()
    assert (ROOT / "docs/SPARSE_RUNTIME_SERIALIZATION.md").is_file()
    assert (ROOT / "docs/cyoa/legacy/legacy-icc-migration-reference.md").is_file()
    assert (SKILLS / "cyoa-plan/references/plan-checklist.md").is_file()
    assert (SKILLS / "cyoa-review/references/review-checklist.md").is_file()
    assert (SKILLS / "cyoa-migrate/references/migration-checklist.md").is_file()
    assert (SKILLS / "cyoa-develop/references/develop-checklist.md").is_file()
    assert (SKILLS / "cyoa-ship/references/ship-checklist.md").is_file()
    assert (SKILLS / "iccplus-local/references/local-workflow-checklist.md").is_file()


def test_current_version_markers_are_synchronized():
    assert (ROOT / "VERSION").read_text().strip() == CURRENT_TOOL_VERSION
    assert f'version = "{CURRENT_TOOL_VERSION}"' in (ROOT / "pyproject.toml").read_text()
    assert f'__version__ = "{CURRENT_TOOL_VERSION}"' in (ROOT / "iccplus_tools/version.py").read_text()

    current_docs = [
        ROOT / "README.md",
        ROOT / "START_HERE.md",
        ROOT / "docs/PACKAGE_README.md",
        ROOT / "docs/README.md",
        ROOT / "docs/PLAY_STRUCTURE.md",
        ROOT / "docs/CLI_REFERENCE.md",
        SKILLS / "cyoa-ship/SKILL.md",
    ]
    for path in current_docs:
        assert CURRENT_TOOL_VERSION in path.read_text(), path

    manifest = (ROOT / "PACKAGE_MANIFEST.json").read_text()
    assert f'"tool_version": "{CURRENT_TOOL_VERSION}"' in manifest
    assert 'rc15' in manifest


def test_current_docs_keep_2107_target_and_sparse_runtime_contract():
    field_reference = (ROOT / "docs/ICCPLUS_FIELD_REFERENCE.md").read_text()
    assert f"ICC Plus {CURRENT_ICCPLUS_VERSION}" in field_reference
    assert "removeSpace" in field_reference
    assert f"ICC Plus {CURRENT_ICCPLUS_VERSION}" in (ROOT / "docs/FIELD_CATALOG.md").read_text()
    sparse = (ROOT / "docs/SPARSE_RUNTIME_SERIALIZATION.md").read_text()
    assert f"ICC Plus {CURRENT_ICCPLUS_VERSION}" in sparse
    assert "load success alone" in sparse.lower()


def test_current_routing_declares_retired_wrappers():
    routing = (SKILLS / "ROUTING-EVALS.md").read_text()
    usage = (ROOT / "docs/cyoa/skills-usage.md").read_text()
    for name in RETIRED:
        assert name in routing
        assert name in usage


def test_current_workflow_docs_do_not_teach_hidden_commands():
    current = [
        "docs/AUTHORING_SCRIPTS.md",
        "docs/BULK_EDIT_COOKBOOK.md",
        "docs/BULK_SELECTORS.md",
        "docs/FIELD_CATALOG.md",
        "docs/ID_GUARANTEES.md",
        "docs/LLM_USAGE.md",
        "docs/PACKAGE_README.md",
        "docs/PATTERN_COOKBOOK.md",
        "docs/SCRIPTING.md",
    ]
    forbidden = [
        "iccplus-local apply ",
        "iccplus-local validate ",
        "iccplus-local match ",
        "iccplus-local list ",
        "iccplus-local search ",
        "iccplus-local show ",
        "apply-visuals",
    ]
    for rel in current:
        text = (ROOT / rel).read_text()
        for token in forbidden:
            assert token not in text, (rel, token)


def test_normalization_is_owned_by_the_source_compiler():
    boundary = (ROOT / "docs/COMPILER_BOUNDARY.md").read_text()
    guide = (ROOT / "docs/cyoa/guide/21-large-project-normalization.md").read_text()
    local_skill = (SKILLS / "iccplus-local/SKILL.md").read_text()
    develop_skill = (SKILLS / "cyoa-develop/SKILL.md").read_text()

    assert "The source compiler owns" in boundary
    assert "ICC Plus Local may validate" in boundary
    assert "ICC Plus Local should not perform these rewrites on its own" in guide
    assert "ICC Plus Local must not silently" in local_skill
    assert "source lowering and normalization to the project compiler" in develop_skill

    function_expectations = {
        "build.md": "does not decide how a higher-level semantic source should be normalized",
        "project.md": "does not choose a compact ID scheme",
        "rules.md": "belong in the source compiler",
        "structure.md": "Those are source/compiler decisions",
        "style.md": "deduplicating repeated style intent belongs in the source compiler",
    }
    for filename, expected in function_expectations.items():
        text = (SKILLS / "iccplus-local/functions" / filename).read_text()
        assert expected in text, filename


def test_runtime_sparsification_stays_native_serialization_not_source_normalization():
    boundary = (ROOT / "docs/COMPILER_BOUNDARY.md").read_text()
    sparse = (ROOT / "docs/SPARSE_RUNTIME_SERIALIZATION.md").read_text()
    project = (SKILLS / "iccplus-local/functions/project.md").read_text()
    ship = (SKILLS / "cyoa-ship/SKILL.md").read_text()

    assert "player-facing runtime payload is a different serialization target" in boundary
    assert "not source normalization" in sparse
    assert "default runtime policy" in project
    assert "behavior-preserving sparse serializer by default" in ship


def test_2108_addon_changelog_is_not_described_as_a_row_selection_limit_fix():
    docs = [
        ROOT / "docs/COMPILER_BOUNDARY.md",
        ROOT / "docs/cyoa/guide/21-large-project-normalization.md",
        SKILLS / "iccplus-local/SKILL.md",
    ]
    for path in docs:
        text = path.read_text()
        assert "layout-width fix" in text, path
        assert "not evidence" in text, path

    guide = (ROOT / "docs/cyoa/guide/21-large-project-normalization.md").read_text()
    local_skill = (SKILLS / "iccplus-local/SKILL.md").read_text()
    rules = (SKILLS / "iccplus-local/functions/rules.md").read_text()
    ship = (SKILLS / "cyoa-ship/SKILL.md").read_text()

    assert "Do not assume ordinary Row choice limits correctly enforce selectable Addon radio sets" not in guide
    assert "Do not assume Row choice limits can replace selectable-Addon radio/exclusion logic" not in local_skill
    assert "addonWidth" in rules
    assert "evidence about `allowedChoices`" in rules
    assert "addonWidth" in ship
    assert "Row selection-limit fix" in ship
