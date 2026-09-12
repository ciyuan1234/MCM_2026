"""问题 4 收缩模型的网格/时间步收敛复算，结果写入 outputs/q4_convergence.json。"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    ATTACHMENT_1_PATH,
    ATTACHMENT_2_PATH,
    CELSIUS_TO_KELVIN,
    CYLINDER_RADIUS_M,
    INITIAL_MOISTURE_DRY_BASIS,
    INITIAL_TEMPERATURE_C,
    PICARD_MAX_ITERATIONS,
    PICARD_TOLERANCE,
    Q1_CONVECTION_H_W_M2_K,
    Q1_CONVECTION_HM_M_S,
    Q4_TARGET_MOISTURE,
)
from src.interpolators import (  # noqa: E402
    PiecewiseLinear,
    read_attachment_1,
    read_attachment_2,
)
from src.material import q4_properties  # noqa: E402
from src.radial_solver import make_radial_grid, solve_radial  # noqa: E402

# (标签, 空间步长 m, 时间步 s, 终止时间 h)
DEFAULT_CONFIGS = (
    ("dr=0.0625mm,dt=15s", 0.0000625, 15.0, 66.0),
    ("dr=0.03125mm,dt=15s", 0.00003125, 15.0, 60.0),
    ("dr=0.015625mm,dt=15s", 0.000015625, 15.0, 60.0),
    ("dr=0.03125mm,dt=30s", 0.00003125, 30.0, 60.0),
)
PRODUCTION_LABEL = "dr=0.03125mm,dt=15s"
SPATIAL_REFERENCE_LABEL = "dr=0.015625mm,dt=15s"
TIME_STEP_REFERENCE_LABEL = "dr=0.03125mm,dt=30s"
OUTPUT_RADIAL_STEP_CM = 0.1
COMPARE_HORIZON_H = 48.0


def _radius_ratio_function():
    attachment2 = read_attachment_2(ATTACHMENT_2_PATH)
    radius = PiecewiseLinear(attachment2.time_s, attachment2.radius_cm)
    radius0_cm = CYLINDER_RADIUS_M * 100.0
    return lambda t: float(radius(t)) / radius0_cm


def _crossing_time_hours(time_s: np.ndarray, center_moisture: np.ndarray) -> float:
    below = np.nonzero(center_moisture <= Q4_TARGET_MOISTURE)[0]
    if below.size == 0:
        raise SystemExit(
            f"center moisture did not reach {Q4_TARGET_MOISTURE} kg/kg; "
            "increase the horizon before comparing convergence"
        )
    index = int(below[0])
    time_prev, time_next = time_s[index - 1], time_s[index]
    moisture_prev, moisture_next = center_moisture[index - 1], center_moisture[index]
    crossing_s = time_prev + (moisture_prev - Q4_TARGET_MOISTURE) * (
        time_next - time_prev
    ) / (moisture_prev - moisture_next)
    return float(crossing_s) / 3600.0


def _output_indices(radius_m: np.ndarray) -> list[int]:
    targets = np.arange(0.0, CYLINDER_RADIUS_M + 1e-12, OUTPUT_RADIAL_STEP_CM / 100.0)
    indices = []
    for target in targets:
        index = int(np.argmin(np.abs(radius_m - target)))
        if not np.isclose(radius_m[index], target, atol=1e-12):
            raise ValueError(f"no grid node matches output radius {target}")
        indices.append(index)
    return indices


def run_convergence(configs=DEFAULT_CONFIGS) -> dict:
    attachment1 = read_attachment_1(ATTACHMENT_1_PATH)
    air_temperature = PiecewiseLinear(attachment1.time_s, attachment1.air_temperature_c)
    air_moisture = PiecewiseLinear(attachment1.time_s, attachment1.air_moisture_dry_basis)
    radius_ratio = _radius_ratio_function()
    compare_times_s = np.arange(
        6.0 * 3600.0, COMPARE_HORIZON_H * 3600.0 + 1.0, 6.0 * 3600.0
    )

    runs: list[dict] = []
    fields: list[np.ndarray] = []
    for label, dr_m, dt_s, run_hours in configs:
        end_s = run_hours * 3600.0
        n_steps = int(round(end_s / dt_s))
        time_s = np.arange(n_steps + 1, dtype=float) * dt_s
        grid = make_radial_grid(CYLINDER_RADIUS_M, dr_m)
        result = solve_radial(
            grid=grid,
            time_s=time_s,
            initial_temperature_c=INITIAL_TEMPERATURE_C,
            initial_moisture_dry_basis=INITIAL_MOISTURE_DRY_BASIS,
            boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
            boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
            property_function=q4_properties,
            h_w_m2_k=Q1_CONVECTION_H_W_M2_K,
            hm_m_s=Q1_CONVECTION_HM_M_S,
            picard_tolerance=PICARD_TOLERANCE,
            max_picard_iterations=PICARD_MAX_ITERATIONS,
            track_linear_residual=True,
            radius_scale=radius_ratio,
        )
        indices = _output_indices(result.radius_m)
        sampled = np.array(
            [
                result.moisture_dry_basis[
                    int(np.argmin(np.abs(result.time_s - t)))
                ][indices]
                for t in compare_times_s
            ]
        )
        fields.append(sampled)
        runs.append(
            {
                "label": label,
                "radial_step_m": dr_m,
                "time_step_s": dt_s,
                "t_f_hours": _crossing_time_hours(
                    result.time_s, result.moisture_dry_basis[:, 0]
                ),
                "center_moisture_at_24h": float(
                    result.moisture_dry_basis[
                        int(np.argmin(np.abs(result.time_s - 24.0 * 3600.0))), 0
                    ]
                ),
                "moisture_balance_relative_error": float(
                    result.diagnostics["moisture_balance_relative_error"]
                ),
                "linear_system_residual_max": float(
                    result.diagnostics["linear_system_residual_max"]
                ),
                "max_picard_iterations": float(
                    result.diagnostics["max_picard_iterations"]
                ),
            }
        )

    labels = [run["label"] for run in runs]
    production_index = labels.index(PRODUCTION_LABEL)
    reference_index = labels.index(SPATIAL_REFERENCE_LABEL)
    time_step_index = labels.index(TIME_STEP_REFERENCE_LABEL)
    production_field = fields[production_index]
    comparisons = {
        "production_label": PRODUCTION_LABEL,
        "spatial_reference_label": SPATIAL_REFERENCE_LABEL,
        "time_step_label": TIME_STEP_REFERENCE_LABEL,
        "spatial_t_f_difference_hours": abs(
            runs[production_index]["t_f_hours"] - runs[reference_index]["t_f_hours"]
        ),
        "time_step_t_f_difference_hours": abs(
            runs[production_index]["t_f_hours"] - runs[time_step_index]["t_f_hours"]
        ),
        "spatial_max_moisture_difference": float(
            np.max(np.abs(production_field - fields[reference_index]))
        ),
        "time_step_max_moisture_difference": float(
            np.max(np.abs(production_field - fields[time_step_index]))
        ),
        "compare_times_hours": (compare_times_s / 3600.0).tolist(),
    }
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "command": " ".join(sys.argv),
        "python": platform.python_version(),
        "compare_horizon_hours": COMPARE_HORIZON_H,
        "target_moisture_dry_basis": Q4_TARGET_MOISTURE,
        "runs": runs,
        "comparisons": comparisons,
    }


def _markdown_table(report: dict) -> str:
    lines = [
        "| 设置 | 空间步长 | 时间步 | 圆心达标时间 t_f (h) | 24 h 圆心含水率 | 水分守恒相对误差 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in report["runs"]:
        lines.append(
            f"| {run['label']} | {run['radial_step_m'] * 1000:.5f} mm | "
            f"{run['time_step_s']:.0f} s | {run['t_f_hours']:.4f} | "
            f"{run['center_moisture_at_24h']:.4f} | "
            f"{run['moisture_balance_relative_error']:.3e} |"
        )
    comparisons = report["comparisons"]
    lines.append("")
    lines.append(
        f"- 生产网格对更细网格的 t_f 差：{comparisons['spatial_t_f_difference_hours']:.4f} h"
    )
    lines.append(
        f"- 生产时间步对更小时间步的 t_f 差：{comparisons['time_step_t_f_difference_hours']:.4f} h"
    )
    lines.append(
        f"- 生产网格对更细网格的最大含水率差：{comparisons['spatial_max_moisture_difference']:.3e} kg/kg"
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    args = parser.parse_args()
    report = run_convergence()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "q4_convergence.json"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    table_path = args.output_dir / "q4_convergence_table.md"
    table_path.write_text(_markdown_table(report), encoding="utf-8")
    print(f"wrote {json_path}")
    print(_markdown_table(report))


if __name__ == "__main__":
    main()
