# Claude Code adapter

## Discovery

Install the complete skill directory at:

```text
# project-local
.claude/skills/pair-programming/

# user-level
~/.claude/skills/pair-programming/
```

Keep `SKILL.md`, `reference/`, `templates/`, and `examples/` together so relative
references remain valid.

## Invocation

```text
/pair-programming plan add capability registry
/pair-programming next
/pair-programming review
/pair-programming hint step 2
/pair-programming take tests
/pair-programming status
```

Trailing arguments are normalized to the internal `/pair ...` semantic protocol.

## Install

```bash
bash scripts/install.sh claude-code
bash scripts/install.sh claude-code --scope user
```

```powershell
.\scripts\install.ps1 claude-code
.\scripts\install.ps1 claude-code -Scope user
```

Use `CLAUDE.md` for guidance that should load every session; keep this multi-step workflow
as an on-demand skill.
