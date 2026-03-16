# OtterForge

OtterForge is a build orchestration tool under active development.

Current foundation includes:

- A layered package structure with separate API, UI, model, service, storage, MCP, and utility packages.
- User-selectable memory backends using JSON files or SQLite.
- Backend migration between JSON and SQLite.
- A CLI skeleton for memory and MCP administration.
- A minimal PyQt UI shell that uses the same backend services.

## Development

Set up a local Windows environment with the installer:

```powershell
.\install_windows.bat
```

This creates `.venv` in the project root, upgrades packaging tools, and installs OtterForge with the `full` extra set.

Run the CLI with:

```powershell
.\.venv\Scripts\python.exe -m otterforge --help
```

Launch the UI with:

```powershell
.\.venv\Scripts\python.exe -m otterforge ui
```
Or on Windows, use the batch launcher from the project root:

```powershell
.\launch_ui.bat
```

Call exposed MCP tools from the CLI:

```powershell
python -m otterforge mcp call list_builders
python -m otterforge mcp call inspect_builder --arg name=pyinstaller
python -m otterforge mcp read-only off
python -m otterforge mcp expose set_memory_backend
python -m otterforge mcp call set_memory_backend --arg backend=sql
```

Inspect available obfuscation adapters and preview obfuscation commands:

```powershell
python -m otterforge obfuscators list
python -m otterforge obfuscators inspect pyarmor
python -m otterforge obfuscate --project-path . --source .\main.py --dry-run -- --private
```

Get package-manager install guidance for missing build/obfuscation tools:

```powershell
python -m otterforge toolchain list
python -m otterforge toolchain doctor
```

List language packs (C/C++, Java, .NET, Node, Go) and generate install plans:

```powershell
python -m otterforge toolchain packs list
python -m otterforge toolchain packs install c_cpp --os windows --manager winget
```

Execute a selected language-pack install plan:

```powershell
python -m otterforge toolchain packs install java --os windows --manager winget --execute
```

Generate and manage capability manifest entries:

```powershell
python -m otterforge manifest refresh
python -m otterforge manifest show
python -m otterforge manifest disable builder.pyinstaller
python -m otterforge manifest enable builder.pyinstaller
```

Inspect module/dependency sources from pyproject and requirements files:

```powershell
python -m otterforge modules list
```

Current adapter set includes Python-focused tools (pyarmor, pyminifier, nuitka, cythonize) plus cross-language options such as javascript-obfuscator, garble (Go), native-strip, proguard (Java), and obfuscar (.NET).

Run obfuscation through MCP once the tool is exposed:

```powershell
python -m otterforge mcp expose run_obfuscation
python -m otterforge mcp read-only off
python -m otterforge mcp call run_obfuscation --arg project_path=. --arg source_path=.\main.py --arg dry_run=true
```

If dependencies are missing, run `.\install_windows.bat` to rebuild the local environment.

The UI now includes a Toolchain tab to view toolchain status, list module dependencies, and plan or run language-pack installs.