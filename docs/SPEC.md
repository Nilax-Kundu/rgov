# rgov — Deterministic Resource Governor
## Specification and Project Boundaries

This document defines the **non-negotiable rules**, **guarantees**, **non-goals**, and **component boundaries** of rgov.

If the implementation contradicts this document, the implementation is wrong.

This document is not aspirational.  
It is a contract.

---

## 1. Purpose

rgov is a **user-space resource governor** that enforces **deterministic, declarative resource budgets** for Linux workloads.

rgov prioritizes:
- determinism of decisions
- bounded behavior
- replayability
- explainability

rgov explicitly rejects:
- heuristics
- adaptivity
- latency promises
- hidden policy

---

## 2. Core Philosophy

### 2.1 Determinism Definition

Determinism means:

> Given identical declared budgets, identical aggregated observations sampled at identical enforcement windows, rgov produces identical enforcement decisions.

Determinism does **not** mean:
- identical instruction timing
- scheduler-level reproducibility
- zero jitter

Truth lives in **policy decisions**, not execution timing.

---

### 2.2 Contract Model

Workloads declare **resource budgets**.
rgov enforces those budgets.
rgov does not infer intent, smooth behavior, or negotiate fairness.

If the declared budget is insufficient for desired behavior, this is a **configuration error**, not a bug.

---

## 3. Time Model

### 3.1 Enforcement Window

- Time is discretized into fixed-length enforcement windows `W`.
- `W` is constant for the lifetime of the process.
- Default `W = 100ms`.

All guarantees are defined **in terms of enforcement windows**, not wall-clock time.

rgov must not react mid-window.

---

### 3.2 Window Semantics

For each window `w`:
- observations are sampled at window boundaries
- decisions apply to the *next* window
- enforcement lag ≤ 1 window

Overshoot and delay are **explicitly bounded** and owned.

---

## 4. CPU Resource Specification

### 4.1 Observation Source

CPU usage `U_w` is defined as:

U_w = Δ(cpu.stat:usage_usec)


measured at enforcement window boundaries.

Observations are:
- aggregated
- monotonic
- cgroup-scoped

rgov does not observe:
- runnable state
- wakeups
- scheduler events
- per-task execution

---

### 4.2 Enforcement Mechanism

CPU budgets are enforced exclusively via:

cgroups v2: cpu.max


Mapping:
- enforcement window `W` → cpu.max period
- enforced quota `T_w` → cpu.max quota

No other CPU control knobs are permitted for policy:
- cpu.weight (forbidden)
- cpu.uclamp (forbidden)
- RT scheduling (forbidden)

---

### 4.3 CPU Policy State Machine

Each workload maintains the following persistent state:

- `state ∈ {Normal, Throttled}`
- `debt ≥ 0`
- `T_w ≥ 0`

The policy is evaluated once per window and is fully deterministic.

All transitions must obey:
- no negative debt
- no throttling without recorded excess
- no transition to Normal with outstanding debt

If replay of `(U_w)` produces divergent decisions, this is a bug.

---

### 4.4 Guarantees (CPU)

rgov guarantees:

1. Decision determinism at window boundaries
2. Bounded overshoot ≤ one enforcement window
3. Enforcement delay ≤ one enforcement window
4. Conditional starvation freedom if:
   - declared budget > 0
   - total declared CPU ≤ system capacity
5. Explainability of every throttle decision

rgov does not guarantee:
- responsiveness
- fairness beyond declared budgets
- real-time behavior

---

## 5. Multi-Workload Model

- Each workload has **independent policy state**
- No cross-workload policy exists
- Interaction occurs only via kernel enforcement

Capacity checks are global and **pre-enforcement**.

Oversubscribed configurations are invalid and must be rejected or reported explicitly.

---

## 6. Replayability

### 6.1 Replay Definition

Given:
- declared budgets
- enforcement window size
- sequence of observed `U_w`

rgov must produce:
- identical state transitions
- identical enforcement decisions

Replay input must exclude:
- wall-clock time
- async events
- scheduler callbacks
- signal timing

Replay divergence is a correctness failure.

---

### 6.2 Logging Requirements

At minimum, rgov must be able to log:

(window_index, state, debt, U_w, T_w)


Logs must be sufficient to replay decisions offline.

---

## 7. Explainability Requirements

Every enforcement action must be explainable as:

- observed condition
- violated invariant
- applied policy rule

Explainability must not rely on:
- heuristics
- probabilistic reasoning
- inferred intent

If a decision cannot be explained, it is invalid.

---

## 8. Component Boundaries

### 8.1 Policy Layer
- Pure logic
- No syscalls
- No clocks
- Fully testable in isolation

### 8.2 Observation Layer
- Reads kernel state
- Performs aggregation only
- No policy decisions

### 8.3 Enforcement Layer
- Writes cpu.max
- Idempotent
- Stateless

### 8.4 Orchestrator
- Advances windows
- Sequences components
- Contains no policy

Cross-layer leakage is forbidden.

---

## 9. Testing Rules

### 9.1 Mandatory Tests

- Policy replay tests
- Invariant violation tests
- Adversarial `U_w` sequences
- Multi-workload isolation tests

### 9.2 Forbidden Test Practices

- Time-based sleeps
- Wall-clock assertions
- Flaky scheduling assumptions
- Performance-only benchmarks as correctness proof

Correctness precedes performance.

---

## 10. Non-Goals (Explicit)

rgov does not aim to:
- maximize utilization
- smooth latency
- auto-tune budgets
- infer workload intent
- replace schedulers or orchestrators

Adding any of the above requires a **new project**, not an extension.

---

## 11. Versioning Rule

Each version of rgov must:
- preserve all guarantees of previous versions
- add evidence, not heuristics
- never weaken determinism or replayability

Breaking this rule constitutes a fork.

---

## 12. Final Rule

If behavior is surprising but explainable, rgov is correct.  
If behavior is unexplainable, rgov is broken.

No exceptions.