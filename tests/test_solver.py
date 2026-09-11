import numpy as np

from src.material import q1_properties
from src.radial_solver import make_radial_grid, solve_constant_radius


def _run_zero_drive(n_steps: int = 20):
    time = np.arange(n_steps + 1, dtype=float)
    grid = make_radial_grid(radius_m=0.02, dr_m=0.001)
    return solve_constant_radius(
        grid=grid,
        time_s=time,
        initial_temperature_c=28.0,
        initial_moisture_dry_basis=2.55,
        boundary_temperature_k=lambda _: 28.0 + 273.15,
        boundary_moisture_dry_basis=lambda _: 2.55,
        property_function=q1_properties,
        h_w_m2_k=25.0,
        hm_m_s=8e-7,
        picard_tolerance=1e-10,
        max_picard_iterations=30,
    )


def test_initial_condition_is_preserved() -> None:
    result = _run_zero_drive(1)
    assert np.allclose(result.temperature_c[0], 28.0)
    assert np.allclose(result.moisture_dry_basis[0], 2.55)


def test_zero_drive_does_not_change_state() -> None:
    result = _run_zero_drive(20)
    assert np.allclose(result.temperature_c, 28.0, atol=1e-9)
    assert np.allclose(result.moisture_dry_basis, 2.55, atol=1e-9)


def test_heating_and_drying_trends() -> None:
    time = np.arange(61, dtype=float)
    grid = make_radial_grid(radius_m=0.02, dr_m=0.001)
    result = solve_constant_radius(
        grid=grid,
        time_s=time,
        initial_temperature_c=28.0,
        initial_moisture_dry_basis=2.55,
        boundary_temperature_k=lambda _: 60.0 + 273.15,
        boundary_moisture_dry_basis=lambda _: 0.02,
        property_function=q1_properties,
        h_w_m2_k=25.0,
        hm_m_s=8e-7,
        picard_tolerance=1e-10,
        max_picard_iterations=30,
    )
    assert result.temperature_c[-1, -1] > result.temperature_c[-1, 0]
    assert result.moisture_dry_basis[-1, -1] < result.moisture_dry_basis[-1, 0]
    assert result.temperature_c[-1, -1] > result.temperature_c[0, -1]
    assert result.moisture_dry_basis[-1, -1] < result.moisture_dry_basis[0, -1]


def test_deterministic_regression_case() -> None:
    time = np.arange(61, dtype=float)
    grid = make_radial_grid(radius_m=0.02, dr_m=0.001)
    result = solve_constant_radius(
        grid=grid,
        time_s=time,
        initial_temperature_c=28.0,
        initial_moisture_dry_basis=2.55,
        boundary_temperature_k=lambda _: 60.0 + 273.15,
        boundary_moisture_dry_basis=lambda _: 0.02,
        property_function=q1_properties,
        h_w_m2_k=25.0,
        hm_m_s=8e-7,
        picard_tolerance=1e-10,
        max_picard_iterations=30,
    )
    assert np.isclose(result.temperature_c[-1, 0], 28.00060771191488, atol=1e-9)
    assert np.isclose(result.temperature_c[-1, -1], 35.057193738586705, atol=1e-9)
    assert np.isclose(result.moisture_dry_basis[-1, 0], 2.55, atol=1e-9)
    assert np.isclose(result.moisture_dry_basis[-1, -1], 2.3673016021297637, atol=1e-9)
