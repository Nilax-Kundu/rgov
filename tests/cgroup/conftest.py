"""
Pytest fixtures for cgroup tests.
"""

import pytest
from .mock_kernel import MockKernel

@pytest.fixture
def mock_kernel():
    """Yields a MockKernel instance, cleaning up after."""
    kernel = MockKernel()
    try:
        yield kernel
    finally:
        kernel.cleanup()
