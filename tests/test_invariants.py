"""
Policy Invariant Tests (v0)

Tests that assert all policy invariants are preserved.

Spec References:
- INVARIANTS.md §4 (Policy State Invariants)
- TESTING.md §2.3 (Invariant Tests)
"""

import pytest
from policy import (
    PolicyState, PolicyStateData, EnforcementDecision,
    evaluate_policy, initial_state
)


class TestInvariantP1:
    """P1: debt >= 0 (non-negative debt)"""
    
    def test_initial_state_has_zero_debt(self):
        """Initial state must have debt = 0"""
        state = initial_state()
        assert state.debt == 0
    
    def test_debt_never_negative_after_overshoot(self):
        """Debt remains non-negative after overshoot"""
        state = initial_state()
        B = 100_000  # 100ms
        W = 100_000
        U_w = 150_000  # 50% overshoot
        
        next_state, _ = evaluate_policy(state, U_w, B, W)
        assert next_state.debt >= 0
    
    def test_debt_never_negative_after_undershoot(self):
        """Debt remains non-negative after undershoot"""
        # Start with some debt
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=10_000)
        B = 100_000
        W = 100_000
        U_w = 50_000  # 50% undershoot
        
        next_state, _ = evaluate_policy(state, U_w, B, W)
        assert next_state.debt >= 0
    
    def test_debt_never_negative_with_large_undershoot(self):
        """Debt floors at 0 even with large undershoot"""
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=10_000)
        B = 100_000
        W = 100_000
        U_w = 0  # Complete undershoot
        
        next_state, _ = evaluate_policy(state, U_w, B, W)
        assert next_state.debt == 0  # Should floor at 0, not go negative


class TestInvariantP2:
    """P2: 0 <= T_w <= B (budget bound)"""
    
    def test_T_w_within_bounds_normal_state(self):
        """T_w is within [0, B] in normal state"""
        state = initial_state()
        B = 100_000
        W = 100_000
        U_w = 50_000
        
        _, decision = evaluate_policy(state, U_w, B, W)
        assert 0 <= decision.T_w <= B
    
    def test_T_w_within_bounds_throttled_state(self):
        """T_w is within [0, B] in throttled state"""
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=50_000)
        B = 100_000
        W = 100_000
        U_w = 50_000
        
        _, decision = evaluate_policy(state, U_w, B, W)
        assert 0 <= decision.T_w <= B
    
    def test_T_w_equals_B_when_no_debt(self):
        """T_w equals B when debt is 0"""
        state = initial_state()
        B = 100_000
        W = 100_000
        U_w = 50_000
        
        _, decision = evaluate_policy(state, U_w, B, W)
        assert decision.T_w == B
    
    def test_T_w_equals_zero_when_debt_exists(self):
        """T_w equals 0 when debt > 0"""
        # Use debt large enough that it won't be fully paid down
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=60_000)
        B = 100_000
        W = 100_000
        U_w = 50_000  # 50k deficit, reduces debt to 10k
        
        _, decision = evaluate_policy(state, U_w, B, W)
        # Debt still exists (10k), so T_w should be 0
        assert decision.T_w == 0


class TestInvariantP3:
    """P3: No throttling without excess (throttle only when debt > 0)"""
    
    def test_no_throttling_at_start(self):
        """No throttling at initial state (debt = 0)"""
        state = initial_state()
        assert state.state == PolicyState.NORMAL
    
    def test_throttling_only_after_overshoot(self):
        """Throttling occurs only after overshoot creates debt"""
        state = initial_state()
        B = 100_000
        W = 100_000
        
        # First window: undershoot, should remain NORMAL
        U_w = 50_000
        next_state, _ = evaluate_policy(state, U_w, B, W)
        assert next_state.state == PolicyState.NORMAL
        assert next_state.debt == 0
        
        # Second window: overshoot, should transition to THROTTLED
        U_w = 150_000
        next_state, _ = evaluate_policy(next_state, U_w, B, W)
        assert next_state.state == PolicyState.THROTTLED
        assert next_state.debt > 0
    
    def test_throttling_is_function_of_debt(self):
        """Throttling is determined by debt, not current U_w"""
        # Even if current window is under budget, throttle if debt exists
        # Use larger debt so it's not fully paid down in one window
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=60_000)
        B = 100_000
        W = 100_000
        U_w = 50_000  # Current window under budget (50k deficit)
        
        next_state, decision = evaluate_policy(state, U_w, B, W)
        # Debt reduced from 60k to 10k (60k - 50k deficit = 10k remaining)
        # Still throttled because debt still exists (though reduced)
        assert next_state.debt == 10_000
        assert next_state.state == PolicyState.THROTTLED
        assert decision.T_w == 0


