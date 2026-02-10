"""
Wall-Clock Driven Window Orchestrator (v1)

This module implements the real-time loop that drives the policy.

Spec References:
- SPEC.md §3 (Time Model)
- ARCHITECTURE.md §3.4 (Orchestrator)
"""

import time
import logging
from typing import Optional, Tuple

from .cpu import write_cpu_quota
from .observation import WindowedObserver
from window import WindowOrchestrator
from policy import PolicyStateData, DecisionRecord
from json_logger import setup_json_logger, log_decision

# Setup logging
logger = logging.getLogger(__name__)

class CgroupOrchestrator:
    """
    Wall-clock driven orchestrator for cgroup v1 implementation.
    
    Responsibility:
    - Triggers window advancement based on wall-clock time.
    - Measures drift but does NOT correct it dynamically (no adaptive sleep).
    - Prevents catch-up loops by strictly bounding lag.
    
    Invariant T1: W is constant.
    Invariant T2: Single evaluation per window.
    Invariant T3: Bounded lag (sleep drift is observed, not dynamically corrected).
    """
    
    def __init__(self, cgroup_path: str, B: int, W_us: int):
        """
        Initialize orchestrator.
        
        Args:
            cgroup_path: Absolute path to cgroup.
            B: Budget in microseconds.
            W_us: Window size in microseconds.
        """
        self._cgroup_path = cgroup_path
        self._B = B
        self._W_us = W_us
        self._W_sec = W_us / 1_000_000.0
        
        # Components
        self._observer = WindowedObserver(cgroup_path)
        self._policy_orch = WindowOrchestrator(B, W_us)
        
        # v3: Structured Logging
        self._trace_logger = setup_json_logger(name="rgov.trace.v1", log_file="rgov_v1_trace.jsonl")
        
        # v3: State Query
        self._last_record = None
        
    def run_loop(self, max_windows: Optional[int] = None) -> None:
        """
        Run the orchestration loop.
        
        Args:
            max_windows: Optional limit on number of windows to process (for testing).
        """
        # Init observation baseline
        self._observer.init_observation()
        
        # Align next wake to valid monotonic future
        next_wake = time.time() + self._W_sec
        
        windows_processed = 0
        
        while max_windows is None or windows_processed < max_windows:
            # 1. Sleep until next window boundary
            now = time.time()
            sleep_duration = next_wake - now
            
            if sleep_duration > 0:
                time.sleep(sleep_duration)
            
            # 2. Wake up and Measure
            # Note: We measure strictly AFTER sleep
            wake_time = time.time()
            drift = wake_time - next_wake
            
            # bounded lag check (logging)
            if drift > self._W_sec:
                logger.warning(f"Major drift detected: {drift*1000:.2f}ms (> W)")
            
            U_w = self._observer.measure_window()
            
            # 3. Policy Evaluation
            next_state, decision, record = self._policy_orch.advance_window(U_w)
            
            # v3: Structured Logging
            # WindowOrchestrator increments index AFTER this call (internally).
            # So get_current_window_index() returns NEXT index.
            # We want the index corresponding to THIS decision.
            # wait, advance_window implements: `self._window_index += 1`.
            # So current index is indeed index + 1 relative to the just-processed window.
            # Correct logic: index = self._policy_orch.get_current_window_index() - 1
            current_window_index = self._policy_orch.get_current_window_index() - 1
            log_decision(self._trace_logger, record, override_window_index=current_window_index)
            
            # v3: State Query
            self._last_record = record
            
            # 4. Enforce
            write_cpu_quota(self._cgroup_path, decision.T_w, self._W_us)
            
            windows_processed += 1
            
            # 5. Schedule Next
            next_wake += self._W_sec
            
            # 6. Anti-Spin / Bounded Lag Logic
            if next_wake < time.time():
                lag = time.time() - next_wake
                missed = int(lag / self._W_sec) + 1
                if missed > 0:
                    logger.warning(f"Lag implies {missed} skipped windows. Realigning.")
                    next_wake += missed * self._W_sec
                    
    def get_status(self) -> Tuple[PolicyStateData, Optional[DecisionRecord]]:
        """
        Query current status (state and last decision).
        Note: WindowOrchestrator does not expose state directly via get_state().
        """
        # We need to access PolicyStateData from WindowOrchestrator
        # WindowOrchestrator has `_policy_state` (private).
        # We should expose it or use `get_history()[-1]`?
        # `get_history` returns WindowRecord (v0), not PolicyStateData.
        # But `_last_record` has `state_after`.
        # If no record yet, return initial state?
        if self._last_record:
            return self._last_record.state_after, self._last_record
        else:
             # Initial state
             from policy import initial_state
             return initial_state(), None
