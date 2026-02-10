"""
CPU Resource Control (v1)

This module implements kernel interaction for CPU control via cgroups v2.
It handles reading observations and enforcing quotas.

Spec References:
- SPEC.md §4.1 (Observation)
- SPEC.md §4.2 (Enforcement)
- v1.md (Single Workload Kernel Binding)
"""

import os

def read_cpu_usage(cgroup_path: str) -> int:
    """
    Read current CPU usage in microseconds from cpu.stat.
    
    Args:
        cgroup_path: Absolute path to the cgroup directory.
        
    Returns:
        int: Total CPU usage in microseconds.
        
    Raises:
        FileNotFoundError: If cpu.stat does not exist.
        PermissionError: If cpu.stat cannot be read.
        ValueError: If usage_usec cannot be parsed.
        OSError: For other I/O errors.
        
    Invariant O2: Derived exclusively from cpu.stat:usage_usec.
    Invariant O3: No interpretation, smoothing, or correction.
    """
    stat_file = os.path.join(cgroup_path, "cpu.stat")
    
    with open(stat_file, "r") as f:
        for line in f:
            if line.startswith("usage_usec"):
                # format: usage_usec 123456
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1])
                    
    raise ValueError(f"Could not find usage_usec in {stat_file}")


def write_cpu_quota(cgroup_path: str, quota_us: int | None, period_us: int) -> None:
    """
    Write CPU quota to cpu.max.
    
    Args:
        cgroup_path: Absolute path to the cgroup directory.
        quota_us: Quota in microseconds, or None for 'max' (unlimited).
        period_us: Period in microseconds.
        
    Raises:
        FileNotFoundError: If cpu.max does not exist.
        PermissionError: If cpu.max cannot be written.
        OSError: For other I/O errors.
        
    Invariant E1: Use cpu.max exclusively.
    Invariant E3: Idempotency (writing same value is safe).
    
    Rules:
        - quota_us=None -> "max <period>"
        - quota_us=0 -> "0 <period>" (fully throttled)
        - quota_us>0 -> "<quota> <period>"
    """
    max_file = os.path.join(cgroup_path, "cpu.max")
    
    # Format the value string
    if quota_us is None:
        quota_str = "max"
    else:
        # P2: Budget Bound is enforced by policy, this function just writes what it's given
        # But we must ensure it's non-negative if strictly typed
        if quota_us < 0:
             raise ValueError(f"Invalid negative quota: {quota_us}")
        quota_str = str(quota_us)
        
    value = f"{quota_str} {period_us}"
    
    # Write to file
    # Note: cgroup writes are atomic, but we overwrite strictly
    with open(max_file, "w") as f:
        f.write(value)
