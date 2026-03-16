"""Tests for HookRunner service."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import tempfile

from otterforge.services.hook_runner import HookRunner, VALID_EVENTS


class TestHookRunnerCRUD(unittest.TestCase):

    def _runner(self) -> HookRunner:
        return HookRunner(memory={})

    def test_add_hook_stores_entry(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            entry = runner.add_hook(tmp, "pre_build", "echo hello")
        self.assertEqual(entry["command"], "echo hello")

    def test_add_invalid_event_raises(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                runner.add_hook(tmp, "invalid_event", "echo bad")

    def test_list_hooks_returns_registered_events(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "pre_build", "echo one")
            runner.add_hook(tmp, "post_build", "echo two")
            hooks = runner.list_hooks(tmp)
        self.assertIn("pre_build", hooks)
        self.assertIn("post_build", hooks)

    def test_remove_hook_by_index(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "pre_build", "echo a")
            runner.add_hook(tmp, "pre_build", "echo b")
            removed = runner.remove_hook(tmp, "pre_build", 0)
            hooks = runner.list_hooks(tmp)
        self.assertTrue(removed)
        remaining = hooks.get("pre_build", [])
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["command"], "echo b")

    def test_remove_hook_out_of_range_returns_false(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "pre_build", "echo a")
            result = runner.remove_hook(tmp, "pre_build", 99)
        self.assertFalse(result)

    def test_clear_hooks_single_event(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "pre_build", "echo a")
            runner.add_hook(tmp, "post_build", "echo b")
            runner.clear_hooks(tmp, event="pre_build")
            hooks = runner.list_hooks(tmp)
        self.assertEqual(hooks.get("pre_build", []), [])
        self.assertEqual(len(hooks.get("post_build", [])), 1)

    def test_clear_hooks_all_events(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "pre_build", "echo a")
            runner.add_hook(tmp, "post_success", "echo b")
            runner.clear_hooks(tmp)
            hooks = runner.list_hooks(tmp)
        self.assertEqual(hooks, {})

    def test_hook_name_defaults_to_command_prefix(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            entry = runner.add_hook(tmp, "pre_build", "echo hello")
        self.assertEqual(entry["name"], "echo hello")

    def test_hook_explicit_name(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            entry = runner.add_hook(tmp, "pre_build", "echo hello", name="Greeting")
        self.assertEqual(entry["name"], "Greeting")


class TestHookRunnerExecution(unittest.TestCase):

    def _runner(self) -> HookRunner:
        return HookRunner(memory={})

    # Cross-platform echo command
    _ECHO = "echo test_output" if sys.platform != "win32" else "echo test_output"

    def test_run_event_returns_results_list(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "pre_build", self._ECHO)
            results = runner.run_event(tmp, "pre_build", cwd=tmp)
        self.assertEqual(len(results), 1)

    def test_successful_hook_has_returncode_zero(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "post_success", self._ECHO)
            results = runner.run_event(tmp, "post_success", cwd=tmp)
        self.assertEqual(results[0].returncode, 0)
        self.assertTrue(results[0].success)

    def test_failing_hook_has_nonzero_returncode(self) -> None:
        runner = self._runner()
        # 'exit 1' in shell, 'cmd /c exit 1' on windows — use python for portability
        fail_cmd = f"{sys.executable} -c \"import sys; sys.exit(1)\""
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "post_failure", fail_cmd, shell=True)
            results = runner.run_event(tmp, "post_failure", cwd=tmp)
        self.assertNotEqual(results[0].returncode, 0)
        self.assertFalse(results[0].success)

    def test_run_event_empty_no_hooks_returns_empty_list(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            results = runner.run_event(tmp, "pre_build", cwd=tmp)
        self.assertEqual(results, [])

    def test_run_event_invalid_event_raises(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                runner.run_event(tmp, "bad_event")

    def test_hooks_run_in_order(self) -> None:
        """Multiple hooks on the same event must run in registration order."""
        runner = self._runner()
        log: list[str] = []

        with tempfile.TemporaryDirectory() as tmp:
            # We can't rely on stdout ordering from subprocesses, so test order
            # via the membership of returned results list
            runner.add_hook(tmp, "pre_build", self._ECHO, name="first")
            runner.add_hook(tmp, "pre_build", self._ECHO, name="second")
            results = runner.run_event(tmp, "pre_build", cwd=tmp)

        self.assertEqual(results[0].name, "first")
        self.assertEqual(results[1].name, "second")

    def test_hook_result_to_dict(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "pre_build", self._ECHO)
            results = runner.run_event(tmp, "pre_build", cwd=tmp)
        d = results[0].to_dict()
        for key in ("event", "name", "command", "returncode", "stdout", "stderr", "success"):
            self.assertIn(key, d)

    def test_pre_and_post_events_independent(self) -> None:
        """Running post_build should not execute pre_build hooks."""
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            runner.add_hook(tmp, "pre_build", self._ECHO, name="pre")
            results = runner.run_event(tmp, "post_build", cwd=tmp)
        self.assertEqual(results, [])

    def test_all_valid_events_accepted(self) -> None:
        runner = self._runner()
        with tempfile.TemporaryDirectory() as tmp:
            for event in VALID_EVENTS:
                # Should not raise
                runner.add_hook(tmp, event, self._ECHO)
                results = runner.run_event(tmp, event, cwd=tmp)
                self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
