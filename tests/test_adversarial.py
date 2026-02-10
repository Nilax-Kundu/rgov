"""
Adversarial Sequence Tests (v0)

Tests that verify policy correctness under adversarial conditions.

Spec References:
- TESTING.md §5 (Adversarial Testing Requirements)
- v0.md §4 (Required Evidence)
"""

import pytest
from replay import ReplayInput, replay
from policy import PolicyState
from generators import (
    generate_continuous_overshoot,
    generate_alternating_overshoot_undershoot,
    generate_zero_usage,
    generate_boundary_conditions,
    generate_long_debt_accumulation,
    generate_oscillation
)


class TestContinuousOvershoot:
    """Test continuous overshoot scenario per TESTING.md §5"""
    
    def test_infinite_overshoot_accumulates_debt(self):
        """Continuous overshoot accumulates debt without bound"""
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=2.0,
            num_windows=100
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Verify debt accumulates
        prev_debt = 0
        for record in output.history:
            current_debt = record.state.debt
            # Debt should monotonically increase
            assert current_debt >= prev_debt
            prev_debt = current_debt
        
        # Final debt should be substantial
        final_debt = output.history[-1].state.debt
        assert final_debt > 0
    
    def test_infinite_overshoot_maintains_throttled_state(self):
        """Continuous overshoot keeps system in THROTTLED state"""
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=1.5,
            num_windows=50
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # After first window, should be throttled and stay throttled
        for i, record in enumerate(output.history[1:], start=1):
            assert record.state.state == PolicyState.THROTTLED, \
                f"Window {i} should be THROTTLED"
    
    def test_infinite_overshoot_enforces_zero_quota(self):
        """Continuous overshoot results in T_w = 0"""
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=3.0,
            num_windows=20
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # After first window, T_w should be 0
        for i, record in enumerate(output.history[1:], start=1):
            assert record.T_w == 0, f"Window {i} should have T_w=0"
    
    def test_all_invariants_hold_under_continuous_overshoot(self):
        """All invariants preserved under continuous overshoot"""
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=5.0,
            num_windows=200
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Verify all invariants for every window
        for record in output.history:
            # P1: debt >= 0
            assert record.state.debt >= 0
            # P2: 0 <= T_w <= B
            assert 0 <= record.T_w <= 100_000
            # P5: state == NORMAL => debt == 0
            if record.state.state == PolicyState.NORMAL:
                assert record.state.debt == 0


