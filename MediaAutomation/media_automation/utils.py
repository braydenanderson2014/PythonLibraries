from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Iterable, List


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(p) for p in parts)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_command(parts: List[str], dry_run: bool = False) -> None:
    if dry_run:
        return
    subprocess.run(parts, check=True)
