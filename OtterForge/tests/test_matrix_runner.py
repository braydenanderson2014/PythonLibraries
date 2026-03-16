"""Tests for MatrixRunner service."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from otterforge.services.matrix_runner import MatrixRunner


@pytest.fixture()
def runner():
    return MatrixRunner()


@pytest.fixture()
def state():
    return {}


@pytest.fixture()
def project(tmp_path):
    return tmp_path


ENTRIES = [
    {"builder_name": "pyinstaller", "platform": "windows"},
    {"builder_name": "nuitka",      "platform": "linux"},
]


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

class TestConfig:
    def test_define_and_get_matrix(self, runner, state, project):
        result = runner.define_matrix(state, project, ENTRIES)
        assert result["entries"] == 2

        cfg = runner.get_matrix(state, project)
        assert len(cfg["matrix"]) == 2

    def test_get_matrix_missing_returns_error(self, runner, state, project):
        result = runner.get_matrix(state, project)
        assert "error" in result

    def test_define_overwrites_existing(self, runner, state, project):
        runner.define_matrix(state, project, ENTRIES)
        runner.define_matrix(state, project, [ENTRIES[0]])
        cfg = runner.get_matrix(state, project)
        assert cfg["entries"] == 1


# ---------------------------------------------------------------------------
# Matrix execution
# ---------------------------------------------------------------------------

class TestRunMatrix:
    def _make_run_fn(self, successes: list[bool]):
        """Return a run_build_fn that returns success True/False in sequence."""
        it = iter(successes)

        def fn(request: dict) -> dict:
            return {"success": next(it), "builder_name": request.get("builder_name")}

        return fn

    def test_all_passing_returns_all_passed(self, runner, state, project):
        fn = self._make_run_fn([True, True])
        result = runner.run_matrix(project, ENTRIES, state, fn)
        assert len(result["passed"]) == 2
        assert len(result["failed"]) == 0

    def test_one_failing_still_runs_all(self, runner, state, project):
        fn = self._make_run_fn([True, False])
        result = runner.run_matrix(project, ENTRIES, state, fn)
        assert len(result["passed"]) == 1
        assert len(result["failed"]) == 1

    def test_all_failing_returns_all_failed(self, runner, state, project):
        fn = self._make_run_fn([False, False])
        result = runner.run_matrix(project, ENTRIES, state, fn)
        assert len(result["failed"]) == 2

    def test_loads_matrix_from_state_when_entries_none(self, runner, state, project):
        runner.define_matrix(state, project, ENTRIES)
        fn = self._make_run_fn([True, True])
        result = runner.run_matrix(project, None, state, fn)
        assert result["total"] == 2

    def test_exception_in_builder_counts_as_failure(self, runner, state, project):
        def bad_fn(request):
            raise RuntimeError("builder exploded")

        result = runner.run_matrix(project, [ENTRIES[0]], state, bad_fn)
        assert len(result["failed"]) == 1

    def test_result_contains_per_entry_details(self, runner, state, project):
        fn = self._make_run_fn([True])
        result = runner.run_matrix(project, [ENTRIES[0]], state, fn)
        assert "results" in result
        assert len(result["results"]) == 1
