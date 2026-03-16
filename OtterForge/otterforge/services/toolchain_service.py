from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from typing import Any


TOOL_INSTALL_HINTS: dict[str, dict[str, Any]] = {
    "pyinstaller": {
        "managers": {
            "cross_platform": ["pipx install pyinstaller", "pip install pyinstaller"],
        }
    },
    "nuitka": {
        "managers": {
            "cross_platform": ["pipx install nuitka", "pip install nuitka"],
        }
    },
    "cxfreeze": {
        "managers": {
            "cross_platform": ["pipx install cx_Freeze", "pip install cx_Freeze"],
        }
    },
    "c": {
        "managers": {
            "windows": ["winget install -e --id LLVM.LLVM", "choco install mingw -y"],
            "linux": ["sudo apt-get install -y build-essential", "sudo dnf groupinstall -y \"Development Tools\""],
            "macos": ["xcode-select --install", "brew install gcc llvm"],
        }
    },
    "cpp": {
        "managers": {
            "windows": ["winget install -e --id LLVM.LLVM", "choco install mingw -y"],
            "linux": ["sudo apt-get install -y build-essential", "sudo dnf groupinstall -y \"Development Tools\""],
            "macos": ["xcode-select --install", "brew install gcc llvm"],
        }
    },
    "rust": {
        "managers": {
            "cross_platform": ["Install Rust using rustup from https://rustup.rs/"],
        }
    },
    "go": {
        "managers": {
            "windows": ["winget install -e --id GoLang.Go", "choco install golang -y"],
            "linux": ["sudo apt-get install -y golang-go", "sudo dnf install -y golang"],
            "macos": ["brew install go"],
        }
    },
    "pyarmor": {
        "managers": {
            "cross_platform": ["pipx install pyarmor", "pip install pyarmor"],
        }
    },
    "pyminifier": {
        "managers": {
            "cross_platform": ["pip install pyminifier3", "pip install pyminifier"],
        }
    },
    "cythonize": {
        "managers": {
            "cross_platform": ["pip install cython"],
        }
    },
    "javascript-obfuscator": {
        "managers": {
            "cross_platform": ["npm install -g javascript-obfuscator"],
        }
    },
    "garble": {
        "managers": {
            "cross_platform": ["go install mvdan.cc/garble@latest"],
        }
    },
    "native-strip": {
        "managers": {
            "linux": ["sudo apt-get install binutils"],
            "macos": ["brew install binutils"],
            "windows": ["choco install mingw"],
        }
    },
    "proguard": {
        "managers": {
            "linux": ["sudo apt-get install proguard"],
            "macos": ["brew install proguard"],
            "windows": ["choco install proguard"],
        }
    },
    "obfuscar": {
        "managers": {
            "cross_platform": ["dotnet tool install --global Obfuscar.GlobalTool"],
        }
    },
}


