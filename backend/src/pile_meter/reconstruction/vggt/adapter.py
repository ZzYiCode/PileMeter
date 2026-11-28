from __future__ import annotations

import gc
import json
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps

from pile_meter.artifacts.manifest import build_run_manifest
from pile_meter.contracts.reconstruction import ReconstructionArtifacts, ReconstructionRequest
from pile_meter.pointcloud.io import write_binary_ply

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
IMAGE_SIZE = 518


def discover_images(image_directory: Path) -> list[Path]:
    if not image_directory.is_dir():
        raise FileNotFoundError(f"Image directory does not exist: {image_directory}")
    paths = sorted(
        path.resolve()
        for path in image_directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )
    if len(paths) < 2:
        raise ValueError("At least two images are required for multi-view reconstruction")
    return paths


def select_evenly(paths: list[Path], max_images: int | None) -> list[Path]:
    if max_images is None or len(paths) <= max_images:
        return paths
    if max_images < 2:
        raise ValueError("max_images must be at least 2")
    indices = np.linspace(0, len(paths) - 1, max_images).round().astype(int)
    return [paths[index] for index in dict.fromkeys(indices.tolist())]


def preprocess_images(paths: list[Path]) -> tuple[np.ndarray, np.ndarray, list[dict[str, int]]]:
    """Letterbox images to a fixed square without losing scene borders."""

    images: list[np.ndarray] = []
    valid_masks: list[np.ndarray] = []
    transforms: list[dict[str, int]] = []

    for path in paths:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            original_width, original_height = image.size
            scale = min(IMAGE_SIZE / original_width, IMAGE_SIZE / original_height)
            resized_width = max(14, round(original_width * scale / 14) * 14)
            resized_height = max(14, round(original_height * scale / 14) * 14)
            resized_width = min(IMAGE_SIZE, resized_width)
            resized_height = min(IMAGE_SIZE, resized_height)
            left = (IMAGE_SIZE - resized_width) // 2
            top = (IMAGE_SIZE - resized_height) // 2
            image = image.resize((resized_width, resized_height), Image.Resampling.BICUBIC)

            canvas = np.ones((IMAGE_SIZE, IMAGE_SIZE, 3), dtype=np.uint8) * 255
            canvas[top : top + resized_height, left : left + resized_width] = np.asarray(image)
            valid_mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=bool)
            valid_mask[top : top + resized_height, left : left + resized_width] = True

            images.append(canvas)
            valid_masks.append(valid_mask)
            transforms.append(
                {
                    "original_width": original_width,
                    "original_height": original_height,
                    "resized_width": resized_width,
                    "resized_height": resized_height,
                    "left": left,
                    "top": top,
                    "canvas_size": IMAGE_SIZE,
                }
            )

    image_array = np.stack(images).astype(np.float32) / 255.0
    return image_array, np.stack(valid_masks), transforms


def _import_vggt(source_root: Path) -> tuple[Any, Any, Any]:
    if not (source_root / "vggt").is_dir():
        raise FileNotFoundError(
            f"VGGT source package not found under {source_root}. "
            "Run scripts/setup-vggt.ps1 or set PILE_METER_VGGT_SOURCE."
        )
    source = str(source_root)
    if source not in sys.path:
        sys.path.insert(0, source)

    from vggt.models.vggt import VGGT
    from vggt.utils.geometry import unproject_depth_map_to_point_map
    from vggt.utils.pose_enc import pose_encoding_to_extri_intri

    return VGGT, unproject_depth_map_to_point_map, pose_encoding_to_extri_intri


def _camera_centers(extrinsics: np.ndarray) -> np.ndarray:
    rotations = extrinsics[:, :3, :3]
    translations = extrinsics[:, :3, 3]
    return -np.einsum("sji,sj->si", rotations, translations)


def _json_float(value: float) -> float:
    return float(round(float(value), 8))


