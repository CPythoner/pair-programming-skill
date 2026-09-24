# Session and Crash Recovery

Pair Programming state is durable, but Git is the source of truth for Human Workspace.
Every substantial new session starts with recovery reconciliation before continuing work.

No new command is required. Natural-language "continue", `/pair status`, and any mutating
`/pair` command run this check when recovery is enabled.

## Schema gate

Read `schema_version` from:

- `.pair/config.yaml`;
- `.pair/manifest.yaml`;
- `.pair/progress.yaml`;
- `.pair/pitfalls.yaml`;
- active `.pair/operations/*.yaml`.

Current supported schema version is `1`.

Legacy early files may contain `version: 1`. They may be read as schema version 1, but the
next write should canonicalize that file to `schema_version: 1`.

If state has a newer unsupported schema version, stop rather than guessing.

## Recovery inputs

Read:

1. manifest;
2. progress;
3. latest session summary;
4. active operation, if any;
5. actual repo root;
6. current Human branch and HEAD;
7. `git status --porcelain=v1`;
8. current staged/unstaged diff summary;
9. existence of solution/guide refs;
10. current design approval revision.

Never trust metadata without comparing it to Git.

## Classification

Classify the workspace before continuing.

### clean_match

Expected branch/HEAD and workspace state match recorded state.

Action: continue normally.

### expected_dirty

HEAD matches and dirty paths are consistent with the current Human step or recorded active
operation.

Action: preserve the dirty work and continue from the relevant checkpoint.

### metadata_stale

Git contains expected completed work, but progress/session metadata is behind and there is
no conflicting drift.

Action: update metadata to observed truth. Do not rewrite source code.

### head_advanced_reconcilable

Human branch advanced independently, but inspection shows the new commits do not invalidate
current feature state or active step.

Action: record the new observed HEAD, update divergence notes where useful, and continue.

### interrupted_takeover

`progress.active_operation` points to a non-terminal takeover.

Action: run the takeover reconciliation procedure from `reference/takeover.md` before any
new source modification.

### reference_missing

Recorded solution/guide ref is missing.

Action: do not fabricate the reference. Recreate a disposable checkout from an existing
recorded commit/ref when possible; otherwise use `/pair rebase-plan` to regenerate the
remaining reference.

### unknown_drift

Branch/HEAD/diff changed in a way that cannot be explained safely from recorded state.

Action: set recovery state to `attention_required`, explain the mismatch, and stop
automatic mutation. Human Workspace stays authoritative.

## Recovery output

Record:

```yaml
recovery:
  state: clean
  checked_at: "..."
  classification: clean_match
  reasons: []
```

Also refresh `workspace_snapshot` after successful reconciliation.

For `attention_required`, record concrete reasons rather than a generic "state mismatch".

## Session summaries

At the end of a substantial session, write:

```text
.pair/sessions/YYYYMMDD-HHMM.md
```

Include:

- Human branch/HEAD/status;
- current step;
- active operation;
- recovery classification;
- changes made;
- validation results;
- decisions/divergences;
- pitfalls surfaced/discussed;
- next concrete action.

Update `progress.last_session` only after the summary is written.

## Safety rules

Recovery never means "restore metadata's preferred code".

Do not automatically:

- reset Human Workspace;
- clean untracked files;
- discard staged/unstaged edits;
- switch branches over local changes;
- replay an uncertain takeover patch;
- delete or recreate references merely because metadata expects them.

When metadata and Human Workspace disagree, preserve Human Workspace and reconcile the
metadata or re-plan.
