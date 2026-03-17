from __future__ import annotations

import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path
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
    "git": {
        "managers": {
            "windows": ["winget install -e --id Git.Git", "choco install git -y"],
            "linux": ["sudo apt-get install -y git", "sudo dnf install -y git"],
            "macos": ["brew install git"],
        }
    },
    "docker": {
        "managers": {
            "windows": ["winget install -e --id Docker.DockerDesktop", "choco install docker-desktop -y"],
            "linux": ["sudo apt-get install -y docker.io", "sudo dnf install -y docker"],
            "macos": ["brew install --cask docker"],
        }
    },
    "uv": {
        "managers": {
            "windows": [
                "powershell -NoProfile -ExecutionPolicy Bypass -Command \"irm https://astral.sh/uv/install.ps1 | iex\""
            ],
            "linux": ["curl -LsSf https://astral.sh/uv/install.sh | sh"],
            "macos": ["curl -LsSf https://astral.sh/uv/install.sh | sh"],
        }
    },
}


LANGUAGE_PACKS: dict[str, dict[str, Any]] = {
    "c_cpp": {
        "name": "C/C++ Toolchain",
        "description": "Compilers, linkers, and debuggers for C/C++ workflows.",
        "detectors": {
            "windows": ["clang --version", "gcc --version", "cl"],
            "linux": ["gcc --version", "clang --version"],
            "macos": ["clang --version", "gcc --version"],
        },
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
        "detectors": {
            "windows": ["java -version"],
            "linux": ["java -version"],
            "macos": ["java -version"],
        },
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
        "detectors": {
            "windows": ["dotnet --version"],
            "linux": ["dotnet --version"],
            "macos": ["dotnet --version"],
        },
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
        "detectors": {
            "windows": ["node --version", "npm --version"],
            "linux": ["node --version", "npm --version"],
            "macos": ["node --version", "npm --version"],
        },
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
        "detectors": {
            "windows": ["go version"],
            "linux": ["go version"],
            "macos": ["go version"],
        },
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
    "windows": ["winget", "choco", "uv", "pip", "npm", "git", "docker"],
    "linux": ["apt", "dnf", "brew", "uv", "pip", "npm", "git", "docker"],
    "macos": ["brew", "uv", "pip", "npm", "git", "docker"],
}


TOOL_PACKAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "pyinstaller": {
        "tool_kind": "builder",
        "name": "PyInstaller",
        "package_name": "pyinstaller",
        "ecosystem": "python",
        "supported_os": ["windows", "linux", "macos"],
        "description": "Build standalone Python executables with PyInstaller.",
    },
    "nuitka": {
        "tool_kind": "builder",
        "name": "Nuitka",
        "package_name": "nuitka",
        "ecosystem": "python",
        "supported_os": ["windows", "linux", "macos"],
        "description": "Compile Python applications with Nuitka.",
    },
    "cxfreeze": {
        "tool_kind": "builder",
        "name": "cx_Freeze",
        "package_name": "cx_Freeze",
        "ecosystem": "python",
        "supported_os": ["windows", "linux", "macos"],
        "description": "Freeze Python applications with cx_Freeze.",
        "aliases": ["cx-freeze", "cx_freeze"],
    },
    "briefcase": {
        "tool_kind": "builder",
        "name": "Briefcase",
        "package_name": "briefcase",
        "ecosystem": "python",
        "supported_os": ["windows", "linux", "macos"],
        "description": "Package Python apps as native applications with Briefcase.",
    },
    "shiv": {
        "tool_kind": "builder",
        "name": "shiv",
        "package_name": "shiv",
        "ecosystem": "python",
        "supported_os": ["windows", "linux", "macos"],
        "description": "Create zipapp-style Python executables with shiv.",
    },
    "py2exe": {
        "tool_kind": "builder",
        "name": "py2exe",
        "package_name": "py2exe",
        "ecosystem": "python",
        "supported_os": ["windows"],
        "description": "Build Windows executables from Python applications with py2exe.",
    },
    "py2app": {
        "tool_kind": "builder",
        "name": "py2app",
        "package_name": "py2app",
        "ecosystem": "python",
        "supported_os": ["macos"],
        "description": "Build macOS app bundles from Python applications with py2app.",
    },
}


