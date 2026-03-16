from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class SizeAnalyzer:
    """Analyse the size of a build output directory.

    Reports:
    - Total size
    - Top N largest files
    - Breakdown by file extension
    - Rough categorisation: Python source, compiled extensions, data, other
    """

    # Extension buckets
    _PYTHON_EXTS = {".py", ".pyc", ".pyo", ".pyd"}
    _NATIVE_EXTS = {".so", ".dll", ".dylib", ".pyd", ".exe"}
    _DATA_EXTS = {".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".txt", ".csv", ".xml", ".html"}
    _MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".mp4", ".mp3", ".wav"}

    def analyse(
        self,
        directory: str | Path,
        top_n: int = 20,
    ) -> dict[str, Any]:
        """Walk *directory* and return a full size report."""
        directory = Path(directory)
        if not directory.is_dir():
            return {"error": f"Directory not found: {directory}"}

        files_info: list[dict[str, Any]] = []
        ext_totals: dict[str, int] = {}
        category_totals: dict[str, int] = {
            "python": 0,
            "native": 0,
            "data": 0,
            "media": 0,
            "other": 0,
        }
        total_bytes = 0
        total_files = 0

        for root, _dirs, files in os.walk(directory):
            for filename in files:
                abs_path = Path(root) / filename
                try:
                    size = abs_path.stat().st_size
                except OSError:
                    continue
                rel = abs_path.relative_to(directory).as_posix()
                ext = abs_path.suffix.lower()

                files_info.append({"path": rel, "size_bytes": size, "ext": ext})
                ext_totals[ext] = ext_totals.get(ext, 0) + size
                total_bytes += size
                total_files += 1

                if ext in self._PYTHON_EXTS:
                    category_totals["python"] += size
                elif ext in self._NATIVE_EXTS:
                    category_totals["native"] += size
                elif ext in self._DATA_EXTS:
                    category_totals["data"] += size
                elif ext in self._MEDIA_EXTS:
                    category_totals["media"] += size
                else:
                    category_totals["other"] += size

        files_info.sort(key=lambda x: x["size_bytes"], reverse=True)
        top_files = files_info[:top_n]

        # Sort extension breakdown by size descending
        ext_breakdown = sorted(
            [{"ext": k or "(no ext)", "size_bytes": v} for k, v in ext_totals.items()],
            key=lambda x: x["size_bytes"],
            reverse=True,
        )

        return {
            "directory": str(directory),
            "total_bytes": total_bytes,
            "total_megabytes": round(total_bytes / (1024 * 1024), 3),
            "total_files": total_files,
            "top_files": [
                {
                    "path": f["path"],
                    "size_bytes": f["size_bytes"],
                    "size_kb": round(f["size_bytes"] / 1024, 1),
                }
                for f in top_files
            ],
            "by_extension": ext_breakdown,
            "by_category": {
                cat: {
                    "size_bytes": sz,
                    "percent": round(sz / total_bytes * 100, 1) if total_bytes else 0,
                }
                for cat, sz in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            },
        }
