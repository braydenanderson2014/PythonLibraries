from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

from otterforge.api.facade import OtterForgeAPI
from otterforge.models.build_request import BuildRequest
from otterforge.ui.main_window import launch_ui


_T = TypeVar("_T")


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _should_render_console_progress() -> bool:
    override = os.environ.get("OTTERFORGE_PROGRESS", "auto").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        return True
    if override in {"0", "false", "no", "off"}:
        return False
    return bool(getattr(sys.stderr, "isatty", lambda: False)())


def _run_with_console_progress(label: str, operation: Callable[[], _T]) -> _T:
    if not _should_render_console_progress():
        return operation()

    stop_event = threading.Event()
    start = time.monotonic()
    outcome: dict[str, bool] = {"failed": False}

    def _animate() -> None:
        width = 20
        tick = 0
        while not stop_event.wait(0.12):
            filled = tick % (width + 1)
            bar = ("#" * filled).ljust(width, "-")
            elapsed = time.monotonic() - start
            sys.stderr.write(f"\r{label}: [{bar}] {elapsed:4.1f}s")
            sys.stderr.flush()
            tick += 1

    spinner = threading.Thread(target=_animate, name="otterforge-cli-progress", daemon=True)
    spinner.start()
    try:
        return operation()
    except Exception:
        outcome["failed"] = True
        raise
    finally:
        stop_event.set()
        spinner.join(timeout=0.5)
        elapsed = time.monotonic() - start
        status = "failed" if outcome["failed"] else "done"
        sys.stderr.write(f"\r{label}: [{'#' * 20}] {status} in {elapsed:4.1f}s\n")
        sys.stderr.flush()


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="otterforge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init")

    set_parser = subparsers.add_parser("set")
    set_parser.add_argument("key")
    set_parser.add_argument("value")

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("key")

    memory_parser = subparsers.add_parser("memory")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", required=True)

    memory_show = memory_subparsers.add_parser("show")
    memory_show.add_argument("--section")

    memory_clear = memory_subparsers.add_parser("clear")
    memory_clear.add_argument("scope", choices=["settings", "history", "profiles", "all", "project"])
    memory_clear.add_argument("--project-name")

    backend_parser = memory_subparsers.add_parser("backend")
    backend_subparsers = backend_parser.add_subparsers(dest="backend_command", required=True)
    backend_subparsers.add_parser("show")
    backend_set = backend_subparsers.add_parser("set")
    backend_set.add_argument("backend", choices=["json", "sql"])

    memory_migrate = memory_subparsers.add_parser("migrate")
    memory_migrate.add_argument("--to", required=True, choices=["json", "sql"], dest="target_backend")

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("path", nargs="?", default=".")
    scan_parser.add_argument("--scope", default="projects")
    scan_parser.add_argument("--include-ext")

    schema_parser = subparsers.add_parser("schema")
    schema_subparsers = schema_parser.add_subparsers(dest="schema_command", required=True)
    schema_export = schema_subparsers.add_parser("export")
    schema_export.add_argument("path", nargs="?", default=".")
    schema_export.add_argument("--output")
    schema_import = schema_subparsers.add_parser("import")
    schema_import.add_argument("schema_path")

    profile_parser = subparsers.add_parser("profile")
    profile_subparsers = profile_parser.add_subparsers(dest="profile_command", required=True)
    profile_create = profile_subparsers.add_parser("create")
    profile_create.add_argument("name")
    profile_create.add_argument("--description", default="")
    profile_create.add_argument("--settings", default="{}")
    profile_subparsers.add_parser("list")
    profile_show = profile_subparsers.add_parser("show")
    profile_show.add_argument("name")

    builders_parser = subparsers.add_parser("builders")
    builders_subparsers = builders_parser.add_subparsers(dest="builders_command", required=True)
    builders_subparsers.add_parser("list")
    builder_inspect = builders_subparsers.add_parser("inspect")
    builder_inspect.add_argument("name")

    packagers_parser = subparsers.add_parser("packagers")
    packagers_subparsers = packagers_parser.add_subparsers(dest="packagers_command", required=True)
    packagers_subparsers.add_parser("list")
    packager_inspect = packagers_subparsers.add_parser("inspect")
    packager_inspect.add_argument("name")

    installers_parser = subparsers.add_parser("installers")
    installers_subparsers = installers_parser.add_subparsers(dest="installers_command", required=True)
    installers_subparsers.add_parser("list")
    installer_inspect = installers_subparsers.add_parser("inspect")
    installer_inspect.add_argument("name")

    plugins_parser = subparsers.add_parser("plugins")
    plugins_subparsers = plugins_parser.add_subparsers(dest="plugins_command", required=True)
    plugins_subparsers.add_parser("list")
    plugins_subparsers.add_parser("discover")
    plugin_install = plugins_subparsers.add_parser("install")
    plugin_install.add_argument("source_path")
    plugin_remove = plugins_subparsers.add_parser("remove")
    plugin_remove.add_argument("name")

    installer_create = subparsers.add_parser("installer")
    installer_create.add_argument("--project-path", default=".")
    installer_create.add_argument("--installer", dest="installer_name", default="")
    installer_create.add_argument("--source", dest="source_artifacts", action="append", default=[])
    installer_create.add_argument("--app-name", dest="application_name", default="")
    installer_create.add_argument("--version", dest="installer_version", default="")
    installer_create.add_argument("--vendor", default="")
    installer_create.add_argument("--install-root", default="")
    installer_create.add_argument("--license-file", default="")
    installer_create.add_argument("--output-dir", default="dist")
    installer_create.add_argument("--dry-run", action="store_true")
    installer_create.add_argument("installer_args", nargs="*")

    obfuscators_parser = subparsers.add_parser("obfuscators")
    obfuscators_subparsers = obfuscators_parser.add_subparsers(dest="obfuscators_command", required=True)
    obfuscators_subparsers.add_parser("list")
    obfuscator_inspect = obfuscators_subparsers.add_parser("inspect")
    obfuscator_inspect.add_argument("name")

    toolchain_parser = subparsers.add_parser("toolchain")
    toolchain_subparsers = toolchain_parser.add_subparsers(dest="toolchain_command", required=True)
    toolchain_subparsers.add_parser("list")
    toolchain_subparsers.add_parser("doctor")
    toolchain_packs = toolchain_subparsers.add_parser("packs")
    toolchain_packs_subparsers = toolchain_packs.add_subparsers(dest="toolchain_packs_command", required=True)
    toolchain_packs_subparsers.add_parser("list")
    toolchain_pack_install = toolchain_packs_subparsers.add_parser("install")
    toolchain_pack_install.add_argument("pack_id")
    toolchain_pack_install.add_argument("--manager")
    toolchain_pack_install.add_argument("--os", dest="os_name")
    toolchain_pack_install.add_argument("--execute", action="store_true")
    toolchain_pack_install.add_argument("--continue-on-error", action="store_true")
    toolchain_pack_add = toolchain_packs_subparsers.add_parser("add")
    toolchain_pack_add.add_argument("pack_id")
    toolchain_pack_add.add_argument("--name", required=True)
    toolchain_pack_add.add_argument("--description", default="")
    toolchain_pack_add.add_argument(
        "--managers-json",
        required=True,
        help="JSON object like {\"windows\": {\"winget\": [\"winget install ...\"]}}",
    )
    toolchain_pack_add.add_argument(
        "--imports-json",
        default="[]",
        help="JSON array of dependency entries (package_name/import_name/ecosystem)",
    )
    toolchain_pack_add.add_argument(
        "--detectors-json",
        default="{}",
        help="JSON object like {\"windows\": [\"python --version\"]}",
    )
    toolchain_pack_remove = toolchain_packs_subparsers.add_parser("remove")
    toolchain_pack_remove.add_argument("pack_id")

    toolchain_packages = toolchain_subparsers.add_parser("packages")
    toolchain_packages_subparsers = toolchain_packages.add_subparsers(
        dest="toolchain_packages_command", required=True
    )

    toolchain_packages_managers = toolchain_packages_subparsers.add_parser("managers")
    toolchain_packages_managers.add_argument("--os", dest="os_name")

    toolchain_packages_search = toolchain_packages_subparsers.add_parser("search")
    toolchain_packages_search.add_argument("query")
    toolchain_packages_search.add_argument("--manager")
    toolchain_packages_search.add_argument("--os", dest="os_name")
    toolchain_packages_search.add_argument("--limit", type=int, default=25)

    toolchain_packages_install = toolchain_packages_subparsers.add_parser("install")
    toolchain_packages_install.add_argument("packages", nargs="+")
    toolchain_packages_install.add_argument("--manager")
    toolchain_packages_install.add_argument("--os", dest="os_name")
    toolchain_packages_install.add_argument("--execute", action="store_true")

    toolchain_packages_uninstall = toolchain_packages_subparsers.add_parser("uninstall")
    toolchain_packages_uninstall.add_argument("packages", nargs="+")
    toolchain_packages_uninstall.add_argument("--manager")
    toolchain_packages_uninstall.add_argument("--os", dest="os_name")
    toolchain_packages_uninstall.add_argument("--execute", action="store_true")

    toolchain_deps = toolchain_subparsers.add_parser("deps")
    toolchain_deps_subparsers = toolchain_deps.add_subparsers(dest="toolchain_deps_command", required=True)

    toolchain_deps_analyze = toolchain_deps_subparsers.add_parser("analyze")
    toolchain_deps_analyze.add_argument("path", nargs="?", default=".")

    toolchain_deps_missing = toolchain_deps_subparsers.add_parser("install-missing")
    toolchain_deps_missing.add_argument("path", nargs="?", default=".")
    toolchain_deps_missing.add_argument("--manager")
    toolchain_deps_missing.add_argument("--os", dest="os_name")
    toolchain_deps_missing.add_argument("--execute", action="store_true")

    modules_parser = subparsers.add_parser("modules")
    modules_subparsers = modules_parser.add_subparsers(dest="modules_command", required=True)
    modules_list = modules_subparsers.add_parser("list")
    modules_list.add_argument("path", nargs="?", default=".")

    manifest_parser = subparsers.add_parser("manifest")
    manifest_subparsers = manifest_parser.add_subparsers(dest="manifest_command", required=True)
    manifest_subparsers.add_parser("show")
    manifest_subparsers.add_parser("refresh")
    manifest_enable = manifest_subparsers.add_parser("enable")
    manifest_enable.add_argument("capability_id")
    manifest_disable = manifest_subparsers.add_parser("disable")
    manifest_disable.add_argument("capability_id")

    obfuscate_parser = subparsers.add_parser("obfuscate")
    obfuscate_parser.add_argument("--project-path", default=".")
    obfuscate_parser.add_argument("--tool", default="pyarmor")
    obfuscate_parser.add_argument("--source")
    obfuscate_parser.add_argument("--output-dir")
    obfuscate_parser.add_argument("--no-recursive", action="store_true")
    obfuscate_parser.add_argument("--dry-run", action="store_true")
    obfuscate_parser.add_argument("tool_args", nargs="*")

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--project-path", default=".")
    build_parser.add_argument("--builder", default="auto")
    build_parser.add_argument("--lang", dest="language", default="auto")
    build_parser.add_argument("--entry")
    build_parser.add_argument("--source", action="append", dest="source_files", default=[])
    build_parser.add_argument("--name")
    build_parser.add_argument("--onefile", action="store_true")
    build_parser.add_argument("--onedir", action="store_true")
    build_parser.add_argument("--console", action="store_true")
    build_parser.add_argument("--noconsole", action="store_true")
    build_parser.add_argument("--icon")
    build_parser.add_argument("--splash")
    build_parser.add_argument("--output-dir")
    build_parser.add_argument("--compiler")
    build_parser.add_argument("--std", dest="standard")
    build_parser.add_argument("--opt", dest="optimization")
    build_parser.add_argument("--debug-symbols", action="store_true")
    build_parser.add_argument("--include", action="append", dest="include_paths", default=[])
    build_parser.add_argument("--lib-path", action="append", dest="library_paths", default=[])
    build_parser.add_argument("--lib", action="append", dest="libraries", default=[])
    build_parser.add_argument("--config-name", dest="compiler_config_name")
    build_parser.add_argument("--clean", action="store_true")
    build_parser.add_argument("--dry-run", action="store_true")
    build_parser.add_argument("builder_args", nargs="*")

    package_parser = subparsers.add_parser("package")
    package_parser.add_argument("--project-path", default=".")
    package_parser.add_argument("--packager", default="auto")
    package_parser.add_argument("--format", dest="package_format", default="wheel")
    package_parser.add_argument("--output-dir")
    package_parser.add_argument("--dry-run", action="store_true")
    package_parser.add_argument("packager_args", nargs="*")

    hooks_parser = subparsers.add_parser("hooks")
    hooks_subparsers = hooks_parser.add_subparsers(dest="hooks_command", required=True)
    hooks_list = hooks_subparsers.add_parser("list")
    hooks_list.add_argument("--project-path", default=".")
    hooks_add = hooks_subparsers.add_parser("add")
    hooks_add.add_argument("event", choices=["pre_build", "post_build", "post_success", "post_failure"])
    hooks_add.add_argument("hook_command")
    hooks_add.add_argument("--project-path", default=".")
    hooks_add.add_argument("--name", default="")
    hooks_add.add_argument("--no-shell", action="store_true")
    hooks_remove = hooks_subparsers.add_parser("remove")
    hooks_remove.add_argument("event", choices=["pre_build", "post_build", "post_success", "post_failure"])
    hooks_remove.add_argument("index", type=int)
    hooks_remove.add_argument("--project-path", default=".")

    version_parser = subparsers.add_parser("version")
    version_subparsers = version_parser.add_subparsers(dest="version_command", required=True)
    version_get = version_subparsers.add_parser("get")
    version_get.add_argument("--project-path", default=".")
    version_set = version_subparsers.add_parser("set")
    version_set.add_argument("version")
    version_set.add_argument("--project-path", default=".")
    version_set.add_argument("--targets", nargs="*", choices=["pyproject", "setup_cfg", "source"])
    version_tag = version_subparsers.add_parser("tag")
    version_tag.add_argument("tag")
    version_tag.add_argument("--project-path", default=".")
    version_tag.add_argument("--message", default="")
    version_tag.add_argument("--push", action="store_true")

    compiler_config_parser = subparsers.add_parser("compiler-config")
    compiler_config_subparsers = compiler_config_parser.add_subparsers(
        dest="compiler_config_command", required=True
    )
    cc_list = compiler_config_subparsers.add_parser("list")
    cc_list.add_argument("--lang", dest="language")

    cc_show = compiler_config_subparsers.add_parser("show")
    cc_show.add_argument("name")
    cc_show.add_argument("--lang", dest="language")

    cc_set = compiler_config_subparsers.add_parser("set")
    cc_set.add_argument("name")
    cc_set.add_argument("--lang", dest="language", required=True)
    cc_set.add_argument("--description", default="")
    cc_set.add_argument("--settings", default="{}")

    cc_delete = compiler_config_subparsers.add_parser("delete")
    cc_delete.add_argument("name")
    cc_delete.add_argument("--lang", dest="language")

    checksums_parser = subparsers.add_parser("checksums")
    checksums_parser.add_argument("artifacts", nargs="*")
    checksums_parser.add_argument("--output-dir", default="dist")

    size_parser = subparsers.add_parser("size")
    size_parser.add_argument("directory", nargs="?", default="dist")
    size_parser.add_argument("--top", dest="top_n", type=int, default=20)

    organize_parser = subparsers.add_parser("organize")
    organize_subparsers = organize_parser.add_subparsers(dest="organize_command", required=True)
    organize_plan = organize_subparsers.add_parser("plan")
    organize_plan.add_argument("target", nargs="?", default=".")
    organize_plan.add_argument("--mode", choices=["copy", "move"], default="copy")
    organize_plan.add_argument("--output")

    organize_apply = organize_subparsers.add_parser("apply")
    organize_apply.add_argument("plan_file")
    organize_apply.add_argument("--force", action="store_true")

    organize_rollback = organize_subparsers.add_parser("rollback")
    organize_rollback.add_argument("manifest_file")
    organize_rollback.add_argument("--force", action="store_true")

    mcp_parser = subparsers.add_parser("mcp")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", required=True)
    mcp_subparsers.add_parser("status")

    mcp_server = mcp_subparsers.add_parser("server")
    mcp_server_subparsers = mcp_server.add_subparsers(dest="server_command", required=True)
    mcp_server_subparsers.add_parser("start")
    mcp_server_subparsers.add_parser("stop")

    mcp_tools = mcp_subparsers.add_parser("tools")
    mcp_tools_subparsers = mcp_tools.add_subparsers(dest="tools_command", required=True)
    mcp_tools_subparsers.add_parser("list")

    mcp_expose = mcp_subparsers.add_parser("expose")
    mcp_expose.add_argument("tool_id")
    mcp_hide = mcp_subparsers.add_parser("hide")
    mcp_hide.add_argument("tool_id")
    mcp_read_only = mcp_subparsers.add_parser("read-only")
    mcp_read_only.add_argument("state", choices=["on", "off"])
    mcp_call = mcp_subparsers.add_parser("call")
    mcp_call.add_argument("tool_id")
    mcp_call.add_argument("--args", default="{}")
    mcp_call.add_argument("--arg", action="append", default=[])

    # Test runner gate commands
    test_parser = subparsers.add_parser("test")
    test_subparsers = test_parser.add_subparsers(dest="test_command", required=True)
    test_run = test_subparsers.add_parser("run")
    test_run.add_argument("--project-path", default=".")
    test_run.add_argument("--command", dest="run_command")

    test_config = test_subparsers.add_parser("config")
    test_config_subparsers = test_config.add_subparsers(dest="test_config_command", required=True)
    test_config_set = test_config_subparsers.add_parser("set")
    test_config_set.add_argument("--project-path", default=".")
    test_config_set.add_argument("--command", dest="command_str", default="pytest")
    test_config_set.add_argument("--gate", action="store_true")
    test_config_get = test_config_subparsers.add_parser("get")
    test_config_get.add_argument("--project-path", default=".")

    # Code signing commands
    sign_parser = subparsers.add_parser("sign")
    sign_parser.add_argument("artifacts", nargs="*")
    sign_parser.add_argument("--project-path", default=".")
    sign_parser.add_argument("--tool")

    signing_config = subparsers.add_parser("signing-config")
    signing_config_subparsers = signing_config.add_subparsers(dest="signing_config_command", required=True)
    signing_set = signing_config_subparsers.add_parser("set")
    signing_set.add_argument("--project-path", default=".")
    signing_set.add_argument("--tool", required=True)
    signing_set.add_argument("--cert", default="")
    signing_set.add_argument("--timestamp-url", default="")
    signing_set.add_argument("--developer-id", default="")
    signing_set.add_argument("--key-id", default="")
    signing_get = signing_config_subparsers.add_parser("get")
    signing_get.add_argument("--project-path", default=".")

    # Dependency audit commands
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--project-path", default=".")
    audit_parser.add_argument("--requirements-file")

    audit_config = subparsers.add_parser("audit-config")
    audit_config_subparsers = audit_config.add_subparsers(dest="audit_config_command", required=True)
    audit_set = audit_config_subparsers.add_parser("set")
    audit_set.add_argument("--project-path", default=".")
    audit_set.add_argument("--gate", action="store_true")
    audit_set.add_argument(
        "--min-severity",
        default="high",
        choices=["critical", "high", "medium", "low", "info"],
    )
    audit_get = audit_config_subparsers.add_parser("get")
    audit_get.add_argument("--project-path", default=".")

    # Asset pipeline commands
    assets_parser = subparsers.add_parser("assets")
    assets_subparsers = assets_parser.add_subparsers(dest="assets_command", required=True)
    assets_prepare = assets_subparsers.add_parser("prepare-icon")
    assets_prepare.add_argument("source_path")
    assets_prepare.add_argument("--platform", choices=["windows", "macos", "linux"], default="windows")
    assets_list = assets_subparsers.add_parser("list")
    assets_list.add_argument("source_path")

    # Container commands
    container_parser = subparsers.add_parser("container")
    container_subparsers = container_parser.add_subparsers(dest="container_command", required=True)
    container_build = container_subparsers.add_parser("build")
    container_build.add_argument("--project-path", default=".")
    container_build.add_argument("--command", dest="build_command", required=True)
    container_build.add_argument("--image")
    container_build.add_argument("--output-dir", default="dist")

    container_config = container_subparsers.add_parser("config")
    container_config_subparsers = container_config.add_subparsers(dest="container_config_command", required=True)
    container_set = container_config_subparsers.add_parser("set")
    container_set.add_argument("--project-path", default=".")
    container_set.add_argument("--image", required=True)
    container_get = container_config_subparsers.add_parser("get")
    container_get.add_argument("--project-path", default=".")

    # Notification commands
    notifications_parser = subparsers.add_parser("notifications")
    notifications_subparsers = notifications_parser.add_subparsers(dest="notifications_command", required=True)
    notifications_set = notifications_subparsers.add_parser("set")
    notifications_set.add_argument("--enabled", type=_parse_bool, default=True)
    notifications_set.add_argument("--webhook-url", default="")
    notifications_subparsers.add_parser("get")

    # Matrix commands
    matrix_parser = subparsers.add_parser("matrix")
    matrix_subparsers = matrix_parser.add_subparsers(dest="matrix_command", required=True)
    matrix_run = matrix_subparsers.add_parser("run")
    matrix_run.add_argument("--project-path", default=".")
    matrix_define = matrix_subparsers.add_parser("define")
    matrix_define.add_argument("--project-path", default=".")
    matrix_define.add_argument("entries")
    matrix_show = matrix_subparsers.add_parser("show")
    matrix_show.add_argument("--project-path", default=".")

    # Sandbox commands
    sandbox_parser = subparsers.add_parser("sandbox")
    sandbox_subparsers = sandbox_parser.add_subparsers(dest="sandbox_command", required=True)
    sandbox_launch = sandbox_subparsers.add_parser("launch")
    sandbox_launch.add_argument("--artifact", dest="artifact_path", required=True)
    sandbox_launch.add_argument("--startup-command")
    sandbox_subparsers.add_parser("available")

    # CI commands
    ci_parser = subparsers.add_parser("ci")
    ci_subparsers = ci_parser.add_subparsers(dest="ci_command", required=True)
    ci_generate = ci_subparsers.add_parser("generate")
    ci_generate.add_argument("--project-path", default=".")
    ci_generate.add_argument("--provider", default="github", choices=["github"])
    ci_generate.add_argument("--profiles", default="[]")
    ci_generate.add_argument("--output-dir")
    ci_export = ci_subparsers.add_parser("export-profile")
    ci_export.add_argument("profile_name")
    ci_export.add_argument("--output")

    # Optional containerized build mode
    build_parser.add_argument("--container", action="store_true")
    build_parser.add_argument("--container-image")

    subparsers.add_parser("ui")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    api = OtterForgeAPI()

    if args.command == "init":
        _print_json(api.get_memory_backend())
        return 0

    if args.command == "set":
        if args.key == "notifications.enabled":
            current = api.get_notification_config()
            _print_json(
                api.set_notification_config(
                    enabled=_parse_bool(args.value),
                    webhook_url=str(current.get("webhook_url", "")),
                )
            )
            return 0
        if args.key == "notifications.webhook_url":
            current = api.get_notification_config()
            _print_json(
                api.set_notification_config(
                    enabled=bool(current.get("enabled", False)),
                    webhook_url=args.value,
                )
            )
            return 0
        if args.key == "build.container_image":
            _print_json(api.set_container_config(".", args.value))
            return 0
        if args.key == "signing.tool":
            current = api.get_signing_config(".")
            _print_json(
                api.set_signing_config(
                    ".",
                    tool=args.value,
                    cert=str(current.get("cert", "")) if isinstance(current, dict) else "",
                    timestamp_url=str(current.get("timestamp_url", "")) if isinstance(current, dict) else "",
                    developer_id=str(current.get("developer_id", "")) if isinstance(current, dict) else "",
                    key_id=str(current.get("key_id", "")) if isinstance(current, dict) else "",
                )
            )
            return 0
        _print_json(api.set_user_setting(args.key, args.value))
        return 0

    if args.command == "get":
        _print_json({args.key: api.get_user_setting(args.key)})
        return 0

    if args.command == "memory":
        if args.memory_command == "show":
            state = api.load_memory()
            _print_json(state if not args.section else {args.section: state.get(args.section)})
            return 0

        if args.memory_command == "clear":
            _print_json(api.clear_memory(args.scope, project_name=args.project_name))
            return 0

        if args.memory_command == "backend":
            if args.backend_command == "show":
                _print_json(api.get_memory_backend())
                return 0
            if args.backend_command == "set":
                _print_json(api.set_memory_backend(args.backend))
                return 0

        if args.memory_command == "migrate":
            _print_json(api.migrate_memory_backend(args.target_backend))
            return 0

    if args.command == "scan":
        include_extensions = args.include_ext.split(",") if args.include_ext else None
        _print_json(
            _run_with_console_progress(
                "Scanning project",
                lambda: api.scan_project(args.path, scope=args.scope, include_extensions=include_extensions),
            )
        )
        return 0

    if args.command == "schema":
        if args.schema_command == "import":
            _print_json(
                _run_with_console_progress(
                    "Importing schema",
                    lambda: api.import_project_schema(args.schema_path),
                )
            )
            return 0
        if args.schema_command == "export":
            scan_result = _run_with_console_progress(
                "Scanning project",
                lambda: api.scan_project(args.path),
            )
            _print_json(
                _run_with_console_progress(
                    "Exporting schema",
                    lambda: api.export_project_schema(scan_result, destination=args.output),
                )
            )
            return 0

    if args.command == "profile":
        if args.profile_command == "create":
            settings = json.loads(args.settings)
            _print_json(api.create_profile(args.name, settings=settings, description=args.description))
            return 0
        if args.profile_command == "list":
            _print_json(api.list_profiles())
            return 0
        if args.profile_command == "show":
            _print_json(api.show_profile(args.name))
            return 0

    if args.command == "builders":
        if args.builders_command == "list":
            _print_json(api.list_builders())
            return 0
        if args.builders_command == "inspect":
            _print_json(api.inspect_builder(args.name))
            return 0

    if args.command == "packagers":
        if args.packagers_command == "list":
            _print_json(api.list_packagers())
            return 0
        if args.packagers_command == "inspect":
            _print_json(api.inspect_packager(args.name))
            return 0

    if args.command == "installers":
        if args.installers_command == "list":
            _print_json(api.list_installers())
            return 0
        if args.installers_command == "inspect":
            _print_json(api.inspect_installer(args.name))
            return 0

    if args.command == "installer":
        payload = {
            "project_path": args.project_path,
            "installer_name": args.installer_name,
            "source_artifacts": args.source_artifacts,
            "application_name": args.application_name,
            "version": args.installer_version,
            "vendor": args.vendor,
            "install_root": args.install_root,
            "license_file": args.license_file,
            "output_dir": args.output_dir,
            "dry_run": args.dry_run,
            "raw_installer_args": args.installer_args,
        }
        _print_json(
            _run_with_console_progress(
                "Running installer",
                lambda: api.run_installer(payload),
            )
        )
        return 0

    if args.command == "plugins":
        if args.plugins_command == "list":
            _print_json(api.list_plugins())
            return 0
        if args.plugins_command == "discover":
            _print_json(api.discover_plugins())
            return 0
        if args.plugins_command == "install":
            _print_json(api.install_plugin(args.source_path))
            return 0
        if args.plugins_command == "remove":
            _print_json(api.remove_plugin(args.name))
            return 0

    if args.command == "obfuscators":
        if args.obfuscators_command == "list":
            _print_json(api.list_obfuscators())
            return 0
        if args.obfuscators_command == "inspect":
            _print_json(api.inspect_obfuscator(args.name))
            return 0

    if args.command == "toolchain":
        if args.toolchain_command == "list":
            _print_json(api.list_toolchain())
            return 0
        if args.toolchain_command == "doctor":
            _print_json(api.doctor_toolchain())
            return 0
        if args.toolchain_command == "packs":
            if args.toolchain_packs_command == "list":
                _print_json(api.list_language_packs())
                return 0
            if args.toolchain_packs_command == "install":
                _print_json(
                    _run_with_console_progress(
                        "Installing language pack" if args.execute else "Planning language pack install",
                        lambda: api.install_language_pack(
                            args.pack_id,
                            manager=args.manager,
                            os_name=args.os_name,
                            execute=args.execute,
                            continue_on_error=args.continue_on_error,
                        ),
                    )
                )
                return 0
            if args.toolchain_packs_command == "add":
                managers = json.loads(args.managers_json)
                imports = json.loads(args.imports_json)
                detectors = json.loads(args.detectors_json)
                _print_json(
                    api.add_language_pack(
                        pack_id=args.pack_id,
                        name=args.name,
                        description=args.description,
                        managers=managers,
                        third_party_imports=imports,
                        detectors=detectors,
                    )
                )
                return 0
            if args.toolchain_packs_command == "remove":
                _print_json(api.remove_language_pack(args.pack_id))
                return 0
        if args.toolchain_command == "packages":
            if args.toolchain_packages_command == "managers":
                _print_json(api.list_package_managers(os_name=args.os_name))
                return 0
            if args.toolchain_packages_command == "search":
                _print_json(
                    _run_with_console_progress(
                        "Searching packages",
                        lambda: api.search_packages(
                            query=args.query,
                            manager=args.manager,
                            os_name=args.os_name,
                            limit=args.limit,
                        ),
                    )
                )
                return 0
            if args.toolchain_packages_command == "install":
                results = _run_with_console_progress(
                    "Installing packages" if args.execute else "Planning package installs",
                    lambda: [
                        api.install_package(
                            package_name=package_name,
                            manager=args.manager,
                            os_name=args.os_name,
                            execute=args.execute,
                        )
                        for package_name in args.packages
                    ],
                )
                _print_json(
                    {
                        "operation": "install",
                        "executed": args.execute,
                        "count": len(results),
                        "results": results,
                    }
                )
                return 0
            if args.toolchain_packages_command == "uninstall":
                results = _run_with_console_progress(
                    "Uninstalling packages" if args.execute else "Planning package uninstalls",
                    lambda: [
                        api.uninstall_package(
                            package_name=package_name,
                            manager=args.manager,
                            os_name=args.os_name,
                            execute=args.execute,
                        )
                        for package_name in args.packages
                    ],
                )
                _print_json(
                    {
                        "operation": "uninstall",
                        "executed": args.execute,
                        "count": len(results),
                        "results": results,
                    }
                )
                return 0
        if args.toolchain_command == "deps":
            if args.toolchain_deps_command == "analyze":
                _print_json(
                    _run_with_console_progress(
                        "Analyzing dependencies",
                        lambda: api.list_modules(args.path),
                    )
                )
                return 0
            if args.toolchain_deps_command == "install-missing":
                analysis = _run_with_console_progress(
                    "Analyzing dependencies",
                    lambda: api.list_modules(args.path),
                )
                missing = list(analysis.get("missing_dependencies", []))
                results = _run_with_console_progress(
                    "Installing missing dependencies" if args.execute else "Planning missing dependency installs",
                    lambda: [
                        api.install_package(
                            package_name=str(name),
                            manager=args.manager,
                            os_name=args.os_name,
                            execute=args.execute,
                        )
                        for name in missing
                    ],
                )
                _print_json(
                    {
                        "path": str(Path(args.path).resolve()),
                        "missing_dependencies": missing,
                        "operation": "install-missing",
                        "executed": args.execute,
                        "count": len(results),
                        "results": results,
                    }
                )
                return 0

    if args.command == "modules":
        if args.modules_command == "list":
            _print_json(api.list_modules(args.path))
            return 0

    if args.command == "manifest":
        if args.manifest_command == "show":
            _print_json(api.show_manifest())
            return 0
        if args.manifest_command == "refresh":
            _print_json(api.refresh_manifest())
            return 0
        if args.manifest_command == "enable":
            _print_json(api.enable_manifest_capability(args.capability_id))
            return 0
        if args.manifest_command == "disable":
            _print_json(api.disable_manifest_capability(args.capability_id))
            return 0

    if args.command == "obfuscate":
        payload = {
            "project_path": args.project_path,
            "tool_name": args.tool,
            "source_path": args.source,
            "output_dir": args.output_dir,
            "recursive": not args.no_recursive,
            "dry_run": args.dry_run,
            "raw_tool_args": args.tool_args,
        }
        _print_json(api.run_obfuscation(payload))
        return 0

    if args.command == "compiler-config":
        if args.compiler_config_command == "list":
            _print_json(api.list_compiler_configs(language=getattr(args, "language", None)))
            return 0
        if args.compiler_config_command == "show":
            _print_json(api.show_compiler_config(args.name, language=getattr(args, "language", None)))
            return 0
        if args.compiler_config_command == "set":
            try:
                settings = json.loads(args.settings)
            except json.JSONDecodeError as exc:
                parser.exit(status=2, message=f"Invalid JSON for --settings: {exc}\n")
            _print_json(
                api.set_compiler_config(
                    args.name,
                    language=args.language,
                    settings=settings,
                    description=args.description,
                )
            )
            return 0
        if args.compiler_config_command == "delete":
            _print_json(api.delete_compiler_config(args.name, language=getattr(args, "language", None)))
            return 0

    if args.command == "checksums":
        _print_json(api.generate_checksums(args.artifacts, output_dir=args.output_dir))
        return 0

    if args.command == "size":
        _print_json(api.analyse_size(args.directory, top_n=args.top_n))
        return 0

    if args.command == "build":
        console_mode = True
        if args.noconsole:
            console_mode = False
        elif args.console:
            console_mode = True

        mode = "onefile"
        if args.onedir:
            mode = "onedir"

        payload = {
            "project_path": args.project_path,
            "builder_name": args.builder,
            "language": args.language,
            "entry_script": args.entry,
            "source_files": args.source_files,
            "executable_name": args.name,
            "mode": mode,
            "console_mode": console_mode,
            "icon_path": args.icon,
            "splash_path": args.splash,
            "output_dir": args.output_dir,
            "compiler": args.compiler,
            "standard": args.standard,
            "optimization": args.optimization,
            "debug_symbols": args.debug_symbols,
            "include_paths": args.include_paths,
            "library_paths": args.library_paths,
            "libraries": args.libraries,
            "compiler_config_name": args.compiler_config_name,
            "clean": args.clean,
            "dry_run": args.dry_run,
            "raw_builder_args": args.builder_args,
        }

        if args.container:
            request = BuildRequest.from_dict(payload)
            build_command = shlex.join(api.command_translator.translate(request))
            _print_json(
                _run_with_console_progress(
                    "Running containerized build",
                    lambda: api.run_container_build(
                        args.project_path,
                        build_command=build_command,
                        image=args.container_image,
                        output_dir=args.output_dir or "dist",
                    ),
                )
            )
            return 0

        _print_json(_run_with_console_progress("Running build", lambda: api.run_build(payload)))
        return 0

    if args.command == "package":
        payload = {
            "project_path": args.project_path,
            "packager_name": args.packager,
            "package_format": args.package_format,
            "output_dir": args.output_dir,
            "dry_run": args.dry_run,
            "raw_packager_args": args.packager_args,
        }
        _print_json(_run_with_console_progress("Running package", lambda: api.run_package(payload)))
        return 0

    if args.command == "hooks":
        if args.hooks_command == "list":
            _print_json(api.list_hooks(args.project_path))
            return 0
        if args.hooks_command == "add":
            _print_json(
                api.add_hook(
                    args.project_path,
                    event=args.event,
                    command=args.hook_command,
                    name=args.name,
                    shell=not args.no_shell,
                )
            )
            return 0
        if args.hooks_command == "remove":
            _print_json(api.remove_hook(args.project_path, args.event, args.index))
            return 0

    if args.command == "version":
        if args.version_command == "get":
            _print_json(api.get_version(args.project_path))
            return 0
        if args.version_command == "set":
            _print_json(api.set_version(args.project_path, args.version, targets=args.targets))
            return 0
        if args.version_command == "tag":
            _print_json(
                api.create_git_tag(
                    args.project_path,
                    args.tag,
                    message=args.message,
                    push=args.push,
                )
            )
            return 0

    if args.command == "organize":
        if args.organize_command == "plan":
            plan = _run_with_console_progress(
                "Creating organization plan",
                lambda: api.create_organization_plan(args.target, mode=args.mode),
            )
            if args.output:
                saved_path = api.save_organization_plan(plan, args.output)
                plan = {**plan, "saved_to": str(Path(saved_path).resolve())}
            _print_json(plan)
            return 0

        if args.organize_command == "apply":
            _print_json(
                _run_with_console_progress(
                    "Applying organization plan",
                    lambda: api.apply_organization_plan(args.plan_file, force=args.force),
                )
            )
            return 0

        if args.organize_command == "rollback":
            _print_json(
                _run_with_console_progress(
                    "Rolling back organization",
                    lambda: api.rollback_organization(args.manifest_file, force=args.force),
                )
            )
            return 0

    if args.command == "mcp":
        if args.mcp_command == "status":
            _print_json(api.get_mcp_status())
            return 0
        if args.mcp_command == "server":
            if args.server_command == "start":
                _print_json(
                    _run_with_console_progress(
                        "Starting MCP server",
                        lambda: api.start_mcp_server(),
                    )
                )
                return 0
            if args.server_command == "stop":
                _print_json(
                    _run_with_console_progress(
                        "Stopping MCP server",
                        lambda: api.stop_mcp_server(),
                    )
                )
                return 0
        if args.mcp_command == "tools" and args.tools_command == "list":
            _print_json(api.list_mcp_tools())
            return 0
        if args.mcp_command == "expose":
            _print_json(api.set_mcp_tool_visibility(args.tool_id, True))
            return 0
        if args.mcp_command == "hide":
            _print_json(api.set_mcp_tool_visibility(args.tool_id, False))
            return 0
        if args.mcp_command == "read-only":
            _print_json(api.set_mcp_read_only(args.state == "on"))
            return 0
        if args.mcp_command == "call":
            call_args: dict[str, Any] = {}

            try:
                parsed_args = json.loads(args.args)
            except json.JSONDecodeError as exc:
                parser.exit(status=2, message=f"Invalid JSON for --args: {exc}\n")

            if not isinstance(parsed_args, dict):
                parser.exit(status=2, message="--args must be a JSON object\n")

            call_args.update(parsed_args)

            for item in args.arg:
                if "=" not in item:
                    parser.exit(status=2, message=f"Invalid --arg '{item}'. Expected key=value format.\n")
                key, raw_value = item.split("=", 1)
                key = key.strip()
                if not key:
                    parser.exit(status=2, message=f"Invalid --arg '{item}'. Key cannot be empty.\n")
                raw_value = raw_value.strip()
                try:
                    parsed_value = json.loads(raw_value)
                except json.JSONDecodeError:
                    parsed_value = raw_value
                call_args[key] = parsed_value

            try:
                _print_json(api.execute_mcp_tool(args.tool_id, call_args))
            except (RuntimeError, PermissionError, KeyError, NotImplementedError, TypeError, ValueError) as exc:
                parser.exit(status=1, message=f"MCP call failed: {exc}\n")
            return 0

    if args.command == "test":
        if args.test_command == "run":
            _print_json(
                _run_with_console_progress(
                    "Running tests",
                    lambda: api.run_tests(args.project_path, command=args.run_command),
                )
            )
            return 0
        if args.test_command == "config":
            if args.test_config_command == "set":
                _print_json(api.set_test_config(args.project_path, command=args.command_str, gate_enabled=args.gate))
                return 0
            if args.test_config_command == "get":
                _print_json(api.get_test_config(args.project_path))
                return 0

    if args.command == "sign":
        _print_json(
            _run_with_console_progress(
                "Signing artifacts",
                lambda: api.sign_artifacts(args.project_path, args.artifacts, tool=args.tool),
            )
        )
        return 0

    if args.command == "signing-config":
        if args.signing_config_command == "set":
            _print_json(
                api.set_signing_config(
                    args.project_path,
                    tool=args.tool,
                    cert=args.cert,
                    timestamp_url=args.timestamp_url,
                    developer_id=args.developer_id,
                    key_id=args.key_id,
                )
            )
            return 0
        if args.signing_config_command == "get":
            _print_json(api.get_signing_config(args.project_path))
            return 0

    if args.command == "audit":
        _print_json(
            _run_with_console_progress(
                "Running audit",
                lambda: api.run_audit(args.project_path, requirements_file=args.requirements_file),
            )
        )
        return 0

    if args.command == "audit-config":
        if args.audit_config_command == "set":
            _print_json(api.set_audit_config(args.project_path, gate_enabled=args.gate, min_severity=args.min_severity))
            return 0
        if args.audit_config_command == "get":
            _print_json(api.get_audit_config(args.project_path))
            return 0

    if args.command == "assets":
        if args.assets_command == "prepare-icon":
            _print_json(
                _run_with_console_progress(
                    "Preparing icon",
                    lambda: api.prepare_icon(args.source_path, target_platform=args.platform),
                )
            )
            return 0
        if args.assets_command == "list":
            _print_json(api.list_assets(args.source_path))
            return 0

    if args.command == "container":
        if args.container_command == "build":
            _print_json(
                _run_with_console_progress(
                    "Running container build",
                    lambda: api.run_container_build(
                        args.project_path,
                        build_command=args.build_command,
                        image=args.image,
                        output_dir=args.output_dir,
                    ),
                )
            )
            return 0
        if args.container_command == "config":
            if args.container_config_command == "set":
                _print_json(api.set_container_config(args.project_path, image=args.image))
                return 0
            if args.container_config_command == "get":
                _print_json(api.get_container_config(args.project_path))
                return 0

    if args.command == "notifications":
        if args.notifications_command == "set":
            _print_json(api.set_notification_config(enabled=args.enabled, webhook_url=args.webhook_url))
            return 0
        if args.notifications_command == "get":
            _print_json(api.get_notification_config())
            return 0

    if args.command == "matrix":
        if args.matrix_command == "run":
            _print_json(
                _run_with_console_progress(
                    "Running matrix",
                    lambda: api.run_matrix(args.project_path),
                )
            )
            return 0
        if args.matrix_command == "define":
            try:
                entries = json.loads(args.entries)
            except json.JSONDecodeError as exc:
                parser.exit(status=2, message=f"Invalid JSON for entries: {exc}\n")
            _print_json(api.define_matrix(args.project_path, entries))
            return 0
        if args.matrix_command == "show":
            _print_json(api.get_matrix(args.project_path))
            return 0

    if args.command == "sandbox":
        if args.sandbox_command == "launch":
            _print_json(
                _run_with_console_progress(
                    "Launching sandbox",
                    lambda: api.launch_sandbox(args.artifact_path, startup_command=args.startup_command),
                )
            )
            return 0
        if args.sandbox_command == "available":
            _print_json({"available": api.sandbox_launcher.is_available()})
            return 0

    if args.command == "ci":
        if args.ci_command == "generate":
            try:
                profiles = json.loads(args.profiles)
            except json.JSONDecodeError as exc:
                parser.exit(status=2, message=f"Invalid JSON for --profiles: {exc}\n")
            out_path = None
            if args.output_dir:
                out_path = Path(args.output_dir) / "otterforge.yml"
            _print_json(
                _run_with_console_progress(
                    "Generating CI workflow",
                    lambda: api.generate_ci_workflow(args.project_path, profiles, output_path=out_path),
                )
            )
            return 0
        if args.ci_command == "export-profile":
            _print_json(api.export_profile_config(args.profile_name, output_path=args.output))
            return 0

    if args.command == "ui":
        try:
            return int(launch_ui())
        except RuntimeError as exc:
            parser.exit(status=1, message=f"{exc}\n")

    parser.error("Unsupported command")
    return 2