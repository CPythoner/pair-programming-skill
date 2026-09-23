# Semantic Review Rubric

Review Human Workspace in this order.

## 1. Correctness

- Does it satisfy the step's expected behavior?
- Any missing path, off-by-one, stale state, wrong default, or invalid transition?
- Do tests cover the intended behavior?

## 2. Invariants

- Ownership/lifetime preserved?
- Threading model preserved?
- API contract preserved?
- Error state recoverable?
- Resource cleanup correct?

## 3. Integration

- Existing callers still work?
- API/build/dependency compatibility preserved?
- Dependency boundaries and visibility correct?
- Build/package/runtime metadata correct?
- Platform or environment differences respected?

## 4. Maintainability

- Responsibility placed in the right abstraction?
- New abstraction actually needed?
- Naming communicates intent?
- Coupling increased unnecessarily?
- Can the next maintainer discover the flow?

## 5. Simplicity

The Shadow solution is NOT automatically better.

If Human code:
- is simpler;
- fits repository conventions better;
- has fewer moving parts;
- still satisfies acceptance criteria;

prefer the Human design and update later steps.

## Finding severity

### must_fix
Correctness, regression, safety, build/test, ownership/lifetime, serious concurrency/API issues.

### should_consider
Design or maintainability concern with plausible future cost.

### nice_to_have
Non-blocking cleanup or readability improvement.

Do not manufacture findings merely because the code differs from Shadow.
