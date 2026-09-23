# GitHub Copilot adapter

## Discovery

Portable project and user locations:

```text
# project-local
.agents/skills/pair-programming/

# user-level
~/.agents/skills/pair-programming/
```

Copilot-native locations:

```text
# project-local
.github/skills/pair-programming/

# user-level
~/.copilot/skills/pair-programming/
```

GitHub Copilot supports Agent Skills in Copilot cloud agent, code review, Copilot CLI,
Copilot app, and VS Code agent mode.

Use `.agents/skills/` by default when you want the same project skill shared with other
Agent Skills-compatible hosts.

## Invocation

Copilot may select the skill automatically from its name and description. To request it
explicitly, mention the slash-prefixed skill name in the prompt, for example:

```text
Use the /pair-programming skill to run: /pair plan add capability registry
Use the /pair-programming skill to run: /pair review
```

In Copilot CLI, use `/skills list` and `/skills info pair-programming` to inspect the
loaded skill.

## Install

Portable-first:

```bash
bash scripts/install.sh github-copilot
```

Copilot-native:

```bash
bash scripts/install.sh github-copilot --native
```

User-level:

```bash
bash scripts/install.sh github-copilot --scope user
bash scripts/install.sh github-copilot --scope user --native
```
