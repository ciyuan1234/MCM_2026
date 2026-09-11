import numpy as np

from src.config import (
    CYLINDER_LENGTH_M,
    CYLINDER_RADIUS_M,
    Q1_CONVECTION_H_W_M2_K,
    Q1_THERMAL_CONDUCTIVITY_W_M_K,
)
from src.diagnostics import q1_model_metrics


def test_q1_model_metrics() -> None:
    metrics = q1_model_metrics()
    assert np.isclose(
        metrics["biot_number"],
        Q1_CONVECTION_H_W_M2_K * CYLINDER_RADIUS_M
        / Q1_THERMAL_CONDUCTIVITY_W_M_K,
    )
    assert np.isclose(metrics["length_radius_ratio"], CYLINDER_LENGTH_M / CYLINDER_RADIUS_M)
    assert metrics["thermal_penetration_1800s_cm"] > 1.0
    assert metrics["moisture_penetration_1800s_cm"] > 0.0
    assert 0.0 < metrics["fourier_number_1800s"] < 1.0
