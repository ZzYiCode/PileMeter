from pathlib import Path

import numpy as np
from PIL import Image

from pile_meter.reconstruction.vggt.adapter import (
    discover_images,
    preprocess_images,
    select_evenly,
)


def _write_image(path: Path, size: tuple[int, int]) -> None:
    Image.new("RGB", size, (120, 150, 170)).save(path)


def test_discover_and_select_images(tmp_path: Path) -> None:
    for index in range(5):
        _write_image(tmp_path / f"{index:03d}.jpg", (320, 240))
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")

    paths = discover_images(tmp_path)
    selected = select_evenly(paths, 3)

    assert len(paths) == 5
    assert selected == [paths[0], paths[2], paths[4]]


def test_preprocess_letterboxes_without_cropping(tmp_path: Path) -> None:
    paths = []
    for index in range(2):
        path = tmp_path / f"{index}.jpg"
        _write_image(path, (640, 360))
        paths.append(path)

    images, masks, transforms = preprocess_images(paths)

    assert images.shape == (2, 518, 518, 3)
    assert np.all(images[:, 0, :, :] == 1.0)
    assert masks.shape == (2, 518, 518)
    assert masks.any()
    assert transforms[0]["canvas_size"] == 518
