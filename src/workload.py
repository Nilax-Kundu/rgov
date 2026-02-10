"""
Workload Identity Definition.

This module defines the identity type for workloads in the system.
Spec Reference: v2.md §3 (Workload Identity)
"""

from typing import NewType

# Strong type for WorkloadID to prevent confusion with generic strings
# Invariant I1: Workloads are distinct entities.
WorkloadID = NewType('WorkloadID', str)

def create_workload_id(name: str) -> WorkloadID:
    """
    Create a valid WorkloadID from a string.
    
    Args:
        name: The distinct name of the workload.
        
    Returns:
        WorkloadID: The typed identifier.
        
    Raises:
        ValueError: If name is empty or invalid.
    """
    if not name or not name.strip():
        raise ValueError("WorkloadID cannot be empty")
    return WorkloadID(name)
