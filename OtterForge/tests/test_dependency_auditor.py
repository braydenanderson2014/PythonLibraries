"""Tests for DependencyAuditor service."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from otterforge.services.dependency_auditor import DependencyAuditor


@pytest.fixture()
def auditor():
    return DependencyAuditor()


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
    def test_set_and_get_config(self, auditor, state, project):
        auditor.set_config(state, project, gate_enabled=True, min_severity="critical")
        cfg = auditor.get_config(state, project)
        assert cfg["gate_enabled"] is True
        assert cfg["min_severity"] == "critical"

    def test_get_config_missing_returns_error(self, auditor, state, project):
        result = auditor.get_config(state, project)
        assert "error" in result

    def test_default_severity_is_high(self, auditor, state, project):
        auditor.set_config(state, project)
        cfg = auditor.get_config(state, project)
        assert cfg["min_severity"] == "high"


# ---------------------------------------------------------------------------
# Tool selection
# ---------------------------------------------------------------------------

class TestToolSelection:
    def test_prefers_pip_audit(self, auditor):
        with patch("shutil.which", side_effect=lambda x: "/usr/bin/pip-audit" if x == "pip-audit" else None):
            assert auditor._pick_tool() == "pip-audit"

    def test_falls_back_to_safety(self, auditor):
        with patch("shutil.which", side_effect=lambda x: "/usr/bin/safety" if x == "safety" else None):
            assert auditor._pick_tool() == "safety"

    def test_returns_none_when_neither_available(self, auditor):
        with patch("shutil.which", return_value=None):
            assert auditor._pick_tool() is None


# ---------------------------------------------------------------------------
# Audit execution
# ---------------------------------------------------------------------------

class TestRunAudit:
    PIP_AUDIT_OUTPUT = json.dumps({
        "dependencies": [
            {
                "name": "requests",
                "version": "2.0.0",
                "vulns": [
                    {
                        "id": "PYSEC-2023-001",
                        "description": "CVE example",
                        "severity": "high",
                        "fix_versions": ["2.28.0"],
                    }
                ],
            }
        ]
    })

    def test_no_tool_available_returns_error(self, auditor, project, state):
        with patch.object(auditor, "_pick_tool", return_value=None):
            result = auditor.run_audit(project, state=state)
        assert result["success"] is False
        assert "pip-audit" in result["error"]

    def test_clean_audit_has_no_vulnerabilities(self, auditor, project, state):
        clean_output = json.dumps({"dependencies": []})
        proc = MagicMock(spec=subprocess.CompletedProcess)
        proc.returncode = 0
        proc.stdout = clean_output
        proc.stderr = ""

        with patch.object(auditor, "_pick_tool", return_value="pip-audit"):
            with patch("subprocess.run", return_value=proc):
                result = auditor.run_audit(project, state=state)

        assert result["count"] == 0
        assert result["blocked"] is False

    def test_gate_blocks_when_vuln_exceeds_threshold(self, auditor, project, state):
        auditor.set_config(state, project, gate_enabled=True, min_severity="high")
        proc = MagicMock(spec=subprocess.CompletedProcess)
        proc.returncode = 1
        proc.stdout = self.PIP_AUDIT_OUTPUT
        proc.stderr = ""

        with patch.object(auditor, "_pick_tool", return_value="pip-audit"):
            with patch("subprocess.run", return_value=proc):
                result = auditor.run_audit(project, state=state)

        assert result["blocked"] is True

    def test_gate_does_not_block_when_disabled(self, auditor, project, state):
        auditor.set_config(state, project, gate_enabled=False, min_severity="high")
        proc = MagicMock(spec=subprocess.CompletedProcess)
        proc.returncode = 1
        proc.stdout = self.PIP_AUDIT_OUTPUT
        proc.stderr = ""

        with patch.object(auditor, "_pick_tool", return_value="pip-audit"):
            with patch("subprocess.run", return_value=proc):
                result = auditor.run_audit(project, state=state)

        assert result["blocked"] is False

    def test_gate_does_not_block_when_below_threshold(self, auditor, project, state):
        auditor.set_config(state, project, gate_enabled=True, min_severity="critical")
        # Vulnerability is only "high", threshold is "critical" — should not block
        proc = MagicMock(spec=subprocess.CompletedProcess)
        proc.returncode = 1
        proc.stdout = self.PIP_AUDIT_OUTPUT
        proc.stderr = ""

        with patch.object(auditor, "_pick_tool", return_value="pip-audit"):
            with patch("subprocess.run", return_value=proc):
                result = auditor.run_audit(project, state=state)

        assert result["blocked"] is False
