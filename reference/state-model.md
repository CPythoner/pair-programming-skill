# State Model

Pair Programming uses explicit, versioned persistent state under `.pair/`.

Canonical schema definitions live in `schemas/`. Current `schema_version` is **1**.

Early state may use `version: 1`; readers may accept it as legacy schema version 1, but the
next write should canonicalize that file to `schema_version: 1`.

## `.pair/config.yaml`

User preferences and workflow defaults. Avoid rewriting it unless configuration changes or
a schema migration is required.

Important sections now include:

- `takeover` — transactional takeover behavior;
- `recovery` — session reconciliation policy;
- `guide_quality` — Guide commit quality requirements.

Schema: `schemas/config.schema.json`.

## `.pair/design.md`

Canonical implementation design for the current feature.

If `/pair plan` receives only a feature goal or incomplete design, create this document
and wait for explicit approval before creating Shadow or implementing source code.

Approval is revision-scoped. Implementation is permitted only when
`status == approved` and `approved_revision == revision`.

## `.pair/manifest.yaml`

Describes the feature and the verified reference plan:

- feature goal / acceptance criteria;
- design revision and approval evidence;
- repository baseline;
- Shadow solution and Guide refs;
- Guide steps;
- validation;
- Pitfall mappings;
- Guide quality result;
- risks / decisions.

Manifest is planned/reference truth. It does not prove Human Workspace has completed a step.

Schema: `schemas/manifest.schema.json`.

## `.pair/progress.yaml`

Describes actual Human Workspace progress.

It tracks:

- workflow phase;
- Human branch/observed HEAD;
- latest workspace snapshot;
- recovery classification;
- active operation;
- current step;
- per-step status and origin;
- divergences;
- knowledge coverage;
- Pitfall communication state;
- latest session.

Schema: `schemas/progress.schema.json`.

## `.pair/pitfalls.yaml`

Canonical structured journal of meaningful failures and hidden constraints discovered in
Shadow or later validation.

Pitfalls include stable IDs, evidence/confidence, contextual applicability, Guide mappings,
review assertions, teaching timing, and avoidance guidance.

Schema: `schemas/pitfalls.schema.json`.

## `.pair/operations/*.yaml`

Durable operation journal for Human Workspace mutations, initially takeover operations.

A takeover operation records:

- requested scope;
- selected strategy;
- checkpoint evidence;
- preflight dependencies/conflicts;
- applied files/symbols;
- validation;
- recovery classification;
- lifecycle status.

Only one non-terminal takeover should be active at a time.

Schema: `schemas/takeover-operation.schema.json`.

## `.pair/notes.md`

Stores design decisions and context that does not fit structured state well:

- why a design was selected;
- why a Shadow approach was rejected;
- repository constraints;
- important review discoveries;
- intentionally deferred work.

## `.pair/checkpoints/`

Recovery evidence created before takeover or other broad generated edits.

A checkpoint is not an alternate workspace and is never auto-restored.

## `.pair/sessions/`

Cross-session summaries. They support recovery but never override actual Git state.

## State consistency

Before a new Pair operation, especially any mutating operation:

1. validate supported schema versions;
2. resolve actual repo root;
3. compare Human branch/HEAD with progress;
4. inspect actual Git status/diff;
5. reconcile any active takeover first;
6. verify solution/Guide refs still exist;
7. verify current design approval revision;
8. verify current step dependencies;
9. update recovery classification and workspace snapshot.

Use `reference/recovery.md` for the decision table.

When Human Workspace and metadata conflict, Human Workspace is authoritative. Reconcile
metadata or re-plan. Never reset Human code merely to satisfy state files.
