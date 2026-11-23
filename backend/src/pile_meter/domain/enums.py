from enum import StrEnum


class JobStatus(StrEnum):
    UPLOADING = "UPLOADING"
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    RECONSTRUCTING = "RECONSTRUCTING"
    MEASURING = "MEASURING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BaseMode(StrEnum):
    PLANE = "plane"
    KNOWN_DEM = "known_dem"
    CONTAINER = "container"
    MANUAL = "manual"


class ScaleStatus(StrEnum):
    RELATIVE = "relative"
    METRIC = "metric"


class QualityStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
