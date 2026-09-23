# Example Session — Capability Registry

This example demonstrates the complete Pair Programming workflow and intentionally uses
**every current `/pair` command at least once**.

Commands covered:

```text
/pair plan
/pair next
/pair review
/pair hint
/pair explain
/pair show
/pair take
/pair challenge
/pair status
/pair rebase-plan
```

The scenario is adding a Capability Registry to an existing Plugin system.

## Host invocation note

This transcript uses the semantic `/pair ...` protocol so every workflow command is easy to
read consistently. On a real host, invoke the same subcommand through the installed skill:

```text
Codex:                         $pair-programming plan ...
Cursor / Claude Code / OpenCode: /pair-programming plan ...
Gemini CLI:                     activate pair-programming, then provide /pair plan ...
GitHub Copilot:                 use /pair-programming skill to run /pair plan ...
Semantic intent:                /pair plan ...
```

The same mapping applies to `next`, `review`, `hint`, `explain`, `show`, `take`,
`challenge`, `status`, and `rebase-plan`.

---

## 1. Start with only a feature goal — `/pair plan`

User:

```text
/pair plan 为 Plugin 增加 Capability Registry
```

This is only a feature goal, not an implementation-ready design.

The agent first inspects the relevant Plugin lifecycle, registration path, tests, and build
setup, then writes:

```text
.pair/design.md
```

Agent:

```text
Design revision: 1
Status: awaiting_approval

Proposed design:

- Introduce CapabilityId and ProviderId as value types.
- Add CapabilityRegistry responsible only for registration and lookup.
- PluginManager owns the registry but the registry does not own Plugin/Provider lifetime.
- Plugin load registers capabilities after successful initialization.
- Plugin unload unregisters capabilities before Provider destruction.
- Duplicate capability providers are allowed and resolved by registration order.
- Focused registry tests plus Plugin lifecycle integration tests will verify behavior.

No Shadow worktree or implementation branch has been created yet.

Please review .pair/design.md and confirm this revision before implementation.
```

User:

```text
方案没问题，按这个方案实现
```

The agent records approval:

```yaml
design:
  status: approved
  revision: 1
  approved_revision: 1
```

Then it enters Shadow implementation.

---

## 2. Shadow implementation and discovery

The agent creates the isolated Shadow checkout and fully implements the approved design.

During implementation it discovers three meaningful pitfalls:

```yaml
P001:
  title: Duplicate registration invalidates an iterator used by lookup
  status: resolved
  related_steps:
    - registry

P002:
  title: Registry entry can outlive Provider during Plugin teardown
  status: resolved
  related_steps:
    - plugin-lifecycle

P003:
  title: Existing integration fixture destroys PluginManager before Plugin
  status: resolved
  related_steps:
    - integration-tests
```

After build and tests pass, the agent creates the Guide Branch:

```text
Step 1  capability-model
Step 2  registry
Step 3  plugin-integration
Step 4  plugin-lifecycle
Step 5  integration-tests
Step 6  final-verification
```

---

## 3. Inspect progress — `/pair status`

User:

```text
/pair status
```

Agent:

```text
Feature: Plugin Capability Registry
Design: approved revision 1
Shadow: verified
Guide: 6 steps

[ ] 1 Capability model
[ ] 2 CapabilityRegistry
[ ] 3 Plugin integration
[ ] 4 Plugin lifecycle
[ ] 5 Integration tests
[ ] 6 Final verification

Shadow pitfalls:
- P001 mapped to Step 2
- P002 mapped to Step 4
- P003 mapped to Step 5

Current:
Step 1 — Capability model
```

---

## 4. Begin coding — `/pair next`

User:

```text
/pair next
```

Agent:

```text
Step 1 — Capability model

Goal:
Represent capability identity independently from PluginManager.

Why:
Registry lookup needs stable value semantics before we introduce storage.

Scope:
- include/capability.h
- CapabilityId
- CapabilityProviderId

Constraints:
- value semantics
- cheap copy/move
- no ownership of Plugin or Provider
- preserve current public Plugin API

Verification:
build the focused plugin test target.

Shadow pitfalls:
None mapped to this step.

Suggested first move:
Define CapabilityId and CapabilityProviderId with equality/hash behavior only.
Do not add the registry yet.
```

