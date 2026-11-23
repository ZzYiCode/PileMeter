from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from pile_meter.domain.enums import BaseMode, JobStatus


class InvalidJobTransition(ValueError):
    """Raised when a job lifecycle transition is not allowed."""


_ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.UPLOADING: {JobStatus.QUEUED, JobStatus.FAILED},
    JobStatus.QUEUED: {JobStatus.VALIDATING, JobStatus.FAILED},
    JobStatus.VALIDATING: {JobStatus.RECONSTRUCTING, JobStatus.FAILED},
    JobStatus.RECONSTRUCTING: {JobStatus.MEASURING, JobStatus.FAILED},
    JobStatus.MEASURING: {JobStatus.COMPLETED, JobStatus.FAILED},
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
}


@dataclass(slots=True)
class Job:
    image_count: int
    scale_length_m: float
    base_mode: BaseMode = BaseMode.PLANE
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.UPLOADING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if self.image_count < 2:
            raise ValueError("At least two images are required")
        if self.scale_length_m <= 0:
            raise ValueError("scale_length_m must be positive")

    @property
    def is_terminal(self) -> bool:
        return self.status in {JobStatus.COMPLETED, JobStatus.FAILED}

    def transition_to(self, target: JobStatus, *, reason: str | None = None) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise InvalidJobTransition(f"Cannot transition from {self.status} to {target}")
        self.status = target
        self.updated_at = datetime.now(UTC)
        if target is JobStatus.FAILED:
            self.failure_reason = reason or "Unknown failure"
