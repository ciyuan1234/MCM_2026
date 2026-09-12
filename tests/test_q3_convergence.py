"""问题 3 长时程收敛证据的检查（复算脚本见 analysis/q3_convergence.py）。"""

import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONVERGENCE_PATH = PROJECT_ROOT / "outputs" / "q3_convergence.json"


def _load_report() -> dict:
    with CONVERGENCE_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def _t_f(report: dict, label: str) -> float:
    for run in report["runs"]:
        if run["label"] == label:
            return float(run["t_f_hours"])
    raise AssertionError(f"missing convergence run: {label}")


def test_q3_convergence_artifact_meets_thresholds() -> None:
    report = _load_report()
    comparisons = report["comparisons"]
    assert float(comparisons["spatial_t_f_difference_hours"]) <= 0.5
    assert float(comparisons["time_step_t_f_difference_hours"]) <= 0.0167
    assert float(comparisons["spatial_max_moisture_difference"]) <= 0.001
    assert float(comparisons["time_step_max_moisture_difference"]) <= 0.001
    for run in report["runs"]:
        assert float(run["moisture_balance_relative_error"]) < 1e-10
        assert float(run["linear_system_residual_max"]) < 1e-9


def test_q3_convergence_is_monotone_and_approaches_production_value() -> None:
    report = _load_report()
    coarse = _t_f(report, "dr=0.0625mm,dt=15s")
    production = _t_f(report, "dr=0.03125mm,dt=15s")
    fine = _t_f(report, "dr=0.015625mm,dt=15s")
    # 细化网格后答案单调下降且相邻差缩小，说明序列在收敛而不是在漂移。
    assert coarse > production > fine
    assert (coarse - production) > (production - fine)
    assert abs(production - fine) <= 0.5
