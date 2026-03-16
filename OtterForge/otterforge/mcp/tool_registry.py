from __future__ import annotations

from dataclasses import dataclass

from .policy import MCPPolicy


@dataclass(slots=True)
class MCPToolDescriptor:
    tool_id: str
    description: str
    mutating: bool = False


DEFAULT_MCP_TOOLS = [
    MCPToolDescriptor("scan_project", "Scan a project and classify files"),
    MCPToolDescriptor("list_builders", "List known build adapters"),
    MCPToolDescriptor("inspect_builder", "Inspect a builder adapter"),
    MCPToolDescriptor("list_obfuscators", "List known obfuscation adapters"),
    MCPToolDescriptor("inspect_obfuscator", "Inspect an obfuscation adapter"),
    MCPToolDescriptor("run_obfuscation", "Run an obfuscation request", mutating=True),
    MCPToolDescriptor("list_modules", "List project modules and dependencies"),
    MCPToolDescriptor("doctor_toolchain", "Report missing tools with install hints"),
    MCPToolDescriptor("list_language_packs", "List installable language packs"),
    MCPToolDescriptor("install_language_pack", "Install or plan a language pack", mutating=True),
    MCPToolDescriptor("show_manifest", "Show capability manifest"),
    MCPToolDescriptor("refresh_manifest", "Refresh capability manifest", mutating=True),
    MCPToolDescriptor("enable_manifest_capability", "Enable a capability in manifest", mutating=True),
    MCPToolDescriptor("disable_manifest_capability", "Disable a capability in manifest", mutating=True),
    MCPToolDescriptor("list_compiler_configs", "List saved compiler configs"),
    MCPToolDescriptor("show_compiler_config", "Show a single compiler config"),
    MCPToolDescriptor("set_compiler_config", "Create or update a compiler config", mutating=True),
    MCPToolDescriptor("delete_compiler_config", "Delete a compiler config", mutating=True),
    MCPToolDescriptor("list_profiles", "List saved build profiles"),
    MCPToolDescriptor("show_profile", "Show a single saved profile"),
    MCPToolDescriptor("create_profile", "Create or update a saved profile", mutating=True),
    MCPToolDescriptor("create_organization_plan", "Create a proposed organization plan"),
    MCPToolDescriptor("apply_organization_plan", "Apply an organization plan", mutating=True),
    MCPToolDescriptor("rollback_organization", "Rollback an organization manifest", mutating=True),
    MCPToolDescriptor("import_project_schema", "Import a project schema file", mutating=True),
    MCPToolDescriptor("export_project_schema", "Export a starter project schema", mutating=True),
    MCPToolDescriptor("list_artifacts", "List artifacts for a project"),
    MCPToolDescriptor("get_build_history", "Read build history for a project"),
    MCPToolDescriptor("run_build", "Run a build request", mutating=True),
    MCPToolDescriptor("load_memory", "Read persisted memory state"),
    # Packager tools
    MCPToolDescriptor("list_packagers", "List known packager adapters"),
    MCPToolDescriptor("inspect_packager", "Inspect a packager adapter"),
    MCPToolDescriptor("run_package", "Run a packaging request", mutating=True),
    # Hook tools
    MCPToolDescriptor("list_hooks", "List lifecycle hooks for a project"),
    MCPToolDescriptor("add_hook", "Add a lifecycle hook", mutating=True),
    MCPToolDescriptor("remove_hook", "Remove a lifecycle hook", mutating=True),
    # Version tools
    MCPToolDescriptor("get_version", "Read version string from a project"),
    MCPToolDescriptor("set_version", "Write a new version string to a project", mutating=True),
    MCPToolDescriptor("create_git_tag", "Create an annotated git version tag", mutating=True),
    MCPToolDescriptor("list_installers", "List known installer adapters"),
    MCPToolDescriptor("inspect_installer", "Show details for a named installer adapter"),
    MCPToolDescriptor("run_installer", "Run an installer build request", mutating=True),
    MCPToolDescriptor("list_plugins", "List loaded plugins"),
    MCPToolDescriptor("install_plugin", "Install a plugin from a file path", mutating=True),
    MCPToolDescriptor("remove_plugin", "Remove a loaded plugin", mutating=True),
    MCPToolDescriptor("generate_checksums", "Generate SHA-256 checksums and release manifest", mutating=True),
    MCPToolDescriptor("analyse_size", "Analyse the size breakdown of a build output directory"),
    MCPToolDescriptor("get_memory_backend", "Read the active memory backend"),
    MCPToolDescriptor("set_memory_backend", "Set the active memory backend", mutating=True),
    MCPToolDescriptor("migrate_memory_backend", "Migrate memory to another backend", mutating=True),
    MCPToolDescriptor("set_mcp_read_only", "Set MCP read-only policy", mutating=True),
    MCPToolDescriptor("get_mcp_status", "Read MCP server status"),
    MCPToolDescriptor("list_mcp_tools", "List exposed MCP tools"),
    # Test runner
    MCPToolDescriptor("run_tests", "Run the project test suite"),
    MCPToolDescriptor("set_test_config", "Configure the test runner command and gate", mutating=True),
    MCPToolDescriptor("get_test_config", "Read the test runner config for a project"),
    # Signing
    MCPToolDescriptor("sign_artifacts", "Sign build artifacts with signtool/codesign/gpg", mutating=True),
    MCPToolDescriptor("set_signing_config", "Configure code-signing settings for a project", mutating=True),
    MCPToolDescriptor("get_signing_config", "Read signing config for a project"),
    # Audit
    MCPToolDescriptor("run_audit", "Audit dependencies for known vulnerabilities"),
    MCPToolDescriptor("set_audit_config", "Configure dependency audit settings", mutating=True),
    MCPToolDescriptor("get_audit_config", "Read dependency audit config for a project"),
    # Assets
    MCPToolDescriptor("prepare_icon", "Convert a source image to a platform icon format", mutating=True),
    MCPToolDescriptor("list_assets", "List cached icon assets for a source image"),
    # Container
    MCPToolDescriptor("run_container_build", "Run a build inside a Docker container", mutating=True),
    MCPToolDescriptor("set_container_config", "Set the Docker image for a project", mutating=True),
    MCPToolDescriptor("get_container_config", "Read container build config for a project"),
    # Notifications
    MCPToolDescriptor("send_notification", "Send a desktop or terminal notification", mutating=True),
    MCPToolDescriptor("set_notification_config", "Configure build notifications", mutating=True),
    # Matrix
    MCPToolDescriptor("run_matrix", "Run a local build matrix sequentially", mutating=True),
    MCPToolDescriptor("define_matrix", "Define and persist a build matrix for a project", mutating=True),
    MCPToolDescriptor("get_matrix", "Read the build matrix for a project"),
    # Sandbox
    MCPToolDescriptor("launch_sandbox", "Launch a Windows Sandbox with a build artifact", mutating=True),
    MCPToolDescriptor("check_sandbox_available", "Check whether Windows Sandbox is available"),
    # CI
    MCPToolDescriptor("generate_ci_workflow", "Generate a GitHub Actions CI workflow", mutating=True),
    MCPToolDescriptor("export_profile_config", "Export a build profile to a portable JSON file", mutating=True),
]


class MCPToolRegistry:
    def __init__(self, policy: MCPPolicy) -> None:
        self.policy = policy

    def list_tools(self) -> list[MCPToolDescriptor]:
        tools = []
        for descriptor in DEFAULT_MCP_TOOLS:
            if descriptor.tool_id not in self.policy.exposed_tools:
                continue
            if self.policy.read_only and descriptor.mutating:
                continue
            tools.append(descriptor)
        return tools