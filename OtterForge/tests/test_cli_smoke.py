"""CLI smoke tests for core command wiring and JSON output shape."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from otterforge.cli import main


def _run_cli(args: list[str], capsys) -> tuple[int, Any]:
    code = main(args)
    captured = capsys.readouterr()
    assert captured.out.strip(), "CLI produced no stdout payload"
    return code, json.loads(captured.out)


def test_builders_list_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(["builders", "list"], capsys)

    assert code == 0
    assert isinstance(payload, list)
    assert any(item.get("name") == "pyinstaller" for item in payload)


def test_manifest_show_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(["manifest", "show"], capsys)

    assert code == 0
    assert isinstance(payload, dict)
    assert payload.get("manifest_version") == 1
    assert isinstance(payload.get("entries"), list)


def test_scan_scope_files_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    app = tmp_path / "app.py"
    app.write_text("print('scan')\n", encoding="utf-8")

    code, payload = _run_cli(["scan", str(tmp_path), "--scope", "files"], capsys)

    assert code == 0
    assert isinstance(payload, dict)
    assert payload.get("scope") == "files"
    files = payload.get("files")
    assert isinstance(files, list)
    assert any(item.get("name") == "app.py" for item in files)


def test_memory_show_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(["memory", "show"], capsys)

    assert code == 0
    assert isinstance(payload, dict)
    assert "user_settings" in payload
    assert "build_history" in payload


def test_build_dry_run_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    entry = tmp_path / "app.py"
    entry.write_text("print('ok')\n", encoding="utf-8")

    code, payload = _run_cli(
        [
            "build",
            "--builder",
            "pyinstaller",
            "--entry",
            str(entry),
            "--project-path",
            str(tmp_path),
            "--dry-run",
        ],
        capsys,
    )

    assert code == 0
    assert payload.get("success") is True
    assert payload.get("exit_code") == 0
    final_command = payload.get("final_command")
    assert isinstance(final_command, list)
    assert final_command
    assert "pyinstaller" in str(final_command[0]).lower()


def test_toolchain_packages_managers_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(["toolchain", "packages", "managers", "--os", "windows"], capsys)

    assert code == 0
    assert isinstance(payload, dict)
    assert payload.get("os") == "windows"
    managers = payload.get("managers")
    assert isinstance(managers, list)
    assert any(item.get("manager") == "pip" for item in managers)


def test_toolchain_install_uv_plan_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(["toolchain", "install-uv", "--os", "windows"], capsys)

    assert code == 0
    assert isinstance(payload, dict)
    assert payload.get("executed") is False
    assert payload.get("os") == "windows"
    assert isinstance(payload.get("command"), list)


def test_toolchain_integrations_list_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(["toolchain", "integrations", "list", "--os", "windows"], capsys)

    assert code == 0
    assert isinstance(payload, dict)
    assert payload.get("count", 0) >= 3
    tools = payload.get("tools")
    assert isinstance(tools, list)
    tool_ids = {item.get("tool_id") for item in tools}
    assert "uv" in tool_ids
    assert "git" in tool_ids
    assert "docker" in tool_ids


def test_toolchain_integrations_install_plan_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(
        ["toolchain", "integrations", "install", "git", "--os", "windows", "--manager", "winget"],
        capsys,
    )

    assert code == 0
    assert isinstance(payload, dict)
    assert payload.get("executed") is False
    assert payload.get("tool_id") == "git"
    assert isinstance(payload.get("command"), list)


def test_toolchain_packages_install_plan_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(
        [
            "toolchain",
            "packages",
            "install",
            "requests",
            "--manager",
            "pip",
        ],
        capsys,
    )

    assert code == 0
    assert payload.get("operation") == "install"
    assert payload.get("executed") is False
    results = payload.get("results")
    assert isinstance(results, list)
    assert results and results[0].get("package") == "requests"


def test_toolchain_packages_uninstall_plan_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    code, payload = _run_cli(
        [
            "toolchain",
            "packages",
            "uninstall",
            "requests",
            "--manager",
            "pip",
        ],
        capsys,
    )

    assert code == 0
    assert payload.get("operation") == "uninstall"
    assert payload.get("executed") is False
    results = payload.get("results")
    assert isinstance(results, list)
    assert results and results[0].get("package") == "requests"


def test_toolchain_deps_analyze_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    app = tmp_path / "app.py"
    app.write_text("import requests\n", encoding="utf-8")
    req = tmp_path / "requirements.txt"
    req.write_text("requests>=2\n", encoding="utf-8")

    code, payload = _run_cli(["toolchain", "deps", "analyze", str(tmp_path)], capsys)

    assert code == 0
    assert isinstance(payload, dict)
    assert "dependency_inventory" in payload
    assert "missing_dependencies" in payload


def test_toolchain_deps_install_missing_plan_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    app = tmp_path / "app.py"
    app.write_text("import totally_fake_dep_xyz\n", encoding="utf-8")

    code, payload = _run_cli(
        [
            "toolchain",
            "deps",
            "install-missing",
            str(tmp_path),
            "--manager",
            "pip",
        ],
        capsys,
    )

    assert code == 0
    assert payload.get("operation") == "install-missing"
    assert payload.get("executed") is False
    assert isinstance(payload.get("results"), list)
