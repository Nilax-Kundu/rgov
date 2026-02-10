"""
Core Policy Logic.

This module defines the pure function that maps (State, Observation, Budget) -> (Enforcement).
It implements the state machine and transition rules.

Spec Reference: v0.md (Policy)
v3.md (Observability - DecisionRecord)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

class PolicyState(str, Enum):
    NORMAL = "NORMAL"
    THROTTLED = "THROTTLED"

@dataclass(frozen=True)
class PolicyStateData:
    """
    Pure data container for policy state.
    
    Attributes:
        mode: Current mode (NORMAL, THROTTLED)
        debt_us: Accumulated debt in microseconds
        last_decision_time: Timestamp of last decision (for debug/logging only, not logic)
    """
    mode: PolicyState 
    debt_us: int
    last_decision_time: float
    
    # Backward compatibility properties if needed
    @property
    def state(self) -> PolicyState:
        return self.mode

    @property
    def debt(self) -> int:
        return self.debt_us

@dataclass(frozen=True)
class EnforcementDecision:
    """
    Output of the policy function.
    
    Attributes:
        T_w: Enforced quota for next window (microseconds).
    """
    T_w: int

@dataclass(frozen=True)
class DecisionRecord:
    """
    Structural record of a policy decision.
    Captures inputs, outputs, and the rule that fired.
    
    Spec Reference: v3.md §1
    Invariant: Fields must be directly emitted by policy logic.
    """
    # Context
    window_index: Optional[int] 
    
    # Inputs
    state_before: PolicyStateData
    debt_before: int
    usage_us: int
    budget_us: int
    
    # Outputs
    enforced_quota: int
    state_after: PolicyStateData
    debt_after: int
    
    # Reasoning (Mechanical)
    policy_rule_id: str
    violated_invariant: Optional[str] = None


def initial_state() -> PolicyStateData:
    """Create initial policy state (Normal, 0 debt)."""
    return PolicyStateData(mode=PolicyState.NORMAL, debt_us=0, last_decision_time=0.0)


def evaluate_policy(
    state: PolicyStateData, 
    U_w: int, 
    B: int, 
    W: int
) -> Tuple[PolicyStateData, EnforcementDecision, DecisionRecord]:
    """
    Pure policy function.
    
    Args:
        state: Current state.
        U_w: Measured usage in previous window.
        B: Target budget.
        W: Window size (physical).
        
    Returns:
        (NewState, EnforcementDecision, DecisionRecord)
    """
    # Validate inputs (Assertion P1/P2 guards)
    assert U_w >= 0, f"Invalid input: U_w={U_w}"
    assert B > 0, f"Invalid input: B={B}"
    
    state_mode = state.mode
    
    # 1. Calculate inputs
    excess = U_w - B
    
    # 2. Transition Logic
    # Rule: Normal Mode
    if state_mode == PolicyState.NORMAL:
        if excess <= 0:
            # Rule N1: Under-budget. No change.
            new_debt = 0 
            new_mode = PolicyState.NORMAL
            enforced = B
            rule_id = "RULE_N1_UNDER_BUDGET"
            invariant = None
        else:
            # Rule N2: Over-budget. 
            new_debt = excess
            new_mode = PolicyState.THROTTLED
            enforced = 0
            rule_id = "RULE_N2_OVER_BUDGET"
            invariant = "INV_USAGE_EXCEEDS_BUDGET"
            
    # Rule: Throttled Mode
    else: # THROTTLED
        repayment = B - U_w
        new_debt = state.debt_us - repayment
        
        if new_debt <= 0:
            # Rule T1: Debt Recovered
            new_debt = 0
            new_mode = PolicyState.NORMAL
            enforced = B
            rule_id = "RULE_T1_DEBT_RECOVERED"
            invariant = None
        else:
            # Rule T2: Still in Debt
            new_mode = PolicyState.THROTTLED
            enforced = 0
            rule_id = "RULE_T2_STILL_IN_DEBT"
            invariant = "INV_DEBT_REMAINING"
            
    # 3. Construct Output
    next_state = PolicyStateData(
        mode=new_mode,
        debt_us=new_debt,
        last_decision_time=0.0 
    )
    decision = EnforcementDecision(T_w=enforced)
    
    record = DecisionRecord(
        window_index=None, 
        state_before=state,
        debt_before=state.debt_us,
        usage_us=U_w,
        budget_us=B,
        enforced_quota=enforced,
        state_after=next_state,
        debt_after=new_debt,
        policy_rule_id=rule_id,
        violated_invariant=invariant
    )
    
    return next_state, decision, record
