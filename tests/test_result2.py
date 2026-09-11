import json
from pathlib import Path

import numpy as np

from src.export_xlsx import verify_two_sheet_workbook

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_result2_workbook_matches_solution() -> None:
    with (PROJECT_ROOT / "outputs" / "result2_solution.json").open(
        encoding="utf-8"
    ) as file:
        solution = json.load(file)
    output_radius_m = np.arange(0.0, 0.0200001, 0.001)
    radius_m = np.array(solution["radius_m"], dtype=float)
    output_indices = [
        int(np.argmin(np.abs(radius_m - target_radius_m)))
        for target_radius_m in output_radius_m
    ]
    verify_two_sheet_workbook(
        PROJECT_ROOT / "outputs" / "result2.xlsx",
        ("温度", "水分浓度"),
        np.array(solution["time_s"], dtype=float),
        output_radius_m,
        (
            np.array(solution["temperature_c"], dtype=float)[:, output_indices],
            np.array(solution["moisture_dry_basis"], dtype=float)[:, output_indices],
        ),
    )
