from pathlib import Path

import pytest


@pytest.fixture
def canonical_pair(tmp_path: Path) -> Path:
    pair = tmp_path / "project" / ".pair"
    pair.mkdir(parents=True)
    (pair / "manifest.yaml").write_text(
        """schema_version: 1
repository:
  name: demo
steps:
  - id: design
    title: Design
    status: completed
  - id: parser
    title: Parser
  - id: tests
    title: Tests
""",
        encoding="utf-8",
    )
    (pair / "progress.yaml").write_text(
        """schema_version: 1
phase: guided_reconstruction
current_step: parser
steps:
  design:
    status: completed
  parser:
    status: active
""",
        encoding="utf-8",
    )
    (pair / "pitfalls.yaml").write_text(
        """schema_version: 1
pitfalls:
  - id: P001
    title: Missing entrypoint
    severity: high
    symptom: Cannot open dashboard
    affected_files: [scripts/dashboard/main.py]
    affected_symbols: [main]
    resolution: Package the generator
""",
        encoding="utf-8",
    )
    sessions = pair / "sessions"
    sessions.mkdir()
    (sessions / "2026-10-15.md").write_text(
        "# Pair Session Summary\n\n## State\n\n- Current step: parser\n",
        encoding="utf-8",
    )
    return pair
