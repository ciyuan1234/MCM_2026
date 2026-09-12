"""问题 4 收敛证据的检查（复算脚本见 analysis/q4_convergence.py）。"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONVERGENCE_PATH = PROJECT_ROOT / "outputs" / "q4_convergence.json"


def _load_report() -> dict:
    with CONVERGENCE_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def _t_f(report: dict, label: str) -> float:
    for run in report["runs"]:
        if run["label"] == label:
            return float(run["t_f_hours"])
    raise AssertionError(f"missing convergence run: {label}")


def test_q4_convergence_artifact_meets_thresholds() -> None:
    report = _load_report()
    comparisons = report["comparisons"]
    assert float(comparisons["spatial_t_f_difference_hours"]) <= 0.5
    assert float(comparisons["time_step_t_f_difference_hours"]) <= 0.0167
    assert float(comparisons["spatial_max_moisture_difference"]) <= 0.001
    assert float(comparisons["time_step_max_moisture_difference"]) <= 0.001
    for run in report["runs"]:
        assert float(run["moisture_balance_relative_error"]) < 1e-10
        assert float(run["linear_system_residual_max"]) < 1e-9


def test_q4_convergence_is_monotone() -> None:
    report = _load_report()
    coarse = _t_f(report, "dr=0.0625mm,dt=15s")
    production = _t_f(report, "dr=0.03125mm,dt=15s")
    fine = _t_f(report, "dr=0.015625mm,dt=15s")
    assert coarse > production > fine
    assert (coarse - production) > (production - fine)
