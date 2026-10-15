"""Exercise the same evolving progress through every generated step view."""

import json
import re
import xml.etree.ElementTree as ET

import pytest
import yaml

from scripts.dashboard.collector import collect_dashboard
from scripts.dashboard.main import run_dashboard, run_workspace_dashboard


SVG = "{http://www.w3.org/2000/svg}"


def graph_nodes(page):
    source = re.search(r'<svg[^>]*xmlns="http://www.w3.org/2000/svg">.*?</svg>', page, re.S)
    return ET.fromstring(source[0]).findall(f"{SVG}a")


def test_changing_steps_stay_consistent_across_all_generated_views(tmp_path):
    workspace = tmp_path / "workspace"
    pair = workspace / "project/.pair"
    pair.mkdir(parents=True)
    (pair / "manifest.yaml").write_text(yaml.safe_dump({"steps": [
        {"id": "01", "title": "First"},
        {"id": "02", "title": "Second", "dependencies": ["01"]},
        {"id": "03", "title": "Third", "dependencies": ["02"]},
        {"id": "04", "title": "Skipped"},
        {"id": "05", "title": "Old plan"},
    ]}))
    (pair / "events.jsonl").write_text(json.dumps({"time": "2026-10-15T08:00:00Z", "event": "Started first step", "step": "01"}) + "\n")

    transitions = [
        ("01", ["active", "pending", "pending"], 0, "Active"),
        ("01", ["review", "pending", "pending"], 0, "In review"),
        ("02", ["completed", "active", "pending"], 1, "Active"),
        ("03", ["completed", "completed", "review"], 2, "In review"),
        ("", ["completed", "completed", "completed"], 3, None),
    ]
    for current, statuses, completed, badge in transitions:
        states = {f"{number:02d}": {"status": status} for number, status in enumerate(statuses, 1)}
        states.update({"04": {"status": "skipped"}, "05": {"status": "superseded"}})
        (pair / "progress.yaml").write_text(yaml.safe_dump({
            "phase": "guided_reconstruction" if current else "complete",
            "current_step": current, "steps": states,
        }))
        run_dashboard(pair)
        run_workspace_dashboard(workspace)
        data = json.loads((pair / "dashboard/data.json").read_text())
        page = (pair / "dashboard/index.html").read_text()
        assert data["current_step"] == (current or None)
        assert (data["completed_steps"], data["total_steps"]) == (completed, 3)
        percent = round(completed / 3 * 100)
        assert f'value="{percent}" max="100"' in page
        assert f"{completed} of 3 steps completed" in page
        assert "5 steps · 2 excluded" in page
        assert data["ownership"]["total"] == completed
        assert "Recorded step: 01" in page  # Historical steps must not follow the current pointer.

        rows = dict(re.findall(r'<li id="step-(\d+)"(.*?)</li>', page, re.S))
        nodes = graph_nodes(page)
        assert len(rows) == len(nodes) == len(data["plan"]) == 5
        for index, (row, step) in enumerate(zip(rows.values(), data["plan"]), 1):
            # The graph may be laid out by dependency rather than manifest order.
            node = next(item for item in nodes if item.get("href") == f"#step-{index}")
            identity = f'Step {index} · ID: {step["id"]}'
            assert identity in row
            assert identity in node.get("aria-label")
            expected_current = step["id"] == current
            assert ('aria-current="step"' in row) == expected_current
            assert (node.get("aria-current") == "step") == expected_current
            label = {"active": "Active", "review": "In review", "completed": "Completed", "skipped": "Skipped", "superseded": "Superseded", "pending": "Pending"}[step["status"]]
            assert label in row and label in "".join(node.itertext())
            if expected_current:
                assert identity in page.split('<div class="current-step">', 1)[1].split('</section>', 1)[0]
                assert f"Current · {badge}" in "".join(node.itertext())
                assert badge in row
                assert badge in page.split('<div class="current-step">', 1)[1].split('</section>', 1)[0]
        if not current:
            assert 'aria-current="step"' not in page
            assert "No current step" in page

        overview = json.loads((workspace / ".pair/dashboard/data.json").read_text())
        project = overview["projects"][0]
        detail = json.loads((workspace / ".pair/dashboard" / project["artifact_dir"] / "data.json").read_text())
        for field in ("current_step", "completed_steps", "total_steps", "plan"):
            assert detail[field] == project["snapshot"][field] == data[field]
        assert f'value="{percent}" max="100"' in (workspace / ".pair/dashboard/index.html").read_text()


