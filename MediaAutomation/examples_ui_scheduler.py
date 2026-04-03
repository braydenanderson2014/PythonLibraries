"""
Examples of using the event system, scheduler, task manager, and UI.

Demonstrates:
1. Basic event system usage
2. Creating and managing schedules
3. Task manager workflows
4. Status tracking and reporting
5. Event subscriptions
"""

import time
import logging
from datetime import datetime
from event_system import initialize_event_system, EventType, get_status_tracker
from task_manager import TaskManager
from scheduler import TaskScheduler


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Example 1: Event System ====================

def example_1_basic_events():
    """Example 1: Using the event system."""
    print("\n" + "="*60)
    print("Example 1: Event System")
    print("="*60)
    
    # Initialize
    event_bus, status_tracker = initialize_event_system()
    
    # Subscribe to events
    def on_event(event):
        print(f"📢 Event: {event.event_type.value} from {event.source}")
        print(f"   Data: {event.data}")
    
    event_bus.subscribe(EventType.TASK_STARTED, on_event)
    event_bus.subscribe(EventType.TASK_COMPLETED, on_event)
    
    # Update task status (publish event automatically)
    status_tracker.update_task_status(
        task_id="task-001",
        task_name="Sample Task",
        status="running",
        progress=0.0,
        total_items=100
    )
    
    time.sleep(0.5)
    
    # Update progress
    status_tracker.update_task_status(
        task_id="task-001",
        task_name="Sample Task",
        status="running",
        progress=50.0,
        processed_items=50,
        total_items=100
    )
    
    time.sleep(0.5)
    
    # Complete task
    status_tracker.update_task_status(
        task_id="task-001",
        task_name="Sample Task",
        status="completed",
        progress=100.0,
        processed_items=100,
        total_items=100
    )


# ==================== Example 2: Task Scheduler ====================

def example_2_task_scheduler():
    """Example 2: Creating and managing schedules."""
    print("\n" + "="*60)
    print("Example 2: Task Scheduler")
    print("="*60)
    
    # Initialize
    event_bus, status_tracker = initialize_event_system()
    scheduler = TaskScheduler(event_bus=event_bus, status_tracker=status_tracker)
    
    # Counter for task execution
    execution_count = {"interval": 0, "cron": 0}
    
    def interval_task():
        execution_count["interval"] += 1
        logger.info(f"✓ Interval task executed (count: {execution_count['interval']})")
    
    def cron_task():
        execution_count["cron"] += 1
        logger.info(f"✓ Cron task executed (count: {execution_count['cron']})")
    
    # Create tasks
    print("\n1. Creating interval-based task (every 10 seconds)...")
    task_id_1 = scheduler.add_interval_task(
        task_name="Interval Task",
        task_function=interval_task,
        interval_value=10,
        interval_unit="seconds",
        description="Runs every 10 seconds"
    )
    print(f"   Created task: {task_id_1}")
    
    print("\n2. Creating cron-based task (every minute)...")
    task_id_2 = scheduler.add_cron_task(
        task_name="Cron Task",
        task_function=cron_task,
        cron_expression="*/1 * * * *",
        description="Runs every minute"
    )
    print(f"   Created task: {task_id_2}")
    
    # View tasks
    print("\n3. Viewing all scheduled tasks...")
    tasks = scheduler.get_all_tasks()
    for task_id, config in tasks.items():
        next_exec = scheduler.get_next_execution_time(task_id)
        print(f"   - {config.task_name}")
        print(f"     Type: {config.schedule_type.value}")
        print(f"     Enabled: {config.enabled}")
        print(f"     Next run: {next_exec}")
    
    # Start scheduler
    print("\n4. Starting scheduler...")
    scheduler.start()
    print("   (Will run for 15 seconds)")
    
    # Wait and observe
    time.sleep(15)
    
    # Check execution history
    print("\n5. Execution history:")
    for task_id, config in tasks.items():
        history = scheduler.get_execution_history(task_id=task_id, limit=5)
        print(f"   {config.task_name}:")
        for execution in history:
            print(f"     - {execution.status.upper()} "
                  f"({execution.execution_time_seconds:.2f}s) "
                  f"at {execution.start_time}")
    
    # Disable task
    print(f"\n6. Disabling task {task_id_1}...")
    scheduler.disable_task(task_id_1)
    
    # Stop scheduler
    print("\n7. Stopping scheduler...")
    scheduler.stop()


# ==================== Example 3: Task Manager ====================

