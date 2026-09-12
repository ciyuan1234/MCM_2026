"""锁定问题 4 结论中的关键数值，并锁定与问题 3 的对比关系。"""

import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
Q4_PATH = PROJECT_ROOT / "outputs" / "result4_solution.json"
Q3_PATH = PROJECT_ROOT / "outputs" / "result3_solution.json"


def _load(path: Path):
    with path.open(encoding="utf-8") as file:
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


def test_q4_drying_time_matches_documented_conclusion() -> None:
    metadata, _, _, _, _ = _load(Q4_PATH)
    assert round(float(metadata["t_f_grid_s"]), 4) == 183060.0
    assert round(float(metadata["t_f_hours"]), 4) == 50.85
    assert round(float(metadata["t_f_interp_s"]), 4) == 183030.385
    assert round(float(metadata["t_f_interp_s"]) / 3600.0, 4) == 50.8418


def test_q4_key_moisture_values_match_documented_conclusion() -> None:
    _, time_s, _, _, moisture = _load(Q4_PATH)
    center = 0
    surface = -1
    index_6h = _time_index(time_s, 21600.0)
    assert round(float(moisture[index_6h, center]), 4) == 1.7172
    assert round(float(moisture[index_6h, surface]), 4) == 0.4218

    index_12h = _time_index(time_s, 43200.0)
    assert round(float(moisture[index_12h, center]), 4) == 0.7346
    assert round(float(moisture[index_12h, surface]), 4) == 0.1667

    index_24h = _time_index(time_s, 86400.0)
    assert round(float(moisture[index_24h, center]), 4) == 0.2838
    assert round(float(moisture[index_24h, surface]), 4) == 0.0671

    index_48h = _time_index(time_s, 172800.0)
    assert round(float(moisture[index_48h, center]), 4) == 0.1557

    assert round(float(moisture[-1, center]), 4) == 0.1500
    assert round(float(moisture[-1, surface]), 4) == 0.0525


def test_q4_shrinkage_makes_drying_faster_than_fixed_radius() -> None:
    q4_metadata, _, _, _, _ = _load(Q4_PATH)
    q3_metadata, _, _, _, _ = _load(Q3_PATH)
    q4_hours = float(q4_metadata["t_f_hours"])
    q3_hours = float(q3_metadata["t_f_hours"])
    assert round(q3_hours, 4) == 57.2667
    assert q4_hours < q3_hours
    saving = q3_hours - q4_hours
    assert round(saving, 4) == 6.4167
    assert round(saving / q3_hours * 100.0, 2) == 11.20


def test_q4_temperature_reaches_air_temperature_early() -> None:
    _, time_s, _, temperature, _ = _load(Q4_PATH)
    index_6h = _time_index(time_s, 21600.0)
    assert round(float(temperature[index_6h, 0]), 4) == 50.1646
    assert round(float(temperature[index_6h, -1]), 4) == 50.1648
    assert abs(float(temperature[-1, 0]) - 50.1650) < 5e-4
