"""Tests for ChecksumService."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from otterforge.services.checksum_service import ChecksumService


@pytest.fixture()
def svc():
    return ChecksumService()


@pytest.fixture()
def artifact(tmp_path):
    f = tmp_path / "app.exe"
    f.write_bytes(b"hello world")
    return f


# ---------------------------------------------------------------------------
# compute_file_hash
# ---------------------------------------------------------------------------

class TestComputeFileHash:
    def test_matches_hashlib_directly(self, svc, tmp_path):
        f = tmp_path / "data.bin"
        data = b"OtterForge test data"
        f.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert svc.compute_file_hash(f) == expected

    def test_different_files_have_different_hashes(self, svc, tmp_path):
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"aaa")
        b.write_bytes(b"bbb")
        assert svc.compute_file_hash(a) != svc.compute_file_hash(b)


# ---------------------------------------------------------------------------
# write_checksums_file
# ---------------------------------------------------------------------------

class TestWriteChecksumsFile:
    def test_creates_file_in_output_dir(self, svc, tmp_path, artifact):
        out = tmp_path / "dist"
        svc.write_checksums_file([artifact], out)
        assert (out / ChecksumService.CHECKSUM_FILENAME).exists()

    def test_contains_correct_digest(self, svc, tmp_path, artifact):
        out = tmp_path / "dist"
        svc.write_checksums_file([artifact], out)
        content = (out / ChecksumService.CHECKSUM_FILENAME).read_text()
        expected_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        assert expected_digest in content

    def test_contains_filename_not_full_path(self, svc, tmp_path, artifact):
        out = tmp_path / "dist"
        svc.write_checksums_file([artifact], out)
        content = (out / ChecksumService.CHECKSUM_FILENAME).read_text()
        assert artifact.name in content
        assert str(artifact.parent) not in content

    def test_multiple_artifacts_all_listed(self, svc, tmp_path):
        a = tmp_path / "a.exe"
        b = tmp_path / "b.exe"
        a.write_bytes(b"aaaa")
        b.write_bytes(b"bbbb")
        out = tmp_path / "dist"
        svc.write_checksums_file([a, b], out)
        content = (out / ChecksumService.CHECKSUM_FILENAME).read_text()
        assert "a.exe" in content
        assert "b.exe" in content

    def test_nonexistent_artifact_skipped(self, svc, tmp_path, artifact):
        ghost = tmp_path / "ghost.exe"
        out = tmp_path / "dist"
        svc.write_checksums_file([artifact, ghost], out)
        content = (out / ChecksumService.CHECKSUM_FILENAME).read_text()
        assert "ghost.exe" not in content
        assert artifact.name in content


# ---------------------------------------------------------------------------
# verify_checksums_file
# ---------------------------------------------------------------------------

class TestVerifyChecksumsFile:
    def test_verify_correctly_written_file(self, svc, tmp_path, artifact):
        out = tmp_path / "dist"
        checksum_file = svc.write_checksums_file([artifact], out)

        # Copy artifact to the dist dir so verification can find it by name
        import shutil
        shutil.copy(artifact, out / artifact.name)

        result = svc.verify_checksums_file(checksum_file, out)
        assert result["ok"] is True
        assert artifact.name in result["passed"]

    def test_verify_detects_tampered_file(self, svc, tmp_path, artifact):
        out = tmp_path / "dist"
        checksum_file = svc.write_checksums_file([artifact], out)

        import shutil
        dist_copy = out / artifact.name
        shutil.copy(artifact, dist_copy)
        dist_copy.write_bytes(b"TAMPERED")

        result = svc.verify_checksums_file(checksum_file, out)
        assert result["ok"] is False

    def test_verify_missing_checksums_file_returns_error(self, svc, tmp_path):
        result = svc.verify_checksums_file(tmp_path / "nonexistent.txt", tmp_path)
        assert result["ok"] is False
        assert "error" in result


# ---------------------------------------------------------------------------
# compute_directory_hashes
# ---------------------------------------------------------------------------

class TestComputeDirectoryHashes:
    def test_returns_relative_paths(self, svc, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "file.txt").write_bytes(b"hello")
        result = svc.compute_directory_hashes(tmp_path)
        assert "sub/file.txt" in result

    def test_empty_directory_returns_empty_dict(self, svc, tmp_path):
        result = svc.compute_directory_hashes(tmp_path)
        assert result == {}
