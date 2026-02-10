# rgov v0 - Policy Simulator

Pure policy simulator for rgov. No kernel interaction, no timing, no real workloads.

## v0 Scope

- CPU policy state machine
- Enforcement window logic (pure)
- Replay harness
- Synthetic observation generators
- Comprehensive test suite

## Running Tests

```bash
pytest tests/ -v
```

## v0 Completion Criteria

- [ ] All policy invariants are asserted and never violated
- [ ] Replay of identical U_w sequences produces identical results
- [ ] Adversarial sequences (infinite overshoot, oscillation, zero usage) are handled correctly
- [ ] Policy can run for arbitrarily many windows without drift
