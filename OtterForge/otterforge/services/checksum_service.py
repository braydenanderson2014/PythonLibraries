from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ChecksumService:
    """Compute SHA-256 checksums for build artifacts and write release manifests."""

    HASH_ALGORITHM = "sha256"
    CHECKSUM_FILENAME = "checksums.sha256.txt"
    MANIFEST_FILENAME = "release_manifest.json"

    # ------------------------------------------------------------------
    # Core checksum computation
    # ------------------------------------------------------------------

    def compute_file_hash(self, file_path: str | Path) -> str:
        """Return the hex SHA-256 digest of a single file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def compute_directory_hashes(self, directory: str | Path) -> dict[str, str]:
        """Return {relative_path: sha256_hex} for every file in directory (recursive)."""
        directory = Path(directory)
        result: dict[str, str] = {}
        for root, _dirs, files in os.walk(directory):
            for filename in sorted(files):
                abs_path = Path(root) / filename
                rel_path = abs_path.relative_to(directory).as_posix()
                result[rel_path] = self.compute_file_hash(abs_path)
        return result

    # ------------------------------------------------------------------
    # Checksum file
    # ------------------------------------------------------------------

    def write_checksums_file(
        self,
        artifact_paths: list[str | Path],
        output_dir: str | Path,
    ) -> str:
        """Write a <name>  <file> style checksums file.  Returns the output path."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / self.CHECKSUM_FILENAME

        lines: list[str] = []
        for artifact in sorted(str(a) for a in artifact_paths):
            if os.path.isfile(artifact):
                digest = self.compute_file_hash(artifact)
                filename = Path(artifact).name
                lines.append(f"{digest}  {filename}")

        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(out_path)

    def verify_checksums_file(self, checksums_file: str | Path, directory: str | Path) -> dict[str, Any]:
        """Verify artifacts in directory against a checksums file.

        Returns: {ok: bool, passed: [...], failed: [...]}
        """
        checksums_file = Path(checksums_file)
        directory = Path(directory)

        if not checksums_file.exists():
            return {"ok": False, "error": "Checksums file not found", "passed": [], "failed": []}

        passed: list[str] = []
        failed: list[str] = []

        for line in checksums_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            expected_digest, filename = parts
            file_path = directory / filename
            if not file_path.exists():
                failed.append(f"{filename}: file not found")
                continue
            actual_digest = self.compute_file_hash(file_path)
            if actual_digest == expected_digest:
                passed.append(filename)
            else:
                failed.append(f"{filename}: expected {expected_digest}, got {actual_digest}")

        return {"ok": len(failed) == 0, "passed": passed, "failed": failed}

    # ------------------------------------------------------------------
    # Release manifest
    # ------------------------------------------------------------------

    def write_release_manifest(
        self,
        artifact_paths: list[str | Path],
        output_dir: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Write a JSON release manifest.  Returns the output path."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / self.MANIFEST_FILENAME

        artifacts_info: list[dict[str, Any]] = []
        for artifact in sorted(str(a) for a in artifact_paths):
            abs_path = Path(artifact)
            if abs_path.is_file():
                artifacts_info.append(
                    {
                        "filename": abs_path.name,
                        "path": str(abs_path),
                        "size_bytes": abs_path.stat().st_size,
                        "sha256": self.compute_file_hash(abs_path),
                    }
                )

        manifest: dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_count": len(artifacts_info),
            "artifacts": artifacts_info,
        }
        if metadata:
            manifest.update(metadata)

        out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return str(out_path)

    def generate(
        self,
        artifact_paths: list[str | Path],
        output_dir: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Convenience: write both checksum file and release manifest.

        Returns: {checksums_file: ..., manifest_file: ...}
        """
        checksums_file = self.write_checksums_file(artifact_paths, output_dir)
        manifest_file = self.write_release_manifest(artifact_paths, output_dir, metadata=metadata)
        return {"checksums_file": checksums_file, "manifest_file": manifest_file}