def test_reordered_numeric_ids_are_not_confused_with_plan_positions(canonical_pair):
    (canonical_pair / "manifest.yaml").write_text('steps:\n- {id: "02", title: First in plan}\n- {id: "01", title: Second in plan}\n')
    (canonical_pair / "progress.yaml").write_text('current_step: "01"\nsteps:\n  "02": {status: completed}\n  "01": {status: active}\n')
    run_dashboard(canonical_pair)
    page = (canonical_pair / "dashboard/index.html").read_text()
    current = next(node for node in graph_nodes(page) if node.get("aria-current") == "step")
    assert current.get("href") == "#step-2"
    assert "Step 2 · ID: 01" in current.get("aria-label")
    assert "2. Second in plan" in "".join(current.itertext())
    assert "Step 1 · ID: 02" in page
    assert "02 / 01" not in page


@pytest.mark.parametrize("field", ["manifest", "progress key", "current step"])
def test_numeric_yaml_ids_fail_visibly_instead_of_silently_losing_progress(canonical_pair, field):
    if field == "manifest":
        (canonical_pair / "manifest.yaml").write_text('steps:\n- {id: 01, title: First}\n')
    elif field == "progress key":
        (canonical_pair / "progress.yaml").write_text('steps:\n  01: {status: completed}\n')
    else:
        (canonical_pair / "progress.yaml").write_text('current_step: 01\nsteps: {}\n')
    with pytest.raises(ValueError, match="quote numeric IDs"):
        collect_dashboard(canonical_pair)


@pytest.mark.parametrize("step", [{"title": "Missing ID"}, {"id": "", "title": "Empty ID"}])
def test_manifest_cannot_invent_an_id_from_the_display_position(canonical_pair, step):
    (canonical_pair / "manifest.yaml").write_text(yaml.safe_dump({"steps": [step]}))
    with pytest.raises(ValueError, match="expected a non-empty string step ID"):
        collect_dashboard(canonical_pair)


@pytest.mark.parametrize("completed_status", ["completed", "done", "complete"])
def test_actual_step_states_override_legacy_plan_statuses(canonical_pair, completed_status):
    (canonical_pair / "manifest.yaml").write_text('{}\n')
    (canonical_pair / "progress.yaml").write_text(yaml.safe_dump({
        "phase": "guided_reconstruction", "current_step": "b",
        "plan": [{"id": "a", "title": "First", "status": "pending"}, {"id": "b", "title": "Second", "status": "pending", "dependencies": ["a"]}],
        "steps": {"a": {"status": completed_status}, "b": {"status": "active"}},
    }))
    snapshot = collect_dashboard(canonical_pair)
    assert [step.status for step in snapshot.plan] == [completed_status, "active"]
    assert [step.readiness for step in snapshot.plan] == ["completed", "in_progress"]
    assert snapshot.completed_steps == snapshot.ownership["total"] == 1
    assert snapshot.actions[0]["command"] == "/pair next b"


def test_dangling_current_step_is_visible_as_state_drift(canonical_pair):
    (canonical_pair / "progress.yaml").write_text('phase: guided_reconstruction\ncurrent_step: missing\nsteps: {}\n')
    snapshot = collect_dashboard(canonical_pair)
    assert any("Current step 'missing' is missing from the plan" in warning for warning in snapshot.warnings)
    assert snapshot.actions[0]["command"] == "/pair status"


@pytest.mark.parametrize("phase,current,states,message", [
    ("guided_reconstruction", "parser", {"design": {"status": "active"}, "parser": {"status": "pending"}}, "differ from current step"),
    ("guided_reconstruction", "", {"parser": {"status": "active"}}, "No current step is recorded"),
    ("complete", "", {"design": {"status": "completed"}}, "Workflow phase is complete"),
])
def test_contradictory_source_progress_requires_reconciliation(canonical_pair, phase, current, states, message):
    (canonical_pair / "progress.yaml").write_text(yaml.safe_dump({"phase": phase, "current_step": current, "steps": states}))
    snapshot = collect_dashboard(canonical_pair)
    assert any(message in warning for warning in snapshot.warnings)
    assert all(action["command"] == "/pair status" for action in snapshot.actions)
    assert {step.id: step.status for step in snapshot.plan}["parser"] == states.get("parser", {}).get("status", "pending")
