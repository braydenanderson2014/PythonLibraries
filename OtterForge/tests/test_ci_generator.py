"""Tests for CIGenerator service."""
from __future__ import annotations

from pathlib import Path

import pytest

from otterforge.services.ci_generator import CIGenerator


@pytest.fixture()
def gen():
    return CIGenerator()


@pytest.fixture()
def project(tmp_path):
    return tmp_path


PROFILES = [
    {"platform": "windows", "builder_name": "pyinstaller", "profile_name": "win-release"},
    {"platform": "linux",   "builder_name": "pyinstaller", "profile_name": "linux-release"},
    {"platform": "macos",   "builder_name": "briefcase",   "profile_name": "mac-release"},
]


# ---------------------------------------------------------------------------
# GitHub Actions generation
# ---------------------------------------------------------------------------

class TestGenerateGitHubActions:
    def test_generates_workflow_key(self, gen, project):
        result = gen.generate_github_actions(project, PROFILES)
        assert "workflow" in result
        assert isinstance(result["workflow"], str)

    def test_returns_provider_github(self, gen, project):
        result = gen.generate_github_actions(project, PROFILES)
        assert result["provider"] == "github"

    def test_yaml_contains_all_platforms(self, gen, project):
        result = gen.generate_github_actions(project, PROFILES)
        yaml = result["workflow"]
        assert "windows-latest" in yaml
        assert "ubuntu-latest" in yaml
        assert "macos-latest" in yaml

    def test_yaml_contains_builders(self, gen, project):
        result = gen.generate_github_actions(project, PROFILES)
        yaml = result["workflow"]
        assert "pyinstaller" in yaml
        assert "briefcase" in yaml

    def test_yaml_contains_job_ids(self, gen, project):
        result = gen.generate_github_actions(project, PROFILES)
        yaml = result["workflow"]
        assert "win_release" in yaml or "win-release" in yaml

    def test_writes_file_when_output_path_given(self, gen, project):
        out = project / ".github" / "workflows" / "build.yml"
        result = gen.generate_github_actions(project, PROFILES, output_path=out)
        assert result["provider"] == "github"
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "windows-latest" in content

    def test_returns_job_count(self, gen, project):
        result = gen.generate_github_actions(project, PROFILES)
        assert result["jobs"] == len(PROFILES)

    def test_single_profile_generates_single_job(self, gen, project):
        result = gen.generate_github_actions(project, [PROFILES[0]])
        yaml = result["workflow"]
        assert "windows-latest" in yaml
        # Other runners should not appear
        assert "ubuntu-latest" not in yaml

    def test_empty_profiles_returns_zero_jobs(self, gen, project):
        result = gen.generate_github_actions(project, [])
        assert result["jobs"] == 0
        yaml = result["workflow"]
        assert "OtterForge" in yaml

    def test_platform_mapping_win_alias(self, gen, project):
        result = gen.generate_github_actions(
            project, [{"platform": "win", "builder_name": "pyinstaller", "profile_name": "p1"}]
        )
        yaml = result["workflow"]
        assert "windows-latest" in yaml
