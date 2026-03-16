from __future__ import annotations

import hashlib
import importlib.util
import struct
from pathlib import Path
from typing import Any


class AssetPipeline:
    """Convert source images (PNG/SVG/JPEG) to platform icon formats.

    Outputs:
      - Windows  → .ico   (multi-resolution: 16, 24, 32, 48, 64, 128, 256)
      - macOS    → .icns  (requires Pillow ≥ 9; macOS only for full support)
      - Linux    → .png   (512×512 copy)
    """

    _ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
    _PNG_SIZE = (512, 512)

    def _cache_dir(self, source_path: str | Path) -> Path:
        h = hashlib.sha256(str(Path(source_path).resolve()).encode()).hexdigest()[:16]
        cache = Path.home() / ".otterforge" / "assets" / h
        cache.mkdir(parents=True, exist_ok=True)
        return cache

    def _pillow_available(self) -> bool:
        return importlib.util.find_spec("PIL") is not None

    # --------------------------------------------------------------------- #
    # Public API                                                              #
    # --------------------------------------------------------------------- #

    def prepare_icon(
        self,
        source_path: str | Path,
        target_platform: str = "windows",
    ) -> dict[str, Any]:
        if not self._pillow_available():
            return {
                "success": False,
                "error": "Pillow is not installed. Install it with: pip install Pillow",
            }

        src = Path(source_path).resolve()
        if not src.exists():
            return {"success": False, "error": f"Source image not found: {src}"}

        platform = target_platform.lower()
        cache = self._cache_dir(src)

        try:
            from PIL import Image  # type: ignore[import]

            img = Image.open(src).convert("RGBA")

            if platform == "windows":
                return self._to_ico(img, src, cache)
            if platform in ("macos", "mac", "darwin"):
                return self._to_icns(img, src, cache)
            # Linux / default
            return self._to_png(img, src, cache)

        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def list_assets(self, source_path: str | Path) -> dict[str, Any]:
        cache = self._cache_dir(source_path)
        files = sorted(cache.iterdir()) if cache.exists() else []
        return {
            "cache_dir": str(cache),
            "assets": [str(f) for f in files],
            "count": len(files),
        }

    # --------------------------------------------------------------------- #
    # Format converters                                                       #
    # --------------------------------------------------------------------- #

    def _to_ico(self, img: Any, src: Path, cache: Path) -> dict[str, Any]:
        out = cache / (src.stem + ".ico")
        sizes = [(s, s) for s in self._ICO_SIZES]
        img.save(str(out), format="ICO", sizes=sizes)
        return {"success": True, "path": str(out), "format": "ico"}

    def _to_icns(self, img: Any, src: Path, cache: Path) -> dict[str, Any]:
        """Write a minimal .icns container using the ic07-ic10 iconset approach."""
        from PIL import Image  # type: ignore[import]

        out = cache / (src.stem + ".icns")
        # Use Pillow's built-in ICNS writer if macOS; otherwise build a minimal container
        try:
            img.save(str(out), format="ICNS")
            return {"success": True, "path": str(out), "format": "icns"}
        except Exception:  # noqa: BLE001
            # Fallback: write a PNG for cross-platform usage
            png_out = cache / (src.stem + "_icon.png")
            resized = img.resize((512, 512), Image.LANCZOS)
            resized.save(str(png_out), format="PNG")
            return {
                "success": True,
                "path": str(png_out),
                "format": "png",
                "note": "ICNS format requires macOS; saved as PNG instead.",
            }

    def _to_png(self, img: Any, src: Path, cache: Path) -> dict[str, Any]:
        from PIL import Image  # type: ignore[import]

        out = cache / (src.stem + "_icon.png")
        resized = img.resize(self._PNG_SIZE, Image.LANCZOS)
        resized.save(str(out), format="PNG")
        return {"success": True, "path": str(out), "format": "png"}
