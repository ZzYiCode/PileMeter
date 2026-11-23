from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    project_root: Path
    artifact_root: Path
    model_root: Path
    api_host: str
    api_port: int

    @classmethod
    def from_env(cls) -> Settings:
        project_root = Path.cwd().resolve()
        artifact_root = Path(
            os.getenv("PILE_METER_ARTIFACT_ROOT", str(project_root / "runtime"))
        ).resolve()
        model_root = Path(
            os.getenv("PILE_METER_MODEL_ROOT", str(project_root / "models"))
        ).resolve()
        return cls(
            environment=os.getenv("PILE_METER_ENV", "local"),
            project_root=project_root,
            artifact_root=artifact_root,
            model_root=model_root,
            api_host=os.getenv("PILE_METER_API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("PILE_METER_API_PORT", "8000")),
        )

    def ensure_runtime_directories(self) -> None:
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        (self.artifact_root / "jobs").mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
