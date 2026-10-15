from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.dashboard import run_workspace_dashboard, watch_dashboard
from scripts.dashboard.workspace import collect_workspace

ROOT = Path(__file__).resolve().parents[2]


def _project(root, name, source):
    target = root / name / ".pair"
    shutil.copytree(source, target)
    return target


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []

    def handle_starttag(self, _tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        self.links.extend(attrs[key] for key in ("href", "src") if key in attrs)


def test_workspace_error_isolation_bounded_scan_and_read_only(tmp_path, canonical_pair):
    root = tmp_path / "workspace"
    root.mkdir()
    _project(root, "forge", canonical_pair)
    bad = _project(root, "broken", canonical_pair)
    (bad / "progress.yaml").write_text("steps: [unfinished\n")
    _project(root, ".hidden", canonical_pair)
    _project(root, "node_modules", canonical_pair)
    _project(root / "nested", "deep", canonical_pair)
    (root / "linked").symlink_to(root / "forge", target_is_directory=True)
    source_files = {path: path.read_bytes() for path in root.rglob("*") if path.is_file() and not path.is_symlink()}

    run_workspace_dashboard(root)

    snapshot = json.loads((root / ".pair/dashboard/data.json").read_text())
    assert [project["name"] for project in snapshot["projects"]] == ["broken", "forge"]
    broken, forge = snapshot["projects"]
    assert broken["snapshot"] is None
    assert "Invalid YAML" in broken["error"]
    assert forge["snapshot"]["completed_steps"] == 1
    assert all(path.read_bytes() == content for path, content in source_files.items())
    html = (root / ".pair/dashboard/index.html").read_text()
    assert "Read error · progress unknown" in html
    assert "average" not in snapshot


def test_workspace_all_generated_links_and_graph_anchors_resolve(tmp_path, canonical_pair):
    root = tmp_path / "workspace"
    root.mkdir()
    pair = _project(root, "project with spaces", canonical_pair)
    path = pair / "manifest.yaml"
    path.write_text(path.read_text().replace("    title: Parser", "    title: Parser\n    dependencies: [design]"))
    run_workspace_dashboard(root)
    output = root / ".pair/dashboard"
    pages = list(output.rglob("*.html"))
    assert len(pages) == 2
    for page in pages:
        parser = Links()
        parser.feed(page.read_text())
        for link in parser.links:
            if link.startswith("#"):
                assert link[1:] in parser.ids, (page, link)
            else:
                assert (page.parent / link).is_file(), (page, link)


def test_workspace_json_only_has_history_but_no_html_or_assets(tmp_path, canonical_pair):
    root = tmp_path / "workspace"
    root.mkdir()
    _project(root, "forge", canonical_pair)
    output = tmp_path / "json-output"
    run_workspace_dashboard(root, output, json_only=True)

    assert (output / "data.json").is_file()
    assert len(list(output.rglob("session-*.json"))) == 1
    assert not list(output.rglob("*.html"))
    assert not list(output.rglob("*.css"))
    assert not list(output.rglob("*.js"))


def test_unreadable_project_replaces_previous_detail_with_unknown_progress(tmp_path, canonical_pair):
    root = tmp_path / "workspace"
    root.mkdir()
    pair = _project(root, "forge", canonical_pair)
    run_workspace_dashboard(root)
    output = root / ".pair/dashboard"
    project = json.loads((output / "data.json").read_text())["projects"][0]
    detail = output / project["artifact_dir"]
    history = next((detail / "history").glob("*.json"))
    previous_history = history.read_bytes()
    (pair / "progress.yaml").write_text("steps: [unfinished\n")
    run_workspace_dashboard(root)
    data = json.loads((detail / "data.json").read_text())
    assert data["progress_known"] is False
    assert data["freshness"]["state"] == "unavailable"
    assert data["current_step"] is None
    assert "Source unavailable · progress unknown" in (detail / "index.html").read_text()
    assert "33%" not in (detail / "index.html").read_text()
    assert history.read_bytes() == previous_history


def test_workspace_watch_keeps_failed_detail_stale_and_recovers(monkeypatch, tmp_path, canonical_pair):
    from scripts.dashboard import watch as watch_module

    root = tmp_path / "workspace"
    root.mkdir()
    failed = _project(root, "alpha", canonical_pair)
    healthy = _project(root, "beta", canonical_pair)
    original = (failed / "progress.yaml").read_text()
    output = root / ".pair/dashboard"

    def read():
        projects = {item["name"]: item for item in json.loads((output / "data.json").read_text())["projects"]}
        detail = output / projects["alpha"]["artifact_dir"]
        return projects, detail, json.loads((detail / "data.json").read_text())

    def break_one_project():
        projects, _, data = read()
        assert data["freshness"]["state"] == "fresh"
        (failed / "progress.yaml").write_text("steps: [unfinished\n")
        path = healthy / "progress.yaml"
        path.write_text(path.read_text().replace("status: active", "status: review"))

    def check_stale_and_repair():
        projects, detail, data = read()
        assert projects["alpha"]["error"]
        assert data["freshness"]["state"] == "stale"
        assert data["current_step"] == "parser"
        assert data["completed_steps"] == 1
        assert "Showing last valid state · stale" in (detail / "index.html").read_text()
        assert data["actions"][0]["command"] == "/pair status"
        assert projects["beta"]["snapshot"]["freshness"]["state"] == "fresh"
        assert projects["beta"]["snapshot"]["plan"][1]["status"] == "review"
        (failed / "progress.yaml").write_text(original.replace("status: active", "status: review"))

    def check_recovery():
        projects, detail, data = read()
        assert projects["alpha"]["error"] is None
        assert data["freshness"]["state"] == "fresh"
        assert data["plan"][1]["status"] == "review"
        assert "Showing last valid state" not in (detail / "index.html").read_text()
        assert data["actions"][0]["command"] == "/pair review parser"

    actions = iter([break_one_project, check_stale_and_repair, check_recovery])

    def sleep(_interval):
        try:
            action = next(actions)
        except StopIteration:
            raise KeyboardInterrupt
        action()

    monkeypatch.setattr(watch_module.time, "sleep", sleep)
    with pytest.raises(KeyboardInterrupt):
        watch_dashboard(workspace=root)


def test_workspace_missing_directory_is_reported(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        collect_workspace(tmp_path / "missing")


def test_workspace_missing_progress_keeps_counts_unknown(tmp_path, canonical_pair):
    root = tmp_path / "workspace"
    root.mkdir()
    pair = _project(root, "forge", canonical_pair)
    (pair / "progress.yaml").unlink()
    run_workspace_dashboard(root)
    content = (root / ".pair/dashboard/index.html").read_text()
    assert "Progress state unavailable" in content
    assert "Completed count unknown" in content
    assert "0 / 3 steps" not in content


def test_workspace_watch_tracks_project_lifecycle_and_independent_errors(monkeypatch, tmp_path, canonical_pair, capsys):
    from scripts.dashboard import watch as watch_module

    root = tmp_path / "workspace"
    root.mkdir()
    alpha = _project(root, "alpha", canonical_pair)
    beta = _project(root, "beta", canonical_pair)

    def changed_projects():
        path = alpha / "progress.yaml"
        path.write_text(path.read_text().replace("current_step: parser", "current_step: tests"))
        (beta / "progress.yaml").write_text("steps: [unfinished\n")
        (root / "late/.pair").mkdir(parents=True)

    def check_partial_and_remove():
        data = json.loads((root / ".pair/dashboard/data.json").read_text())
        assert next(project for project in data["projects"] if project["name"] == "alpha")["snapshot"]["current_step"] == "tests"
        assert next(project for project in data["projects"] if project["name"] == "beta")["error"]
        beta.rename(beta.with_name(".pair-removed"))

    actions = iter([changed_projects, check_partial_and_remove])

    def sleep(_interval):
        try:
            action = next(actions)
        except StopIteration:
            raise KeyboardInterrupt
        action()

    monkeypatch.setattr(watch_module.time, "sleep", sleep)
    with pytest.raises(KeyboardInterrupt):
        watch_dashboard(workspace=root, json_only=True)
    data = json.loads((root / ".pair/dashboard/data.json").read_text())
    assert [project["name"] for project in data["projects"]] == ["alpha", "late"]
    assert data["freshness"]["mode"] == "watch"
    output = capsys.readouterr().out
    assert "alpha Step: parser -> tests" in output
    assert "Project beta read error" in output
    assert "late/.pair/ created" in output


def test_workspace_cli_and_mutually_exclusive_inputs(tmp_path, canonical_pair):
    root = tmp_path / "workspace"
    root.mkdir()
    _project(root, "forge", canonical_pair)
    args = [sys.executable, str(ROOT / "scripts/dashboard/main.py"), "--workspace", str(root), "--json"]
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ""}
    result = subprocess.run(args, cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (root / ".pair/dashboard/data.json").is_file()
    result = subprocess.run([*args, "--pair-dir", str(canonical_pair)], env=environment, capture_output=True, text=True)
    assert result.returncode == 2
    assert "not allowed with argument" in result.stderr
