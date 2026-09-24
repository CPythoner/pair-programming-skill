# Selective Takeover

`/pair take` is a first-class workflow, not a failure state. It is also the operation most
likely to modify Human Workspace, so it uses a transaction-like protocol.

The goals are:

- preserve existing Human work;
- apply only the requested semantic scope;
- make interruption detectable and recoverable;
- avoid replaying an already-applied change;
- leave enough evidence to explain exactly what happened.

## Supported scopes

- step
- file
- symbol
- tests
- build
- dependencies
- tooling
- remaining
- all

## Operation journal

Every takeover creates an operation file before source modification:

```text
.pair/operations/<operation-id>.yaml
```

Initialize it from `templates/takeover-operation.yaml`.

Record the active operation in `.pair/progress.yaml`:

```yaml
active_operation:
  id: T20260924-001
  path: ".pair/operations/T20260924-001.yaml"
  kind: takeover
  status: prepared
```

Takeover status transitions:

```text
prepared
   ↓
applying
   ↓
applied
   ↓
validating
   ↓
completed
```

Interruption or ambiguity may transition to:

```text
interrupted
needs_reconciliation
abandoned
```

Never start a second takeover while a non-terminal takeover exists. Reconcile the current
operation first.

## Preflight

Before modifying Human Workspace:

1. resolve repo root and current branch;
2. verify the requested scope and current Guide dependency state;
3. inspect staged, unstaged, and relevant untracked work;
4. identify Human changes overlapping the requested scope;
5. map relevant Shadow pitfalls using step, file, symbol, and current context;
6. choose the smallest safe application strategy;
7. create a recovery checkpoint;
8. write the operation journal with status `prepared`;
9. set `progress.active_operation`.

If the requested scope is ambiguous, dependency prerequisites are missing, or Human changes
make the intended delta unclear, stop before source modification and explain the conflict.

## Recovery checkpoint

Create:

```text
.pair/checkpoints/<operation-id>/
```

At minimum capture:

- current branch;
- current HEAD;
- `git status --porcelain=v1`;
- staged diff;
- unstaged binary diff;
- relevant untracked file list;
- copies of relevant untracked files when practical.

Store the evidence paths in the operation journal.

The checkpoint is evidence for recovery. Do not automatically restore it.

## Choose application mode

### Semantic port — preferred

Use when Human implementation differs from Guide.

Read the intent of the reference delta, then implement that intent against current Human
code. Apply known pitfall avoidance while porting.

### Cherry-pick Guide commit

Use only when:

- the whole guide step is requested;
- current state matches the expected predecessor;
- dependencies are satisfied;
- no unrelated Human changes overlap.

### 3-way patch

Use when source is close but not commit-aligned and the conflict surface is small.

### Manual adaptation

Use when:

- symbol-level takeover;
- file has significant Human edits;
- API shape changed;
- re-plan has diverged;
- automated application would obscure Human intent.

## Apply protocol

Immediately before the first source edit, set status to `applying`.

During application:

- touch only the requested scope and necessary prerequisites;
- preserve unrelated Human edits;
- record changed files/symbols;
- record adaptations from the reference;
- do not mark the operation completed just because the patch applied.

After the intended code is present:

1. save a post-apply diff under the operation/checkpoint evidence;
2. set status to `applied`;
3. verify current files against the requested semantic scope;
4. set status to `validating`;
5. run focused validation, then broader validation when proportionate;
6. store commands/results;
7. update step origin to `ai` or `mixed`;
8. update pitfall communication state;
9. set status to `completed`;
10. clear `progress.active_operation`;
11. return control to Human mode.

## Interruption and idempotent resume

On a later session, a non-terminal operation must be reconciled before any new takeover.

Compare:

- checkpoint branch/HEAD;
- current branch/HEAD;
- checkpoint diff/status;
- operation changed-file list;
- current diff;
- post-apply evidence when present;
- validation status.

Classify the operation as one of:

### Not applied

No intended takeover delta is present. Resume from `prepared` after re-running preflight.

### Partially applied

Some intended changes exist but evidence shows the scope is incomplete. Mark
`needs_reconciliation`, identify what is already present, and semantic-port only the
missing behavior. Never replay the full patch blindly.

### Applied but not validated

The intended delta is present and no contradictory drift is found. Resume at validation;
do not apply the code again.

### Completed but metadata stale

Validation/evidence shows the takeover completed but metadata was not finalized. Reconcile
metadata only, then clear the active operation.

### Diverged / ambiguous

Current Human changes overlap or invalidate the recorded intent. Mark
`needs_reconciliation` and stop automatic application. Preserve Human Workspace and
explain the mismatch.

This classification is what makes takeover effectively idempotent across interrupted
sessions.

## Conflict policy

Never choose "theirs" for an entire file just because Shadow has a working version.

Preserve Human changes unless they contradict explicitly requested behavior. If a clean
automated application is impossible, use semantic/manual adaptation.

Do not use destructive reset/clean/checkout to force the workspace into the Guide state.

## Validation and completion

A takeover is not complete until one of these is recorded:

- `validation.status: passed`;
- `validation.status: limited` with the limitation explicitly documented.

A failed validation leaves the operation active until the failure is fixed, intentionally
abandoned, or handed back to the user with `needs_reconciliation`.

## `take remaining` and `take all`

These are explicit requests for autonomous completion, but they do not waive safety rules.

Still:

- create one operation journal;
- checkpoint Human work first;
- treat current Human code as authoritative source state;
- apply only missing behavior;
- preserve relevant divergences;
- validate;
- provide architecture and diff walkthrough;
- return control unless the user explicitly requested continued autonomy.
