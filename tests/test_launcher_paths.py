from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_symlinked_iccplus_launcher_resolves_real_repository_root(tmp_path: Path):
    link = tmp_path / "iccplus-local"
    link.symlink_to(ROOT / "iccplus-local")
    result = subprocess.run(
        ["sh", str(link), "--version"],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "0.10.0rc15" in result.stdout


def test_symlinked_installer_links_real_launchers_and_marks_them_executable(tmp_path: Path):
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()
    for name in ("install.sh", "iccplus-local", "cyoa-compress"):
        shutil.copyfile(ROOT / name, fake_repo / name)

    installer_link = tmp_path / "install-link"
    installer_link.symlink_to(fake_repo / "install.sh")
    bin_dir = tmp_path / "bin"

    result = subprocess.run(
        ["sh", str(installer_link), str(bin_dir)],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (bin_dir / "iccplus-local").is_symlink()
    assert (bin_dir / "cyoa-compress").is_symlink()
    assert (bin_dir / "iccplus-local").resolve() == fake_repo / "iccplus-local"
    assert (bin_dir / "cyoa-compress").resolve() == fake_repo / "cyoa-compress"
    assert os.access(fake_repo / "iccplus-local", os.X_OK)
    assert os.access(fake_repo / "cyoa-compress", os.X_OK)
