"""
Mock Kernel for v1 Integration Tests

This module provides a mock cgroup environment for testing the CgroupOrchestrator.
It simulates the kernel interface (files) without needing root or real cgroups.

Spec References:
- TESTING.md §2.6 (Mock Kernel)
"""

import os
import tempfile
import shutil

class MockKernel:
    """
    Simulates a cgroup directory with cpu.stat and cpu.max.
    """
    
    def __init__(self):
        self.root_dir = tempfile.mkdtemp(prefix="rgov_mock_cgroup_")
        self.cpu_stat = os.path.join(self.root_dir, "cpu.stat")
        self.cpu_max = os.path.join(self.root_dir, "cpu.max")
        
        # Initialize default kernel state
        self.set_usage(0)
        self.set_quota(None, 100_000)
        
    def cleanup(self):
        """Remove temporary directory."""
        shutil.rmtree(self.root_dir)
        
    def path(self) -> str:
        """Return path to cgroup root."""
        return self.root_dir
        
    # --- Kernel Simulation Methods ---
    
    def set_usage(self, usage_usec: int):
        """Simulate kernel updating cpu.stat."""
        with open(self.cpu_stat, "w") as f:
            # Matches format in read_cpu_usage
            f.write(f"usage_usec {usage_usec}\n")
            f.write("user_usec 0\n")
            f.write("system_usec 0\n")
            
    def set_quota(self, quota: int | None, period: int):
        """Simulate explicit kernel state for quota (usually unnecessary as orchestrator writes it)."""
        q_str = "max" if quota is None else str(quota)
        with open(self.cpu_max, "w") as f:
            f.write(f"{q_str} {period}\n")
            
    # --- Verification Methods ---
            
    def read_enforced_quota(self) -> tuple[int | None, int]:
        """Read what the orchestrator wrote to cpu.max."""
        with open(self.cpu_max, "r") as f:
            content = f.read().strip()
        
        parts = content.split()
        if len(parts) != 2:
            raise ValueError(f"Invalid cpu.max content: {content}")
            
        quota_str, period_str = parts
        period = int(period_str)
        quota = None if quota_str == "max" else int(quota_str)
        return quota, period
