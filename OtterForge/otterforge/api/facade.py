from __future__ import annotations

import shlex
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from otterforge.models.build_request import BuildRequest
from otterforge.models.installer_request import InstallerRequest
from otterforge.models.obfuscation_request import ObfuscationRequest
from otterforge.models.package_request import PackageRequest
from otterforge.mcp.server import MCPServer
from otterforge.services.build_runner import BuildRunner
from otterforge.services.command_translator import CommandTranslator
from otterforge.services.compiler_config_service import CompilerConfigService
from otterforge.services.hook_runner import HookRunner
from otterforge.services.manifest_service import ManifestService
from otterforge.services.memory_backend_manager import MemoryBackendManager
from otterforge.services.module_service import ModuleService
from otterforge.services.obfuscation_runner import ObfuscationRunner
from otterforge.services.package_runner import PackageRunner
from otterforge.services.profile_service import ProfileService
from otterforge.services.project_scanner import ProjectScanner
from otterforge.services.project_organizer import ProjectOrganizer
from otterforge.services.schema_service import SchemaService
from otterforge.services.toolchain_service import ToolchainService
from otterforge.services.installer_runner import InstallerRunner
from otterforge.services.version_resolver import VersionResolver
from otterforge.services.checksum_service import ChecksumService
from otterforge.services.size_analyzer import SizeAnalyzer
from otterforge.packagers.registry import PackagerRegistry
from otterforge.installers.registry import InstallerRegistry
from otterforge.plugins.loader import PluginLoader
from otterforge.services.test_runner_gate import TestRunnerGate
from otterforge.services.signing_service import SigningService
from otterforge.services.dependency_auditor import DependencyAuditor
from otterforge.services.asset_pipeline import AssetPipeline
from otterforge.services.container_runner import ContainerRunner
from otterforge.services.notification_service import NotificationService
from otterforge.services.matrix_runner import MatrixRunner
from otterforge.services.sandbox_launcher import SandboxLauncher
from otterforge.services.ci_generator import CIGenerator


