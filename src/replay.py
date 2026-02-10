"""
Replay Harness (v0)

This module implements the replay harness for determinism verification.

The harness accepts recorded observations and replays policy decisions
to prove determinism per SPEC.md §6 and TESTING.md §2.2.

Spec References:
- SPEC.md §6 (Replayability)
- TESTING.md §2.2 (Replay Tests)
- INVARIANTS.md G1, G2 (Determinism, Replayability)
"""

from typing import List
from dataclasses import dataclass

from window import WindowOrchestrator, WindowRecord


@dataclass(frozen=True)
class ReplayInput:
    """
    Input for replay harness per SPEC.md §6.1
    
    Contains all information needed to reproduce policy decisions.
    """
    B: int  # declared budget (microseconds)
    W: int  # enforcement window size (symbolic constant, microseconds)
    observations: List[int]  # sequence of U_w observations
    
    def __post_init__(self):
        assert self.B > 0, f"Invalid budget: B={self.B}"
        assert self.W > 0, f"Invalid window size: W={self.W}"
        assert len(self.observations) > 0, "Empty observation sequence"
        for i, U_w in enumerate(self.observations):
            assert U_w >= 0, f"Invalid observation at index {i}: U_w={U_w}"


@dataclass(frozen=True)
class ReplayOutput:
    """
    Output from replay harness.
    
    Contains complete history of policy decisions for verification.
    """
    history: List[WindowRecord]
    
    def __post_init__(self):
        assert len(self.history) > 0, "Empty history"


def replay(replay_input: ReplayInput) -> ReplayOutput:
    """
    Replay policy decisions from recorded observations.
    
    This function proves determinism per INVARIANTS.md G1:
    Given identical inputs, produces identical outputs.
    
    Args:
        replay_input: Recorded observations and configuration
    
    Returns:
        Complete history of policy decisions
    
    Invariants:
        - G1: Determinism (identical inputs => identical outputs)
        - G2: Replayability (reproducible offline)
    
    Forbidden:
        - No wall-clock time
        - No async events
        - No scheduler callbacks
        - No signal timing
    """
    # Create orchestrator with declared budget and window size
    orchestrator = WindowOrchestrator(B=replay_input.B, W=replay_input.W)
    
    # Replay each observation
    for U_w in replay_input.observations:
        orchestrator.advance_window(U_w)
    
    # Return complete history
    history = orchestrator.get_history()
    return ReplayOutput(history=history)


def verify_replay_determinism(
    replay_input: ReplayInput,
    num_runs: int = 2
) -> bool:
    """
    Verify that replay is deterministic.
    
    Runs replay multiple times and verifies identical outputs.
    
    Args:
        replay_input: Input to replay
        num_runs: Number of replay runs to compare (default: 2)
    
    Returns:
        True if all runs produce identical results, False otherwise
    
    Spec Reference:
        - TESTING.md §2.2 (Replay Tests)
        - INVARIANTS.md G1 (Determinism Invariant)
    """
    assert num_runs >= 2, f"Need at least 2 runs to verify determinism, got {num_runs}"
    
    # Run replay multiple times
    outputs = [replay(replay_input) for _ in range(num_runs)]
    
    # Verify all outputs are identical
    first_output = outputs[0]
    for i, output in enumerate(outputs[1:], start=1):
        if len(first_output.history) != len(output.history):
            return False
        
        for window_idx, (record1, record2) in enumerate(zip(first_output.history, output.history)):
            # Compare all fields
            if (record1.window_index != record2.window_index or
                record1.state != record2.state or
                record1.U_w != record2.U_w or
                record1.T_w != record2.T_w):
                return False
    
    return True