The user implements the value types.

---

## 5. Ask for a light hint — `/pair hint`

On Step 2, the user is unsure how the registry should store multiple providers.

User:

```text
/pair hint step 2
```

Agent gives Level 1:

```text
Hint Level 1 — Concept

Separate two questions:

1. How do you identify one capability?
2. Can one capability have more than one provider?

Do not choose the container first. Decide the lookup semantics first.
```

The user still wants more help.

User:

```text
/pair hint step 2 level 2
```

Agent:

```text
Hint Level 2 — Structure

A useful shape is:

CapabilityId
    -> ordered collection of ProviderId

Keep ownership outside the registry.

Shadow pitfall P001:
The first Shadow attempt stored iterators into a vector that was later mutated by duplicate
registration. Those iterators became invalid.

Avoid designing lookup around long-lived container iterators.
```

---

## 6. Ask for explanation without seeing the answer — `/pair explain`

User:

```text
/pair explain symbol CapabilityRegistry::find
```

Agent:

```text
Purpose:
Return the currently selected provider for a capability.

Input:
CapabilityId.

Output:
A provider identity/reference that does not transfer ownership.

Important invariant:
The registry must not make Provider lifetime longer than Plugin lifetime.

Call path:
PluginManager -> CapabilityRegistry::find -> selected provider.

Failure mode:
No provider registered for the requested capability.

Why not return a stored vector iterator?
Because registration/unregistration mutates the underlying collection and iterator lifetime
would become part of the public contract.
```

No code is changed.

---

## 7. Inspect the reference implementation — `/pair show`

The user wants to see only the reference implementation of the lookup function.

User:

```text
/pair show symbol CapabilityRegistry::find
```

Agent:

```text
Reference only — no Human Workspace changes applied.

[Shows the minimal reference implementation and surrounding contract.]

This is the Shadow/Guide solution, not a mandatory implementation.
```

The user writes a different but equivalent implementation.

---

## 8. Review human code — `/pair review`

User:

```text
/pair review step 2
```

Agent:

```text
must_fix:
None.

should_consider:
None.

Known Shadow-pitfall check:
P001 does not apply to your implementation because you return ProviderId values rather than
persisting iterators into the provider list.

Validation:
Focused registry tests passed.

Step 2 complete.
Origin: human.
```

The Human implementation differs from Shadow, but the agent keeps it because it is correct.

---

## 9. Check understanding — `/pair challenge`

User:

```text
/pair challenge step 2
```

Agent:

```text
1. Why does CapabilityRegistry store provider identity instead of owning Provider objects?

2. If duplicate providers are supported, what invariant determines which provider find()
   returns?

3. What kind of bug would appear if callers kept references into the registry's internal
   provider container across unregister()?
```

User answers.

The agent corrects any concrete misconception and records useful concepts as covered/revisit.

---

## 10. Continue to a step with a known Shadow pitfall — `/pair next`

User:

```text
/pair next
```

Later, Step 4 becomes current.

Agent proactively reports:

```text
Step 4 — Plugin lifecycle

Goal:
Make registry entries follow Provider lifetime correctly.

Shadow pitfall P002

What happened in Shadow:
The first implementation removed registry entries after Plugin destruction.

Symptom:
Integration test observed a dangling provider reference.

Root cause:
CapabilityRegistry does not own Provider lifetime.

Invariant for your implementation:
unregister capabilities BEFORE destroying the Provider/Plugin object.

Avoid:
Do not rely on registry cleanup from a later manager destructor.
```

The user receives the warning without having to ask.

---

## 11. Delegate a low-value part — `/pair take`

The user wants to understand lifecycle code but does not want to write repetitive tests.

User:

```text
/pair take tests
```

The agent:

