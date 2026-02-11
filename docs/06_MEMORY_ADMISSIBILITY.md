Purpose

This document evaluates whether memory can be governed under the same constitutional principles that define rgov today.

It does not propose an implementation.

It exists to answer one question only:

Can memory be admitted into rgov without violating determinism, replayability, mechanical causality, and honesty?

If the answer is “no”, rgov must stop at v3.

Stopping is a correct outcome.

Non-Negotiable Constraints (Inherited from rgov)

Any memory policy admitted into rgov must satisfy all of the following:

Same abstraction layer for observation and enforcement

What we observe must be exactly what we enforce against.

No inferred or proxy metrics.

Windowed semantics

Decisions occur only at fixed window boundaries.

No mid-window reactions.

Deterministic decisions

Given identical inputs, identical decisions must occur.

Replayability

All decisions must be reproducible offline.

No dependence on timing, kernel callbacks, or async signals.

Mechanical causality

Every enforcement action must map to:

a violated invariant

a specific policy rule

recorded inputs

No heuristics

No smoothing

No prediction

No inference of intent

No “best effort” behavior

If any of these cannot be upheld, memory is inadmissible.

What “Memory” Means in rgov (If Admitted)

If memory is admitted, rgov would define exactly one notion of memory:

Accounted resident memory usage as reported by the kernel at the cgroup boundary.

Not modeled:

Page cache usefulness

Working set size

Hot vs cold pages

Latency

Allocation intent

Application semantics

rgov does not attempt to understand memory.
It only accounts and enforces.

Observation (Candidate)

The only admissible observation would be:

A single cumulative memory usage metric exposed by the kernel

Sampled only at window boundaries

Treated as authoritative truth

Constraints:

No sampling mid-window

No PSI signals

No reclaim feedback

No allocation failure events

No page-level signals

If memory pressure cannot be observed cleanly at window boundaries, memory is inadmissible.

Policy Model (If Admitted)

The only admissible policy shape mirrors CPU exactly:

Declared memory budget (hard cap)

Windowed comparison of observed usage vs budget

Debt or violation tracking (optional, but must be explicit)

No adaptivity

Policy must not:

Gradually squeeze memory

Predict future allocations

Distinguish “temporary” vs “persistent” usage

Attempt to be kind

A workload either respects its memory contract, or it does not.

Enforcement (Critical Section)

Unlike CPU, memory enforcement is destructive.

If memory is admitted, rgov must be explicit about this:

Allowed enforcement actions (if admitted)

Setting a hard memory limit

Triggering kernel-defined reclaim

Allowing the kernel to kill the workload

Explicit truth

Memory enforcement may kill the workload.
This is not a failure mode.
It is correct behavior.

rgov will not:

Retry

Soften

Delay

Apologize

Mask kernel behavior

If enforcement happens, it happens because the contract was violated.

Guarantees (If Memory Is Admitted)

rgov could only guarantee the following:

Attribution: If a workload is killed or reclaimed, the reason is recorded and explainable.

Determinism of decisions: Given identical observations and budgets, the same enforcement decision is made.

No surprise policy: No hidden rules, no dynamic adjustment.

rgov explicitly would not guarantee:

Memory allocation success

Latency bounds

Reclaim smoothness

Graceful degradation

Survival under pressure

Fairness between workloads

Cache friendliness

Performance

Non-Goals (Absolute)

If any of the following are desired, memory must not be admitted:

“Try not to kill things”

“Handle spikes gracefully”

“Be production friendly”

“Protect users from misconfiguration”

“Balance memory dynamically”

“Borrow unused memory”

“Avoid OOMs”

“Do what Kubernetes does”

“Make memory usage feel nice”

Those goals require heuristics.

Heuristics are forbidden.

The Hard Problem (Why This Might Fail)

Memory violates rgov’s model in ways CPU does not:

Overshoot can be fatal before the window closes

Kernel reclaim behavior is opinionated and opaque

Enforcement has irreversible consequences

Observation lag is asymmetric and hostile

If these cannot be owned explicitly and honestly, memory must be rejected.

Decision Criterion

Memory may proceed to v4 only if the following sentence is true without mental gymnastics:

“rgov may kill your workload for violating its declared memory budget,
and this outcome is deterministic, explainable, replayable, and correct.”

If that sentence feels misleading, uncomfortable, or politically difficult:

Do not implement v4.

Final Position

This document exists to fail memory safely.

If memory fits:

proceed to v4 with eyes open

If memory does not fit:

freeze rgov at v3

document the refusal

consider the system complete

Either outcome is success.

rgov’s integrity matters more than symmetry.

End of document.