"""生成问题四的效应拆解证据文件 outputs/q4_decomposition.json。

四个对照点：
  A = 附录 3 物性 + 固定半径 2 cm      -> outputs/result3_solution.json
  B = 附录 4 物性 + 固定半径 2 cm      -> EXP-004 的实验产物（--case-b 指定）
  C = 附录 4 物性 + 实际收缩           -> outputs/result4_solution.json
  D = 附录 4 物性 + 全程 1.198 cm      -> EXP-003 报告值（--case-d-hours）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_TIME_STEP_S = 60.0


def _downsample(time_s: np.ndarray, center: np.ndarray) -> tuple[list, list]:
    stride = int(round(OUTPUT_TIME_STEP_S / float(time_s[1] - time_s[0])))
    stride = max(stride, 1)
    return time_s[::stride].tolist(), center[::stride].tolist()


def _main_repo_case(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        solution = json.load(file)
    time_s = np.array(solution["time_s"], dtype=float)
    center = np.array(solution["moisture_dry_basis"], dtype=float)[:, 0]
    return {
        "t_f_hours": float(solution["metadata"]["t_f_hours"]),
        "time_s": _downsample(time_s, center)[0],
        "center_moisture": _downsample(time_s, center)[1],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-b", type=Path, required=True, help="EXP-004 的 B 产物")
    parser.add_argument(
        "--case-d-hours",
        type=float,
        default=47.5598,
        help="EXP-003 的 D 值（附录 4 + 全程 1.198 cm）",
    )
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "q4_decomposition.json")
    args = parser.parse_args()

    with args.case_b.open(encoding="utf-8") as file:
        case_b_raw = json.load(file)
    time_b = np.array(case_b_raw["time_s"], dtype=float)
    center_b = np.array(case_b_raw["center_moisture"], dtype=float)

    cases = {
        "A_appendix3_fixed_radius": _main_repo_case(
            PROJECT_ROOT / "outputs" / "result3_solution.json"
        ),
        "B_appendix4_fixed_radius": {
            "t_f_hours": float(case_b_raw["t_f_hours"]),
            "time_s": _downsample(time_b, center_b)[0],
            "center_moisture": _downsample(time_b, center_b)[1],
        },
        "C_appendix4_shrinking": _main_repo_case(
            PROJECT_ROOT / "outputs" / "result4_solution.json"
        ),
        "D_appendix4_final_radius": {"t_f_hours": float(args.case_d_hours)},
    }
    a_hours = cases["A_appendix3_fixed_radius"]["t_f_hours"]
    b_hours = cases["B_appendix4_fixed_radius"]["t_f_hours"]
    c_hours = cases["C_appendix4_shrinking"]["t_f_hours"]
    effects = {
        "property_effect_hours": b_hours - a_hours,
        "geometry_effect_hours": c_hours - b_hours,
        "total_effect_hours": c_hours - a_hours,
        "reference_final_radius_effect_hours": c_hours
        - cases["D_appendix4_final_radius"]["t_f_hours"],
    }
    payload = {
        "note": "A/B/C 为同一求解器与同一数值设置下的三个对照点；D 为 EXP-003 的参考点。",
        "cases": cases,
        "effects": effects,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    print(json.dumps({"t_f": {k: v["t_f_hours"] for k, v in cases.items()}, "effects": effects}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