LANGUAGE_PACKS: dict[str, dict[str, Any]] = {
    "c_cpp": {
        "name": "C/C++ Toolchain",
        "description": "Compilers, linkers, and debuggers for C/C++ workflows.",
        "managers": {
            "windows": {
                "winget": [
                    "winget install -e --id MSYS2.MSYS2",
                    "winget install -e --id LLVM.LLVM",
                ],
                "choco": [
                    "choco install mingw -y",
                    "choco install llvm -y",
                ],
            },
            "linux": {
                "apt": [
                    "sudo apt-get update",
                    "sudo apt-get install -y build-essential gdb",
                ],
                "dnf": [
                    "sudo dnf groupinstall -y \"Development Tools\"",
                ],
            },
            "macos": {
                "brew": [
                    "xcode-select --install",
                    "brew install gcc llvm",
                ],
            },
        },
    },
    "java": {
        "name": "Java SDK",
        "description": "JDK toolchain for Java build and obfuscation workflows.",
        "managers": {
            "windows": {
                "winget": ["winget install -e --id Microsoft.OpenJDK.21"],
                "choco": ["choco install temurin21 -y"],
            },
            "linux": {
                "apt": [
                    "sudo apt-get update",
                    "sudo apt-get install -y openjdk-21-jdk",
                ],
                "dnf": ["sudo dnf install -y java-21-openjdk-devel"],
            },
            "macos": {
                "brew": ["brew install openjdk@21"],
            },
        },
    },
    "dotnet": {
        "name": ".NET SDK",
        "description": "Runtime and SDK tools for .NET applications and obfuscation.",
        "managers": {
            "windows": {
                "winget": ["winget install -e --id Microsoft.DotNet.SDK.8"],
                "choco": ["choco install dotnet-sdk -y"],
            },
            "linux": {
                "apt": [
                    "sudo apt-get update",
                    "sudo apt-get install -y dotnet-sdk-8.0",
                ],
                "dnf": ["sudo dnf install -y dotnet-sdk-8.0"],
            },
            "macos": {
                "brew": ["brew install dotnet"],
            },
        },
    },
    "nodejs": {
        "name": "Node.js + npm",
        "description": "Node runtime and npm for JavaScript toolchains.",
        "managers": {
            "windows": {
                "winget": ["winget install -e --id OpenJS.NodeJS.LTS"],
                "choco": ["choco install nodejs-lts -y"],
            },
            "linux": {
                "apt": [
                    "sudo apt-get update",
                    "sudo apt-get install -y nodejs npm",
                ],
                "dnf": ["sudo dnf install -y nodejs npm"],
            },
            "macos": {
                "brew": ["brew install node"],
            },
        },
    },
    "go": {
        "name": "Go SDK",
        "description": "Go compiler and tools for Go build/obfuscation.",
        "managers": {
            "windows": {
                "winget": ["winget install -e --id GoLang.Go"],
                "choco": ["choco install golang -y"],
            },
            "linux": {
                "apt": [
                    "sudo apt-get update",
                    "sudo apt-get install -y golang-go",
                ],
                "dnf": ["sudo dnf install -y golang"],
            },
            "macos": {
                "brew": ["brew install go"],
            },
        },
    },
}


PACKAGE_MANAGERS_BY_OS: dict[str, list[str]] = {
    "windows": ["winget", "choco", "uv", "pip", "npm"],
    "linux": ["apt", "dnf", "brew", "uv", "pip", "npm"],
    "macos": ["brew", "uv", "pip", "npm"],
}


