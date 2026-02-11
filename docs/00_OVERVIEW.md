# rgov Documentation Overview

This directory contains the complete, frozen specification and rationale for **rgov**, a deterministic workload regulator.

rgov is a **finished system**.  
No future versions are planned beyond v3.

The documents here describe:
- what the system guarantees
- how those guarantees are enforced
- what the system explicitly refuses to do
- and why the project stops where it does

This is a reference corpus, not a roadmap.

---

## How to Read These Documents

Readers are encouraged to follow the documents in order.

Each file answers a **different class of question** and is intentionally scoped.  
No single document is sufficient on its own.

### Recommended Reading Order

1. **SPEC.md**  
   Defines the system’s behavior, guarantees, and formal policy rules.  
   This is the authoritative description of *what rgov does*.

2. **ARCHITECTURE.md**  
   Describes the component structure and dependency boundaries that enforce the specification.  
   This explains *how the system is prevented from violating the spec*.

3. **INVARIANTS.md**  
   Lists the conditions that must never be violated.  
   Any invariant violation implies the system is incorrect.

4. **TESTING.md**  
   Describes how correctness is verified and what the test suite proves.  
   Tests exist to assert invariants, not to benchmark performance.

5. **NON_GOALS.md**  
   Enumerates behaviors and features rgov explicitly rejects.  
   This document is a defense against scope creep and heuristic drift.

6. **MEMORY_ADMISSIBILITY.md**  
   Evaluates memory governance under the same constitutional constraints and formally rejects it.  
   This document records a deliberate refusal, not a future plan.

7. **VERSIONS.md**  
   Describes the historical evolution of rgov from v0 to v3.  
   This document is archival; no further versions are planned.

8. **process/AGENT_RULES.md**  
   Records the constraints imposed on automated implementation during development.  
   This document is not part of the runtime specification and has no effect on system behavior.

9. **STATUS.md**  
   Declares the project complete and explains why stopping at v3 is the correct outcome.

---

## What These Documents Are Not

These documents do **not**:
- propose future features
- describe adaptive behavior
- explain performance optimizations
- provide operational tuning guidance
- justify decisions with heuristics or intent

rgov is intentionally conservative and explicit.  
Anything not written here does not exist.

---

## Final Note

rgov’s documentation is intentionally strict and repetitive.  
Redundancy is used to reinforce boundaries, not to simplify reading.

If a behavior is surprising but explainable from these documents, the system is correct.  
If a behavior cannot be explained from these documents, the system is broken.

This overview exists to make that line unambiguous.
