from __future__ import annotations

import subprocess
import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .file_distribution import DistributionStrategy, FileDistributor, OutputFolder


NodeDefinition = Dict[str, Any]
RawTreeNode = Union[str, NodeDefinition]


NODE_LIBRARY: Dict[str, Dict[str, Any]] = {
    "download_input": {
        "name": "Download Input",
        "description": "Use the downloaded file as workflow input.",
    },
    "size_check": {
        "name": "Check File Size",
        "description": "Measure file size to drive branching decisions.",
        "params": {
            "threshold_gb": "Optional threshold override for this node and downstream size routes.",
        },
    },
    "route_small_to_load_balance": {
        "name": "Small File Route",
        "description": "If file is <= threshold, route directly to load-balanced output and finish.",
        "params": {
            "threshold_gb": "Optional threshold override for small-file route.",
        },
    },
    "route_large_to_encode": {
        "name": "Large File Encode",
        "description": "If file is > threshold, run HandBrake encoding.",
        "params": {
            "threshold_gb": "Optional threshold override for large-file encode route.",
            "preset": "Optional HandBrake preset override for this node.",
        },
    },
    "subtitle_detect_or_generate": {
        "name": "Subtitle Detect/Generate",
        "description": "Detect subtitle stream and generate subtitles if missing.",
        "params": {
            "profile": "Optional subtitle profile override for this node.",
        },
    },
    "av_check": {
        "name": "Audio/Video Check",
        "description": "Verify valid video/audio streams and dimensions.",
    },
    "fix_media_if_needed": {
        "name": "Fix Media",
        "description": "Attempt remediation for broken media (remux/audio fix).",
        "params": {
            "max_attempts": "Maximum remediation attempts for this node.",
        },
    },
    "cleanup_and_retry_if_failed": {
        "name": "Cleanup And Retry",
        "description": "Cleanup problematic files and create a retry download job if still invalid.",
    },
    "load_balance_output": {
        "name": "Load Balanced Output",
        "description": "Send resulting media file to configured output folders.",
    },
}


DEFAULT_BEHAVIOR_TREES: Dict[str, List[NodeDefinition]] = {
    "default_media_flow": [
        {"node_id": "download_input", "params": {}},
        {"node_id": "size_check", "params": {"threshold_gb": 10.0}},
        {"node_id": "route_small_to_load_balance", "params": {}},
        {"node_id": "route_large_to_encode", "params": {}},
        {"node_id": "subtitle_detect_or_generate", "params": {}},
        {"node_id": "av_check", "params": {}},
        {"node_id": "fix_media_if_needed", "params": {"max_attempts": 1}},
        {"node_id": "cleanup_and_retry_if_failed", "params": {}},
        {"node_id": "load_balance_output", "params": {}},
    ],
    "encode_always_flow": [
        {"node_id": "download_input", "params": {}},
        {"node_id": "size_check", "params": {}},
        {"node_id": "route_large_to_encode", "params": {}},
        {"node_id": "subtitle_detect_or_generate", "params": {}},
        {"node_id": "av_check", "params": {}},
        {"node_id": "fix_media_if_needed", "params": {"max_attempts": 1}},
        {"node_id": "cleanup_and_retry_if_failed", "params": {}},
        {"node_id": "load_balance_output", "params": {}},
    ],
    "direct_output_flow": [
        {"node_id": "download_input", "params": {}},
        {"node_id": "size_check", "params": {}},
        {"node_id": "subtitle_detect_or_generate", "params": {}},
        {"node_id": "av_check", "params": {}},
        {"node_id": "fix_media_if_needed", "params": {"max_attempts": 1}},
        {"node_id": "cleanup_and_retry_if_failed", "params": {}},
        {"node_id": "load_balance_output", "params": {}},
    ],
}


def normalize_tree_nodes(tree_nodes: List[RawTreeNode]) -> List[NodeDefinition]:
    """Normalize behavior tree nodes into dict format with node_id + params."""
    normalized: List[NodeDefinition] = []
    for node in tree_nodes or []:
        if isinstance(node, str):
            node_id = node.strip()
            if not node_id:
                continue
            normalized.append({"node_id": node_id, "params": {}})
            continue
        if isinstance(node, dict):
            node_id = str(node.get("node_id", "")).strip()
            if not node_id:
                continue
            params = node.get("params", {})
            if not isinstance(params, dict):
                params = {}
            normalized.append({"node_id": node_id, "params": dict(params)})
    return normalized


