from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .app_runner import execute_pipeline
from .config_loader import create_starter_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Media automation pipeline")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    parser.add_argument(
        "--new-config",
        action="store_true",
        help="Create a starter config at --config if it does not exist, then continue startup",
    )
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode")
    parser.add_argument("--run", action="store_true", help="Force real execution mode")
    parser.add_argument("--job", help="Run a single job by name")
    parser.add_argument("--gui", action="store_true", help="Launch PyQt6 desktop UI")
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        help="Import path for plugin module(s) exposing register(registry)",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = Path(args.config)

    if args.new_config:
        created = create_starter_config(config_path)
        if created:
            print(f"[config] Created starter config: {config_path}")
        else:
            print(f"[config] Config already exists, leaving it unchanged: {config_path}")

    if args.gui:
        from .gui import launch_gui

        return launch_gui(
            config_path=config_path,
            dry_run_default=bool(args.dry_run),
            plugins=list(args.plugin),
        )

    if args.dry_run and args.run:
        parser.error("Use either --dry-run or --run, not both.")

    dry_run_override = None
    if args.dry_run:
        dry_run_override = True
    elif args.run:
        dry_run_override = False

    code, lines = execute_pipeline(
        config_path=config_path,
        dry_run_override=dry_run_override,
        only_job=args.job,
        plugins=args.plugin,
    )
    for line in lines:
        print(line)
    return code
