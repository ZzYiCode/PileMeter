from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pile_meter.domain.enums import ScaleStatus


@dataclass(slots=True)
class PipelineContext:
    job_id: str
    run_id: str
    artifact_dir: Path
    scale_status: ScaleStatus = ScaleStatus.RELATIVE
    metadata: dict[str, Any] = field(default_factory=dict)
    completed_steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    step_durations_ms: dict[str, float] = field(default_factory=dict)

    def ensure_artifact_dir(self) -> Path:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        return self.artifact_dir
