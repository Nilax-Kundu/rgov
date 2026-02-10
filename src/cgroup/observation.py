"""
Windowed Observation Aggregator (v1)

This module implements the logic to aggregate raw cumulative counters
into per-window observations (U_w).

Spec References:
- SPEC.md §3.1 (Windowed usage)
- INVARIANTS.md O1 (Aggregated per window)
"""

from .cpu import read_cpu_usage

class WindowedObserver:
    """
    Maintains state for windowed CPU observation.
    
    Responsibility:
    - Read cumulative usage at start/end of windows.
    - Compute delta (U_w).
    - Handle counter monotonicity.
    
    Invariant O1: Aggregated per window.
    """
    
    def __init__(self, cgroup_path: str):
        """
        Initialize observer.
        
        Args:
            cgroup_path: Absolute path to cgroup.
        """
        self._cgroup_path = cgroup_path
        self._last_usage_usec = None
        
    def init_observation(self):
        """
        Initialize the observation baseline.
        Must be called once before the first window.
        """
        self._last_usage_usec = read_cpu_usage(self._cgroup_path)
        
    def measure_window(self) -> int:
        """
        Measure usage for the just-completed window.
        
        Returns:
            int: U_w (microseconds used since last measurement).
            
        Raises:
            RuntimeError: If init_observation was not called.
            ValueError: If cpu.stat is invalid.
        """
        if self._last_usage_usec is None:
            raise RuntimeError("Observer not initialized. Call init_observation() first.")
            
        current_usage = read_cpu_usage(self._cgroup_path)
        
        # Calculate delta
        U_w = current_usage - self._last_usage_usec
        
        # Sanity check for monotonicity
        if U_w < 0:
            # In v1, we assume 64-bit counters and no resets.
            # A negative value implies a kernel bug, cgroup reset, or massive wraparound.
            # We treat it as 0 to be safe, but this effectively means data loss.
            # Ideally we'd log this.
            # For now, strict v1: clamp to 0 is safer than crashing the orchestrator.
            U_w = 0
            
        # Update baseline for next window
        self._last_usage_usec = current_usage
        
        return U_w