INTEGRATION_TOOL_DEFINITIONS: dict[str, dict[str, Any]] = {
    "uv": {
        "name": "uv",
        "description": "Fast Python package manager used for Python dependency installs.",
        "binary": "uv",
        "version_command": ["uv", "--version"],
        "supported_os": ["windows", "linux", "macos"],
        "managers": {
            "windows": {
                "powershell": [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "irm https://astral.sh/uv/install.ps1 | iex",
                ],
            },
            "linux": {
                "sh": ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
            },
            "macos": {
                "sh": ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
            },
        },
    },
    "git": {
        "name": "Git / GitHub",
        "description": "Required for GitHub repository clone/import workflows and git-based operations.",
        "binary": "git",
        "version_command": ["git", "--version"],
        "supported_os": ["windows", "linux", "macos"],
        "managers": {
            "windows": {
                "winget": ["winget", "install", "-e", "--id", "Git.Git"],
                "choco": ["choco", "install", "git", "-y"],
            },
            "linux": {
                "apt": ["sudo", "apt-get", "install", "-y", "git"],
                "dnf": ["sudo", "dnf", "install", "-y", "git"],
            },
            "macos": {
                "brew": ["brew", "install", "git"],
            },
        },
    },
    "docker": {
        "name": "Docker",
        "description": "Required for containerized build workflows.",
        "binary": "docker",
        "version_command": ["docker", "--version"],
        "supported_os": ["windows", "linux", "macos"],
        "managers": {
            "windows": {
                "winget": ["winget", "install", "-e", "--id", "Docker.DockerDesktop"],
                "choco": ["choco", "install", "docker-desktop", "-y"],
            },
            "linux": {
                "apt": ["sudo", "apt-get", "install", "-y", "docker.io"],
                "dnf": ["sudo", "dnf", "install", "-y", "docker"],
            },
            "macos": {
                "brew": ["brew", "install", "--cask", "docker"],
            },
        },
    },
}


