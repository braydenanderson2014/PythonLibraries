from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Iterable, Sequence

from ..models import JobArtifacts, JobConfig, PipelineContext
from ..utils import ensure_dir


def _as_int(value: object, fallback: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return fallback


def _as_bool(value: object, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return fallback


def _coerce_extensions(raw: object) -> tuple[str, ...]:
    if isinstance(raw, list):
        values = [str(item).strip().lower() for item in raw if str(item).strip()]
        return tuple(values) if values else (".mkv", ".mp4")
    return (".mkv", ".mp4")


def _find_newest_completed_file(
    watch_dir: Path,
    allowed_suffixes: Sequence[str],
    since_ts: float,
    stable_for_sec: int,
) -> Path | None:
    candidates: list[Path] = []
    for suffix in allowed_suffixes:
        candidates.extend(watch_dir.glob(f"*{suffix}"))

    filtered = [p for p in candidates if p.is_file() and p.stat().st_mtime >= since_ts]
    if not filtered:
        return None

    latest = max(filtered, key=lambda p: p.stat().st_mtime)
    first_size = latest.stat().st_size
    time.sleep(stable_for_sec)
    second_size = latest.stat().st_size
    if first_size != second_size:
        return None
    return latest


def launch_and_wait_for_download(
    adapter_name: str,
    exe: str,
    ctx: PipelineContext,
    job: JobConfig,
    artifacts: JobArtifacts,
) -> Path:
    defaults = ctx.defaults
    metadata = job.metadata

    watch_dir_raw = metadata.get("download_watch_dir") or defaults.get("download_watch_dir")
    if not isinstance(watch_dir_raw, str) or not watch_dir_raw.strip():
        raise RuntimeError(
            f"[{adapter_name}] Missing download_watch_dir. Set job.metadata.download_watch_dir "
            "or defaults.download_watch_dir."
        )

    watch_dir = Path(watch_dir_raw).expanduser().resolve()
    ensure_dir(watch_dir)

    timeout_sec = _as_int(metadata.get("download_timeout_sec", defaults.get("download_timeout_sec")), 900)
    stable_for_sec = _as_int(
        metadata.get("download_stable_for_sec", defaults.get("download_stable_for_sec")),
        8,
    )
    include_source_url = _as_bool(
        metadata.get("launch_with_source_url", defaults.get("launch_with_source_url")),
        True,
    )
    first_use_signin_required = _as_bool(
        metadata.get("first_use_signin_required", defaults.get("first_use_signin_required")),
        True,
    )
    first_use_signin_wait_sec = _as_int(
        metadata.get("first_use_signin_wait_sec", defaults.get("first_use_signin_wait_sec")),
        45,
    )
    launch_args_raw = metadata.get("launch_args", [])
    launch_args = [str(x) for x in launch_args_raw] if isinstance(launch_args_raw, list) else []
    suffixes = _coerce_extensions(metadata.get("download_extensions", defaults.get("download_extensions")))
    state_root = ctx.temp_root / ".state" / adapter_name
    ensure_dir(state_root)
    signed_in_marker = state_root / "signed_in.ok"

    launch_cmd = [exe]
    launch_cmd.extend(launch_args)
    if include_source_url and job.source.strip():
        launch_cmd.append(job.source)

    artifacts.logs.append(f"[{adapter_name}] launching app: {' '.join(launch_cmd)}")
    artifacts.logs.append(f"[{adapter_name}] watch dir: {watch_dir}")
    artifacts.logs.append(f"[{adapter_name}] timeout: {timeout_sec}s, stability window: {stable_for_sec}s")
    artifacts.logs.append(
        f"[{adapter_name}] app is non-CLI; complete selection/download in the app window manually."
    )

    if ctx.dry_run:
        return watch_dir / f"{job.output_name}.mkv"

    started_at = time.time()
    subprocess.Popen(launch_cmd)

    if first_use_signin_required and not signed_in_marker.exists():
        artifacts.logs.append(
            f"[{adapter_name}] first-use sign-in checkpoint: maximize the app, verify account is signed in, "
            f"and keep it ready for automation. Waiting {first_use_signin_wait_sec} seconds."
        )
        time.sleep(first_use_signin_wait_sec)
        signed_in_marker.write_text("ok\n", encoding="utf-8")
        artifacts.logs.append(f"[{adapter_name}] sign-in checkpoint complete: {signed_in_marker}")

    deadline = started_at + timeout_sec
    while time.time() < deadline:
        found = _find_newest_completed_file(
            watch_dir=watch_dir,
            allowed_suffixes=suffixes,
            since_ts=started_at,
            stable_for_sec=stable_for_sec,
        )
        if found is not None:
            artifacts.logs.append(f"[{adapter_name}] detected completed file: {found}")
            return found
        time.sleep(2)

    raise RuntimeError(
        f"[{adapter_name}] Timed out waiting for completed download in {watch_dir} "
        f"after {timeout_sec} seconds."
    )
