"""
Backup Scheduler
===============

Automated backup scheduling system providing:
- Cron-like scheduling for regular backups
- Background task execution
- Backup retention management
- Health monitoring and alerting

Part of Foundation Gaps Implementation - Phase 2
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import logging

from .backup_manager import BackupManager, BackupError

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Backup schedule types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class BackupSchedule:
    """Backup schedule configuration"""
    name: str
    schedule_type: ScheduleType
    hour: int = 2  # Default to 2 AM
    minute: int = 0
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None  # 1-31
    enabled: bool = True
    compress: bool = True
    include_data: bool = True
    retention_days: int = 30
    retention_minimum: int = 5
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BackupScheduler:
    """
    Automated backup scheduler with cron-like functionality.
    
    Features:
    - Multiple schedule types (daily, weekly, monthly)
    - Background execution with threading
    - Automatic cleanup based on retention policies
    - Health monitoring and error handling
    - Callback support for notifications
    """
    
    def __init__(self, backup_manager: BackupManager):
        """
        Initialize backup scheduler.
        
        Args:
            backup_manager: BackupManager instance for executing backups
        """
        self.backup_manager = backup_manager
        self.schedules: Dict[str, BackupSchedule] = {}
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.last_run_times: Dict[str, datetime] = {}
        self.execution_stats: Dict[str, Dict[str, Any]] = {}
        
        # Callback functions
        self.on_backup_success: Optional[Callable] = None
        self.on_backup_failure: Optional[Callable] = None
        self.on_cleanup_complete: Optional[Callable] = None
        
        logger.info("BackupScheduler initialized")
    
    def add_schedule(self, schedule: BackupSchedule) -> None:
        """
        Add a backup schedule.
        
        Args:
            schedule: BackupSchedule configuration
        """
        self.schedules[schedule.name] = schedule
        self.execution_stats[schedule.name] = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_success": None,
            "last_failure": None,
            "average_duration_seconds": 0.0
        }
        logger.info(f"Added backup schedule: {schedule.name} ({schedule.schedule_type.value})")
    
    def remove_schedule(self, schedule_name: str) -> bool:
        """
        Remove a backup schedule.
        
        Args:
            schedule_name: Name of schedule to remove
            
        Returns:
            bool: True if schedule was removed
        """
        if schedule_name in self.schedules:
            del self.schedules[schedule_name]
            if schedule_name in self.last_run_times:
                del self.last_run_times[schedule_name]
            if schedule_name in self.execution_stats:
                del self.execution_stats[schedule_name]
            logger.info(f"Removed backup schedule: {schedule_name}")
            return True
        return False
    
    def get_schedule(self, schedule_name: str) -> Optional[BackupSchedule]:
        """
        Get a backup schedule by name.
        
        Args:
            schedule_name: Name of schedule
            
        Returns:
            BackupSchedule or None if not found
        """
        return self.schedules.get(schedule_name)
    
    def list_schedules(self) -> List[BackupSchedule]:
        """
        List all backup schedules.
        
        Returns:
            List of BackupSchedule objects
        """
        return list(self.schedules.values())
    
    def start(self) -> None:
        """Start the backup scheduler in background thread."""
        if self.running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Backup scheduler started")
    
    def stop(self) -> None:
        """Stop the backup scheduler."""
        if not self.running:
            logger.warning("Backup scheduler is not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        logger.info("Backup scheduler stopped")
    
    def execute_schedule_now(self, schedule_name: str) -> bool:
        """
        Execute a specific schedule immediately.
        
        Args:
            schedule_name: Name of schedule to execute
            
        Returns:
            bool: True if execution was successful
        """
        schedule = self.schedules.get(schedule_name)
        if not schedule:
            logger.error(f"Schedule not found: {schedule_name}")
            return False
        
        if not schedule.enabled:
            logger.warning(f"Schedule is disabled: {schedule_name}")
            return False
        
        return self._execute_backup(schedule)
    
    def get_next_run_time(self, schedule_name: str) -> Optional[datetime]:
        """
        Get the next scheduled run time for a schedule.
        
        Args:
            schedule_name: Name of schedule
            
        Returns:
            datetime of next run or None if schedule not found
        """
        schedule = self.schedules.get(schedule_name)
        if not schedule or not schedule.enabled:
            return None
        
        now = datetime.now()
        last_run = self.last_run_times.get(schedule_name)
        
        if schedule.schedule_type == ScheduleType.DAILY:
            next_run = now.replace(hour=schedule.hour, minute=schedule.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif schedule.schedule_type == ScheduleType.WEEKLY:
            # Find next occurrence of the specified day of week
            days_ahead = schedule.day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=schedule.hour, minute=schedule.minute, second=0, microsecond=0)
            return next_run
        
        elif schedule.schedule_type == ScheduleType.MONTHLY:
            # Find next occurrence of the specified day of month
            next_run = now.replace(day=schedule.day_of_month, hour=schedule.hour, 
                                 minute=schedule.minute, second=0, microsecond=0)
            if next_run <= now:
                # Move to next month
                if next_run.month == 12:
                    next_run = next_run.replace(year=next_run.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=next_run.month + 1)
            return next_run
        
        return None
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """
        Get scheduler statistics.
        
        Returns:
            Dict containing scheduler statistics
        """
        total_schedules = len(self.schedules)
        enabled_schedules = sum(1 for s in self.schedules.values() if s.enabled)
        
        return {
            "running": self.running,
            "total_schedules": total_schedules,
            "enabled_schedules": enabled_schedules,
            "disabled_schedules": total_schedules - enabled_schedules,
            "execution_stats": self.execution_stats.copy(),
            "next_runs": {
                name: self.get_next_run_time(name).isoformat() if self.get_next_run_time(name) else None
                for name in self.schedules.keys()
            }
        }
    
    # Callback registration methods
    
    def set_success_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Set callback for successful backups.
        
        Args:
            callback: Function(schedule_name, backup_name) -> None
        """
        self.on_backup_success = callback
    
    def set_failure_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """
        Set callback for failed backups.
        
        Args:
            callback: Function(schedule_name, error) -> None
        """
        self.on_backup_failure = callback
    
    def set_cleanup_callback(self, callback: Callable[[str, int], None]) -> None:
        """
        Set callback for cleanup completion.
        
        Args:
            callback: Function(schedule_name, deleted_count) -> None
        """
        self.on_cleanup_complete = callback
    
    # Private methods
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop running in background thread."""
        logger.info("Backup scheduler loop started")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check each schedule
                for schedule_name, schedule in self.schedules.items():
                    if not schedule.enabled:
                        continue
                    
                    if self._should_run_now(schedule_name, schedule, current_time):
                        logger.info(f"Executing scheduled backup: {schedule_name}")
                        self._execute_backup(schedule)
                        self.last_run_times[schedule_name] = current_time
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Continue after error
        
        logger.info("Backup scheduler loop stopped")
    
    def _should_run_now(self, schedule_name: str, schedule: BackupSchedule, current_time: datetime) -> bool:
        """
        Check if a schedule should run now.
        
        Args:
            schedule_name: Name of schedule
            schedule: BackupSchedule object
            current_time: Current datetime
            
        Returns:
            bool: True if schedule should run
        """
        last_run = self.last_run_times.get(schedule_name)
        
        # If never run before, check if it's time
        if not last_run:
            return self._is_schedule_time(schedule, current_time)
        
        # Check if enough time has passed since last run
        if schedule.schedule_type == ScheduleType.DAILY:
            return (current_time - last_run).days >= 1 and self._is_schedule_time(schedule, current_time)
        elif schedule.schedule_type == ScheduleType.WEEKLY:
            return (current_time - last_run).days >= 7 and self._is_schedule_time(schedule, current_time)
        elif schedule.schedule_type == ScheduleType.MONTHLY:
            return (current_time - last_run).days >= 28 and self._is_schedule_time(schedule, current_time)
        
        return False
    
    def _is_schedule_time(self, schedule: BackupSchedule, current_time: datetime) -> bool:
        """
        Check if current time matches schedule time.
        
        Args:
            schedule: BackupSchedule object
            current_time: Current datetime
            
        Returns:
            bool: True if it's time to run
        """
        if current_time.hour != schedule.hour or current_time.minute != schedule.minute:
            return False
        
        if schedule.schedule_type == ScheduleType.WEEKLY:
            return current_time.weekday() == schedule.day_of_week
        elif schedule.schedule_type == ScheduleType.MONTHLY:
            return current_time.day == schedule.day_of_month
        
        return True  # Daily schedules only check hour/minute
    
    def _execute_backup(self, schedule: BackupSchedule) -> bool:
        """
        Execute a backup for the given schedule.
        
        Args:
            schedule: BackupSchedule to execute
            
        Returns:
            bool: True if backup was successful
        """
        start_time = time.time()
        stats = self.execution_stats[schedule.name]
        stats["total_runs"] += 1
        
        try:
            # Generate backup name with schedule prefix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{schedule.name}_{timestamp}"
            
            # Create backup
            backup_name = self.backup_manager.create_backup(
                backup_name=backup_name,
                compress=schedule.compress,
                include_data=schedule.include_data,
                metadata={
                    "schedule_name": schedule.name,
                    "schedule_type": schedule.schedule_type.value,
                    "automated": True,
                    **schedule.metadata
                }
            )
            
            # Update success stats
            stats["successful_runs"] += 1
            stats["last_success"] = datetime.now().isoformat()
            
            # Calculate average duration
            duration = time.time() - start_time
            if stats["successful_runs"] == 1:
                stats["average_duration_seconds"] = duration
            else:
                stats["average_duration_seconds"] = (
                    (stats["average_duration_seconds"] * (stats["successful_runs"] - 1) + duration) 
                    / stats["successful_runs"]
                )
            
            logger.info(f"Scheduled backup completed successfully: {backup_name} ({duration:.2f}s)")
            
            # Execute cleanup
            deleted_count = self.backup_manager.cleanup_old_backups(
                keep_days=schedule.retention_days,
                keep_minimum=schedule.retention_minimum
            )
            
            # Call callbacks
            if self.on_backup_success:
                try:
                    self.on_backup_success(schedule.name, backup_name)
                except Exception as e:
                    logger.error(f"Error in success callback: {str(e)}")
            
            if self.on_cleanup_complete and deleted_count > 0:
                try:
                    self.on_cleanup_complete(schedule.name, deleted_count)
                except Exception as e:
                    logger.error(f"Error in cleanup callback: {str(e)}")
            
            return True
            
        except Exception as e:
            # Update failure stats
            stats["failed_runs"] += 1
            stats["last_failure"] = datetime.now().isoformat()
            
            logger.error(f"Scheduled backup failed for {schedule.name}: {str(e)}")
            
            # Call failure callback
            if self.on_backup_failure:
                try:
                    self.on_backup_failure(schedule.name, e)
                except Exception as cb_error:
                    logger.error(f"Error in failure callback: {str(cb_error)}")
            
            return False


# Convenience functions for common schedules

def create_daily_backup_schedule(name: str, hour: int = 2, minute: int = 0, 
                               retention_days: int = 30) -> BackupSchedule:
    """Create a daily backup schedule."""
    return BackupSchedule(
        name=name,
        schedule_type=ScheduleType.DAILY,
        hour=hour,
        minute=minute,
        retention_days=retention_days
    )


def create_weekly_backup_schedule(name: str, day_of_week: int = 6, hour: int = 2, 
                                minute: int = 0, retention_days: int = 90) -> BackupSchedule:
    """Create a weekly backup schedule (default: Sunday at 2 AM)."""
    return BackupSchedule(
        name=name,
        schedule_type=ScheduleType.WEEKLY,
        day_of_week=day_of_week,
        hour=hour,
        minute=minute,
        retention_days=retention_days
    )


def create_monthly_backup_schedule(name: str, day_of_month: int = 1, hour: int = 2,
                                 minute: int = 0, retention_days: int = 365) -> BackupSchedule:
    """Create a monthly backup schedule (default: 1st of month at 2 AM)."""
    return BackupSchedule(
        name=name,
        schedule_type=ScheduleType.MONTHLY,
        day_of_month=day_of_month,
        hour=hour,
        minute=minute,
        retention_days=retention_days
    ) 