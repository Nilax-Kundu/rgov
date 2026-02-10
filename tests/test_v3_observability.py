"""
v3 Observability Tests.

Tests:
1. DecisionRecord structure and content.
2. JSON Logging output format and content.
3. Queryable State Interface (get_status).
4. Window Index propagation.

Spec Reference: v3.md
"""

import pytest
import json
import logging
import time
from unittest.mock import MagicMock, patch, mock_open
from dataclasses import asdict

from policy import DecisionRecord, PolicyStateData, PolicyState, initial_state, evaluate_policy
from json_logger import setup_json_logger, log_decision
from cgroup.orchestrator import CgroupOrchestrator
from cgroup.orchestrator_v2 import MultiWorkloadOrchestrator
from workload import WorkloadID

class TestJSONLogging:
    """Test JSON logging infrastructure"""
    
    def test_log_decision_format(self):
        """Test that log_decision produces correct JSON format"""
        # Create a mock logger
        mock_logger = MagicMock()
        
        # Create a dummy record
        state = initial_state()
        record = DecisionRecord(
            window_index=None,
            state_before=state,
            debt_before=0,
            usage_us=50_000,
            budget_us=100_000,
            enforced_quota=100_000,
            state_after=state,
            debt_after=0,
            policy_rule_id="TEST_RULE",
            violated_invariant=None
        )
        
        # Log with override index
        log_decision(mock_logger, record, override_window_index=123)
        
        # Verify logger.info called with correct JSON string
        mock_logger.info.assert_called_once()
        log_entry = mock_logger.info.call_args[0][0]
        data = json.loads(log_entry)
        
        # Check integrity
        assert data['window_index'] == 123
        assert data['policy_rule_id'] == "TEST_RULE"
        assert data['state_before']['mode'] == "NORMAL" # Enum converted to string
        assert 'timestamp' in data


class TestV1Observability:
    """Test CgroupOrchestrator (v1) observability features"""
    
    @patch('cgroup.orchestrator.WindowedObserver')
    @patch('cgroup.orchestrator.write_cpu_quota')
    @patch('cgroup.orchestrator.setup_json_logger')
    def test_v1_logging_and_status(self, mock_setup_logger, mock_write, mock_observer_cls):
        """Test v1 logging and get_status()"""
        # Mock dependencies
        mock_observer = mock_observer_cls.return_value
        mock_observer.measure_window.return_value = 50_000
        
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger
        
        # Init orchestrator
        orch = CgroupOrchestrator(cgroup_path="/test", B=100_000, W_us=100_000)
        
        # Run 1 window
        # We mock time.sleep to avoid delay
        with patch('time.sleep'):
            orch.run_loop(max_windows=1)
            
        # Verify logging
        # orch._policy_orch index should be 1 locally (stats 0->1).
        # We logged with index 0.
        mock_logger.info.assert_called()
        last_log = mock_logger.info.call_args[0][0]
        data = json.loads(last_log)
        assert data['window_index'] == 0
        assert data['budget_us'] == 100_000
        
        # Verify get_status
        state, record = orch.get_status()
        assert state is not None
        assert record is not None
        assert record.usage_us == 50_000


class TestV2Observability:
    """Test MultiWorkloadOrchestrator (v2) observability features"""
    
    @patch('cgroup.orchestrator_v2.WindowedObserver')
    @patch('cgroup.orchestrator_v2.write_cpu_quota')
    @patch('cgroup.orchestrator_v2.setup_json_logger')
    def test_v2_logging_and_status(self, mock_setup_logger, mock_write, mock_observer_cls):
        """Test v2 logging and get_status()"""
        # Mock dependencies
        mock_observer = mock_observer_cls.return_value
        mock_observer.measure_window.return_value = 150_000 # Overshoot
        
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger
        
        # Init orchestrator
        orch = MultiWorkloadOrchestrator(capacity_us=200_000, W_us=100_000)
        wid = WorkloadID("test_wl")
        orch.register_workload(wid, "/test", 100_000)
        
        # Run 1 global window
        with patch('time.sleep'):
            orch.run_loop(max_windows=1)
            
        # Verify logging
        mock_logger.info.assert_called()
        last_log = mock_logger.info.call_args[0][0]
        data = json.loads(last_log)
        
        assert data['window_index'] == 0
        assert data['usage_us'] == 150_000
        assert data['policy_rule_id'] == "RULE_N2_OVER_BUDGET"
        
        # Verify get_status
        state, record = orch.get_status(wid)
        assert state.mode == PolicyState.THROTTLED
        assert record is not None
        assert record.violated_invariant == "INV_USAGE_EXCEEDS_BUDGET"