def example_3_task_manager():
    """Example 3: Using the task manager."""
    print("\n" + "="*60)
    print("Example 3: Task Manager")
    print("="*60)
    
    # Initialize
    event_bus, status_tracker = initialize_event_system()
    task_manager = TaskManager(event_bus=event_bus, status_tracker=status_tracker)
    scheduler = task_manager.get_scheduler()
    
    # Task functions that task manager can execute
    def scan_files():
        logger.info("🔍 Scanning files...")
        status_tracker.update_task_status(
            task_id="scan-files",
            task_name="File Scan",
            status="running"
        )
        time.sleep(2)  # Simulate work
        status_tracker.update_task_status(
            task_id="scan-files",
            task_name="File Scan",
            status="completed"
        )
        logger.info("✓ File scan completed")
    
    def health_check():
        logger.info("🔍 Checking service health...")
        status_tracker.update_task_status(
            task_id="health-check",
            task_name="Health Check",
            status="running"
        )
        
        # Simulate checking services
        status_tracker.update_service_status(
            service_name="Prowlarr",
            service_type="indexer",
            is_online=True,
            response_time_ms=125
        )
        status_tracker.update_service_status(
            service_name="Radarr",
            service_type="download_manager",
            is_online=True,
            response_time_ms=98
        )
        
        time.sleep(1)
        status_tracker.update_task_status(
            task_id="health-check",
            task_name="Health Check",
            status="completed"
        )
        logger.info("✓ Health check completed")
    
    print("\n1. Starting task manager...")
    task_manager.start()
    
    print("\n2. Scheduling recurring health checks...")
    task_id = task_manager.schedule_service_health_check(
        interval_value=5,
        interval_unit="seconds"
    )
    logger.info(f"   Scheduled: {task_id}")
    
    print("\n3. Getting scheduler info...")
    print(f"   Is running: {scheduler.is_running()}")
    print(f"   Active tasks: {len(scheduler.get_all_tasks())}")
    
    print("\n4. Running health check manually...")
    task_manager.check_all_services_health()
    
    print("\n5. Waiting 10 seconds for scheduled tasks...")
    time.sleep(10)
    
    print("\n6. Checking system status...")
    status = status_tracker.get_system_status()
    services = status_tracker.get_all_service_statuses()
    stats = status_tracker.get_statistics()
    
    print(f"   System status: {status.value}")
    print(f"   Active services: {len(services)}")
    for service_name, service in services.items():
        print(f"     - {service.service_name}: {'Online' if service.is_online else 'Offline'}")
    
    print("\n7. Stopping task manager...")
    task_manager.stop()


# ==================== Example 4: Event Subscriptions ====================

def example_4_event_subscriptions():
    """Example 4: Advanced event subscriptions."""
    print("\n" + "="*60)
    print("Example 4: Event Subscriptions")
    print("="*60)
    
    # Initialize
    event_bus, status_tracker = initialize_event_system()
    
    # Task completion tracker
    completions = {"count": 0, "total_time": 0.0}
    
    def on_task_completed(event):
        completions["count"] += 1
        print(f"✓ Task completed: {event.data.get('task_name')}")
        print(f"  Total completions: {completions['count']}")
    
    def on_task_failed(event):
        error = event.data.get('error_message', 'Unknown error')
        print(f"✗ Task failed: {event.data.get('task_name')}")
        print(f"  Error: {error}")
    
    def on_stats_updated(event):
        print(f"📊 Statistics updated:")
        print(f"   Files scanned: {event.data.get('total_files_scanned')}")
        print(f"   Files distributed: {event.data.get('total_files_distributed')}")
    
    def on_service_online(event):
        print(f"🟢 {event.data.get('service_name')} is online "
              f"({event.data.get('response_time_ms')}ms)")
    
    def on_service_offline(event):
        print(f"🔴 {event.data.get('service_name')} is offline")
    
    # Subscribe
    print("\n1. Subscribing to events...")
    event_bus.subscribe(EventType.TASK_COMPLETED, on_task_completed)
    event_bus.subscribe(EventType.TASK_FAILED, on_task_failed)
    event_bus.subscribe(EventType.STATISTICS_UPDATED, on_stats_updated)
    event_bus.subscribe(EventType.SERVICE_ONLINE, on_service_online)
    event_bus.subscribe(EventType.SERVICE_OFFLINE, on_service_offline)
    print("   Subscribed to 5 event types")
    
    # Trigger events
    print("\n2. Triggering events...")
    
    # Task completed
    status_tracker.update_task_status(
        task_id="task-1",
        task_name="Test Task 1",
        status="completed"
    )
    
    # Service online
    status_tracker.update_service_status(
        service_name="Plex",
        service_type="media_server",
        is_online=True,
        response_time_ms=150
    )
    
    # Statistics update
    status_tracker.update_statistics(
        total_files_scanned=42,
        total_files_distributed=38
    )
    
    # Service offline
    status_tracker.update_service_status(
        service_name="Sonarr",
        service_type="download_manager",
        is_online=False,
        response_time_ms=0,
        error_message="Connection timeout"
    )
    
    print("\n3. Event history:")
    history = event_bus.get_history(limit=10)
    for event in history:
        print(f"   - {event.event_type.value} from {event.source}")


