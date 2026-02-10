# ARCHITECTURE.md
## Structural Boundaries and Component Contracts

This document defines the **complete architecture** of rgov.

Its purpose is to **freeze component boundaries** so that:
- behavior remains deterministic
- replayability is preserved
- future code cannot silently weaken guarantees

If code violates this document, the code is incorrect, even if it appears to work.

This document is normative.

---

## 1. Architectural Principles

The architecture of rgov is governed by the following principles:

1. **Separation of mechanism and policy**
2. **One-way dependencies only**
3. **No hidden state**
4. **No implicit time**
5. **Determinism over convenience**

Any architectural change that violates these principles constitutes a fork.

---

## 2. Component Overview

rgov is composed of exactly four primary components:

1. Policy
2. Observation
3. Enforcement
4. Orchestrator

Each component has:
- a single responsibility
- explicitly allowed dependencies
- explicitly forbidden behaviors

There are no auxiliary components that make decisions.

---

## 3. Component Specifications

### 3.1 Policy Component

#### Responsibility

The Policy component:
- implements the resource state machine
- computes enforcement decisions
- maintains all policy-relevant state

Policy is the **only place** where decisions are made.

#### Inputs
- Aggregated observations (`U_w`)
- Declared budgets
- Prior policy state

#### Outputs
- Next enforcement decision (`T_w`)
- Updated policy state

#### Allowed Behavior
- Pure computation
- Deterministic state transitions
- Explicit handling of invalid states

#### Forbidden Behavior
- System calls
- Kernel interaction
- Timers or clocks
- Threads or async execution
- Reading environment state
- Logging as a side effect
- Access to wall-clock time
- Direct enforcement actions

Policy must be:
- referentially transparent
- replayable in isolation
- testable without the operating system

If policy behavior depends on anything other than its inputs, it is invalid.

---

### 3.2 Observation Component

#### Responsibility

The Observation component:
- reads kernel-provided metrics
- aggregates raw signals into window-scoped observations
- provides inputs to policy

Observation **never interprets** data.

#### Inputs
- Kernel interfaces (e.g., cgroup files)

#### Outputs
- Aggregated observations (`U_w`)

#### Allowed Behavior
- File reads
- Parsing
- Numeric aggregation
- Boundary sampling at window edges

#### Forbidden Behavior
- Decision making
- State mutation beyond aggregation
- Enforcement actions
- Policy evaluation
- Heuristics
- Smoothing or filtering
- Guessing or inference

Observation must:
- expose exactly what the kernel reports
- perform no semantic transformation
- be replaceable by recorded logs during replay

If Observation attempts to “improve” the signal, it is wrong.

---

### 3.3 Enforcement Component

#### Responsibility

The Enforcement component:
- applies decisions produced by Policy
- maps abstract decisions to kernel controls

Enforcement is **purely declarative**.

#### Inputs
- Enforcement decision (`T_w`)
- Enforcement window size (`W`)

#### Outputs
- Kernel state changes (e.g., `cpu.max` writes)

#### Allowed Behavior
- Writing kernel control files
- Idempotent application of decisions

#### Forbidden Behavior
- Reading usage or metrics
- Maintaining policy state
- Decision making
- Conditional behavior based on kernel feedback
- Timing-sensitive logic
- Retry heuristics

Enforcement must:
- be stateless
- be safe to repeat
- reflect Policy output exactly

If Enforcement alters a decision, it is incorrect.

---

### 3.4 Orchestrator Component

#### Responsibility

The Orchestrator:
- advances enforcement windows
- sequences Observation → Policy → Enforcement
- coordinates component execution

The Orchestrator owns **control flow only**, not meaning.

#### Inputs
- Window size (`W`)
- Component interfaces

#### Outputs
- Ordered execution of components

#### Allowed Behavior
- Window advancement
- Component invocation
- Error propagation

#### Forbidden Behavior
- Making decisions
- Interpreting observations
- Modifying policy state directly
- Introducing asynchronous paths
- Skipping components

The Orchestrator must:
- be boring
- be predictable
- be replaceable without semantic change

If Orchestrator behavior affects policy outcomes, the architecture is broken.

---

## 4. Dependency Rules

### 4.1 Allowed Dependency Graph

Orchestrator
├── Observation ──> Kernel
├── Policy
└── Enforcement ──> Kernel


### 4.2 Forbidden Dependencies

The following are strictly forbidden:

- Policy → Kernel
- Policy → Observation
- Policy → Enforcement
- Observation → Policy
- Enforcement → Observation
- Enforcement → Policy
- Kernel → Policy (directly or indirectly)

Reverse dependencies are not allowed under any circumstance.

---

## 5. State Ownership Rules

- Policy state lives **only** in the Policy component
- Observation holds no persistent state beyond a single window
- Enforcement holds no state
- Orchestrator holds no policy-relevant state

Duplicated or shadow state is forbidden.

If the same concept appears in more than one component, the architecture is violated.

---

## 6. Time Handling Rules

- Time exists only as **window indices**
- No component may observe wall-clock time
- No component may react mid-window
- No component may schedule work based on time deltas

The only temporal primitive is:
advance_window()


Anything else is a violation.

---

## 7. Error Handling and Invalid States

- Invalid configurations must be detected explicitly
- Errors must not be masked or corrected heuristically
- Policy must fail loudly on impossible states

Silent recovery is forbidden.

If the system cannot proceed without violating guarantees, it must stop.

---

## 8. Testing Implications

Each component must be testable in isolation:

- Policy: pure replay tests
- Observation: deterministic input-output tests
- Enforcement: idempotency tests
- Orchestrator: sequencing tests

Integration tests must not weaken component boundaries.

---

## 9. Extension Rule

New resources (e.g., memory) must:
- replicate this architecture
- reuse the same component roles
- introduce no cross-resource coupling in policy

If a resource cannot fit this architecture, it does not belong in rgov.

---

## 10. Final Rule

Architecture is not a suggestion.

If a change:
- simplifies code but weakens boundaries
- improves performance but reduces determinism
- adds convenience but hides causality

the change must be rejected.

Correctness and explainability are higher priority than elegance.
