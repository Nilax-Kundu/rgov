# rgov

**A deterministic, rule-constrained workload regulator.**

rgov is a deterministic CPU resource governor for Linux.

It enforces declared CPU budgets using fixed rules and recorded facts — not heuristics, prediction, or best-effort scheduling.

Given the same inputs, rgov will always make the same decision.  
Every enforcement action is explainable, replayable, and tied to a violated invariant.

This project is intentionally feature-complete.

> "rgov stops not because it ran out of ideas, but because adding more would require lying."

---

### Project Status: COMPLETE (v3)

**rgov is intentionally feature-complete.** Every resource domain admitted into the core (CPU) satisfies the project's strict constitutional requirements for determinism and causal transparency. Additional domains, such as Memory (v4), were evaluated and deliberately rejected because their enforcement mechanisms (destructive OOM, opaque kernel reclaim) would have compromised the system's honesty.

rgov remains as a reference artifact for infrastructure that prioritizes correctness and mechanical explainability over heuristic adaptivity.

---

## Core Philosophy

rgov represents a departure from adaptive or heuristic-driven infrastructure. rgov is not a scheduler and does not optimize execution; it enforces declared resource contracts. It is built on three non-negotiable pillars:

1.  **Deterministic Enforcement**: Given the same inputs and budget, the system will always make the same enforcement decision. No smoothing, no prediction, no "best effort."
2.  **Causal Transparency**: Every decision is a read-only projection of recorded facts. If a workload is throttled, the system provides a `DecisionRecord` that maps exactly to a violated invariant and a specific rule.
3.  **Strict Isolation**: Workload states are logically distinct and execution is isolated. One workload's overshoot cannot influence another's budget.

## Capabilities

- **Deterministic CPU Governance**: Windowed regulation mapping $(state, observation, budget) \to (enforcement)$.
- **Structured Logging (v3)**: Machine-parsable JSON traces for every decision, optimized for offline replay and audit.
- **Multi-Workload Orchestration (v2)**: Support for $N$ workloads with strict state isolation and safety boundaries.
- **Kernel Binding (v1)**: Direct integration with Linux `cgroups` for authoritative enforcement.

## Documentation

rgov is governed by a detailed specification. Please refer to the `docs/` directory for technical depth:

- [**SPEC.md**](docs/SPEC.md): The core mathematical and architectural specification.
- [**INVARIANTS.md**](docs/INVARIANTS.md): The formal definitions of system safety and correctness.
- [**STATUS.md**](docs/STATUS.md): The final project completion declaration and rationale.
- [**MEMORY_ADMISSIBILITY.md**](docs/MEMORY_ADMISSIBILITY.md): The architectural evaluation and refusal of memory governance.

## Verification

rgov is backed by a rigorous test suite that asserts determinism and invariant preservation across 70+ scenarios, including adversarial edge cases.

```bash
python -m pytest tests/ -v
```

---

*rgov. Correctness before convenience.*
