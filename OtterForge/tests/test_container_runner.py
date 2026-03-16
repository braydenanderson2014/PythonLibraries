"""Tests for ContainerRunner service."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from otterforge.services.container_runner import ContainerRunner


@pytest.fixture()
def runner():
    return ContainerRunner()


@pytest.fixture()
def state():
    return {}


@pytest.fixture()
def project(tmp_path):
    return tmp_path


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

class TestConfig:
    def test_set_and_get_config(self, runner, state, project):
        runner.set_config(state, project, "python:3.13-slim")
        cfg = runner.get_config(state, project)
        assert cfg["image"] == "python:3.13-slim"

    def test_get_config_missing_returns_error(self, runner, state, project):
        result = runner.get_config(state, project)
        assert "error" in result


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

class TestAvailability:
    def test_available_when_docker_on_path(self, runner):
        with patch("shutil.which", return_value="/usr/bin/docker"):
            assert runner.is_available() is True

    def test_unavailable_when_docker_not_on_path(self, runner):
        with patch("shutil.which", return_value=None):
            assert runner.is_available() is False


# ---------------------------------------------------------------------------
# Build command construction
# ---------------------------------------------------------------------------

class TestRunBuild:
    def test_returns_error_when_docker_unavailable(self, runner, state, project):
        with patch.object(runner, "is_available", return_value=False):
            result = runner.run_build(project, "pyinstaller main.py", state)
        assert result["success"] is False
        assert "Docker" in result["error"]

    def test_returns_error_when_no_image_configured(self, runner, state, project):
        with patch.object(runner, "is_available", return_value=True):
            result = runner.run_build(project, "pyinstaller main.py", state)
        assert result["success"] is False
        assert "image" in result["error"].lower()

    def test_successful_run_with_image_from_config(self, runner, state, project):
        runner.set_config(state, project, "python:3.13-slim")
        proc = MagicMock(spec=subprocess.CompletedProcess)
        proc.returncode = 0
        proc.stdout = "Build success"
        proc.stderr = ""

        with patch.object(runner, "is_available", return_value=True):
            with patch("subprocess.run", return_value=proc):
                result = runner.run_build(project, "pyinstaller main.py", state)
        assert result["success"] is True

    def test_image_override_takes_precedence_over_config(self, runner, state, project):
        runner.set_config(state, project, "python:3.11-slim")
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = ""
            proc.stderr = ""
            return proc

        with patch.object(runner, "is_available", return_value=True):
            with patch("subprocess.run", side_effect=fake_run):
                runner.run_build(project, "pyinstaller main.py", state, image="python:3.13-slim")

        assert any("python:3.13-slim" in str(a) for a in captured["cmd"])
