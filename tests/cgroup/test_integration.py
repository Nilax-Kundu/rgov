"""
Integration Tests for v1 Cgroup Orchestrator

Verifies the full stack: Orchestrator -> Observer -> Policy -> Enforcer -> Mock Kernel.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from cgroup.orchestrator import CgroupOrchestrator
from policy import PolicyState


class TestOrchestration:
    
    def test_basic_loop(self, mock_kernel):
        """Verify basic loop operation: usage read -> policy -> enforcement written."""
        # Setup
        cgroup_path = mock_kernel.path()
        B = 100_000
        W_us = 100_000
        W_sec = 0.1
        orch = CgroupOrchestrator(cgroup_path, B, W_us)
        
        # We need to simulate:
        # 1. Start (Usage 0)
        # 2. Window 1 (Usage 50k) -> Enforce B
        # 3. Window 2 (Usage 200k/Delta 150k) -> Enforce B (decision made after window, affects NEXT)
        #    Wait. The enforcement happens at the END of the window for the NEXT window.
        #    Window 1 (50k). Debt 0. Decision: Normal (B). Enforce B.
        #    Window 2 (150k). Debt 50k. Decision: Throttled (0). Enforce 0.
        #    Window 3 (0k). Debt 0 (paid down). Decision: Normal (B). Enforce B.
        
        validation_errors = []
        
        def sleep_side_effect(duration):
            # This is called AT THE START of each loop iteration (waiting for next window).
            # We can use this to update the mock kernel for the *upcoming* measurement
            # and verify the *previous* enforcement.
            
            nonlocal window_count
            window_count += 1
            
            # Read current enforcement (result of previous window)
            try:
                quota, period = mock_kernel.read_enforced_quota()
                if window_count == 1:
                    # Before Window 1 (Just started). 
                    # Enforcement hasn't run yet, so it should be whatever MockKernel defaulted to (None/max)
                    # or strictly, we don't care, but for this test we know it's None.
                    if quota is not None: validation_errors.append(f"Window 1 Start: Expected None, got {quota}")
                    # Update usage for Window 1: 50k
                    mock_kernel.set_usage(50_000)
                    
                elif window_count == 2:
                    # After Window 1. 50k usage. Under budget. State Normal. Enforce B.
                    if quota != B: validation_errors.append(f"Window 2 Start: Expected {B}, got {quota}")
                    # Update usage for Window 2: 50k -> 200k (Delta 150k)
                    mock_kernel.set_usage(200_000)
                    
                elif window_count == 3:
                     # After Window 2. 150k usage. Over budget. State Throttled. Enforce 0.
                     if quota != 0: validation_errors.append(f"Window 3 Start: Expected 0, got {quota}")
                     # Update usage for Window 3: 200k -> 200k (Delta 0)
                     mock_kernel.set_usage(200_000)
                     
            except Exception as e:
                validation_errors.append(str(e))

        window_count = 0
        
        # Mock time.time() is tricky because run_loop calls it multiple times.
        # We can just return a monotonic sequence.
        # And mock sleep() to trigger our side effect.
        
        # time values:
        # Start: 1000
        # Loop 1: sleep(check), wake, drift check
        # ...
        
        time_sequence = [1000.0 + i*0.01 for i in range(100)] # Plenty of ticks
        
        with patch('time.time', side_effect=time_sequence):
            with patch('time.sleep', side_effect=sleep_side_effect):
                 orch.run_loop(max_windows=3)
        
        # Final check (After loop 3)
        # Usage 0. Debt paid. State Normal. Enforce B.
        quota, period = mock_kernel.read_enforced_quota()
        if quota != B:
             validation_errors.append(f"Final State: Expected {B}, got {quota}")
             
        assert not validation_errors, f"Validation errors: {validation_errors}"

    def test_drift_handling(self, mock_kernel):
        """Verify bounded drift handling: skip windows if very late."""
        cgroup_path = mock_kernel.path()
        B = 100_000
        W_us = 100_000
        W_sec = 0.1
        orch = CgroupOrchestrator(cgroup_path, B, W_us)
        
        # Simulate a massive lag (2.5 windows)
        start_time = 1000.0
        with patch('time.time', side_effect=[
            start_time,          # Init next_wake
            start_time + 0.35,   # Sleep return (Late!)
            start_time + 0.35,   # Wake
            start_time + 0.35,   # Lag check (drift = 0.25)
            # Realign Logic:
            # lag = 0.25. missed = int(0.25/0.1) + 1 = 3?
            # next_wake jumps.
            start_time + 0.35    # Realign check time
        ]):
            with patch('time.sleep'):
                # We expect warning logs about drift
                with patch('cgroup.orchestrator.logger') as mock_logger:
                    mock_kernel.set_usage(10_000)
                    orch.run_loop(max_windows=1)
                    
                    # Verify warning
                    assert mock_logger.warning.call_count >= 1
                    args = mock_logger.warning.call_args_list[0][0][0]
                    # Check for keywords from implementation
                    assert "drift detected" in args or "skipped windows" in args

    def test_idempotency(self, mock_kernel):
        """Verify enforcement idempotency."""
        from cgroup.cpu import write_cpu_quota
        cgroup_path = mock_kernel.path()
        
        # Write same value twice
        write_cpu_quota(cgroup_path, 50_000, 100_000)
        write_cpu_quota(cgroup_path, 50_000, 100_000)
        
        # Verify content
        quota, period = mock_kernel.read_enforced_quota()
        assert quota == 50_000
        assert period == 100_000
        
    def test_unlimited_quota(self, mock_kernel):
        """Verify explicit 'max' writing."""
        from cgroup.cpu import write_cpu_quota
        cgroup_path = mock_kernel.path()
        
        write_cpu_quota(cgroup_path, None, 100_000)
        
        with open(mock_kernel.cpu_max, "r") as f:
            content = f.read().strip()
        assert content == "max 100000"
