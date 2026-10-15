import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from scripts.dashboard import watch_dashboard
from scripts.dashboard import watch as watch_module
from scripts.dashboard import export as export_module


ROOT = Path(__file__).resolve().parents[2]


def _poll(monkeypatch, pair_dir, actions, **options):
    actions = iter(actions)

    def sleep(_interval):
        try:
            action = next(actions)
        except StopIteration:
            raise KeyboardInterrupt
        action()

    monkeypatch.setattr(watch_module.time, "sleep", sleep)
    with pytest.raises(KeyboardInterrupt):
        watch_dashboard(pair_dir=pair_dir, **options)


def _data(pair_dir):
    return json.loads((pair_dir / "dashboard/data.json").read_text())


@pytest.mark.parametrize("source,old,new,field,expected", [
    ("manifest.yaml", "name: demo", "name: other", "project", "other"),
    ("progress.yaml", "current_step: parser", "current_step: tests", "current_step", "tests"),
    ("pitfalls.yaml", "Missing entrypoint", "Fixed entrypoint", "pitfalls", "Fixed entrypoint"),
])
def test_state_changes_refresh_dashboard(monkeypatch, canonical_pair, capsys, source, old, new, field, expected):
    path = canonical_pair / source
    original = path.read_text()
    _poll(monkeypatch, canonical_pair, [lambda: path.write_text(original.replace(old, new))])

    result = _data(canonical_pair)
    if field == "pitfalls":
        assert result[field][0]["title"] == expected
    else:
        assert result[field] == expected
    assert (canonical_pair / "dashboard/index.html").is_file()
    output = capsys.readouterr().out
    assert f"{source} changed" in output
    assert output.count("Dashboard refreshed") == 1
    if source == "progress.yaml":
        assert "Step: parser -> tests" in output


@pytest.mark.parametrize("remove", [False, True])
def test_session_creation_and_removal_refresh_history(monkeypatch, canonical_pair, capsys, remove):
    path = canonical_pair / "sessions" / ("2026-10-15.md" if remove else "2026-10-16.md")
    action = path.unlink if remove else lambda: path.write_text("# Session\n\n- Current step: tests\n")
    _poll(monkeypatch, canonical_pair, [action])

    assert len(_data(canonical_pair)["events"]) == (0 if remove else 2)
    assert f"sessions/{path.name} {'removed' if remove else 'created'}" in capsys.readouterr().out


def test_same_size_and_timestamp_edit_is_detected(monkeypatch, canonical_pair):
    path = canonical_pair / "progress.yaml"
    original = path.read_text()
    metadata = path.stat()

    def modify():
        path.write_text(original.replace("current_step: parser", "current_step: review"))
        os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
        assert path.stat().st_size == metadata.st_size

    _poll(monkeypatch, canonical_pair, [modify])

    assert _data(canonical_pair)["current_step"] == "review"


def test_output_and_unrelated_pair_changes_do_not_trigger_refresh(monkeypatch, canonical_pair, capsys):
    initial = {}

    def unrelated_changes():
        initial["json"] = (canonical_pair / "dashboard/data.json").read_bytes()
        (canonical_pair / "dashboard/index.html").write_text("Generated output changed externally")
        (canonical_pair / "notes.md").write_text("Unrelated notes")
        (canonical_pair / "sessions/.DS_Store").write_bytes(b"not a session")

    _poll(monkeypatch, canonical_pair, [unrelated_changes, lambda: None])

    assert (canonical_pair / "dashboard/data.json").read_bytes() == initial["json"]
    assert "Dashboard refreshed" not in capsys.readouterr().out


def test_partial_yaml_preserves_artifacts_then_recovers(monkeypatch, canonical_pair, capsys):
    path = canonical_pair / "progress.yaml"
    valid = path.read_text()
    saved = {}

    def partial_write():
        for name in ("data.json", "index.html"):
            saved[name] = (canonical_pair / "dashboard" / name).read_bytes()
        path.write_text("steps: [unfinished\n")

    def check_unchanged():
        # Business data stays intact; new freshness metadata makes the stale view visible.
        previous = json.loads(saved["data.json"])
        current = _data(canonical_pair)
        for key in ("project", "plan", "current_step", "sessions", "generated_at"):
            assert current[key] == previous[key]
        assert current["freshness"]["state"] == "stale"
        assert current["actions"][0]["command"] == "/pair status"
        assert current["actions"][0]["kind"] == "source"
        assert "Showing last valid state" in (canonical_pair / "dashboard/index.html").read_text()

    _poll(monkeypatch, canonical_pair, [
        partial_write, check_unchanged, check_unchanged,
        lambda: path.write_text(valid.replace("current_step: parser", "current_step: tests")),
    ])

    assert _data(canonical_pair)["current_step"] == "tests"
    output = capsys.readouterr().out
    assert output.count("Dashboard refresh failed") == 1
    assert output.count("Dashboard refreshed") == 1
    assert "Step: parser -> tests" in output


def test_transient_output_error_retries_without_another_source_change(monkeypatch, canonical_pair, capsys):
    export = export_module.export_html
    writes = 0

    def failing_once(snapshot, output):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("Temporary write failure")
        export(snapshot, output)

    monkeypatch.setattr(export_module, "export_html", failing_once)
    path = canonical_pair / "manifest.yaml"
    original = path.read_text()
    _poll(monkeypatch, canonical_pair, [
        lambda: path.write_text(original.replace("name: demo", "name: recovered")),
        lambda: None,
    ])

    assert "recovered" in (canonical_pair / "dashboard/index.html").read_text()
    output = capsys.readouterr().out
    assert output.count("Dashboard refresh failed") == 1
    assert output.count("Dashboard refreshed") == 1


