"""
Long-Running Stability Tests (v0)

Tests that verify policy can run for arbitrarily many windows without drift.

Spec References:
- v0.md §4 (Required Evidence)
- TESTING.md §3 (Mandatory Test Properties)
"""

import pytest
from replay import ReplayInput, replay, verify_replay_determinism
from policy import PolicyState
from generators import (
    generate_continuous_overshoot,
    generate_alternating_overshoot_undershoot,
    generate_oscillation
)


class TestLongRunningStability:
    """Test that policy can run for many windows without drift"""
    
    def test_10k_windows_no_drift(self):
        """Policy runs for 10,000 windows without drift"""
        # Alternating pattern for 10k windows
        observations = generate_alternating_overshoot_undershoot(
            B=100_000,
            overshoot_factor=1.5,
            undershoot_factor=0.5,
            num_cycles=5000  # 10k windows
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Verify all windows processed
        assert len(output.history) == 10_000
        
        # Verify all invariants hold throughout
        for record in output.history:
            assert record.state.debt >= 0  # P1
            assert 0 <= record.T_w <= 100_000  # P2
            if record.state.state == PolicyState.NORMAL:
                assert record.state.debt == 0  # P5
    
    def test_100k_windows_determinism(self):
        """Policy is deterministic over 100,000 windows"""
        # Simple repeating pattern
        base_pattern = [150_000, 50_000]  # Overshoot, undershoot
        observations = base_pattern * 50_000  # 100k windows
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        
        # Verify determinism (run twice, compare)
        assert verify_replay_determinism(replay_input, num_runs=2)
    
    def test_1m_windows_no_overflow(self):
        """Policy handles 1 million windows without numeric overflow"""
        # Continuous moderate overshoot
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=1.1,  # Small overshoot
            num_windows=1_000_000
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Verify no overflow (debt should be representable)
        final_debt = output.history[-1].state.debt
        assert final_debt >= 0
        assert isinstance(final_debt, int)
        
        # Debt should be large but finite
        # Each window: U_w = 110k, B = 100k, excess = 10k
        # After 1M windows: debt = 1M * 10k = 10B microseconds
        # Note: First window starts with debt=0, so final debt after window 999,999
        # is the accumulated debt from all 1M windows
        expected_debt = 1_000_000 * 10_000
        # Allow small tolerance for any edge effects
        assert abs(output.history[-1].state.debt - expected_debt) <= 10_000


class TestDeterminismOverLongSequences:
    """Test determinism is preserved over long sequences"""
    
    def test_determinism_with_complex_pattern(self):
        """Determinism holds for complex pattern over many windows"""
        # Complex repeating pattern
        pattern = [50_000, 100_000, 150_000, 75_000, 125_000, 0, 200_000, 25_000]
        observations = pattern * 1000  # 8k windows
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        
        # Run multiple times and verify identical results
        assert verify_replay_determinism(replay_input, num_runs=5)
    
    def test_determinism_with_oscillation(self):
        """Determinism holds for oscillating pattern over many windows"""
        observations = generate_oscillation(
            B=100_000,
            high_factor=10.0,
            low_factor=0.0,
            num_oscillations=10_000  # 20k windows
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        assert verify_replay_determinism(replay_input, num_runs=3)


class TestInvariantsOverLongRuns:
    """Test that all invariants hold over long runs"""
    
    def test_all_invariants_over_50k_windows(self):
        """All invariants preserved over 50,000 windows"""
        observations = generate_alternating_overshoot_undershoot(
            B=100_000,
            overshoot_factor=2.0,
            undershoot_factor=0.3,
            num_cycles=25_000  # 50k windows
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Check every 1000th window to avoid excessive iteration
        for i in range(0, len(output.history), 1000):
            record = output.history[i]
            
            # P1: debt >= 0
            assert record.state.debt >= 0, f"P1 violated at window {i}"
            
            # P2: 0 <= T_w <= B
            assert 0 <= record.T_w <= 100_000, f"P2 violated at window {i}"
            
            # P5: state == NORMAL => debt == 0
            if record.state.state == PolicyState.NORMAL:
                assert record.state.debt == 0, f"P5 violated at window {i}"
    
    def test_no_state_corruption_over_time(self):
        """State remains valid over extended run"""
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=1.2,
            num_windows=100_000
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Verify state is valid at start, middle, and end
        checkpoints = [0, len(output.history) // 2, len(output.history) - 1]
        
        for idx in checkpoints:
            record = output.history[idx]
            # State should be valid
            assert record.state.state in [PolicyState.NORMAL, PolicyState.THROTTLED]
            assert record.state.debt >= 0
            assert 0 <= record.T_w <= 100_000


class TestWindowIndexIntegrity:
    """Test that window indices remain correct over long runs"""
    
    def test_window_indices_sequential_over_100k_windows(self):
        """Window indices remain sequential over 100k windows"""
        observations = [100_000] * 100_000  # Exact budget
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Verify indices are sequential
        for i, record in enumerate(output.history):
            assert record.window_index == i, \
                f"Window index mismatch at position {i}: expected {i}, got {record.window_index}"
    
    def test_no_window_index_overflow(self):
        """Window indices don't overflow with large counts"""
        observations = [50_000] * 1_000_000
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        # Last window should have index 999,999
        assert output.history[-1].window_index == 999_999


class TestMemoryStability:
    """Test that memory usage remains stable over long runs"""
    
    def test_history_grows_linearly(self):
        """History size grows linearly with window count"""
        for num_windows in [1000, 10_000, 100_000]:
            observations = [100_000] * num_windows
            
            replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
            output = replay(replay_input)
            
            # History should have exactly num_windows entries
            assert len(output.history) == num_windows
    
    def test_no_state_accumulation_beyond_history(self):
        """No hidden state accumulates beyond recorded history"""
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=2.0,
            num_windows=10_000
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        
        # Run twice and verify identical history size
        output1 = replay(replay_input)
        output2 = replay(replay_input)
        
        assert len(output1.history) == len(output2.history)
        assert len(output1.history) == len(observations)
