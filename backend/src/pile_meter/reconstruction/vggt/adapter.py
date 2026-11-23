from __future__ import annotations

from pathlib import Path

from pile_meter.contracts.reconstruction import ReconstructionArtifacts, ReconstructionRequest


class VGGTReconstructor:
    """VGGT adapter boundary.

    The implementation will be connected in milestone M1. Keeping the boundary
    in place now prevents model-specific dictionaries from leaking into the API
    and volume modules.
    """

    def __init__(self, model_root: Path, weights_name: str = "model.safetensors") -> None:
        self.model_root = model_root
        self.weights_path = model_root / weights_name

    @property
    def is_ready(self) -> bool:
        return self.weights_path.is_file()

    def reconstruct(self, request: ReconstructionRequest) -> ReconstructionArtifacts:
        if not self.is_ready:
            raise RuntimeError(
                f"VGGT weights not found at {self.weights_path}. "
                "Set PILE_METER_MODEL_ROOT or place the weights in models/."
            )
        raise NotImplementedError("VGGT inference will be connected in milestone M1.")
