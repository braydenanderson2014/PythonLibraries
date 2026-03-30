"""
Task scheduler for media automation with support for:
- Simple interval-based scheduling (every X minutes/hours)
- Cron-style scheduling (e.g., "0 */12 * * *")
- One-time scheduled tasks
- Task execution with automatic status tracking
"""

import threading
import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional, List, Any
from croniter import croniter
import uuid


logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of schedules supported."""
    INTERVAL = "interval"  # Simple interval (minutes, hours, days)
    CRON = "cron"  # Cron expression
    ONCE = "once"  # One-time execution


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled task."""
    task_id: str
    task_name: str
    task_function: Callable
    schedule_type: ScheduleType
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # For INTERVAL schedules
    interval_value: Optional[int] = None  # Value
    interval_unit: Optional[str] = None  # "minutes", "hours", "days"
    
    # For CRON schedules
    cron_expression: Optional[str] = None  # "0 */12 * * *"
    
    # For ONCE schedules
    scheduled_time: Optional[str] = None  # ISO format datetime
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "schedule_type": self.schedule_type.value,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "interval_value": self.interval_value,
            "interval_unit": self.interval_unit,
            "cron_expression": self.cron_expression,
            "scheduled_time": self.scheduled_time,
            "description": self.description,
            "tags": self.tags
        }


@dataclass
class TaskExecution:
    """Record of a task execution."""
    task_id: str
    task_name: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"  # running, completed, failed
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "error_message": self.error_message,
            "execution_time_seconds": self.execution_time_seconds
        }


