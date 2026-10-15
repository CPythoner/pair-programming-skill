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
├── history/                 # Rebuildable session metadata exports
├── projects/                # Workspace mode: per-project detail artifacts
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

## Watch mode

```bash
python3 /absolute/path/to/pair-programming/scripts/dashboard/main.py --watch
```

The corresponding semantic invocation is `/pair dashboard --watch`.
Use `watch_dashboard()` in `scripts/dashboard/watch.py`. Generate once, then poll with
`pathlib` and the Python standard library, without a watchdog dependency.

Monitor `manifest.yaml`, `progress.yaml`, `pitfalls.yaml`, and `sessions/*.md`, plus
legacy `.json` state, `events.jsonl`, structured session metadata, and `operations/*.yaml`. Detect creation, deletion, content changes, and
modification time changes. Exclude generated dashboard files and unrelated Pair state
so output writes never trigger another generation.

On changes, report affected input paths, current-step transitions, and successful
refreshes. Coalesce changes found in the same poll into one generation. Use a positive,
finite `--interval` in seconds (default: 1). Preserve `--json`, `--pair-dir`, and `--output`
semantics. Ctrl-C stops cleanly without a traceback.

If an input is malformed during a write, keep the last valid business values and continue
retrying. Suppress repeated identical errors until recovery or a different error.
Publish a stale warning with the error and last successful generation time; freshness
metadata may change without replacing those business values.
Watch updates static files; reload an open HTML page to display the refreshed state.
The mode does not start a web server or modify Pair source state.

## P2 derived views

- What needs attention: pending design revision, recovery attention, non-terminal takeover,
  recorded validation failures, dependency errors, and next-ready/current-step commands.
  Commands are suggestions only. Guided-step suggestions require guided reconstruction.
- Graph: `manifest.steps.dependencies` defines edges; `progress.steps` defines observed
  status. Derive readiness/blocked_by without adding a persisted `blocked` state. Missing
  IDs, duplicate IDs, and cycles are explicit errors. Unimplemented skipped/superseded
  dependencies do not satisfy prerequisites.
- Step completion: completed/done steps divided by active plan steps, excluding skipped
  and superseded entries. Missing progress state produces an unknown percentage.
- Implementation origin: counts/percentages of completed steps marked human, ai, mixed,
  or unknown, with explicit denominator and known-origin coverage. Takeover or Git actor
  records do not imply whole-step ownership. Mixed is never divided into assumed shares.
- Validation: only explicit `manifest.validation.last_results[*].status` records establish
  passed/failed/limited evidence. Commands and completion ratios do not prove validation.
- Knowledge: show recorded covered/revisit topics; do not convert coverage to understanding.

## Session history

Read `sessions/*.md` frontmatter, `*.yaml`, and `*.json` using `schemas/session.schema.json`.
The Pair workflow records stable IDs, feature/title, timezone-aware start/end times, and
session outcome at the time of the session. Legacy Markdown has unknown real times and
outcome; its file-mtime timeline entries are labeled.

Export `history/session-<stable-id-hash>.json`; repeated generations update the same
session, not a new session. The same day may contain many sessions. Duplicate IDs disable
conflicting exports and show warnings. Only files matching the generated history naming
contract are pruned after source deletion; unrelated output files are preserved.
History is source-session metadata, not an invented snapshot of past code or progress.

## Workspace overview

```text
/pair dashboard --workspace ~/workspace
/pair dashboard --workspace ~/workspace --watch
```

Scan direct child directories with `.pair`; skip hidden directories, node_modules/vendor/venv,
and symbolic links. Defaults to `<workspace>/.pair/dashboard`, with safe hashed per-project
artifact directories, a project list, detail links, and independent read errors. Missing or
unreadable progress stays unknown. Do not calculate cross-project average completion.
Workspace Watch detects project creation/removal and consumed source changes.

All views remain projections of Pair source state and never become another source of truth.
