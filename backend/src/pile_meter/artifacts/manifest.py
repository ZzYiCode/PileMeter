from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pile_meter import __version__
from pile_meter.domain.enums import ScaleStatus

SCHEMA_VERSION = "1.0"


def build_run_manifest(
    *,
    job_id: str,
    run_id: str,
    image_count: int,
    model_name: str = "not-configured",
    scale_status: ScaleStatus = ScaleStatus.RELATIVE,
    configuration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "software_version": __version__,
        "model": {
            "name": model_name,
        },
        "input": {
            "image_count": image_count,
            "preprocess_mode": None,
        },
        "coordinate_system": "vggt-world",
        "scale_status": scale_status.value,
        "configuration": configuration or {},
    }