class VGGTReconstructor:
    """Run local VGGT-1B inference and export visualization artifacts."""

    def __init__(
        self,
        model_root: Path,
        weights_path: Path | None = None,
        source_root: Path | None = None,
        weights_name: str = "model.safetensors",
        device: str = "auto",
        max_images: int = 6,
        confidence_quantile: float = 25.0,
        max_view_points: int = 350_000,
    ) -> None:
        self.model_root = model_root
        self.weights_path = weights_path or model_root / weights_name
        self.source_root = source_root
        self.device = device
        self.max_images = max_images
        self.confidence_quantile = confidence_quantile
        self.max_view_points = max_view_points

    @property
    def is_ready(self) -> bool:
        return self.weights_path.is_file() and (
            self.source_root is None or (self.source_root / "vggt").is_dir()
        )

    def _resolve_device(self, torch: Any) -> tuple[Any, str]:
        if self.device not in {"auto", "cuda", "cpu"}:
            raise ValueError("device must be one of: auto, cuda, cpu")
        if self.device == "cpu":
            return torch.device("cpu"), "cpu"
        if not torch.cuda.is_available():
            if self.device == "cuda":
                raise RuntimeError("CUDA was requested but is not available")
            return torch.device("cpu"), "cpu"

        cuda_device = torch.device("cuda")
        try:
            probe = torch.ones((2, 2), device=cuda_device)
            _ = probe @ probe
            torch.cuda.synchronize()
        except RuntimeError as error:
            if self.device == "cuda":
                raise RuntimeError(f"CUDA runtime is incompatible: {error}") from error
            return torch.device("cpu"), "cpu"
        return cuda_device, torch.cuda.get_device_name(0)

    def reconstruct(self, request: ReconstructionRequest) -> ReconstructionArtifacts:
        if not self.weights_path.is_file():
            raise FileNotFoundError(
                f"VGGT weights not found at {self.weights_path}. "
                "Run scripts/setup-vggt.ps1 or set PILE_METER_VGGT_WEIGHTS."
            )
        if self.source_root is None:
            raise ValueError("VGGT source_root must be configured")

        import torch
        from safetensors.torch import load_file

        VGGT, unproject_depth, pose_to_camera = _import_vggt(self.source_root)
        started_at = time.perf_counter()
        request.output_directory.mkdir(parents=True, exist_ok=True)
        selected_paths = select_evenly(request.image_paths, self.max_images)

        image_array, valid_masks, transforms = preprocess_images(selected_paths)
        image_tensor = torch.from_numpy(image_array).permute(0, 3, 1, 2)
        device, device_name = self._resolve_device(torch)
        model_dtype = torch.float32

        model = VGGT(
            enable_camera=True,
            enable_depth=True,
            enable_point=True,
            enable_track=False,
        )
        state_dict = load_file(str(self.weights_path), device="cpu")
        incompatible = model.load_state_dict(state_dict, strict=False)
        del state_dict
        gc.collect()
        model = model.to(device=device, dtype=model_dtype).eval()
        image_tensor = image_tensor.to(device=device, dtype=model_dtype)

        autocast_context = (
            torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16)
            if device.type == "cuda"
            else nullcontext()
        )
        with torch.inference_mode(), autocast_context:
            predictions = model(image_tensor)
            if device.type == "cuda":
                torch.cuda.synchronize()

        extrinsics_tensor, intrinsics_tensor = pose_to_camera(
            predictions["pose_enc"],
            image_tensor.shape[-2:],
        )
        extrinsics = extrinsics_tensor.squeeze(0).float().cpu().numpy()
        intrinsics = intrinsics_tensor.squeeze(0).float().cpu().numpy()
        depth = predictions["depth"].squeeze(0).float().cpu().numpy().squeeze(-1)
        depth_confidence = predictions["depth_conf"].squeeze(0).float().cpu().numpy()
        point_map = predictions["world_points"].squeeze(0).float().cpu().numpy()
        point_confidence = predictions["world_points_conf"].squeeze(0).float().cpu().numpy()
        world_points_from_depth = unproject_depth(
            depth[..., None],
            extrinsics,
            intrinsics,
        ).astype(np.float32)
        if device.type == "cuda":
            torch.cuda.empty_cache()

        _, height, width = depth.shape
        colors = image_array.transpose(0, 2, 3, 1)
        colors_uint8 = np.clip(colors * 255.0, 0, 255).astype(np.uint8)

        all_points = world_points_from_depth.reshape(-1, 3)
        all_confidence = depth_confidence.reshape(-1)
        all_colors = colors_uint8.reshape(-1, 3)
        all_valid = (
            valid_masks.reshape(-1)
            & np.isfinite(all_points).all(axis=1)
            & np.isfinite(all_confidence)
            & (depth.reshape(-1) > 1e-6)
        )
        if not all_valid.any():
            raise RuntimeError("VGGT returned no valid depth points")

        confidence_threshold = float(
            np.quantile(
                all_confidence[all_valid],
                np.clip(self.confidence_quantile, 0.0, 99.0) / 100.0,
            )
        )
        keep = all_valid & (all_confidence >= confidence_threshold)
        kept_indices = np.flatnonzero(keep)
        kept_points = all_points[keep]
        kept_colors = all_colors[keep]
        if len(kept_points) == 0:
            raise RuntimeError("Confidence filtering removed every point")

        view_indices = np.arange(len(kept_points))
        if len(view_indices) > self.max_view_points:
            rng = np.random.default_rng(42)
            view_indices = np.sort(
                rng.choice(len(view_indices), self.max_view_points, replace=False)
            )

        view_points = kept_points[view_indices]
        view_colors = kept_colors[view_indices]
        raw_ply_path = request.output_directory / "points_raw.ply"
        view_ply_path = request.output_directory / "points_view.ply"
        write_binary_ply(raw_ply_path, kept_points, kept_colors)
        write_binary_ply(view_ply_path, view_points, view_colors)

        camera_centers = _camera_centers(extrinsics)
        cameras_path = request.output_directory / "cameras.json"
        cameras_payload = {
            "coordinate_system": "vggt-world",
            "extrinsics": extrinsics.tolist(),
            "intrinsics": intrinsics.tolist(),
            "camera_centers": camera_centers.tolist(),
            "image_names": [path.name for path in selected_paths],
            "image_size": [height, width],
        }
        cameras_path.write_text(
            json.dumps(cameras_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        predictions_path = request.output_directory / "predictions.npz"
        np.savez_compressed(
            predictions_path,
            depth=depth,
            depth_confidence=depth_confidence,
            extrinsics=extrinsics,
            intrinsics=intrinsics,
            world_points_from_depth=world_points_from_depth,
            world_points_from_pointmap=point_map,
            pointmap_confidence=point_confidence,
            input_images=colors_uint8,
            valid_masks=valid_masks,
            camera_centers=camera_centers,
            kept_flat_indices=kept_indices,
            confidence_threshold=np.asarray(confidence_threshold, dtype=np.float32),
            image_names=np.asarray([path.name for path in selected_paths]),
        )

        scene_min = view_points.min(axis=0)
        scene_max = view_points.max(axis=0)
        scene_size = scene_max - scene_min
        elapsed_seconds = time.perf_counter() - started_at
        manifest = build_run_manifest(
            job_id=request.job_id,
            run_id=request.run_id,
            image_count=len(selected_paths),
            model_name="VGGT-1B",
            configuration={
                "device": device_name,
                "dtype": str(model_dtype).replace("torch.", ""),
                "autocast_dtype": "bfloat16" if device.type == "cuda" else None,
                "confidence_quantile": self.confidence_quantile,
                "max_view_points": self.max_view_points,
                "preprocess": "letterbox-518",
            },
        )
        manifest.update(
            {
                "status": "completed",
                "duration_seconds": round(elapsed_seconds, 3),
                "model": {
                    "name": "VGGT-1B",
                    "weights": str(self.weights_path),
                    "weights_bytes": self.weights_path.stat().st_size,
                    "missing_state_keys": len(incompatible.missing_keys),
                    "unexpected_state_keys": len(incompatible.unexpected_keys),
                },
                "input": {
                    "image_count": len(selected_paths),
                    "images": [path.name for path in selected_paths],
                    "preprocess_mode": "letterbox-518",
                    "transforms": transforms,
                },
                "pointcloud": {
                    "confidence_threshold": confidence_threshold,
                    "raw_point_count": int(len(kept_points)),
                    "view_point_count": int(len(view_points)),
                    "bounds_min": [_json_float(value) for value in scene_min],
                    "bounds_max": [_json_float(value) for value in scene_max],
                    "bounds_size": [_json_float(value) for value in scene_size],
                },
                "artifacts": {
                    "predictions": predictions_path.name,
                    "points_raw": raw_ply_path.name,
                    "points_view": view_ply_path.name,
                    "cameras": cameras_path.name,
                },
            }
        )
        manifest_path = request.output_directory / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        del model
        gc.collect()
        if device.type == "cuda":
            torch.cuda.empty_cache()

        return ReconstructionArtifacts(
            model_name="VGGT-1B",
            predictions_path=predictions_path,
            raw_pointcloud_path=raw_ply_path,
            view_pointcloud_path=view_ply_path,
            cameras_path=cameras_path,
            image_count=len(selected_paths),
        )
