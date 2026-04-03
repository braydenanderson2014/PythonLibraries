"""
Central event and status tracking system for media automation.

Provides:
- Global event bus for all components to publish/subscribe to events
- Status tracking for all tasks and services
- Real-time updates to UI components
- Thread-safe event handling
"""

import threading
import json
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Callable, Optional, Any
from collections import defaultdict
import logging


logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be published."""
    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_PROGRESS = "task_progress"
    
    # Service events
    SERVICE_HEALTH_CHECK = "service_health_check"
    SERVICE_ONLINE = "service_online"
    SERVICE_OFFLINE = "service_offline"
    
    # File events
    FILE_SCANNED = "file_scanned"
    FILE_DISTRIBUTED = "file_distributed"
    DISTRIBUTION_STARTED = "distribution_started"
    DISTRIBUTION_COMPLETED = "distribution_completed"
    
    # System events
    SYSTEM_STATUS_CHANGED = "system_status_changed"
    STATISTICS_UPDATED = "statistics_updated"
    ERROR_OCCURRED = "error_occurred"
    
    # Scheduler events
    TASK_SCHEDULED = "task_scheduled"
    TASK_RESCHEDULED = "task_rescheduled"
    TASK_CANCELLED = "task_cancelled"


class TaskStatus(Enum):
    """Status of a task."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class SystemStatus(Enum):
    """Overall system status."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING_TASKS = "running_tasks"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class Event:
    """Represents a single event in the system."""
    event_type: EventType
    timestamp: str
    source: str  # Component that generated the event
    data: Dict[str, Any]
    priority: int = 0  # Higher priority events processed first
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "data": self.data,
            "priority": self.priority
        }


@dataclass
class TaskStatus:
    """Tracks the status of a specific task."""
    task_id: str
    task_name: str
    status: str  # idle, running, completed, error
    progress: float = 0.0  # 0-100
    current_item: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    processed_items: int = 0
    total_items: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ServiceStatus:
    """Tracks the status of a service."""
    service_name: str
    service_type: str  # indexer, download_manager, media_server
    is_online: bool
    last_check: str
    response_time_ms: float
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class EventBus:
    """
    Central event bus for publishing and subscribing to system events.
    Thread-safe implementation with priority queue.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._lock = threading.RLock()
        self._max_history = 1000  # Keep last 1000 events
        
    def subscribe(self, event_type: EventType, callback: Callable) -> Callable:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event is published (receives Event object)
            
        Returns:
            The callback function (for chaining)
        """
        with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed {callback.__name__ if hasattr(callback, '__name__') else 'callback'} to {event_type.value}")
        return callback
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from an event type."""
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            # Get subscribers (sorted by priority)
            subscribers = self._subscribers.get(event.event_type, [])
            
        # Call subscribers outside of lock to avoid deadlocks
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}", exc_info=True)
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (None for all)
            limit: Maximum number of events to return
            
        Returns:
            List of events, most recent first
        """
        with self._lock:
            history = self._event_history[-limit:]
            
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        
        return list(reversed(history))
    
    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()


class StatusTracker:
    """
    Tracks the status of all tasks and services in the system.
    Provides a single source of truth for current system state.
    """
    
    def __init__(self, event_bus: EventBus):
        """Initialize the status tracker."""
        self.event_bus = event_bus
        self._tasks: Dict[str, TaskStatus] = {}
        self._services: Dict[str, ServiceStatus] = {}
        self._system_status = SystemStatus.INITIALIZING
        self._lock = threading.RLock()
        self._statistics = {
            "total_files_scanned": 0,
            "total_files_distributed": 0,
            "total_distribution_size_gb": 0.0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "uptime_seconds": 0,
        }
    
    def update_task_status(self, task_id: str, task_name: str, status: str, 
                          progress: float = 0.0, current_item: Optional[str] = None,
                          error_message: Optional[str] = None, processed_items: int = 0,
                          total_items: int = 0) -> None:
        """Update the status of a task."""
        with self._lock:
            old_status = self._tasks.get(task_id)
            
            now = datetime.now().isoformat()
            task = TaskStatus(
                task_id=task_id,
                task_name=task_name,
                status=status,
                progress=progress,
                current_item=current_item,
                error_message=error_message,
                processed_items=processed_items,
                total_items=total_items,
                start_time=old_status.start_time if old_status and old_status.start_time else now,
                end_time=now if status in ["completed", "error", "cancelled"] else None
            )
            
            self._tasks[task_id] = task
            
            # Publish event
            event_type = {
                "running": EventType.TASK_STARTED,
                "completed": EventType.TASK_COMPLETED,
                "error": EventType.TASK_FAILED,
            }.get(status, EventType.TASK_PROGRESS)
            
            event = Event(
                event_type=event_type,
                timestamp=now,
                source=task_name,
                data={
                    "task_id": task_id,
                    "task_name": task_name,
                    "status": status,
                    "progress": progress,
                    "current_item": current_item,
                    "error_message": error_message,
                    "processed_items": processed_items,
                    "total_items": total_items
                }
            )
            
            self.event_bus.publish(event)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the current status of a task."""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_task_statuses(self) -> Dict[str, TaskStatus]:
        """Get status of all tasks."""
        with self._lock:
            return dict(self._tasks)
    
    def update_service_status(self, service_name: str, service_type: str, is_online: bool,
                            response_time_ms: float, error_message: Optional[str] = None) -> None:
        """Update the status of a service."""
        with self._lock:
            now = datetime.now().isoformat()
            service = ServiceStatus(
                service_name=service_name,
                service_type=service_type,
                is_online=is_online,
                last_check=now,
                response_time_ms=response_time_ms,
                error_message=error_message
            )
            self._services[service_name] = service
            
            # Publish event
            event_type = EventType.SERVICE_ONLINE if is_online else EventType.SERVICE_OFFLINE
            event = Event(
                event_type=event_type,
                timestamp=now,
                source=service_name,
                data={
                    "service_name": service_name,
                    "service_type": service_type,
                    "is_online": is_online,
                    "response_time_ms": response_time_ms,
                    "error_message": error_message
                }
            )
            self.event_bus.publish(event)
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get the current status of a service."""
        with self._lock:
            return self._services.get(service_name)
    
    def get_all_service_statuses(self) -> Dict[str, ServiceStatus]:
        """Get status of all services."""
        with self._lock:
            return dict(self._services)
    
    def set_system_status(self, status: SystemStatus) -> None:
        """Update overall system status."""
        with self._lock:
            self._system_status = status
            
            event = Event(
                event_type=EventType.SYSTEM_STATUS_CHANGED,
                timestamp=datetime.now().isoformat(),
                source="system",
                data={"system_status": status.value}
            )
            self.event_bus.publish(event)
    
    def get_system_status(self) -> SystemStatus:
        """Get overall system status."""
        with self._lock:
            return self._system_status
    
    def update_statistics(self, **kwargs) -> None:
        """Update system statistics."""
        with self._lock:
            self._statistics.update(kwargs)
            
            event = Event(
                event_type=EventType.STATISTICS_UPDATED,
                timestamp=datetime.now().isoformat(),
                source="system",
                data=self._statistics.copy()
            )
            self.event_bus.publish(event)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current system statistics."""
        with self._lock:
            return self._statistics.copy()
    
    def increment_statistic(self, key: str, amount: float = 1.0) -> None:
        """Increment a statistic value."""
        with self._lock:
            if key in self._statistics:
                self._statistics[key] += amount
                self.update_statistics(**self._statistics)


# Global instances (singleton pattern)
_event_bus: Optional[EventBus] = None
_status_tracker: Optional[StatusTracker] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def get_status_tracker() -> StatusTracker:
    """Get the global status tracker instance."""
    global _status_tracker
    if _status_tracker is None:
        _status_tracker = StatusTracker(get_event_bus())
    return _status_tracker


def initialize_event_system() -> tuple[EventBus, StatusTracker]:
    """Initialize the event system and return both instances."""
    return get_event_bus(), get_status_tracker()