# ==================== Example 5: Integration Example ====================

def example_5_full_integration():
    """Example 5: Full integration of all components."""
    print("\n" + "="*60)
    print("Example 5: Full Integration")
    print("="*60)
    
    # Initialize all components
    event_bus, status_tracker = initialize_event_system()
    task_manager = TaskManager(event_bus=event_bus, status_tracker=status_tracker)
    scheduler = task_manager.get_scheduler()
    
    # Create a workflow
    execution_log = []
    
    def complete_workflow():
        """Simulated complete workflow."""
        timestamp = datetime.now().isoformat()
        start = time.time()
        
        # Step 1: Scan
        logger.info("📁 Workflow Step 1: Scanning files...")
        status_tracker.update_task_status("workflow", "Workflow", "running", 
                                         current_item="Scanning...")
        time.sleep(1)
        status_tracker.increment_statistic("total_files_scanned", 25)
        
        # Step 2: Distribute
        logger.info("📦 Workflow Step 2: Distributing files...")
        status_tracker.update_task_status("workflow", "Workflow", "running",
                                         progress=33, current_item="Distributing...")
        time.sleep(1)
        status_tracker.increment_statistic("total_files_distributed", 23)
        status_tracker.increment_statistic("total_distribution_size_gb", 5.2)
        
        # Step 3: Trigger media servers
        logger.info("📺 Workflow Step 3: Triggering media server scans...")
        status_tracker.update_task_status("workflow", "Workflow", "running",
                                         progress=66, current_item="Media scan...")
        time.sleep(1)
        
        # Complete
        status_tracker.update_task_status("workflow", "Workflow", "completed",
                                         progress=100)
        
        duration = time.time() - start
        execution_log.append({
            "timestamp": timestamp,
            "duration": duration,
            "status": "completed"
        })
        logger.info(f"✓ Workflow completed in {duration:.2f}s")
    
    print("\n1. Setting up workflow schedule...")
    
    # Schedule daily at 2 AM
    workflow_task_id = scheduler.add_cron_task(
        task_name="Daily Workflow",
        task_function=complete_workflow,
        cron_expression="0 2 * * *",
        description="Run complete workflow daily at 2 AM"
    )
    logger.info(f"   Scheduled: {workflow_task_id}")
    
    # Also schedule hourly health checks
    health_task_id = scheduler.add_interval_task(
        task_name="Health Check",
        task_function=lambda: task_manager.check_all_services_health(),
        interval_value=1,
        interval_unit="hours",
        description="Check service health every hour"
    )
    logger.info(f"   Scheduled: {health_task_id}")
    
    print("\n2. Starting task manager...")
    task_manager.start()
    
    print("\n3. Executing workflow manually...")
    complete_workflow()
    
    print("\n4. System status report:")
    print(f"   Total scheduled tasks: {len(scheduler.get_all_tasks())}")
    print(f"   Tasks in scheduler:")
    for task_id, config in scheduler.get_all_tasks().items():
        next_exec = scheduler.get_next_execution_time(task_id)
        print(f"     - {config.task_name} (next: {next_exec})")
    
    stats = status_tracker.get_statistics()
    print(f"\n   System Statistics:")
    print(f"     Files scanned: {stats.get('total_files_scanned', 0)}")
    print(f"     Files distributed: {stats.get('total_files_distributed', 0)}")
    print(f"     Total size: {stats.get('total_distribution_size_gb', 0):.2f} GB")
    
    print(f"\n   Execution Log:")
    for log_entry in execution_log:
        print(f"     {log_entry['timestamp']}: {log_entry['status']} "
              f"({log_entry['duration']:.2f}s)")
    
    print("\n5. Stopping task manager...")
    task_manager.stop()


# ==================== Main ====================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Media Automation System - Examples")
    print("="*60)
    
    # Run examples
    try:
        example_1_basic_events()
        example_2_task_scheduler()
        example_3_task_manager()
        example_4_event_subscriptions()
        example_5_full_integration()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
