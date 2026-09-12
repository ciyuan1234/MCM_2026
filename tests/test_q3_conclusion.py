"""锁定问题 3 结论中的关键数值，防止结论与结果文件脱节。"""

import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOLUTION_PATH = PROJECT_ROOT / "outputs" / "result3_solution.json"


def _load_solution():
    with SOLUTION_PATH.open(encoding="utf-8") as file:
        solution = json.load(file)
    return (
        solution["metadata"],
        np.array(solution["time_s"], dtype=float),
        np.array(solution["radius_m"], dtype=float),
        np.array(solution["temperature_c"], dtype=float),
        np.array(solution["moisture_dry_basis"], dtype=float),
    )


def _time_index(time_s: np.ndarray, target_s: float) -> int:
    return int(np.where(np.isclose(time_s, target_s))[0][0])


def test_q3_drying_time_matches_documented_conclusion() -> None:
    metadata, _, _, _, _ = _load_solution()
    assert round(float(metadata["t_f_grid_s"]), 4) == 206160.0
    assert round(float(metadata["t_f_hours"]), 4) == 57.2667
    assert round(float(metadata["t_f_interp_s"]), 4) == 206102.0103
    assert round(float(metadata["t_f_interp_s"]) / 3600.0, 4) == 57.2506


def test_q3_key_moisture_values_match_documented_conclusion() -> None:
    _, time_s, _, _, moisture = _load_solution()
    center = 0
    surface = -1

    index_05h = _time_index(time_s, 1800.0)
    assert round(float(moisture[index_05h, center]), 4) == 2.5499
    assert round(float(moisture[index_05h, surface]), 4) == 1.6500

    index_6h = _time_index(time_s, 21600.0)
    assert round(float(moisture[index_6h, center]), 4) == 1.0160
    assert round(float(moisture[index_6h, surface]), 4) == 0.5337

    index_24h = _time_index(time_s, 86400.0)
    assert round(float(moisture[index_24h, center]), 4) == 0.2372
    assert round(float(moisture[index_24h, surface]), 4) == 0.0662

    index_48h = _time_index(time_s, 172800.0)
    assert round(float(moisture[index_48h, center]), 4) == 0.1615

    assert round(float(moisture[-1, center]), 4) == 0.1500
    assert round(float(moisture[-1, surface]), 4) == 0.0525


def test_q3_temperature_reaches_air_temperature_quickly() -> None:
    _, time_s, _, temperature, _ = _load_solution()
    index_6h = _time_index(time_s, 21600.0)
    assert round(float(temperature[index_6h, 0]), 4) == 50.1645
    assert round(float(temperature[index_6h, -1]), 4) == 50.1647
    assert abs(float(temperature[-1, 0]) - 50.1650) < 5e-4


def test_q3_center_surface_moisture_spread_at_24h() -> None:
    _, time_s, _, _, moisture = _load_solution()
    index_24h = _time_index(time_s, 86400.0)
    spread = float(moisture[index_24h, 0] - moisture[index_24h, -1])
    assert round(spread, 4) == 0.1709
