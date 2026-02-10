"""
Policy State Storage (v2)

This module implements the isolated storage for policy state per workload.
Spec Reference: v2.md §3 (State Isolation)
"""

from typing import Dict, Optional
from workload import WorkloadID
from policy import PolicyStateData, initial_state

class PolicyStore:
    """
    Container for per-workload policy state.
    
    Invariant I2: State is strictly per-workload.
    Invariant I3: No shared state between entries.
    """
    
    def __init__(self):
        self._states: Dict[WorkloadID, PolicyStateData] = {}
        
    def get_state(self, workload_id: WorkloadID) -> PolicyStateData:
        """
        Retrieve state for a workload. 
        If not present, initializes new state (Normal, 0 debt).
        """
        if workload_id not in self._states:
            self._states[workload_id] = initial_state()
        return self._states[workload_id]
        
    def update_state(self, workload_id: WorkloadID, state: PolicyStateData) -> None:
        """
        Update state for a workload.
        """
        self._states[workload_id] = state
        
    def reset(self, workload_id: WorkloadID) -> None:
        """Reset state for a workload (e.g. on deregistration or explicit reset)."""
        self._states[workload_id] = initial_state()
