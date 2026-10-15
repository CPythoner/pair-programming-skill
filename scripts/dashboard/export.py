"""Write dashboard projections without changing their source state."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile

from .model import DashboardSnapshot, WorkspaceSnapshot
from .renderer import render_dashboard, render_workspace


def _write_json(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def export_json(snapshot: DashboardSnapshot | WorkspaceSnapshot, output: Path) -> None:
    _write_json(snapshot.to_dict(), output)


def export_html(snapshot: DashboardSnapshot, output: Path) -> None:
    render_dashboard(snapshot, output)


def _export_history(snapshot: DashboardSnapshot, output: Path) -> None:
    if (output / "history").is_symlink():
        raise ValueError("Generated history must be a directory, not a symbolic link")
    expected = set()
    for session in snapshot.sessions:
        if session.get("history_file"):
            filename = Path(session["history_file"]).name
            if not re.fullmatch(r"session-[a-f0-9]{64}\.json", filename):
                raise ValueError("Invalid generated history filename")
            expected.add(filename)
            _write_json(session, output / "history" / filename)
    history = output / "history"
    if history.is_dir():
        for path in history.glob("session-*.json"):
            if re.fullmatch(r"session-[a-f0-9]{64}\.json", path.name) and path.name not in expected:
                path.unlink()


def export_dashboard(snapshot: DashboardSnapshot | WorkspaceSnapshot, output: Path, json_only: bool = False) -> None:
    if isinstance(snapshot, WorkspaceSnapshot):
        for project in snapshot.projects:
            project_output = output / project.artifact_dir
            if project.snapshot is not None:
                export_dashboard(project.snapshot, project_output, json_only)
            elif project.error:
                # Replace a previous detail page too; an open page must not keep
                # presenting old counts as fresh after its overview reports failure.
                unavailable = DashboardSnapshot(
                    project=project.name, status="attention_required", progress_known=False,
                    generated_at=snapshot.generated_at, workspace_link="../../index.html",
                    freshness={**snapshot.freshness, "state": "unavailable", "error": project.error},
                    actions=[{"kind": "source", "title": "Resolve source read error", "detail": "Progress cannot be verified until source records are readable.", "command": "/pair status"}],
                )
                # Failure does not prove that previously exported sessions were removed.
                export_json(unavailable, project_output / "data.json")
                if not json_only:
                    export_html(unavailable, project_output / "index.html")
        export_json(snapshot, output / "data.json")
        if not json_only:
            render_workspace(snapshot, output / "index.html")
    else:
        _export_history(snapshot, output)
        export_json(snapshot, output / "data.json")
        if not json_only:
            export_html(snapshot, output / "index.html")
