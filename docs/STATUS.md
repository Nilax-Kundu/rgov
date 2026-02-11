rgov — Project Completion Declaration

Status: COMPLETE
Final Version: v3 (Observability & Causal Transparency)
Reason for Completion: Architectural integrity preserved

What rgov is

rgov is a deterministic, windowed CPU resource governor with:

explicit, declarative contracts

bounded and owned slack

mechanical enforcement

strict workload isolation

causal transparency without interpretation

Every decision made by rgov is:

explainable from recorded facts

replayable offline

attributable to a violated invariant and a specific rule

free of heuristics, adaptivity, or hidden policy

This is not a prototype.
It is a finished system.

What rgov deliberately is not

rgov does not attempt to be:

adaptive

fair beyond declared budgets

latency-aware

“nice” under misconfiguration

predictive

self-correcting

user-protective

Those properties require heuristics and inference.
Heuristics were explicitly rejected.

Why the project stops at v3

Memory support (v4) was evaluated under the same honesty constraints that governed CPU.

That evaluation concluded:

Memory enforcement is destructive and irreversible.

Observation and enforcement do not align cleanly at a windowed boundary.

Kernel reclaim and OOM behavior introduce opaque policy.

Any attempt to soften or hide these facts would violate rgov’s constitution.

Rather than dilute the system with partial truths or sympathetic behavior, memory was rejected.

Rejecting memory is not a limitation.
It is proof that rgov has real boundaries.

What has been proven

Across v0–v3, rgov demonstrated that it is possible to build infrastructure that is:

correct before it is fast

boring before it is clever

explainable before it is convenient

constrained before it is extensible

Most systems compromise these properties gradually.
rgov never did.

Final principle

rgov stops not because it ran out of ideas,
but because adding more would require lying.

That is the correct stopping point.

rgov is complete.