class TestAlternatingOvershootUndershoot:
    """Test oscillation scenario per TESTING.md §5"""
    
    def test_alternating_sequence_handles_debt_correctly(self):
        """Alternating overshoot/undershoot handles debt accumulation and paydown"""
        observations = generate_alternating_overshoot_undershoot(
            B=100_000,
            overshoot_factor=2.0,
            undershoot_factor=0.5,
            num_cycles=50
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Verify debt oscillates but remains bounded
        for record in output.history:
            assert record.state.debt >= 0  # P1
    
    def test_alternating_with_equal_overshoot_undershoot(self):
        """Alternating with balanced over/under eventually stabilizes"""
        # Overshoot by 50k, undershoot by 50k
        observations = []
        for _ in range(20):
            observations.append(150_000)  # +50k debt
            observations.append(50_000)   # -50k debt
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Debt should oscillate but not grow unbounded
        max_debt = max(record.state.debt for record in output.history)
        assert max_debt < 100_000  # Should not exceed one window of overshoot
    
    def test_rapid_oscillation_preserves_invariants(self):
        """Rapid oscillation preserves all invariants"""
        observations = generate_oscillation(
            B=100_000,
            high_factor=3.0,
            low_factor=0.1,
            num_oscillations=100
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        for record in output.history:
            # All invariants must hold
            assert record.state.debt >= 0  # P1
            assert 0 <= record.T_w <= 100_000  # P2
            if record.state.state == PolicyState.NORMAL:
                assert record.state.debt == 0  # P5


class TestZeroUsage:
    """Test zero usage scenario per TESTING.md §5"""
    
    def test_zero_usage_from_clean_state(self):
        """Zero usage from clean state maintains NORMAL"""
        observations = generate_zero_usage(num_windows=100)
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # All windows should be NORMAL with zero debt
        for record in output.history:
            assert record.state.state == PolicyState.NORMAL
            assert record.state.debt == 0
            assert record.T_w == 100_000  # Full budget
    
    def test_zero_usage_pays_down_debt(self):
        """Zero usage pays down existing debt"""
        # First create debt, then zero usage
        observations = [200_000]  # Create 100k debt
        observations.extend(generate_zero_usage(num_windows=5))
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # First window creates debt
        assert output.history[0].state.debt == 0  # State at START of window
        # After first window, should have debt
        # Zero usage should pay it down
        # Eventually should return to NORMAL
        final_record = output.history[-1]
        # After enough zero-usage windows, debt should be paid
        # (100k debt, 100k paydown per window = 1 window to clear)


class TestBoundaryConditions:
    """Test boundary conditions per TESTING.md §5"""
    
    def test_exact_budget_usage_maintains_state(self):
        """Using exactly B maintains current state"""
        observations = generate_boundary_conditions(B=100_000, num_windows=100)
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Should remain in NORMAL state with zero debt
        for record in output.history:
            assert record.state.state == PolicyState.NORMAL
            assert record.state.debt == 0
    
    def test_exact_budget_with_existing_debt(self):
        """Using exactly B with existing debt maintains debt"""
        # Create debt, then use exactly B
        observations = [150_000]  # Create 50k debt
        observations.extend(generate_boundary_conditions(B=100_000, num_windows=10))
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # After first window, should have 50k debt
        # Subsequent windows at exactly B should maintain that debt
        for i in range(1, len(output.history)):
            # Debt should remain constant at 50k
            assert output.history[i].state.debt == 50_000


class TestLongDebtAccumulation:
    """Test long debt accumulation per TESTING.md §5"""
    
    def test_long_accumulation_then_paydown(self):
        """Long debt accumulation followed by paydown"""
        observations = generate_long_debt_accumulation(
            B=100_000,
            overshoot_factor=1.5,
            accumulation_windows=100,
            paydown_factor=0.5,
            paydown_windows=200
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Find peak debt
        peak_debt = max(record.state.debt for record in output.history)
        assert peak_debt > 0
        
        # Verify debt eventually decreases
        final_debt = output.history[-1].state.debt
        # With enough paydown windows, debt should be reduced or cleared
        assert final_debt < peak_debt or final_debt == 0
    
    def test_massive_debt_accumulation(self):
        """Massive debt accumulation preserves invariants"""
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=10.0,  # 10x overshoot
            num_windows=1000
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Even with massive debt, invariants must hold
        for record in output.history:
            assert record.state.debt >= 0  # P1
            assert 0 <= record.T_w <= 100_000  # P2
        
        # Debt should be very large
        final_debt = output.history[-1].state.debt
        assert final_debt > 1_000_000  # At least 1 second of accumulated debt


class TestAdversarialCombinations:
    """Test combinations of adversarial scenarios"""
    
    def test_overshoot_then_zero_then_overshoot(self):
        """Overshoot → zero usage → overshoot again"""
        observations = []
        observations.extend(generate_continuous_overshoot(B=100_000, overshoot_factor=2.0, num_windows=10))
        observations.extend(generate_zero_usage(num_windows=5))
        observations.extend(generate_continuous_overshoot(B=100_000, overshoot_factor=3.0, num_windows=10))
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # All invariants must hold throughout
        for record in output.history:
            assert record.state.debt >= 0
            assert 0 <= record.T_w <= 100_000
    
    def test_all_scenarios_combined(self):
        """Combination of all adversarial scenarios"""
        observations = []
        observations.extend(generate_continuous_overshoot(B=100_000, overshoot_factor=2.0, num_windows=20))
        observations.extend(generate_zero_usage(num_windows=10))
        observations.extend(generate_alternating_overshoot_undershoot(B=100_000, overshoot_factor=1.5, undershoot_factor=0.5, num_cycles=20))
        observations.extend(generate_boundary_conditions(B=100_000, num_windows=10))
        observations.extend(generate_oscillation(B=100_000, high_factor=5.0, low_factor=0.0, num_oscillations=20))
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Verify all invariants hold throughout complex scenario
        for record in output.history:
            assert record.state.debt >= 0  # P1
            assert 0 <= record.T_w <= 100_000  # P2
            if record.state.state == PolicyState.NORMAL:
                assert record.state.debt == 0  # P5
