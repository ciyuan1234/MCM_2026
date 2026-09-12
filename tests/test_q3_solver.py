"""问题 3 的求解器级检查（时间步 15 s；不含长时程收敛复算）。"""

import numpy as np

from src.config import (
    ATTACHMENT_1_PATH,
    CELSIUS_TO_KELVIN,
    CYLINDER_RADIUS_M,
    Q3_TIME_STEP_S,
)
from src.interpolators import PiecewiseLinear, read_attachment_1
from src.material import q2_properties
from src.radial_solver import make_radial_grid, solve_constant_radius


def _solve(hours: float, dr_m: float = 0.00025, dt_s: float = Q3_TIME_STEP_S):
    attachment = read_attachment_1(ATTACHMENT_1_PATH)
    air_temperature = PiecewiseLinear(attachment.time_s, attachment.air_temperature_c)
    air_moisture = PiecewiseLinear(attachment.time_s, attachment.air_moisture_dry_basis)
    n_steps = int(round(hours * 3600.0 / dt_s))
    time_s = np.arange(n_steps + 1, dtype=float) * dt_s
    grid = make_radial_grid(CYLINDER_RADIUS_M, dr_m)
    return solve_constant_radius(
        grid=grid,
        time_s=time_s,
        initial_temperature_c=28.0,
        initial_moisture_dry_basis=2.55,
        boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
        boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
        property_function=q2_properties,
        h_w_m2_k=25.0,
        hm_m_s=8e-7,
        picard_tolerance=1e-8,
        max_picard_iterations=40,
        track_linear_residual=True,
    )


def test_q3_zero_drive_keeps_initial_state() -> None:
    time_s = np.arange(0.0, 3600.0 + 1e-9, 60.0)
    grid = make_radial_grid(CYLINDER_RADIUS_M, 0.001)
    result = solve_constant_radius(
        grid=grid,
        time_s=time_s,
        initial_temperature_c=28.0,
        initial_moisture_dry_basis=2.55,
        boundary_temperature_k=lambda _: 28.0 + CELSIUS_TO_KELVIN,
        boundary_moisture_dry_basis=lambda _: 2.55,
        property_function=q2_properties,
        h_w_m2_k=25.0,
        hm_m_s=8e-7,
        picard_tolerance=1e-10,
        max_picard_iterations=40,
    )
    assert np.allclose(result.temperature_c, 28.0, atol=1e-9)
    assert np.allclose(result.moisture_dry_basis, 2.55, atol=1e-9)


def test_q3_center_is_last_position_to_dry() -> None:
    result = _solve(hours=6.0)
    moisture = result.moisture_dry_basis
    assert np.allclose(moisture.max(axis=1), moisture[:, 0], atol=1e-12)
    assert np.all(np.diff(moisture[:, 0]) <= 1e-12)
    assert moisture[-1, 0] < moisture[0, 0]
    assert moisture[-1, -1] < moisture[-1, 0]


def test_q3_surface_reaches_air_moisture_before_center_reaches_target() -> None:
    result = _solve(hours=24.0, dr_m=0.000125)
    moisture = result.moisture_dry_basis
    assert float(moisture[-1, -1]) < 0.08
    assert float(moisture[-1, 0]) > 0.15


def test_q3_grid_convergence_over_short_window() -> None:
    coarse = _solve(hours=2.0, dr_m=0.0000625)
    fine = _solve(hours=2.0, dr_m=0.00003125)
    output_radius_m = np.arange(0.0, CYLINDER_RADIUS_M + 1e-12, 0.001)
    coarse_values = np.array(
        [
            coarse.moisture_dry_basis[-1, int(np.argmin(np.abs(coarse.radius_m - target)))]
            for target in output_radius_m
        ]
    )
    fine_values = np.array(
        [
            fine.moisture_dry_basis[-1, int(np.argmin(np.abs(fine.radius_m - target)))]
            for target in output_radius_m
        ]
    )
    assert float(np.max(np.abs(coarse_values - fine_values))) <= 0.001


def test_q3_moisture_balance_is_closed() -> None:
    result = _solve(hours=6.0)
    diagnostics = result.diagnostics
    assert float(diagnostics["moisture_balance_relative_error"]) < 1e-10
    assert float(diagnostics["linear_system_residual_max"]) < 1e-9
