import json
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pile_meter import __version__
from pile_meter.settings import get_settings


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str
    scale_status: Literal["relative"]
    capabilities: dict[str, bool]


class ReconstructionResponse(BaseModel):
    run_id: str
    created_at: str
    model_name: str
    image_count: int
    point_count: int
    scale_status: str
    pointcloud_url: str
    cameras_url: str
    manifest_url: str
    bounds_size: list[float]


settings = get_settings()
settings.ensure_runtime_directories()

app = FastAPI(
    title="PileMeter API",
    version=__version__,
    description="Multi-view stockpile reconstruction and measurement API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.mount(
    "/artifacts",
    StaticFiles(directory=settings.artifact_root, check_dir=False),
    name="artifacts",
)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="pile-meter-backend",
        version=__version__,
        environment=settings.environment,
        scale_status="relative",
        capabilities={
            "job_api": False,
            "vggt_reconstruction": True,
            "pointcloud_viewer": True,
            "volume_measurement": False,
        },
    )


@app.get(
    "/api/v1/reconstructions/latest",
    response_model=ReconstructionResponse,
    tags=["reconstruction"],
)
def latest_reconstruction() -> ReconstructionResponse:
    reconstruction_root = settings.artifact_root / "reconstructions"
    manifests = sorted(
        reconstruction_root.glob("*/manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        raise HTTPException(
            status_code=404,
            detail="No reconstruction result found. Run 'pile-meter reconstruct' first.",
        )

    manifest_path = manifests[0]
    run_directory = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    relative_run = run_directory.relative_to(settings.artifact_root).as_posix()
    artifact_prefix = f"/artifacts/{relative_run}"
    pointcloud_name = manifest["artifacts"]["points_view"]
    cameras_name = manifest["artifacts"]["cameras"]
    return ReconstructionResponse(
        run_id=manifest["run_id"],
        created_at=manifest["created_at"],
        model_name=manifest["model"]["name"],
        image_count=manifest["input"]["image_count"],
        point_count=manifest["pointcloud"]["view_point_count"],
        scale_status=manifest["scale_status"],
        pointcloud_url=f"{artifact_prefix}/{pointcloud_name}",
        cameras_url=f"{artifact_prefix}/{cameras_name}",
        manifest_url=f"{artifact_prefix}/manifest.json",
        bounds_size=manifest["pointcloud"]["bounds_size"],
    )
