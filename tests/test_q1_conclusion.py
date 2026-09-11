import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOLUTION_PATH = PROJECT_ROOT / "outputs" / "result1_solution.json"


def _load_solution():
    with SOLUTION_PATH.open(encoding="utf-8") as file:
        solution = json.load(file)
    return (
        np.array(solution["time_s"], dtype=float),
        np.array(solution["temperature_c"], dtype=float),
        np.array(solution["moisture_dry_basis"], dtype=float),
    )


def _index(time_s, target):
    return int(np.where(np.isclose(time_s, target))[0][0])


def test_q1_conclusion_values_match_solution() -> None:
    time_s, temperature_c, moisture = _load_solution()
    index_100 = _index(time_s, 100.0)
    index_1800 = _index(time_s, 1800.0)

    assert round(float(temperature_c[index_100, 0]), 4) == 28.0001
    assert round(float(temperature_c[index_100, -1]), 4) == 28.1792
    assert round(float(moisture[index_100, 0]), 4) == 2.5500
    assert round(float(moisture[index_100, -1]), 4) == 2.2886

    assert round(float(temperature_c[index_1800, 0]), 4) == 33.5764
    assert round(float(temperature_c[index_1800, -1]), 4) == 36.7860
    assert round(float(moisture[index_1800, 0]), 4) == 2.5500
    assert round(float(moisture[index_1800, -1]), 4) == 1.5117

    temperature_difference = (
        temperature_c[index_1800, -1] - temperature_c[index_1800, 0]
    )
    moisture_difference = moisture[index_1800, 0] - moisture[index_1800, -1]
    assert round(float(temperature_difference), 4) == 3.2096
    assert round(float(moisture_difference), 4) == 1.0382
