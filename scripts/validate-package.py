#!/usr/bin/env python3
from __future__ import annotations

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
    "reference/pitfall-journal.md",
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
    "examples/example-session.md",
    "adapters/README.md",
    "adapters/codex.md",
    "adapters/claude-code.md",
    "adapters/opencode.md",
    "adapters/github-copilot.md",
    "adapters/gemini-cli.md",
    "adapters/cursor.md",
    "scripts/install.sh",
    "scripts/install.ps1",
]

COMMANDS = [
    "plan", "next", "review", "hint", "explain",
    "show", "take", "challenge", "status", "rebase-plan",
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

description_match = re.search(
    r"(?ms)^description:\s*>\s*\n(?P<body>(?:^[ \t]+.*\n?)+)",
    frontmatter,
)
if not description_match:
    fail("frontmatter must contain a folded description")
description = " ".join(line.strip() for line in description_match.group("body").splitlines()).strip()
if not description:
    fail("description is empty")
if len(description) > 1024:
    fail(f"description exceeds 1024 characters: {len(description)}")
if "compatibility:" not in frontmatter:
    fail("frontmatter is missing compatibility")
if 'opencode/slash: "true"' not in frontmatter:
    fail('frontmatter must expose the skill in OpenCode slash catalog')

example = (ROOT / "examples/example-session.md").read_text(encoding="utf-8")
for cmd in COMMANDS:
    semantic = f"/pair {cmd}"
    if semantic not in text:
        fail(f"SKILL.md is missing semantic command: {semantic}")
    if semantic not in example:
        fail(f"example session is missing command coverage: {semantic}")

for invocation in ("$pair-programming plan", "/pair-programming plan"):
    if invocation not in text:
        fail(f"SKILL.md is missing host invocation example: {invocation}")

install_sh = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")
for platform in ("portable", "codex", "cursor", "gemini-cli", "github-copilot", "claude-code", "opencode"):
    if platform not in install_sh:
        fail(f"install.sh is missing platform: {platform}")

print("pair-programming package validation passed")
print(f"  skill: {name}")
print(f"  description chars: {len(description)}")
print("  adapters: codex, cursor, gemini-cli, github-copilot, claude-code, opencode")
print(f"  semantic commands checked: {len(COMMANDS)}")
