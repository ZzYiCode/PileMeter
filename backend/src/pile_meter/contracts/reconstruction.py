from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ReconstructionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    run_id: str
    image_paths: list[Path] = Field(min_length=2)
    output_directory: Path


@dataclass(frozen=True, slots=True)
class ReconstructionArtifacts:
    model_name: str
    predictions_path: Path
    raw_pointcloud_path: Path
    view_pointcloud_path: Path
    cameras_path: Path
    image_count: int
    scale_status: str = "relative"
