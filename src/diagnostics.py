"""Reproducible dimensionless metrics used to justify model selection."""

from __future__ import annotations

import math

from .config import (
    CYLINDER_LENGTH_M,
    CYLINDER_RADIUS_M,
    INITIAL_MOISTURE_DRY_BASIS,
    Q1_CONVECTION_H_W_M2_K,
    Q1_CONVECTION_HM_M_S,
    Q1_DENSITY_KG_M3,
    Q1_DIFFUSIVITY_EXPONENT,
    Q1_DIFFUSIVITY_PREFACTOR_M2_S,
    Q1_END_TIME_S,
    Q1_HEAT_CAPACITY_J_KG_K,
    Q1_THERMAL_CONDUCTIVITY_W_M_K,
)


def q1_model_metrics() -> dict[str, float]:
    thermal_diffusivity = Q1_THERMAL_CONDUCTIVITY_W_M_K / (
        Q1_DENSITY_KG_M3 * Q1_HEAT_CAPACITY_J_KG_K
    )
    initial_moisture_diffusivity = Q1_DIFFUSIVITY_PREFACTOR_M2_S * math.exp(
        -Q1_DIFFUSIVITY_EXPONENT / INITIAL_MOISTURE_DRY_BASIS
    )
    thermal_penetration_m = math.sqrt(thermal_diffusivity * Q1_END_TIME_S)
    moisture_penetration_m = math.sqrt(
        initial_moisture_diffusivity * Q1_END_TIME_S
    )
    return {
        "thermal_diffusivity_m2_s": thermal_diffusivity,
        "thermal_penetration_1800s_m": thermal_penetration_m,
        "thermal_penetration_1800s_cm": thermal_penetration_m * 100.0,
        "initial_moisture_diffusivity_m2_s": initial_moisture_diffusivity,
        "moisture_penetration_1800s_m": moisture_penetration_m,
        "moisture_penetration_1800s_cm": moisture_penetration_m * 100.0,
        "biot_number": (
            Q1_CONVECTION_H_W_M2_K
            * CYLINDER_RADIUS_M
            / Q1_THERMAL_CONDUCTIVITY_W_M_K
        ),
        "fourier_number_1800s": (
            thermal_diffusivity * Q1_END_TIME_S / CYLINDER_RADIUS_M**2
        ),
        "mass_transfer_biot_number": (
            Q1_CONVECTION_HM_M_S
            * CYLINDER_RADIUS_M
            / initial_moisture_diffusivity
        ),
        "length_radius_ratio": CYLINDER_LENGTH_M / CYLINDER_RADIUS_M,
        "length_diameter_ratio": CYLINDER_LENGTH_M / (2.0 * CYLINDER_RADIUS_M),
    }
