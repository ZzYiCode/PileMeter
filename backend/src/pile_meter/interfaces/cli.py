from __future__ import annotations

import argparse
import importlib.util
import json
import math
import platform
from pathlib import Path
from uuid import uuid4

from pile_meter import __version__
from pile_meter.pointcloud.io import write_ascii_ply
from pile_meter.settings import get_settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pile-meter", description="PileMeter developer CLI")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check local runtime configuration")

    demo_parser = subparsers.add_parser("demo-ply", help="Generate a relative-scale demo cloud")
    demo_parser.add_argument(
        "--output",
        type=Path,
        default=Path("runtime/demo/demo_pointcloud.ply"),
        help="Output PLY path",
    )

    reconstruct_parser = subparsers.add_parser(
        "reconstruct",
        help="Run local VGGT inference on a directory of RGB images",
    )
    reconstruct_parser.add_argument("--images", type=Path, required=True)
    reconstruct_parser.add_argument(
        "--output",
        type=Path,
        help="Run output directory; defaults to runtime/reconstructions/<run_id>",
    )
    reconstruct_parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    reconstruct_parser.add_argument("--max-images", type=int, default=6)
    reconstruct_parser.add_argument(
        "--confidence-quantile",
        type=float,
        default=25.0,
        help="Remove this percentage of the lowest-confidence points",
    )
    reconstruct_parser.add_argument("--max-view-points", type=int, default=350_000)
    return parser


def _doctor() -> None:
    settings = get_settings()
    settings.ensure_runtime_directories()
    report = {
        "service": "PileMeter",
        "version": __version__,
        "status": "ok",
        "python": platform.python_version(),
        "environment": settings.environment,
        "project_root": str(settings.project_root),
        "artifact_root": str(settings.artifact_root),
        "model_root": str(settings.model_root),
        "vggt_source": str(settings.vggt_source_root),
        "vggt_source_present": (settings.vggt_source_root / "vggt").is_dir(),
        "vggt_weights": str(settings.vggt_weights_path),
        "vggt_weights_present": settings.vggt_weights_path.is_file(),
        "torch_present": bool(importlib.util.find_spec("torch")),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _demo_points() -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    points: list[tuple[float, float, float]] = []
    colors: list[tuple[int, int, int]] = []
    grid = 41
    extent = 1.0

    for iy in range(grid):
        for ix in range(grid):
            x = -extent + 2 * extent * ix / (grid - 1)
            y = -extent + 2 * extent * iy / (grid - 1)
            radius = math.hypot(x, y)
            height = max(0.0, 0.55 * (1.0 - (radius / 0.9) ** 2))
            points.append((x, y, height))
            shade = min(235, 90 + int(height * 240))
            colors.append((shade, 150, 80))

    return points, colors


def _reconstruct(
    images: Path,
    output: Path | None,
    device: str,
    max_images: int,
    confidence_quantile: float,
    max_view_points: int,
) -> None:
    from pile_meter.contracts.reconstruction import ReconstructionRequest
    from pile_meter.reconstruction.vggt.adapter import VGGTReconstructor, discover_images

    settings = get_settings()
    settings.ensure_runtime_directories()
    image_paths = discover_images(images.resolve())
    run_id = uuid4().hex[:12]
    job_id = uuid4().hex
    output_directory = (
        output.resolve()
        if output is not None
        else settings.artifact_root / "reconstructions" / run_id
    )
    reconstructor = VGGTReconstructor(
        model_root=settings.model_root,
        weights_path=settings.vggt_weights_path,
        source_root=settings.vggt_source_root,
        device=device,
        max_images=max_images,
        confidence_quantile=confidence_quantile,
        max_view_points=max_view_points,
    )
    artifacts = reconstructor.reconstruct(
        ReconstructionRequest(
            job_id=job_id,
            run_id=run_id,
            image_paths=image_paths,
            output_directory=output_directory,
        )
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "model": artifacts.model_name,
                "image_count": artifacts.image_count,
                "scale_status": artifacts.scale_status,
                "pointcloud": str(artifacts.view_pointcloud_path),
                "manifest": str(output_directory / "manifest.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    args = _build_parser().parse_args()
    if args.command == "doctor":
        _doctor()
        return
    if args.command == "demo-ply":
        points, colors = _demo_points()
        output = write_ascii_ply(args.output, points, colors)
        print(json.dumps({"status": "ok", "pointcloud": str(output)}, ensure_ascii=False))
        return
    if args.command == "reconstruct":
        _reconstruct(
            images=args.images,
            output=args.output,
            device=args.device,
            max_images=args.max_images,
            confidence_quantile=args.confidence_quantile,
            max_view_points=args.max_view_points,
        )
        return
    raise ValueError(f"Unsupported command: {args.command}")
