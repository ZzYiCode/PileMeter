from pathlib import Path

import numpy as np
import pytest

from pile_meter.pointcloud.io import write_ascii_ply, write_binary_ply


def test_write_ascii_ply(tmp_path: Path) -> None:
    output = write_ascii_ply(
        tmp_path / "points.ply",
        [(0, 0, 0), (1, 2, 3)],
        [(255, 0, 0), (0, 255, 0)],
    )

    content = output.read_text(encoding="ascii")
    assert "element vertex 2" in content
    assert "255 0 0" in content
    assert "0 255 0" in content


def test_write_ascii_ply_rejects_non_finite_points(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-finite"):
        write_ascii_ply(tmp_path / "bad.ply", [(0, 0, float("nan"))])


def test_write_binary_ply(tmp_path: Path) -> None:
    output = write_binary_ply(
        tmp_path / "binary.ply",
        np.asarray([[0, 1, 2], [3, 4, 5]], dtype=np.float32),
        np.asarray([[255, 0, 0], [0, 255, 0]], dtype=np.uint8),
    )

    payload = output.read_bytes()
    assert payload.startswith(b"ply\nformat binary_little_endian")
    assert b"element vertex 2" in payload
    assert len(payload) > 100