class TestInvariantP4:
    """P4: Debt decreases only when U_w < B"""
    
    def test_debt_increases_on_overshoot(self):
        """Debt increases when U_w > B"""
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=10_000)
        B = 100_000
        W = 100_000
        U_w = 150_000  # Overshoot
        
        next_state, _ = evaluate_policy(state, U_w, B, W)
        assert next_state.debt > state.debt
    
    def test_debt_decreases_on_undershoot(self):
        """Debt decreases when U_w < B"""
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=50_000)
        B = 100_000
        W = 100_000
        U_w = 50_000  # Undershoot
        
        next_state, _ = evaluate_policy(state, U_w, B, W)
        assert next_state.debt < state.debt
    
    def test_debt_unchanged_at_exact_budget(self):
        """Debt unchanged when U_w == B"""
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=50_000)
        B = 100_000
        W = 100_000
        U_w = 100_000  # Exact budget
        
        next_state, _ = evaluate_policy(state, U_w, B, W)
        assert next_state.debt == state.debt


class TestInvariantP5:
    """P5: state == NORMAL => debt == 0 (normal-state cleanliness)"""
    
    def test_initial_state_is_normal_with_zero_debt(self):
        """Initial state is NORMAL with debt = 0"""
        state = initial_state()
        assert state.state == PolicyState.NORMAL
        assert state.debt == 0
    
    def test_transition_to_normal_only_when_debt_zero(self):
        """Transition to NORMAL only when debt reaches 0"""
        # Start with debt
        state = PolicyStateData(state=PolicyState.THROTTLED, debt=50_000)
        B = 100_000
        W = 100_000
        
        # Pay down debt partially
        U_w = 0
        next_state, _ = evaluate_policy(state, U_w, B, W)
        # Debt should be 0 now (50k debt - 100k deficit = 0)
        assert next_state.debt == 0
        assert next_state.state == PolicyState.NORMAL
    
    def test_cannot_construct_normal_state_with_debt(self):
        """Cannot construct NORMAL state with debt > 0 (assertion should fail)"""
        with pytest.raises(AssertionError, match="Invariant P5 violated"):
            PolicyStateData(state=PolicyState.NORMAL, debt=1)


class TestInvariantP6:
    """P6: Deterministic transitions (identical inputs => identical outputs)"""
    
    def test_identical_inputs_produce_identical_outputs(self):
        """Same inputs produce same outputs"""
        state = initial_state()
        B = 100_000
        W = 100_000
        U_w = 75_000
        
        # Run twice with identical inputs
        next_state1, decision1 = evaluate_policy(state, U_w, B, W)
        next_state2, decision2 = evaluate_policy(state, U_w, B, W)
        
        assert next_state1 == next_state2
        assert decision1.T_w == decision2.T_w
    
    def test_determinism_across_multiple_windows(self):
        """Determinism holds across multiple windows"""
        observations = [50_000, 150_000, 75_000, 100_000, 0]
        B = 100_000
        W = 100_000
        
        # Run sequence twice
        def run_sequence():
            state = initial_state()
            results = []
            for U_w in observations:
                state, decision = evaluate_policy(state, U_w, B, W)
                results.append((state, decision.T_w))
            return results
        
        results1 = run_sequence()
        results2 = run_sequence()
        
        assert results1 == results2


class TestInvariantAssertions:
    """Test that invariant violations trigger assertions"""
    
    def test_negative_debt_assertion(self):
        """Negative debt triggers assertion"""
        with pytest.raises(AssertionError, match="Invariant P1 violated"):
            PolicyStateData(state=PolicyState.THROTTLED, debt=-1)
    
    def test_negative_T_w_assertion(self):
        """Negative T_w triggers assertion"""
        with pytest.raises(AssertionError, match="Invariant P2 violated"):
            EnforcementDecision(T_w=-1)
    
    def test_invalid_U_w_assertion(self):
        """Negative U_w triggers assertion"""
        state = initial_state()
        B = 100_000
        W = 100_000
        
        with pytest.raises(AssertionError, match="Invalid input: U_w"):
            evaluate_policy(state, U_w=-1, B=B, W=W)
    
    def test_invalid_budget_assertion(self):
        """Invalid budget triggers assertion"""
        state = initial_state()
        W = 100_000
        
        with pytest.raises(AssertionError, match="Invalid input: B"):
            evaluate_policy(state, U_w=50_000, B=0, W=W)
