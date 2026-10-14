# Pair Dashboard

## `/pair dashboard`

The dashboard command is a read-only observability command.

It must not modify Human source code, implementation state, Git branches, or Pair workflow state.

The dashboard is a projection of existing Pair state, not an alternative state store.

## Input

Read existing Pair state only:

```text
.pair/
├── manifest.yaml
├── progress.yaml
├── design.md
├── pitfalls.yaml
├── sessions/
├── operations/
└── checkpoints/
```

Do not initialize or rewrite `.pair` state only for dashboard generation.

Read canonical YAML first; legacy JSON snapshots may be used only when the corresponding
YAML file is absent. Use manifest steps for the reference plan and progress steps for
actual completion. Read Markdown session summaries from `sessions/`; label file-mtime
timestamps as such. Missing state must remain visible, and unsupported schema versions
or malformed structured state must report a generation error.

## Runtime entrypoint

Normalize `$pair-programming dashboard` and `/pair-programming dashboard` to
`/pair dashboard`. Resolve the generator from the loaded skill directory, then execute
from the user's project root:

```bash
python3 /absolute/path/to/pair-programming/scripts/dashboard/main.py
```

Use Python 3.10+ and the YAML dependency declared in
`scripts/dashboard/requirements.txt`. For setup and CLI examples, read
`scripts/dashboard/README.md`. Report the generated artifact paths and allow the HTML
to be opened directly. Generation is available while design approval or recovery is
pending because it writes only dashboard projections.

## Generation contract

The implementation flow is:

```text
Read .pair state
        |
        v
Build DashboardSnapshot
        |
        +--> data.json
        |
        v
Render static HTML
        |
        v
Write assets
```

The implementation belongs to:

```text
scripts/dashboard/
```

Generated files belong to:

```text
.pair/dashboard/
```

Never create a top-level `dashboard/` source directory.

## Output contract

```text
.pair/dashboard/
├── index.html
├── data.json
└── assets/
    ├── style.css
    └── app.js
```

The output must open directly in a browser without npm, bundlers, or a build step.

## HTML requirements

Generated dashboard HTML must:

- be a static page;
- use local assets;
- avoid external runtime dependencies;
- work on desktop and mobile;
- represent Pair state without becoming another state source.

Example structure:

```html
<!doctype html>
<html>
<head>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <main id="dashboard"></main>
  <script src="assets/app.js"></script>
</body>
</html>
```

## Required sections

### Session

Show:

- project;
- phase;
- status;
- updated time.

### Progress

Show:

- total steps;
- completed steps;
- current step;
- step state.

### Plan

Visualize:

- completed;
- active;
- pending;
- blocked steps.

### Timeline

Use session history data.

Show:

- timestamp;
- event;
- actor;
- related step.

### Pitfalls

Read `pitfalls.yaml`.

Show:

- title;
- severity;
- affected scope;
- resolution.

## Options

Supported implementations may provide:

- JSON-only export;
- custom `.pair` directory;
- custom output directory.

## Future extensions

Watch mode, ownership metrics, graphs, and workspace dashboards must remain views over Pair state and must not introduce another source of truth.
