import json
from pathlib import Path

import numpy as np

from src.diagnostics import q2_property_ranges

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_q2_property_ranges_match_solution() -> None:
    with (PROJECT_ROOT / "outputs" / "result2_solution.json").open(
        encoding="utf-8"
    ) as file:
        solution = json.load(file)
    ranges = q2_property_ranges(
        np.array(solution["moisture_dry_basis"], dtype=float),
        np.array(solution["temperature_c"], dtype=float) + 273.15,
    )
    assert ranges["density_min_kg_m3"] < ranges["density_max_kg_m3"]
    assert ranges["heat_capacity_min_j_kg_k"] < ranges["heat_capacity_max_j_kg_k"]
    assert (
        ranges["thermal_conductivity_min_w_m_k"]
        < ranges["thermal_conductivity_max_w_m_k"]
    )
    assert (
        ranges["moisture_diffusivity_min_m2_s"]
        < ranges["moisture_diffusivity_max_m2_s"]
    )
