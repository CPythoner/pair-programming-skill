import json

import pytest

from scripts.dashboard import collect_dashboard


def test_collect_dashboard(tmp_path):
    pair = tmp_path / ".pair"
    pair.mkdir()

    (pair / "manifest.json").write_text(
        json.dumps({"project": "demo"}), encoding="utf-8"
    )
    (pair / "progress.json").write_text(
        json.dumps(
            {
                "status": "implementing",
                "current_step": "parser",
                "plan": [
                    {"id": "1", "title": "Design", "status": "done"},
                    {"id": "2", "title": "Parser", "status": "active"},
                ],
            }
        ),
        encoding="utf-8",
    )

    snapshot = collect_dashboard(pair)

    assert snapshot.project == "demo"
    assert snapshot.status == "implementing"
    assert snapshot.completed_steps == 1
    assert len(snapshot.plan) == 2


def test_missing_pair_files_are_supported(tmp_path):
    snapshot = collect_dashboard(tmp_path / ".pair")

    assert snapshot.status == "unknown"
    assert snapshot.plan == []
    assert snapshot.updated_at is None
    assert len(snapshot.warnings) == 3
    assert not (tmp_path / ".pair").exists()


def test_canonical_yaml_uses_actual_progress_and_sessions(canonical_pair):
    snapshot = collect_dashboard(canonical_pair)

    assert snapshot.project == "demo"
    assert snapshot.phase == "guided_reconstruction"
    assert snapshot.current_step == "parser"
    assert snapshot.completed_steps == 1
    assert [item.status for item in snapshot.plan] == ["completed", "active", "pending"]
    assert snapshot.updated_at is not None
    assert snapshot.warnings == []
    assert snapshot.events[0].step == "parser"
    assert snapshot.events[0].details["time_source"] == "file_mtime"
    assert snapshot.pitfalls[0].severity == "high"
    assert snapshot.pitfalls[0].resolution == "Package the generator"
    assert snapshot.pitfalls[0].affected_scope == ["scripts/dashboard/main.py", "main"]


def test_yaml_takes_precedence_over_legacy_json(canonical_pair):
    (canonical_pair / "manifest.json").write_text('{"project": "stale"}')
    (canonical_pair / "progress.json").write_text('{"status": "complete"}')

    snapshot = collect_dashboard(canonical_pair)

    assert snapshot.project == "demo"
    assert snapshot.status == "guided_reconstruction"


def test_empty_session_step_does_not_consume_the_next_field(canonical_pair):
    (canonical_pair / "sessions/2026-10-15.md").write_text(
        "# Pair Session Summary\n\n- Current step:\n- Shadow generation: 1\n"
    )

    assert collect_dashboard(canonical_pair).events[0].step is None


def test_manifest_completion_does_not_imply_human_completion(canonical_pair):
    (canonical_pair / "progress.yaml").write_text("schema_version: 1\nsteps: {}\n")

    snapshot = collect_dashboard(canonical_pair)

    assert snapshot.completed_steps == 0
    assert all(item.status == "pending" for item in snapshot.plan)


@pytest.mark.parametrize("version_key", ["schema_version", "version"])
def test_unsupported_state_schema_fails_closed(canonical_pair, version_key):
    (canonical_pair / "progress.yaml").write_text(f"{version_key}: 2\n")

    with pytest.raises(ValueError, match="Unsupported schema version"):
        collect_dashboard(canonical_pair)


def test_malformed_yaml_reports_source_file(canonical_pair):
    (canonical_pair / "progress.yaml").write_text("steps: [broken\n")

    with pytest.raises(ValueError, match="Invalid YAML in .*progress.yaml"):
        collect_dashboard(canonical_pair)


def test_dashboard_remains_available_during_pending_approval_and_recovery(canonical_pair):
    (canonical_pair / "progress.yaml").write_text(
        "phase: design\ndesign_status: awaiting_approval\n"
    )
    assert collect_dashboard(canonical_pair).status == "awaiting_approval"

    (canonical_pair / "progress.yaml").write_text(
        "phase: design\nrecovery:\n  state: attention_required\n"
    )
    assert collect_dashboard(canonical_pair).status == "attention_required"
