"""
Central task manager for media automation.

Coordinates:
- Manual task execution
- Scheduled task management
- Status tracking and reporting
- Integration with all subsystems (scanning, distribution, services)
"""

import threading
import logging
import os
import subprocess
import json
from datetime import datetime
from typing import Dict, Callable, Optional, List, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path

from event_system import EventBus, StatusTracker, EventType, Event, get_event_bus, get_status_tracker
from scheduler import TaskScheduler
from media_automation.node_flow import (
    NodeFlowExecutor,
    get_default_behavior_trees,
    get_node_library,
    normalize_tree_nodes,
)


logger = logging.getLogger(__name__)


@dataclass
class DownloadJob:
    """Represents a single download request tracked by the system."""

    job_id: str
    query: str
    content_type: str
    preferred_manager: Optional[str] = None
    status: str = "queued"
    selected_manager: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    attempts: int = 0
    message: str = ""
    search_results_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FollowupAction:
    """Represents a queued/scheduled next-step action for a job."""

    action_id: str
    job_id: str
    action_type: str  # encode | subtitle | workflow
    schedule_mode: str  # now | once | cron | interval
    status: str = "scheduled"
    input_path: str = ""
    output_path: str = ""
    preset_or_profile: str = ""
    cron_expression: Optional[str] = None
    interval_value: Optional[int] = None
    interval_unit: Optional[str] = None
    scheduled_time: Optional[str] = None
    scheduler_task_id: Optional[str] = None
    workflow_options: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaskManager:
    """
    Central manager for all system tasks.
    
    Handles:
    - Coordinating manual and scheduled tasks
    - Tracking task status
    - Managing service health checks
    - Triggering workflows
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None,
                 status_tracker: Optional[StatusTracker] = None,
                 adapters_factory=None,
                 config: Optional[Dict[str, Any]] = None,
                 config_path: str = "config.json"):
        """
        Initialize the task manager.
        
        Args:
            event_bus: Optional EventBus for publishing events
            status_tracker: Optional StatusTracker for tracking status
            adapters_factory: Optional factory for adapter access
            config: Optional application config for adapter-specific defaults
            config_path: Config path for persisting custom workflow trees/settings
        """
        self.event_bus = event_bus or get_event_bus()
        self.status_tracker = status_tracker or get_status_tracker()
        self.adapters_factory = adapters_factory
        self.config = config or {}
        self.config_path = config_path
        
        self.scheduler = TaskScheduler(event_bus=self.event_bus, status_tracker=self.status_tracker)
        
        self._running_tasks: Dict[str, threading.Thread] = {}
        self._task_results: Dict[str, Any] = {}
        self._download_jobs: Dict[str, DownloadJob] = {}
        self._followup_actions: Dict[str, FollowupAction] = {}
        self._custom_behavior_trees: Dict[str, List[Dict[str, Any]]] = {}
        self._workflow_defaults: Dict[str, Any] = {
            "size_threshold_gb": 10.0,
        }
        self._lock = threading.RLock()

        self._load_workflow_config_from_memory()
        
        logger.info("Task manager initialized")

    def _load_workflow_config_from_memory(self) -> None:
        """Load custom trees/defaults from in-memory config dict."""
        workflow_cfg = self.config.get("workflow", {}) if isinstance(self.config, dict) else {}
        custom = workflow_cfg.get("custom_behavior_trees", {})
        defaults = workflow_cfg.get("defaults", {})

        if isinstance(custom, dict):
            normalized_trees: Dict[str, List[Dict[str, Any]]] = {}
            for name, nodes in custom.items():
                if not isinstance(nodes, list):
                    continue
                normalized = normalize_tree_nodes(nodes)
                if normalized:
                    normalized_trees[str(name)] = normalized
            self._custom_behavior_trees = normalized_trees

        if isinstance(defaults, dict):
            threshold = defaults.get("size_threshold_gb")
            if threshold is not None:
                try:
                    self._workflow_defaults["size_threshold_gb"] = float(threshold)
                except Exception:
                    pass

    def _persist_workflow_config(self) -> None:
        """Persist workflow trees/defaults to config file so they survive restarts."""
        if not self.config_path:
            return

        with self._lock:
            cfg = dict(self.config)
            workflow_cfg = dict(cfg.get("workflow", {}))
            workflow_cfg["custom_behavior_trees"] = {
                name: normalize_tree_nodes(nodes) for name, nodes in self._custom_behavior_trees.items()
            }
            workflow_cfg["defaults"] = {
                "size_threshold_gb": float(self._workflow_defaults.get("size_threshold_gb", 10.0))
            }
            cfg["workflow"] = workflow_cfg
            self.config = cfg

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            logger.warning("Could not persist workflow configuration to %s: %s", self.config_path, e)

    # ==================== Download Discovery/Jobs ====================

    def search_download_sources(self, query: str, content_type: str = "movie") -> Dict[str, Any]:
        """
        Search available tools for a title before creating a download job.

        Returns a normalized response so the UI can render a mixed-source result list.
        """
        response = {
            "success": True,
            "query": query,
            "content_type": content_type,
            "sources": [],
            "errors": [],
        }

        if not query.strip():
            response["success"] = False
            response["errors"].append("Query is empty")
            return response

        if not self.adapters_factory:
            response["success"] = False
            response["errors"].append("No adapters factory configured")
            return response

        # Search with Prowlarr if available.
        if hasattr(self.adapters_factory, "indexers") and "prowlarr" in self.adapters_factory.indexers:
            try:
                indexer = self.adapters_factory.indexers["prowlarr"]
                category_map = {
                    "movie": [2000],
                    "show": [5000],
                    "music": [3000],
                    "book": [7000],
                }
                raw = indexer.search(query, categories=category_map.get(content_type))
                results = raw.get("results", []) if isinstance(raw, dict) else []

                normalized = []
                for item in results[:25]:
                    normalized.append(
                        {
                            "source": "prowlarr",
                            "title": item.get("title", "(no title)"),
                            "size": item.get("size", 0),
                            "seeders": item.get("seeders", 0),
                            "magnet_url": item.get("magnetUrl") or item.get("downloadUrl"),
                        }
                    )

                response["sources"].extend(normalized)
            except Exception as e:
                response["errors"].append(f"Prowlarr search failed: {e}")

        # Include active download managers as additional "available tools" metadata.
        manager_names = self._resolve_download_managers(content_type, preferred_manager=None)
        for manager_name in manager_names:
            response["sources"].append(
                {
                    "source": manager_name,
                    "title": f"{manager_name} available for submission",
                    "size": 0,
                    "seeders": 0,
                    "magnet_url": None,
                }
            )

        if not response["sources"] and response["errors"]:
            response["success"] = False

        return response

    def create_download_job(
        self,
        query: str,
        content_type: str = "movie",
        preferred_manager: Optional[str] = None,
    ) -> str:
        """Create a tracked download job and start it asynchronously."""
        job_id = self._generate_task_id()
        job = DownloadJob(
            job_id=job_id,
            query=query.strip(),
            content_type=content_type,
            preferred_manager=preferred_manager,
            status="queued",
            message="Job created",
        )

        with self._lock:
            self._download_jobs[job_id] = job

        self.status_tracker.update_task_status(
            task_id=job_id,
            task_name=f"Download Job: {job.query}",
            status="running",
            current_item="Queued",
        )

        self._execute_task_async(job_id, f"Download Job: {job.query}", lambda: self._run_download_job(job_id))
        return job_id

    def get_download_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all tracked download jobs as serializable dicts."""
        with self._lock:
            return {job_id: job.to_dict() for job_id, job in self._download_jobs.items()}

    def get_download_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get one tracked download job by ID."""
        with self._lock:
            job = self._download_jobs.get(job_id)
            return job.to_dict() if job else None

    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Return all known jobs for the Jobs tab (currently tracked download jobs)."""
        return self.get_download_jobs()

    def get_followup_actions(self) -> Dict[str, Dict[str, Any]]:
        """Get all follow-up actions for UI listing."""
        with self._lock:
            return {action_id: action.to_dict() for action_id, action in self._followup_actions.items()}

    def get_available_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Return all available workflow blocks/nodes."""
        return get_node_library()

    def get_behavior_trees(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return merged built-in + custom behavior trees."""
        trees = get_default_behavior_trees()
        with self._lock:
            trees.update({name: normalize_tree_nodes(nodes) for name, nodes in self._custom_behavior_trees.items()})
        return trees

    def get_custom_behavior_trees(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return custom behavior trees only."""
        with self._lock:
            return {name: normalize_tree_nodes(nodes) for name, nodes in self._custom_behavior_trees.items()}

    def get_workflow_defaults(self) -> Dict[str, Any]:
        """Return persisted workflow defaults."""
        with self._lock:
            return dict(self._workflow_defaults)

    def update_workflow_defaults(self, *, size_threshold_gb: Optional[float] = None) -> None:
        """Update persisted workflow defaults."""
        with self._lock:
            if size_threshold_gb is not None:
                self._workflow_defaults["size_threshold_gb"] = float(size_threshold_gb)
        self._persist_workflow_config()

    def add_custom_behavior_tree(self, tree_name: str, node_ids: List[Any]) -> None:
        """Save a user-defined behavior tree made from available node IDs + params.

        Accepts both flat lists (legacy) and flat-with-branches lists produced
        by the Node-RED canvas (split/merge graph format).
        """
        clean_name = (tree_name or "").strip()
        if not clean_name:
            raise ValueError("Tree name is required")

        library = get_node_library()
        normalized = normalize_tree_nodes(node_ids)
        if not normalized:
            raise ValueError("At least one node is required")

        invalid = self._collect_invalid_node_ids(normalized, library)
        if invalid:
            raise ValueError(f"Unknown node ids: {', '.join(invalid)}")

        with self._lock:
            self._custom_behavior_trees[clean_name] = normalized
        self._persist_workflow_config()

    @staticmethod
    def _collect_invalid_node_ids(nodes: List[Any], library: dict) -> List[str]:
        """Recursively collect node_ids that aren't in the library.
        split and merge are virtual control nodes and are always valid.
        """
        invalid: List[str] = []
        virtual = {"split", "merge"}
        for n in nodes:
            if not isinstance(n, dict):
                continue
            nid  = n.get("node_id", "")
            kind = n.get("node_kind", "normal")
            if kind in ("split", "merge") or nid in virtual:
                # recurse into branch children
                branches = n.get("branches", {})
                if isinstance(branches, dict):
                    for branch_nodes in branches.values():
                        invalid.extend(
                            TaskManager._collect_invalid_node_ids(branch_nodes, library)
                        )
                continue
            if nid not in library:
                invalid.append(nid)
        return invalid

    def delete_custom_behavior_tree(self, tree_name: str) -> None:
        """Delete a saved custom behavior tree."""
        with self._lock:
            if tree_name in self._custom_behavior_trees:
                del self._custom_behavior_trees[tree_name]
        self._persist_workflow_config()

    def schedule_followup_action(
        self,
        job_id: str,
        action_type: str,
        schedule_mode: str,
        input_path: str,
        output_path: str,
        preset_or_profile: str = "",
        scheduled_time: Optional[str] = None,
        cron_expression: Optional[str] = None,
        interval_value: Optional[int] = None,
        interval_unit: Optional[str] = None,
        workflow_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create and schedule a next-step action for a selected job."""
        if job_id not in self._download_jobs:
            raise ValueError(f"Unknown job id: {job_id}")
        if action_type not in {"encode", "subtitle", "workflow"}:
            raise ValueError("action_type must be 'encode', 'subtitle', or 'workflow'")
        if schedule_mode not in {"now", "once", "cron", "interval"}:
            raise ValueError("schedule_mode must be one of: now, once, cron, interval")
        if not input_path or not output_path:
            raise ValueError("input_path and output_path are required")

        action_id = self._generate_task_id()
        action = FollowupAction(
            action_id=action_id,
            job_id=job_id,
            action_type=action_type,
            schedule_mode=schedule_mode,
            input_path=input_path,
            output_path=output_path,
            preset_or_profile=preset_or_profile,
            scheduled_time=scheduled_time,
            cron_expression=cron_expression,
            interval_value=interval_value,
            interval_unit=interval_unit,
            workflow_options=workflow_options or {},
            message="Action scheduled",
        )

        with self._lock:
            self._followup_actions[action_id] = action

        if schedule_mode == "now":
            self._execute_task_async(
                action_id,
                f"Job Follow-up: {action_type}",
                lambda: self._run_followup_action(action_id),
            )
            return action_id

        def _run_later():
            self._run_followup_action(action_id)

        if schedule_mode == "once":
            if not scheduled_time:
                raise ValueError("scheduled_time is required for once mode")
            scheduler_task_id = self.scheduler.add_once_task(
                task_name=f"Follow-up {action_type} ({job_id[:8]})",
                task_function=_run_later,
                scheduled_time=scheduled_time,
                description=f"Run {action_type} follow-up for job {job_id}",
            )
        elif schedule_mode == "cron":
            if not cron_expression:
                raise ValueError("cron_expression is required for cron mode")
            scheduler_task_id = self.scheduler.add_cron_task(
                task_name=f"Follow-up {action_type} ({job_id[:8]})",
                task_function=_run_later,
                cron_expression=cron_expression,
                description=f"Run {action_type} follow-up for job {job_id}",
            )
        else:
            if not interval_value or not interval_unit:
                raise ValueError("interval_value and interval_unit are required for interval mode")
            scheduler_task_id = self.scheduler.add_interval_task(
                task_name=f"Follow-up {action_type} ({job_id[:8]})",
                task_function=_run_later,
                interval_value=interval_value,
                interval_unit=interval_unit,
                description=f"Run {action_type} follow-up for job {job_id}",
            )

        self._update_followup_action(action_id, scheduler_task_id=scheduler_task_id, message="Scheduled in task scheduler")
        return action_id

    def _update_followup_action(self, action_id: str, **kwargs) -> None:
        """Update fields on a follow-up action in a thread-safe way."""
        with self._lock:
            action = self._followup_actions.get(action_id)
            if not action:
                return
            for key, value in kwargs.items():
                if hasattr(action, key):
                    setattr(action, key, value)
            action.updated_at = datetime.now().isoformat()

    def _run_followup_action(self, action_id: str) -> None:
        """Execute follow-up action using configured executables."""
        with self._lock:
            action = self._followup_actions.get(action_id)
        if not action:
            return

        task_name = f"Follow-up {action.action_type}: {action.job_id[:8]}"
        self._update_followup_action(action_id, status="running", message="Starting action")
        self.status_tracker.update_task_status(
            task_id=action_id,
            task_name=task_name,
            status="running",
            current_item=f"{action.input_path} -> {action.output_path}",
        )

        try:
            if action.action_type == "encode":
                self._run_encode_action(action)
            elif action.action_type == "subtitle":
                self._run_subtitle_action(action)
            else:
                self._run_workflow_action(action)

            self._update_followup_action(action_id, status="completed", message="Action completed successfully")
            self.status_tracker.update_task_status(
                task_id=action_id,
                task_name=task_name,
                status="completed",
                current_item=f"Output: {action.output_path}",
            )
            self.status_tracker.increment_statistic("total_tasks_completed", 1)
        except Exception as e:
            logger.error("Follow-up action failed (%s): %s", action_id, e, exc_info=True)
            self._update_followup_action(action_id, status="failed", message=str(e))
            self.status_tracker.update_task_status(
                task_id=action_id,
                task_name=task_name,
                status="error",
                error_message=str(e),
            )
            self.status_tracker.increment_statistic("total_tasks_failed", 1)

    def _run_encode_action(self, action: FollowupAction) -> None:
        """Execute HandBrake encode step for a selected job."""
        executables = self.config.get("executables", {}) if isinstance(self.config, dict) else {}
        handbrake_exe = executables.get("handbrake") or "HandBrakeCLI"
        preset = action.preset_or_profile or self.config.get("defaults", {}).get("handbrake_preset", "Fast 1080p30")

        command = [
            handbrake_exe,
            "-i",
            action.input_path,
            "-o",
            action.output_path,
            "--preset",
            preset,
        ]
        self._run_subprocess_command(command)

    def _run_subtitle_action(self, action: FollowupAction) -> None:
        """Execute subtitle processing step for a selected job."""
        executables = self.config.get("executables", {}) if isinstance(self.config, dict) else {}
        subtitle_exe = executables.get("subtitle_tool") or "python"
        profile = action.preset_or_profile or self.config.get("defaults", {}).get("subtitle_profile", "default")

        if os.path.basename(subtitle_exe).lower().startswith("python"):
            command = [
                subtitle_exe,
                "Subtitle/main.py",
                "--input",
                action.input_path,
                "--output",
                action.output_path,
                "--profile",
                profile,
            ]
        else:
            command = [
                subtitle_exe,
                "--input",
                action.input_path,
                "--output",
                action.output_path,
                "--profile",
                profile,
            ]

        self._run_subprocess_command(command)

    def _run_workflow_action(self, action: FollowupAction) -> None:
        """Execute the default node-based workflow for a selected job."""
        job = self.get_download_job(action.job_id)
        if not job:
            raise RuntimeError(f"Unknown job id in workflow action: {action.job_id}")

        default_threshold = float(self._workflow_defaults.get("size_threshold_gb", 10.0))
        threshold_gb = float(action.workflow_options.get("size_threshold_gb", default_threshold))

        executor = NodeFlowExecutor(
            config=self.config,
            run_encode=self._run_encode_file,
            run_subtitle=self._run_subtitle_file,
            retry_download=self.retry_download_job,
        )
        tree_name = str(action.workflow_options.get("tree_name", "default_media_flow"))
        custom_trees = self.get_custom_behavior_trees()
        result = executor.execute_named_tree(
            tree_name=tree_name,
            custom_trees=custom_trees,
            job_id=action.job_id,
            query=job.get("query", ""),
            input_path=action.input_path,
            output_path=action.output_path,
            threshold_gb=threshold_gb,
        )

        if not result.get("success", False):
            raise RuntimeError(result.get("message", "Workflow execution failed"))

    def retry_download_job(self, job_id: str) -> str:
        """Create a new download job using the same query and type as an earlier job."""
        job = self.get_download_job(job_id)
        if not job:
            raise ValueError(f"Cannot retry unknown job id: {job_id}")

        new_job_id = self.create_download_job(
            query=job.get("query", ""),
            content_type=job.get("content_type", "movie"),
            preferred_manager=job.get("preferred_manager"),
        )

        self._update_download_job(job_id, message=f"Retry created: {new_job_id}")
        return new_job_id

    def _run_encode_file(self, input_path: Path, output_path: Path, preset: str) -> None:
        """Encode helper for workflow engine."""
        executables = self.config.get("executables", {}) if isinstance(self.config, dict) else {}
        handbrake_exe = executables.get("handbrake") or "HandBrakeCLI"
        command = [
            handbrake_exe,
            "-i",
            str(input_path),
            "-o",
            str(output_path),
            "--preset",
            preset,
        ]
        self._run_subprocess_command(command)

    def _run_subtitle_file(self, input_path: Path, output_path: Path, profile: str) -> None:
        """Subtitle helper for workflow engine."""
        executables = self.config.get("executables", {}) if isinstance(self.config, dict) else {}
        subtitle_exe = executables.get("subtitle_tool") or "python"

        if os.path.basename(subtitle_exe).lower().startswith("python"):
            command = [
                subtitle_exe,
                "Subtitle/main.py",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--profile",
                profile,
            ]
        else:
            command = [
                subtitle_exe,
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--profile",
                profile,
            ]
        self._run_subprocess_command(command)

    @staticmethod
    def _run_subprocess_command(command: List[str]) -> None:
        """Run a command and raise if execution fails."""
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            detail = stderr or stdout or f"Exit code {completed.returncode}"
            raise RuntimeError(f"Command failed: {' '.join(command)} :: {detail}")

    def get_available_download_managers(self, content_type: str = "movie") -> List[str]:
        """Return enabled manager names in priority order for a content type."""
        return self._resolve_download_managers(content_type, preferred_manager=None)

    def _run_download_job(self, job_id: str) -> None:
        """Worker that executes a queued download job against available managers."""
        with self._lock:
            job = self._download_jobs.get(job_id)
        if not job:
            return

        if not self.adapters_factory or not hasattr(self.adapters_factory, "download_managers"):
            self._update_download_job(job_id, status="failed", message="No download manager adapters configured")
            self.status_tracker.update_task_status(
                task_id=job_id,
                task_name=f"Download Job: {job.query}",
                status="error",
                error_message="No download manager adapters configured",
            )
            return

        # Optional discovery pass so the UI can display "searching" lifecycle.
        self._update_download_job(job_id, status="searching", message="Searching sources")
        search_result = self.search_download_sources(job.query, job.content_type)
        source_count = len(search_result.get("sources", []))
        self._update_download_job(
            job_id,
            status="searching",
            search_results_count=source_count,
            message=f"Found {source_count} source entries",
        )

        managers = self._resolve_download_managers(job.content_type, job.preferred_manager)
        if not managers:
            self._update_download_job(job_id, status="failed", message="No compatible managers configured")
            self.status_tracker.update_task_status(
                task_id=job_id,
                task_name=f"Download Job: {job.query}",
                status="error",
                error_message="No compatible managers configured",
            )
            return

        for manager_name in managers:
            adapter = self.adapters_factory.download_managers.get(manager_name)
            if not adapter:
                continue

            options = self._build_download_options(manager_name, job.content_type)
            self._update_download_job(
                job_id,
                status="submitting",
                selected_manager=manager_name,
                attempts=job.attempts + 1,
                message=f"Submitting via {manager_name}",
            )

            try:
                ok = adapter.search_and_download(job.query, **options)
            except Exception as e:
                ok = False
                logger.warning("Download submission failed for %s via %s: %s", job.query, manager_name, e)

            with self._lock:
                job = self._download_jobs.get(job_id)
                if not job:
                    return

            if ok:
                self._update_download_job(
                    job_id,
                    status="completed",
                    selected_manager=manager_name,
                    message=f"Submitted successfully via {manager_name}",
                )
                self.status_tracker.update_task_status(
                    task_id=job_id,
                    task_name=f"Download Job: {job.query}",
                    status="completed",
                    current_item=f"Manager: {manager_name}",
                )
                self.status_tracker.increment_statistic("total_tasks_completed", 1)
                return

        # All attempts failed.
        self._update_download_job(
            job_id,
            status="failed",
            message="No manager could submit this query",
        )
        self.status_tracker.update_task_status(
            task_id=job_id,
            task_name=f"Download Job: {job.query}",
            status="error",
            error_message="No manager could submit this query",
        )
        self.status_tracker.increment_statistic("total_tasks_failed", 1)

    def _update_download_job(self, job_id: str, **kwargs) -> None:
        """Update fields on a download job in a thread-safe way."""
        with self._lock:
            job = self._download_jobs.get(job_id)
            if not job:
                return
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = datetime.now().isoformat()

    def _resolve_download_managers(self, content_type: str, preferred_manager: Optional[str]) -> List[str]:
        """Pick manager order by content type, then include configured fallbacks."""
        if not self.adapters_factory or not hasattr(self.adapters_factory, "download_managers"):
            return []

        available = list(self.adapters_factory.download_managers.keys())
        if preferred_manager and preferred_manager in available:
            return [preferred_manager] + [m for m in available if m != preferred_manager]

        by_type = {
            "movie": ["radarr", "qbittorrent"],
            "show": ["sonarr", "qbittorrent"],
            "music": ["lidarr", "qbittorrent"],
            "book": ["readarr", "qbittorrent"],
            "generic": ["qbittorrent", "radarr", "sonarr", "lidarr", "readarr"],
        }
        ordered = [m for m in by_type.get(content_type, by_type["generic"]) if m in available]
        # Keep any extra managers available as tail fallback.
        ordered.extend([m for m in available if m not in ordered])
        return ordered

    def _build_download_options(self, manager_name: str, content_type: str) -> Dict[str, Any]:
        """Build per-manager options from config defaults."""
        servarr_cfg = self.config.get("servarr", {}) if isinstance(self.config, dict) else {}
        qb_cfg = self.config.get("download_managers", {}).get("qbittorrent", {}) if isinstance(self.config, dict) else {}

        if manager_name in ("sonarr", "radarr", "lidarr", "readarr"):
            cfg = servarr_cfg.get(manager_name, {})
            options = {
                "quality_profile_id": cfg.get("quality_profile_id", 1),
                "root_folder_path": cfg.get("root_folder_path", "/downloads"),
            }
            if manager_name in ("lidarr", "readarr"):
                options["metadata_profile_id"] = cfg.get("metadata_profile_id", 1)
            return options

        if manager_name == "qbittorrent":
            return {
                "save_path": qb_cfg.get("save_path", ""),
            }

        return {}
    
    # ==================== Scan Tasks ====================
    
    def execute_file_scan(self, scanner_instance) -> str:
        """
        Trigger a file scan operation.
        
        Args:
            scanner_instance: FileScanner instance to use
            
        Returns:
            task_id: ID of the running task
        """
        task_id = self._generate_task_id()
        
        def scan_task():
            try:
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="File Scan",
                    status="running"
                )
                
                # Execute scan
                new_files = scanner_instance.scan_once()
                
                # Update statistics
                self.status_tracker.increment_statistic("total_files_scanned", len(new_files))
                
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="File Scan",
                    status="completed",
                    processed_items=len(new_files),
                    total_items=len(new_files)
                )
                
                logger.info(f"File scan completed: {len(new_files)} new files")
                
            except Exception as e:
                logger.error(f"File scan failed: {e}", exc_info=True)
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="File Scan",
                    status="error",
                    error_message=str(e)
                )
        
        return self._execute_task_async(task_id, "File Scan", scan_task)
    
    # ==================== Distribution Tasks ====================
    
    def execute_file_distribution(self, distributor_instance, files: List) -> str:
        """
        Trigger a file distribution operation.
        
        Args:
            distributor_instance: FileDistributor instance to use
            files: List of ScannedFile objects to distribute
            
        Returns:
            task_id: ID of the running task
        """
        task_id = self._generate_task_id()
        total_files = len(files)
        
        def distribution_task():
            try:
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="File Distribution",
                    status="running",
                    total_items=total_files
                )
                
                # Execute distribution with progress tracking
                results = distributor_instance.distribute_batch(files)
                
                successful = sum(1 for v in results.values() if v.get("success", False))
                total_size = sum(f.size_bytes for f in files)
                
                # Update statistics
                self.status_tracker.increment_statistic("total_files_distributed", successful)
                self.status_tracker.increment_statistic(
                    "total_distribution_size_gb",
                    total_size / (1024 ** 3)
                )
                
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="File Distribution",
                    status="completed",
                    processed_items=successful,
                    total_items=total_files
                )
                
                logger.info(f"Distribution completed: {successful}/{total_files} files distributed")
                
            except Exception as e:
                logger.error(f"Distribution failed: {e}", exc_info=True)
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="File Distribution",
                    status="error",
                    error_message=str(e)
                )
        
        return self._execute_task_async(task_id, "File Distribution", distribution_task)
    
    # ==================== Service Health Checks ====================
    
    def check_all_services_health(self) -> str:
        """
        Check health of all configured services.
        
        Returns:
            task_id: ID of the health check task
        """
        task_id = self._generate_task_id()
        
        def health_check_task():
            if not self.adapters_factory:
                logger.warning("No adapters factory available for health check")
                return
            
            try:
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="Service Health Check",
                    status="running"
                )
                
                services_checked = 0
                services_ok = 0
                
                # Check indexers
                if hasattr(self.adapters_factory, 'indexers'):
                    for name, adapter in self.adapters_factory.indexers.items():
                        services_checked += 1
                        try:
                            if hasattr(adapter, 'health_check'):
                                adapter.health_check()
                                self.status_tracker.update_service_status(
                                    service_name=name,
                                    service_type="indexer",
                                    is_online=True,
                                    response_time_ms=0
                                )
                                services_ok += 1
                        except Exception as e:
                            logger.warning(f"Indexer {name} health check failed: {e}")
                            self.status_tracker.update_service_status(
                                service_name=name,
                                service_type="indexer",
                                is_online=False,
                                response_time_ms=0,
                                error_message=str(e)
                            )
                
                # Check download managers
                if hasattr(self.adapters_factory, 'download_managers'):
                    for name, adapter in self.adapters_factory.download_managers.items():
                        services_checked += 1
                        try:
                            if hasattr(adapter, 'health_check'):
                                adapter.health_check()
                                self.status_tracker.update_service_status(
                                    service_name=name,
                                    service_type="download_manager",
                                    is_online=True,
                                    response_time_ms=0
                                )
                                services_ok += 1
                        except Exception as e:
                            logger.warning(f"Download manager {name} health check failed: {e}")
                            self.status_tracker.update_service_status(
                                service_name=name,
                                service_type="download_manager",
                                is_online=False,
                                response_time_ms=0,
                                error_message=str(e)
                            )
                
                # Check media servers
                if hasattr(self.adapters_factory, 'media_servers'):
                    for name, adapter in self.adapters_factory.media_servers.items():
                        services_checked += 1
                        try:
                            if hasattr(adapter, 'health_check'):
                                adapter.health_check()
                                self.status_tracker.update_service_status(
                                    service_name=name,
                                    service_type="media_server",
                                    is_online=True,
                                    response_time_ms=0
                                )
                                services_ok += 1
                        except Exception as e:
                            logger.warning(f"Media server {name} health check failed: {e}")
                            self.status_tracker.update_service_status(
                                service_name=name,
                                service_type="media_server",
                                is_online=False,
                                response_time_ms=0,
                                error_message=str(e)
                            )
                
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="Service Health Check",
                    status="completed",
                    processed_items=services_ok,
                    total_items=services_checked
                )
                
                logger.info(f"Service health check completed: {services_ok}/{services_checked} online")
                
            except Exception as e:
                logger.error(f"Service health check failed: {e}", exc_info=True)
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="Service Health Check",
                    status="error",
                    error_message=str(e)
                )
        
        return self._execute_task_async(task_id, "Service Health Check", health_check_task)
    
    # ==================== End-to-End Workflows ====================
    
    def execute_full_workflow(self, scanner, distributor, trigger_media_scan: bool = True) -> str:
        """
        Execute a complete workflow: scan -> distribute -> trigger media server scans.
        
        Args:
            scanner: FileScanner instance
            distributor: FileDistributor instance
            trigger_media_scan: Whether to trigger media server library scans
            
        Returns:
            task_id: ID of the workflow task
        """
        task_id = self._generate_task_id()
        
        def workflow():
            try:
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="Full Workflow",
                    status="running",
                    current_item="Scanning files..."
                )
                
                # Step 1: Scan
                new_files = scanner.scan_once()
                logger.info(f"Workflow: Found {len(new_files)} new files")
                
                if not new_files:
                    self.status_tracker.update_task_status(
                        task_id=task_id,
                        task_name="Full Workflow",
                        status="completed"
                    )
                    return
                
                # Step 2: Distribute
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="Full Workflow",
                    status="running",
                    current_item="Distributing files...",
                    total_items=len(new_files)
                )
                
                results = distributor.distribute_batch(new_files)
                successful = sum(1 for v in results.values() if v.get("success", False))
                logger.info(f"Workflow: Distributed {successful}/{len(new_files)} files")
                
                # Step 3: Trigger media server scans (optional)
                if trigger_media_scan and self.adapters_factory and hasattr(self.adapters_factory, 'media_servers'):
                    self.status_tracker.update_task_status(
                        task_id=task_id,
                        task_name="Full Workflow",
                        status="running",
                        current_item="Triggering media server scans..."
                    )
                    
                    for name, adapter in self.adapters_factory.media_servers.items():
                        try:
                            libraries = adapter.get_libraries()
                            for lib in libraries:
                                adapter.scan_library(lib["id"])
                            logger.info(f"Workflow: Triggered scan on {name}")
                        except Exception as e:
                            logger.warning(f"Workflow: Could not trigger scan on {name}: {e}")
                
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="Full Workflow",
                    status="completed",
                    processed_items=successful,
                    total_items=len(new_files)
                )
                
                logger.info("Workflow completed successfully")
                
            except Exception as e:
                logger.error(f"Workflow failed: {e}", exc_info=True)
                self.status_tracker.update_task_status(
                    task_id=task_id,
                    task_name="Full Workflow",
                    status="error",
                    error_message=str(e)
                )
        
        return self._execute_task_async(task_id, "Full Workflow", workflow)
    
    # ==================== Scheduler Integration ====================
    
    def schedule_recurring_scan(self, scanner_instance, interval_value: int,
                               interval_unit: str = "hours") -> str:
        """Schedule recurring file scans."""
        def scan_task():
            self.execute_file_scan(scanner_instance)
        
        return self.scheduler.add_interval_task(
            task_name="Recurring File Scan",
            task_function=scan_task,
            interval_value=interval_value,
            interval_unit=interval_unit,
            description=f"Scan files every {interval_value} {interval_unit}"
        )
    
    def schedule_service_health_check(self, interval_value: int = 30,
                                     interval_unit: str = "minutes") -> str:
        """Schedule recurring service health checks."""
        def health_check_task():
            self.check_all_services_health()
        
        return self.scheduler.add_interval_task(
            task_name="Recurring Service Health Check",
            task_function=health_check_task,
            interval_value=interval_value,
            interval_unit=interval_unit,
            description=f"Check service health every {interval_value} {interval_unit}"
        )
    
    def get_scheduler(self) -> TaskScheduler:
        """Get the task scheduler instance."""
        return self.scheduler
    
    # ==================== Internal Utilities ====================
    
    def _execute_task_async(self, task_id: str, task_name: str, task_func: Callable) -> str:
        """Execute a task asynchronously in a background thread."""
        def task_wrapper():
            try:
                task_func()
            finally:
                with self._lock:
                    if task_id in self._running_tasks:
                        del self._running_tasks[task_id]
        
        thread = threading.Thread(target=task_wrapper, daemon=True, name=task_name)
        
        with self._lock:
            self._running_tasks[task_id] = thread
        
        thread.start()
        logger.info(f"Started async task: {task_name} (ID: {task_id})")
        
        return task_id
    
    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        import uuid
        return str(uuid.uuid4())
    
    def get_running_tasks(self) -> Dict[str, str]:
        """Get list of currently running tasks."""
        with self._lock:
            return {k: v.name for k, v in self._running_tasks.items() if v.is_alive()}
    
    def start(self) -> None:
        """Start the task manager."""
        self.scheduler.start()
        from event_system import SystemStatus

        self.status_tracker.set_system_status(SystemStatus.READY)
        logger.info("Task manager started")
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop the task manager gracefully."""
        self.scheduler.stop(timeout=timeout)
        logger.info("Task manager stopped")
    
    def is_running(self) -> bool:
        """Check if task manager is running."""
        return self.scheduler.is_running()
