"""
Structured Logging Infrastructure (v3).

Implements JSON structured logging for policy decisions.
Ensures logs are machine-parsable and sufficient for replay.

Spec Reference: v3.md §2
"""

import json
import logging
import time
from dataclasses import asdict, is_dataclass
from typing import Any
from enum import Enum

from policy import DecisionRecord

class JSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder for rgov types."""
    def default(self, o: Any) -> Any:
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, Enum):
            return o.value
        return super().default(o)

def setup_json_logger(name: str = "rgov.trace", log_file: str = "rgov_trace.jsonl") -> logging.Logger:
    """
    Setup a logger that writes JSON lines.
    
    Args:
        name: Logger name.
        log_file: Path to log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False # Do not propagate to root logger (avoid console noise)
    
    # Check if handler exists to avoid duplicates
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(message)s') # Raw message only (which will be JSON)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def log_decision(
    logger: logging.Logger, 
    record: DecisionRecord,
    override_window_index: int = None
) -> None:
    """
    Log a decision record as a JSON line.
    
    Adds a non-semantic wall-clock timestamp.
    """
    data = asdict(record)
    
    # Inject window index if provided (authoritative source)
    if override_window_index is not None:
        data['window_index'] = override_window_index
    
    # Enum handling
    # The JSONEncoder handles Enums in the dump
    
    # Add non-semantic timestamp
    data['timestamp'] = time.time()
    
    # Serialize
    json_line = json.dumps(data, cls=JSONEncoder)
    
    logger.info(json_line)
