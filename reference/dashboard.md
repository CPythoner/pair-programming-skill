# Pair Dashboard

## `/pair dashboard`

The dashboard command is a read-only observability command.

It must not modify Human source code or implementation state.

Behavior:

1. Read existing `.pair/` state.
2. Collect session, plan, history, and pitfall information.
3. Generate dashboard artifacts.

Default output:

```text
.pair/dashboard/
├── index.html
└── data.json
```

Supported options:

- JSON export only
- custom `.pair` directory
- custom output directory

The dashboard is a view of Pair state, not an alternative state store.
