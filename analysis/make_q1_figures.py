"""Generate publication-style Chinese figures for problem 1."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import matplotlib

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "mcm_matplotlib"),
)
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOLUTION_PATHS = {
    1: PROJECT_ROOT / "outputs" / "result1_solution.json",
    2: PROJECT_ROOT / "outputs" / "result2_solution.json",
}
DEFAULT_SOLUTION_PATH = DEFAULT_SOLUTION_PATHS[1]
DEFAULT_FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures"

PROFILE_TIMES_BY_PROBLEM = {
    1: [100.0, 300.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0],
    2: [1800.0, 3600.0, 5400.0, 7200.0, 9000.0, 10800.0],
}
CENTER_COLOR = "#0072B2"
SURFACE_COLOR = "#D55E00"
SOURCE_TEXT = (
    "数据来源：附件1、附录2；模型：一维径向传热—水分扩散；"
    "生成脚本：analysis/make_q1_figures.py"
)


def _configure_style() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": [
                "Arial Unicode MS",
                "Heiti TC",
                "Songti SC",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10.5,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.linewidth": 0.8,
            "figure.dpi": 120,
        }
    )


def _style_axis(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.grid(True, which="major", alpha=0.25, linewidth=0.6)
    axis.set_axisbelow(True)


def _time_index(time_s: np.ndarray, target_time_s: float) -> int:
    matches = np.where(np.isclose(time_s, target_time_s))[0]
    if matches.size != 1:
        raise ValueError(f"time {target_time_s} is not unique in the solution")
    return int(matches[0])


def _plot_profiles(
    axis,
    radius_cm: np.ndarray,
    values: np.ndarray,
    time_s: np.ndarray,
    times_s: list[float],
    ylabel: str,
    title: str,
) -> ScalarMappable:
    norm = Normalize(vmin=min(times_s), vmax=max(times_s))
    cmap = plt.get_cmap("viridis")
    for target_time_s in times_s:
        index = _time_index(time_s, target_time_s)
        axis.plot(
            radius_cm,
            values[index],
            color=cmap(norm(target_time_s)),
            linewidth=1.6,
            label=f"{target_time_s:.0f} s",
        )

    for target_time_s, offset_y in [(times_s[0], 9), (times_s[-1], -11)]:
        index = _time_index(time_s, target_time_s)
        axis.annotate(
            f"{target_time_s:.0f} s",
            xy=(radius_cm[-1], values[index, -1]),
            xytext=(6, offset_y),
            textcoords="offset points",
            color=cmap(norm(target_time_s)),
            fontsize=8,
            va="center",
            annotation_clip=False,
        )

    axis.set_xlabel("到药材中心的距离 (cm)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.margins(x=0.02)
    _style_axis(axis)
    return ScalarMappable(norm=norm, cmap=cmap)


def _plot_center_surface(
    axis,
    time_s: np.ndarray,
    center_values: np.ndarray,
    surface_values: np.ndarray,
    ylabel: str,
    title: str,
) -> None:
    axis.plot(
        time_s,
        center_values,
        color=CENTER_COLOR,
        linewidth=1.8,
        label="圆心 r=0 cm",
    )
    axis.plot(
        time_s,
        surface_values,
        color=SURFACE_COLOR,
        linewidth=1.8,
        linestyle="--",
        label="表面 r=2 cm",
    )
    axis.fill_between(
        time_s,
        center_values,
        surface_values,
        color=SURFACE_COLOR,
        alpha=0.12,
        linewidth=0,
    )
    axis.annotate(
        f"{center_values[-1]:.2f}",
        xy=(time_s[-1], center_values[-1]),
        xytext=(6, 6),
        textcoords="offset points",
        color=CENTER_COLOR,
        fontsize=8,
        annotation_clip=False,
    )
    axis.annotate(
        f"{surface_values[-1]:.2f}",
        xy=(time_s[-1], surface_values[-1]),
        xytext=(6, -12),
        textcoords="offset points",
        color=SURFACE_COLOR,
        fontsize=8,
        annotation_clip=False,
    )
    axis.set_xlabel("时间 (s)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend(loc="best")
    axis.margins(x=0.02)
    _style_axis(axis)


def _add_source_note(fig) -> None:
    fig.text(
        0.01,
        0.01,
        SOURCE_TEXT,
        ha="left",
        va="bottom",
        fontsize=7,
        color="#555555",
    )


def _save_figure(fig, figure_dir: Path, stem: str) -> list[Path]:
    paths: list[Path] = []
    for extension in ("png", "pdf", "svg"):
        path = figure_dir / f"{stem}.{extension}"
        fig.savefig(
            path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
        )
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"failed to write figure: {path}")
        paths.append(path)
    return paths


def generate_figures(
    solution_path: Path | None = None,
    figure_dir: Path = DEFAULT_FIGURE_DIR,
    problem: int = 1,
) -> list[Path]:
    if problem not in DEFAULT_SOLUTION_PATHS:
        raise ValueError(f"unsupported problem: {problem}")
    if solution_path is None:
        solution_path = DEFAULT_SOLUTION_PATHS[problem]
    profile_times = PROFILE_TIMES_BY_PROBLEM[problem]
    stage_label = "预热阶段" if problem == 1 else "变物性烘干阶段"

    with solution_path.open(encoding="utf-8") as file:
        solution = json.load(file)

    time_s = np.array(solution["time_s"], dtype=float)
    radius_cm = np.array(solution["radius_m"], dtype=float) * 100.0
    temperature_c = np.array(solution["temperature_c"], dtype=float)
    moisture = np.array(solution["moisture_dry_basis"], dtype=float)
    figure_dir.mkdir(parents=True, exist_ok=True)
    _configure_style()
    paths: list[Path] = []

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    scalar_map = _plot_profiles(
        axis,
        radius_cm,
        temperature_c,
        time_s,
        profile_times,
        "温度 (°C)",
        f"{stage_label}药材径向温度分布",
    )
    colorbar = fig.colorbar(scalar_map, ax=axis, pad=0.02)
    colorbar.set_label("时间 (s)")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig)
    paths.extend(_save_figure(fig, figure_dir, f"fig1_q{problem}_temperature_profiles"))
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    scalar_map = _plot_profiles(
        axis,
        radius_cm,
        moisture,
        time_s,
        profile_times,
        "水分浓度 (kg/kg，干基)",
        f"{stage_label}药材径向水分浓度分布",
    )
    colorbar = fig.colorbar(scalar_map, ax=axis, pad=0.02)
    colorbar.set_label("时间 (s)")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig)
    paths.extend(_save_figure(fig, figure_dir, f"fig2_q{problem}_moisture_profiles"))
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    _plot_center_surface(
        axis,
        time_s,
        temperature_c[:, 0],
        temperature_c[:, -1],
        "温度 (°C)",
        "圆心与表面温度随时间变化",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig)
    paths.extend(_save_figure(fig, figure_dir, f"fig3_q{problem}_center_surface_temperature"))
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    _plot_center_surface(
        axis,
        time_s,
        moisture[:, 0],
        moisture[:, -1],
        "水分浓度 (kg/kg，干基)",
        "圆心与表面水分浓度随时间变化",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig)
    paths.extend(_save_figure(fig, figure_dir, f"fig4_q{problem}_center_surface_moisture"))
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.2))
    scalar_map = _plot_profiles(
        axes[0, 0],
        radius_cm,
        temperature_c,
        time_s,
        profile_times,
        "温度 (°C)",
        "径向温度分布",
    )
    fig.colorbar(scalar_map, ax=axes[0, 0], fraction=0.046, pad=0.02).set_label("时间 (s)")
    scalar_map = _plot_profiles(
        axes[0, 1],
        radius_cm,
        moisture,
        time_s,
        profile_times,
        "水分浓度 (kg/kg，干基)",
        "径向水分浓度分布",
    )
    fig.colorbar(scalar_map, ax=axes[0, 1], fraction=0.046, pad=0.02).set_label("时间 (s)")
    _plot_center_surface(
        axes[1, 0],
        time_s,
        temperature_c[:, 0],
        temperature_c[:, -1],
        "温度 (°C)",
        "圆心与表面温度",
    )
    _plot_center_surface(
        axes[1, 1],
        time_s,
        moisture[:, 0],
        moisture[:, -1],
        "水分浓度 (kg/kg，干基)",
        "圆心与表面水分浓度",
    )
    fig.suptitle(f"问题{problem}：{stage_label}温度与水分浓度演化", fontsize=14)
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    _add_source_note(fig)
    paths.extend(_save_figure(fig, figure_dir, f"fig5_q{problem}_summary_2x2"))
    plt.close(fig)

    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--problem", type=int, choices=[1, 2], default=1)
    parser.add_argument("--solution", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    args = parser.parse_args()
    paths = generate_figures(args.solution, args.output_dir, args.problem)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
