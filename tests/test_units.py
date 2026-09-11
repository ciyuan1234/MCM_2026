import numpy as np

from src.config import CYLINDER_RADIUS_CM, CYLINDER_RADIUS_M
from src.units import (
    celsius_to_kelvin,
    cm_to_m,
    kelvin_to_celsius,
    m_to_cm,
)


def test_geometry_conversion() -> None:
    assert np.isclose(cm_to_m(2.0), 0.02)
    assert np.isclose(m_to_cm(0.02), 2.0)
    assert np.isclose(CYLINDER_RADIUS_CM, 2.0)
    assert np.isclose(CYLINDER_RADIUS_M, cm_to_m(2.0))


def test_temperature_conversion() -> None:
    assert np.isclose(celsius_to_kelvin(28.0), 301.15)
    assert np.isclose(kelvin_to_celsius(301.15), 28.0)
    assert np.isclose(
        kelvin_to_celsius(celsius_to_kelvin(50.165)),
        50.165,
    )
