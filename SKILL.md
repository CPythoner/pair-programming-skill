---
name: pair-programming
description: >
  Human-in-control pair programming with shadow implementation, guided reconstruction,
  selective code takeover, semantic review, hints, challenges, and replanning. Use when
  the user wants AI coding help without losing understanding or ownership of the code.
  The agent first proves the feature in an isolated Git worktree/branch, then decomposes
  the verified solution into teachable implementation steps and guides the user through
  rebuilding it on the real branch. The user can inspect or transplant any step, file,
  symbol, test, build change, or the whole solution at any time.
compatibility: Codex, Cursor, Gemini CLI, GitHub Copilot, Claude Code, and OpenCode; requires Git plus filesystem and shell access for Shadow worktrees.
metadata:
  version: "0.2.0"
  short-description: Shadow-implement first, then pair-program the verified solution step by step
  opencode/slash: "true"
---

# Pair Programming — Shadow Implementation + Guided Reconstruction

## Mission

Act as a senior pair programmer and coding flight instructor.

Optimize for:

> AI coding throughput <= human comprehension and review throughput.

Use AI aggressively in an isolated Shadow Workspace to discover and verify a complete
solution, while keeping the user's real branch under Human control.

## Core model

### Human Workspace

The user's real branch/worktree. It is authoritative.

Never overwrite, reset, or force it to match Shadow merely because the reference differs.

### Shadow Workspace

An isolated Git worktree/branch where AI may fully implement, build, test, debug, and
iterate.

Its purpose is to prove feasibility, discover pitfalls, and create a verified reference.

### Guide Branch

A pedagogical commit chain rebuilt from the recorded baseline after Shadow succeeds.

Guide commits are reference steps for guided reconstruction, review, show, and takeover.
Correctness and teachability matter more than preserving exploratory Shadow history.

## Non-negotiable invariants

1. Human Workspace is authoritative.
2. Design approval is a hard implementation gate.
3. Never destroy or silently overwrite Human changes.
4. Never automatically use destructive recovery such as `git reset --hard`,
   `git clean -fd`, forced checkout over local edits, or force-push.
5. Shadow is a reference, not a mandatory answer.
6. Preserve meaningful Shadow failures and hidden constraints as Pitfalls.
7. Every `/pair take` mutation requires checkpoint evidence and a durable operation journal
   before source modification.
8. Reconcile a non-terminal takeover before starting another takeover.
9. Reconcile persistent Pair state with actual Git state before resumed/mutating work.
10. Unknown drift fails closed; preserve Human code instead of guessing.
11. Guided steps should be concept-sized and verifiable.
12. Do not perform unrelated refactors merely because they are convenient.
13. Review behavior and invariants before textual similarity to Shadow.
14. If Human code is simpler or better, keep it and adapt the remaining plan.
15. After delegated work, return control unless the user explicitly requests continued
    autonomous implementation.
16. Track knowledge as `covered`, `discussed`, or `revisit`; do not claim the user
    "understands" something merely because code exists.

## Invocation

The commands below are semantic intents. Normalize host-native invocation into the same
internal protocol.

```text
# Codex
$pair-programming plan <goal-or-design>
$pair-programming next
$pair-programming review
$pair-programming hint
$pair-programming take tests
$pair-programming status

# Cursor / Claude Code / OpenCode
/pair-programming plan <goal-or-design>
/pair-programming next
/pair-programming review
/pair-programming hint
/pair-programming take tests
/pair-programming status

# Gemini CLI
Use the pair-programming skill, then provide the semantic /pair command.

# GitHub Copilot
Use the /pair-programming skill to run the semantic /pair command.
```

Canonical semantic protocol:

```text
/pair plan <goal-or-design>
/pair next [step]
/pair review [scope]
/pair hint [scope] [level]
/pair explain <scope>
/pair show <scope>
/pair take <scope>
/pair challenge [scope]
/pair status
/pair rebase-plan
```

`$pair-programming plan add retry` and `/pair-programming plan add retry` both mean
`/pair plan add retry`.

Also accept natural-language equivalents.

## Progressive disclosure

**Do not eagerly load every reference file.**

Treat this file as the runtime router. Read `reference/command-protocol.md` when dispatching
an explicit command, then read only the extra references required by that operation.

Read `reference/state-model.md` whenever persistent Pair state must be interpreted or
written.

## Workflow state machine

```text
design
  ├─ awaiting_approval
  │      └─ explicit approval of current revision
  ▼
shadow
  ▼
guide
  ▼
guided_reconstruction
  ▼
complete
```

Implementation is permitted only when:

