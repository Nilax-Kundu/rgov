# VERSIONS.md
## Versioning Model and Progression Rules

rgov versions represent **evidence milestones**, not releases.

A version is complete only when its requirements are proven.
Skipping versions or merging versions is forbidden.

---

## 1. Versioning Philosophy

Each version of rgov must:

- Preserve all guarantees of previous versions
- Add evidence, not heuristics
- Reduce unknowns, not hide them
- Fail loudly if assumptions are violated

Versions are monotonic.
Guarantees may be tightened, never weakened.

---

## 2. Advancement Rule

rgov may advance from version N to N+1 only when:

- All requirements of version N are met
- All tests defined for version N pass
- All invariants remain satisfied
- No new policy inputs were introduced

If a version cannot be completed, it must be fixed or abandoned.
It must not be skipped.

---

## 3. Scope Rule

A version may introduce:

- new evidence
- new test coverage
- new kernel contact
- new resource classes (only when explicitly stated)

A version may not introduce:

- heuristics
- adaptivity
- hidden policy
- weakened determinism

---

## 4. Failure Rule

If implementation at a given version reveals:

- incorrect assumptions
- violated bounds
- kernel behavior outside documented limits

the version must be updated to document the finding.
The spec must not lie to “keep moving”.

---

## 5. Authority

For each version:
- the corresponding `versions/vX.md` file is authoritative
- later versions do not override earlier guarantees
