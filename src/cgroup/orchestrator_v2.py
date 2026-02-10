"""
Multi-Workload Orchestrator (v2)

This module implements the v2 orchestrator that manages multiple independent workloads.
It enforces strict isolation and capacity limits.

Spec References:
- v2.md §3 (Iteration, Capacity)
- ARCHITECTURE.md §3 (Orchestrator)
"""

import time
import logging
from typing import Dict, List, Optional

from .cpu import write_cpu_quota
from .observation import WindowedObserver
from window import WindowOrchestrator, WindowRecord
from workload import WorkloadID
from policy_storage import PolicyStore
from policy import PolicyStateData, evaluate_policy

# Setup logging
logger = logging.getLogger(__name__)

class MultiWorkloadOrchestrator:
    """
    v2 Orchestrator for multiple independent workloads.
    
    Responsibilities:
    - Register workloads with static capacity check.
    - Run global loop driving all workloads.
    - Ensure isolation (no cross-talk).
    - Ensure order-independence.
    
    Invariant C1: Total budget <= Capacity.
    Invariant T1: Global window W is constant.
    Invariant I3: No cross-workload logic.
    """
    
    def __init__(self, capacity_us: int, W_us: int):
        """
        Initialize orchestrator.
        
        Args:
            capacity_us: Total physical capacity in microseconds (Fixed Constant).
            W_us: Global window size in microseconds.
        """
        self._capacity_us = capacity_us
        self._W_us = W_us
        self._W_sec = W_us / 1_000_000.0
        
        # Registry
        self._workloads: List[WorkloadID] = []
        self._cgroup_paths: Dict[WorkloadID, str] = {}
        self._budgets: Dict[WorkloadID, int] = {}
        
        # Components per workload
        self._observers: Dict[WorkloadID, WindowedObserver] = {}
        self._policy_store = PolicyStore()
        
    def register_workload(self, workload_id: WorkloadID, cgroup_path: str, budget_us: int) -> None:
        """
        Register a new workload.
        
        Validation: Sum(Budgets) + new_budget <= Capacity.
        
        Args:
            workload_id: Unique identifier.
            cgroup_path: Path to cgroup.
            budget_us: Budget in microseconds.
            
        Raises:
            ValueError: If capacity exceeded or ID duplicate.
        """
        if workload_id in self._workloads:
            raise ValueError(f"Duplicate workload ID: {workload_id}")
            
        current_total = sum(self._budgets.values())
        if current_total + budget_us > self._capacity_us:
             raise ValueError(f"Capacity exceeded: {current_total + budget_us} > {self._capacity_us}")
             
        # Registration
        self._workloads.append(workload_id)
        # Sort workloads to ensure deterministic iteration order,
        # ensuring order-independence verification is consistent.
        # Note: The Requirement is that order MUST NOT matter.
        # But for determinism in logging/debugging, sorting is fine.
        # We will test that order doesn't matter by shuffling in tests.
        self._workloads.sort(key=lambda x: str(x))
        
        self._cgroup_paths[workload_id] = cgroup_path
        self._budgets[workload_id] = budget_us
        self._observers[workload_id] = WindowedObserver(cgroup_path)
        
        # Start strictly fresh? PolicyStore handles init on first access.
        
        logger.info(f"Registered workload {workload_id} with budget {budget_us}")

    def run_loop(self, max_windows: Optional[int] = None) -> None:
        """
        Run the orchestration loop.
        """
        # Init all observers
        for wid in self._workloads:
             self._observers[wid].init_observation()
             
        next_wake = time.time() + self._W_sec
        windows_processed = 0
        
        while max_windows is None or windows_processed < max_windows:
            # 1. Sleep
            now = time.time()
            sleep_duration = next_wake - now
            if sleep_duration > 0:
                time.sleep(sleep_duration)
                
            # 2. Iteration (Order Independent)
            # We iterate over the list.
            for wid in self._workloads:
                self._process_workload(wid)
                
            windows_processed += 1
            next_wake += self._W_sec
            
            # Anti-spin logic (Same as v1)
            if next_wake < time.time():
                 lag = time.time() - next_wake
                 missed = int(lag / self._W_sec) + 1
                 if missed > 0:
                      logger.warning(f"Lag implies {missed} skipped windows.")
                      next_wake += missed * self._W_sec
                      
    def _process_workload(self, wid: WorkloadID) -> None:
        """Process a single workload for one window."""
        cgroup = self._cgroup_paths[wid]
        observer = self._observers[wid]
        budget = self._budgets[wid]
        state = self._policy_store.get_state(wid)
        
        # A. Measure
        U_w = observer.measure_window()
        
        # B. Policy
        next_state, decision = evaluate_policy(state, U_w, budget, self._W_us)
        self._policy_store.update_state(wid, next_state)
        
        # C. Enforce
        # Strict numeric enforcement
        write_cpu_quota(cgroup, decision.T_w, self._W_us)
