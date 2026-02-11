# TESTING.md
## Correctness, Evidence, and Test Discipline

This document defines what constitutes a **valid test** for rgov.

Tests are not demonstrations.
Tests are not benchmarks.
Tests are not reassurance.

Tests exist to **prove invariant preservation**.

If a test passes but violates this document, the test is invalid.

This document is normative.

---

## 1. Testing Philosophy

rgov correctness is defined by:
- determinism
- replayability
- invariant preservation

Performance, fairness, and smoothness are secondary concerns.

A slow but correct system is acceptable.
A fast but nondeterministic system is not.

---

## 2. Test Categories

All tests must fall into exactly one of the following categories.

### 2.1 Policy Tests (Pure)

**Purpose:**  
Validate the policy state machine in isolation.

**Scope:**
- Policy component only
- No kernel
- No time
- No IO

**Characteristics:**
- Deterministic
- Replayable
- Fast
- Exhaustive where possible

**Examples:**
- Adversarial `U_w` sequences
- Debt accumulation and decay
- Boundary conditions (`U_w == B`, `U_w == 0`)
- State transition legality

If a policy test requires mocking time or the OS, it is invalid.

---

### 2.2 Replay Tests

**Purpose:**  
Prove determinism.

**Scope:**
- Recorded inputs only
- Offline execution

**Requirements:**
Given identical:
- declared budgets
- window size
- `U_w` sequence

The system must produce identical:
- state transitions
- `T_w` decisions

**Failure Meaning:**
Replay divergence is a correctness failure, not test flakiness.

---

### 2.3 Invariant Tests

**Purpose:**  
Assert that invariants are never violated.

**Scope:**
- All components
- All execution paths

**Method:**
- Instrument state
- Assert invariants at:
  - window boundaries
  - state transitions
  - enforcement application

If an invariant fails, the test must fail immediately.

---

### 2.4 Observation Tests

**Purpose:**  
Validate aggregation correctness.

**Scope:**
- Observation component only

**Characteristics:**
- Deterministic inputs
- Deterministic outputs
- No policy logic

**Examples:**
- Correct delta computation
- Boundary sampling correctness
- No mid-window reads

Observation tests must not assert “reasonableness”, only correctness.

---

### 2.5 Enforcement Tests

**Purpose:**  
Validate enforcement semantics without policy.

**Scope:**
- Enforcement component only

**Characteristics:**
- Idempotency checks
- Correct mapping of `(T_w, W)` → kernel state

**Examples:**
- Repeated writes produce identical kernel state
- No side effects beyond intended control files

Enforcement tests must not depend on workload behavior.

---

### 2.6 Integration Tests

**Purpose:**  
Validate component sequencing.

**Scope:**
- Orchestrator + components
- Minimal real kernel interaction

**Constraints:**
- Must not introduce new logic paths
- Must not relax component boundaries
- Must not depend on precise timing

Integration tests validate *composition*, not optimization.

---

## 3. Mandatory Test Properties

Every valid test must satisfy all of the following.

### 3.1 Determinism

Running the same test twice must produce identical results.

If not:
- the test is invalid
- or the system is broken

---

### 3.2 No Wall-Clock Dependence

Tests must not:
- sleep
- wait for real time
- assert durations
- rely on scheduling luck

The only temporal primitive allowed is:
advance_window()


---

### 3.3 Explicit Assertions

Tests must assert:
- invariants
- exact state
- exact decisions

Tests must not assert:
- “looks stable”
- “roughly fair”
- “close enough”

---

## 4. Forbidden Test Practices

The following are explicitly forbidden:

- `sleep()`-based timing
- polling with timeouts
- asserting latency or responsiveness
- asserting fairness or utilization
- relying on scheduler behavior
- benchmarking as correctness proof
- ignoring flakiness
- retrying failed tests without explanation

Any test using these practices must be rejected.

---

## 5. Adversarial Testing Requirements

The test suite must include adversarial cases, including:

- Continuous overshoot (`U_w >> B`)
- Alternating overshoot / undershoot
- Long debt accumulation
- Zero-usage windows
- Budget at capacity boundary
- Multiple workloads with independent state

Happy-path tests are insufficient.

---

## 6. Multi-Workload Tests

For multi-workload scenarios:

- Each workload must be tested independently
- Adding a workload must not change another’s policy state
- Capacity violations must be detected explicitly

Cross-workload coupling is a test failure.

---

## 7. Failure Semantics

When a test fails:

- The failure must be reproducible
- The violated invariant must be identifiable
- The failure must not be dismissed as “timing noise”

Flaky tests indicate either:
- invalid tests
- or broken determinism

Both are unacceptable.

---

## 8. Performance Tests (Non-Authoritative)

Performance tests:
- may exist
- must be clearly labeled
- must not be used to justify correctness

Performance regressions do not justify invariant violations.

---

## 9. Test Coverage Expectations

Coverage is defined by:
- invariant coverage
- state transition coverage
- boundary condition coverage

Line coverage is insufficient.

---

## 10. Final Rule

If a test passes but violates:
- SPEC.md
- ARCHITECTURE.md
- INVARIANTS.md

the test is wrong.

If a test fails while all invariants hold,
the test is wrong.

Correctness is defined by invariant preservation,
not by intuition, metrics, or confidence.

No exceptions.