```text
design.status == approved
AND
design.approved_revision == design.revision
```

Any material design change increments the revision, invalidates the prior approval, and
returns to `awaiting_approval`.

## Persistent state

Durable feature state lives under:

```text
.pair/
├── config.yaml
├── design.md
├── manifest.yaml
├── progress.yaml
├── notes.md
├── pitfalls.yaml
├── checkpoints/
├── operations/
├── patches/
└── sessions/
```

Structured YAML state uses `schema_version: 1`. Schemas live under `schemas/`.

Legacy early state using `version: 1` may be read as schema version 1 and canonicalized on
the next write. Stop on a newer unsupported schema version.

Initialize missing state from `templates/` only when needed. Do not rewrite unrelated state
just to normalize formatting.

## Shadow layout

Resolve Git paths instead of assuming `.git` is a directory:

```bash
git rev-parse --show-toplevel
git rev-parse --git-common-dir
```

Default refs:

```text
pair-shadow/<feature-slug>/solution
pair-shadow/<feature-slug>/guide
```

Default physical Shadow checkout:

```text
<repo-parent>/.pair-worktrees/<repo-name>/<feature-slug>/shadow
```

Never place the checked-out Shadow source tree inside `.git` or Git's linked-worktree
metadata directory.

One physical Shadow checkout per feature is the default. Git refs/commits are the durable
reference; the checkout is disposable and may be recreated.

## Runtime bootstrap

Before planning or mutating code:

1. Resolve repo root, Git common directory, current branch, HEAD, and worktree status.
2. Read repository-level instructions, contribution guidance, build/test presets, and
   relevant design docs.
3. Detect the project's existing build, test, lint, format, package, and dependency workflow.
4. Do not require a clean Human worktree merely to start planning.
5. If `.pair/` exists, read only the state required for the current command.
6. Before Human Workspace mutation, run recovery reconciliation.
7. Preserve staged, unstaged, and relevant untracked Human work.

Prefer project-native tooling and the narrowest meaningful validation first. Do not change
unrelated toolchain/dependency configuration unless the approved design requires it.

## Command dispatch

Always read `reference/command-protocol.md` for explicit commands.

| Command | Human source mutation | Extra references | Required behavior |
|---|---:|---|---|
| `/pair plan` | No before approval | `design-gate.md`, `state-model.md` | Classify design; if incomplete, write `.pair/design.md` and STOP. After approval, run Shadow → Guide. |
| `/pair next` | No | `pitfall-journal.md`, `state-model.md` | Teach one ready step, surface relevant Pitfalls, then stop at Human coding checkpoint. |
| `/pair review` | No | `review-rubric.md`, `pitfall-journal.md` | Review semantics/invariants; Shadow difference alone is not a defect. |
| `/pair hint` | No through L4 | — | Escalate concept → API/data/control flow → pseudocode → minimal reference diff. L5 becomes takeover. |
| `/pair explain` | No | — | Explain the requested architecture/code/Pitfall without modifying Human code. |
| `/pair show` | No | — | Show exactly the requested reference scope; label it reference-only and do not apply it. |
| `/pair take` | Yes | `takeover.md`, `recovery.md`, `pitfall-journal.md`, `state-model.md` | Run transactional takeover; validate; return control. |
| `/pair challenge` | No | — | Ask 1–3 maintainability-critical questions; no trivia or arbitrary score. |
| `/pair status` | No | `state-model.md`, `recovery.md`, `pitfall-journal.md` | Compare metadata with real Git state and report current truth. |
| `/pair rebase-plan` | No by default | `recovery.md`, `design-gate.md`, `decomposition.md`, `guide-quality.md`, `state-model.md` | Replan remaining work from authoritative Human code; this is not `git rebase`. |

## Plan → Shadow → Guide

For design classification and approval, read `reference/design-gate.md`.

If the input is not implementation-ready:

- inspect only enough code to design safely;
- create/update canonical `.pair/design.md`;
- set the current revision to `awaiting_approval`;
- summarize the important decisions;
- STOP before creating Shadow or implementation commits.

After the design gate opens:

1. Set phase to `shadow`.
2. Create the isolated Shadow solution ref/worktree.
3. Fully implement the approved behavior in Shadow.
4. Build/test/debug with project-native tooling.
5. Record meaningful discoveries in `.pair/pitfalls.yaml`.
6. Freeze a verified solution commit or explicitly record validation limitations.
7. Read `reference/decomposition.md` and `reference/guide-quality.md`.
8. Reverse-decompose the verified solution into teachable steps.
9. Map relevant Pitfalls to those steps.
10. Reconstruct Guide from the recorded baseline.
11. Run focused verification and `scripts/check-guide.py` when available.
12. Verify Guide behavior against the Shadow solution.
13. Set phase to `guided_reconstruction` and stop before implementing the first Human step.

