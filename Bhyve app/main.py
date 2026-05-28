from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from bhyve_app.config import AppConfig, load_app_config
from bhyve_app.controller import BhyveTemperatureService, Decision, format_device_summary
from bhyve_app.web_ui import launch_web_ui

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"
GLOBAL_FLAG_NAMES = {"--config", "--verbose"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Temperature-driven manual watering for Orbit BHyve."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the JSON config file.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("devices", help="List sprinkler devices and zones.")
    subparsers.add_parser(
        "status",
        help="Preview one control cycle without changing BHyve.",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run the temperature controller once or continuously.",
    )
    run_parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single control cycle and exit.",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate rules but do not send start/stop commands.",
    )

    water_parser = subparsers.add_parser(
        "water",
        help="Manually start a zone for testing.",
    )
    water_parser.add_argument("--device-id", required=True)
    water_parser.add_argument("--station", type=int, required=True)
    water_parser.add_argument("--minutes", type=float, required=True)

    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop a manual run on a device.",
    )
    stop_parser.add_argument("--device-id", required=True)

    web_parser = subparsers.add_parser(
        "web",
        help="Launch the local web UI for config editing and control.",
    )
    web_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host interface for the web server (use 0.0.0.0 for LAN access).",
    )
    web_parser.add_argument(
        "--port",
        type=int,
        default=8787,
        help="Port for the local web server.",
    )
    web_parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the web UI in the default browser.",
    )

    return parser


def normalize_cli_args(argv: list[str]) -> list[str]:
    global_args: list[str] = []
    remaining_args: list[str] = []
    index = 0

    while index < len(argv):
        token = argv[index]
        if token == "--config":
            global_args.append(token)
            if index + 1 < len(argv):
                global_args.append(argv[index + 1])
                index += 2
                continue
            remaining_args.append(token)
            index += 1
            continue
        if token == "--verbose":
            global_args.append(token)
            index += 1
            continue
        remaining_args.append(token)
        index += 1

    if not remaining_args or remaining_args[0] in GLOBAL_FLAG_NAMES:
        remaining_args = ["run", *remaining_args]

    return [*global_args, *remaining_args]


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def print_decisions(decisions: list[Decision]) -> None:
    for decision in decisions:
        prefix = decision.action.upper() if decision.applied else decision.action
        print(
            f"[{prefix}] {decision.rule_name} | device={decision.device_id} "
            f"station={decision.station} | reason={decision.reason}"
        )


async def run_devices_command(config: AppConfig) -> None:
    service = BhyveTemperatureService(config)
    devices = await service.list_devices()
    for device in devices:
        print(format_device_summary(device))


async def run_status_command(config: AppConfig) -> None:
    service = BhyveTemperatureService(config)
    report = await service.run_cycle(apply_changes=False)
    print(
        f"Temperature: {report.temperature.value:.1f} "
        f"{report.temperature.unit} at {report.temperature.observed_at.isoformat()}"
    )
    print_decisions(report.decisions)


async def run_controller_command(config: AppConfig, once: bool, dry_run: bool) -> None:
    service = BhyveTemperatureService(config)
    while True:
        report = await service.run_cycle(
            apply_changes=not dry_run,
            wait_for_scheduled_stops=once and not dry_run,
        )
        print(
            f"Temperature: {report.temperature.value:.1f} "
            f"{report.temperature.unit} at {report.temperature.observed_at.isoformat()}"
        )
        print_decisions(report.decisions)
        if once:
            return
        await asyncio.sleep(config.bhyve.poll_interval_seconds)


async def run_manual_water_command(
    config: AppConfig, device_id: str, station: int, minutes: float
) -> None:
    service = BhyveTemperatureService(config)
    await service.start_manual_watering(
        device_id,
        station,
        minutes,
        wait_for_scheduled_stop=True,
    )
    print(
        f"Requested manual watering for device={device_id} station={station} "
        f"minutes={minutes}"
    )


async def run_stop_command(config: AppConfig, device_id: str) -> None:
    service = BhyveTemperatureService(config)
    await service.stop_manual_watering(device_id)
    print(f"Requested stop for device={device_id}")


async def dispatch(args: argparse.Namespace) -> None:
    config = load_app_config(args.config)
    if args.command == "devices":
        await run_devices_command(config)
        return
    if args.command == "status":
        await run_status_command(config)
        return
    if args.command == "run":
        await run_controller_command(config, once=args.once, dry_run=args.dry_run)
        return
    if args.command == "water":
        await run_manual_water_command(
            config,
            device_id=args.device_id,
            station=args.station,
            minutes=args.minutes,
        )
        return
    if args.command == "stop":
        await run_stop_command(config, device_id=args.device_id)
        return
    raise ValueError(f"Unsupported command: {args.command}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args(normalize_cli_args(sys.argv[1:]))
    configure_logging(args.verbose)
    if args.command == "web":
        launch_web_ui(
            config_path=args.config,
            host=args.host,
            port=args.port,
            open_browser=args.open_browser,
        )
        return 0
    try:
        asyncio.run(dispatch(args))
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
