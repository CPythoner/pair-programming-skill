import json
from pathlib import Path

import pytest

from scripts.dashboard.collector import collect_dashboard
from scripts.dashboard.main import run_dashboard


def _record(session_id="session-01", **changes):
    return {"schema_version": 1, "id": session_id, "title": "Dashboard session", "feature_slug": "dashboard",
            "started_at": "2026-10-15T09:00:00+08:00", "ended_at": "2026-10-15T10:00:00+08:00",
            "status": "completed", **changes}


def test_same_day_sessions_and_all_formats_have_distinct_stable_history(canonical_pair):
    import yaml

    sessions = canonical_pair / "sessions"
    (sessions / "first.md").write_text("---\n" + yaml.safe_dump(_record("first")) + "---\n# Summary\n")
    (sessions / "second.yaml").write_text(yaml.safe_dump(_record("second", status="abandoned")))
    (sessions / "third.json").write_text(json.dumps(_record("third", ended_at=None, status="active")))
    run_dashboard(canonical_pair)
    history = canonical_pair / "dashboard/history"
    paths = {path.name for path in history.glob("*.json")}
    assert len(paths) == 4  # Three structured records and the existing legacy Markdown.
    data = collect_dashboard(canonical_pair)
    structured = [item for item in data.sessions if not item["legacy"]]
    assert {item["status"] for item in structured} == {"completed", "abandoned", "active"}
    assert all(item["started_at"] for item in structured)

    (sessions / "third.json").write_text(json.dumps(_record("third", title="Updated title")))
    run_dashboard(canonical_pair)
    assert {path.name for path in history.glob("*.json")} == paths
    assert any(json.loads(path.read_text())["title"] == "Updated title" for path in history.glob("*.json"))


def test_history_is_rebuildable_and_prunes_only_managed_exports(canonical_pair):
    run_dashboard(canonical_pair)
    history = canonical_pair / "dashboard/history"
    record = next(history.glob("session-*.json"))
    original = record.read_bytes()
    record.unlink()
    run_dashboard(canonical_pair)
    assert record.read_bytes() == original
    (history / "notes.json").write_text("user notes")
    (canonical_pair / "sessions/2026-10-15.md").unlink()
    run_dashboard(canonical_pair)
    assert not list(history.glob("session-*.json"))
    assert (history / "notes.json").read_text() == "user notes"


def test_legacy_summary_does_not_invent_outcome_or_actual_times(canonical_pair):
    session = collect_dashboard(canonical_pair).sessions[0]
    assert session["legacy"] is True
    assert session["status"] == "unknown"
    assert session["started_at"] is None
    assert session["ended_at"] is None
    assert session["source_modified_at"]


def test_duplicate_ids_disable_conflicting_exports(canonical_pair):
    for name in ("a", "b"):
        (canonical_pair / f"sessions/{name}.json").write_text(json.dumps(_record()))
    snapshot = collect_dashboard(canonical_pair)
    assert any("Duplicate session ID" in warning for warning in snapshot.warnings)
    assert all(item["history_file"] is None for item in snapshot.sessions if not item["legacy"])
    run_dashboard(canonical_pair)
    assert len(list((canonical_pair / "dashboard/history").glob("*.json"))) == 1


@pytest.mark.parametrize("changes", [{"id": "../../outside"}, {"started_at": "2026-10-15"}, {"ended_at": "2026-10-14T09:00:00+08:00"}])
def test_invalid_metadata_reports_warning_without_fabricating_history(canonical_pair, changes):
    (canonical_pair / "sessions/invalid.json").write_text(json.dumps(_record(**changes)))
    snapshot = collect_dashboard(canonical_pair)
    assert len(snapshot.sessions) == 1
    assert any("Cannot read sessions/invalid.json" in warning for warning in snapshot.warnings)


def test_session_data_and_page_are_escaped(canonical_pair):
    title = '<script>alert(1)</script>'
    (canonical_pair / "sessions/script.json").write_text(json.dumps(_record(title=title)))
    run_dashboard(canonical_pair)
    html = (canonical_pair / "dashboard/index.html").read_text()
    assert title not in html
    assert "&lt;script&gt;" in html


def test_event_order_compares_instants_across_timezones(canonical_pair):
    (canonical_pair / "events.jsonl").write_text(
        '{"time":"2026-10-15T09:00:00+08:00","event":"earlier"}\n'
        '{"time":"2026-10-15T02:00:00+00:00","event":"later"}\n'
    )
    events = collect_dashboard(canonical_pair).events
    names = [event.event for event in events]
    assert names.index("earlier") < names.index("later")
