"""
Synthetic U_w Generators (v0)

This module provides generators for adversarial test sequences.

These generators create pathological observation sequences to test
policy correctness under extreme conditions per TESTING.md §5.

Spec References:
- TESTING.md §5 (Adversarial Testing Requirements)
- v0.md §4 (Required Evidence)
"""

from typing import List, Iterator


def generate_continuous_overshoot(B: int, overshoot_factor: float, num_windows: int) -> List[int]:
    """
    Generate continuous overshoot sequence.
    
    Every window uses overshoot_factor * B.
    Tests debt accumulation without bound.
    
    Args:
        B: Declared budget (microseconds)
        overshoot_factor: Multiplier for overshoot (e.g., 2.0 = 200% of budget)
        num_windows: Number of windows to generate
    
    Returns:
        List of U_w observations
    
    Spec Reference:
        - TESTING.md §5 (Continuous overshoot)
    """
    assert B > 0, f"Invalid budget: B={B}"
    assert overshoot_factor > 1.0, f"overshoot_factor must be > 1.0, got {overshoot_factor}"
    assert num_windows > 0, f"num_windows must be > 0, got {num_windows}"
    
    U_w = int(B * overshoot_factor)
    return [U_w] * num_windows


def generate_alternating_overshoot_undershoot(
    B: int,
    overshoot_factor: float,
    undershoot_factor: float,
    num_cycles: int
) -> List[int]:
    """
    Generate alternating overshoot/undershoot sequence.
    
    Alternates between overshoot and undershoot to test debt accumulation
    and paydown logic.
    
    Args:
        B: Declared budget (microseconds)
        overshoot_factor: Multiplier for overshoot windows (e.g., 2.0)
        undershoot_factor: Multiplier for undershoot windows (e.g., 0.5)
        num_cycles: Number of overshoot/undershoot cycles
    
    Returns:
        List of U_w observations
    
    Spec Reference:
        - TESTING.md §5 (Alternating overshoot/undershoot)
    """
    assert B > 0, f"Invalid budget: B={B}"
    assert overshoot_factor > 1.0, f"overshoot_factor must be > 1.0, got {overshoot_factor}"
    assert 0.0 < undershoot_factor < 1.0, f"undershoot_factor must be in (0, 1), got {undershoot_factor}"
    assert num_cycles > 0, f"num_cycles must be > 0, got {num_cycles}"
    
    overshoot_U_w = int(B * overshoot_factor)
    undershoot_U_w = int(B * undershoot_factor)
    
    result = []
    for _ in range(num_cycles):
        result.append(overshoot_U_w)
        result.append(undershoot_U_w)
    
    return result


def generate_zero_usage(num_windows: int) -> List[int]:
    """
    Generate zero-usage sequence.
    
    All windows have U_w = 0.
    Tests debt paydown and state transitions to NORMAL.
    
    Args:
        num_windows: Number of windows to generate
    
    Returns:
        List of U_w observations (all zeros)
    
    Spec Reference:
        - TESTING.md §5 (Zero-usage windows)
    """
    assert num_windows > 0, f"num_windows must be > 0, got {num_windows}"
    return [0] * num_windows


def generate_boundary_conditions(B: int, num_windows: int) -> List[int]:
    """
    Generate boundary condition sequence.
    
    All windows have U_w exactly equal to B.
    Tests exact budget matching (no overshoot, no undershoot).
    
    Args:
        B: Declared budget (microseconds)
        num_windows: Number of windows to generate
    
    Returns:
        List of U_w observations (all equal to B)
    
    Spec Reference:
        - TESTING.md §5 (Budget at capacity boundary)
    """
    assert B > 0, f"Invalid budget: B={B}"
    assert num_windows > 0, f"num_windows must be > 0, got {num_windows}"
    return [B] * num_windows


def generate_long_debt_accumulation(
    B: int,
    overshoot_factor: float,
    accumulation_windows: int,
    paydown_factor: float,
    paydown_windows: int
) -> List[int]:
    """
    Generate long debt accumulation followed by paydown.
    
    First phase: accumulate debt over many windows
    Second phase: pay down debt over many windows
    
    Args:
        B: Declared budget (microseconds)
        overshoot_factor: Multiplier for accumulation phase (e.g., 1.5)
        accumulation_windows: Number of windows to accumulate debt
        paydown_factor: Multiplier for paydown phase (e.g., 0.5)
        paydown_windows: Number of windows to pay down debt
    
    Returns:
        List of U_w observations
    
    Spec Reference:
        - TESTING.md §5 (Long debt accumulation)
    """
    assert B > 0, f"Invalid budget: B={B}"
    assert overshoot_factor > 1.0, f"overshoot_factor must be > 1.0, got {overshoot_factor}"
    assert accumulation_windows > 0, f"accumulation_windows must be > 0, got {accumulation_windows}"
    assert 0.0 < paydown_factor < 1.0, f"paydown_factor must be in (0, 1), got {paydown_factor}"
    assert paydown_windows > 0, f"paydown_windows must be > 0, got {paydown_windows}"
    
    accumulation_U_w = int(B * overshoot_factor)
    paydown_U_w = int(B * paydown_factor)
    
    result = []
    result.extend([accumulation_U_w] * accumulation_windows)
    result.extend([paydown_U_w] * paydown_windows)
    
    return result


def generate_oscillation(
    B: int,
    high_factor: float,
    low_factor: float,
    num_oscillations: int
) -> List[int]:
    """
    Generate oscillating sequence with rapid changes.
    
    Rapidly alternates between high and low usage to stress-test
    state transitions.
    
    Args:
        B: Declared budget (microseconds)
        high_factor: Multiplier for high windows (e.g., 3.0)
        low_factor: Multiplier for low windows (e.g., 0.1)
        num_oscillations: Number of high/low pairs
    
    Returns:
        List of U_w observations
    
    Spec Reference:
        - v0.md §4 (oscillation)
    """
    assert B > 0, f"Invalid budget: B={B}"
    assert high_factor > 1.0, f"high_factor must be > 1.0, got {high_factor}"
    assert 0.0 <= low_factor < 1.0, f"low_factor must be in [0, 1), got {low_factor}"
    assert num_oscillations > 0, f"num_oscillations must be > 0, got {num_oscillations}"
    
    high_U_w = int(B * high_factor)
    low_U_w = int(B * low_factor)
    
    result = []
    for _ in range(num_oscillations):
        result.append(high_U_w)
        result.append(low_U_w)
    
    return result