class ToolchainService:
    GITHUB_URL_RE = re.compile(
        r"^https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?(?:/)?$",
        re.IGNORECASE,
    )

    def _merged_language_packs(
        self,
        custom_packs: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, dict[str, Any]]:
        merged = {pack_id: dict(meta) for pack_id, meta in LANGUAGE_PACKS.items()}
        for pack_id, meta in (custom_packs or {}).items():
            normalized_pack = str(pack_id).strip().lower()
            if not normalized_pack:
                continue
            if not isinstance(meta, dict):
                continue
            merged[normalized_pack] = dict(meta)
        return merged

    def _detect_language_pack_installation(
        self,
        pack_meta: dict[str, Any],
        normalized_os: str,
    ) -> tuple[bool | None, str | None]:
        detectors_by_os = pack_meta.get("detectors", {})
        if not isinstance(detectors_by_os, dict):
            return None, None

        detectors = detectors_by_os.get(normalized_os, [])
        if not isinstance(detectors, list) or not detectors:
            return None, None

        for detector in detectors:
            command: list[str]
            if isinstance(detector, str):
                command = shlex.split(detector)
            elif isinstance(detector, dict):
                raw_command = detector.get("command", [])
                if isinstance(raw_command, str):
                    command = shlex.split(raw_command)
                elif isinstance(raw_command, list):
                    command = [str(item) for item in raw_command if str(item).strip()]
                else:
                    continue
            else:
                continue

            if not command:
                continue

            executable = command[0]
            if shutil.which(executable) is None:
                continue

            try:
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,
                )
            except Exception:
                continue

            if process.returncode != 0:
                continue

            version_line = ""
            for stream in [process.stdout, process.stderr]:
                if stream:
                    version_line = stream.splitlines()[0].strip()
                    if version_line:
                        break

            return True, (version_line or None)

        return False, None

    def _normalize_language_pack_imports(self, pack_meta: dict[str, Any]) -> list[dict[str, Any]]:
        entries = pack_meta.get("third_party_imports", [])
        if not isinstance(entries, list):
            return []

        normalized: list[dict[str, Any]] = []
        for entry in entries:
            if isinstance(entry, str):
                package_name = entry.strip()
                if not package_name:
                    continue
                normalized.append(
                    {
                        "import_name": package_name,
                        "package_name": package_name,
                        "ecosystem": "python",
                        "manager": None,
                        "description": "",
                    }
                )
                continue

            if not isinstance(entry, dict):
                continue

            package_name = str(entry.get("package_name", "")).strip()
            import_name = str(entry.get("import_name", package_name)).strip()
            if not package_name:
                continue

            normalized.append(
                {
                    "import_name": import_name or package_name,
                    "package_name": package_name,
                    "ecosystem": str(entry.get("ecosystem", "python")).strip().lower() or "python",
                    "manager": str(entry.get("manager", "")).strip().lower() or None,
                    "description": str(entry.get("description", "")).strip(),
                }
            )

        return normalized

    def _build_language_pack_dependency_modules(
        self,
        pack_id: str,
        pack_meta: dict[str, Any],
        normalized_os: str,
    ) -> list[dict[str, Any]]:
        modules: list[dict[str, Any]] = []
        for dep in self._normalize_language_pack_imports(pack_meta):
            package_name = str(dep.get("package_name", "")).strip()
            if not package_name:
                continue

            ecosystem = str(dep.get("ecosystem", "python")).strip().lower() or None
            preferred_manager = dep.get("manager")

            installed = None
            installed_version = None
            if ecosystem == "python":
                installed_version = self._python_package_version(package_name)
                installed = installed_version is not None

            try:
                install_candidates = self.list_install_candidates_for_package(
                    package_name=package_name,
                    os_name=normalized_os,
                    preferred_manager=str(preferred_manager) if preferred_manager else None,
                    ecosystem=ecosystem,
                )
            except Exception:
                install_candidates = []

            modules.append(
                {
                    "module_id": f"language-pack-dependency:{pack_id}:{package_name.lower()}",
                    "module_kind": "language_pack_dependency",
                    "name": package_name,
                    "package_name": package_name,
                    "description": str(dep.get("description", "")).strip(),
                    "source": "language_pack_dependency",
                    "installed": installed,
                    "installed_version": installed_version,
                    "install_candidates": install_candidates,
                    "metadata": {
                        "pack_id": pack_id,
                        "import_name": dep.get("import_name"),
                        "ecosystem": ecosystem,
                    },
                }
            )

        return modules

    def build_toolchain_report(
        self,
        builders: list[dict[str, Any]],
        obfuscators: list[dict[str, Any]],
        integration_tools: list[dict[str, Any]] | None = None,
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

        for integration_tool in integration_tools or []:
            tools.append(
                {
                    "tool_id": str(integration_tool["tool_id"]),
                    "category": "integration",
                    "language_family": str(integration_tool.get("language_family", "integration")),
                    "available": bool(integration_tool.get("available", False)),
                    "version": integration_tool.get("version"),
                    "platforms": list(integration_tool.get("platforms", [])),
                    "install": integration_tool.get("install") or self._hint_for(str(integration_tool["tool_id"])),
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

    def list_language_packs(
        self,
        custom_packs: dict[str, dict[str, Any]] | None = None,
        os_name: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized_os = self._normalize_os_name(os_name)
        packs: list[dict[str, Any]] = []
        merged = self._merged_language_packs(custom_packs)
        custom_pack_ids = {str(item).strip().lower() for item in (custom_packs or {}).keys()}
        for pack_id, meta in merged.items():
            managers = meta.get("managers", {})
            if not isinstance(managers, dict):
                managers = {}
            managers_by_os = {
                os_name: sorted(os_managers.keys())
                for os_name, os_managers in managers.items()
                if isinstance(os_managers, dict)
            }
            installed, installed_version = self._detect_language_pack_installation(meta, normalized_os)
            third_party_imports = self._normalize_language_pack_imports(meta)
            packs.append(
                {
                    "pack_id": pack_id,
                    "name": meta["name"],
                    "description": meta["description"],
                    "managers": managers_by_os,
                    "installed": installed,
                    "installed_version": installed_version,
                    "third_party_imports": third_party_imports,
                    "source": "custom" if pack_id in custom_pack_ids else "builtin",
                }
            )
        return sorted(packs, key=lambda item: str(item["pack_id"]))

    def plan_language_pack_install(
        self,
        pack_id: str,
        manager: str | None = None,
        os_name: str | None = None,
        custom_packs: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        normalized_pack = pack_id.strip().lower()
        merged = self._merged_language_packs(custom_packs)
        if normalized_pack not in merged:
            raise KeyError(f"Unknown language pack: {pack_id}")

        normalized_os = self._normalize_os_name(os_name)
        pack = merged[normalized_pack]
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
        custom_packs: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        plan = self.plan_language_pack_install(
            pack_id=pack_id,
            manager=manager,
            os_name=os_name,
            custom_packs=custom_packs,
        )
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

    def is_integration_tool_available(self, tool_id: str) -> bool:
        definition = INTEGRATION_TOOL_DEFINITIONS.get(tool_id.strip().lower())
        if definition is None:
            raise KeyError(f"Unknown integration tool: {tool_id}")
        binary = str(definition.get("binary", "")).strip()
        return bool(binary and shutil.which(binary) is not None)

    def _integration_tool_version(self, tool_id: str) -> str | None:
        definition = INTEGRATION_TOOL_DEFINITIONS.get(tool_id.strip().lower())
        if definition is None:
            return None

        binary = str(definition.get("binary", "")).strip()
        version_command = list(definition.get("version_command", []))
        if not binary or not version_command or shutil.which(binary) is None:
            return None

        try:
            result = subprocess.run(
                version_command,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except Exception:
            return None

        if result.returncode != 0:
            return None
        output = result.stdout.strip() or result.stderr.strip()
        return output.splitlines()[0] if output else None

    def list_integration_tools(self, os_name: str | None = None) -> list[dict[str, Any]]:
        normalized_os = self._normalize_os_name(os_name)
        tools: list[dict[str, Any]] = []

        for tool_id, definition in sorted(INTEGRATION_TOOL_DEFINITIONS.items()):
            supported_os = [str(item).strip().lower() for item in definition.get("supported_os", [])]
            if supported_os and normalized_os not in supported_os:
                continue

            tools.append(
                {
                    "tool_id": tool_id,
                    "category": "integration",
                    "language_family": "integration",
                    "available": self.is_integration_tool_available(tool_id),
                    "version": self._integration_tool_version(tool_id),
                    "platforms": supported_os,
                    "install": self._hint_for(tool_id),
                    "description": str(definition.get("description", "")),
                }
            )

        return tools

    def list_integration_modules(self, os_name: str | None = None) -> list[dict[str, Any]]:
        normalized_os = self._normalize_os_name(os_name)
        modules: list[dict[str, Any]] = []

        for tool_id, definition in sorted(INTEGRATION_TOOL_DEFINITIONS.items()):
            supported_os = [str(item).strip().lower() for item in definition.get("supported_os", [])]
            if supported_os and normalized_os not in supported_os:
                continue

            managers_for_os = definition.get("managers", {}).get(normalized_os, {})
            install_candidates: list[dict[str, Any]] = []
            for manager_name, command in sorted(managers_for_os.items()):
                install_candidates.append(
                    {
                        "manager": manager_name,
                        "available": self._is_package_manager_available(manager_name),
                        "supports_uninstall": False,
                        "install_command": list(command),
                        "uninstall_command": [],
                    }
                )

            modules.append(
                {
                    "module_id": f"integration:{tool_id}",
                    "module_kind": "integration_tool",
                    "name": str(definition.get("name", tool_id)),
                    "package_name": tool_id,
                    "tool_id": tool_id,
                    "description": str(definition.get("description", "")),
                    "source": "integration",
                    "installed": self.is_integration_tool_available(tool_id),
                    "installed_version": self._integration_tool_version(tool_id),
                    "install_candidates": install_candidates,
                    "metadata": {
                        "binary": definition.get("binary"),
                    },
                }
            )

        return modules

    def install_integration_tool(
        self,
        tool_id: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        normalized_tool = tool_id.strip().lower()
        definition = INTEGRATION_TOOL_DEFINITIONS.get(normalized_tool)
        if definition is None:
            raise KeyError(f"Unknown integration tool: {tool_id}")

        normalized_os = self._normalize_os_name(os_name)

        # uv uses dedicated bootstrap logic to support PATH registration.
        if normalized_tool == "uv":
            result = self.install_uv(os_name=normalized_os, execute=execute)
            return {
                **result,
                "tool_id": "uv",
                "name": str(definition.get("name", "uv")),
                "manager": "bootstrap",
                "manager_available": True,
                "installed_before": bool(result.get("already_available", False)),
            }

        managers_for_os = definition.get("managers", {}).get(normalized_os, {})
        if not managers_for_os:
            raise ValueError(
                f"Integration tool '{tool_id}' has no installer entries for OS '{normalized_os}'"
            )

        if manager:
            selected_manager = manager.strip().lower()
            if selected_manager not in managers_for_os:
                supported = ", ".join(sorted(managers_for_os.keys()))
                raise ValueError(
                    f"Integration tool '{tool_id}' does not support manager '{selected_manager}' on {normalized_os}. "
                    f"Supported: {supported}"
                )
        else:
            available_managers = [
                manager_name
                for manager_name in sorted(managers_for_os.keys())
                if self._is_package_manager_available(manager_name)
            ]
            selected_manager = available_managers[0] if available_managers else sorted(managers_for_os.keys())[0]

        command = list(managers_for_os[selected_manager])
        manager_available = self._is_package_manager_available(selected_manager)
        binary_name = str(definition.get("binary", "")).strip()

        plan = {
            "tool_id": normalized_tool,
            "name": str(definition.get("name", normalized_tool)),
            "os": normalized_os,
            "manager": selected_manager,
            "manager_available": manager_available,
            "command": command,
            "installed_before": bool(binary_name and shutil.which(binary_name) is not None),
        }

        if not execute:
            return {
                **plan,
                "executed": False,
                "message": "Install plan generated. Re-run with execute=true to install this integration tool.",
            }

        if not manager_available:
            return {
                **plan,
                "executed": True,
                "success": False,
                "returncode": 127,
                "stdout": "",
                "stderr": f"Package manager '{selected_manager}' is not available on PATH.",
            }

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            return {
                **plan,
                "executed": True,
                "success": False,
                "returncode": 127,
                "stdout": "",
                "stderr": str(exc),
            }

        discovered_binary = shutil.which(binary_name) if binary_name else None
        path_registration = None
        if process.returncode == 0 and discovered_binary:
            path_registration = self._try_register_directory_to_path(str(Path(discovered_binary).parent))

        return {
            **plan,
            "executed": True,
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "binary": discovered_binary,
            "installed_after": bool(discovered_binary),
            "path_registration": path_registration,
        }

    def list_language_pack_modules(
        self,
        os_name: str | None = None,
        custom_packs: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        normalized_os = self._normalize_os_name(os_name)
        modules: list[dict[str, Any]] = []

        merged = self._merged_language_packs(custom_packs)
        custom_pack_ids = set((custom_packs or {}).keys())

        for pack_id, meta in sorted(merged.items(), key=lambda item: item[0]):
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

            installed, installed_version = self._detect_language_pack_installation(meta, normalized_os)
            third_party_imports = self._normalize_language_pack_imports(meta)

            modules.append(
                {
                    "module_id": f"language-pack:{pack_id}",
                    "module_kind": "language_pack",
                    "name": str(meta.get("name", pack_id)),
                    "package_name": pack_id,
                    "pack_id": pack_id,
                    "description": str(meta.get("description", "")),
                    "source": "language_pack",
                    "installed": installed,
                    "installed_version": installed_version,
                    "install_candidates": install_candidates,
                    "metadata": {
                        "pack_source": "custom" if pack_id in custom_pack_ids else "builtin",
                        "third_party_import_count": len(third_party_imports),
                        "third_party_imports": third_party_imports,
                    },
                }
            )

            modules.extend(
                self._build_language_pack_dependency_modules(
                    pack_id=pack_id,
                    pack_meta=meta,
                    normalized_os=normalized_os,
                )
            )

        return modules

    def list_tool_modules(
        self,
        tools: list[dict[str, Any]],
        os_name: str | None = None,
        tool_kind: str = "builder",
    ) -> list[dict[str, Any]]:
        normalized_os = self._normalize_os_name(os_name)
        modules: list[dict[str, Any]] = []

        for tool in tools:
            tool_id = str(tool.get("name", "")).strip().lower()
            if not tool_id:
                continue

            definition = TOOL_PACKAGE_DEFINITIONS.get(tool_id)
            if definition is None:
                continue
            if str(definition.get("tool_kind", "")).strip().lower() != tool_kind:
                continue

            supported_os = [str(item).strip().lower() for item in definition.get("supported_os", [])]
            if supported_os and normalized_os not in supported_os:
                continue

            package_name = str(definition.get("package_name", tool_id)).strip()
            ecosystem = str(definition.get("ecosystem", "")).strip() or None
            install_candidates = self.list_install_candidates_for_package(
                package_name=package_name,
                os_name=normalized_os,
                ecosystem=ecosystem,
            )

            python_installed_version = None
            if ecosystem == "python":
                python_installed_version = self._python_package_version(package_name)

            installed = bool(tool.get("available", False))
            installed_version = str(tool.get("version")) if tool.get("version") else None
            if python_installed_version:
                installed = True
                installed_version = python_installed_version

            modules.append(
                {
                    "module_id": f"{tool_kind}:{tool_id}",
                    "module_kind": f"{tool_kind}_tool",
                    "name": str(definition.get("name", tool.get("name", tool_id))),
                    "package_name": package_name,
                    "tool_id": tool_id,
                    "description": str(definition.get("description", "")),
                    "source": tool_kind,
                    "installed": installed,
                    "installed_version": installed_version,
                    "install_candidates": install_candidates,
                    "metadata": {
                        "tool_kind": tool_kind,
                        "language_family": tool.get("language_family"),
                        "platforms": list(tool.get("platforms", [])),
                    },
                }
            )

        return modules

    def search_known_tool_modules(
        self,
        query: str,
        tools: list[dict[str, Any]],
        os_name: str | None = None,
        tool_kind: str = "builder",
    ) -> list[dict[str, Any]]:
        needle = query.strip().lower()
        if not needle:
            return []

        modules: list[dict[str, Any]] = []
        for module in self.list_tool_modules(tools=tools, os_name=os_name, tool_kind=tool_kind):
            haystacks = [
                str(module.get("tool_id", "")).lower(),
                str(module.get("name", "")).lower(),
                str(module.get("package_name", "")).lower(),
                str(module.get("description", "")).lower(),
            ]
            if any(needle in haystack for haystack in haystacks):
                modules.append(module)
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

    def _parse_github_repo_url(self, repo_url: str) -> tuple[str, str, str]:
        cleaned = repo_url.strip()
        match = self.GITHUB_URL_RE.match(cleaned)
        if not match:
            raise ValueError("GitHub URL must look like https://github.com/owner/repo")

        owner = str(match.group("owner")).strip()
        repo = str(match.group("repo")).strip()
        canonical_url = f"https://github.com/{owner}/{repo}.git"
        return owner, repo, canonical_url

    def build_github_repo_module_entry(
        self,
        repo_url: str,
        destination_root: str | None = None,
        branch: str | None = None,
    ) -> dict[str, Any]:
        owner, repo, canonical_url = self._parse_github_repo_url(repo_url)
        root = Path(destination_root).expanduser().resolve() if destination_root else (Path.home() / "OtterForgeRepos")
        target_dir = (root / owner / repo).resolve()

        return {
            "module_id": f"github_repo:{owner.lower()}/{repo.lower()}",
            "module_kind": "github_repo",
            "name": f"{owner}/{repo}",
            "package_name": f"{owner}/{repo}",
            "description": "GitHub repository source checkout",
            "source": "github",
            "installed": target_dir.exists(),
            "installed_version": None,
            "install_candidates": [
                {
                    "manager": "git",
                    "available": shutil.which("git") is not None,
                    "supports_uninstall": False,
                    "install_command": self._github_clone_command(canonical_url, str(target_dir), branch=branch),
                    "uninstall_command": [],
                }
            ],
            "metadata": {
                "repo_url": canonical_url,
                "owner": owner,
                "repo": repo,
                "branch": (branch or "").strip() or None,
                "destination_root": str(root),
                "target_dir": str(target_dir),
            },
        }

    def _github_clone_command(self, repo_url: str, target_dir: str, branch: str | None = None) -> list[str]:
        command = ["git", "clone", "--depth", "1"]
        clean_branch = (branch or "").strip()
        if clean_branch:
            command.extend(["--branch", clean_branch])
        command.extend([repo_url, target_dir])
        return command

    def install_github_repo(
        self,
        repo_url: str,
        destination_root: str | None = None,
        branch: str | None = None,
        existing_policy: str = "error",
        execute: bool = False,
    ) -> dict[str, Any]:
        module = self.build_github_repo_module_entry(
            repo_url=repo_url,
            destination_root=destination_root,
            branch=branch,
        )
        metadata = dict(module.get("metadata", {}))
        target_dir = str(metadata.get("target_dir", "")).strip()
        canonical_url = str(metadata.get("repo_url", "")).strip()
        clean_branch = str(metadata.get("branch") or "").strip() or None
        clean_policy = (existing_policy or "error").strip().lower()
        if clean_policy not in {"error", "pull", "clone_or_pull"}:
            raise ValueError("existing_policy must be one of: error, pull, clone_or_pull")
        command = self._github_clone_command(canonical_url, target_dir, branch=clean_branch)

        plan = {
            "repo_url": canonical_url,
            "destination_root": metadata.get("destination_root"),
            "target_dir": target_dir,
            "branch": clean_branch,
            "existing_policy": clean_policy,
            "manager": "git",
            "command": command,
            "installed": bool(module.get("installed")),
        }

        if not execute:
            return {
                **plan,
                "executed": False,
                "message": "GitHub clone plan generated. Re-run with execute=true to clone.",
            }

        if shutil.which("git") is None:
            return {
                **plan,
                "executed": True,
                "success": False,
                "returncode": 127,
                "stdout": "",
                "stderr": "git executable was not found on PATH.",
            }

        target_path = Path(target_dir)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            if clean_policy in {"pull", "clone_or_pull"}:
                pull_command = ["git", "-C", str(target_path), "pull", "--ff-only"]
                process = subprocess.run(
                    pull_command,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                return {
                    **plan,
                    "command": pull_command,
                    "executed": True,
                    "success": process.returncode == 0,
                    "returncode": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "operation": "pull",
                }
            return {
                **plan,
                "executed": True,
                "success": False,
                "returncode": 1,
                "stdout": "",
                "stderr": f"Target directory already exists: {target_dir}",
                "operation": "clone",
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
            "operation": "clone",
        }

    def list_install_candidates_for_package(
        self,
        package_name: str,
        os_name: str | None = None,
        preferred_manager: str | None = None,
        ecosystem: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized_package = self._resolve_package_name(package_name.strip(), ecosystem=ecosystem)
        if not normalized_package:
            raise ValueError("Package name cannot be empty.")

        normalized_os = self._normalize_os_name(os_name)
        supported = [
            manager
            for manager in PACKAGE_MANAGERS_BY_OS.get(normalized_os, [])
            if self._manager_capabilities(manager).get("supports_package_ops", False)
        ]
        python_managers = [manager for manager in ["pip", "uv"] if manager in supported]

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

    def _python_package_version(self, package_name: str) -> str | None:
        try:
            return importlib_metadata.version(package_name)
        except importlib_metadata.PackageNotFoundError:
            return None
        except Exception:
            return None

    def list_package_managers(self, os_name: str | None = None) -> dict[str, Any]:
        normalized_os = self._normalize_os_name(os_name)
        managers: list[dict[str, Any]] = []
        for manager in PACKAGE_MANAGERS_BY_OS.get(normalized_os, []):
            capabilities = self._manager_capabilities(manager)
            managers.append(
                {
                    "manager": manager,
                    "available": self._is_package_manager_available(manager),
                    "command": self._manager_binary(manager),
                    "capabilities": capabilities,
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
        ecosystem: str | None = None,
    ) -> dict[str, Any]:
        cleaned_package = self._resolve_package_name(package_name.strip(), ecosystem=ecosystem)
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

        result: dict[str, Any] = {
            **plan,
            "executed": True,
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }

        if result["success"] and selected_manager in {"pip", "uv"}:
            result["path_registration"] = self._try_register_scripts_to_path()

        return result

    def uninstall_package(
        self,
        package_name: str,
        manager: str | None = None,
        os_name: str | None = None,
        execute: bool = False,
        ecosystem: str | None = None,
    ) -> dict[str, Any]:
        cleaned_package = self._resolve_package_name(package_name.strip(), ecosystem=ecosystem)
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

    def install_uv(
        self,
        os_name: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        normalized_os = self._normalize_os_name(os_name)
        command = self._uv_bootstrap_command(normalized_os)
        already_available = shutil.which("uv") is not None

        plan = {
            "os": normalized_os,
            "command": command,
            "already_available": already_available,
            "path_registration": None,
        }

        if not execute:
            return {
                **plan,
                "executed": False,
                "message": "uv install plan generated. Re-run with execute=true to install and register PATH.",
            }

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            return {
                **plan,
                "executed": True,
                "success": False,
                "returncode": 127,
                "stdout": "",
                "stderr": str(exc),
            }

        uv_binary = self._locate_uv_binary()
        path_registration = None
        if process.returncode == 0 and uv_binary:
            path_registration = self._try_register_directory_to_path(str(Path(uv_binary).parent))

        return {
            **plan,
            "executed": True,
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "uv_binary": uv_binary,
            "path_registration": path_registration,
        }

    def _uv_bootstrap_command(self, normalized_os: str) -> list[str]:
        if normalized_os == "windows":
            return [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "irm https://astral.sh/uv/install.ps1 | iex",
            ]
        return ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]

    def _locate_uv_binary(self) -> str | None:
        discovered = shutil.which("uv")
        if discovered:
            return discovered

        candidates = [
            Path.home() / ".local" / "bin" / ("uv.exe" if sys.platform == "win32" else "uv"),
            Path.home() / ".cargo" / "bin" / ("uv.exe" if sys.platform == "win32" else "uv"),
            Path(self._get_python_scripts_dir()) / ("uv.exe" if sys.platform == "win32" else "uv"),
        ]
        for candidate in candidates:
            try:
                if candidate.exists():
                    return str(candidate)
            except Exception:
                continue
        return None

    def _manager_binary(self, manager: str) -> str:
        if manager == "apt":
            return "apt-cache"
        if manager == "pip":
            return sys.executable
        if manager == "uv":
            return "uv"
        return manager

    def _manager_capabilities(self, manager: str) -> dict[str, Any]:
        package_ops = manager in {"winget", "choco", "apt", "dnf", "brew", "pip", "uv", "npm"}
        return {
            "supports_package_search": package_ops,
            "supports_package_install": package_ops,
            "supports_package_uninstall": package_ops,
            "supports_package_ops": package_ops,
            "supports_github": manager == "git",
            "supports_container": manager == "docker",
        }

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
            if not self._manager_capabilities(chosen).get("supports_package_ops", False):
                raise ValueError(
                    f"Manager '{chosen}' is available for integrations but does not support package search/install."
                )
            return chosen

        for candidate in supported:
            if (
                self._manager_capabilities(candidate).get("supports_package_ops", False)
                and self._is_package_manager_available(candidate)
            ):
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

    def _resolve_package_name(self, package_name: str, ecosystem: str | None = None) -> str:
        cleaned = package_name.strip()
        if not cleaned:
            return cleaned

        if ecosystem not in {None, "", "python"}:
            return cleaned

        normalized = cleaned.lower().replace("-", "").replace("_", "")
        for tool_id, definition in TOOL_PACKAGE_DEFINITIONS.items():
            candidates = [tool_id, str(definition.get("package_name", "")), *definition.get("aliases", [])]
            for candidate in candidates:
                candidate_key = str(candidate).strip().lower().replace("-", "").replace("_", "")
                if candidate_key == normalized:
                    return str(definition.get("package_name", cleaned))

        return cleaned

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

    # ------------------------------------------------------------------ #
    # PATH registration helpers                                            #
    # ------------------------------------------------------------------ #

    def _get_python_scripts_dir(self) -> str:
        """Return the Scripts (Windows) or bin (Unix) directory for sys.executable."""
        return str(Path(sys.executable).parent.resolve())

    def _normalize_path_entry(self, value: str) -> str:
        cleaned = str(value or "").strip().strip('"')
        if not cleaned:
            return ""
        expanded = os.path.expandvars(os.path.expanduser(cleaned))
        return os.path.normcase(os.path.normpath(expanded))

    def _is_scripts_dir_in_path(self, scripts_dir: str) -> bool:
        """Return True if scripts_dir is already in the persistent user PATH."""
        return self._is_directory_in_path(scripts_dir)

    def _is_directory_in_path(self, directory: str) -> bool:
        target = self._normalize_path_entry(directory)
        if not target:
            return False

        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ)
                try:
                    current_path, _ = winreg.QueryValueEx(key, "Path")
                except FileNotFoundError:
                    current_path = ""
                finally:
                    winreg.CloseKey(key)
                return any(
                    self._normalize_path_entry(p) == target
                    for p in current_path.split(";") if p
                )
            except Exception:
                return False
        else:
            return any(
                self._normalize_path_entry(p) == target
                for p in os.environ.get("PATH", "").split(":")
            )

    def _add_scripts_dir_to_path(self, scripts_dir: str) -> bool:
        """Persistently add scripts_dir to the user PATH. Returns True on success."""
        return self._add_directory_to_path(scripts_dir)

    def _add_directory_to_path(self, directory: str) -> bool:
        target_dir = str(Path(directory).expanduser())
        normalized_target = self._normalize_path_entry(target_dir)
        if not normalized_target:
            return False

        if sys.platform == "win32":
            try:
                import ctypes
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    "Environment",
                    0,
                    winreg.KEY_READ | winreg.KEY_WRITE,
                )
                try:
                    try:
                        current_path, reg_type = winreg.QueryValueEx(key, "Path")
                    except FileNotFoundError:
                        current_path = ""
                        reg_type = winreg.REG_EXPAND_SZ
                    dirs = [
                        d for d in current_path.split(";")
                        if d and self._normalize_path_entry(d) != normalized_target
                    ]
                    dirs.append(target_dir)
                    winreg.SetValueEx(key, "Path", 0, reg_type, ";".join(dirs))
                finally:
                    winreg.CloseKey(key)
                # Broadcast WM_SETTINGCHANGE so Explorer/shell picks up the new PATH
                ctypes.windll.user32.SendMessageTimeoutW(
                    0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None
                )
                return True
            except Exception:
                return False
        else:
            profile = Path.home() / ".profile"
            export_line = f'\nexport PATH="{target_dir}:$PATH"  # added by OtterForge\n'
            try:
                content = profile.read_text() if profile.exists() else ""
                if target_dir not in content:
                    with open(profile, "a") as fh:
                        fh.write(export_line)
                    return True
                return False
            except Exception:
                return False

    def _try_register_scripts_to_path(self) -> dict[str, Any]:
        """Add the current Python's scripts dir to the persistent user PATH if missing."""
        scripts_dir = self._get_python_scripts_dir()
        registration = self._try_register_directory_to_path(scripts_dir)
        return {
            "scripts_dir": scripts_dir,
            "already_in_path": registration["already_in_path"],
            "registered": registration["registered"],
            "path": registration["path"],
        }

    def _try_register_directory_to_path(self, directory: str) -> dict[str, Any]:
        target_dir = str(Path(directory).expanduser())
        if self._is_directory_in_path(target_dir):
            return {"path": target_dir, "already_in_path": True, "registered": False}
        registered = self._add_directory_to_path(target_dir)
        return {"path": target_dir, "already_in_path": False, "registered": registered}
