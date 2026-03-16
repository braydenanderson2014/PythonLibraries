"""Tests for SigningService."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from otterforge.services.signing_service import SigningService


@pytest.fixture()
def svc():
    return SigningService()


@pytest.fixture()
def state():
    return {}


@pytest.fixture()
def project(tmp_path):
    return tmp_path


@pytest.fixture()
def artifact(tmp_path):
    f = tmp_path / "app.exe"
    f.write_bytes(b"\x00" * 16)
    return f


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

class TestConfig:
    def test_set_config_stores_tool(self, svc, state, project):
        result = svc.set_config(state, project, "signtool", cert="my.pfx")
        assert result["tool"] == "signtool"
        assert result["configured"] is True

    def test_get_config_redacts_cert(self, svc, state, project):
        svc.set_config(state, project, "gpg", cert="/secret/cert.pfx")
        cfg = svc.get_config(state, project)
        assert "cert" not in cfg
        assert cfg["tool"] == "gpg"

    def test_get_config_missing_returns_error(self, svc, state, project):
        result = svc.get_config(state, project)
        assert "error" in result

    def test_set_config_merges_existing(self, svc, state, project):
        svc.set_config(state, project, "signtool", cert="cert.pfx")
        # Update only the timestamp without supplying cert again
        svc.set_config(state, project, "signtool", timestamp_url="http://ts.example.com")
        raw_cfg = state["signing_configs"][str(Path(project).resolve())]
        # cert must still be present from original set
        assert raw_cfg["cert"] == "cert.pfx"
        assert raw_cfg["timestamp_url"] == "http://ts.example.com"


# ---------------------------------------------------------------------------
# Tool resolution
# ---------------------------------------------------------------------------

class TestToolResolution:
    def test_default_tool_is_platform_appropriate(self, svc):
        tool = svc._default_tool()
        if sys.platform.startswith("win"):
            assert tool == "signtool"
        elif sys.platform == "darwin":
            assert tool == "codesign"
        else:
            assert tool == "gpg"

    def test_tool_available_uses_shutil_which(self, svc):
        with patch("shutil.which", return_value="/usr/bin/gpg"):
            assert svc._tool_available("gpg") is True
        with patch("shutil.which", return_value=None):
            assert svc._tool_available("gpg") is False


# ---------------------------------------------------------------------------
# Sign artifacts
# ---------------------------------------------------------------------------

class TestSignArtifacts:
    def test_unavailable_tool_returns_warning_not_error(self, svc, state, project, artifact):
        with patch.object(svc, "_tool_available", return_value=False):
            result = svc.sign_artifacts(project, [str(artifact)], state, tool="signtool")
        assert len(result["failed"]) == 1
        assert any("warning" in d for d in result["details"])

    def test_successful_sign_included_in_signed_list(self, svc, state, project, artifact):
        fake_result = {"path": str(artifact), "success": True}
        with patch.object(svc, "_tool_available", return_value=True):
            with patch.object(svc, "_sign_one", return_value=fake_result):
                result = svc.sign_artifacts(project, [str(artifact)], state, tool="gpg")
        assert str(artifact) in result["signed"]
        assert len(result["failed"]) == 0

    def test_empty_artifact_list(self, svc, state, project):
        result = svc.sign_artifacts(project, [], state, tool="gpg")
        assert result["signed"] == []
        assert result["failed"] == []
