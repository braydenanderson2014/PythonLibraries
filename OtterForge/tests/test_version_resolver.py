"""Tests for VersionResolver service."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from otterforge.services.version_resolver import VersionResolver


@pytest.fixture()
def resolver():
    return VersionResolver()


# ---------------------------------------------------------------------------
# pyproject.toml reading
# ---------------------------------------------------------------------------

class TestPyprojectVersion:
    def test_reads_project_version(self, resolver, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "myapp"\nversion = "1.2.3"\n', encoding="utf-8"
        )
        assert resolver._read_pyproject_version(tmp_path) == "1.2.3"

    def test_reads_poetry_version(self, resolver, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.poetry]\nname = "myapp"\nversion = "0.9.0"\n', encoding="utf-8"
        )
        assert resolver._read_pyproject_version(tmp_path) == "0.9.0"

    def test_returns_none_when_file_missing(self, resolver, tmp_path):
        assert resolver._read_pyproject_version(tmp_path) is None

    def test_returns_none_when_version_absent(self, resolver, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "myapp"\n', encoding="utf-8")
        assert resolver._read_pyproject_version(tmp_path) is None


# ---------------------------------------------------------------------------
# setup.cfg reading
# ---------------------------------------------------------------------------

class TestSetupCfgVersion:
    def test_reads_metadata_version(self, resolver, tmp_path):
        (tmp_path / "setup.cfg").write_text(
            "[metadata]\nname = myapp\nversion = 2.0.0\n", encoding="utf-8"
        )
        assert resolver._read_setup_cfg_version(tmp_path) == "2.0.0"

    def test_returns_none_when_file_missing(self, resolver, tmp_path):
        assert resolver._read_setup_cfg_version(tmp_path) is None


# ---------------------------------------------------------------------------
# Source __version__ reading
# ---------------------------------------------------------------------------

class TestSourceVersion:
    def test_reads_double_quoted_version(self, resolver, tmp_path):
        (tmp_path / "myapp.py").write_text('__version__ = "3.1.4"\n', encoding="utf-8")
        assert resolver._read_source_version(tmp_path) == "3.1.4"

    def test_reads_single_quoted_version(self, resolver, tmp_path):
        (tmp_path / "myapp.py").write_text("__version__ = '0.1.0'\n", encoding="utf-8")
        assert resolver._read_source_version(tmp_path) == "0.1.0"

    def test_returns_none_when_not_found(self, resolver, tmp_path):
        assert resolver._read_source_version(tmp_path) is None


# ---------------------------------------------------------------------------
# Effective version priority
# ---------------------------------------------------------------------------

class TestEffectiveVersion:
    def test_pyproject_takes_precedence(self, resolver, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nversion = "1.0.0"\n', encoding="utf-8"
        )
        (tmp_path / "app.py").write_text('__version__ = "0.0.1"\n', encoding="utf-8")
        info = resolver.get_version(tmp_path)
        assert info["effective_version"] == "1.0.0"

    def test_source_version_as_fallback(self, resolver, tmp_path):
        (tmp_path / "app.py").write_text('__version__ = "4.5.6"\n', encoding="utf-8")
        info = resolver.get_version(tmp_path)
        assert info["effective_version"] == "4.5.6"

    def test_returns_none_when_nothing_found(self, resolver, tmp_path):
        info = resolver.get_version(tmp_path)
        assert info["effective_version"] is None

    def test_returns_all_source_fields(self, resolver, tmp_path):
        info = resolver.get_version(tmp_path)
        assert "pyproject_version" in info
        assert "setup_cfg_version" in info
        assert "source_version" in info
        assert "git" in info
