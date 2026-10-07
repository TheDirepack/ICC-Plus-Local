from __future__ import annotations

import zipfile
from pathlib import Path

import scripts.build_release_archives as release


def _relative_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as zf:
        return {name.split("/", 1)[1] for name in zf.namelist() if "/" in name}


def test_release_archives_keep_full_docs_and_skills_but_drop_tests(tmp_path: Path):
    full = release.build_full(tmp_path, "test-ref")
    names = _relative_names(full)
    assert "skills/iccplus-local/SKILL.md" in names
    assert "skills/cyoa-review/SKILL.md" in names
    assert "docs/GAMEPLAY_RUNNER.md" in names
    assert "iccplus_tools/editor.py" in names
    assert not any(name.startswith("tests/") for name in names)
    assert not any(name.startswith("cli_tests/") for name in names)
    assert not any(name.startswith("compression_tests/") for name in names)
    assert not any(name.startswith("online_tests/") for name in names)
    assert not any(name.startswith(".github/") for name in names)
    assert "run-tests" not in names
    assert "run-compression-tests" not in names
    assert "run-upstream-parity-tests" not in names


def test_viewer_archive_contains_runtime_skill_docs_and_no_authoring(tmp_path: Path):
    viewer = release.build_viewer(tmp_path, "test-ref")
    names = _relative_names(viewer)
    assert "iccplus_tools/simulator.py" in names
    assert "iccplus_tools/viewer_cli.py" in names
    assert "skills/iccplus-viewer-test/SKILL.md" in names
    assert "docs/PLAY_STRUCTURE.md" in names
    assert "docs/GAMEPLAY_RUNNER.md" in names
    assert "iccplus_tools/editor.py" not in names
    assert "iccplus_tools/generation.py" not in names
    assert "iccplus_tools/build_pipeline.py" not in names
    assert not any(name.startswith("skills/cyoa-plan/") for name in names)
    assert not any(name.startswith("skills/iccplus-local/") for name in names)


def test_viewer_runtime_dependency_closure_is_authoring_free():
    forbidden = {
        "editor", "generation", "build_pipeline", "operations", "phase_ops", "assets",
        "packaging", "style_templates", "visuals", "creator_helpers", "project_integrity",
    }
    modules = {
        Path(name).stem
        for name in release.VIEWER_CODE
        if name.startswith("iccplus_tools/") and name.endswith(".py")
    }
    assert forbidden.isdisjoint(modules)


def test_full_archive_marks_user_launchers_executable(tmp_path: Path):
    full = release.build_full(tmp_path, "test-ref")
    with zipfile.ZipFile(full) as zf:
        infos = {
            info.filename.split("/", 1)[1]: info
            for info in zf.infolist()
            if "/" in info.filename
        }
    for name in ("iccplus-local", "cyoa-compress", "install.sh"):
        mode = (infos[name].external_attr >> 16) & 0o777
        assert mode & 0o111, f"{name} is not executable in the full release ZIP"
