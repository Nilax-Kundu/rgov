"""
Multi-Workload Orchestrator (v2)

This module implements the orchestrator for multiple independent workloads.
It follows the v2 checklist requirements:
- State isolation (WorkloadID -> PolicyState)
- Order independence
- Capacity checking

Spec Reference: v2.md, ARCHITECTURE.md
v3.md (Observability)
"""

import time
import logging
from typing import List, Optional, Tuple

from workload import WorkloadID
from policy_storage import PolicyStore
from policy import evaluate_policy, initial_state, PolicyStateData, DecisionRecord
from .cpu import write_cpu_quota
from .observation import WindowedObserver
from json_logger import setup_json_logger, log_decision

logger = logging.getLogger(__name__)

class MultiWorkloadOrchestrator:
    """
    Orchestrator for multiple independent workloads (v2).
    
    Invariants:
    - I1 (Distinct Entity): Workloads identified by strict WorkloadID.
    - I2 (State Isolation): States stored in isolated PolicyStore.
    - C1 (Capacity Bound): Total budget <= Capacity.
    - T1 (Global Window): Single loop drives all workloads.
    """
    
    def __init__(self, capacity_us: int, W_us: int):
        """
        Initialize orchestrator.
        
        Args:
            capacity_us: Total physical capacity (microseconds).
            W_us: Window size (microseconds).
        """
        assert capacity_us > 0, f"Invalid capacity: {capacity_us}"
        assert W_us > 0, f"Invalid window size: {W_us}"
        
        self._capacity_us = capacity_us
        self._W_us = W_us
        self._W_sec = W_us / 1_000_000.0
        
        self._policy_store = PolicyStore()
        
        # Registration state
        self._workloads: List[WorkloadID] = []
        self._budgets: dict[WorkloadID, int] = {}
        self._cgroups: dict[WorkloadID, str] = {}
        self._observers: dict[WorkloadID, WindowedObserver] = {}
        
        # v3: Structured Logging
        self._trace_logger = setup_json_logger(name="rgov.trace.v2", log_file="rgov_v2_trace.jsonl")
        
        # v3: Global Window Index
        self._global_window_index = 0
        
    def register_workload(self, wid: WorkloadID, cgroup_path: str, budget_us: int) -> None:
        """
        Register a new workload.
        
        Precondition:
        - Sum of existing budgets + new budget <= Capacity.
        """
        assert budget_us > 0, f"Invalid budget: {budget_us}"
        
        # Capacity Check
        current_total = sum(self._budgets.values())
        if current_total + budget_us > self._capacity_us:
            raise ValueError(f"Capacity exceeded: {current_total} + {budget_us} > {self._capacity_us}")
            
        # Register
        self._workloads.append(wid)
        self._budgets[wid] = budget_us
        self._cgroups[wid] = cgroup_path
        self._observers[wid] = WindowedObserver(cgroup_path)
        
        # Initialize state isolated
        self._policy_store.update_state(wid, initial_state())
        
        # Sort workloads strictly by ID for deterministic iteration order (Invariant: Order Independence)
        # Note: WorkloadID is string-based NewType, so sortable.
        self._workloads.sort()
        
    def run_loop(self, max_windows: Optional[int] = None) -> None:
        """
        Run the multi-workload orchestration loop.
        """
        # Init observations
        for wid in self._workloads:
            self._observers[wid].init_observation()
            
        next_wake = time.time() + self._W_sec
        
        while max_windows is None or self._global_window_index < max_windows:
            # 1. Sleep
            now = time.time()
            sleep_duration = next_wake - now
            if sleep_duration > 0:
                time.sleep(sleep_duration)
                
            # 2. Wake & Measure (All workloads)
            # Iteration Invariant: Order doesn't matter for policy, solely for execution sequence.
            # We iterate in sorted order.
            
            # Drift check
            wake_time = time.time()
            if wake_time - next_wake > self._W_sec:
                logger.warning(f"Major drift > W")
                
            # Process each workload independently
            for wid in self._workloads:
                # A. Measure
                observer = self._observers[wid]
                state = self._policy_store.get_state(wid)
                budget = self._budgets[wid]
                
                U_w = observer.measure_window()
                
                # B. Policy
                next_state, decision, record = evaluate_policy(
                    state=state, 
                    U_w=U_w, 
                    B=budget, 
                    W=self._W_us
                )
                self._policy_store.set_decision(wid, next_state, record)
                
                # v3: Logging
                log_decision(self._trace_logger, record, override_window_index=self._global_window_index)
                
                # C. Enforce
                write_cpu_quota(self._cgroups[wid], decision.T_w, self._W_us)
                
            # Increment global window
            self._global_window_index += 1
            
            # Schedule Next
            next_wake += self._W_sec
            
            # Anti-spin
            if next_wake < time.time():
                lag = time.time() - next_wake
                missed = int(lag / self._W_sec) + 1
                if missed > 0:
                    logger.warning(f"Lag: skipped {missed} windows")
                    next_wake += missed * self._W_sec
                    
    def get_status(self, workload_id: WorkloadID) -> Tuple[PolicyStateData, Optional[DecisionRecord]]:
        """
        Query current status (state and last decision) for a workload.
        """
        state = self._policy_store.get_state(workload_id)
        record = self._policy_store.get_last_record(workload_id)
        return state, record
