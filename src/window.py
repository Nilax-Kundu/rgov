"""
Enforcement Window Logic (v0 - Pure)

This module implements pure window advancement logic for rgov v0.

This is PURE LOGIC ONLY - no actual timing, no clocks, no system calls.
Window size W is a symbolic constant carried through interfaces.

Spec References:
- SPEC.md §3 (Time Model)
- INVARIANTS.md §3 (Time Invariants)
"""

from dataclasses import dataclass
from typing import List, Tuple

from policy import PolicyStateData, EnforcementDecision, evaluate_policy, initial_state


@dataclass(frozen=True)
class WindowRecord:
    """
    Record of policy state and decision for a single window.
    
    Used for logging and replay verification per SPEC.md §6.2
    """
    window_index: int
    state: PolicyStateData
    U_w: int  # observed usage for this window
    T_w: int  # enforced quota for next window
    
    def __post_init__(self):
        assert self.window_index >= 0, f"Invalid window_index: {self.window_index}"
        assert self.U_w >= 0, f"Invalid U_w: {self.U_w}"
        assert self.T_w >= 0, f"Invalid T_w: {self.T_w}"


class WindowOrchestrator:
    """
    Pure window advancement orchestrator.
    
    This orchestrator:
    - Advances window indices
    - Sequences policy evaluation
    - Maintains no policy-relevant state (only window counter)
    
    Invariants:
    - T1: Window size W is constant
    - T2: Policy evaluated exactly once per window
    - G4: Decisions only at window boundaries
    
    Forbidden:
    - No wall-clock time
    - No actual timers
    - No mid-window reactions
    - No decision making (only sequencing)
    """
    
    def __init__(self, B: int, W: int):
        """
        Initialize orchestrator.
        
        Args:
            B: Declared budget (microseconds per window)
            W: Enforcement window size (symbolic constant, microseconds)
        """
        assert B > 0, f"Invalid budget: B={B}"
        assert W > 0, f"Invalid window size: W={W}"
        
        self._B = B
        self._W = W  # T1: Fixed window size (constant)
        self._window_index = 0
        self._policy_state = initial_state()
        self._history: List[WindowRecord] = []
    
    def advance_window(self, U_w: int) -> Tuple[PolicyStateData, EnforcementDecision]:
        """
        Advance one enforcement window.
        
        This is the only temporal primitive per ARCHITECTURE.md §6.
        
        Args:
            U_w: Observed CPU usage for this window (microseconds)
        
        Returns:
            Tuple of (next_policy_state, enforcement_decision)
        
        Invariants:
            - T2: Policy evaluated exactly once per window
            - G4: Window exclusivity (decisions only at boundaries)
        """
        assert U_w >= 0, f"Invalid U_w: {U_w}"
        
        # T2: Evaluate policy exactly once per window
        next_state, decision = evaluate_policy(
            current_state=self._policy_state,
            U_w=U_w,
            B=self._B,
            W=self._W
        )
        
        # Record this window (for logging/replay per SPEC.md §6.2)
        record = WindowRecord(
            window_index=self._window_index,
            state=self._policy_state,  # state at START of window
            U_w=U_w,
            T_w=decision.T_w
        )
        self._history.append(record)
        
        # Update state for next window
        self._policy_state = next_state
        self._window_index += 1
        
        return next_state, decision
    
    def get_history(self) -> List[WindowRecord]:
        """
        Get complete window history.
        
        Used for replay verification and logging per SPEC.md §6.2
        """
        return list(self._history)  # Return copy to prevent mutation
    
    def get_current_window_index(self) -> int:
        """Get current window index (for debugging/logging only)"""
        return self._window_index
    
    def get_current_state(self) -> PolicyStateData:
        """Get current policy state (for debugging/logging only)"""
        return self._policy_state
