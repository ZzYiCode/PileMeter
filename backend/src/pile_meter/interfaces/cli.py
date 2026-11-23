from __future__ import annotations

import argparse
import json
import math
import platform
from pathlib import Path

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
        "vggt_weights_present": (settings.model_root / "model.safetensors").is_file(),
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
    raise ValueError(f"Unsupported command: {args.command}")