class OtterForgeAPI:
    CUSTOM_LANGUAGE_PACKS_SETTING = "custom_language_packs"

    def __init__(self, project_root: Path | str | None = None) -> None:
        self.backend_manager = MemoryBackendManager(project_root)
        self.mcp_server = MCPServer(self.backend_manager)
        self.project_scanner = ProjectScanner()
        self.schema_service = SchemaService()
        self.profile_service = ProfileService()
        self.command_translator = CommandTranslator()
        self.build_runner = BuildRunner(self.command_translator)
        self.obfuscation_runner = ObfuscationRunner()
        self.compiler_config_service = CompilerConfigService()
        self.module_service = ModuleService()
        self.toolchain_service = ToolchainService()
        self.manifest_service = ManifestService(self.backend_manager.data_dir / "otterforge.manifest.json")
        self.project_organizer = ProjectOrganizer(self.backend_manager.data_dir / "organization")
        self.package_runner = PackageRunner(PackagerRegistry())
        self.hook_runner = HookRunner(self.backend_manager.read_memory())
        self.version_resolver = VersionResolver()
        self.installer_runner = InstallerRunner()
        self._installer_registry = InstallerRegistry()
        self.plugin_loader = PluginLoader()
        self.checksum_service = ChecksumService()
        self.size_analyzer = SizeAnalyzer()
        self.test_runner_gate = TestRunnerGate()
        self.signing_service = SigningService()
        self.dependency_auditor = DependencyAuditor()
        self.asset_pipeline = AssetPipeline()
        self.container_runner = ContainerRunner()
        self.notification_service = NotificationService()
        self.matrix_runner = MatrixRunner()
        self.sandbox_launcher = SandboxLauncher()
        self.ci_generator = CIGenerator()
        self._register_mcp_handlers()

    def _register_mcp_handlers(self) -> None:
        self.mcp_server.register_tool_handler(
            "scan_project",
            lambda args: self.scan_project(
                args.get("path", "."),
                scope=str(args.get("scope", "projects")),
                include_extensions=args.get("include_extensions"),
            ),
        )
        self.mcp_server.register_tool_handler("list_builders", lambda args: self.list_builders())
        self.mcp_server.register_tool_handler(
            "inspect_builder",
            lambda args: self.inspect_builder(str(args["name"])),
        )
        self.mcp_server.register_tool_handler(
            "list_obfuscators",
            lambda args: self.list_obfuscators(),
        )
        self.mcp_server.register_tool_handler(
            "inspect_obfuscator",
            lambda args: self.inspect_obfuscator(str(args["name"])),
        )
        self.mcp_server.register_tool_handler(
            "run_obfuscation",
            lambda args: self.run_obfuscation(args),
        )
        self.mcp_server.register_tool_handler(
            "list_modules",
            lambda args: self.list_modules(args.get("path", ".")),
        )
        self.mcp_server.register_tool_handler(
            "doctor_toolchain",
            lambda args: self.doctor_toolchain(),
        )
        self.mcp_server.register_tool_handler(
            "list_language_packs",
            lambda args: self.list_language_packs(),
        )
        self.mcp_server.register_tool_handler(
            "install_language_pack",
            lambda args: self.install_language_pack(
                str(args["pack_id"]),
                manager=args.get("manager"),
                os_name=args.get("os_name"),
                execute=bool(args.get("execute", False)),
                continue_on_error=bool(args.get("continue_on_error", False)),
            ),
        )
        self.mcp_server.register_tool_handler(
            "install_uv",
            lambda args: self.install_uv(
                os_name=args.get("os_name"),
                execute=bool(args.get("execute", False)),
            ),
        )
        self.mcp_server.register_tool_handler(
            "list_integration_tools",
            lambda args: self.list_integration_tools(os_name=args.get("os_name")),
        )
        self.mcp_server.register_tool_handler(
            "install_integration_tool",
            lambda args: self.install_integration_tool(
                tool_id=str(args["tool_id"]),
                manager=args.get("manager"),
                os_name=args.get("os_name"),
                execute=bool(args.get("execute", False)),
            ),
        )
        self.mcp_server.register_tool_handler("show_manifest", lambda args: self.show_manifest())
        self.mcp_server.register_tool_handler("refresh_manifest", lambda args: self.refresh_manifest())
        self.mcp_server.register_tool_handler(
            "enable_manifest_capability",
            lambda args: self.enable_manifest_capability(str(args["capability_id"])),
        )
        self.mcp_server.register_tool_handler(
            "disable_manifest_capability",
            lambda args: self.disable_manifest_capability(str(args["capability_id"])),
        )
        self.mcp_server.register_tool_handler(
            "list_compiler_configs",
            lambda args: self.list_compiler_configs(language=args.get("language")),
        )
        self.mcp_server.register_tool_handler(
            "show_compiler_config",
            lambda args: self.show_compiler_config(
                str(args["name"]),
                language=args.get("language"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "set_compiler_config",
            lambda args: self.set_compiler_config(
                str(args["name"]),
                language=str(args["language"]),
                settings=dict(args.get("settings", {})),
                description=str(args.get("description", "")),
            ),
        )
        self.mcp_server.register_tool_handler(
            "delete_compiler_config",
            lambda args: self.delete_compiler_config(
                str(args["name"]),
                language=args.get("language"),
            ),
        )
        self.mcp_server.register_tool_handler("list_profiles", lambda args: self.list_profiles())
        self.mcp_server.register_tool_handler(
            "show_profile",
            lambda args: self.show_profile(str(args["name"])),
        )
        self.mcp_server.register_tool_handler(
            "create_profile",
            lambda args: self.create_profile(
                str(args["name"]),
                settings=dict(args.get("settings", {})),
                description=str(args.get("description", "")),
            ),
        )
        self.mcp_server.register_tool_handler(
            "create_organization_plan",
            lambda args: self.create_organization_plan(
                str(args.get("target", ".")),
                mode=str(args.get("mode", "copy")),
            ),
        )
        self.mcp_server.register_tool_handler(
            "apply_organization_plan",
            lambda args: self.apply_organization_plan(
                str(args["plan_path"]),
                force=bool(args.get("force", False)),
            ),
        )
        self.mcp_server.register_tool_handler(
            "rollback_organization",
            lambda args: self.rollback_organization(
                str(args["manifest_path"]),
                force=bool(args.get("force", False)),
            ),
        )
        self.mcp_server.register_tool_handler(
            "import_project_schema",
            lambda args: self.import_project_schema(str(args["schema_path"])),
        )
        self.mcp_server.register_tool_handler(
            "export_project_schema",
            lambda args: self.export_project_schema(
                self.scan_project(str(args.get("path", "."))),
                destination=args.get("destination"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "list_artifacts",
            lambda args: self.list_artifacts(str(args["project"])),
        )
        self.mcp_server.register_tool_handler(
            "get_build_history",
            lambda args: self.get_build_history(args.get("project")),
        )
        self.mcp_server.register_tool_handler(
            "run_build",
            lambda args: self.run_build(args),
        )
        self.mcp_server.register_tool_handler("load_memory", lambda args: self.load_memory())
        self.mcp_server.register_tool_handler(
            "get_memory_backend",
            lambda args: self.get_memory_backend(),
        )
        self.mcp_server.register_tool_handler(
            "set_memory_backend",
            lambda args: self.set_memory_backend(
                str(args["backend"]),
                config=args.get("config"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "migrate_memory_backend",
            lambda args: self.migrate_memory_backend(str(args["target_backend"])),
        )
        self.mcp_server.register_tool_handler(
            "set_mcp_read_only",
            lambda args: self.set_mcp_read_only(bool(args["enabled"])),
        )
        self.mcp_server.register_tool_handler("get_mcp_status", lambda args: self.get_mcp_status())
        self.mcp_server.register_tool_handler("list_mcp_tools", lambda args: self.list_mcp_tools())

        # Packager handlers
        self.mcp_server.register_tool_handler("list_packagers", lambda args: self.list_packagers())
        self.mcp_server.register_tool_handler(
            "inspect_packager",
            lambda args: self.inspect_packager(str(args["name"])),
        )
        self.mcp_server.register_tool_handler(
            "run_package",
            lambda args: self.run_package(args),
        )
        # Hook handlers
        self.mcp_server.register_tool_handler(
            "list_hooks",
            lambda args: self.list_hooks(str(args.get("project_path", "."))),
        )
        self.mcp_server.register_tool_handler(
            "add_hook",
            lambda args: self.add_hook(
                str(args["project_path"]),
                event=str(args["event"]),
                command=str(args["command"]),
                name=str(args.get("name", "")),
                shell=bool(args.get("shell", True)),
            ),
        )
        self.mcp_server.register_tool_handler(
            "remove_hook",
            lambda args: self.remove_hook(
                str(args["project_path"]),
                event=str(args["event"]),
                index=int(args["index"]),
            ),
        )
        # Version handlers
        self.mcp_server.register_tool_handler(
            "get_version",
            lambda args: self.get_version(str(args.get("project_path", "."))),
        )
        self.mcp_server.register_tool_handler(
            "set_version",
            lambda args: self.set_version(
                str(args["project_path"]),
                new_version=str(args["version"]),
                targets=args.get("targets"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "create_git_tag",
            lambda args: self.create_git_tag(
                str(args["project_path"]),
                tag=str(args["tag"]),
                message=str(args.get("message", "")),
                push=bool(args.get("push", False)),
            ),
        )
        # Installer handlers
        self.mcp_server.register_tool_handler("list_installers", lambda args: self.list_installers())
        self.mcp_server.register_tool_handler(
            "inspect_installer",
            lambda args: self.inspect_installer(str(args["name"])),
        )
        self.mcp_server.register_tool_handler(
            "run_installer",
            lambda args: self.run_installer(args),
        )
        # Plugin handlers
        self.mcp_server.register_tool_handler("list_plugins", lambda args: self.list_plugins())
        self.mcp_server.register_tool_handler(
            "install_plugin",
            lambda args: self.install_plugin(str(args["source_path"])),
        )
        self.mcp_server.register_tool_handler(
            "remove_plugin",
            lambda args: self.remove_plugin(str(args["name"])),
        )
        # Checksum + size handlers
        self.mcp_server.register_tool_handler(
            "generate_checksums",
            lambda args: self.generate_checksums(
                args.get("artifact_paths", []),
                output_dir=str(args.get("output_dir", "dist")),
                metadata=args.get("metadata"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "analyse_size",
            lambda args: self.analyse_size(
                str(args.get("directory", "dist")),
                top_n=int(args.get("top_n", 20)),
            ),
        )
        # Test runner handlers
        self.mcp_server.register_tool_handler(
            "run_tests",
            lambda args: self.run_tests(
                str(args.get("project_path", ".")),
                command=args.get("command"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "set_test_config",
            lambda args: self.set_test_config(
                str(args["project_path"]),
                command=str(args.get("command", "pytest")),
                gate_enabled=bool(args.get("gate_enabled", False)),
            ),
        )
        self.mcp_server.register_tool_handler(
            "get_test_config",
            lambda args: self.get_test_config(str(args["project_path"])),
        )
        # Signing handlers
        self.mcp_server.register_tool_handler(
            "sign_artifacts",
            lambda args: self.sign_artifacts(
                str(args["project_path"]),
                artifact_paths=list(args.get("artifact_paths", [])),
                tool=args.get("tool"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "set_signing_config",
            lambda args: self.set_signing_config(
                str(args["project_path"]),
                tool=str(args["tool"]),
                cert=str(args.get("cert", "")),
                timestamp_url=str(args.get("timestamp_url", "")),
                developer_id=str(args.get("developer_id", "")),
                key_id=str(args.get("key_id", "")),
            ),
        )
        self.mcp_server.register_tool_handler(
            "get_signing_config",
            lambda args: self.get_signing_config(str(args["project_path"])),
        )
        # Audit handlers
        self.mcp_server.register_tool_handler(
            "run_audit",
            lambda args: self.run_audit(
                str(args.get("project_path", ".")),
                requirements_file=args.get("requirements_file"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "set_audit_config",
            lambda args: self.set_audit_config(
                str(args["project_path"]),
                gate_enabled=bool(args.get("gate_enabled", False)),
                min_severity=str(args.get("min_severity", "high")),
            ),
        )
        self.mcp_server.register_tool_handler(
            "get_audit_config",
            lambda args: self.get_audit_config(str(args["project_path"])),
        )
        # Asset pipeline handlers
        self.mcp_server.register_tool_handler(
            "prepare_icon",
            lambda args: self.prepare_icon(
                str(args["source_path"]),
                target_platform=str(args.get("platform", "windows")),
            ),
        )
        self.mcp_server.register_tool_handler(
            "list_assets",
            lambda args: self.list_assets(str(args["source_path"])),
        )
        # Container handlers
        self.mcp_server.register_tool_handler(
            "run_container_build",
            lambda args: self.run_container_build(
                str(args.get("project_path", ".")),
                build_command=str(args.get("build_command", "")),
                image=args.get("image"),
                output_dir=str(args.get("output_dir", "dist")),
            ),
        )
        self.mcp_server.register_tool_handler(
            "set_container_config",
            lambda args: self.set_container_config(
                str(args["project_path"]),
                image=str(args["image"]),
            ),
        )
        self.mcp_server.register_tool_handler(
            "get_container_config",
            lambda args: self.get_container_config(str(args["project_path"])),
        )
        # Notification handlers
        self.mcp_server.register_tool_handler(
            "send_notification",
            lambda args: self.notification_service.notify(
                title=str(args.get("title", "")),
                message=str(args.get("message", "")),
                success=bool(args.get("success", True)),
            ),
        )
        self.mcp_server.register_tool_handler(
            "set_notification_config",
            lambda args: self.set_notification_config(
                enabled=bool(args.get("enabled", True)),
                webhook_url=str(args.get("webhook_url", "")),
            ),
        )
        # Matrix handlers
        self.mcp_server.register_tool_handler(
            "run_matrix",
            lambda args: self.run_matrix(
                str(args.get("project_path", ".")),
                entries=args.get("entries"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "define_matrix",
            lambda args: self.define_matrix(
                str(args["project_path"]),
                entries=list(args.get("entries", [])),
            ),
        )
        self.mcp_server.register_tool_handler(
            "get_matrix",
            lambda args: self.get_matrix(str(args["project_path"])),
        )
        # Sandbox handlers
        self.mcp_server.register_tool_handler(
            "launch_sandbox",
            lambda args: self.launch_sandbox(
                str(args["artifact_path"]),
                startup_command=args.get("startup_command"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "check_sandbox_available",
            lambda args: {"available": self.sandbox_launcher.is_available()},
        )
        # CI handlers
        self.mcp_server.register_tool_handler(
            "generate_ci_workflow",
            lambda args: self.generate_ci_workflow(
                str(args.get("project_path", ".")),
                profiles=list(args.get("profiles", [])),
                output_path=args.get("output_path"),
            ),
        )
        self.mcp_server.register_tool_handler(
            "export_profile_config",
            lambda args: self.export_profile_config(
                str(args["profile_name"]),
                output_path=args.get("output_path"),
            ),
        )

    def discover_project(self, path: str | Path) -> dict[str, Any]:
        project_path = Path(path).resolve()
        return {
            "path": str(project_path),
            "exists": project_path.exists(),
            "children": sorted(item.name for item in project_path.iterdir()) if project_path.exists() else [],
        }

    def list_builders(self) -> list[dict[str, str]]:
        return self.command_translator.list_builders()

    def inspect_builder(self, name: str) -> dict[str, Any]:
        return self.command_translator.inspect_builder(name)

    def list_obfuscators(self) -> list[dict[str, Any]]:
        return self.obfuscation_runner.registry.list_obfuscators()

    def inspect_obfuscator(self, name: str) -> dict[str, Any]:
        return self.obfuscation_runner.registry.inspect(name)

    def list_modules(self, path: str | Path = ".") -> dict[str, Any]:
        return self.module_service.list_modules(path)

    def list_toolchain(self) -> dict[str, Any]:
        builders = self.list_builders()
        obfuscators = self.list_obfuscators()
        integrations = self.toolchain_service.list_integration_tools()
        return self.toolchain_service.build_toolchain_report(
            builders,
            obfuscators,
            integration_tools=integrations,
        )

    def doctor_toolchain(self) -> dict[str, Any]:
        report = self.list_toolchain()
        return {
            "summary": report["summary"],
            "missing": report["missing"],
        }

    def _get_custom_language_packs(self) -> dict[str, dict[str, Any]]:
        state = self.backend_manager.read_memory()
        raw = state.get("user_settings", {}).get(self.CUSTOM_LANGUAGE_PACKS_SETTING, {})
        if not isinstance(raw, dict):
            return {}

        normalized: dict[str, dict[str, Any]] = {}
        for pack_id, payload in raw.items():
            normalized_id = str(pack_id).strip().lower()
            if not normalized_id:
                continue
            if isinstance(payload, dict):
                normalized[normalized_id] = dict(payload)
        return normalized

    def _save_custom_language_packs(self, custom_packs: dict[str, dict[str, Any]]) -> None:
        state = self.backend_manager.read_memory()
        user_settings = state.get("user_settings", {})
        if not isinstance(user_settings, dict):
            user_settings = {}
            state["user_settings"] = user_settings
        user_settings[self.CUSTOM_LANGUAGE_PACKS_SETTING] = custom_packs
        self.save_memory(state)

    def add_language_pack(
        self,
        pack_id: str,
        name: str,
        description: str,
        managers: dict[str, dict[str, list[str]]],
        third_party_imports: list[dict[str, Any]] | None = None,
        detectors: dict[str, list[Any]] | None = None,
    ) -> dict[str, Any]:
        normalized_pack = pack_id.strip().lower()
        if not normalized_pack:
            raise ValueError("pack_id cannot be empty")
        if not name.strip():
            raise ValueError("name cannot be empty")
        if not isinstance(managers, dict) or not managers:
            raise ValueError("managers must be a non-empty dictionary")

        custom_packs = self._get_custom_language_packs()
        custom_packs[normalized_pack] = {
            "name": name.strip(),
            "description": description.strip(),
            "managers": managers,
            "third_party_imports": third_party_imports or [],
            "detectors": detectors or {},
        }
        self._save_custom_language_packs(custom_packs)

        packs = self.list_language_packs().get("packs", [])
        for item in packs:
            if str(item.get("pack_id", "")).strip().lower() == normalized_pack:
                return item
        raise KeyError(f"Failed to persist language pack '{normalized_pack}'")

    def remove_language_pack(self, pack_id: str) -> dict[str, Any]:
        normalized_pack = pack_id.strip().lower()
        if not normalized_pack:
            raise ValueError("pack_id cannot be empty")

        custom_packs = self._get_custom_language_packs()
        removed = custom_packs.pop(normalized_pack, None)
        if removed is None:
            raise KeyError(f"Custom language pack '{pack_id}' not found")
        self._save_custom_language_packs(custom_packs)
        return {"removed": normalized_pack}

    def list_language_packs(self) -> dict[str, Any]:
        packs = self.toolchain_service.list_language_packs(
            custom_packs=self._get_custom_language_packs(),
        )
        return {
            "count": len(packs),
            "packs": packs,
        }

    def list_unified_modules(self, path: str | Path = ".", os_name: str | None = None) -> dict[str, Any]:
        dependency_payload = self.list_modules(path)
        package_modules: list[dict[str, Any]] = []
        for item in dependency_payload.get("dependency_inventory", []):
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            package_modules.append(
                self.toolchain_service.build_package_module_entry(
                    package_name=name,
                    os_name=os_name,
                    source=str(item.get("source", "dependency")),
                    ecosystem="python",
                    installed=bool(item.get("installed", False)),
                    installed_version=(
                        str(item.get("installed_version")) if item.get("installed_version") else None
                    ),
                    metadata={
                        "declared_spec": item.get("declared_spec"),
                    },
                )
            )

        builder_modules = self.toolchain_service.list_tool_modules(
            tools=self.list_builders(),
            os_name=os_name,
            tool_kind="builder",
        )
        language_pack_modules = self.toolchain_service.list_language_pack_modules(
            os_name=os_name,
            custom_packs=self._get_custom_language_packs(),
        )
        integration_modules = self.toolchain_service.list_integration_modules(os_name=os_name)
        modules = sorted(
            [*package_modules, *builder_modules, *language_pack_modules, *integration_modules],
            key=lambda entry: (str(entry.get("module_kind", "")), str(entry.get("name", "")).lower()),
        )

        return {
            "path": str(Path(path).resolve()),
            "os": os_name,
            "count": len(modules),
            "modules": modules,
            "dependency_analysis": dependency_payload,
        }

    def search_unified_modules(
        self,
        query: str,
        manager: str | None = None,
        os_name: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        query_clean = query.strip()
        package_result = self.search_packages(query=query, manager=manager, os_name=os_name, limit=limit)
        modules: list[dict[str, Any]] = []
        seen_module_ids: set[str] = set()
        ecosystem = "python" if package_result.get("manager") in {"pip", "uv"} else None
        for item in package_result.get("results", []):
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            module = self.toolchain_service.build_package_module_entry(
                package_name=name,
                os_name=os_name,
                source="search",
                preferred_manager=str(package_result.get("manager") or "").strip() or None,
                ecosystem=ecosystem,
                installed=None,
                installed_version=None,
                metadata={"line": item.get("line")},
            )
            module_id = str(module.get("module_id", "")).strip()
            if module_id and module_id not in seen_module_ids:
                seen_module_ids.add(module_id)
                modules.append(module)

        # If query is a GitHub repo URL, only offer install when git is available.
        if "github.com/" in query_clean.lower() and self.toolchain_service.is_integration_tool_available("git"):
            try:
                module = self.toolchain_service.build_github_repo_module_entry(repo_url=query_clean)
            except Exception:
                module = None
            if module is not None:
                module_id = str(module.get("module_id", "")).strip()
                if module_id and module_id not in seen_module_ids:
                    seen_module_ids.add(module_id)
                    modules.append(module)

        for module in self.toolchain_service.search_known_tool_modules(
            query=query,
            tools=self.list_builders(),
            os_name=os_name,
            tool_kind="builder",
        ):
            module_id = str(module.get("module_id", "")).strip()
            if module_id and module_id not in seen_module_ids:
                seen_module_ids.add(module_id)
                modules.append(module)

        needle = query_clean.lower()
        for module in self.toolchain_service.list_integration_modules(os_name=os_name):
            haystacks = [
                str(module.get("tool_id", "")).lower(),
                str(module.get("name", "")).lower(),
                str(module.get("description", "")).lower(),
            ]
            if not any(needle in haystack for haystack in haystacks):
                continue
            module_id = str(module.get("module_id", "")).strip()
            if module_id and module_id not in seen_module_ids:
                seen_module_ids.add(module_id)
                modules.append(module)

        return {
            **package_result,
            "module_count": len(modules),
            "modules": modules,
        }

    def build_github_repo_module(
        self,
        repo_url: str,
        destination_root: str | None = None,
        branch: str | None = None,
    ) -> dict[str, Any]:
        if not self.toolchain_service.is_integration_tool_available("git"):
            raise RuntimeError("Git is not available on PATH. Install Git before using GitHub repository features.")
        return self.toolchain_service.build_github_repo_module_entry(
            repo_url=repo_url,
            destination_root=destination_root,
            branch=branch,
        )

    def install_github_repo(
        self,
        repo_url: str,
        destination_root: str | None = None,
        branch: str | None = None,
        existing_policy: str = "error",
        execute: bool = False,
    ) -> dict[str, Any]:
        return self.toolchain_service.install_github_repo(
            repo_url=repo_url,
            destination_root=destination_root,
            branch=branch,
            existing_policy=existing_policy,
            execute=execute,
        )

    def install_language_pack(
        self,
        pack_id: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
        continue_on_error: bool = False,
    ) -> dict[str, Any]:
        return self.toolchain_service.install_language_pack(
            pack_id=pack_id,
            manager=manager,
            os_name=os_name,
            execute=execute,
            continue_on_error=continue_on_error,
            custom_packs=self._get_custom_language_packs(),
        )

    def install_uv(
        self,
        os_name: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        return self.toolchain_service.install_uv(os_name=os_name, execute=execute)

    def list_integration_tools(self, os_name: str | None = None) -> dict[str, Any]:
        tools = self.toolchain_service.list_integration_tools(os_name=os_name)
        return {
            "os": os_name,
            "count": len(tools),
            "tools": tools,
        }

    def install_integration_tool(
        self,
        tool_id: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        return self.toolchain_service.install_integration_tool(
            tool_id=tool_id,
            manager=manager,
            os_name=os_name,
            execute=execute,
        )

    def list_package_managers(self, os_name: str | None = None) -> dict[str, Any]:
        return self.toolchain_service.list_package_managers(os_name=os_name)

    def search_packages(
        self,
        query: str,
        manager: str | None = None,
        os_name: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        return self.toolchain_service.search_packages(
            query=query,
            manager=manager,
            os_name=os_name,
            limit=limit,
        )

    def install_package(
        self,
        package_name: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        return self.toolchain_service.install_package(
            package_name=package_name,
            manager=manager,
            os_name=os_name,
            execute=execute,
        )

    def uninstall_package(
        self,
        package_name: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        return self.toolchain_service.uninstall_package(
            package_name=package_name,
            manager=manager,
            os_name=os_name,
            execute=execute,
        )

    def show_manifest(self) -> dict[str, Any]:
        return self.manifest_service.load_manifest()

    def refresh_manifest(self) -> dict[str, Any]:
        return self.manifest_service.refresh_manifest(
            builders=self.list_builders(),
            obfuscators=self.list_obfuscators(),
            language_packs=self.list_language_packs().get("packs", []),
        )

    def enable_manifest_capability(self, capability_id: str) -> dict[str, Any]:
        return self.manifest_service.set_enabled(capability_id, True)

    def disable_manifest_capability(self, capability_id: str) -> dict[str, Any]:
        return self.manifest_service.set_enabled(capability_id, False)

    def list_compiler_configs(self, language: str | None = None) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        configs = self.compiler_config_service.list_configs(state, language=language)
        return {
            "count": len(configs),
            "configs": configs,
        }

    def show_compiler_config(self, name: str, language: str | None = None) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.compiler_config_service.get_config(state, name, language=language)

    def set_compiler_config(
        self,
        name: str,
        language: str,
        settings: dict[str, Any],
        description: str = "",
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        updated = self.compiler_config_service.save_config(
            state,
            name,
            language,
            settings=settings,
            description=description,
        )
        self.save_memory(updated)
        return self.compiler_config_service.get_config(updated, name, language=language)

    def delete_compiler_config(self, name: str, language: str | None = None) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        deleted = self.compiler_config_service.delete_config(state, name, language=language)
        self.save_memory(state)
        return deleted

    def list_packagers(self) -> list[dict[str, str]]:
        return self.package_runner.registry.list_packagers()

    def inspect_packager(self, name: str) -> dict[str, Any]:
        return self.package_runner.registry.inspect(name)

    def run_package(self, request: PackageRequest | dict[str, Any]) -> dict[str, Any]:
        pkg_request = request if isinstance(request, PackageRequest) else PackageRequest.from_dict(request)
        result = self.package_runner.run(pkg_request)
        return result.to_dict()

    def list_hooks(self, project_path: str | Path = ".") -> dict[str, Any]:
        # Re-sync hook_runner memory each call so it sees latest state
        self.hook_runner._memory = self.backend_manager.read_memory()
        return self.hook_runner.list_hooks(project_path)

    def add_hook(
        self,
        project_path: str | Path,
        event: str,
        command: str,
        name: str = "",
        shell: bool = True,
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        self.hook_runner._memory = state
        entry = self.hook_runner.add_hook(project_path, event, command, name=name, shell=shell)
        self.save_memory(state)
        return {"added": entry, "project_path": str(project_path), "event": event}

    def remove_hook(self, project_path: str | Path, event: str, index: int) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        self.hook_runner._memory = state
        removed = self.hook_runner.remove_hook(project_path, event, index)
        self.save_memory(state)
        return {"removed": removed, "event": event, "index": index}

    def get_version(self, project_path: str | Path = ".") -> dict[str, Any]:
        return self.version_resolver.get_version(project_path)

    def set_version(
        self,
        project_path: str | Path,
        new_version: str,
        targets: list[str] | None = None,
    ) -> dict[str, Any]:
        return self.version_resolver.set_version(project_path, new_version, targets=targets)

    def create_git_tag(
        self,
        project_path: str | Path,
        tag: str,
        message: str = "",
        push: bool = False,
    ) -> dict[str, Any]:
        return self.version_resolver.create_git_tag(project_path, tag, message=message, push=push)

    def list_installers(self) -> list[dict[str, Any]]:
        return self._installer_registry.list_all()

    def inspect_installer(self, name: str) -> dict[str, Any]:
        adapter = self._installer_registry.get(name)
        if adapter is None:
            return {"error": f"Installer '{name}' not found"}
        return adapter.get_info()

    def run_installer(self, request: InstallerRequest | dict[str, Any]) -> dict[str, Any]:
        inst_request = request if isinstance(request, InstallerRequest) else InstallerRequest.from_dict(request)
        result = self.installer_runner.run(inst_request)
        return result.to_dict()

    def list_plugins(self) -> list[dict[str, Any]]:
        return self.plugin_loader.registry.list_plugins()

    def install_plugin(self, source_path: str) -> dict[str, Any]:
        return self.plugin_loader.install(source_path)

    def remove_plugin(self, name: str) -> dict[str, Any]:
        return self.plugin_loader.unload(name)

    def discover_plugins(self) -> list[dict[str, Any]]:
        return self.plugin_loader.discover()

    def generate_checksums(
        self,
        artifact_paths: list[str],
        output_dir: str = "dist",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        return self.checksum_service.generate(artifact_paths, output_dir, metadata=metadata)

    def analyse_size(self, directory: str, top_n: int = 20) -> dict[str, Any]:
        return self.size_analyzer.analyse(directory, top_n=top_n)

    def list_artifacts(self, project: str) -> list[dict[str, Any]]:
        state = self.backend_manager.read_memory()
        return [
            item for item in state["build_history"] if item.get("project_name") == project
        ]

    def get_build_history(self, project: str | None = None) -> list[dict[str, Any]]:
        history = self.backend_manager.read_memory()["build_history"]
        if project is None:
            return history
        return [item for item in history if item.get("project_name") == project]

    def load_memory(self) -> dict[str, Any]:
        return self.backend_manager.read_memory()

    def save_memory(self, state: dict[str, Any]) -> dict[str, Any]:
        store = self.backend_manager.get_store()
        try:
            store.save_state(state)
        finally:
            store.close()
        return state

    def get_memory_backend(self) -> dict[str, Any]:
        return self.backend_manager.get_status()

    def set_memory_backend(self, backend: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.backend_manager.set_backend(backend, config_update=config)

    def migrate_memory_backend(self, target_backend: str) -> dict[str, Any]:
        return self.backend_manager.migrate_to(target_backend)

    def set_user_setting(self, key: str, value: Any) -> dict[str, Any]:
        return self.backend_manager.write_user_setting(key, value)

    def get_user_setting(self, key: str) -> Any:
        return self.backend_manager.get_user_setting(key)

    def scan_project(
        self,
        path: str | Path,
        scope: str = "projects",
        include_extensions: list[str] | None = None,
    ) -> dict[str, Any]:
        return self.project_scanner.discover(path, scope=scope, include_extensions=include_extensions)

    def classify_project_files(self, path: str | Path) -> list[dict[str, Any]]:
        return self.scan_project(path).get("files", [])

    def import_project_schema(self, path: str | Path) -> dict[str, Any]:
        schema = self.schema_service.load_schema(path)
        schema_path = str(Path(path).resolve())
        root = schema.get("project", {}).get("root")
        if root:
            self._record_project_schema_path(root, schema_path, imported=True)
        return schema

    def create_profile(
        self,
        name: str,
        settings: dict[str, Any],
        description: str = "",
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        updated = self.profile_service.create_profile(state, name, settings, description=description)
        self.save_memory(updated)
        return self.profile_service.get_profile(updated, name)

    def list_profiles(self) -> list[dict[str, Any]]:
        state = self.backend_manager.read_memory()
        return self.profile_service.list_profiles(state)

    def show_profile(self, name: str) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.profile_service.get_profile(state, name)

    def create_organization_plan(
        self,
        project_or_group: str,
        mode: str = "copy",
    ) -> dict[str, Any]:
        scan_result = self.scan_project(project_or_group)
        return self.project_organizer.create_plan(project_or_group, scan_result, mode=mode)

    def apply_organization_plan(
        self,
        plan_or_path: dict[str, Any] | str | Path,
        force: bool = False,
    ) -> dict[str, Any]:
        plan = (
            self.project_organizer.load_plan(plan_or_path)
            if isinstance(plan_or_path, (str, Path))
            else plan_or_path
        )
        return self.project_organizer.apply_plan(plan, force=force)

    def save_organization_plan(self, plan: dict[str, Any], output_path: str | Path) -> Path:
        return self.project_organizer.save_plan(plan, output_path)

    def rollback_organization(self, manifest_path: str | Path, force: bool = False) -> dict[str, Any]:
        return self.project_organizer.rollback(manifest_path, force=force)

    def run_build(self, request: BuildRequest | dict[str, Any]) -> dict[str, Any]:
        raw_request = request if isinstance(request, dict) else {}
        build_request = request if isinstance(request, BuildRequest) else BuildRequest.from_dict(request)
        state = self.backend_manager.read_memory()
        self.hook_runner._memory = state

        if build_request.compiler_config_name:
            language_hint = self._build_language_hint(build_request)
            config = self.compiler_config_service.get_config(
                state,
                build_request.compiler_config_name,
                language=language_hint,
            )
            loaded_settings = dict(config.get("settings", {}))
            build_request.compiler_config = {
                **loaded_settings,
                **build_request.compiler_config,
            }

            if build_request.language.strip().lower() in {"", "auto"}:
                build_request.language = str(config.get("language", "auto"))

        # Optional test gate before build execution.
        test_result: dict[str, Any] | None = None
        test_cfg = self.test_runner_gate.get_config(state, build_request.project_path)
        if "error" not in test_cfg and bool(test_cfg.get("gate_enabled", False)):
            test_result = self.test_runner_gate.run_tests(
                build_request.project_path,
                command=str(test_cfg.get("command", "pytest")),
                state=state,
            )
            if not test_result.get("success", False):
                now = datetime.now(UTC).isoformat()
                result_dict = {
                    "success": False,
                    "exit_code": int(test_result.get("exit_code", 1)),
                    "final_command": [],
                    "artifact_paths": [],
                    "stdout": str(test_result.get("stdout", "")),
                    "stderr": "Build blocked: test gate failed.",
                    "started_at": now,
                    "finished_at": now,
                    "duration_seconds": float(test_result.get("duration", 0.0)),
                    "builder_name": build_request.builder_name,
                    "target_platform": build_request.target_platform,
                    "test_result": test_result,
                    "hook_results": {"pre_build": [], "post_build": [], "post_failure": []},
                }
                state["build_history"].append({**result_dict, "project_name": build_request.project_path.name})
                self.save_memory(state)
                return result_dict

        # Optional dependency audit gate before build execution.
        audit_result: dict[str, Any] | None = None
        audit_cfg = self.dependency_auditor.get_config(state, build_request.project_path)
        if "error" not in audit_cfg and bool(audit_cfg.get("gate_enabled", False)):
            audit_result = self.dependency_auditor.run_audit(
                build_request.project_path,
                requirements_file=raw_request.get("requirements_file") if isinstance(raw_request, dict) else None,
                state=state,
            )
            if bool(audit_result.get("blocked", False)):
                now = datetime.now(UTC).isoformat()
                result_dict = {
                    "success": False,
                    "exit_code": 1,
                    "final_command": [],
                    "artifact_paths": [],
                    "stdout": "",
                    "stderr": "Build blocked: dependency audit gate failed.",
                    "started_at": now,
                    "finished_at": now,
                    "duration_seconds": 0.0,
                    "builder_name": build_request.builder_name,
                    "target_platform": build_request.target_platform,
                    "audit_result": audit_result,
                    "hook_results": {"pre_build": [], "post_build": [], "post_failure": []},
                }
                state["build_history"].append({**result_dict, "project_name": build_request.project_path.name})
                self.save_memory(state)
                return result_dict

        hook_results: dict[str, list[dict[str, Any]]] = {
            "pre_build": [
                item.to_dict()
                for item in self.hook_runner.run_event(
                    build_request.project_path,
                    "pre_build",
                    cwd=build_request.project_path,
                )
            ],
        }

        container_mode = bool(raw_request.get("container", False)) if isinstance(raw_request, dict) else False
        if container_mode:
            build_cmd = shlex.join(self.command_translator.translate(build_request))
            result_dict = self.container_runner.run_build(
                build_request.project_path,
                build_command=build_cmd,
                state=state,
                image=raw_request.get("container_image") if isinstance(raw_request, dict) else None,
                output_dir=str(build_request.output_dir or "dist"),
            )
            result_dict.setdefault("builder_name", build_request.builder_name)
            result_dict.setdefault("target_platform", build_request.target_platform)
        else:
            result = self.build_runner.run(build_request)
            result_dict = result.to_dict()

        hook_results["post_build"] = [
            item.to_dict()
            for item in self.hook_runner.run_event(
                build_request.project_path,
                "post_build",
                cwd=build_request.project_path,
            )
        ]
        terminal_event = "post_success" if result_dict.get("success") else "post_failure"
        hook_results[terminal_event] = [
            item.to_dict()
            for item in self.hook_runner.run_event(
                build_request.project_path,
                terminal_event,
                cwd=build_request.project_path,
            )
        ]
        result_dict["hook_results"] = hook_results

        if test_result is not None:
            result_dict["test_result"] = test_result
        if audit_result is not None:
            result_dict["audit_result"] = audit_result

        duration = float(result_dict.get("duration_seconds", 0.0) or 0.0)
        result_dict["notification"] = self.notification_service.auto_notify(
            state,
            project_name=build_request.project_path.name,
            builder_name=str(result_dict.get("builder_name", build_request.builder_name)),
            success=bool(result_dict.get("success", False)),
            duration=duration,
        )

        state["build_history"].append(
            {
                **result_dict,
                "project_name": build_request.project_path.name,
            }
        )
        self.save_memory(state)
        return result_dict

    def run_tests(self, project_path: str | Path, command: str | None = None) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.test_runner_gate.run_tests(project_path, command=command, state=state)

    def set_test_config(
        self,
        project_path: str | Path,
        command: str = "pytest",
        gate_enabled: bool = False,
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        cfg = self.test_runner_gate.set_config(
            state,
            project_path,
            command=command,
            gate_enabled=gate_enabled,
        )
        self.save_memory(state)
        return cfg

    def get_test_config(self, project_path: str | Path) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.test_runner_gate.get_config(state, project_path)

    def sign_artifacts(
        self,
        project_path: str | Path,
        artifact_paths: list[str],
        tool: str | None = None,
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.signing_service.sign_artifacts(
            project_path,
            artifact_paths=artifact_paths,
            state=state,
            tool=tool,
        )

    def set_signing_config(
        self,
        project_path: str | Path,
        tool: str,
        *,
        cert: str = "",
        timestamp_url: str = "",
        developer_id: str = "",
        key_id: str = "",
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        cfg = self.signing_service.set_config(
            state,
            project_path,
            tool,
            cert=cert,
            timestamp_url=timestamp_url,
            developer_id=developer_id,
            key_id=key_id,
        )
        self.save_memory(state)
        return cfg

    def get_signing_config(self, project_path: str | Path) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.signing_service.get_config(state, project_path)

    def run_audit(
        self,
        project_path: str | Path,
        requirements_file: str | None = None,
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.dependency_auditor.run_audit(
            project_path,
            requirements_file=requirements_file,
            state=state,
        )

    def set_audit_config(
        self,
        project_path: str | Path,
        gate_enabled: bool = False,
        min_severity: str = "high",
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        cfg = self.dependency_auditor.set_config(
            state,
            project_path,
            gate_enabled=gate_enabled,
            min_severity=min_severity,
        )
        self.save_memory(state)
        return cfg

    def get_audit_config(self, project_path: str | Path) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.dependency_auditor.get_config(state, project_path)

    def prepare_icon(self, source_path: str | Path, target_platform: str = "windows") -> dict[str, Any]:
        return self.asset_pipeline.prepare_icon(source_path, target_platform=target_platform)

    def list_assets(self, source_path: str | Path) -> dict[str, Any]:
        return self.asset_pipeline.list_assets(source_path)

    def run_container_build(
        self,
        project_path: str | Path,
        build_command: str,
        image: str | None = None,
        output_dir: str = "dist",
    ) -> dict[str, Any]:
        if not self.toolchain_service.is_integration_tool_available("docker"):
            return {
                "success": False,
                "error": "Docker is not available on PATH. Install Docker before running container builds.",
            }
        state = self.backend_manager.read_memory()
        return self.container_runner.run_build(
            project_path,
            build_command=build_command,
            state=state,
            image=image,
            output_dir=output_dir,
        )

    def set_container_config(self, project_path: str | Path, image: str) -> dict[str, Any]:
        if not self.toolchain_service.is_integration_tool_available("docker"):
            return {
                "error": "Docker is not available on PATH. Install Docker before configuring container builds.",
            }
        state = self.backend_manager.read_memory()
        cfg = self.container_runner.set_config(state, project_path, image=image)
        self.save_memory(state)
        return cfg

    def get_container_config(self, project_path: str | Path) -> dict[str, Any]:
        if not self.toolchain_service.is_integration_tool_available("docker"):
            return {
                "error": "Docker is not available on PATH. Install Docker before using container features.",
            }
        state = self.backend_manager.read_memory()
        return self.container_runner.get_config(state, project_path)

    def set_notification_config(self, enabled: bool = True, webhook_url: str = "") -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        cfg = self.notification_service.set_config(state, enabled=enabled, webhook_url=webhook_url)
        self.save_memory(state)
        return cfg

    def get_notification_config(self) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.notification_service.get_config(state)

    def define_matrix(self, project_path: str | Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        result = self.matrix_runner.define_matrix(state, project_path, entries)
        self.save_memory(state)
        return result

    def get_matrix(self, project_path: str | Path) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.matrix_runner.get_matrix(state, project_path)

    def run_matrix(
        self,
        project_path: str | Path,
        entries: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        return self.matrix_runner.run_matrix(
            project_path,
            entries=entries,
            state=state,
            run_build_fn=self.run_build,
        )

    def launch_sandbox(
        self,
        artifact_path: str | Path,
        startup_command: str | None = None,
    ) -> dict[str, Any]:
        return self.sandbox_launcher.launch(artifact_path, startup_command=startup_command)

    def generate_ci_workflow(
        self,
        project_path: str | Path,
        profiles: list[dict[str, Any]],
        output_path: str | Path | None = None,
    ) -> dict[str, Any]:
        if not profiles:
            state = self.backend_manager.read_memory()
            stored = self.matrix_runner.get_matrix(state, project_path)
            if "error" in stored:
                return {
                    "error": "No profiles provided and no matrix defined for this project.",
                }
            profiles = list(stored.get("matrix", []))

        return self.ci_generator.generate_github_actions(
            project_path,
            profiles=profiles,
            output_path=output_path,
        )

    def export_profile_config(
        self,
        profile_name: str,
        output_path: str | Path | None = None,
    ) -> dict[str, Any]:
        state = self.backend_manager.read_memory()
        profile_data = self.profile_service.get_profile(state, profile_name)
        return self.ci_generator.export_profile(
            profile_name,
            profile_data,
            output_path=output_path,
        )

    def run_obfuscation(self, request: ObfuscationRequest | dict[str, Any]) -> dict[str, Any]:
        obfuscation_request = (
            request
            if isinstance(request, ObfuscationRequest)
            else ObfuscationRequest.from_dict(request)
        )
        result = self.obfuscation_runner.run(obfuscation_request)
        return result.to_dict()

    def _build_language_hint(self, build_request: BuildRequest) -> str | None:
        requested = build_request.language.strip().lower()
        if requested not in {"", "auto"}:
            return requested

        builder_name = build_request.builder_name.strip().lower()
        if builder_name in {"c", "cpp", "rust", "go", "python"}:
            return builder_name
        if builder_name in {"c++", "cplusplus"}:
            return "cpp"
        if builder_name in {"pyinstaller", "nuitka", "cxfreeze"}:
            return "python"
        return None

    def _record_project_schema_path(
        self,
        project_root: str,
        schema_path: str,
        imported: bool,
    ) -> None:
        state = self.backend_manager.read_memory()
        key = str(Path(project_root).resolve())
        project_record = state.setdefault("projects", {}).setdefault(
            key,
            {
                "path": key,
                "schema_paths": [],
                "last_imported_schema": None,
                "last_generated_schema": None,
            },
        )
        if schema_path not in project_record["schema_paths"]:
            project_record["schema_paths"].append(schema_path)
        if imported:
            project_record["last_imported_schema"] = schema_path
        else:
            project_record["last_generated_schema"] = schema_path
        self.save_memory(state)

    def export_project_schema(
        self,
        project: dict[str, Any],
        destination: str | Path | None = None,
    ) -> dict[str, Any]:
        schema = self.schema_service.export_starter_schema(project)
        project_root = project.get("path")
        output_path: Path | None = None
        if destination is not None:
            output_path = self.schema_service.save_schema(schema, destination)
        elif project_root:
            output_path = self.schema_service.save_schema(
                schema,
                Path(project_root) / "otterforge.project.json",
            )

        if output_path and project_root:
            self._record_project_schema_path(project_root, str(output_path.resolve()), imported=False)
            schema = {**schema, "saved_to": str(output_path.resolve())}
        return schema

    def clear_memory(self, scope: str, project_name: str | None = None) -> dict[str, Any]:
        return self.backend_manager.clear_memory(scope, project_name)

    def get_mcp_status(self) -> dict[str, Any]:
        return self.mcp_server.status()

    def start_mcp_server(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        transport = "stdio" if config is None else str(config.get("transport", "stdio"))
        return self.mcp_server.start(transport=transport)

    def stop_mcp_server(self) -> dict[str, Any]:
        return self.mcp_server.stop()

    def set_mcp_read_only(self, enabled: bool) -> dict[str, Any]:
        return self.mcp_server.set_read_only(enabled)

    def list_mcp_tools(self) -> list[dict[str, Any]]:
        return self.mcp_server.list_tools()

    def set_mcp_tool_visibility(self, tool_id: str, enabled: bool) -> dict[str, Any]:
        return self.mcp_server.set_tool_visibility(tool_id, enabled)

    def execute_mcp_tool(self, tool_id: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.mcp_server.execute_tool(tool_id, arguments=arguments)