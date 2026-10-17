import json

import pytest

from scripts.dashboard.collector import collect_dashboard
from scripts.dashboard.insights import analyze_plan, implementation_origin, validation_summary, workflow_actions
from scripts.dashboard.model import PlanItem


def test_dependencies_and_readiness_preserve_source_status():
    plan = [PlanItem("design", "Design", "completed"),
            PlanItem("test", "Test", dependencies=["design"]),
            PlanItem("review", "Review", dependencies=["test"])]
    graph = analyze_plan(plan)

    assert graph == {"layers": [["design"], ["test"], ["review"]], "edges": [["design", "test"], ["test", "review"]], "errors": []}
    assert plan[1].readiness == "ready"
    assert plan[2].readiness == "waiting"
    assert plan[2].blocked_by == ["test"]
    assert plan[2].status == "pending"


@pytest.mark.parametrize("plan,message", [
    ([PlanItem("a", "A", dependencies=["missing"])], "missing dependency"),
    ([PlanItem("a", "A", dependencies=["b"]), PlanItem("b", "B", dependencies=["a"])], "Dependency cycle"),
    ([PlanItem("a", "A"), PlanItem("a", "Other A")], "Duplicate step ID"),
])
def test_invalid_graph_never_offers_ready_steps(plan, message):
    graph = analyze_plan(plan)

    assert any(message in error for error in graph["errors"])
    assert all(step.readiness != "ready" for step in plan)


def test_skipped_dependency_is_not_assumed_implemented():
    plan = [PlanItem("a", "A", "skipped"), PlanItem("b", "B", dependencies=["a"])]
    analyze_plan(plan)
    assert plan[1].readiness == "waiting"


def test_origin_denominator_and_unknown_coverage_are_explicit():
    plan = [PlanItem(str(index), str(index), "completed", origin=origin)
            for index, origin in enumerate(["human", "ai", "mixed", "unknown"])]
    plan.append(PlanItem("pending", "Pending", origin="human"))
    result = implementation_origin(plan)

    assert result["unit"] == "completed_steps"
    assert result["total"] == 4
    assert result["counts"] == {"human": 1, "ai": 1, "mixed": 1, "unknown": 1}
    assert set(result["percentages"].values()) == {25.0}
    assert result["coverage"] == 75
    empty = implementation_origin([])
    assert empty["coverage"] is None
    assert all(value is None for value in empty["percentages"].values())


def test_validation_requires_recorded_results():
    assert validation_summary({"validation": {"commands": ["pytest"]}}, {})["status"] == "unknown"
    assert validation_summary({"validation": {"last_results": [{"status": "passed"}]}}, {})["status"] == "passed"
    assert validation_summary({"validation": {"last_results": [{"status": "passed"}, {"status": "failed"}]}}, {})["status"] == "failed"
    assert validation_summary({"validation": {"last_results": ["pytest", {"status": "passed"}]}}, {})["status"] == "unknown"


def test_gates_take_priority_over_suggesting_next_step():
    plan = [PlanItem("a", "A")]
    graph = analyze_plan(plan)
    progress = {"phase": "guided_reconstruction", "recovery": {"state": "attention_required"}}
    actions = workflow_actions({"design": {"status": "awaiting_approval", "revision": 2}}, progress, plan, graph, {"status": "unknown"}, [{"id": "op-1", "status": "interrupted"}])

    assert {item["kind"] for item in actions} == {"recovery", "takeover", "approval"}
    assert not any(item["command"].startswith("/pair next") for item in actions)
    ready = workflow_actions({}, {"phase": "guided_reconstruction"}, plan, graph, {"status": "unknown"}, [])
    assert ready[0]["command"] == "/pair next a"
    shadow = workflow_actions({}, {"phase": "shadow"}, plan, graph, {"status": "unknown"}, [])
    assert shadow[0]["command"] == "/pair status"


def test_completed_takeover_does_not_imply_ai_ownership(canonical_pair):
    operations = canonical_pair / "operations"
    operations.mkdir()
    (operations / "op-1.yaml").write_text("schema_version: 1\noperation:\n  id: op-1\n  status: completed\n")
    snapshot = collect_dashboard(canonical_pair)
    assert snapshot.ownership["counts"]["unknown"] == 1
    assert snapshot.ownership["counts"]["ai"] == 0


def test_collector_derives_graph_origin_knowledge_and_validations(tmp_path):
    pair = tmp_path / ".pair"
    pair.mkdir()
    (pair / "manifest.json").write_text(json.dumps({"steps": [
        {"id": "a", "title": "A"}, {"id": "b", "title": "B", "dependencies": ["a"]},
        {"id": "retired", "title": "Retired"},
    ], "validation": {"last_results": [{"status": "passed"}]}}))
    (pair / "progress.json").write_text(json.dumps({"phase": "guided_reconstruction", "steps": {
        "a": {"status": "completed", "origin": "mixed"}, "retired": {"status": "superseded"},
    }, "knowledge": {"covered": ["parsing"], "revisit": ["recovery"]}}))
    snapshot = collect_dashboard(pair)

    assert snapshot.total_steps == 2
    assert snapshot.completed_steps == 1
    assert snapshot.plan[1].readiness == "ready"
    assert snapshot.ownership["counts"]["mixed"] == 1
    assert snapshot.knowledge["revisit"] == ["recovery"]
    assert snapshot.validation["status"] == "passed"


def test_malformed_dependency_list_is_not_treated_as_ready(canonical_pair):
    (canonical_pair / "manifest.yaml").write_text('steps:\n  - id: a\n    title: A\n    dependencies: missing\n')
    snapshot = collect_dashboard(canonical_pair)
    assert snapshot.graph["errors"]
    assert snapshot.plan[0].readiness == "unknown"


def test_missing_progress_does_not_become_zero_percent(canonical_pair):
    (canonical_pair / "progress.yaml").unlink()
    snapshot = collect_dashboard(canonical_pair)
    assert snapshot.progress_known is False
    assert all(step.status == "unknown" for step in snapshot.plan)
    from scripts.dashboard.renderer import _render_html
    content = _render_html(snapshot)
    assert 'class="completion">—' in content
    assert "completion is unknown" in content
    assert '<progress ' not in content


def test_active_step_with_unmet_prerequisite_is_not_suggested_for_continuation():
    plan = [PlanItem("a", "A"), PlanItem("b", "B", "active", dependencies=["a"])]
    graph = analyze_plan(plan)
    assert plan[1].status == "active"
    assert plan[1].readiness == "waiting"
    actions = workflow_actions({}, {"phase": "guided_reconstruction", "current_step": "b"}, plan, graph, {"status": "unknown"}, [])
    assert actions[0]["command"] == "/pair status"
    assert "prerequisites" in actions[0]["title"]


def test_missing_current_step_is_reported_as_metadata_drift():
    plan = [PlanItem("a", "A")]
    graph = analyze_plan(plan)
    actions = workflow_actions({}, {"phase": "guided_reconstruction", "current_step": "missing"}, plan, graph, {"status": "unknown"}, [])
    assert actions[0]["kind"] == "recovery"
