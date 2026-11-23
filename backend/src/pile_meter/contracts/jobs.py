from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat

from pile_meter.domain.enums import BaseMode, JobStatus


class JobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    images: list[str] = Field(min_length=2)
    scale_length_m: PositiveFloat
    base_mode: BaseMode = BaseMode.PLANE
    notes: str = Field(default="", max_length=2000)


class JobAccepted(BaseModel):
    job_id: str
    status: JobStatus
