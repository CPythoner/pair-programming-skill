# Pair Dashboard

## `/pair dashboard`

The dashboard command is a read-only observability command.

It must not modify Human source code, implementation state, Git branches, or Pair workflow state.

The dashboard is a projection of existing Pair state, not an alternative state store.

## Input

Read only the existing project state:

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

Do not create missing Pair state only for dashboard generation.

## Generation pipeline

The implementation must follow this flow:

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
Write dashboard assets
```

The renderer implementation lives under:

```text
scripts/dashboard/
```

The generated artifacts live under:

```text
.pair/dashboard/
```

Never create a top-level `dashboard/` directory.

## Output contract

Default output:

```text
.pair/dashboard/
├── index.html
├── data.json
└── assets/
    ├── style.css
    └── app.js
```

The generated dashboard must open directly in a browser without a build step.

## HTML generation requirements

The generated page must:

- be a static HTML application;
- avoid npm/build dependencies;
- use local assets only;
- remain readable on desktop and mobile;
- preserve the relationship between Pair state and rendered information.

Expected structure:

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

## Required dashboard sections

### Session

Display:

- project name;
- current phase;
- current status;
- last update time.

### Progress

Display:

- total steps;
- completed steps;
- current step;
- step status.

### Plan

Visualize the implementation plan:

- completed steps;
- active step;
- pending steps;
- blocked steps.

### Timeline

Read historical events from sessions/history data.

Display:

- timestamp;
- event;
- actor;
- related step.

### Pitfalls

Read `pitfalls.yaml`.

Display:

- pitfall title;
- severity;
- affected scope;
- resolution.

## Supported options

- JSON export only;
- custom `.pair` directory;
- custom output directory.

## Future extensions

Enhancements may add:

- watch mode;
- multi-project overview;
- ownership metrics;
- richer graphs.

These must remain views over Pair state and must not introduce another source of truth.
