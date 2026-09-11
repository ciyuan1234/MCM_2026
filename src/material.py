"""Material property models from the problem appendices."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MaterialProperties:
    density_kg_m3: np.ndarray
    heat_capacity_j_kg_k: np.ndarray
    thermal_conductivity_w_m_k: np.ndarray
    moisture_diffusivity_m2_s: np.ndarray


def _validate_positive(values: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains a non-finite value")
    if np.any(arr <= 0.0):
        raise ValueError(f"{name} must be positive")
    return arr


def q1_properties(moisture: np.ndarray, temperature_k: np.ndarray) -> MaterialProperties:
    moisture = _validate_positive(moisture, "moisture")
    _validate_positive(temperature_k, "temperature_k")
    diffusivity = 7e-9 * np.exp(-0.89 / moisture)
    return MaterialProperties(
        density_kg_m3=np.full_like(moisture, 820.0),
        heat_capacity_j_kg_k=np.full_like(moisture, 2600.0),
        thermal_conductivity_w_m_k=np.full_like(moisture, 0.36),
        moisture_diffusivity_m2_s=diffusivity,
    )


def q2_properties(moisture: np.ndarray, temperature_k: np.ndarray) -> MaterialProperties:
    moisture = _validate_positive(moisture, "moisture")
    temperature_k = _validate_positive(temperature_k, "temperature_k")
    ratio = moisture / (moisture + 1.0)
    diffusivity = 2.4e-3 * np.exp(-0.45 / moisture) * np.exp(-3850.0 / temperature_k)
    return MaterialProperties(
        density_kg_m3=650.0 + 128.0 * moisture,
        heat_capacity_j_kg_k=1450.0 + 2736.0 * ratio,
        thermal_conductivity_w_m_k=0.21 + 0.38 * ratio,
        moisture_diffusivity_m2_s=diffusivity,
    )


def q4_properties(moisture: np.ndarray, temperature_k: np.ndarray) -> MaterialProperties:
    moisture = _validate_positive(moisture, "moisture")
    temperature_k = _validate_positive(temperature_k, "temperature_k")
    ratio = moisture / (moisture + 1.0)
    diffusivity = 4.2e-4 * np.exp(-0.30 / moisture) * np.exp(-3850.0 / temperature_k)
    return MaterialProperties(
        density_kg_m3=760.0 + 90.0 * moisture,
        heat_capacity_j_kg_k=1850.0 + 2150.0 * ratio,
        thermal_conductivity_w_m_k=0.12 + 0.20 * ratio,
        moisture_diffusivity_m2_s=diffusivity,
    )
