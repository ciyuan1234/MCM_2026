import numpy as np

from src.material import q1_properties, q2_properties


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


def test_q2_properties_match_appendix_3() -> None:
    moisture = np.array([2.55])
    temperature_k = np.array([301.15])
    properties = q2_properties(moisture, temperature_k)
    ratio = moisture / (moisture + 1.0)
    assert np.isclose(properties.density_kg_m3[0], 650.0 + 128.0 * 2.55)
    assert np.isclose(properties.heat_capacity_j_kg_k[0], 1450.0 + 2736.0 * ratio[0])
    assert np.isclose(properties.thermal_conductivity_w_m_k[0], 0.21 + 0.38 * ratio[0])
    assert np.isclose(
        properties.moisture_diffusivity_m2_s[0],
        2.4e-3
        * np.exp(-0.45 / 2.55)
        * np.exp(-3850.0 / 301.15),
    )
