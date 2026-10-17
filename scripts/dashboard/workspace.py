"""Bounded workspace discovery with independent project read failures."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .collector import collect_dashboard
from .model import WorkspaceProject, WorkspaceSnapshot


def project_paths(workspace: Path) -> list[Path]:
    workspace = Path(workspace)
    if not workspace.is_dir():
        raise ValueError(f"Workspace directory does not exist: {workspace}")
    return sorted(
        child for child in workspace.iterdir()
        if not child.name.startswith(".") and child.name not in {"node_modules", "vendor", "venv"}
        and not child.is_symlink() and child.is_dir()
        and (child / ".pair").is_dir() and not (child / ".pair").is_symlink()
    )


def collect_workspace(workspace: Path) -> WorkspaceSnapshot:
    workspace = Path(workspace).resolve()
    projects = []
    for path in project_paths(workspace):
        artifact_dir = "projects/" + hashlib.sha256(path.name.encode()).hexdigest()[:24]
        project = WorkspaceProject(path.name, str(path), artifact_dir)
        try:
            project.snapshot = collect_dashboard(path / ".pair")
            project.snapshot.workspace_link = "../../index.html"
        except (OSError, ValueError) as exc:
            project.error = str(exc)
        projects.append(project)
    return WorkspaceSnapshot(root=str(workspace), projects=projects)
