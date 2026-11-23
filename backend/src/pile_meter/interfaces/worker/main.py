from __future__ import annotations

import json

from pile_meter.settings import get_settings


def main() -> None:
    """Print the worker scaffold status.

    Queue consumption and GPU pipeline execution will be added after the
    reconstruction adapter is integrated.
    """

    settings = get_settings()
    settings.ensure_runtime_directories()
    print(
        json.dumps(
            {
                "service": "pile-meter-worker",
                "status": "scaffold",
                "artifact_root": str(settings.artifact_root),
                "model_root": str(settings.model_root),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