1. creates a checkpoint of the Human Workspace;
2. identifies the Guide test delta;
3. adapts the tests to the user's actual API names;
4. applies only test changes;
5. runs focused tests;
6. records origin as `mixed`;
7. tells the user which pitfalls the tests cover.

Agent:

```text
Applied:
- registry duplicate-provider tests
- lifecycle cleanup tests
- teardown-order regression test for P002
- fixture-order regression test for P003

No production implementation was replaced.

Validation:
Focused tests passed.

Control returned to you.
```

---

## 12. Inspect progress again — `/pair status`

User:

```text
/pair status
```

Agent:

```text
Feature: Plugin Capability Registry
Design: approved revision 1
Shadow: verified

[✓] 1 Capability model          human
[✓] 2 CapabilityRegistry        human
[✓] 3 Plugin integration        human
[→] 4 Plugin lifecycle          human
[✓] 5 Integration tests         mixed
[ ] 6 Final verification

Pitfalls:
✓ P001 surfaced and discussed
✓ P002 surfaced
✓ P003 surfaced through delegated tests

Next:
finish lifecycle ordering, then run final verification.
```

---

## 13. Human design diverges — `/pair rebase-plan`

While implementing Step 4, the user realizes the existing PluginManager already has a
lifecycle hook that makes the original Guide design unnecessarily complex.

The user changes the Human implementation to use that existing hook.

User:

```text
/pair rebase-plan
```

The agent treats Human Workspace as authoritative.

It does NOT reset the user's code back to Shadow.

Instead it:

1. preserves completed Human work;
2. creates a new Shadow generation from the current Human state;
3. reimplements only remaining behavior;
4. verifies the lifecycle hook approach;
5. regenerates remaining Guide steps;
6. marks obsolete steps as `superseded`.

Agent:

```text
Replanned from Human implementation.

Accepted divergence:
Use existing PluginManager::onBeforeUnload lifecycle hook.

Superseded:
old Step 4 teardown integration.

New remaining plan:
4b Validate lifecycle hook ordering
6  Final verification

Pitfall P002 remains relevant, but the new architecture avoids it structurally by enforcing
unregister in onBeforeUnload().
```

---

## 14. Review the replanned implementation — `/pair review`

User:

```text
/pair review
```

Agent validates:

- lifecycle ordering;
- known Pitfall P002;
- regression tests;
- current design constraints.

Agent:

```text
No must-fix issues.

P002:
Structurally avoided. unregister() runs from onBeforeUnload() before Provider destruction.

Validation passed.

Step 4b complete.
```

---

## 15. Final status

User:

```text
/pair status
```

Agent:

```text
Feature: Plugin Capability Registry
Design: approved revision 1
Shadow generation: 2
Human Workspace: authoritative

[✓] Capability model
[✓] CapabilityRegistry
[✓] Plugin integration
[✓] Lifecycle hook integration
[✓] Integration tests
[✓] Final verification

Implementation origin:
- human: core model, registry, lifecycle
- mixed: tests
- ai: test boilerplate only

Pitfalls:
✓ P001 discussed
✓ P002 discussed and structurally avoided
✓ P003 covered by regression test

Validation:
all required focused/integration checks passed.

Feature complete.
```

---

## Command coverage

This example used every current command:

| Command | Where it was used |
|---|---|
| `/pair plan` | Create design, wait for approval, then run Shadow |
| `/pair next` | Enter guided implementation steps |
| `/pair review` | Review Human implementation semantically |
| `/pair hint` | Progressive help without immediately revealing the answer |
| `/pair explain` | Explain a symbol and its invariants |
| `/pair show` | Inspect reference implementation without applying it |
| `/pair take` | Delegate tests to AI |
| `/pair challenge` | Check architectural understanding |
| `/pair status` | Inspect workflow, ownership, and Pitfall state |
| `/pair rebase-plan` | Rebuild remaining plan after Human design divergence |

The example intentionally demonstrates the intended balance:

> AI explores first, the human remains in control, and Shadow discoveries become teaching
> material instead of disappearing with the final patch.
