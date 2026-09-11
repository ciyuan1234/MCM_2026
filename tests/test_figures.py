from pathlib import Path

from PIL import Image

from analysis.make_q1_figures import DEFAULT_SOLUTION_PATH, generate_figures


def test_generate_q1_figures_in_all_formats(tmp_path: Path) -> None:
    paths = generate_figures(DEFAULT_SOLUTION_PATH, tmp_path)
    assert len(paths) == 15
    for extension in ("png", "pdf", "svg"):
        files = sorted(tmp_path.glob(f"*.{extension}"))
        assert len(files) == 5
        assert all(file.stat().st_size > 0 for file in files)

    for png_path in tmp_path.glob("*.png"):
        with Image.open(png_path) as image:
            assert image.width >= 1000
            assert image.height >= 600