class TaskScheduler:
    """
    Manages task scheduling and execution.
    
    Supports:
    - Simple intervals (every X minutes/hours/days)
    - Cron-style scheduling
    - One-time scheduled tasks
    - Task execution tracking
    - Graceful shutdown
    """
    
    def __init__(self, event_bus = None, status_tracker = None):
        """
        Initialize the scheduler.
        
        Args:
            event_bus: Optional EventBus for publishing events
            status_tracker: Optional StatusTracker for tracking task status
        """
        self.event_bus = event_bus
        self.status_tracker = status_tracker
        
        self._schedules: Dict[str, ScheduleConfig] = {}
        self._next_execution_times: Dict[str, datetime] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._last_executions: Dict[str, TaskExecution] = {}
        self._execution_history: List[TaskExecution] = []
        self._max_history = 500
    
    def add_interval_task(self, task_name: str, task_function: Callable,
                         interval_value: int, interval_unit: str = "minutes",
                         description: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
        """
        Add a task that runs at regular intervals.
        
        Args:
            task_name: Human-readable name for the task
            task_function: Function to call (should accept no arguments)
            interval_value: How many units between executions
            interval_unit: "minutes", "hours", or "days"
            description: Task description
            tags: Optional list of tags for organization
            
        Returns:
            task_id: Unique identifier for the task
        """
        task_id = str(uuid.uuid4())
        
        config = ScheduleConfig(
            task_id=task_id,
            task_name=task_name,
            task_function=task_function,
            schedule_type=ScheduleType.INTERVAL,
            interval_value=interval_value,
            interval_unit=interval_unit,
            description=description,
            tags=tags or []
        )
        
        with self._lock:
            self._schedules[task_id] = config
            self._calculate_next_execution(task_id)
        
        logger.info(f"Added interval task '{task_name}' (ID: {task_id}): every {interval_value} {interval_unit}")
        
        if self.event_bus:
            event = self._create_event("TASK_SCHEDULED", task_id, config)
            self.event_bus.publish(event)
        
        return task_id
    
    def add_cron_task(self, task_name: str, task_function: Callable,
                     cron_expression: str, description: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> str:
        """
        Add a task that runs on a cron schedule.
        
        Args:
            task_name: Human-readable name for the task
            task_function: Function to call (should accept no arguments)
            cron_expression: Cron expression (e.g., "0 */12 * * *" for twice daily)
                Examples:
                - "*/5 * * * *" - Every 5 minutes
                - "0 * * * *" - Every hour
                - "0 0 * * *" - Daily at midnight
                - "0 0 * * MON" - Weekly on Monday at midnight
                - "0 2 * * MON-FRI" - 2 AM on weekdays
            description: Task description
            tags: Optional list of tags for organization
            
        Returns:
            task_id: Unique identifier for the task
            
        Raises:
            ValueError: If cron expression is invalid
        """
        # Validate cron expression
        try:
            croniter(cron_expression)
        except ValueError as e:
            logger.error(f"Invalid cron expression: {cron_expression}")
            raise ValueError(f"Invalid cron expression: {e}")
        
        task_id = str(uuid.uuid4())
        
        config = ScheduleConfig(
            task_id=task_id,
            task_name=task_name,
            task_function=task_function,
            schedule_type=ScheduleType.CRON,
            cron_expression=cron_expression,
            description=description,
            tags=tags or []
        )
        
        with self._lock:
            self._schedules[task_id] = config
            self._calculate_next_execution(task_id)
        
        logger.info(f"Added cron task '{task_name}' (ID: {task_id}): {cron_expression}")
        
        if self.event_bus:
            event = self._create_event("TASK_SCHEDULED", task_id, config)
            self.event_bus.publish(event)
        
        return task_id
    
    def add_once_task(self, task_name: str, task_function: Callable,
                     scheduled_time: str, description: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> str:
        """
        Add a one-time task scheduled for a specific time.
        
        Args:
            task_name: Human-readable name for the task
            task_function: Function to call (should accept no arguments)
            scheduled_time: ISO format datetime string (e.g., "2026-03-29T15:30:00")
            description: Task description
            tags: Optional list of tags for organization
            
        Returns:
            task_id: Unique identifier for the task
        """
        task_id = str(uuid.uuid4())
        
        config = ScheduleConfig(
            task_id=task_id,
            task_name=task_name,
            task_function=task_function,
            schedule_type=ScheduleType.ONCE,
            scheduled_time=scheduled_time,
            description=description,
            tags=tags or []
        )
        
        with self._lock:
            self._schedules[task_id] = config
            self._next_execution_times[task_id] = datetime.fromisoformat(scheduled_time)
        
        logger.info(f"Added one-time task '{task_name}' (ID: {task_id}): {scheduled_time}")
        
        if self.event_bus:
            event = self._create_event("TASK_SCHEDULED", task_id, config)
            self.event_bus.publish(event)
        
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        with self._lock:
            if task_id in self._schedules:
                config = self._schedules.pop(task_id)
                if task_id in self._next_execution_times:
                    del self._next_execution_times[task_id]
                logger.info(f"Removed task '{config.task_name}' (ID: {task_id})")
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduleConfig]:
        """Get a task configuration."""
        with self._lock:
            return self._schedules.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, ScheduleConfig]:
        """Get all scheduled tasks."""
        with self._lock:
            return dict(self._schedules)
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task."""
        with self._lock:
            if task_id in self._schedules:
                self._schedules[task_id].enabled = True
                logger.info(f"Enabled task '{self._schedules[task_id].task_name}'")
                return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task."""
        with self._lock:
            if task_id in self._schedules:
                self._schedules[task_id].enabled = False
                logger.info(f"Disabled task '{self._schedules[task_id].task_name}'")
                return True
        return False
    
    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Scheduler started")
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop the scheduler gracefully."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("Scheduler stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running and self._thread and self._thread.is_alive()
    
    def _run(self) -> None:
        """Main scheduler loop (runs in background thread)."""
        logger.info("Scheduler loop starting")
        
        while self._running:
            now = datetime.now()
            
            with self._lock:
                tasks_to_execute = []
                for task_id, config in self._schedules.items():
                    if not config.enabled:
                        continue
                    
                    next_exec_time = self._next_execution_times.get(task_id)
                    if next_exec_time and now >= next_exec_time:
                        tasks_to_execute.append((task_id, config))
            
            # Execute tasks outside of lock
            for task_id, config in tasks_to_execute:
                self._execute_task(task_id, config)
            
            # Sleep a bit to avoid busy waiting
            time.sleep(1)
    
    def _execute_task(self, task_id: str, config: ScheduleConfig) -> None:
        """Execute a scheduled task."""
        start_time = datetime.now()
        execution = TaskExecution(
            task_id=task_id,
            task_name=config.task_name,
            start_time=start_time.isoformat()
        )
        
        try:
            logger.info(f"Executing scheduled task: {config.task_name}")
            
            # Update status if tracker available
            if self.status_tracker:
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name=config.task_name,
                    status="running"
                )
            
            # Execute the function
            config.task_function()
            
            # Success
            execution.status = "completed"
            
            # Update status
            if self.status_tracker:
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name=config.task_name,
                    status="completed"
                )
            
            logger.info(f"Task completed: {config.task_name}")
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            logger.error(f"Task failed: {config.task_name}: {e}", exc_info=True)
            
            # Update status
            if self.status_tracker:
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name=config.task_name,
                    status="error",
                    error_message=str(e)
                )
        
        finally:
            # Record execution
            execution.end_time = datetime.now().isoformat()
            execution.execution_time_seconds = (datetime.fromisoformat(execution.end_time) -
                                               datetime.fromisoformat(execution.start_time)).total_seconds()
            
            with self._lock:
                self._last_executions[task_id] = execution
                self._execution_history.append(execution)
                if len(self._execution_history) > self._max_history:
                    self._execution_history.pop(0)
                
                # Schedule next execution
                self._calculate_next_execution(task_id)
            
            # Publish event
            if self.event_bus:
                event_type = "TASK_COMPLETED" if execution.status == "completed" else "TASK_FAILED"
                event = self._create_execution_event(event_type, execution)
                self.event_bus.publish(event)
    
    def _calculate_next_execution(self, task_id: str) -> None:
        """Calculate when a task should next execute."""
        with self._lock:
            config = self._schedules.get(task_id)
            if not config:
                return
            
            now = datetime.now()
            
            if config.schedule_type == ScheduleType.INTERVAL:
                # Calculate interval in seconds
                multipliers = {
                    "minutes": 60,
                    "hours": 3600,
                    "days": 86400
                }
                interval_seconds = config.interval_value * multipliers.get(config.interval_unit, 60)
                self._next_execution_times[task_id] = now + timedelta(seconds=interval_seconds)
            
            elif config.schedule_type == ScheduleType.CRON:
                # Use croniter to calculate next execution
                cron = croniter(config.cron_expression, now)
                self._next_execution_times[task_id] = cron.get_next(datetime)
            
            elif config.schedule_type == ScheduleType.ONCE:
                # One-time tasks don't need rescheduling
                pass
    
    def get_next_execution_time(self, task_id: str) -> Optional[datetime]:
        """Get when a task will next execute."""
        with self._lock:
            return self._next_execution_times.get(task_id)
    
    def get_last_execution(self, task_id: str) -> Optional[TaskExecution]:
        """Get the last execution record for a task."""
        with self._lock:
            return self._last_executions.get(task_id)
    
    def get_execution_history(self, task_id: Optional[str] = None, limit: int = 100) -> List[TaskExecution]:
        """Get execution history."""
        with self._lock:
            history = list(self._execution_history[-limit:])
        
        if task_id:
            history = [e for e in history if e.task_id == task_id]
        
        return list(reversed(history))
    
    def _create_event(self, event_type: str, task_id: str, config: ScheduleConfig):
        """Create an event for the event bus."""
        from event_system import Event, EventType
        
        # Map string event types to EventType enum
        event_type_map = {
            "TASK_SCHEDULED": EventType.TASK_SCHEDULED,
        }
        
        return Event(
            event_type=event_type_map.get(event_type, EventType.TASK_SCHEDULED),
            timestamp=datetime.now().isoformat(),
            source="scheduler",
            data=config.to_dict()
        )
    
    def _create_execution_event(self, event_type: str, execution: TaskExecution):
        """Create an execution event for the event bus."""
        from event_system import Event, EventType
        
        # Map string event types to EventType enum
        event_type_map = {
            "TASK_COMPLETED": EventType.TASK_COMPLETED,
            "TASK_FAILED": EventType.TASK_FAILED,
        }
        
        return Event(
            event_type=event_type_map.get(event_type, EventType.TASK_COMPLETED),
            timestamp=datetime.now().isoformat(),
            source="scheduler",
            data=execution.to_dict()
        )