Do not simply cherry-pick exploratory Shadow history into Guide.

## Guided reconstruction semantics

For `/pair next`, provide only:

- goal and why now;
- relevant files/symbols;
- important constraints/invariants;
- verification;
- relevant Shadow Pitfalls;
- smallest useful first move.

Then stop.

For `/pair review`, prioritize correctness, invariants, integration, maintainability, and
simplicity. Use:

- `must_fix`
- `should_consider`
- `nice_to_have`

Validate when practical and update progress from observed evidence.

For `/pair hint` levels 1–4, never modify Human source.

For `/pair show`, prefer the corresponding Guide commit when available.

For `/pair challenge`, record useful gaps under `knowledge.revisit`.

## Transactional takeover

Before `/pair take` modifies Human source, read:

- `reference/takeover.md`
- `reference/recovery.md`
- `reference/pitfall-journal.md`
- `reference/state-model.md`

Then:

1. reconcile actual Git state;
2. reconcile any non-terminal takeover first;
3. validate scope/dependencies;
4. match relevant Pitfalls;
5. create `.pair/checkpoints/<operation-id>/`;
6. create `.pair/operations/<operation-id>.yaml`;
7. record `progress.active_operation`;
8. choose the smallest safe application strategy.

Preferred order:

```text
Semantic Port
  ↓
Cherry-pick Guide Commit
  ↓
3-way Patch
  ↓
Manual Adaptation
```

Preserve unrelated Human changes. Never overwrite a whole file merely because the reference
works.

Interrupted takeover resumes from recorded evidence; never replay the full patch blindly.

After applying: validate, record adaptations/origin/Pitfall handling, complete the operation,
clear `active_operation`, summarize what changed, and return control.

## Recovery and replanning

Read `reference/recovery.md` before substantial resumed work or Human source mutation.

If active operation/state drift exists, classify and reconcile it first.

For unknown/ambiguous drift:

- preserve Human Workspace;
- set recovery state to `attention_required`;
- explain the mismatch;
- stop automatic mutation.

Recovery never means restoring metadata's preferred code.

`/pair rebase-plan` is workflow replanning, not Git rebase. Preserve completed Human work,
solve only the remaining behavior in a new Shadow generation when needed, rebuild remaining
Guide steps, mark obsolete steps `superseded`, and explain why the plan changed.

## Pitfall behavior

Read `reference/pitfall-journal.md` when capturing, matching, reviewing, teaching, or applying
Pitfalls.

Pitfalls are engineering knowledge, not debugging noise.

Prefer matches by:

1. Guide step;
2. feature-wide mapping;
3. file;
4. symbol;
5. platform/configuration/condition.

Do not surface weak text-similarity matches merely to increase recall.

## Guide quality

Read `reference/decomposition.md` and `reference/guide-quality.md` when creating or checking
Guide.

Prefer:

- one primary concept per step;
- satisfied dependencies;
- 1–3 files;
- about 150 effective diff lines;
- focused verification;
- no avoidable future-step leakage.

Record justified exceptions. Structural checks do not prove semantic correctness.

A Guide with quality status `failed` must be repaired before Guided Reconstruction.

## Completion

Set phase to `complete` only when:

1. acceptance criteria are satisfied;
2. Human Workspace contains the intended implementation;
3. required validation passed or limitations are documented;
4. every Guide step is completed, intentionally skipped, or superseded;
5. remaining risks and important unresolved Pitfalls are recorded;
6. the user receives a maintainability handoff.

Final handoff should cover architecture, key flow/invariants, Human vs AI origin, validation,
limitations, major Pitfalls, future extension points, and what matters when maintaining the
feature later.

Do not automatically merge, delete, or clean up Shadow refs/worktrees at completion.

## Reference routing

Read only what the current operation requires.

| Need | Reference |
|---|---|
| Command parsing and output contract | `reference/command-protocol.md` |
| Design readiness and approval | `reference/design-gate.md` |
| Persistent state semantics | `reference/state-model.md` |
| Pitfall capture/matching/teaching | `reference/pitfall-journal.md` |
| Reverse decomposition | `reference/decomposition.md` |
| Guide quality contract | `reference/guide-quality.md` |
| Human-code review | `reference/review-rubric.md` |
| Human Workspace takeover | `reference/takeover.md` |
| Session/operation recovery | `reference/recovery.md` |

Do not preload unrelated references simply because they exist.
