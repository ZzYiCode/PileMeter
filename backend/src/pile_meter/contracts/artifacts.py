from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class ArtifactKind(StrEnum):
    PREDICTIONS = "predictions"
    POINT_CLOUD = "point_cloud"
    VIEW_POINT_CLOUD = "view_point_cloud"
    CAMERAS = "cameras"
    REPORT = "report"


class ArtifactRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ArtifactKind
    path: Path
    media_type: str
    size_bytes: int | None = None
    sha256: str | None = None
