"""Tests for AssetPipeline service."""
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

from otterforge.services.asset_pipeline import AssetPipeline


def _write_minimal_png(path: Path) -> None:
    """Write a 1×1 white PNG file (valid Pillow input)."""
    import struct, zlib
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)
    raw = b"\x00\xff\xff\xff"
    compressed = zlib.compress(raw)
    idat = chunk(b"IDAT", compressed)
    iend = chunk(b"IEND", b"")
    path.write_bytes(sig + ihdr + idat + iend)


class TestAssetPipelineNoPillow(unittest.TestCase):
    """Behaviour when Pillow is not installed."""

    def test_prepare_icon_returns_failure_without_pillow(self) -> None:
        pipeline = AssetPipeline()
        with patch.object(pipeline, "_pillow_available", return_value=False):
            with tempfile.TemporaryDirectory() as tmp:
                fake_src = Path(tmp) / "icon.png"
                fake_src.write_bytes(b"")
                result = pipeline.prepare_icon(str(fake_src))
        self.assertFalse(result["success"])
        self.assertIn("Pillow", result["error"])

    def test_prepare_icon_missing_source_returns_failure(self) -> None:
        pipeline = AssetPipeline()
        fake_spec = MagicMock()
        with patch("importlib.util.find_spec", return_value=fake_spec):
            result = pipeline.prepare_icon("/nonexistent/icon.png")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])


class TestAssetPipelineListAssets(unittest.TestCase):

    def test_list_assets_returns_dict_with_required_keys(self) -> None:
        pipeline = AssetPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "icon.png"
            src.write_bytes(b"stub")
            result = pipeline.list_assets(str(src))
        self.assertIn("cache_dir", result)
        self.assertIn("assets", result)
        self.assertIn("count", result)

    def test_list_assets_count_matches_assets_len(self) -> None:
        pipeline = AssetPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "icon.png"
            src.write_bytes(b"stub")
            result = pipeline.list_assets(str(src))
        self.assertEqual(result["count"], len(result["assets"]))

    def test_list_assets_empty_when_no_cache(self) -> None:
        pipeline = AssetPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            # Use a path that hasn't been converted yet → cache dir won't exist
            src = Path(tmp) / "fresh.png"
            src.write_bytes(b"stub")
            # Patch home to a temp dir so no pre-existing cache interferes
            with patch("pathlib.Path.home", return_value=Path(tmp) / "home"):
                result = pipeline.list_assets(str(src))
        self.assertEqual(result["count"], 0)

    def test_cache_dir_deterministic_for_same_source(self) -> None:
        pipeline = AssetPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "icon.png"
            src.write_bytes(b"stub")
            dir1 = pipeline._cache_dir(src)
            dir2 = pipeline._cache_dir(src)
        self.assertEqual(dir1, dir2)

    def test_cache_dir_differs_for_different_sources(self) -> None:
        pipeline = AssetPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            src_a = Path(tmp) / "icon_a.png"
            src_b = Path(tmp) / "icon_b.png"
            src_a.write_bytes(b"stub")
            src_b.write_bytes(b"stub")
            dir_a = pipeline._cache_dir(src_a)
            dir_b = pipeline._cache_dir(src_b)
        self.assertNotEqual(dir_a, dir_b)


class TestAssetPipelineWithPillow(unittest.TestCase):
    """Tests that run only when Pillow is installed."""

    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util
        cls.pillow_available = importlib.util.find_spec("PIL") is not None

    def _skip_if_no_pillow(self) -> None:
        if not self.pillow_available:
            self.skipTest("Pillow not installed — skipping live conversion tests")

    def test_prepare_icon_windows_produces_ico(self) -> None:
        self._skip_if_no_pillow()
        pipeline = AssetPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            # Patch home so cache lands inside tmp
            with patch("pathlib.Path.home", return_value=Path(tmp) / "home"):
                src = Path(tmp) / "icon.png"
                _write_minimal_png(src)
                result = pipeline.prepare_icon(str(src), target_platform="windows")
        self.assertTrue(result["success"], msg=result.get("error"))
        self.assertEqual(result["format"], "ico")
        self.assertTrue(Path(result["path"]).exists())

    def test_prepare_icon_linux_produces_png(self) -> None:
        self._skip_if_no_pillow()
        pipeline = AssetPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("pathlib.Path.home", return_value=Path(tmp) / "home"):
                src = Path(tmp) / "icon.png"
                _write_minimal_png(src)
                result = pipeline.prepare_icon(str(src), target_platform="linux")
        self.assertTrue(result["success"], msg=result.get("error"))
        self.assertEqual(result["format"], "png")

    def test_prepare_icon_after_conversion_appears_in_list_assets(self) -> None:
        self._skip_if_no_pillow()
        pipeline = AssetPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("pathlib.Path.home", return_value=Path(tmp) / "home"):
                src = Path(tmp) / "icon.png"
                _write_minimal_png(src)
                pipeline.prepare_icon(str(src), target_platform="linux")
                listing = pipeline.list_assets(str(src))
        self.assertGreater(listing["count"], 0)


if __name__ == "__main__":
    unittest.main()
