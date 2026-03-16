"""Tests for SandboxLauncher service."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from otterforge.services.sandbox_launcher import SandboxLauncher


@pytest.fixture()
def launcher():
    return SandboxLauncher()


@pytest.fixture()
def artifact(tmp_path):
    f = tmp_path / "app.exe"
    f.write_bytes(b"\x00" * 16)
    return f


# ---------------------------------------------------------------------------
# Availability detection
# ---------------------------------------------------------------------------

class TestAvailability:
    def test_available_when_windowssandbox_on_path(self, launcher):
        with patch("shutil.which", return_value="C:\\Windows\\System32\\WindowsSandbox.exe"):
            assert launcher.is_available() is True

    def test_unavailable_when_windowssandbox_missing(self, launcher):
        with patch("shutil.which", return_value=None):
            assert launcher.is_available() is False


# ---------------------------------------------------------------------------
# Launch — available gate
# ---------------------------------------------------------------------------

class TestLaunch:
    def test_returns_error_when_unavailable(self, launcher, artifact):
        with patch.object(launcher, "is_available", return_value=False):
            result = launcher.launch(artifact)
        assert result["success"] is False
        assert "WindowsSandbox" in result["error"]

    def test_returns_error_when_artifact_missing(self, launcher, tmp_path):
        with patch.object(launcher, "is_available", return_value=True):
            result = launcher.launch(tmp_path / "nonexistent.exe")
        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ---------------------------------------------------------------------------
# WSB file generation
# ---------------------------------------------------------------------------

class TestWsbGeneration:
    def _capture_wsb(self, launcher, artifact, startup_command=None):
        """Capture WSB content without actually launching Windows Sandbox."""
        written = {}

        original_write = Path.write_text

        def fake_write(self_path, content, *args, **kwargs):
            if str(self_path).endswith(".wsb"):
                written["content"] = content
                written["path"] = str(self_path)
            return original_write(self_path, content, *args, **kwargs)

        with patch.object(launcher, "is_available", return_value=True):
            with patch("subprocess.Popen"):
                with patch.object(Path, "write_text", fake_write):
                    result = launcher.launch(artifact, startup_command=startup_command)

        return written, result

    def test_wsb_file_contains_host_folder_path(self, launcher, artifact):
        written, result = self._capture_wsb(launcher, artifact)
        assert result["success"] is True
        assert str(artifact.parent) in written["content"]

    def test_wsb_file_without_startup_has_no_logon_command(self, launcher, artifact):
        written, _ = self._capture_wsb(launcher, artifact)
        assert "LogonCommand" not in written["content"]

    def test_wsb_file_with_startup_includes_logon_command(self, launcher, artifact):
        written, _ = self._capture_wsb(launcher, artifact, startup_command="cmd.exe /k app.exe")
        assert "LogonCommand" in written["content"]
        assert "app.exe" in written["content"]

    def test_wsb_path_in_result(self, launcher, artifact):
        written, result = self._capture_wsb(launcher, artifact)
        assert "wsb_path" in result
        assert result["wsb_path"].endswith(".wsb")
