import pytest

from pile_meter.domain.enums import JobStatus
from pile_meter.domain.job import InvalidJobTransition, Job


def test_job_follows_happy_path() -> None:
    job = Job(image_count=6, scale_length_m=0.5)

    for status in [
        JobStatus.QUEUED,
        JobStatus.VALIDATING,
        JobStatus.RECONSTRUCTING,
        JobStatus.MEASURING,
        JobStatus.COMPLETED,
    ]:
        job.transition_to(status)

    assert job.status is JobStatus.COMPLETED
    assert job.is_terminal


def test_job_rejects_invalid_transition() -> None:
    job = Job(image_count=6, scale_length_m=0.5)

    with pytest.raises(InvalidJobTransition):
        job.transition_to(JobStatus.COMPLETED)
