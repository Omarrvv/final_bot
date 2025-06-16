"""
Comprehensive Audit Logger
==========================

Comprehensive audit logging system providing:
- Structured audit event logging
- Multiple output formats (JSON, structured text)
- Audit trail integrity verification
- Performance impact monitoring

Part of Foundation Gaps Implementation - Phase 4
"""

import json
import logging
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"


class AuditCategory(Enum):
    """Audit event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"


@dataclass
class AuditEvent:
    """Structured audit event"""
    event_id: str
    timestamp: datetime
    level: AuditLevel
    category: AuditCategory
    action: str
    resource: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    details: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.metadata is None:
            self.metadata = {}
        
        # Add system metadata
        self.metadata.update({
            "hostname": self._get_hostname(),
            "process_id": self._get_process_id(),
            "thread_id": threading.get_ident()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        data['category'] = self.category.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    def calculate_hash(self) -> str:
        """Calculate hash for integrity verification"""
        # Create deterministic string representation
        hash_data = f"{self.event_id}|{self.timestamp.isoformat()}|{self.level.value}|{self.category.value}|{self.action}|{self.resource}"
        return hashlib.sha256(hash_data.encode()).hexdigest()
    
    @staticmethod
    def _get_hostname() -> str:
        """Get system hostname"""
        import socket
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"
    
    @staticmethod
    def _get_process_id() -> int:
        """Get process ID"""
        import os
        return os.getpid()


class AuditLogger:
    """
    Comprehensive audit logging system.
    
    Features:
    - Structured audit event logging
    - Multiple output formats and destinations
    - Audit trail integrity verification
    - Performance monitoring and optimization
    - Configurable retention policies
    """
    
    def __init__(self,
                 log_file: str = "logs/audit.log",
                 json_log_file: str = "logs/audit.json",
                 enable_console: bool = True,
                 enable_integrity_check: bool = True,
                 buffer_size: int = 100,
                 flush_interval: int = 60):
        """
        Initialize audit logger.
        
        Args:
            log_file: Path to structured text log file
            json_log_file: Path to JSON log file
            enable_console: Enable console output
            enable_integrity_check: Enable integrity verification
            buffer_size: Number of events to buffer before flushing
            flush_interval: Seconds between automatic flushes
        """
        self.log_file = Path(log_file)
        self.json_log_file = Path(json_log_file)
        self.enable_console = enable_console
        self.enable_integrity_check = enable_integrity_check
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # Create log directories
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.json_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Event buffer for performance
        self.event_buffer: List[AuditEvent] = []
        self.buffer_lock = threading.Lock()
        
        # Integrity tracking
        self.event_hashes: List[str] = []
        self.integrity_file = self.log_file.parent / "audit_integrity.json"
        
        # Performance metrics
        self.metrics = {
            "events_logged": 0,
            "events_buffered": 0,
            "flush_count": 0,
            "integrity_checks": 0,
            "performance_warnings": 0
        }
        
        # Auto-flush timer
        self.flush_timer: Optional[threading.Timer] = None
        self._start_auto_flush()
        
        logger.info("AuditLogger initialized")
    
    def log_event(self, 
                  level: AuditLevel,
                  category: AuditCategory,
                  action: str,
                  resource: str,
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  request_id: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an audit event.
        
        Args:
            level: Event severity level
            category: Event category
            action: Action performed
            resource: Resource affected
            user_id: User identifier
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request identifier
            details: Additional event details
            metadata: Additional metadata
            
        Returns:
            str: Event ID
        """
        try:
            # Create audit event
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                level=level,
                category=category,
                action=action,
                resource=resource,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                details=details or {},
                metadata=metadata or {}
            )
            
            # Add to buffer
            with self.buffer_lock:
                self.event_buffer.append(event)
                self.metrics["events_buffered"] += 1
                
                # Flush if buffer is full
                if len(self.event_buffer) >= self.buffer_size:
                    self._flush_buffer()
            
            # Console output if enabled
            if self.enable_console:
                self._log_to_console(event)
            
            self.metrics["events_logged"] += 1
            
            return event.event_id
            
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
            raise
    
    def log_authentication(self, action: str, user_id: str, success: bool, 
                          ip_address: str = None, details: Dict[str, Any] = None) -> str:
        """Log authentication event"""
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        details = details or {}
        details.update({"success": success})
        
        return self.log_event(
            level=level,
            category=AuditCategory.AUTHENTICATION,
            action=action,
            resource=f"user:{user_id}",
            user_id=user_id,
            ip_address=ip_address,
            details=details
        )
    
    def log_authorization(self, action: str, user_id: str, resource: str, 
                         granted: bool, ip_address: str = None, 
                         details: Dict[str, Any] = None) -> str:
        """Log authorization event"""
        level = AuditLevel.INFO if granted else AuditLevel.WARNING
        details = details or {}
        details.update({"granted": granted})
        
        return self.log_event(
            level=level,
            category=AuditCategory.AUTHORIZATION,
            action=action,
            resource=resource,
            user_id=user_id,
            ip_address=ip_address,
            details=details
        )
    
    def log_data_access(self, action: str, resource: str, user_id: str = None,
                       record_count: int = None, details: Dict[str, Any] = None) -> str:
        """Log data access event"""
        details = details or {}
        if record_count is not None:
            details["record_count"] = record_count
        
        return self.log_event(
            level=AuditLevel.INFO,
            category=AuditCategory.DATA_ACCESS,
            action=action,
            resource=resource,
            user_id=user_id,
            details=details
        )
    
    def log_configuration_change(self, action: str, resource: str, user_id: str,
                                old_value: Any = None, new_value: Any = None,
                                details: Dict[str, Any] = None) -> str:
        """Log configuration change event"""
        details = details or {}
        if old_value is not None:
            details["old_value"] = str(old_value)
        if new_value is not None:
            details["new_value"] = str(new_value)
        
        return self.log_event(
            level=AuditLevel.INFO,
            category=AuditCategory.CONFIGURATION,
            action=action,
            resource=resource,
            user_id=user_id,
            details=details
        )
    
    def log_security_event(self, action: str, resource: str, severity: str = "medium",
                          ip_address: str = None, details: Dict[str, Any] = None) -> str:
        """Log security event"""
        level_map = {
            "low": AuditLevel.INFO,
            "medium": AuditLevel.WARNING,
            "high": AuditLevel.ERROR,
            "critical": AuditLevel.CRITICAL
        }
        level = level_map.get(severity, AuditLevel.WARNING)
        
        details = details or {}
        details["severity"] = severity
        
        return self.log_event(
            level=level,
            category=AuditCategory.SECURITY,
            action=action,
            resource=resource,
            ip_address=ip_address,
            details=details
        )
    
    def log_api_request(self, method: str, endpoint: str, user_id: str = None,
                       session_id: str = None, ip_address: str = None,
                       user_agent: str = None, request_id: str = None,
                       response_code: int = None, response_time_ms: float = None,
                       details: Dict[str, Any] = None) -> str:
        """Log API request event"""
        details = details or {}
        if response_code is not None:
            details["response_code"] = response_code
        if response_time_ms is not None:
            details["response_time_ms"] = response_time_ms
        
        # Determine level based on response code
        level = AuditLevel.INFO
        if response_code and response_code >= 400:
            level = AuditLevel.WARNING if response_code < 500 else AuditLevel.ERROR
        
        return self.log_event(
            level=level,
            category=AuditCategory.API,
            action=f"{method} {endpoint}",
            resource=endpoint,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details=details
        )
    
    def log_database_operation(self, operation: str, table: str, user_id: str = None,
                              record_count: int = None, execution_time_ms: float = None,
                              details: Dict[str, Any] = None) -> str:
        """Log database operation event"""
        details = details or {}
        if record_count is not None:
            details["record_count"] = record_count
        if execution_time_ms is not None:
            details["execution_time_ms"] = execution_time_ms
        
        return self.log_event(
            level=AuditLevel.INFO,
            category=AuditCategory.DATABASE,
            action=operation,
            resource=f"table:{table}",
            user_id=user_id,
            details=details
        )
    
    def log_error(self, error: str, resource: str, user_id: str = None,
                 error_type: str = None, stack_trace: str = None,
                 details: Dict[str, Any] = None) -> str:
        """Log error event"""
        details = details or {}
        if error_type:
            details["error_type"] = error_type
        if stack_trace:
            details["stack_trace"] = stack_trace
        
        return self.log_event(
            level=AuditLevel.ERROR,
            category=AuditCategory.ERROR,
            action="error_occurred",
            resource=resource,
            user_id=user_id,
            details=details
        )
    
    def flush(self) -> None:
        """Manually flush buffered events"""
        with self.buffer_lock:
            self._flush_buffer()
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify audit trail integrity.
        
        Returns:
            Dict containing integrity verification results
        """
        if not self.enable_integrity_check:
            return {"enabled": False, "message": "Integrity checking disabled"}
        
        try:
            # Load stored hashes
            stored_hashes = self._load_integrity_hashes()
            
            # Read and verify log entries
            verified_count = 0
            tampered_events = []
            
            if self.json_log_file.exists():
                with open(self.json_log_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            event_data = json.loads(line.strip())
                            event_id = event_data.get('event_id')
                            
                            if event_id in stored_hashes:
                                # Recreate event and verify hash
                                expected_hash = stored_hashes[event_id]
                                
                                # Calculate hash from stored data
                                hash_data = f"{event_data['event_id']}|{event_data['timestamp']}|{event_data['level']}|{event_data['category']}|{event_data['action']}|{event_data['resource']}"
                                actual_hash = hashlib.sha256(hash_data.encode()).hexdigest()
                                
                                if actual_hash == expected_hash:
                                    verified_count += 1
                                else:
                                    tampered_events.append({
                                        "event_id": event_id,
                                        "line_number": line_num,
                                        "expected_hash": expected_hash,
                                        "actual_hash": actual_hash
                                    })
                        except json.JSONDecodeError:
                            continue
            
            self.metrics["integrity_checks"] += 1
            
            return {
                "enabled": True,
                "verified_events": verified_count,
                "tampered_events": len(tampered_events),
                "tampered_details": tampered_events,
                "integrity_intact": len(tampered_events) == 0
            }
            
        except Exception as e:
            logger.error(f"Error verifying audit integrity: {str(e)}")
            return {"enabled": True, "error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get audit logger performance metrics"""
        with self.buffer_lock:
            current_buffer_size = len(self.event_buffer)
        
        return {
            **self.metrics,
            "current_buffer_size": current_buffer_size,
            "buffer_utilization": current_buffer_size / self.buffer_size,
            "integrity_enabled": self.enable_integrity_check
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old log files.
        
        Args:
            days_to_keep: Number of days of logs to retain
            
        Returns:
            Dict containing cleanup results
        """
        try:
            from datetime import timedelta
            import os
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Archive old logs (placeholder - would implement actual archiving)
            archived_files = []
            deleted_files = []
            
            # For now, just report what would be cleaned up
            log_dir = self.log_file.parent
            for log_file in log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    # Would archive/delete here
                    archived_files.append(str(log_file))
            
            return {
                "cutoff_date": cutoff_date.isoformat(),
                "archived_files": archived_files,
                "deleted_files": deleted_files,
                "total_processed": len(archived_files) + len(deleted_files)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {str(e)}")
            return {"error": str(e)}
    
    def shutdown(self) -> None:
        """Shutdown audit logger and flush remaining events"""
        try:
            # Stop auto-flush timer
            if self.flush_timer:
                self.flush_timer.cancel()
            
            # Flush remaining events
            self.flush()
            
            logger.info("AuditLogger shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during audit logger shutdown: {str(e)}")
    
    # Private methods
    
    def _flush_buffer(self) -> None:
        """Flush buffered events to log files"""
        if not self.event_buffer:
            return
        
        try:
            events_to_flush = self.event_buffer.copy()
            self.event_buffer.clear()
            
            # Write to structured text log
            with open(self.log_file, 'a', encoding='utf-8') as f:
                for event in events_to_flush:
                    log_line = self._format_structured_log(event)
                    f.write(log_line + '\n')
            
            # Write to JSON log
            with open(self.json_log_file, 'a', encoding='utf-8') as f:
                for event in events_to_flush:
                    f.write(event.to_json() + '\n')
            
            # Update integrity hashes
            if self.enable_integrity_check:
                for event in events_to_flush:
                    event_hash = event.calculate_hash()
                    self.event_hashes.append(event_hash)
                
                self._save_integrity_hashes()
            
            self.metrics["flush_count"] += 1
            
        except Exception as e:
            logger.error(f"Error flushing audit events: {str(e)}")
            # Put events back in buffer on error
            self.event_buffer.extend(events_to_flush)
    
    def _format_structured_log(self, event: AuditEvent) -> str:
        """Format event as structured text log entry"""
        return (f"[{event.timestamp.isoformat()}] "
                f"{event.level.value.upper()} "
                f"{event.category.value} "
                f"action={event.action} "
                f"resource={event.resource} "
                f"user={event.user_id or 'anonymous'} "
                f"event_id={event.event_id}")
    
    def _log_to_console(self, event: AuditEvent) -> None:
        """Log event to console"""
        console_logger = logging.getLogger("audit.console")
        log_level = {
            AuditLevel.INFO: logging.INFO,
            AuditLevel.WARNING: logging.WARNING,
            AuditLevel.ERROR: logging.ERROR,
            AuditLevel.CRITICAL: logging.CRITICAL,
            AuditLevel.SECURITY: logging.WARNING
        }.get(event.level, logging.INFO)
        
        console_logger.log(log_level, self._format_structured_log(event))
    
    def _start_auto_flush(self) -> None:
        """Start automatic flush timer"""
        def auto_flush():
            try:
                with self.buffer_lock:
                    if self.event_buffer:
                        self._flush_buffer()
            except Exception as e:
                logger.error(f"Error in auto-flush: {str(e)}")
            finally:
                # Schedule next flush
                self.flush_timer = threading.Timer(self.flush_interval, auto_flush)
                self.flush_timer.start()
        
        self.flush_timer = threading.Timer(self.flush_interval, auto_flush)
        self.flush_timer.start()
    
    def _load_integrity_hashes(self) -> Dict[str, str]:
        """Load integrity hashes from file"""
        try:
            if self.integrity_file.exists():
                with open(self.integrity_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading integrity hashes: {str(e)}")
            return {}
    
    def _save_integrity_hashes(self) -> None:
        """Save integrity hashes to file"""
        try:
            # Create mapping of event IDs to hashes
            hash_mapping = {}
            
            # Read events from JSON log to get event IDs
            if self.json_log_file.exists():
                with open(self.json_log_file, 'r') as f:
                    for line, event_hash in zip(f, self.event_hashes):
                        try:
                            event_data = json.loads(line.strip())
                            event_id = event_data.get('event_id')
                            if event_id:
                                hash_mapping[event_id] = event_hash
                        except json.JSONDecodeError:
                            continue
            
            with open(self.integrity_file, 'w') as f:
                json.dump(hash_mapping, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving integrity hashes: {str(e)}") 