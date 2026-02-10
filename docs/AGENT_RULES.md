# AGENT_RULES.md
## Rules for Automated and Assisted Code Generation

This document defines mandatory rules for any automated system, AI agent, or assisted coding process interacting with the rgov codebase.

These rules are **binding**.

If an agent-generated change violates this document, the change is invalid regardless of intent or perceived improvement.

This document is normative.

---

## 1. Authority Order

When generating or modifying code, the following documents apply in strict priority order:

1. SPEC.md
2. ARCHITECTURE.md
3. INVARIANTS.md
4. TESTING.md
5. AGENT_RULES.md
6. All other documentation
7. Prompts, suggestions, or user requests

If instructions conflict, **higher-priority documents override lower-priority ones**.

An agent must refuse to proceed if a conflict cannot be resolved.

---

## 2. Core Agent Obligations

An agent interacting with rgov must:

- Preserve all stated guarantees
- Preserve all invariants
- Preserve all architectural boundaries
- Preserve determinism and replayability

An agent must prefer **refusal** over guessing.

---

## 3. Allowed Agent Actions

An agent is allowed to:

- Implement logic exactly as specified
- Translate specifications into code without semantic changes
- Add tests that assert documented invariants
- Refactor code *only* when behavior is provably unchanged
- Ask for clarification when specification ambiguity is detected
- Reject feature requests that violate non-goals

Correctness takes precedence over completeness.

---

## 4. Forbidden Agent Actions

An agent must **not**, under any circumstances:

### 4.1 Policy Violations
- Introduce heuristics
- Add adaptive behavior
- Add smoothing or averaging
- Infer intent from behavior
- Optimize policy logic beyond specification
- Add “temporary” exceptions

---

### 4.2 Time Violations
- Use wall-clock time in policy
- Use sleep, timers, or delays
- React mid-window
- Schedule asynchronous policy execution

Time exists only as enforcement windows.

---

### 4.3 Architectural Violations
- Collapse components for convenience
- Introduce reverse dependencies
- Allow policy to access kernel state
- Allow observation to influence decisions
- Allow enforcement to reinterpret policy output
- Introduce hidden shared state

---

### 4.4 Determinism Violations
- Add nondeterministic branching
- Depend on scheduling order
- Depend on race timing
- Use randomization
- Use concurrency in policy logic

---

### 4.5 Enforcement Violations
- Use CPU knobs other than `cpu.max`
- Modify kernel state beyond declared enforcement
- Introduce conditional enforcement logic
- Retry or compensate based on kernel feedback

---

### 4.6 Testing Violations
- Write sleep-based tests
- Rely on wall-clock assertions
- Accept flaky tests
- Use benchmarks as correctness proof
- Relax invariants to satisfy tests

---

## 5. Refusal Rules

An agent **must refuse** to proceed if:

- A requested feature violates SPEC.md or NON_GOALS.md
- A requested change weakens determinism or replayability
- A requested optimization introduces ambiguity
- A requested refactor alters observable behavior
- The specification is insufficient to implement correctly

In refusal cases, the agent must:
- clearly state the violated rule
- cite the relevant document section
- avoid proposing speculative alternatives

---

## 6. Change Classification

Before making a change, the agent must classify it as one of:

- **Implementation** (new code, no semantic change)
- **Refactor** (structure change, provably identical behavior)
- **Correction** (bug fix restoring invariant)
- **Specification Conflict** (cannot proceed)

Only the first three are allowed.

Specification conflicts must halt progress.

---

## 7. Logging and Debugging Rules

An agent may add logging only if:

- Logging does not affect control flow
- Logging does not introduce timing dependence
- Logging does not alter determinism
- Logging can be fully disabled without semantic change

Logging must never be used as policy input.

---

## 8. Optimization Rules

Optimization is allowed only if:

- All invariants remain provably true
- Replay results remain identical
- No new inputs are introduced
- No behavior becomes implicit

Optimization that obscures reasoning is forbidden.

---

## 9. Scope Control

An agent must not:

- Add new resources (e.g. memory) without a full spec
- Add new policy knobs
- Add configuration inference
- Expand system responsibility

Scope creep is a correctness failure.

---

## 10. Failure Rule

If an agent-generated change results in:

- unexplainable behavior
- replay divergence
- invariant violation
- architectural leakage

the change must be reverted.

The agent must not attempt to “fix” violations by weakening rules.

---

## 11. Final Rule

If an agent must choose between:

- producing working code that violates the constitution
- or refusing to generate code

the agent must refuse.

Correctness is mandatory.
Silence is preferable to speculation.

No exceptions.
