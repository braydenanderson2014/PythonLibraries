"""Tests for CommandTranslator service."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from otterforge.services.command_translator import CommandTranslator
from otterforge.models.build_request import BuildRequest


@pytest.fixture()
def translator():
    return CommandTranslator()


@pytest.fixture()
def entry_script(tmp_path):
    f = tmp_path / "main.py"
    f.write_text("print('hello')\n", encoding="utf-8")
    return f


def _state(entry: str | Path | None = None, builder: str = "pyinstaller", name: str = "MyApp"):
    return {
        "user_settings": {
            "project_path": ".",
            "entry_script": str(entry) if entry else None,
            "default_builder": builder,
            "app_name": name,
        }
    }


# ---------------------------------------------------------------------------
# build_request_from_memory
# ---------------------------------------------------------------------------

class TestBuildRequestFromMemory:
    def test_picks_builder_from_memory(self, translator, entry_script):
        state = _state(entry=entry_script, builder="nuitka")
        req = translator.build_request_from_memory(state)
        assert req.builder_name == "nuitka"

    def test_override_takes_precedence_over_memory(self, translator, entry_script):
        state = _state(entry=entry_script, builder="nuitka")
        req = translator.build_request_from_memory(state, overrides={"builder_name": "pyinstaller"})
        assert req.builder_name == "pyinstaller"

    def test_default_mode_is_onefile(self, translator, entry_script):
        state = _state(entry=entry_script)
        req = translator.build_request_from_memory(state)
        assert req.mode == "onefile"

    def test_dry_run_defaults_to_false(self, translator, entry_script):
        state = _state(entry=entry_script)
        req = translator.build_request_from_memory(state)
        assert req.dry_run is False

    def test_dry_run_override(self, translator, entry_script):
        state = _state(entry=entry_script)
        req = translator.build_request_from_memory(state, overrides={"dry_run": True})
        assert req.dry_run is True


# ---------------------------------------------------------------------------
# resolve_builder_name
# ---------------------------------------------------------------------------

class TestResolveBuilderName:
    def _req(self, builder="auto", lang="auto", entry=None):
        return BuildRequest(
            project_path=Path("."),
            builder_name=builder,
            language=lang,
            entry_script=Path(entry) if entry else None,
        )

    def test_explicit_builder_returned_as_is(self, translator):
        req = self._req(builder="nuitka")
        assert translator.resolve_builder_name(req) == "nuitka"

    def test_auto_builder_detects_python_from_extension(self, translator, tmp_path):
        entry = tmp_path / "main.py"
        entry.touch()
        req = self._req(builder="auto", entry=str(entry))
        assert translator.resolve_builder_name(req) == "pyinstaller"

    def test_auto_falls_back_to_pyinstaller(self, translator):
        req = self._req(builder="auto")
        assert translator.resolve_builder_name(req) == "pyinstaller"

    def test_language_override_selects_rust(self, translator):
        req = self._req(builder="auto", lang="rust")
        assert translator.resolve_builder_name(req) == "rust"

    def test_language_override_selects_go(self, translator):
        req = self._req(builder="auto", lang="go")
        assert translator.resolve_builder_name(req) == "go"

    def test_cpp_alias_normalised(self, translator):
        req = self._req(builder="auto", lang="c++")
        assert translator.resolve_builder_name(req) == "cpp"


# ---------------------------------------------------------------------------
# PyInstaller command translation
# ---------------------------------------------------------------------------

class TestPyInstallerTranslation:
    def test_onefile_flag(self, translator, entry_script):
        req = BuildRequest(
            project_path=entry_script.parent,
            builder_name="pyinstaller",
            entry_script=entry_script,
            mode="onefile",
        )
        cmd = translator.translate(req)
        assert "--onefile" in cmd
        assert str(entry_script) in cmd

    def test_onedir_flag(self, translator, entry_script):
        req = BuildRequest(
            project_path=entry_script.parent,
            builder_name="pyinstaller",
            entry_script=entry_script,
            mode="onedir",
        )
        cmd = translator.translate(req)
        assert "--onedir" in cmd

    def test_noconsole_flag(self, translator, entry_script):
        req = BuildRequest(
            project_path=entry_script.parent,
            builder_name="pyinstaller",
            entry_script=entry_script,
            console_mode=False,
        )
        cmd = translator.translate(req)
        assert "--noconsole" in cmd

    def test_name_flag(self, translator, entry_script):
        req = BuildRequest(
            project_path=entry_script.parent,
            builder_name="pyinstaller",
            entry_script=entry_script,
            executable_name="MyApp",
        )
        cmd = translator.translate(req)
        assert "--name" in cmd
        assert "MyApp" in cmd

    def test_clean_flag(self, translator, entry_script):
        req = BuildRequest(
            project_path=entry_script.parent,
            builder_name="pyinstaller",
            entry_script=entry_script,
            clean=True,
        )
        cmd = translator.translate(req)
        assert "--clean" in cmd

    def test_raw_args_appended(self, translator, entry_script):
        req = BuildRequest(
            project_path=entry_script.parent,
            builder_name="pyinstaller",
            entry_script=entry_script,
            raw_builder_args=["--hidden-import", "my_pkg"],
        )
        cmd = translator.translate(req)
        assert "--hidden-import" in cmd
        assert "my_pkg" in cmd
