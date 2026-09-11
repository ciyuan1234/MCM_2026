"""Implicit finite-volume solver for the one-dimensional radial model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve

from .material import MaterialProperties


class PicardConvergenceError(RuntimeError):
    """Raised when the nonlinear iteration does not converge."""


@dataclass(frozen=True)
class RadialGrid:
    radius_m: np.ndarray
    node_volume_per_length_m2: np.ndarray
    face_area_per_length_m: np.ndarray
    surface_area_per_length_m: float
    dr_m: float

    @property
    def n_nodes(self) -> int:
        return int(self.radius_m.size)


@dataclass(frozen=True)
class SolverResult:
    time_s: np.ndarray
    radius_m: np.ndarray
    temperature_c: np.ndarray
    moisture_dry_basis: np.ndarray
    picard_iterations: np.ndarray
    diagnostics: dict[str, float]


def make_radial_grid(radius_m: float, dr_m: float) -> RadialGrid:
    if radius_m <= 0.0 or dr_m <= 0.0:
        raise ValueError("radius and radial step must be positive")
    n_intervals = int(round(radius_m / dr_m))
    if not np.isclose(n_intervals * dr_m, radius_m, rtol=0.0, atol=1e-12):
        raise ValueError("radius must be an integer multiple of the radial step")

    radius = np.arange(n_intervals + 1, dtype=float) * dr_m
    node_volume = np.empty(n_intervals + 1, dtype=float)
    for j, r_j in enumerate(radius):
        if j == 0:
            node_volume[j] = np.pi * (dr_m / 2.0) ** 2
        elif j == n_intervals:
            node_volume[j] = np.pi * (radius_m**2 - (radius_m - dr_m / 2.0) ** 2)
        else:
            node_volume[j] = 2.0 * np.pi * r_j * dr_m

    face_radius = radius[:-1] + dr_m / 2.0
    face_area = 2.0 * np.pi * face_radius
    surface_area = 2.0 * np.pi * radius_m
    return RadialGrid(radius, node_volume, face_area, surface_area, dr_m)


def _harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if np.any(left <= 0.0) or np.any(right <= 0.0):
        raise ValueError("diffusion coefficients must be positive")
    return 2.0 * left * right / (left + right)


def _build_heat_system(
    grid: RadialGrid,
    properties: MaterialProperties,
    temperature_old_k: np.ndarray,
    air_temperature_k: float,
    dt_s: float,
    h_w_m2_k: float,
) -> tuple[csr_matrix, np.ndarray]:
    n = grid.n_nodes
    matrix = np.zeros((n, n), dtype=float)
    rhs = np.zeros(n, dtype=float)

    storage = (
        properties.density_kg_m3
        * properties.heat_capacity_j_kg_k
        * grid.node_volume_per_length_m2
        / dt_s
    )
    matrix[np.arange(n), np.arange(n)] += storage
    rhs += storage * temperature_old_k

    for j in range(n - 1):
        face_k = _harmonic_mean(
            np.array([properties.thermal_conductivity_w_m_k[j]]),
            np.array([properties.thermal_conductivity_w_m_k[j + 1]]),
        )[0]
        conductance = grid.face_area_per_length_m[j] * face_k / grid.dr_m
        matrix[j, j] += conductance
        matrix[j, j + 1] -= conductance
        matrix[j + 1, j + 1] += conductance
        matrix[j + 1, j] -= conductance

    boundary_conductance = grid.surface_area_per_length_m * h_w_m2_k
    matrix[-1, -1] += boundary_conductance
    rhs[-1] += boundary_conductance * air_temperature_k
    return csr_matrix(matrix), rhs


def _build_moisture_system(
    grid: RadialGrid,
    moisture_diffusivity_m2_s: np.ndarray,
    moisture_old: np.ndarray,
    air_moisture: float,
    dt_s: float,
    hm_m_s: float,
) -> tuple[csr_matrix, np.ndarray]:
    n = grid.n_nodes
    matrix = np.zeros((n, n), dtype=float)
    rhs = np.zeros(n, dtype=float)

    storage = grid.node_volume_per_length_m2 / dt_s
    matrix[np.arange(n), np.arange(n)] += storage
    rhs += storage * moisture_old

    for j in range(n - 1):
        face_d = _harmonic_mean(
            np.array([moisture_diffusivity_m2_s[j]]),
            np.array([moisture_diffusivity_m2_s[j + 1]]),
        )[0]
        conductance = grid.face_area_per_length_m[j] * face_d / grid.dr_m
        matrix[j, j] += conductance
        matrix[j, j + 1] -= conductance
        matrix[j + 1, j + 1] += conductance
        matrix[j + 1, j] -= conductance

    boundary_conductance = grid.surface_area_per_length_m * hm_m_s
    matrix[-1, -1] += boundary_conductance
    rhs[-1] += boundary_conductance * air_moisture
    return csr_matrix(matrix), rhs


def solve_constant_radius(
    *,
    grid: RadialGrid,
    time_s: np.ndarray,
    initial_temperature_c: float,
    initial_moisture_dry_basis: float,
    boundary_temperature_k: Callable[[float], float],
    boundary_moisture_dry_basis: Callable[[float], float],
    property_function: Callable[[np.ndarray, np.ndarray], MaterialProperties],
    h_w_m2_k: float,
    hm_m_s: float,
    picard_tolerance: float,
    max_picard_iterations: int,
) -> SolverResult:
    time = np.asarray(time_s, dtype=float)
    if time.ndim != 1 or time.size < 2:
        raise ValueError("time grid must be one-dimensional with at least two points")
    if not np.isclose(time[0], 0.0, rtol=0.0, atol=1e-12):
        raise ValueError("time grid must start at zero")
    dt_s = time[1] - time[0]
    if dt_s <= 0.0:
        raise ValueError("time step must be positive")
    if not np.allclose(np.diff(time), dt_s, rtol=0.0, atol=1e-12):
        raise ValueError("time grid must be uniform")

    n_times = time.size
    n_nodes = grid.n_nodes
    temperature_k = np.full(n_nodes, initial_temperature_c + 273.15, dtype=float)
    moisture = np.full(n_nodes, initial_moisture_dry_basis, dtype=float)
    temperature_history = np.empty((n_times, n_nodes), dtype=float)
    moisture_history = np.empty((n_times, n_nodes), dtype=float)
    picard_history = np.zeros(n_times, dtype=int)
    temperature_history[0] = temperature_k
    moisture_history[0] = moisture

    boundary_heat_integral = 0.0
    boundary_moisture_integral = 0.0

    for step in range(1, n_times):
        current_time = float(time[step])
        air_temperature_k = float(boundary_temperature_k(current_time))
        air_moisture = float(boundary_moisture_dry_basis(current_time))
        temperature_old = temperature_k.copy()
        moisture_old = moisture.copy()
        temperature_guess = temperature_old.copy()
        moisture_guess = moisture_old.copy()

        converged = False
        iterations = 0
        for iterations in range(1, max_picard_iterations + 1):
            properties = property_function(moisture_guess, temperature_guess)
            heat_matrix, heat_rhs = _build_heat_system(
                grid,
                properties,
                temperature_old,
                air_temperature_k,
                dt_s,
                h_w_m2_k,
            )
            temperature_solution = spsolve(heat_matrix, heat_rhs)

            moisture_properties = property_function(moisture_guess, temperature_solution)
            moisture_matrix, moisture_rhs = _build_moisture_system(
                grid,
                moisture_properties.moisture_diffusivity_m2_s,
                moisture_old,
                air_moisture,
                dt_s,
                hm_m_s,
            )
            moisture_solution = spsolve(moisture_matrix, moisture_rhs)

            error = max(
                float(np.max(np.abs(temperature_solution - temperature_guess))),
                float(np.max(np.abs(moisture_solution - moisture_guess))),
            )
            temperature_guess = temperature_solution
            moisture_guess = moisture_solution
            if error < picard_tolerance:
                converged = True
                break

        if not converged:
            raise PicardConvergenceError(
                f"Picard iteration did not converge at t={current_time:.6f} s"
            )
        if not np.all(np.isfinite(temperature_guess)) or not np.all(np.isfinite(moisture_guess)):
            raise ValueError(f"non-finite solution at t={current_time:.6f} s")
        if np.any(temperature_guess <= 0.0):
            raise ValueError(f"non-positive absolute temperature at t={current_time:.6f} s")
        if np.any(moisture_guess < 0.0):
            raise ValueError(f"negative moisture at t={current_time:.6f} s")

        temperature_k = temperature_guess
        moisture = moisture_guess
        temperature_history[step] = temperature_k
        moisture_history[step] = moisture
        picard_history[step] = iterations

        boundary_heat_integral += (
            grid.surface_area_per_length_m
            * h_w_m2_k
            * (air_temperature_k - temperature_k[-1])
            * dt_s
        )
        boundary_moisture_integral += (
            grid.surface_area_per_length_m
            * hm_m_s
            * (air_moisture - moisture[-1])
            * dt_s
        )

    final_properties = property_function(moisture_history[-1], temperature_history[-1])
    internal_energy_change = float(
        np.sum(
            final_properties.density_kg_m3
            * final_properties.heat_capacity_j_kg_k
            * grid.node_volume_per_length_m2
            * (temperature_history[-1] - temperature_history[0])
        )
    )
    internal_moisture_change = float(
        np.sum(grid.node_volume_per_length_m2 * (moisture_history[-1] - moisture_history[0]))
    )
    diagnostics = {
        "boundary_heat_integral_j_per_m": float(boundary_heat_integral),
        "internal_energy_change_j_per_m": internal_energy_change,
        "heat_balance_relative_error": abs(
            internal_energy_change - boundary_heat_integral
        )
        / max(abs(internal_energy_change), abs(boundary_heat_integral), 1e-30),
        "boundary_moisture_integral": float(boundary_moisture_integral),
        "internal_moisture_change": internal_moisture_change,
        "moisture_balance_relative_error": abs(
            internal_moisture_change - boundary_moisture_integral
        )
        / max(abs(internal_moisture_change), abs(boundary_moisture_integral), 1e-30),
        "max_picard_iterations": float(np.max(picard_history)),
    }
    return SolverResult(
        time_s=time,
        radius_m=grid.radius_m.copy(),
        temperature_c=temperature_history - 273.15,
        moisture_dry_basis=moisture_history,
        picard_iterations=picard_history,
        diagnostics=diagnostics,
    )
