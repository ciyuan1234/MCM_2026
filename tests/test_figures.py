from pathlib import Path

from PIL import Image

from analysis.make_q1_figures import (
    DEFAULT_SOLUTION_PATHS,
    generate_figures,
)


def test_generate_q1_figures_in_all_formats(tmp_path: Path) -> None:
    paths = generate_figures(DEFAULT_SOLUTION_PATHS[1], tmp_path, 1)
    assert len(paths) == 15
    for extension in ("png", "pdf", "svg"):
        files = sorted(tmp_path.glob(f"*.{extension}"))
        assert len(files) == 5
        assert all(file.stat().st_size > 0 for file in files)

    for png_path in tmp_path.glob("*.png"):
        with Image.open(png_path) as image:
            assert image.width >= 1000
            assert image.height >= 600


def test_generate_q2_figures_in_all_formats(tmp_path: Path) -> None:
    paths = generate_figures(DEFAULT_SOLUTION_PATHS[2], tmp_path, 2)
    assert len(paths) == 15
    for extension in ("png", "pdf", "svg"):
        assert len(sorted(tmp_path.glob(f"*.{extension}"))) == 5


def test_generate_q3_figures_in_all_formats(tmp_path: Path) -> None:
    paths = generate_figures(DEFAULT_SOLUTION_PATHS[3], tmp_path, 3)
    assert len(paths) == 18
    for extension in ("png", "pdf", "svg"):
        assert len(sorted(tmp_path.glob(f"*.{extension}"))) == 6
