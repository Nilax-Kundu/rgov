# NON_GOALS.md
## Explicitly Rejected Goals and Features

This document defines what rgov **does not attempt to do**.

These are not missing features.
They are **intentional exclusions**.

Requests to add any item listed here must be rejected without debate.
Doing so preserves determinism, replayability, and explainability.

This document is normative.

---

## 1. Philosophy of Non-Goals

rgov is designed to be:
- deterministic
- bounded
- explainable
- conservative

Anything that introduces:
- heuristics
- inference
- adaptivity
- hidden state
- subjective improvement

is incompatible with rgov’s design.

Non-goals are first-class design decisions.

---

## 2. Performance and Optimization Non-Goals

rgov does **not** aim to:

- Maximize throughput
- Maximize utilization
- Win performance benchmarks
- Compete with schedulers on efficiency
- Optimize for bursty workloads
- Hide or amortize cost spikes

Correctness precedes performance.

If a workload performs poorly under rgov,
the declared budget is likely incorrect.

---

## 3. Latency and Responsiveness Non-Goals

rgov does **not** provide:

- Latency guarantees
- Response-time guarantees
- Deadline scheduling
- Tail-latency optimization
- Jitter minimization
- Interactive responsiveness tuning

rgov enforces resource contracts, not user experience.

Latency-sensitive workloads require different systems.

---

## 4. Fairness and Policy Non-Goals

rgov does **not** attempt to:

- Enforce fairness beyond declared budgets
- Balance workloads dynamically
- Resolve contention automatically
- Infer “importance” of tasks
- Adjust priorities at runtime

Fairness exists only in declared contracts.

Anything else is heuristic.

---

## 5. Adaptivity and Intelligence Non-Goals

rgov explicitly rejects:

- Auto-tuning
- Adaptive budgets
- Feedback control loops
- Learning-based policies
- ML-driven decisions
- Historical smoothing
- Predictive scheduling

rgov is not a control system.
rgov is a governor.

---

## 6. Scheduler Interaction Non-Goals

rgov does **not** aim to:

- Replace the Linux scheduler
- Compete with CFS
- Influence scheduling decisions directly
- Use scheduler hints
- Interpret scheduler state

Specifically forbidden:
- cpu.weight
- cpu.uclamp
- RT scheduling classes
- Per-task priority manipulation

rgov operates above the scheduler, not within it.

---

## 7. Abstraction and Convenience Non-Goals

rgov does **not** attempt to:

- Be transparent or invisible
- Automatically “do the right thing”
- Protect users from misconfiguration
- Smooth rough edges
- Provide convenience abstractions

Misconfiguration must be detectable, not hidden.

---

## 8. Scope and Integration Non-Goals

rgov does **not** aim to:

- Be a container runtime
- Replace systemd
- Replace Kubernetes
- Provide orchestration
- Manage lifecycles
- Coordinate distributed systems

rgov is a local, single-host governor.

---

## 9. Observability Non-Goals

rgov does **not** attempt to:

- Provide rich dashboards
- Visualize performance trends
- Aggregate metrics across time
- Produce insights or recommendations

rgov explains decisions, not systems.

---

## 10. Error Handling Non-Goals

rgov does **not**:

- Recover silently from invalid states
- Correct bad configurations
- Mask kernel behavior
- Retry policy decisions heuristically

Invalid configurations must fail loudly.

---

## 11. Extensibility Non-Goals

rgov does **not** support:

- Plugins
- Policy injection
- User-defined heuristics
- Runtime policy modification

Extensibility that weakens guarantees is forbidden.

---

## 12. Compatibility Non-Goals

rgov does **not** aim to:

- Support non-Linux systems
- Support cgroups v1
- Support legacy kernels
- Support heterogeneous policy backends

Constraints are intentional.

---

## 13. Final Rule

If a proposed feature:

- increases convenience
- improves subjective experience
- reduces user effort
- hides system behavior

at the cost of:
- determinism
- replayability
- explainability
- bounded behavior

the feature must be rejected.

rgov prefers being strict, explicit, and sometimes unpleasant
over being flexible, adaptive, or surprising.

No exceptions.
