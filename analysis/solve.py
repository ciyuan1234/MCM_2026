"""Reproducible entry point for the drying-problem models."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
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
)
from src.export_xlsx import verify_two_sheet_workbook, write_solution_json  # noqa: E402
from src.interpolators import PiecewiseLinear, read_attachment_1  # noqa: E402
from src.material import q1_properties, q2_properties  # noqa: E402
from src.radial_solver import make_radial_grid, solve_constant_radius  # noqa: E402


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
    subprocess.run(
        [
            "node",
            str(builder),
            str(json_path),
            str(xlsx_path),
            str(template_path),
            ",".join(sheet_names),
        ],
        check=True,
        cwd=PROJECT_ROOT,
    )


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
        verify_two_sheet_workbook(
            xlsx_path,
            sheet_names,
            result.time_s,
            result.radius_m,
            (result.temperature_c, result.moisture_dry_basis),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--problem", type=int, choices=[1, 2], required=True)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--dr-m", type=float, default=DEFAULT_RADIAL_STEP_M)
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
    if args.problem == 1:
        _solve_problem_1(args)
        return
    if args.problem == 2:
        _solve_problem_2(args)
        return
    raise NotImplementedError(f"problem {args.problem} is not implemented yet")


if __name__ == "__main__":
    main()
