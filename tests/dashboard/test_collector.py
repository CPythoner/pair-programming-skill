import json

from dashboard import collect_dashboard


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
