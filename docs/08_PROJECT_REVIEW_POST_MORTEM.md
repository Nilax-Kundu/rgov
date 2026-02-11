# Post-Mortem Architectural Review (Non-Normative)

This document is a post-mortem architectural evaluation written in an external-review style.
It does not define requirements, guarantees, or behavior.
In case of conflict, this document has no authority.

## 1. Executive Summary
rgov v3 is a technically sovereign system. It succeeds by rejecting the "Resource Management" trap and strictly adhering to "Resource Governance." By enforcing declarative contracts through a deterministic state machine and verifiable cgroup bindings, it achieves a level of mechanical honesty rarely found in infrastructure tools.

## 2. Technical Strengths

### The "Closing Bracket" Strategy
The project's greatest asset is its defined end. Most software expands until it fails; rgov stops where its guarantees would necessitate heuristics. The rejection of Memory (v4) is a masterclass in architectural integrity—it prioritizes the system's "constitution" over feature-parity.

### Causal Projection (v3)
The `DecisionRecord` and structured logging are not just "observability"—they are **mechanical evidence**. By ensuring that every enforcement action is a read-only projection of the state machine, rgov eliminates the "explanation-reality gap" that plagues complex governors.

### Determinism & Replayability
The decoupling of the `Policy Layer` from the `Orchestrator` (v0 inheritance) makes the system auditable. The ability to verify deterministic behavior via `replay.py` across 70+ test cases provides a quantitative proof of correctness that exceeds typical integration testing.

## 3. Vulnerabilities & Considerations

### The "Governor's Lag"
rgov owns its lag (≤ 1 window), but this is a double-edged sword. In environments with extreme micro-bursting, the discretization of time into 100ms units means the kernel `cpu.max` may be "trailing the truth." This is an acceptable trade-off for determinism, but requires users to understand that they are buying **Borne Accuracy**, not **Real-Time Responsiveness**.

### Kernel Dependency
The system is as honest as the kernel's `cpu.stat`. While the `v1` bindings are clean, rgov is technically a passenger of the Linux accounting subsystem. If the kernel's usage reporting drifts, rgov's decisions will be "locally correct" (per inputs) but "globally drifted" (per physical reality).

## 4. Final Verdict
rgov is **finished**. 

It is not a Swiss Army knife; it is a **Torque Wrench**. It does one thing with extreme precision and refuses to be used for anything else. Pushing this to GitHub marks the archive of a system that serves as a benchmark for how to build "Honest Infrastructure."

---
*Reviewer: rgov maintainer*
