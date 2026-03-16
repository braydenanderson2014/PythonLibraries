from __future__ import annotations

import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

_WSB_TEMPLATE = textwrap.dedent("""\
    <Configuration>
      <MappedFolders>
        <MappedFolder>
          <HostFolder>{host_folder}</HostFolder>
          <ReadOnly>{read_only}</ReadOnly>
        </MappedFolder>
      </MappedFolders>
      {logon_command}
    </Configuration>
""")

_LOGON_TEMPLATE = textwrap.dedent("""\
    <LogonCommand>
        <Command>{command}</Command>
      </LogonCommand>
""")


class SandboxLauncher:
    """Generate a Windows Sandbox (.wsb) config and launch the sandbox."""

    def is_available(self) -> bool:
        return shutil.which("WindowsSandbox.exe") is not None

    def launch(
        self,
        artifact_path: str | Path,
        startup_command: str | None = None,
    ) -> dict[str, Any]:
        if not self.is_available():
            return {
                "success": False,
                "error": (
                    "WindowsSandbox.exe not found. "
                    "Enable 'Windows Sandbox' in Windows Features."
                ),
            }

        artifact = Path(artifact_path).resolve()
        if not artifact.exists():
            return {"success": False, "error": f"Artifact not found: {artifact}"}

        host_folder = str(artifact.parent)

        logon_block = ""
        if startup_command:
            logon_block = _LOGON_TEMPLATE.format(command=startup_command)

        wsb_content = _WSB_TEMPLATE.format(
            host_folder=host_folder,
            read_only="false",
            logon_command=logon_block,
        )

        # Write .wsb to a temp file
        tmp_dir = tempfile.mkdtemp(prefix="otterforge_sandbox_")
        wsb_path = Path(tmp_dir) / "otterforge.wsb"
        wsb_path.write_text(wsb_content, encoding="utf-8")

        try:
            subprocess.Popen(  # noqa: S603
                ["WindowsSandbox.exe", str(wsb_path)],
                shell=False,
            )
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc), "wsb_path": str(wsb_path)}

        return {
            "success": True,
            "wsb_path": str(wsb_path),
            "host_folder": host_folder,
            "artifact": str(artifact),
        }

    def generate_wsb(
        self,
        artifact_path: str | Path,
        startup_command: str | None = None,
    ) -> dict[str, Any]:
        """Return the .wsb XML without launching it."""
        artifact = Path(artifact_path).resolve()
        host_folder = str(artifact.parent)

        logon_block = ""
        if startup_command:
            logon_block = _LOGON_TEMPLATE.format(command=startup_command)

        wsb_content = _WSB_TEMPLATE.format(
            host_folder=host_folder,
            read_only="false",
            logon_command=logon_block,
        )
        return {
            "wsb_content": wsb_content,
            "host_folder": host_folder,
            "artifact": str(artifact),
        }
