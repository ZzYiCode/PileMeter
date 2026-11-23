from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
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


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="pile-meter-backend",
        version=__version__,
        environment=settings.environment,
        scale_status="relative",
        capabilities={
            "job_api": False,
            "vggt_reconstruction": False,
            "pointcloud_viewer": False,
            "volume_measurement": False,
        },
    )
