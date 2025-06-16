"""
Log Aggregator
==============

Log aggregation system providing:
- Multi-source log collection
- Log parsing and normalization
- Log analysis and reporting
- Performance metrics extraction

Part of Foundation Gaps Implementation - Phase 4
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Log entry structure"""
    timestamp: datetime
    level: LogLevel
    source: str
    message: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LogAggregator:
    """
    Log aggregation system.
    
    Features:
    - Multi-source log collection
    - Log parsing and analysis
    - Performance metrics
    - Reporting capabilities
    """
    
    def __init__(self):
        """Initialize log aggregator"""
        self.entries: List[LogEntry] = []
        
    def add_entry(self, entry: LogEntry) -> None:
        """Add a log entry"""
        self.entries.append(entry)
        
    def get_entries(self, 
                   level: Optional[LogLevel] = None,
                   source: Optional[str] = None,
                   limit: Optional[int] = None) -> List[LogEntry]:
        """Get filtered log entries"""
        filtered = self.entries
        
        if level:
            filtered = [e for e in filtered if e.level == level]
        if source:
            filtered = [e for e in filtered if e.source == source]
        if limit:
            filtered = filtered[-limit:]
            
        return filtered
        
    def get_stats(self) -> Dict[str, Any]:
        """Get log statistics"""
        return {
            "total_entries": len(self.entries),
            "by_level": {level.value: len([e for e in self.entries if e.level == level]) 
                        for level in LogLevel},
            "sources": list(set(e.source for e in self.entries))
        } 