# OpenCode adapter

## Discovery

Native OpenCode locations:

```text
# project-local
.opencode/skills/pair-programming/

# user-level
~/.config/opencode/skills/pair-programming/
```

OpenCode also discovers compatible definitions from:

```text
.agents/skills/pair-programming/
.claude/skills/pair-programming/
```

Therefore a repository-local Codex installation in `.agents/skills/` can also be visible
to OpenCode without a second copy. Use the native `.opencode/skills/` path when OpenCode
is the intended owner of the installation or when you want OpenCode-specific precedence.

## Slash catalog

The canonical `SKILL.md` includes:

```yaml
metadata:
  opencode/slash: "true"
```

This explicitly exposes the skill in OpenCode's slash-command catalog while keeping the
same portable skill body for the other hosts.

The skill ID is `pair-programming`, matching the directory name and canonical lowercase
kebab-case `name`.

## Invocation

```text
/pair-programming plan add capability registry
/pair-programming next
/pair-programming review
/pair-programming hint step 2
/pair-programming take tests
/pair-programming status
```

OpenCode can also load it automatically through the native skill tool when its description
matches the task.

## Install

```bash
bash scripts/install.sh opencode
bash scripts/install.sh opencode --scope user
```

```powershell
.\scripts\install.ps1 opencode
.\scripts\install.ps1 opencode -Scope user
```

If the skill is not visible, check the selected agent's `skill` permission, source
precedence, and whether another source defines the same ID later.
