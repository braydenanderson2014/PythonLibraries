"""Tests for SizeAnalyzer service."""
from __future__ import annotations

from pathlib import Path

import pytest

from otterforge.services.size_analyzer import SizeAnalyzer


@pytest.fixture()
def analyzer():
    return SizeAnalyzer()


@pytest.fixture()
def dist_dir(tmp_path):
    """A small fake dist directory with a few files of known sizes."""
    d = tmp_path / "dist"
    d.mkdir()
    (d / "app.exe").write_bytes(b"x" * 2048)
    (d / "python313.dll").write_bytes(b"y" * 4096)
    (d / "requests").mkdir()
    (d / "requests" / "__init__.py").write_bytes(b"z" * 512)
    (d / "icon.png").write_bytes(b"p" * 256)
    (d / "config.json").write_bytes(b"c" * 64)
    return d


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------

class TestAnalyseStructure:
    def test_returns_total_bytes(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir)
        assert "total_bytes" in result
        assert result["total_bytes"] == 2048 + 4096 + 512 + 256 + 64

    def test_returns_total_files(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir)
        assert result["total_files"] == 5

    def test_returns_top_files(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir)
        assert "top_files" in result
        # Largest should be python313.dll at 4096 bytes
        assert result["top_files"][0]["size_bytes"] == 4096

    def test_top_n_limits_list(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir, top_n=2)
        assert len(result["top_files"]) <= 2

    def test_returns_category_breakdown(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir)
        cats = result["by_category"]
        assert "python" in cats
        assert "native" in cats
        assert "data" in cats
        assert "media" in cats

    def test_python_category_includes_py_files(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir)
        assert result["by_category"]["python"]["size_bytes"] == 512  # __init__.py

    def test_native_category_includes_dll_and_exe(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir)
        # .exe and .dll are both in native
        assert result["by_category"]["native"]["size_bytes"] == 2048 + 4096

    def test_media_category_includes_png(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir)
        assert result["by_category"]["media"]["size_bytes"] == 256

    def test_data_category_includes_json(self, analyzer, dist_dir):
        result = analyzer.analyse(dist_dir)
        assert result["by_category"]["data"]["size_bytes"] == 64


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_missing_directory_returns_error(self, analyzer, tmp_path):
        result = analyzer.analyse(tmp_path / "nonexistent")
        assert "error" in result

    def test_empty_directory(self, analyzer, tmp_path):
        result = analyzer.analyse(tmp_path)
        assert result["total_bytes"] == 0
        assert result["total_files"] == 0
        assert result["top_files"] == []
