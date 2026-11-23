from typing import Protocol

from pile_meter.contracts.reconstruction import ReconstructionArtifacts, ReconstructionRequest


class Reconstructor(Protocol):
    """Stable boundary for VGGT or an alternative reconstruction backend."""

    def reconstruct(self, request: ReconstructionRequest) -> ReconstructionArtifacts: ...
