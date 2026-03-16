from __future__ import annotations

from pathlib import Path
from typing import Any


class MatrixRunner:
    """Run a list of build configs (profiles/builders) sequentially.

    Matrix entry schema:
      {
        "profile_name": str,   # optional profile to merge settings from
        "builder_name": str,
        "platform":     str,   # informational label ("windows", "linux", …)
        ...                    # any extra BuildRequest fields
      }
    """

    _SECTION = "matrix_configs"

    # --------------------------------------------------------------------- #
    # Config helpers                                                          #
    # --------------------------------------------------------------------- #

    def _configs(self, state: dict[str, Any]) -> dict[str, Any]:
        return state.setdefault(self._SECTION, {})

    def define_matrix(
        self,
        state: dict[str, Any],
        project_path: str | Path,
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        self._configs(state)[key] = entries
        return {"project": key, "entries": len(entries), "matrix": entries}

    def get_matrix(
        self, state: dict[str, Any], project_path: str | Path
    ) -> dict[str, Any]:
        key = str(Path(project_path).resolve())
        entries = self._configs(state).get(key)
        if entries is None:
            return {"error": f"No matrix defined for '{key}'"}
        return {"project": key, "entries": len(entries), "matrix": entries}

    # --------------------------------------------------------------------- #
    # Matrix execution                                                        #
    # --------------------------------------------------------------------- #

    def run_matrix(
        self,
        project_path: str | Path,
        entries: list[dict[str, Any]] | None,
        state: dict[str, Any],
        run_build_fn: Any,  # callable[dict] -> dict
    ) -> dict[str, Any]:
        if entries is None:
            cfg = self.get_matrix(state, project_path)
            if "error" in cfg:
                return {"success": False, "error": cfg["error"]}
            entries = cfg["matrix"]

        passed: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []

        for entry in entries:
            request = {
                "project_path": str(Path(project_path).resolve()),
                **entry,
            }
            try:
                result = run_build_fn(request)
            except Exception as exc:  # noqa: BLE001
                result = {
                    "success": False,
                    "error": str(exc),
                    "builder_name": entry.get("builder_name", "unknown"),
                }

            label = entry.get("builder_name", entry.get("profile_name", str(entry)))
            record = {
                "label": label,
                "platform": entry.get("platform", ""),
                "success": result.get("success", False),
                "result": result,
            }
            results.append(record)
            if record["success"]:
                passed.append(label)
            else:
                failed.append(label)

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "results": results,
            "all_passed": len(failed) == 0,
        }
