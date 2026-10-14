from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

from scripts.dashboard.main import run_dashboard


def test_run_dashboard_generates_artifacts(tmp_path: Path) -> None:
    pair_dir = tmp_path / ".pair"
    pair_dir.mkdir()

    output = tmp_path / "dashboard"

    run_dashboard(pair_dir=pair_dir, output=output)

    assert (output / "data.json").exists()
    assert (output / "index.html").exists()


def test_run_dashboard_json_only(tmp_path: Path) -> None:
    pair_dir = tmp_path / ".pair"
    pair_dir.mkdir()

    output = tmp_path / "dashboard"

    run_dashboard(pair_dir=pair_dir, output=output, json_only=True)

    assert (output / "data.json").exists()
    assert not (output / "index.html").exists()
    assert not (output / "assets").exists()


ROOT = Path(__file__).resolve().parents[2]


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ""},
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("entrypoint", ["module", "script"])
def test_cli_entrypoints_start_without_import_errors(entrypoint):
    args = ["-m", "scripts.dashboard.main"] if entrypoint == "module" else [str(ROOT / "scripts/dashboard/main.py")]
    result = _run([*args, "--help"], ROOT)

    assert result.returncode == 0, result.stderr
    assert "--pair-dir" in result.stdout
    assert result.stderr == ""


def test_generation_does_not_rewrite_source_state(canonical_pair):
    originals = {path: path.read_bytes() for path in canonical_pair.rglob("*") if path.is_file()}

    run_dashboard(pair_dir=canonical_pair)

    assert all(path.read_bytes() == content for path, content in originals.items())
    generated = canonical_pair / "dashboard"
    assert (generated / "index.html").is_file()
    assert (generated / "assets/style.css").is_file()
    assert (generated / "assets/app.js").is_file()
    data = json.loads((generated / "data.json").read_text())
    assert data["project"] == "demo"
    assert data["completed_steps"] == 1


def test_json_only_preserves_previous_html_and_assets(canonical_pair):
    run_dashboard(pair_dir=canonical_pair)
    generated = canonical_pair / "dashboard"
    previous = {path: path.read_bytes() for path in generated.rglob("*") if path.name != "data.json" and path.is_file()}

    run_dashboard(pair_dir=canonical_pair, json_only=True)

    assert all(path.read_bytes() == content for path, content in previous.items())


def test_installed_dashboard_runs_from_user_project(tmp_path, canonical_pair):
    install_target = tmp_path / "installation"
    install_target.mkdir()
    installation = subprocess.run(
        ["bash", str(ROOT / "scripts/install.sh"), "codex", "--target", str(install_target)],
        capture_output=True,
        text=True,
    )
    assert installation.returncode == 0, installation.stderr
    skill = install_target / ".agents/skills/pair-programming"
    assert (skill / "reference/dashboard.md").is_file()
    assert (skill / "scripts/dashboard/export.py").is_file()
    assert (skill / "scripts/dashboard/requirements.txt").is_file()
    assert not list(skill.rglob("__pycache__"))

    result = _run([str(skill / "scripts/dashboard/main.py")], canonical_pair.parent)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    generated = canonical_pair / "dashboard"
    assert str(generated / "index.html") in result.stdout
    assert json.loads((generated / "data.json").read_text())["project"] == "demo"
    assert not (skill / ".pair").exists()


def test_direct_cli_custom_paths_and_json_only(tmp_path, canonical_pair):
    output = tmp_path / "custom dashboard"
    result = _run([
        str(ROOT / "scripts/dashboard/main.py"),
        "--pair-dir", str(canonical_pair), "--output", str(output), "--json",
    ], tmp_path)

    assert result.returncode == 0, result.stderr
    assert (output / "data.json").is_file()
    assert not (output / "index.html").exists()
    assert not (output / "assets").exists()


def test_invalid_state_cli_fails_before_writing_artifacts(tmp_path, canonical_pair):
    (canonical_pair / "progress.yaml").write_text("schema_version: 2\n")
    output = tmp_path / "dashboard"
    result = _run([
        str(ROOT / "scripts/dashboard/main.py"), "--pair-dir", str(canonical_pair),
        "--output", str(output),
    ], tmp_path)

    assert result.returncode == 1
    assert "Unsupported schema version" in result.stderr
    assert not output.exists()
