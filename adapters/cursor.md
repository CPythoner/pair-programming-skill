# Cursor adapter

## Discovery

Portable locations:

```text
# project-local
.agents/skills/pair-programming/

# user-level
~/.agents/skills/pair-programming/
```

Cursor-native locations:

```text
# project-local
.cursor/skills/pair-programming/

# user-level
~/.cursor/skills/pair-programming/
```

Cursor automatically discovers both `.agents/skills/` and `.cursor/skills/`. It can
also discover compatible Claude and Codex skill directories.

Use the portable location by default so the same checkout can be shared with Codex, Gemini
CLI, GitHub Copilot, and OpenCode.

Use `--native` only when you specifically want Cursor-owned placement, for example when
using Cursor's personal skill synchronization behavior.

## Invocation

Cursor may invoke the skill automatically from its description. It can also be selected
explicitly as a slash skill:

```text
/pair-programming plan add capability registry
/pair-programming next
/pair-programming review
/pair-programming hint step 2
/pair-programming take tests
/pair-programming status
```

The workflow keeps automatic invocation enabled; it does not set
`disable-model-invocation: true`.

## Install

Portable-first:

```bash
bash scripts/install.sh cursor
```

Cursor-native:

```bash
bash scripts/install.sh cursor --native
```

User-level:

```bash
bash scripts/install.sh cursor --scope user
bash scripts/install.sh cursor --scope user --native
```