def test_json_only_and_legacy_event_changes(monkeypatch, tmp_path, capsys):
    pair = tmp_path / ".pair"
    pair.mkdir()
    (pair / "manifest.json").write_text('{"project": "legacy"}')
    (pair / "progress.json").write_text('{"current_step": "one"}')
    event = '{"time": "2026-10-15T11:00:00+08:00", "event": "review", "step": "one"}\n'
    _poll(monkeypatch, pair, [lambda: (pair / "events.jsonl").write_text(event)], json_only=True)

    assert _data(pair)["events"][0]["event"] == "review"
    assert not (pair / "dashboard/index.html").exists()
    assert not (pair / "dashboard/assets").exists()
    assert "events.jsonl created" in capsys.readouterr().out


@pytest.mark.parametrize("interval", [0, -1, math.nan, math.inf])
def test_invalid_interval_fails_before_generation(tmp_path, interval):
    with pytest.raises(ValueError, match="greater than zero"):
        watch_dashboard(pair_dir=tmp_path / ".pair", interval=interval)
    assert not (tmp_path / ".pair").exists()


def test_initial_generation_is_read_only(monkeypatch, canonical_pair):
    originals = {path: path.read_bytes() for path in canonical_pair.rglob("*") if path.is_file()}
    _poll(monkeypatch, canonical_pair, [lambda: None])

    assert all(path.read_bytes() == data for path, data in originals.items())


def _wait_for_data(path, predicate):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            if predicate(json.loads(path.read_text())):
                return
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        time.sleep(0.01)
    pytest.fail(f"Watch did not update {path} within five seconds")


@pytest.mark.skipif(os.name == "nt", reason="This subprocess signal check uses Unix SIGINT")
@pytest.mark.parametrize("entrypoint", ["module", "script"])
def test_real_watch_cli_refreshes_and_stops_cleanly(tmp_path, canonical_pair, entrypoint):
    output = tmp_path / "custom dashboard"
    args = ["-m", "scripts.dashboard.main"] if entrypoint == "module" else [str(ROOT / "scripts/dashboard/main.py")]
    process = subprocess.Popen(
        [sys.executable, *args, "--watch", "--interval", "0.05", "--json",
         "--pair-dir", str(canonical_pair), "--output", str(output)],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ""},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        _wait_for_data(output / "data.json", lambda data: data["current_step"] == "parser")
        path = canonical_pair / "progress.yaml"
        path.write_text(path.read_text().replace("current_step: parser", "current_step: tests"))
        _wait_for_data(output / "data.json", lambda data: data["current_step"] == "tests")
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()

    assert process.returncode == 0, stderr
    assert stderr == ""
    assert "Step: parser -> tests" in stdout
    assert "Dashboard refreshed" in stdout
    assert "Dashboard watch stopped." in stdout
    assert "Traceback" not in stdout
    assert not (output / "index.html").exists()
    assert not (output / "assets").exists()


@pytest.mark.parametrize("source", ["session", "operation"])
def test_structured_sessions_and_takeover_journals_are_watched(monkeypatch, canonical_pair, source):
    def add_source():
        if source == "session":
            (canonical_pair / "sessions/new.json").write_text(json.dumps({
                "schema_version": 1, "id": "new-session", "title": "New session", "feature_slug": "demo",
                "started_at": "2026-10-15T10:00:00+08:00", "status": "active",
            }))
        else:
            operations = canonical_pair / "operations"
            operations.mkdir()
            (operations / "op.yaml").write_text("operation:\n  id: interrupted-op\n  status: interrupted\n")

    _poll(monkeypatch, canonical_pair, [add_source])
    data = _data(canonical_pair)
    if source == "session":
        assert any(session["id"] == "new-session" for session in data["sessions"])
    else:
        assert any(action["kind"] == "takeover" for action in data["actions"])


def test_transient_fingerprint_error_recovers_freshness_without_edits(monkeypatch, canonical_pair):
    fingerprint = watch_module._fingerprint
    reads = 0

    def failing_once(pair_dir):
        nonlocal reads
        reads += 1
        if reads == 2:
            raise OSError("Temporary read error")
        return fingerprint(pair_dir)

    monkeypatch.setattr(watch_module, "_fingerprint", failing_once)
    _poll(monkeypatch, canonical_pair, [lambda: None, lambda: None])
    assert _data(canonical_pair)["freshness"]["state"] == "fresh"


def test_invalid_session_write_preserves_previous_business_data(monkeypatch, canonical_pair):
    def break_session():
        (canonical_pair / "sessions/new.json").write_text('{"unfinished":')

    _poll(monkeypatch, canonical_pair, [break_session])
    data = _data(canonical_pair)
    assert len(data["sessions"]) == 1
    assert data["freshness"]["state"] == "stale"
    assert "sessions/new.json" in data["freshness"]["error"]


def test_partial_jsonl_event_preserves_last_valid_view(monkeypatch, canonical_pair):
    _poll(monkeypatch, canonical_pair, [lambda: (canonical_pair / "events.jsonl").write_text('{"event":')])
    data = _data(canonical_pair)
    assert len(data["events"]) == 1
    assert data["freshness"]["state"] == "stale"
    assert "events.jsonl:1" in data["freshness"]["error"]
