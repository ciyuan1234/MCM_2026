"""问题 4 求解器级检查：常数半径回归、收缩行为与守恒。"""

import numpy as np
import pytest

from src.config import (
    ATTACHMENT_1_PATH,
    ATTACHMENT_2_PATH,
    CELSIUS_TO_KELVIN,
    CYLINDER_RADIUS_M,
    Q4_TIME_STEP_S,
)
from src.interpolators import (
    PiecewiseLinear,
    read_attachment_1,
    read_attachment_2,
)
from src.material import q1_properties, q4_properties
from src.radial_solver import make_radial_grid, solve_constant_radius, solve_radial


def _boundaries():
    attachment1 = read_attachment_1(ATTACHMENT_1_PATH)
    return (
        PiecewiseLinear(attachment1.time_s, attachment1.air_temperature_c),
        PiecewiseLinear(attachment1.time_s, attachment1.air_moisture_dry_basis),
    )


def _radius_ratio_function():
    attachment2 = read_attachment_2(ATTACHMENT_2_PATH)
    radius = PiecewiseLinear(attachment2.time_s, attachment2.radius_cm)
    radius0_cm = CYLINDER_RADIUS_M * 100.0
    return lambda t: float(radius(t)) / radius0_cm


def test_constant_radius_path_is_unchanged_by_generalization() -> None:
    """`solve_radial` 在 volume/surface scale 恒为 1 时必须与 `solve_constant_radius` 完全一致。"""
    air_temperature, air_moisture = _boundaries()
    time_s = np.arange(0.0, 600.0 + 1e-9, 30.0)
    grid = make_radial_grid(CYLINDER_RADIUS_M, 0.00025)
    common = dict(
        grid=grid,
        time_s=time_s,
        initial_temperature_c=28.0,
        initial_moisture_dry_basis=2.55,
        boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
        boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
        property_function=q1_properties,
        h_w_m2_k=25.0,
        hm_m_s=8e-7,
        picard_tolerance=1e-10,
        max_picard_iterations=40,
    )
    reference = solve_constant_radius(**common)
    generalized = solve_radial(**common, radius_scale=None)
    assert np.array_equal(reference.temperature_c, generalized.temperature_c)
    assert np.array_equal(reference.moisture_dry_basis, generalized.moisture_dry_basis)
    assert reference.diagnostics == generalized.diagnostics


def test_shrinking_domain_dries_faster_than_frozen_geometry() -> None:
    """同一物性与边界下，收缩使路径变短，圆心应比固定半径更快失水。"""
    air_temperature, air_moisture = _boundaries()
    time_s = np.arange(0.0, 24.0 * 3600.0 + 1e-9, 60.0)
    grid = make_radial_grid(CYLINDER_RADIUS_M, 0.00025)
    common = dict(
        grid=grid,
        time_s=time_s,
        initial_temperature_c=28.0,
        initial_moisture_dry_basis=2.55,
        boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
        boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
        property_function=q4_properties,
        h_w_m2_k=25.0,
        hm_m_s=8e-7,
        picard_tolerance=1e-8,
        max_picard_iterations=40,
    )
    frozen = solve_constant_radius(**common)
    shrinking = solve_radial(**common, radius_scale=_radius_ratio_function())
    assert float(shrinking.moisture_dry_basis[-1, 0]) < float(
        frozen.moisture_dry_basis[-1, 0]
    )


def test_shrinking_run_keeps_center_as_driest_position_and_conserves_moisture() -> None:
    air_temperature, air_moisture = _boundaries()
    time_s = np.arange(0.0, 12.0 * 3600.0 + 1e-9, Q4_TIME_STEP_S)
    grid = make_radial_grid(CYLINDER_RADIUS_M, 0.00025)
    result = solve_radial(
        grid=grid,
        time_s=time_s,
        initial_temperature_c=28.0,
        initial_moisture_dry_basis=2.55,
        boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
        boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
        property_function=q4_properties,
        h_w_m2_k=25.0,
        hm_m_s=8e-7,
        picard_tolerance=1e-8,
        max_picard_iterations=40,
        track_linear_residual=True,
        radius_scale=_radius_ratio_function(),
    )
    moisture = result.moisture_dry_basis
    assert np.allclose(moisture.max(axis=1), moisture[:, 0], atol=1e-12)
    assert np.all(np.diff(moisture[:, 0]) <= 1e-12)
    assert float(result.diagnostics["moisture_balance_relative_error"]) < 1e-10
    assert float(result.diagnostics["linear_system_residual_max"]) < 1e-9


def test_non_positive_radius_ratio_is_rejected() -> None:
    air_temperature, air_moisture = _boundaries()
    time_s = np.arange(0.0, 120.0 + 1e-9, 60.0)
    grid = make_radial_grid(CYLINDER_RADIUS_M, 0.001)
    with pytest.raises(ValueError):
        solve_radial(
            grid=grid,
            time_s=time_s,
            initial_temperature_c=28.0,
            initial_moisture_dry_basis=2.55,
            boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
            boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
            property_function=q4_properties,
            h_w_m2_k=25.0,
            hm_m_s=8e-7,
            picard_tolerance=1e-8,
            max_picard_iterations=40,
            radius_scale=lambda t: 0.0,
        )


def test_attachment_2_radius_is_monotone_non_increasing() -> None:
    attachment2 = read_attachment_2(ATTACHMENT_2_PATH)
    assert np.all(np.diff(attachment2.radius_cm) <= 0.0)
    assert float(attachment2.radius_cm[0]) == 2.0
    assert float(attachment2.radius_cm[-1]) == 1.198
