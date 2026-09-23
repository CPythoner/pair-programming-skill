# Native adapters

Pair Programming Skill keeps one canonical `SKILL.md` package. Adapters only define how
each host discovers and invokes that package.

| Host | Default project path | Default user path | Host-native alternative |
|---|---|---|---|
| Portable Agent Skills | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | — |
| Codex | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | — |
| Cursor | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | `.cursor/skills/` |
| Gemini CLI | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | `.gemini/skills/` |
| GitHub Copilot | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | `.github/skills/`, `~/.copilot/skills/` |
| Claude Code | `.claude/skills/pair-programming/` | `~/.claude/skills/pair-programming/` | — |
| OpenCode | `.opencode/skills/pair-programming/` | `~/.config/opencode/skills/pair-programming/` | also reads `.agents/skills/`, `.claude/skills/` |

The workflow itself still has one source of truth:

```text
SKILL.md
reference/
templates/
examples/
```

## Portable-first strategy

For hosts that support the Agent Skills standard directly, prefer:

```text
.agents/skills/pair-programming/
```

This lets one project-local installation serve multiple compatible hosts without duplicating
the skill.

Current portable-first hosts in this repository:

```text
Codex
Cursor
Gemini CLI
GitHub Copilot
OpenCode (compatible discovery)
```

Claude Code keeps its own native `.claude/skills/` path.

## Host-specific invocation

The workflow's internal semantic protocol is always:

```text
/pair plan
/pair next
/pair review
/pair hint
/pair explain
/pair show
/pair take
/pair challenge
/pair status
/pair rebase-plan
```

Host activation differs:

- Codex: `$pair-programming <command> ...`
- Cursor: `/pair-programming <command> ...`
- Claude Code: `/pair-programming <command> ...`
- OpenCode: `/pair-programming <command> ...`
- Gemini CLI: activate/select the skill, then provide the semantic `/pair ...` intent
- GitHub Copilot: explicitly mention `/pair-programming` in the prompt when deterministic activation is desired

## Installers

Portable shared install:

```bash
bash scripts/install.sh portable
```

Host-aware install:

```bash
bash scripts/install.sh <codex|cursor|gemini-cli|github-copilot|claude-code|opencode>
```

Use `--native` for Cursor, Gemini CLI, or GitHub Copilot when you want the host-specific
directory instead of `.agents/skills/`.

Existing installations are never overwritten unless force overwrite is explicitly requested.
