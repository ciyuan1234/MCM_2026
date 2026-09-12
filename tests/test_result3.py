import json
from pathlib import Path

import numpy as np

from src.config import Q3_OUTPUT_TIME_STEP_S, Q3_TARGET_MOISTURE
from src.export_xlsx import verify_single_sheet_workbook

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOLUTION_PATH = PROJECT_ROOT / "outputs" / "result3_solution.json"


def _load_solution():
    with SOLUTION_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def test_result3_workbook_matches_solution() -> None:
    solution = _load_solution()
    output_radius_m = np.arange(0.0, 0.0200001, 0.001)
    radius_m = np.array(solution["radius_m"], dtype=float)
    output_indices = [
        int(np.argmin(np.abs(radius_m - target_radius_m)))
        for target_radius_m in output_radius_m
    ]
    verify_single_sheet_workbook(
        PROJECT_ROOT / "outputs" / "result3.xlsx",
        "Sheet1",
        np.array(solution["time_s"], dtype=float),
        output_radius_m,
        np.array(solution["moisture_dry_basis"], dtype=float)[:, output_indices],
    )


def test_result3_time_grid_follows_delivery_interval() -> None:
    solution = _load_solution()
    time_s = np.array(solution["time_s"], dtype=float)
    assert time_s[0] == 0.0
    assert np.allclose(np.diff(time_s), Q3_OUTPUT_TIME_STEP_S, atol=1e-9)
    assert np.isclose(
        float(solution["metadata"]["t_f_grid_s"]), float(time_s[-1]), atol=1e-9
    )


def test_result3_ends_at_first_delivery_time_meeting_target() -> None:
    solution = _load_solution()
    moisture = np.array(solution["moisture_dry_basis"], dtype=float)
    center = moisture[:, 0]
    assert float(center[-1]) <= Q3_TARGET_MOISTURE
    assert float(center[-2]) > Q3_TARGET_MOISTURE


def test_result3_center_is_spatial_maximum_and_monotone_decreasing() -> None:
    solution = _load_solution()
    moisture = np.array(solution["moisture_dry_basis"], dtype=float)
    center = moisture[:, 0]
    assert np.allclose(moisture.max(axis=1), center, atol=1e-12)
    assert np.all(np.diff(center) <= 1e-12)


def test_result3_finite_and_non_negative() -> None:
    solution = _load_solution()
    moisture = np.array(solution["moisture_dry_basis"], dtype=float)
    temperature = np.array(solution["temperature_c"], dtype=float)
    assert np.all(np.isfinite(moisture)) and np.all(np.isfinite(temperature))
    assert np.all(moisture > 0.0)
    assert np.all(temperature > -273.15)