class ToolchainService:
    def build_toolchain_report(
        self,
        builders: list[dict[str, Any]],
        obfuscators: list[dict[str, Any]],
    ) -> dict[str, Any]:
        tools: list[dict[str, Any]] = []

        for builder in builders:
            tools.append(
                {
                    "tool_id": str(builder["name"]),
                    "category": "builder",
                    "language_family": str(builder.get("language_family", "unknown")),
                    "available": bool(builder.get("available", False)),
                    "version": builder.get("version"),
                    "platforms": list(builder.get("platforms", [])),
                    "install": self._hint_for(str(builder["name"])),
                }
            )

        for obfuscator in obfuscators:
            tools.append(
                {
                    "tool_id": str(obfuscator["name"]),
                    "category": "obfuscator",
                    "language_family": str(obfuscator.get("language_family", "unknown")),
                    "available": bool(obfuscator.get("available", False)),
                    "version": obfuscator.get("version"),
                    "platforms": list(obfuscator.get("platforms", [])),
                    "install": self._hint_for(str(obfuscator["name"])),
                }
            )

        missing_tools = [tool for tool in tools if not tool["available"]]
        return {
            "tools": tools,
            "summary": {
                "total_tools": len(tools),
                "available_tools": len(tools) - len(missing_tools),
                "missing_tools": len(missing_tools),
            },
            "missing": missing_tools,
        }

    def _hint_for(self, tool_id: str) -> dict[str, Any]:
        hint = TOOL_INSTALL_HINTS.get(tool_id, {})
        managers = hint.get("managers", {})
        if managers:
            return {"managers": managers}
        return {
            "managers": {
                "cross_platform": [
                    f"Install '{tool_id}' using your preferred package manager and ensure it is on PATH."
                ]
            }
        }

    def list_language_packs(self) -> list[dict[str, Any]]:
        packs: list[dict[str, Any]] = []
        for pack_id, meta in LANGUAGE_PACKS.items():
            managers_by_os = {
                os_name: sorted(os_managers.keys())
                for os_name, os_managers in meta["managers"].items()
            }
            packs.append(
                {
                    "pack_id": pack_id,
                    "name": meta["name"],
                    "description": meta["description"],
                    "managers": managers_by_os,
                }
            )
        return sorted(packs, key=lambda item: str(item["pack_id"]))

    def plan_language_pack_install(
        self,
        pack_id: str,
        manager: str | None = None,
        os_name: str | None = None,
    ) -> dict[str, Any]:
        normalized_pack = pack_id.strip().lower()
        if normalized_pack not in LANGUAGE_PACKS:
            raise KeyError(f"Unknown language pack: {pack_id}")

        normalized_os = self._normalize_os_name(os_name)
        pack = LANGUAGE_PACKS[normalized_pack]
        per_os_managers = pack["managers"].get(normalized_os, {})
        if not per_os_managers:
            raise ValueError(f"Language pack '{pack_id}' has no manager entries for OS '{normalized_os}'")

        selected_manager = manager.strip().lower() if manager else sorted(per_os_managers.keys())[0]
        if selected_manager not in per_os_managers:
            supported = ", ".join(sorted(per_os_managers.keys()))
            raise ValueError(
                f"Language pack '{pack_id}' does not support manager '{selected_manager}' on {normalized_os}. "
                f"Supported: {supported}"
            )

        commands = list(per_os_managers[selected_manager])
        return {
            "pack_id": normalized_pack,
            "name": pack["name"],
            "os": normalized_os,
            "manager": selected_manager,
            "commands": commands,
            "requires_elevation": any(cmd.startswith("sudo ") for cmd in commands),
        }

    def install_language_pack(
        self,
        pack_id: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
        continue_on_error: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_language_pack_install(pack_id=pack_id, manager=manager, os_name=os_name)
        if not execute:
            return {
                **plan,
                "executed": False,
                "message": "Plan generated. Re-run with execute=true (or CLI --execute) to run commands.",
            }

        results: list[dict[str, Any]] = []
        for command in plan["commands"]:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )
            step = {
                "command": command,
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
            results.append(step)
            if process.returncode != 0 and not continue_on_error:
                break

        success = all(step["returncode"] == 0 for step in results)
        return {
            **plan,
            "executed": True,
            "success": success,
            "steps": results,
        }

    # ------------------------------------------------------------------ #
    # Package browser                                                      #
    # ------------------------------------------------------------------ #

    def list_language_pack_modules(self, os_name: str | None = None) -> list[dict[str, Any]]:
        normalized_os = self._normalize_os_name(os_name)
        modules: list[dict[str, Any]] = []

        for pack_id, meta in sorted(LANGUAGE_PACKS.items(), key=lambda item: item[0]):
            per_os_managers = dict(meta.get("managers", {})).get(normalized_os, {})
            install_candidates: list[dict[str, Any]] = []
            for manager_name, commands in sorted(per_os_managers.items()):
                install_candidates.append(
                    {
                        "manager": manager_name,
                        "available": self._is_package_manager_available(manager_name),
                        "install_commands": list(commands),
                        "supports_uninstall": False,
                    }
                )

            modules.append(
                {
                    "module_id": f"language-pack:{pack_id}",
                    "module_kind": "language_pack",
                    "name": str(meta.get("name", pack_id)),
                    "package_name": pack_id,
                    "pack_id": pack_id,
                    "description": str(meta.get("description", "")),
                    "source": "language_pack",
                    "installed": None,
                    "installed_version": None,
                    "install_candidates": install_candidates,
                }
            )

        return modules

    def build_package_module_entry(
        self,
        package_name: str,
        os_name: str | None = None,
        source: str = "package",
        preferred_manager: str | None = None,
        ecosystem: str | None = None,
        installed: bool | None = None,
        installed_version: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_name = package_name.strip()
        if not normalized_name:
            raise ValueError("Package name cannot be empty.")

        install_candidates = self.list_install_candidates_for_package(
            package_name=normalized_name,
            os_name=os_name,
            preferred_manager=preferred_manager,
            ecosystem=ecosystem,
        )

        return {
            "module_id": f"package:{normalized_name.lower()}",
            "module_kind": "package",
            "name": normalized_name,
            "package_name": normalized_name,
            "description": "",
            "source": source,
            "installed": installed,
            "installed_version": installed_version,
            "install_candidates": install_candidates,
            "metadata": metadata or {},
        }

    def list_install_candidates_for_package(
        self,
        package_name: str,
        os_name: str | None = None,
        preferred_manager: str | None = None,
        ecosystem: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized_package = package_name.strip()
        if not normalized_package:
            raise ValueError("Package name cannot be empty.")

        normalized_os = self._normalize_os_name(os_name)
        supported = list(PACKAGE_MANAGERS_BY_OS.get(normalized_os, []))
        python_managers = [manager for manager in ["uv", "pip"] if manager in supported]

        if ecosystem == "python":
            base_order = python_managers or supported
        else:
            base_order = supported

        ordered: list[str] = []
        preferred = (preferred_manager or "").strip().lower()
        if preferred:
            if preferred in supported:
                ordered.append(preferred)
            else:
                raise ValueError(
                    f"Manager '{preferred}' is not supported on {normalized_os}. Supported: {', '.join(supported)}"
                )

        for manager in base_order:
            if manager not in ordered:
                ordered.append(manager)

        candidates: list[dict[str, Any]] = []
        for manager in ordered:
            candidate: dict[str, Any] = {
                "manager": manager,
                "available": self._is_package_manager_available(manager),
                "supports_uninstall": True,
                "install_command": self._package_install_command(manager, normalized_package),
                "uninstall_command": self._package_uninstall_command(manager, normalized_package),
            }
            candidates.append(candidate)

        return candidates

    def list_package_managers(self, os_name: str | None = None) -> dict[str, Any]:
        normalized_os = self._normalize_os_name(os_name)
        managers: list[dict[str, Any]] = []
        for manager in PACKAGE_MANAGERS_BY_OS.get(normalized_os, []):
            managers.append(
                {
                    "manager": manager,
                    "available": self._is_package_manager_available(manager),
                    "command": self._manager_binary(manager),
                }
            )
        return {
            "os": normalized_os,
            "managers": managers,
        }

    def search_packages(
        self,
        query: str,
        manager: str | None = None,
        os_name: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Package query cannot be empty.")

        normalized_os = self._normalize_os_name(os_name)
        selected_manager = self._select_package_manager(manager, normalized_os)
        command = self._package_search_command(selected_manager, cleaned_query, limit)

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = process.stdout or process.stderr
        results = self._parse_package_search_output(selected_manager, combined_output, limit)

        return {
            "query": cleaned_query,
            "os": normalized_os,
            "manager": selected_manager,
            "command": command,
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "results": results,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }

    def install_package(
        self,
        package_name: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        cleaned_package = package_name.strip()
        if not cleaned_package:
            raise ValueError("Package name cannot be empty.")

        normalized_os = self._normalize_os_name(os_name)
        selected_manager = self._select_package_manager(manager, normalized_os)
        command = self._package_install_command(selected_manager, cleaned_package)

        plan = {
            "package": cleaned_package,
            "os": normalized_os,
            "manager": selected_manager,
            "command": command,
            "requires_elevation": bool(command and command[0] == "sudo"),
        }

        if not execute:
            return {
                **plan,
                "executed": False,
                "message": "Install plan generated. Re-run with execute=true to install.",
            }

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        return {
            **plan,
            "executed": True,
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }

    def uninstall_package(
        self,
        package_name: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        cleaned_package = package_name.strip()
        if not cleaned_package:
            raise ValueError("Package name cannot be empty.")

        normalized_os = self._normalize_os_name(os_name)
        selected_manager = self._select_package_manager(manager, normalized_os)
        command = self._package_uninstall_command(selected_manager, cleaned_package)

        plan = {
            "package": cleaned_package,
            "os": normalized_os,
            "manager": selected_manager,
            "command": command,
            "requires_elevation": bool(command and command[0] == "sudo"),
        }

        if not execute:
            return {
                **plan,
                "executed": False,
                "message": "Uninstall plan generated. Re-run with execute=true to uninstall.",
            }

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        return {
            **plan,
            "executed": True,
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }

    def _manager_binary(self, manager: str) -> str:
        if manager == "apt":
            return "apt-cache"
        if manager == "pip":
            return sys.executable
        if manager == "uv":
            return "uv"
        return manager

    def _is_package_manager_available(self, manager: str) -> bool:
        if manager == "pip":
            return True
        if manager == "uv":
            return shutil.which("uv") is not None
        if manager == "apt":
            return shutil.which("apt-cache") is not None or shutil.which("apt-get") is not None
        return shutil.which(manager) is not None

    def _select_package_manager(self, manager: str | None, normalized_os: str) -> str:
        supported = PACKAGE_MANAGERS_BY_OS.get(normalized_os, [])
        if manager:
            chosen = manager.strip().lower()
            if chosen not in supported:
                raise ValueError(
                    f"Manager '{chosen}' is not supported on {normalized_os}. Supported: {', '.join(supported)}"
                )
            return chosen

        for candidate in supported:
            if self._is_package_manager_available(candidate):
                return candidate

        if not supported:
            raise ValueError(f"No package managers configured for OS '{normalized_os}'.")
        return supported[0]

    def _package_search_command(self, manager: str, query: str, limit: int) -> list[str]:
        if manager == "winget":
            return ["winget", "search", query]
        if manager == "choco":
            return ["choco", "search", query, "--limit-output"]
        if manager == "apt":
            return ["apt-cache", "search", query]
        if manager == "dnf":
            return ["dnf", "search", query]
        if manager == "brew":
            return ["brew", "search", query]
        if manager == "pip":
            return [sys.executable, "-m", "pip", "index", "versions", query]
        if manager == "uv":
            # uv currently lacks a stable search command; use pip index for discovery.
            return [sys.executable, "-m", "pip", "index", "versions", query]
        if manager == "npm":
            return ["npm", "search", query, "--parseable"]
        raise ValueError(f"Unsupported package manager for search: {manager}")

    def _package_install_command(self, manager: str, package_name: str) -> list[str]:
        if manager == "winget":
            return ["winget", "install", package_name]
        if manager == "choco":
            return ["choco", "install", package_name, "-y"]
        if manager == "apt":
            return ["sudo", "apt-get", "install", "-y", package_name]
        if manager == "dnf":
            return ["sudo", "dnf", "install", "-y", package_name]
        if manager == "brew":
            return ["brew", "install", package_name]
        if manager == "pip":
            return [sys.executable, "-m", "pip", "install", package_name]
        if manager == "uv":
            return ["uv", "pip", "install", package_name]
        if manager == "npm":
            return ["npm", "install", "-g", package_name]
        raise ValueError(f"Unsupported package manager for install: {manager}")

    def _package_uninstall_command(self, manager: str, package_name: str) -> list[str]:
        if manager == "winget":
            return ["winget", "uninstall", package_name]
        if manager == "choco":
            return ["choco", "uninstall", package_name, "-y"]
        if manager == "apt":
            return ["sudo", "apt-get", "remove", "-y", package_name]
        if manager == "dnf":
            return ["sudo", "dnf", "remove", "-y", package_name]
        if manager == "brew":
            return ["brew", "uninstall", package_name]
        if manager == "pip":
            return [sys.executable, "-m", "pip", "uninstall", "-y", package_name]
        if manager == "uv":
            return ["uv", "pip", "uninstall", "-y", package_name]
        if manager == "npm":
            return ["npm", "uninstall", "-g", package_name]
        raise ValueError(f"Unsupported package manager for uninstall: {manager}")

    def _parse_package_search_output(self, manager: str, output: str, limit: int) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        seen: set[str] = set()
        for raw in output.splitlines():
            line = raw.strip()
            if not line:
                continue

            name = ""
            if manager == "choco" and "|" in line:
                name = line.split("|", 1)[0].strip()
            elif manager == "apt" and " - " in line:
                name = line.split(" - ", 1)[0].strip()
            elif manager == "npm" and "\t" in line:
                name = line.split("\t", 1)[0].strip()
            elif manager == "winget":
                lower = line.lower()
                if lower.startswith("name") or set(line) == {"-"}:
                    continue
                parts = line.split()
                name = parts[0].strip() if parts else ""
            elif manager == "brew":
                if line.startswith("==>"):
                    continue
                parts = line.split()
                name = parts[0].strip() if parts else ""
            elif manager == "pip":
                name = line.split(" ", 1)[0].strip()
            else:
                parts = line.split()
                name = parts[0].strip() if parts else ""

            if not name or name in seen:
                continue
            seen.add(name)
            results.append({"name": name, "line": line})

            if len(results) >= max(1, limit):
                break

        return results

    def _normalize_os_name(self, os_name: str | None) -> str:
        if os_name:
            value = os_name.strip().lower()
        else:
            value = platform.system().strip().lower()

        if value.startswith("win"):
            return "windows"
        if value.startswith("darwin") or value.startswith("mac"):
            return "macos"
        if value.startswith("linux"):
            return "linux"
        raise ValueError(f"Unsupported OS value: {os_name or value}")
