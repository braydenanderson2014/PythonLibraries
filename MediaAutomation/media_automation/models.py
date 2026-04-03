from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class JobConfig:
    name: str
    enabled: bool
    source_type: str
    source: str
    output_name: str
    ripper: str
    encoder: str
    ripper_candidates: List[str] = field(default_factory=list)
    subtitle_adapter: Optional[str] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineContext:
    dry_run: bool
    output_root: Path
    temp_root: Path
    executables: Dict[str, str]
    defaults: Dict[str, Any]


@dataclass
class JobArtifacts:
    ripped_file: Optional[Path] = None
    subtitled_file: Optional[Path] = None
    encoded_file: Optional[Path] = None
    logs: List[str] = field(default_factory=list)

    @property
    def latest_media_file(self) -> Optional[Path]:
        return self.encoded_file or self.subtitled_file or self.ripped_file
