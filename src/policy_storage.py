"""
Policy State Storage (v2)

This module implements the isolated storage for policy state per workload.
Spec Reference: v2.md §3 (State Isolation)
"""

from typing import Dict, Optional, Tuple
from workload import WorkloadID
from policy import PolicyStateData, DecisionRecord, initial_state

class PolicyStore:
    """
    Container for per-workload policy state.
    
    Invariant I2: State is strictly per-workload.
    Invariant I3: No shared state between entries.
    """
    
    def __init__(self):
        self._states: Dict[WorkloadID, PolicyStateData] = {}
        self._last_records: Dict[WorkloadID, Optional[DecisionRecord]] = {}
        
    def get_state(self, workload_id: WorkloadID) -> PolicyStateData:
        """
        Retrieve state for a workload. 
        If not present, initializes new state (Normal, 0 debt).
        """
        if workload_id not in self._states:
            self._states[workload_id] = initial_state()
            self._last_records[workload_id] = None
        return self._states[workload_id]
        
    def get_last_record(self, workload_id: WorkloadID) -> Optional[DecisionRecord]:
        """
        Retrieve the last decision record for a workload.
        """
        if workload_id not in self._last_records:
            return None
        return self._last_records[workload_id]

    def update_state(self, workload_id: WorkloadID, state: PolicyStateData) -> None:
        """
        Update state for a workload (without record).
        """
        self._states[workload_id] = state

    def set_decision(self, workload_id: WorkloadID, state: PolicyStateData, record: DecisionRecord) -> None:
        """
        Update state and record for a workload after a decision.
        """
        self._states[workload_id] = state
        self._last_records[workload_id] = record
        
    def reset(self, workload_id: WorkloadID) -> None:
        """Reset state for a workload (e.g. on deregistration or explicit reset)."""
        self._states[workload_id] = initial_state()
        self._last_records[workload_id] = None