def get_node_library() -> Dict[str, Dict[str, Any]]:
    """Return available workflow nodes/blocks that users can assemble into trees."""
    return copy.deepcopy(NODE_LIBRARY)


def get_default_behavior_trees() -> Dict[str, List[NodeDefinition]]:
    """Return built-in behavior trees."""
    return {name: normalize_tree_nodes(nodes) for name, nodes in DEFAULT_BEHAVIOR_TREES.items()}


@dataclass
class FlowContext:
    """Mutable state while a node-based workflow executes."""

    job_id: str
    query: str
    input_path: Path
    current_file: Path
    output_file_name: str
    config: Dict[str, Any]
    state: Dict[str, Any] = field(default_factory=dict)


class NodeFlowExecutor:
    """Default node-based media QA and routing workflow executor."""

    def __init__(
        self,
        config: Dict[str, Any],
        run_encode: Callable[[Path, Path, str], None],
        run_subtitle: Callable[[Path, Path, str], None],
        retry_download: Callable[[str], str],
    ) -> None:
        self.config = config
        self.run_encode = run_encode
        self.run_subtitle = run_subtitle
        self.retry_download = retry_download

    def execute_default_flow(
        self,
        job_id: str,
        query: str,
        input_path: str,
        output_path: str,
        threshold_gb: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Default flow:
        download -> size check -> (encode if >threshold) -> subtitle detect -> av check
        -> (fix if needed) -> load balance output -> done
        -> if unrecoverable: cleanup + retry download
        """
        in_file = Path(input_path)
        if not in_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        out_target = Path(output_path)
        output_file_name = out_target.name if out_target.name else in_file.name

        ctx = FlowContext(
            job_id=job_id,
            query=query,
            input_path=in_file,
            current_file=in_file,
            output_file_name=output_file_name,
            config=self.config,
            state={
                "threshold_gb": threshold_gb,
                "fix_attempts": 0,
                "max_fix_attempts": 1,
                "has_subtitles": False,
                "av_ok": False,
                "early_routed": False,
                "retry_job_id": None,
            },
        )

        return self.execute_behavior_tree(ctx, tree_nodes=DEFAULT_BEHAVIOR_TREES["default_media_flow"])

    def execute_behavior_tree(self, ctx: FlowContext, tree_nodes: List[RawTreeNode]) -> Dict[str, Any]:
        """Execute a behavior tree represented as an ordered list of node IDs."""
        for node_def in normalize_tree_nodes(tree_nodes):
            node_id = node_def["node_id"]
            params = node_def.get("params", {})
            if node_id not in NODE_LIBRARY:
                raise ValueError(f"Unknown node id in behavior tree: {node_id}")

            # Short-circuit when small-file route already completed routing.
            if ctx.state.get("early_routed"):
                break

            if node_id == "download_input":
                # Input already present by construction.
                continue

            if node_id == "size_check":
                if "threshold_gb" in params:
                    try:
                        ctx.state["threshold_gb"] = float(params.get("threshold_gb"))
                    except Exception:
                        pass
                ctx.state["file_size_gb"] = self._file_size_gb(ctx.current_file)
                continue

            if node_id == "route_small_to_load_balance":
                threshold_raw = params.get("threshold_gb", ctx.state.get("threshold_gb", 10.0))
                threshold = float(threshold_raw)
                size_gb = float(ctx.state.get("file_size_gb", self._file_size_gb(ctx.current_file)))
                if size_gb <= threshold:
                    routed = self._route_to_load_balanced_output(ctx.current_file, ctx.output_file_name)
                    if routed:
                        ctx.current_file = routed
                    ctx.state["early_routed"] = True
                continue

            if node_id == "route_large_to_encode":
                threshold_raw = params.get("threshold_gb", ctx.state.get("threshold_gb", 10.0))
                threshold = float(threshold_raw)
                size_gb = float(ctx.state.get("file_size_gb", self._file_size_gb(ctx.current_file)))
                if size_gb > threshold:
                    encoded_path = self._derive_path(ctx.current_file, suffix=".encoded.mkv")
                    preset = params.get("preset") or ctx.config.get("defaults", {}).get("handbrake_preset", "Fast 1080p30")
                    self.run_encode(ctx.current_file, encoded_path, preset)
                    ctx.current_file = encoded_path
                continue

            if node_id == "subtitle_detect_or_generate":
                ctx.state["has_subtitles"] = self._has_subtitle_stream(ctx.current_file)
                if not ctx.state["has_subtitles"]:
                    subtitle_out = self._derive_path(ctx.current_file, suffix=".subtitled.mkv")
                    profile = params.get("profile") or ctx.config.get("defaults", {}).get("subtitle_profile", "default")
                    self.run_subtitle(ctx.current_file, subtitle_out, profile)
                    if subtitle_out.exists():
                        ctx.current_file = subtitle_out
                        ctx.state["has_subtitles"] = self._has_subtitle_stream(ctx.current_file)
                continue

            if node_id == "av_check":
                av_ok, av_message = self._check_audio_video_integrity(ctx.current_file)
                ctx.state["av_ok"] = av_ok
                ctx.state["av_message"] = av_message
                continue

            if node_id == "fix_media_if_needed":
                if not ctx.state.get("av_ok", False):
                    max_attempts = int(params.get("max_attempts", ctx.state.get("max_fix_attempts", 1)))
                    ctx.state["max_fix_attempts"] = max_attempts
                    attempts = int(ctx.state.get("fix_attempts", 0))
                    if attempts < max_attempts:
                        fixed = self._attempt_media_fix(ctx.current_file)
                        ctx.state["fix_attempts"] = attempts + 1
                        if fixed and fixed.exists():
                            ctx.current_file = fixed
                            av_ok, av_message = self._check_audio_video_integrity(ctx.current_file)
                            ctx.state["av_ok"] = av_ok
                            ctx.state["av_message"] = av_message
                continue

            if node_id == "cleanup_and_retry_if_failed":
                if not ctx.state.get("av_ok", False):
                    self._cleanup_intermediate_files(ctx)
                    retry_id = self.retry_download(ctx.job_id)
                    ctx.state["retry_job_id"] = retry_id
                    return {
                        "success": False,
                        "status": "retry_triggered",
                        "message": f"Workflow failed validation; retry job created: {retry_id}",
                        "retry_job_id": retry_id,
                        "final_file": str(ctx.current_file),
                    }
                continue

            if node_id == "load_balance_output":
                routed_path = self._route_to_load_balanced_output(ctx.current_file, ctx.output_file_name)
                if routed_path:
                    ctx.current_file = routed_path
                continue

        return {
            "success": True,
            "status": "completed",
            "message": "Workflow completed successfully",
            "file_size_gb": float(ctx.state.get("file_size_gb", self._file_size_gb(ctx.current_file))),
            "has_subtitles": ctx.state["has_subtitles"],
            "av_message": ctx.state.get("av_message", "ok"),
            "final_file": str(ctx.current_file),
            "routed": bool(ctx.state.get("early_routed", False) or self._is_under_output_tree(ctx.current_file)),
        }

    def execute_named_tree(
        self,
        tree_name: str,
        custom_trees: Dict[str, List[RawTreeNode]],
        job_id: str,
        query: str,
        input_path: str,
        output_path: str,
        threshold_gb: float = 10.0,
    ) -> Dict[str, Any]:
        """Execute one of the built-in or custom behavior trees by name."""
        all_trees = get_default_behavior_trees()
        all_trees.update({k: normalize_tree_nodes(v) for k, v in (custom_trees or {}).items()})

        if tree_name not in all_trees:
            raise ValueError(f"Unknown behavior tree: {tree_name}")

        in_file = Path(input_path)
        if not in_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        out_target = Path(output_path)
        output_file_name = out_target.name if out_target.name else in_file.name

        ctx = FlowContext(
            job_id=job_id,
            query=query,
            input_path=in_file,
            current_file=in_file,
            output_file_name=output_file_name,
            config=self.config,
            state={
                "threshold_gb": threshold_gb,
                "fix_attempts": 0,
                "max_fix_attempts": 1,
                "has_subtitles": False,
                "av_ok": False,
                "early_routed": False,
                "retry_job_id": None,
            },
        )

        return self.execute_behavior_tree(ctx, tree_nodes=all_trees[tree_name])

    def _is_under_output_tree(self, file_path: Path) -> bool:
        """Best effort check that file sits under any configured output directory."""
        file_dist_cfg = self.config.get("file_distribution", {}) if isinstance(self.config, dict) else {}
        folders_cfg = file_dist_cfg.get("output_folders", {}) if isinstance(file_dist_cfg, dict) else {}
        try:
            target = file_path.resolve()
        except Exception:
            return False
        for _, folder in folders_cfg.items():
            try:
                out_path = Path(folder.get("path", "")).resolve()
            except Exception:
                continue
            if str(target).lower().startswith(str(out_path).lower()):
                return True
        return False

    @staticmethod
    def _file_size_gb(path: Path) -> float:
        return path.stat().st_size / (1024 ** 3)

    @staticmethod
    def _derive_path(path: Path, suffix: str) -> Path:
        return path.with_name(f"{path.stem}{suffix}")

    @staticmethod
    def _run_command(command: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def _ffprobe_streams(self, media_path: Path) -> List[Dict[str, Any]]:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            str(media_path),
        ]
        proc = self._run_command(command)
        if proc.returncode != 0:
            return []
        try:
            import json

            data = json.loads(proc.stdout or "{}")
            return data.get("streams", [])
        except Exception:
            return []

    def _has_subtitle_stream(self, media_path: Path) -> bool:
        streams = self._ffprobe_streams(media_path)
        return any(s.get("codec_type") == "subtitle" for s in streams)

    def _check_audio_video_integrity(self, media_path: Path) -> tuple[bool, str]:
        streams = self._ffprobe_streams(media_path)
        if not streams:
            return False, "No stream metadata found (ffprobe failed or empty file)"

        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        if not video_streams:
            return False, "No video stream"
        if not audio_streams:
            return False, "No audio stream"

        # Basic blank-video heuristic: reported dimensions must be valid.
        v0 = video_streams[0]
        width = int(v0.get("width", 0) or 0)
        height = int(v0.get("height", 0) or 0)
        if width <= 0 or height <= 0:
            return False, "Invalid video dimensions"

        return True, "Audio/video streams look valid"

    def _attempt_media_fix(self, media_path: Path) -> Optional[Path]:
        # First attempt: remux copy (often fixes container/index issues).
        fixed_copy = media_path.with_name(f"{media_path.stem}.fixed.mkv")
        remux_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(media_path),
            "-c",
            "copy",
            str(fixed_copy),
        ]
        remux = self._run_command(remux_cmd)
        if remux.returncode == 0 and fixed_copy.exists():
            ok, _ = self._check_audio_video_integrity(fixed_copy)
            if ok:
                return fixed_copy

        # Second attempt: re-encode audio stream if missing/broken audio metadata.
        fixed_audio = media_path.with_name(f"{media_path.stem}.fixaudio.mkv")
        audio_fix_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(media_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            str(fixed_audio),
        ]
        audio_fix = self._run_command(audio_fix_cmd)
        if audio_fix.returncode == 0 and fixed_audio.exists():
            ok, _ = self._check_audio_video_integrity(fixed_audio)
            if ok:
                return fixed_audio

        return None

    def _route_to_load_balanced_output(self, media_path: Path, output_file_name: str) -> Optional[Path]:
        file_dist_cfg = self.config.get("file_distribution", {}) if isinstance(self.config, dict) else {}
        if not file_dist_cfg or not file_dist_cfg.get("enabled", False):
            return None

        folders_cfg = file_dist_cfg.get("output_folders", {})
        outputs: List[OutputFolder] = []
        for _, folder in folders_cfg.items():
            try:
                outputs.append(
                    OutputFolder(
                        path=Path(folder.get("path", "")),
                        max_size_gb=folder.get("max_size_gb"),
                        enabled=folder.get("enabled", True),
                    )
                )
            except Exception:
                continue

        if not outputs:
            return None

        strategy_raw = str(file_dist_cfg.get("strategy", "equal_size")).lower()
        strategy_map = {
            "equal_size": DistributionStrategy.EQUAL_SIZE,
            "least_used": DistributionStrategy.LEAST_USED,
            "round_robin": DistributionStrategy.ROUND_ROBIN,
            "random": DistributionStrategy.RANDOM,
        }
        strategy = strategy_map.get(strategy_raw, DistributionStrategy.EQUAL_SIZE)

        distributor = FileDistributor(
            output_folders=outputs,
            strategy=strategy,
            copy_mode=bool(file_dist_cfg.get("copy_mode", False)),
        )
        return distributor.distribute_file(media_path, new_name=output_file_name)

    @staticmethod
    def _cleanup_intermediate_files(ctx: FlowContext) -> None:
        current = ctx.current_file
        if current.exists() and current != ctx.input_path:
            try:
                current.unlink()
            except Exception:
                pass
