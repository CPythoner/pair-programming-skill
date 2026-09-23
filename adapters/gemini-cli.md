# Gemini CLI adapter

## Discovery

Portable locations:

```text
# workspace
.agents/skills/pair-programming/

# user
~/.agents/skills/pair-programming/
```

Gemini-native locations:

```text
# workspace
.gemini/skills/pair-programming/

# user
~/.gemini/skills/pair-programming/
```

Gemini CLI officially treats `.agents/skills/` as an alias for `.gemini/skills/`.
Within the same tier, the portable `.agents/skills/` alias has precedence.

Use the portable location by default so one installation can also serve other compatible
coding agents.

## Activation

Gemini CLI discovers skill metadata at session start and activates matching skills through
its native skill activation flow.

A direct custom `/pair-programming` slash command is not assumed here. To explicitly steer
Gemini, use natural language such as:

```text
Use the pair-programming skill. Run the semantic command: /pair plan add capability registry
```

Useful Gemini management commands:

```text
/skills list
/skills reload
/skills enable pair-programming
```

Gemini CLI also provides terminal-level skill management such as `gemini skills install`
and `gemini skills link`.

## Install

Portable-first:

```bash
bash scripts/install.sh gemini-cli
```

Gemini-native:

```bash
bash scripts/install.sh gemini-cli --native
```

User-level:

```bash
bash scripts/install.sh gemini-cli --scope user
bash scripts/install.sh gemini-cli --scope user --native
```
