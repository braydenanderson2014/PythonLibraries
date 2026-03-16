"""Tests for TestRunnerGate service."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from otterforge.services.test_runner_gate import TestRunnerGate


@pytest.fixture()
def gate():
    return TestRunnerGate()


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
    def test_set_and_get_config(self, gate, state, project):
        gate.set_config(state, project, "pytest -q", gate_enabled=True)
        cfg = gate.get_config(state, project)
        assert cfg["command"] == "pytest -q"
        assert cfg["gate_enabled"] is True

    def test_get_config_missing_returns_error(self, gate, state, project):
        result = gate.get_config(state, project)
        assert "error" in result

    def test_set_config_overwrites(self, gate, state, project):
        gate.set_config(state, project, "pytest", gate_enabled=False)
        gate.set_config(state, project, "python -m unittest", gate_enabled=True)
        cfg = gate.get_config(state, project)
        assert cfg["command"] == "python -m unittest"
        assert cfg["gate_enabled"] is True


# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------

class TestRunTests:
    def _make_completed(self, returncode=0, stdout="", stderr=""):
        proc = MagicMock(spec=subprocess.CompletedProcess)
        proc.returncode = returncode
        proc.stdout = stdout
        proc.stderr = stderr
        return proc

    def test_passing_tests_succeed(self, gate, state, project):
        with patch("subprocess.run", return_value=self._make_completed(0, "1 passed")):
            result = gate.run_tests(project, command="pytest")
        assert result["success"] is True
        assert result["exit_code"] == 0

    def test_failing_tests_not_success(self, gate, state, project):
        with patch("subprocess.run", return_value=self._make_completed(1, "", "FAILED")):
            result = gate.run_tests(project, command="pytest")
        assert result["success"] is False
        assert result["exit_code"] == 1

    def test_command_from_state_config(self, gate, state, project):
        gate.set_config(state, project, "python -m pytest", gate_enabled=False)
        captured = {}

        def fake_run(*args, **kwargs):
            captured["cmd"] = args[0] if args else kwargs.get("args")
            return self._make_completed(0)

        with patch("subprocess.run", side_effect=fake_run):
            result = gate.run_tests(project, command=None, state=state)
        assert result["success"] is True

    def test_default_command_is_pytest(self, gate, state, project):
        captured = {}

        def fake_run(*args, **kwargs):
            captured["cmd"] = args[0] if args else kwargs.get("args")
            return self._make_completed(0)

        with patch("subprocess.run", side_effect=fake_run):
            gate.run_tests(project)
        assert captured["cmd"] == "pytest"

    def test_timeout_returns_failure(self, gate, project):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 300)):
            result = gate.run_tests(project, command="pytest")
        assert result["success"] is False
        assert "timed out" in result["stderr"].lower()

    def test_result_contains_duration_and_command(self, gate, project):
        with patch("subprocess.run", return_value=self._make_completed(0)):
            result = gate.run_tests(project, command="pytest")
        assert "duration" in result
        assert result.get("command") == "pytest"

    def test_subprocess_exception_returns_failure(self, gate, project):
        with patch("subprocess.run", side_effect=OSError("not found")):
            result = gate.run_tests(project, command="pytest-nonexistent")
        assert result["success"] is False
