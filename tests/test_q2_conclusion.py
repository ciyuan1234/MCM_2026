import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOLUTION_PATH = PROJECT_ROOT / "outputs" / "result2_solution.json"


def _load_solution():
    with SOLUTION_PATH.open(encoding="utf-8") as file:
        solution = json.load(file)
    return (
        np.array(solution["time_s"], dtype=float),
        np.array(solution["radius_m"], dtype=float),
        np.array(solution["temperature_c"], dtype=float),
        np.array(solution["moisture_dry_basis"], dtype=float),
    )


def _index(time_s, target):
    return int(np.where(np.isclose(time_s, target))[0][0])


def _radius_index(radius_m, target_cm):
    return int(np.argmin(np.abs(radius_m - target_cm / 100.0)))


def test_q2_conclusion_values_match_solution() -> None:
    time_s, radius_m, temperature_c, moisture = _load_solution()
    index_05h = _index(time_s, 1800.0)
    index_3h = _index(time_s, 10800.0)
    center = _radius_index(radius_m, 0.0)
    surface = _radius_index(radius_m, 2.0)

    assert round(float(temperature_c[index_05h, center]), 4) == 32.1908
    assert round(float(temperature_c[index_05h, surface]), 4) == 35.4146
    assert round(float(moisture[index_05h, center]), 4) == 2.5499
    assert round(float(moisture[index_05h, surface]), 4) == 1.6485

    assert round(float(temperature_c[index_3h, center]), 4) == 49.8495
    assert round(float(temperature_c[index_3h, surface]), 4) == 49.9663
    assert round(float(moisture[index_3h, center]), 4) == 1.7662
    assert round(float(moisture[index_3h, surface]), 4) == 1.0078

    temperature_difference = (
        temperature_c[index_3h, surface] - temperature_c[index_3h, center]
    )
    moisture_difference = moisture[index_3h, center] - moisture[index_3h, surface]
    assert round(float(temperature_difference), 4) == 0.1168
    assert round(float(moisture_difference), 4) == 0.7585
