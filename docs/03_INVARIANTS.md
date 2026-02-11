# INVARIANTS.md
## System Invariants and Correctness Conditions

This document defines the invariants that must hold for rgov to be correct.

An invariant is a statement that must be true:
- at all times, or
- at specific boundaries (e.g. window transitions)

If any invariant is violated:
- the system is incorrect
- the behavior is a bug
- no heuristic recovery is permitted

This document is normative.

---

## 1. Invariant Philosophy

rgov correctness is defined by **invariants**, not outcomes.

- Unexpected but explainable behavior is acceptable.
- Unexplainable behavior is not.

Every invariant exists to:
- preserve determinism
- preserve replayability
- preserve bounded behavior
- prevent silent semantic drift

---

## 2. Global Invariants

These invariants apply to the entire system.

### G1. Determinism Invariant

Given identical:
- declared budgets
- enforcement window size
- sequence of aggregated observations

the system must produce identical:
- state transitions
- enforcement decisions

Any divergence is a correctness failure.

---

### G2. Replayability Invariant

All policy decisions must be reproducible offline using recorded inputs.

No decision may depend on:
- wall-clock time
- scheduling order
- async callbacks
- external state

If replay diverges, the system is broken.

---

### G3. Single Source of Truth

Each conceptual quantity must have exactly one owner.

Examples:
- Policy state → Policy component only
- Observations → Observation component only
- Enforcement actions → Enforcement component only

Duplicated or shadow state is forbidden.

---

### G4. Window Exclusivity

All policy decisions:
- occur only at enforcement window boundaries
- apply only to the next window

Mid-window reactions are forbidden.

---

## 3. Time Invariants

### T1. Fixed Window Invariant

- Enforcement window size `W` is constant
- `W` must not change at runtime

Any attempt to resize or adapt `W` violates determinism.

---

### T2. Single Evaluation Per Window

For each window `w`:
- policy is evaluated exactly once
- enforcement decision `T_w` is computed exactly once

Multiple evaluations per window are forbidden.

---

### T3. Bounded Lag Invariant

All observation, decision, and enforcement lag is bounded by:
- at most one enforcement window

Unbounded delay is a correctness failure.

---

## 4. Policy State Invariants (CPU)

These invariants apply to the CPU policy state machine.

Let:
- `debt` be accumulated excess CPU usage
- `B` be declared CPU budget
- `T_w` be enforced quota for window `w`

---

### P1. Non-Negative Debt

debt ≥ 0


Debt must never be negative.

---

### P2. Budget Bound

0 ≤ T_w ≤ B


Enforced quota must never exceed declared budget.

---

### P3. No Throttling Without Excess

If throttling occurs, then:
∃ w' ≤ w : U_w' > B


Throttling without recorded excess is forbidden.

---

### P4. No Forgiveness Without Payment

Debt may only decrease when:
U_w < B


Debt must not decay spontaneously.

---

### P5. Normal-State Cleanliness

state == Normal ⇒ debt == 0


Transitioning to `Normal` with outstanding debt is forbidden.

---

### P6. Deterministic Transitions

Given identical `(state, debt, U_w)`:
- the next `(state, debt, T_w)` must be identical

Any nondeterministic branching is a bug.

---

## 5. Observation Invariants

### O1. Aggregation Boundary

Observations must be:
- aggregated per window
- sampled only at window boundaries

Event-level or mid-window sampling is forbidden.

---

### O2. Source Fidelity

CPU usage `U_w` must be derived exclusively from:
cpu.stat:usage_usec


Alternative or auxiliary sources must not influence policy.

---

### O3. No Interpretation

Observation must not:
- infer runnable state
- smooth values
- correct kernel behavior
- guess intent

Observation reports, policy decides.

---

## 6. Enforcement Invariants

### E1. Enforcement Mechanism Exclusivity

CPU enforcement must use:
cgroups v2: cpu.max


No other CPU knobs may affect enforcement.

---

### E2. Enforcement Is Declarative

Given `(T_w, W)`:
- enforcement must write exactly one equivalent kernel state
- enforcement must not modify `T_w`

Enforcement must not reinterpret policy output.

---

### E3. Idempotency

Applying the same enforcement decision multiple times must not change behavior.

If repeated writes alter outcomes, enforcement is incorrect.

---

## 7. Multi-Workload Invariants

### M1. Independent Policy State

Each workload must maintain:
- independent policy state
- independent debt accounting

Cross-workload policy coupling is forbidden.

---

### M2. Capacity Precondition

For each resource:
Σ declared_budgets ≤ system_capacity


If violated:
- configuration is invalid
- behavior is undefined
- enforcement must not attempt to compensate

---

### M3. Isolation Under Valid Configurations

Under valid capacity conditions:
- adding or removing a workload must not alter another workload’s policy state

Violation indicates hidden coupling.

---

## 8. Explainability Invariants

### X1. Causal Traceability

Every enforcement action must be traceable to:
- a specific observed condition
- a specific violated invariant
- a specific policy rule

If a decision cannot be explained, it is invalid.

---

### X2. No Implicit Reasons

Enforcement must not rely on:
- intuition
- fairness assumptions
- inferred intent
- historical smoothing

Only explicit state and observations are allowed.

---

## 9. Forbidden States and Events

The following must never occur:

- Negative debt
- Enforcement without policy decision
- Policy decision without observation
- Mid-window policy evaluation
- Wall-clock time in policy logic
- Async decision paths
- Hidden state outside Policy
- Kernel feedback influencing policy directly

Any occurrence is a hard failure.

---

## 10. Testing Implications

Tests must assert invariants directly.

A test that passes but violates an invariant is invalid.

Correctness is defined by invariant preservation, not by:
- throughput
- fairness
- subjective performance
- visual smoothness

---

## 11. Final Invariant

If all invariants hold, rgov is correct.

If any invariant is violated, rgov is broken,
regardless of observed performance or user satisfaction.

There are no exceptions.