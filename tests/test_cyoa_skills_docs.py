from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

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
    assert (ROOT / "docs/cyoa/legacy/legacy-icc-migration-reference.md").is_file()
    assert (SKILLS / "cyoa-plan/references/plan-checklist.md").is_file()
    assert (SKILLS / "cyoa-review/references/review-checklist.md").is_file()
    assert (SKILLS / "cyoa-migrate/references/migration-checklist.md").is_file()
    assert (SKILLS / "cyoa-develop/references/develop-checklist.md").is_file()
    assert (SKILLS / "cyoa-ship/references/ship-checklist.md").is_file()


def test_current_docs_use_rc13_and_2107():
    assert (ROOT / "VERSION").read_text().strip() == "0.10.0rc13"
    assert "0.10.0rc13" in (ROOT / "START_HERE.md").read_text()
    assert "ICC Plus 2.10.7" in (ROOT / "docs/ICCPLUS_FIELD_REFERENCE.md").read_text()
    assert "removeSpace" in (ROOT / "docs/ICCPLUS_FIELD_REFERENCE.md").read_text()
    assert "ICC Plus 2.10.7" in (ROOT / "docs/FIELD_CATALOG.md").read_text()


def test_current_agent_docs_do_not_teach_retired_wrapper_skills():
    texts = "\n".join(
        p.read_text()
        for p in [
            ROOT / "README.md",
            SKILLS / "README.md",
            ROOT / "docs/cyoa/skills-usage.md",
            ROOT / "docs/LLM_USAGE.md",
        ]
    )
    for name in RETIRED:
        assert f"`{name}`" not in texts.replace(
            "The old wrapper skills `cyoa-create`, `cyoa-edit`, `cyoa-look`, and `cyoa-test` are intentionally absent.",
            ""
        ).replace(
            "Do not recreate separate `cyoa-create`, `cyoa-edit`, `cyoa-look`, or `cyoa-test` skills.",
            ""
        )


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
