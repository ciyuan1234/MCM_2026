import numpy as np

from src.material import q1_properties


def test_q1_properties_return_expected_constants() -> None:
    moisture = np.array([2.55, 1.5])
    temperature = np.array([300.0, 310.0])
    properties = q1_properties(moisture, temperature)
    assert np.allclose(properties.density_kg_m3, [820.0, 820.0])
    assert np.allclose(properties.heat_capacity_j_kg_k, [2600.0, 2600.0])
    assert np.allclose(properties.thermal_conductivity_w_m_k, [0.36, 0.36])
    assert np.allclose(
        properties.moisture_diffusivity_m2_s,
        7e-9 * np.exp(-0.89 / moisture),
    )


def test_q1_properties_reject_non_positive_moisture() -> None:
    try:
        q1_properties(np.array([0.0]), np.array([300.0]))
    except ValueError as exc:
        assert "moisture" in str(exc)
    else:
        raise AssertionError("expected ValueError")
