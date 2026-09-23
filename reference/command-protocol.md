# Command Protocol

The slash commands are semantic intents. They do not require a shell extension.

## Host invocation normalization

Use the host's native skill invocation and normalize the trailing arguments into this
document's `/pair ...` protocol:

```text
Codex:                         $pair-programming <command> ...
Cursor / Claude Code / OpenCode: /pair-programming <command> ...
Gemini CLI:                     activate pair-programming, then provide /pair <command> ...
GitHub Copilot:                 use /pair-programming skill to run /pair <command> ...
Internal semantic form:         /pair <command> ...
```

Example: `$pair-programming review step 2` and
`/pair-programming review step 2` both mean `/pair review step 2`.


## `/pair plan <goal-or-design>`

Input may be:
- a feature goal / requirement;
- an implementation-ready design;
- a design-document/spec reference;
- optional acceptance criteria / constraints.

First classify the input.

### If the input is NOT implementation-ready

1. Inspect relevant existing code.
2. Design the solution.
3. Save the canonical design to `.pair/design.md`.
4. Set `manifest.design.source: ai_generated`.
5. Set `manifest.design.status: awaiting_approval`.
6. Report the design summary and ask the user to confirm it.
7. STOP.

Do not create a Shadow worktree/branch or implement source code before explicit approval.

After the user approves the saved design, continue the same plan:
- bind approval to the current design revision;
- set design status to `approved`;
- set phase to `shadow`;
- create Shadow;
- fully implement and verify;
- build the Guide commit chain.

### If the input IS implementation-ready

Normalize/save it to `.pair/design.md`, record it as user-provided and approved, then
proceed to Shadow implementation unless the user explicitly asked for planning/review only.

Output after the implementation phase:
- feature summary;
- approved design reference;
- Shadow verification status;
- number of Guide steps;
- concise list of steps;
- major risks;
- current action: ready for `/pair next`.

Do not paste the whole solution.


## Design approval gate for all commands

Before any command that could create or apply implementation code, read the current design
state.

Implementation is allowed only when:

```text
design.status == approved
AND
design.approved_revision == design.revision
```

While awaiting approval:
- `/pair status` reports the pending design revision.
- `/pair explain design` and design-review discussion are allowed.
- requests to revise the design update `.pair/design.md`, increment the revision, and keep
  the gate closed.
- `/pair next`, `/pair take`, or other implementation requests must not create Shadow or
  modify implementation code; remind the user that the current design revision needs
  explicit approval.
- an explicit phrase such as "按这个方案实现" counts as approval and may immediately
  continue into Shadow implementation in the same turn.

## `/pair next [step]`

If no step is supplied, pick the first incomplete step with satisfied dependencies.

Output:
- goal;
- why;
- context;
- constraints;
- files/symbols;
- validation;
- relevant Shadow pitfalls (proactively, when mapped to this step);
- first coding move.

Stop at Human coding checkpoint.

## `/pair review [scope]`

Default scope:
- current step.

May review:
- step;
- file;
- symbol;
- current diff.

Output:
- must_fix;
- should_consider;
- nice_to_have;
- known Shadow-pitfall checks relevant to the reviewed scope;
- validation result;
- whether step can be marked complete.

Avoid empty headings; omit categories with no content.

## `/pair hint [scope] [level]`

Default scope: current blocker/current step.
Default level: previous level + 1, starting at 1.

Do not modify code for levels 1–4.
Level 5 becomes takeover.

## `/pair explain <scope>`

No modifications.

## `/pair show <scope>`

No modifications.
Use Guide commit where possible.
Mark output as reference.

## `/pair take <scope>`

Modifies Human Workspace.
Create checkpoint first.
Validate after.

## `/pair challenge [scope]`

Ask 1–3 questions.
No code modification.

## `/pair status`

Read metadata + actual git status.
Do not trust stale metadata blindly.

Also report:
- unresolved Shadow pitfalls;
- pitfalls related to the current/next step;
- pitfall entries that have not yet been surfaced to the user.

## `/pair rebase-plan`

This is workflow replanning, not `git rebase`.
Preserve Human Workspace.
Create a new Shadow generation if needed.
