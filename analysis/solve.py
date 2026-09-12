"""Reproducible entry point for the drying-problem models."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import numpy as np
import openpyxl
import scipy

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    ATTACHMENT_1_PATH,
    ATTACHMENT_2_PATH,
    CELSIUS_TO_KELVIN,
    CYLINDER_RADIUS_M,
    DEFAULT_RADIAL_STEP_M,
    INITIAL_MOISTURE_DRY_BASIS,
    INITIAL_TEMPERATURE_C,
    PICARD_MAX_ITERATIONS,
    PICARD_TOLERANCE,
    Q1_CONVECTION_H_W_M2_K,
    Q1_CONVECTION_HM_M_S,
    Q1_END_TIME_S,
    Q1_TIME_STEP_S,
    Q2_END_TIME_S,
    Q2_TIME_STEP_S,
    Q3_HORIZON_CAP_S,
    Q3_OUTPUT_TIME_STEP_S,
    Q3_RADIAL_STEP_M,
    Q3_TARGET_MOISTURE,
    Q3_TIME_STEP_S,
    Q4_HORIZON_CAP_S,
    Q4_OUTPUT_TIME_STEP_S,
    Q4_OUTPUT_RADIAL_STEP_CM,
    Q4_RADIAL_STEP_M,
    Q4_SURFACE_HEADER,
    Q4_TARGET_MOISTURE,
    Q4_TIME_STEP_S,
)
from src.export_xlsx import (  # noqa: E402
    verify_single_sheet_workbook,
    verify_two_sheet_workbook,
    write_solution_json,
)
from src.interpolators import (  # noqa: E402
    PiecewiseLinear,
    read_attachment_1,
    read_attachment_2,
)
from src.material import q1_properties, q2_properties, q4_properties  # noqa: E402
from src.radial_solver import (  # noqa: E402
    make_radial_grid,
    solve_constant_radius,
    solve_radial,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _code_hashes() -> dict[str, str]:
    paths = [
        PROJECT_ROOT / "analysis" / "solve.py",
        PROJECT_ROOT / "analysis" / "build_two_sheet_workbook.mjs",
        PROJECT_ROOT / "src" / "config.py",
        PROJECT_ROOT / "src" / "interpolators.py",
        PROJECT_ROOT / "src" / "material.py",
        PROJECT_ROOT / "src" / "radial_solver.py",
        PROJECT_ROOT / "src" / "export_xlsx.py",
    ]
    return {str(path.relative_to(PROJECT_ROOT)): _sha256(path) for path in paths}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _run_node_builder(
    json_path: Path,
    xlsx_path: Path,
    template_path: Path,
    sheet_names: tuple[str, str],
    last_header: str | None = None,
) -> None:
    marker = (
        PROJECT_ROOT
        / ".codex"
        / "skills"
        / "spreadsheets"
        / "container_tools"
        / "mark_artifact_operation_started.mjs"
    )
    builder = PROJECT_ROOT / "analysis" / "build_two_sheet_workbook.mjs"
    if not marker.exists():
        marker = (
            Path("/Users/a1-6/.codex/plugins/cache/openai-primary-runtime")
            / "spreadsheets"
            / "26.909.12148"
            / "skills"
            / "spreadsheets"
            / "container_tools"
            / "mark_artifact_operation_started.mjs"
        )
    subprocess.run(
        [
            "node",
            str(marker),
            "--operation-kind",
            "edit",
            "--expected-output-count",
            "1",
            "--output-format",
            "xlsx",
        ],
        check=True,
        cwd=PROJECT_ROOT,
    )
    builder_args = [
        "node",
        str(builder),
        str(json_path),
        str(xlsx_path),
        str(template_path),
        ",".join(sheet_names),
    ]
    if last_header:
        builder_args.append(last_header)
    subprocess.run(builder_args, check=True, cwd=PROJECT_ROOT)


def _solve_constant_radius_problem(
    *,
    problem: int,
    model_name: str,
    property_function,
    default_end_s: float,
    default_dt_s: float,
    template_relative_path: str,
    output_stem: str,
    track_linear_residual: bool,
    args: argparse.Namespace,
) -> None:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    attachment = read_attachment_1(ATTACHMENT_1_PATH)
    air_temperature = PiecewiseLinear(attachment.time_s, attachment.air_temperature_c)
    air_moisture = PiecewiseLinear(attachment.time_s, attachment.air_moisture_dry_basis)

    end_s = default_end_s if args.end_s is None else args.end_s
    dt_s = default_dt_s if args.dt_s is None else args.dt_s
    n_steps = int(round(end_s / dt_s))
    time_s = np.arange(n_steps + 1, dtype=float) * dt_s
    grid = make_radial_grid(radius_m=CYLINDER_RADIUS_M, dr_m=args.dr_m)
    result = solve_constant_radius(
        grid=grid,
        time_s=time_s,
        initial_temperature_c=INITIAL_TEMPERATURE_C,
        initial_moisture_dry_basis=INITIAL_MOISTURE_DRY_BASIS,
        boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
        boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
        property_function=property_function,
        h_w_m2_k=Q1_CONVECTION_H_W_M2_K,
        hm_m_s=Q1_CONVECTION_HM_M_S,
        picard_tolerance=args.picard_tol,
        max_picard_iterations=args.max_picard_iterations,
        track_linear_residual=track_linear_residual,
    )

    json_path = output_dir / f"{output_stem}_solution.json"
    xlsx_path = output_dir / f"{output_stem}.xlsx"
    template_path = PROJECT_ROOT / template_relative_path
    metadata = {
        "problem": problem,
        "model": model_name,
        "initial_temperature_c": INITIAL_TEMPERATURE_C,
        "initial_moisture_dry_basis": INITIAL_MOISTURE_DRY_BASIS,
        "radius_m": CYLINDER_RADIUS_M,
        "radial_step_m": args.dr_m,
        "output_radial_step_cm": 0.1,
        "time_step_s": dt_s,
        "end_time_s": end_s,
        "picard_tolerance": args.picard_tol,
        "max_picard_iterations": args.max_picard_iterations,
        "diagnostics": result.diagnostics,
    }
    write_solution_json(result, json_path, metadata)
    if not args.no_build_xlsx:
        sheet_names = ("温度", "水分浓度")
        _run_node_builder(json_path, xlsx_path, template_path, sheet_names)
        output_radius_m = np.arange(0.0, CYLINDER_RADIUS_M + 1e-12, 0.001)
        output_indices = []
        for target_radius_m in output_radius_m:
            index = int(np.argmin(np.abs(result.radius_m - target_radius_m)))
            if not np.isclose(result.radius_m[index], target_radius_m, atol=1e-12):
                raise ValueError(
                    f"no computed grid node matches output radius {target_radius_m}"
                )
            output_indices.append(index)
        output_temperature_c = result.temperature_c[:, output_indices]
        output_moisture = result.moisture_dry_basis[:, output_indices]
        verify_two_sheet_workbook(
            xlsx_path,
            sheet_names,
            result.time_s,
            output_radius_m,
            (output_temperature_c, output_moisture),
        )

    manifest = {
        "problem": problem,
        "timestamp": datetime.now().astimezone().isoformat(),
        "command": " ".join(sys.argv),
        "inputs": {
            "attachment_1": str(ATTACHMENT_1_PATH.relative_to(PROJECT_ROOT)),
            "template": template_relative_path,
        },
        "outputs": {
            "solution_json": _display_path(json_path),
            "workbook": None if args.no_build_xlsx else _display_path(xlsx_path),
        },
        "parameters": metadata,
        "code_hashes": _code_hashes(),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "openpyxl": openpyxl.__version__,
        },
    }
    manifest_path = output_dir / f"run_manifest_q{problem}.json"
    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    latest_manifest_path = output_dir / "run_manifest.json"
    with latest_manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)

    print(f"problem {problem} completed: {json_path}")
    if not args.no_build_xlsx:
        print(f"workbook written: {xlsx_path}")
    print(f"manifest written: {manifest_path}")
    print(json.dumps(result.diagnostics, ensure_ascii=False, indent=2))


def _solve_problem_1(args: argparse.Namespace) -> None:
    _solve_constant_radius_problem(
        problem=1,
        model_name="constant-property radial heat and moisture diffusion",
        property_function=q1_properties,
        default_end_s=Q1_END_TIME_S,
        default_dt_s=Q1_TIME_STEP_S,
        template_relative_path="附件/附件3/result1.xlsx",
        output_stem="result1",
        track_linear_residual=False,
        args=args,
    )


def _solve_problem_2(args: argparse.Namespace) -> None:
    _solve_constant_radius_problem(
        problem=2,
        model_name="appendix-3 variable-property radial heat and moisture diffusion",
        property_function=q2_properties,
        default_end_s=Q2_END_TIME_S,
        default_dt_s=Q2_TIME_STEP_S,
        template_relative_path="附件/附件3/result2.xlsx",
        output_stem="result2",
        track_linear_residual=True,
        args=args,
    )


def _solve_problem_3(args: argparse.Namespace) -> None:
    """问题 3：求圆心含水率首次达到 0.15 kg/kg 的烘干时间。"""
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    attachment = read_attachment_1(ATTACHMENT_1_PATH)
    air_temperature = PiecewiseLinear(attachment.time_s, attachment.air_temperature_c)
    air_moisture = PiecewiseLinear(attachment.time_s, attachment.air_moisture_dry_basis)

    dt_s = Q3_TIME_STEP_S if args.dt_s is None else args.dt_s
    horizon_s = Q3_HORIZON_CAP_S if args.end_s is None else args.end_s
    grid = make_radial_grid(radius_m=CYLINDER_RADIUS_M, dr_m=args.dr_m)

    def run(end_s: float):
        n_steps = int(round(end_s / dt_s))
        time_s = np.arange(n_steps + 1, dtype=float) * dt_s
        return solve_constant_radius(
            grid=grid,
            time_s=time_s,
            initial_temperature_c=INITIAL_TEMPERATURE_C,
            initial_moisture_dry_basis=INITIAL_MOISTURE_DRY_BASIS,
            boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
            boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
            property_function=q2_properties,
            h_w_m2_k=Q1_CONVECTION_H_W_M2_K,
            hm_m_s=Q1_CONVECTION_HM_M_S,
            picard_tolerance=args.picard_tol,
            max_picard_iterations=args.max_picard_iterations,
            track_linear_residual=True,
        )

    screening = run(horizon_s)
    center_moisture = screening.moisture_dry_basis[:, 0]
    below = np.nonzero(center_moisture <= Q3_TARGET_MOISTURE)[0]
    if below.size == 0:
        raise SystemExit(
            f"center moisture did not reach {Q3_TARGET_MOISTURE} kg/kg within "
            f"{horizon_s:.0f} s; refusing to write a partial or extrapolated result"
        )

    crossing_index = int(below[0])
    time_prev = float(screening.time_s[crossing_index - 1])
    time_next = float(screening.time_s[crossing_index])
    moisture_prev = float(center_moisture[crossing_index - 1])
    moisture_next = float(center_moisture[crossing_index])
    t_f_interp_s = time_prev + (moisture_prev - Q3_TARGET_MOISTURE) * (
        time_next - time_prev
    ) / (moisture_prev - moisture_next)

    output_stride = int(round(Q3_OUTPUT_TIME_STEP_S / dt_s))
    if output_stride < 1 or not np.isclose(
        output_stride * dt_s, Q3_OUTPUT_TIME_STEP_S, rtol=0.0, atol=1e-9
    ):
        raise ValueError(
            f"time step {dt_s} s is not compatible with the "
            f"{Q3_OUTPUT_TIME_STEP_S} s delivery interval"
        )
    if crossing_index % output_stride == 0:
        delivery_index = crossing_index
    else:
        delivery_index = (crossing_index // output_stride + 1) * output_stride
    t_f_grid_s = delivery_index * dt_s

    result = run(t_f_grid_s)
    sampled = replace(
        result,
        time_s=result.time_s[::output_stride],
        temperature_c=result.temperature_c[::output_stride],
        moisture_dry_basis=result.moisture_dry_basis[::output_stride],
        picard_iterations=result.picard_iterations[::output_stride],
    )
    if float(sampled.moisture_dry_basis[-1, 0]) > Q3_TARGET_MOISTURE:
        raise AssertionError("final sampled step does not satisfy the moisture criterion")
    if sampled.time_s.size > 1 and (
        float(sampled.moisture_dry_basis[-2, 0]) <= Q3_TARGET_MOISTURE
    ):
        raise AssertionError("an earlier delivery time already satisfied the criterion")

    json_path = output_dir / "result3_solution.json"
    xlsx_path = output_dir / "result3.xlsx"
    template_path = PROJECT_ROOT / "附件" / "附件3" / "result3.xlsx"
    metadata = {
        "problem": 3,
        "model": "appendix-3 variable-property radial heat and moisture diffusion "
        "with last-value long-term boundary",
        "initial_temperature_c": INITIAL_TEMPERATURE_C,
        "initial_moisture_dry_basis": INITIAL_MOISTURE_DRY_BASIS,
        "radius_m": CYLINDER_RADIUS_M,
        "radial_step_m": args.dr_m,
        "output_radial_step_cm": 0.1,
        "time_step_s": dt_s,
        "end_time_s": t_f_grid_s,
        "output_time_step_s": Q3_OUTPUT_TIME_STEP_S,
        "horizon_cap_s": horizon_s,
        "target_moisture_dry_basis": Q3_TARGET_MOISTURE,
        "t_f_grid_s": t_f_grid_s,
        "t_f_interp_s": t_f_interp_s,
        "t_f_hours": t_f_grid_s / 3600.0,
        "picard_tolerance": args.picard_tol,
        "max_picard_iterations": args.max_picard_iterations,
        "diagnostics": result.diagnostics,
    }
    write_solution_json(sampled, json_path, metadata)

    if not args.no_build_xlsx:
        _run_node_builder(json_path, xlsx_path, template_path, ("Sheet1",))
        output_radius_m = np.arange(0.0, CYLINDER_RADIUS_M + 1e-12, 0.001)
        output_indices = []
        for target_radius_m in output_radius_m:
            index = int(np.argmin(np.abs(sampled.radius_m - target_radius_m)))
            if not np.isclose(sampled.radius_m[index], target_radius_m, atol=1e-12):
                raise ValueError(
                    f"no computed grid node matches output radius {target_radius_m}"
                )
            output_indices.append(index)
        verify_single_sheet_workbook(
            xlsx_path,
            "Sheet1",
            sampled.time_s,
            output_radius_m,
            sampled.moisture_dry_basis[:, output_indices],
        )

    manifest = {
        "problem": 3,
        "timestamp": datetime.now().astimezone().isoformat(),
        "command": " ".join(sys.argv),
        "inputs": {
            "attachment_1": str(ATTACHMENT_1_PATH.relative_to(PROJECT_ROOT)),
            "template": "附件/附件3/result3.xlsx",
        },
        "outputs": {
            "solution_json": _display_path(json_path),
            "workbook": None if args.no_build_xlsx else _display_path(xlsx_path),
        },
        "parameters": metadata,
        "code_hashes": _code_hashes(),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "openpyxl": openpyxl.__version__,
        },
    }
    manifest_path = output_dir / "run_manifest_q3.json"
    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    latest_manifest_path = output_dir / "run_manifest.json"
    with latest_manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)

    print(f"problem 3 completed: {json_path}")
    print(f"t_f_grid = {t_f_grid_s:.0f} s ({t_f_grid_s / 3600.0:.4f} h)")
    print(f"t_f_interp = {t_f_interp_s:.0f} s ({t_f_interp_s / 3600.0:.4f} h)")
    if not args.no_build_xlsx:
        print(f"workbook written: {xlsx_path}")
    print(f"manifest written: {manifest_path}")
    print(json.dumps(result.diagnostics, ensure_ascii=False, indent=2))


def _solve_problem_4(args: argparse.Namespace) -> None:
    """问题 4：材料坐标下的收缩圆柱模型，求圆心含水率首次达到 0.15 kg/kg 的时间。"""
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    attachment1 = read_attachment_1(ATTACHMENT_1_PATH)
    attachment2 = read_attachment_2(ATTACHMENT_2_PATH)
    air_temperature = PiecewiseLinear(attachment1.time_s, attachment1.air_temperature_c)
    air_moisture = PiecewiseLinear(attachment1.time_s, attachment1.air_moisture_dry_basis)
    radius_cm = PiecewiseLinear(attachment2.time_s, attachment2.radius_cm)
    if np.any(np.diff(attachment2.radius_cm) > 0.0):
        raise ValueError("attachment 2 radius must be non-increasing (shrinkage only)")

    radius0_cm = CYLINDER_RADIUS_M * 100.0

    def radius_ratio(t: float) -> float:
        ratio = float(radius_cm(t)) / radius0_cm
        if not np.isfinite(ratio) or ratio <= 0.0:
            raise ValueError(f"invalid radius ratio at t={t:.6f} s")
        return ratio

    dt_s = Q4_TIME_STEP_S if args.dt_s is None else args.dt_s
    horizon_s = Q4_HORIZON_CAP_S if args.end_s is None else args.end_s
    grid = make_radial_grid(radius_m=CYLINDER_RADIUS_M, dr_m=args.dr_m)

    def run(end_s: float):
        n_steps = int(round(end_s / dt_s))
        time_s = np.arange(n_steps + 1, dtype=float) * dt_s
        return solve_radial(
            grid=grid,
            time_s=time_s,
            initial_temperature_c=INITIAL_TEMPERATURE_C,
            initial_moisture_dry_basis=INITIAL_MOISTURE_DRY_BASIS,
            boundary_temperature_k=lambda t: float(air_temperature(t)) + CELSIUS_TO_KELVIN,
            boundary_moisture_dry_basis=lambda t: float(air_moisture(t)),
            property_function=q4_properties,
            h_w_m2_k=Q1_CONVECTION_H_W_M2_K,
            hm_m_s=Q1_CONVECTION_HM_M_S,
            picard_tolerance=args.picard_tol,
            max_picard_iterations=args.max_picard_iterations,
            track_linear_residual=True,
            radius_scale=radius_ratio,
        )

    screening = run(horizon_s)
    center_moisture = screening.moisture_dry_basis[:, 0]
    below = np.nonzero(center_moisture <= Q4_TARGET_MOISTURE)[0]
    if below.size == 0:
        raise SystemExit(
            f"center moisture did not reach {Q4_TARGET_MOISTURE} kg/kg within "
            f"{horizon_s:.0f} s ({horizon_s / 3600.0:.1f} h); refusing to extrapolate"
        )
    crossing_index = int(below[0])
    time_prev = float(screening.time_s[crossing_index - 1])
    time_next = float(screening.time_s[crossing_index])
    moisture_prev = float(center_moisture[crossing_index - 1])
    moisture_next = float(center_moisture[crossing_index])
    t_f_interp_s = time_prev + (moisture_prev - Q4_TARGET_MOISTURE) * (
        time_next - time_prev
    ) / (moisture_prev - moisture_next)

    output_stride = int(round(Q4_OUTPUT_TIME_STEP_S / dt_s))
    if output_stride < 1 or not np.isclose(
        output_stride * dt_s, Q4_OUTPUT_TIME_STEP_S, rtol=0.0, atol=1e-9
    ):
        raise ValueError("time step is not compatible with the delivery interval")
    if crossing_index % output_stride == 0:
        delivery_index = crossing_index
    else:
        delivery_index = (crossing_index // output_stride + 1) * output_stride
    t_f_grid_s = delivery_index * dt_s

    result = run(t_f_grid_s)
    sampled = replace(
        result,
        time_s=result.time_s[::output_stride],
        temperature_c=result.temperature_c[::output_stride],
        moisture_dry_basis=result.moisture_dry_basis[::output_stride],
        picard_iterations=result.picard_iterations[::output_stride],
    )
    if float(sampled.moisture_dry_basis[-1, 0]) > Q4_TARGET_MOISTURE:
        raise AssertionError("final sampled step does not satisfy the moisture criterion")
    if sampled.time_s.size > 1 and (
        float(sampled.moisture_dry_basis[-2, 0]) <= Q4_TARGET_MOISTURE
    ):
        raise AssertionError("an earlier delivery time already satisfied the criterion")

    json_path = output_dir / "result4_solution.json"
    xlsx_path = output_dir / "result4.xlsx"
    template_path = PROJECT_ROOT / "附件" / "附件3" / "result4.xlsx"
    metadata = {
        "problem": 4,
        "model": "appendix-4 shrinking cylinder in material coordinates "
        "(affine shrinkage, no advective term)",
        "initial_temperature_c": INITIAL_TEMPERATURE_C,
        "initial_moisture_dry_basis": INITIAL_MOISTURE_DRY_BASIS,
        "reference_radius_m": CYLINDER_RADIUS_M,
        "radial_step_m": args.dr_m,
        "output_radial_step_cm": Q4_OUTPUT_RADIAL_STEP_CM,
        "time_step_s": dt_s,
        "end_time_s": t_f_grid_s,
        "output_time_step_s": Q4_OUTPUT_TIME_STEP_S,
        "horizon_cap_s": horizon_s,
        "target_moisture_dry_basis": Q4_TARGET_MOISTURE,
        "t_f_grid_s": t_f_grid_s,
        "t_f_interp_s": t_f_interp_s,
        "t_f_hours": t_f_grid_s / 3600.0,
        "radius_min_cm": float(np.min(attachment2.radius_cm)),
        "radius_end_cm": float(attachment2.radius_cm[-1]),
        "column_convention": "material points labelled by initial distance; last column is the moving surface",
        "picard_tolerance": args.picard_tol,
        "max_picard_iterations": args.max_picard_iterations,
        "diagnostics": result.diagnostics,
    }
    write_solution_json(sampled, json_path, metadata)

    if not args.no_build_xlsx:
        _run_node_builder(
            json_path,
            xlsx_path,
            template_path,
            ("Sheet1",),
            last_header=Q4_SURFACE_HEADER,
        )
        output_radius_m = np.arange(
            0.0,
            CYLINDER_RADIUS_M + 1e-12,
            Q4_OUTPUT_RADIAL_STEP_CM / 100.0,
        )
        output_indices = []
        for target_radius_m in output_radius_m:
            index = int(np.argmin(np.abs(sampled.radius_m - target_radius_m)))
            if not np.isclose(sampled.radius_m[index], target_radius_m, atol=1e-12):
                raise ValueError(
                    f"no computed grid node matches output radius {target_radius_m}"
                )
            output_indices.append(index)
        verify_single_sheet_workbook(
            xlsx_path,
            "Sheet1",
            sampled.time_s,
            output_radius_m,
            sampled.moisture_dry_basis[:, output_indices],
            last_header=Q4_SURFACE_HEADER,
        )

    manifest = {
        "problem": 4,
        "timestamp": datetime.now().astimezone().isoformat(),
        "command": " ".join(sys.argv),
        "inputs": {
            "attachment_1": str(ATTACHMENT_1_PATH.relative_to(PROJECT_ROOT)),
            "attachment_2": str(ATTACHMENT_2_PATH.relative_to(PROJECT_ROOT)),
            "template": "附件/附件3/result4.xlsx",
        },
        "outputs": {
            "solution_json": _display_path(json_path),
            "workbook": None if args.no_build_xlsx else _display_path(xlsx_path),
        },
        "parameters": metadata,
        "code_hashes": _code_hashes(),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "openpyxl": openpyxl.__version__,
        },
    }
    manifest_path = output_dir / "run_manifest_q4.json"
    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    latest_manifest_path = output_dir / "run_manifest.json"
    with latest_manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)

    print(f"problem 4 completed: {json_path}")
    print(f"t_f_grid = {t_f_grid_s:.0f} s ({t_f_grid_s / 3600.0:.4f} h)")
    print(f"t_f_interp = {t_f_interp_s:.0f} s ({t_f_interp_s / 3600.0:.4f} h)")
    if not args.no_build_xlsx:
        print(f"workbook written: {xlsx_path}")
    print(f"manifest written: {manifest_path}")
    print(json.dumps(result.diagnostics, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--problem", type=int, choices=[1, 2, 3, 4], required=True)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--dr-m", type=float, default=None)
    parser.add_argument("--dt-s", type=float, default=None)
    parser.add_argument("--end-s", type=float, default=None)
    parser.add_argument("--picard-tol", type=float, default=PICARD_TOLERANCE)
    parser.add_argument(
        "--max-picard-iterations",
        type=int,
        default=PICARD_MAX_ITERATIONS,
    )
    parser.add_argument("--no-build-xlsx", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.dr_m is None:
        if args.problem == 3:
            args.dr_m = Q3_RADIAL_STEP_M
        elif args.problem == 4:
            args.dr_m = Q4_RADIAL_STEP_M
        else:
            args.dr_m = DEFAULT_RADIAL_STEP_M
    if args.problem == 1:
        _solve_problem_1(args)
        return
    if args.problem == 2:
        _solve_problem_2(args)
        return
    if args.problem == 3:
        _solve_problem_3(args)
        return
    if args.problem == 4:
        _solve_problem_4(args)
        return
    raise NotImplementedError(f"problem {args.problem} is not implemented yet")


if __name__ == "__main__":
    main()
