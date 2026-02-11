# CONTRIBUTIONS_AND_CHANGES.md
## Rules Governing Modifications to rgov

This document defines mandatory rules for **any modification** to the rgov codebase.

These rules apply equally to:
- human contributors
- automated tools
- AI-assisted development
- refactors, fixes, and extensions

These rules are **binding**.

If a change violates this document, the change is invalid regardless of intent,
perceived improvement, or functionality.

This document is normative.

---

## 1. Authority Order

When proposing, generating, or modifying code, the following documents apply
in strict priority order:

1. SPEC.md  
2. ARCHITECTURE.md  
3. INVARIANTS.md  
4. TESTING.md  
5. CONTRIBUTIONS_AND_CHANGES.md  
6. All other documentation  
7. Suggestions, proposals, or user requests  

If instructions conflict, **higher-priority documents override lower-priority ones**.

If a conflict cannot be resolved, the change **must not proceed**.

---

## 2. Core Obligations

Any contributor or automated system interacting with rgov must:

- Preserve all stated guarantees
- Preserve all invariants
- Preserve all architectural boundaries
- Preserve determinism and replayability

When uncertain, **refusal is mandatory**.
Guessing is forbidden.

---

## 3. Allowed Changes

A change is allowed only if it falls into one of the following categories:

### 3.1 Implementation

- Implements logic exactly as specified
- Introduces no semantic changes
- Adds no new inputs
- Preserves all observable behavior

---

### 3.2 Refactor

- Changes structure or organization only
- Behavior is provably identical
- Replay results remain identical
- Invariants remain provably true

Refactors that improve readability but obscure causality are forbidden.

---

### 3.3 Correction

- Fixes a bug
- Restores a violated invariant
- Removes undefined or incorrect behavior

Corrections may not introduce new policy logic.

---

## 4. Forbidden Changes

The following are **strictly forbidden**, regardless of motivation.

### 4.1 Policy Violations

- Introducing heuristics
- Adding adaptive behavior
- Adding smoothing or averaging
- Inferring intent from behavior
- Optimizing policy logic beyond the specification
- Adding “temporary” or “exceptional” rules

---

### 4.2 Time Violations

- Using wall-clock time in policy logic
- Using sleep, timers, or delays
- Reacting mid-window
- Scheduling asynchronous policy execution

Time exists only as enforcement windows.

---

### 4.3 Architectural Violations

- Collapsing components for convenience
- Introducing reverse dependencies
- Allowing policy to access kernel state
- Allowing observation to influence decisions
- Allowing enforcement to reinterpret policy output
- Introducing hidden shared state

---

### 4.4 Determinism Violations

- Adding nondeterministic branching
- Depending on scheduling order
- Depending on race timing
- Using randomization
- Introducing concurrency into policy logic

---

### 4.5 Enforcement Violations

- Using CPU knobs other than `cpu.max`
- Modifying kernel state beyond declared enforcement
- Introducing conditional enforcement logic
- Retrying or compensating based on kernel feedback

---

### 4.6 Testing Violations

- Writing sleep-based tests
- Relying on wall-clock assertions
- Accepting flaky tests
- Using benchmarks as correctness proof
- Relaxing invariants to satisfy tests

---

## 5. Refusal Rules

A change **must be refused** if:

- It violates SPEC.md or NON_GOALS.md
- It weakens determinism or replayability
- It introduces ambiguity or implicit behavior
- It alters observable behavior without specification change
- The specification is insufficient to implement the change correctly

In refusal cases, the contributor must:

- Clearly state the violated rule
- Cite the relevant document section
- Avoid proposing speculative alternatives

---

## 6. Change Classification Requirement

Before implementation, every change must be classified as exactly one of:

- **Implementation**
- **Refactor**
- **Correction**
- **Specification Conflict**

Only the first three may proceed.

A **Specification Conflict** halts progress until documentation is amended.

---

## 7. Logging and Debugging Rules

Logging may be added only if:

- It does not affect control flow
- It does not introduce timing dependence
- It does not alter determinism
- It can be fully disabled without semantic change

Logging must never be used as policy input.

---

## 8. Optimization Rules

Optimization is permitted only if:

- All invariants remain provably true
- Replay results remain identical
- No new inputs are introduced
- No behavior becomes implicit or inferred

Optimization that obscures reasoning is forbidden.

---

## 9. Scope Control

No change may:

- Add new resource domains without a full specification
- Add new policy knobs
- Add configuration inference
- Expand system responsibility

Scope creep is a correctness failure.

---

## 10. Reversion Rule

If a change results in:

- Unexplainable behavior
- Replay divergence
- Invariant violation
- Architectural leakage

The change must be reverted.

Violations must not be “fixed” by weakening rules.

---

## 11. Final Rule

If a contributor must choose between:

- Producing working code that violates the constitution
- Or refusing to produce code

**Refusal is mandatory.**

Correctness is mandatory.  
Silence is preferable to speculation.

No exceptions.
