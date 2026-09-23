# Codex adapter

## Discovery

Use the portable Agent Skills location:

```text
# project-local
.agents/skills/pair-programming/

# user-level
~/.agents/skills/pair-programming/
```

The project-local `.agents/skills/` convention matches current OpenAI repository skill
practice and keeps this workflow portable to other Agent Skills-compatible hosts.

Keep `SKILL.md`, `reference/`, `templates/`, and `examples/` together so relative
references remain valid.

## Invocation

```text
$pair-programming plan add capability registry
$pair-programming next
$pair-programming review
$pair-programming hint step 2
$pair-programming take tests
$pair-programming status
```

These host-native calls map to the internal `/pair ...` semantic protocol.

## Install

```bash
bash scripts/install.sh codex
bash scripts/install.sh codex --scope user
```

```powershell
.\scripts\install.ps1 codex
.\scripts\install.ps1 codex -Scope user
```

Keep always-on repository rules in `AGENTS.md`; keep this workflow in an on-demand skill.
