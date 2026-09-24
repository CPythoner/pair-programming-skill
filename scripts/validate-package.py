#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "SKILL.md"

REQUIRED_FILES = [
    "SKILL.md",
    "reference/command-protocol.md",
    "reference/decomposition.md",
    "reference/design-gate.md",
    "reference/guide-quality.md",
    "reference/pitfall-journal.md",
    "reference/recovery.md",
    "reference/review-rubric.md",
    "reference/state-model.md",
    "reference/takeover.md",
    "templates/config.yaml",
    "templates/design.md",
    "templates/manifest.yaml",
    "templates/notes.md",
    "templates/pitfalls.yaml",
    "templates/progress.yaml",
    "templates/session-summary.md",
    "templates/takeover-operation.yaml",
    "schemas/README.md",
    "schemas/config.schema.json",
    "schemas/manifest.schema.json",
    "schemas/progress.schema.json",
    "schemas/pitfalls.schema.json",
    "schemas/takeover-operation.schema.json",
    "examples/example-session.md",
    "adapters/README.md",
    "adapters/codex.md",
    "adapters/claude-code.md",
    "adapters/opencode.md",
    "adapters/github-copilot.md",
    "adapters/gemini-cli.md",
    "adapters/cursor.md",
    "scripts/check-guide.py",
    "scripts/install.sh",
    "scripts/install.ps1",
]

COMMANDS = [
    "plan", "next", "review", "hint", "explain",
    "show", "take", "challenge", "status", "rebase-plan",
]

SCHEMA_FILES = [
    "schemas/config.schema.json",
    "schemas/manifest.schema.json",
    "schemas/progress.schema.json",
    "schemas/pitfalls.schema.json",
    "schemas/takeover-operation.schema.json",
]

VERSIONED_TEMPLATES = [
    "templates/config.yaml",
    "templates/manifest.yaml",
    "templates/progress.yaml",
    "templates/pitfalls.yaml",
    "templates/takeover-operation.yaml",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


for rel in REQUIRED_FILES:
    if not (ROOT / rel).is_file():
        fail(f"missing required file: {rel}")

text = SKILL.read_text(encoding="utf-8")
if not text.startswith("---\n"):
    fail("SKILL.md must start with YAML frontmatter")
end = text.find("\n---\n", 4)
if end < 0:
    fail("SKILL.md frontmatter is not closed")
frontmatter = text[4:end]

name_match = re.search(r"(?m)^name:\s*([^\n]+)$", frontmatter)
if not name_match:
    fail("frontmatter is missing name")
name = name_match.group(1).strip().strip("'\"")
if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
    fail(f"skill name is not portable kebab-case: {name}")
if name != "pair-programming":
    fail(f"unexpected skill name: {name}")

version_match = re.search(r'(?m)^\s{2}version:\s*["\']?([^"\'\n]+)', frontmatter)
if not version_match:
    fail("metadata.version is missing")
version = version_match.group(1).strip()
if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version):
    fail(f"metadata.version is not MAJOR.MINOR.PATCH: {version}")

description_match = re.search(
    r"(?ms)^description:\s*>\s*\n(?P<body>(?:^[ \t]+.*\n?)+)",
    frontmatter,
)
if not description_match:
    fail("frontmatter must contain a folded description")
description = " ".join(
    line.strip() for line in description_match.group("body").splitlines()
).strip()
if not description:
    fail("description is empty")
if len(description) > 1024:
    fail(f"description exceeds 1024 characters: {len(description)}")
if "compatibility:" not in frontmatter:
    fail("frontmatter is missing compatibility")
if 'opencode/slash: "true"' not in frontmatter:
    fail('frontmatter must expose the skill in OpenCode slash catalog')

for required_reference in (
    "reference/command-protocol.md",
    "reference/design-gate.md",
    "reference/decomposition.md",
    "reference/guide-quality.md",
    "reference/pitfall-journal.md",
    "reference/recovery.md",
    "reference/review-rubric.md",
    "reference/state-model.md",
    "reference/takeover.md",
    ".pair/operations/",
):
    if required_reference not in text:
        fail(f"SKILL.md is missing routed workflow reference: {required_reference}")

example = (ROOT / "examples/example-session.md").read_text(encoding="utf-8")
for command in COMMANDS:
    semantic = f"/pair {command}"
    if semantic not in text:
        fail(f"SKILL.md is missing semantic command: {semantic}")
    if semantic not in example:
        fail(f"example session is missing command coverage: {semantic}")

for invocation in ("$pair-programming plan", "/pair-programming plan"):
    if invocation not in text:
        fail(f"SKILL.md is missing host invocation example: {invocation}")

for rel in VERSIONED_TEMPLATES:
    template = (ROOT / rel).read_text(encoding="utf-8")
    if not re.search(r"(?m)^schema_version:\s*1\s*$", template):
        fail(f"{rel} must declare schema_version: 1")
    if re.search(r"(?m)^version:\s*1\s*$", template):
        fail(f"{rel} still uses legacy top-level version: 1")

for rel in SCHEMA_FILES:
    try:
        schema = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON schema {rel}: {exc}")
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail(f"{rel} must use JSON Schema draft 2020-12")
    if not schema.get("$id"):
        fail(f"{rel} is missing $id")
    properties = schema.get("properties", {})
    schema_version = properties.get("schema_version", {})
    if schema_version.get("const") != 1:
        fail(f"{rel} must pin schema_version to 1")

for rel in ("scripts/validate-package.py", "scripts/check-guide.py"):
    try:
        ast.parse((ROOT / rel).read_text(encoding="utf-8"), filename=rel)
    except SyntaxError as exc:
        fail(f"python syntax error in {rel}: {exc}")

install_sh = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")
install_ps = (ROOT / "scripts/install.ps1").read_text(encoding="utf-8")
for platform in (
    "portable", "codex", "cursor", "gemini-cli",
    "github-copilot", "claude-code", "opencode",
):
    if platform not in install_sh:
        fail(f"install.sh is missing platform: {platform}")
    if platform not in install_ps:
        fail(f"install.ps1 is missing platform: {platform}")

for runtime_component in ("schemas", "check-guide.py"):
    if runtime_component not in install_sh:
        fail(f"install.sh does not package runtime component: {runtime_component}")
    if runtime_component not in install_ps:
        fail(f"install.ps1 does not package runtime component: {runtime_component}")

print("pair-programming package validation passed")
print(f"  skill: {name}")
print(f"  version: {version}")
print(f"  description chars: {len(description)}")
print("  state schema version: 1")
print(f"  schemas checked: {len(SCHEMA_FILES)}")
print("  adapters: codex, cursor, gemini-cli, github-copilot, claude-code, opencode")
print(f"  semantic commands checked: {len(COMMANDS)}")
