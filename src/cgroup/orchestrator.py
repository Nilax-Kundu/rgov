"""
Wall-Clock Driven Window Orchestrator (v1)

This module implements the real-time loop that drives the policy.

Spec References:
- SPEC.md §3 (Time Model)
- ARCHITECTURE.md §3.4 (Orchestrator)
"""

import time
import logging
from typing import Optional

from .cpu import write_cpu_quota
from .observation import WindowedObserver
from window import WindowOrchestrator, WindowRecord

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
            next_state, decision = self._policy_orch.advance_window(U_w)
            
            # 4. Enforce
            # Period is usually W, but technically defined by policy?
            # In v1 checklist: "Writes cpu.max with $quota $period"
            # We use W as period constant.
            
            # Handle unlimited/throttled quota translation
            quota_to_write = decision.T_w if decision.T_w < self._B else None
            # WAIT: If T_w == B, do we write None ("max")?
            # v0 policy returns T_w = B for Normal.
            # v1 checklist: "cpu.max = 'max <period>' means unlimited".
            # If we write T_w=B (e.g. 100ms/100ms), that is NOT unlimited. It is capped at 100% CPU.
            # While "max" allows >100% if multiple CPUs?
            # CPU controller `cpu.max`: "max 100000" means unconstrained.
            # "100000 100000" means capped at 1 CPU.
            # Our policy manages a SINGLE workload on a BUDGET.
            # If Budget B = 1 CPU, then T_w=B IS the limit.
            # We should strictly enforce T_w.
            # So `quota_us = decision.T_w`.
            # UNLESS decision.T_w is explicitly a sentinel for unlimited?
            # v0 policy does not support unlimited sentinel. It supports [0, B].
            # So strictly: we enforce T_w.
            # Only if T_w was somehow None (not possible in v0 type hint) would we write max.
            # BUT, the checklist says: "cpu.max = 'max <period>' means unlimited".
            # This might be for "shutdown" or "startup"?
            # For run_loop, we just enforce T_w.
            
            write_cpu_quota(self._cgroup_path, decision.T_w, self._W_us)
            
            windows_processed += 1
            
            # 5. Schedule Next
            next_wake += self._W_sec
            
            # 6. Anti-Spin / Bounded Lag Logic
            # If we are effectively "catch-up looping" (next_wake is already past),
            # we must shift phase to avoid spinning.
            if next_wake < time.time():
                lag = time.time() - next_wake
                # How many windows did we miss?
                missed = int(lag / self._W_sec) + 1
                if missed > 0:
                    logger.warning(f"Lag implies {missed} skipped windows. Realigning.")
                    # We shift next_wake forward.
                    # We do NOT run policy for skipped windows (Usage aggregated in next real window)
                    next_wake += missed * self._W_sec
