"""
CPU Policy State Machine (v0)

This module implements the deterministic CPU policy state machine for rgov v0.

Guarantees:
- Deterministic state transitions
- Invariant preservation (P1-P6)
- No system calls, no clocks, no kernel interaction
- Pure computation only

Spec References:
- SPEC.md §4.3 (CPU Policy State Machine)
- INVARIANTS.md §4 (Policy State Invariants)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class PolicyState(Enum):
    """Policy state enum per SPEC.md §4.3"""
    NORMAL = "Normal"
    THROTTLED = "Throttled"


@dataclass(frozen=True)
class PolicyStateData:
    """
    Policy state variables per SPEC.md §4.3
    
    Invariants:
    - P1: debt >= 0 (non-negative debt)
    - P5: state == NORMAL => debt == 0 (normal-state cleanliness)
    """
    state: PolicyState
    debt: int  # microseconds, must be >= 0
    
    def __post_init__(self):
        """Assert invariants on construction"""
        # P1: Non-negative debt
        assert self.debt >= 0, f"Invariant P1 violated: debt={self.debt} < 0"
        
        # P5: Normal-state cleanliness
        if self.state == PolicyState.NORMAL:
            assert self.debt == 0, f"Invariant P5 violated: state=NORMAL but debt={self.debt} != 0"


@dataclass(frozen=True)
class EnforcementDecision:
    """
    Enforcement decision for a single window
    
    Invariants:
    - P2: 0 <= T_w <= B (budget bound)
    """
    T_w: int  # enforced quota in microseconds
    
    def __post_init__(self):
        """Assert invariants on construction"""
        # P2 partial check: T_w >= 0 (budget bound upper check requires B, done in evaluate_policy)
        assert self.T_w >= 0, f"Invariant P2 violated: T_w={self.T_w} < 0"


def evaluate_policy(
    current_state: PolicyStateData,
    U_w: int,
    B: int,
    W: int  # symbolic constant, carried through but not used numerically
) -> Tuple[PolicyStateData, EnforcementDecision]:
    """
    Evaluate policy for one enforcement window.
    
    This is the core deterministic state transition function.
    
    Args:
        current_state: Current policy state
        U_w: Observed CPU usage in this window (microseconds)
        B: Declared budget (microseconds per window)
        W: Enforcement window size (symbolic constant, microseconds)
    
    Returns:
        Tuple of (next_state, enforcement_decision)
    
    Invariants preserved:
        - P1: debt >= 0
        - P2: 0 <= T_w <= B
        - P3: No throttling without excess (throttle only when debt > 0)
        - P4: Debt decreases only when U_w < B
        - P5: state == NORMAL => debt == 0
        - P6: Deterministic transitions (identical inputs => identical outputs)
    
    Spec References:
        - SPEC.md §4.3
        - INVARIANTS.md §4
    
    Forbidden:
        - No system calls
        - No clocks or timers
        - No nondeterministic branching
        - No heuristics
    """
    # Validate inputs
    assert U_w >= 0, f"Invalid input: U_w={U_w} < 0"
    assert B > 0, f"Invalid input: B={B} <= 0"
    assert W > 0, f"Invalid input: W={W} <= 0"
    
    # Calculate excess or deficit for this window
    excess = U_w - B
    
    # Update debt based on current window
    if excess > 0:
        # Overshoot: accumulate debt
        new_debt = current_state.debt + excess
    elif excess < 0:
        # Undershoot: pay down debt (P4: debt decreases only when U_w < B)
        deficit = -excess
        new_debt = max(0, current_state.debt - deficit)
    else:
        # Exactly at budget: debt unchanged
        new_debt = current_state.debt
    
    # Determine next state and enforcement decision
    # P3 refinement: Throttle is a function of debt, not directly of U_w
    # Throttling occurs only when debt > 0
    if new_debt > 0:
        # We have outstanding debt: throttle
        next_state_enum = PolicyState.THROTTLED
        # Throttle to zero quota
        T_w = 0
    else:
        # No debt: normal operation
        next_state_enum = PolicyState.NORMAL
        # Allow full budget
        T_w = B
    
    # P2: Budget bound check
    assert 0 <= T_w <= B, f"Invariant P2 violated: T_w={T_w} not in [0, {B}]"
    
    # Construct next state (invariants checked in __post_init__)
    next_state = PolicyStateData(state=next_state_enum, debt=new_debt)
    decision = EnforcementDecision(T_w=T_w)
    
    return next_state, decision


def initial_state() -> PolicyStateData:
    """
    Create initial policy state.
    
    Initial state is always NORMAL with zero debt per P5.
    """
    return PolicyStateData(state=PolicyState.NORMAL, debt=0)
