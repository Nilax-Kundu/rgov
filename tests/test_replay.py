"""
Replay Determinism Tests (v0)

Tests that verify replay determinism per SPEC.md §6 and TESTING.md §2.2.

Spec References:
- SPEC.md §6 (Replayability)
- TESTING.md §2.2 (Replay Tests)
- INVARIANTS.md G1, G2 (Determinism, Replayability)
- v0.md §4 (Required Evidence)
"""

import pytest
from replay import ReplayInput, replay, verify_replay_determinism
from generators import (
    generate_continuous_overshoot,
    generate_alternating_overshoot_undershoot,
    generate_zero_usage,
    generate_boundary_conditions
)


class TestReplayDeterminism:
    """Test that replay is deterministic per INVARIANTS.md G1"""
    
    def test_simple_sequence_determinism(self):
        """Simple observation sequence replays deterministically"""
        replay_input = ReplayInput(
            B=100_000,
            W=100_000,
            observations=[50_000, 100_000, 150_000, 75_000]
        )
        
        assert verify_replay_determinism(replay_input, num_runs=5)
    
    def test_overshoot_sequence_determinism(self):
        """Continuous overshoot replays deterministically"""
        observations = generate_continuous_overshoot(
            B=100_000,
            overshoot_factor=2.0,
            num_windows=100
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        assert verify_replay_determinism(replay_input, num_runs=3)
    
    def test_alternating_sequence_determinism(self):
        """Alternating overshoot/undershoot replays deterministically"""
        observations = generate_alternating_overshoot_undershoot(
            B=100_000,
            overshoot_factor=2.0,
            undershoot_factor=0.5,
            num_cycles=50
        )
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        assert verify_replay_determinism(replay_input, num_runs=3)
    
    def test_zero_usage_determinism(self):
        """Zero usage replays deterministically"""
        observations = generate_zero_usage(num_windows=100)
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        assert verify_replay_determinism(replay_input, num_runs=3)
    
    def test_boundary_conditions_determinism(self):
        """Boundary conditions replay deterministically"""
        observations = generate_boundary_conditions(B=100_000, num_windows=100)
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        assert verify_replay_determinism(replay_input, num_runs=3)


class TestReplayIdentity:
    """Test that identical inputs produce identical outputs"""
    
    def test_identical_observations_produce_identical_history(self):
        """Identical observation sequences produce identical history"""
        observations = [50_000, 150_000, 75_000, 100_000, 0]
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        
        output1 = replay(replay_input)
        output2 = replay(replay_input)
        
        assert len(output1.history) == len(output2.history)
        
        for record1, record2 in zip(output1.history, output2.history):
            assert record1.window_index == record2.window_index
            assert record1.state == record2.state
            assert record1.U_w == record2.U_w
            assert record1.T_w == record2.T_w
    
    def test_different_budgets_produce_different_results(self):
        """Different budgets produce different results (sanity check)"""
        observations = [150_000, 150_000, 150_000]
        
        replay_input1 = ReplayInput(B=100_000, W=100_000, observations=observations)
        replay_input2 = ReplayInput(B=200_000, W=100_000, observations=observations)
        
        output1 = replay(replay_input1)
        output2 = replay(replay_input2)
        
        # With B=100k, should throttle. With B=200k, should not.
        # Verify they produce different results
        assert output1.history != output2.history
    
    def test_different_observations_produce_different_results(self):
        """Different observations produce different results (sanity check)"""
        replay_input1 = ReplayInput(
            B=100_000,
            W=100_000,
            observations=[50_000, 50_000, 50_000]
        )
        replay_input2 = ReplayInput(
            B=100_000,
            W=100_000,
            observations=[150_000, 150_000, 150_000]
        )
        
        output1 = replay(replay_input1)
        output2 = replay(replay_input2)
        
        # Different observations should produce different results
        assert output1.history != output2.history


class TestReplayWithDifferentWindowSizes:
    """Test replay with different window sizes (W is symbolic constant)"""
    
    def test_replay_with_different_W_values(self):
        """Replay works with different W values (symbolic constant)"""
        observations = [50_000, 100_000, 150_000]
        
        # W is symbolic, so different values should still work
        for W in [50_000, 100_000, 200_000]:
            replay_input = ReplayInput(B=100_000, W=W, observations=observations)
            output = replay(replay_input)
            assert len(output.history) == len(observations)
    
    def test_W_does_not_affect_policy_decisions(self):
        """W is symbolic and does not affect policy decisions"""
        observations = [50_000, 150_000, 75_000]
        B = 100_000
        
        # Replay with different W values
        replay_input1 = ReplayInput(B=B, W=100_000, observations=observations)
        replay_input2 = ReplayInput(B=B, W=200_000, observations=observations)
        
        output1 = replay(replay_input1)
        output2 = replay(replay_input2)
        
        # Policy decisions should be identical (W is just carried through)
        for record1, record2 in zip(output1.history, output2.history):
            assert record1.state == record2.state
            assert record1.T_w == record2.T_w


class TestReplayLogging:
    """Test that replay produces correct logging output per SPEC.md §6.2"""
    
    def test_replay_logs_all_windows(self):
        """Replay logs all windows"""
        observations = [50_000, 100_000, 150_000, 75_000, 0]
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        assert len(output.history) == len(observations)
    
    def test_replay_logs_contain_required_fields(self):
        """Replay logs contain (window_index, state, debt, U_w, T_w) per SPEC.md §6.2"""
        observations = [150_000, 50_000]
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        for i, record in enumerate(output.history):
            # Verify all required fields are present
            assert record.window_index == i
            assert record.state is not None
            assert record.state.debt >= 0  # Can access debt
            assert record.U_w == observations[i]
            assert record.T_w >= 0
    
    def test_window_indices_are_sequential(self):
        """Window indices are sequential starting from 0"""
        observations = [50_000, 100_000, 150_000, 75_000]
        
        replay_input = ReplayInput(B=100_000, W=100_000, observations=observations)
        output = replay(replay_input)
        
        for i, record in enumerate(output.history):
            assert record.window_index == i
