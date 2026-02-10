"""
v2 Integration Tests (Multiple Independent Workloads)

Verifies isolation, capacity checks, and order independence.
Spec Reference: v2.md §4
"""

import time
import pytest
from unittest.mock import patch, MagicMock, call

from cgroup.orchestrator_v2 import MultiWorkloadOrchestrator
from workload import create_workload_id
from tests.cgroup.mock_kernel import MockKernel

class TestMultiWorkload:
    
    def test_capacity_rejection(self, mock_kernel):
        """Verify registration is rejected if capacity is exceeded."""
        capacity = 100_000
        W = 100_000
        orch = MultiWorkloadOrchestrator(capacity, W)
        
        # 1. Register valid workload
        w1 = create_workload_id("w1")
        orch.register_workload(w1, mock_kernel.path(), 60_000)
        
        # 2. Register accumulating valid workload
        w2 = create_workload_id("w2")
        orch.register_workload(w2, mock_kernel.path(), 40_000)
        
        # 3. Register invalid workload (excess)
        w3 = create_workload_id("w3")
        with pytest.raises(ValueError, match="Capacity exceeded"):
            orch.register_workload(w3, mock_kernel.path(), 1)
            
    def test_isolation(self):
        """Verify one workload's behavior does not affect another."""
        k1 = MockKernel()
        k2 = MockKernel()
        
        try:
            capacity = 200_000
            W = 100_000
            orch = MultiWorkloadOrchestrator(capacity, W)
            
            w1 = create_workload_id("victim")
            w2 = create_workload_id("aggressor")
            
            orch.register_workload(w1, k1.path(), 100_000)
            orch.register_workload(w2, k2.path(), 100_000)
            
            # Scenario:
            # Baseline: 0 usage.
            # Window 1:
            #   W1 usage increases by 50k (Safe).
            #   W2 usage increases by 150k (Unsafe/Overshoot).
            
            k1.set_usage(0)
            k2.set_usage(0)
            
            def sleep_update(duration):
                # Called at start of loop (waiting for Window 1)
                # Update kernels to reflect usage *during* Window 1
                k1.set_usage(50_000)
                k2.set_usage(150_000)
                
            start_time = 1000.0
            # Init -> Sleep Check (Return 1000.0) -> Sleep(0.1) -> Lag Check (1000.1)
            time_sequence = [
                start_time,          # Init next_wake = 1000.1
                start_time,          # Sleep check (now=1000.0 -> duration=0.1 -> sleep calls side effect)
                start_time + 0.1     # Lag check
            ]
            
            with patch('time.time', side_effect=time_sequence):
                with patch('time.sleep', side_effect=sleep_update):
                    orch.run_loop(max_windows=1)
                    
            # Verify W1 (Normal)
            # Usage 50k. Budget 100k. Debt 0.
            q1, p1 = k1.read_enforced_quota()
            assert q1 == 100_000, f"Victim W1 should be Normal, got {q1}"
            
            # Verify W2 (Throttled)
            # Usage 150k. Budget 100k. Debt 50k.
            q2, p2 = k2.read_enforced_quota()
            assert q2 == 0, f"Aggressor W2 should be Throttled, got {q2}"
            
        finally:
            k1.cleanup()
            k2.cleanup()

    def test_order_independence(self):
        """Verify output stability regardless of processing order."""
        k1 = MockKernel()
        k2 = MockKernel()
        
        try:
            # Scenario setup identical to isolation test
            capacity = 200_000
            W = 100_000
            orch = MultiWorkloadOrchestrator(capacity, W)
            w1 = create_workload_id("A")
            w2 = create_workload_id("B")
            orch.register_workload(w1, k1.path(), 100_000)
            orch.register_workload(w2, k2.path(), 100_000)
            
            # FORCE REVERSE ORDER (B, A) by modifying internal list
            # Normally sorted as [A, B]. We force [B, A].
            orch._workloads = [w2, w1]
            
            k1.set_usage(0)
            k2.set_usage(0)
            
            def sleep_update(duration):
                k1.set_usage(150_000) # Overshoot
                k2.set_usage(150_000) # Overshoot
                
            start_time = 1000.0
            time_sequence = [
                start_time,
                start_time,
                start_time + 0.1
            ]
            
            with patch('time.time', side_effect=time_sequence):
                with patch('time.sleep', side_effect=sleep_update):
                    orch.run_loop(max_windows=1)
            
            # Check results
            q1, _ = k1.read_enforced_quota()
            q2, _ = k2.read_enforced_quota()
            
            # Both should be throttled (0)
            # If order mattered (e.g. shared capacity), one might succeed.
            assert q1 == 0, f"W1 result unstable. Got {q1}"
            assert q2 == 0, f"W2 result unstable. Got {q2}"
            
        finally:
            k1.cleanup()
            k2.cleanup()
