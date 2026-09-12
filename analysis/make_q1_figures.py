"""Generate publication-style Chinese figures for problem 1."""

from __future__ import annotations

import argparse
import json
import os
import sys
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
from matplotlib.colors import LinearSegmentedColormap, Normalize
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ATTACHMENT_2_PATH  # noqa: E402
from src.interpolators import PiecewiseLinear, read_attachment_2  # noqa: E402
DEFAULT_SOLUTION_PATHS = {
    1: PROJECT_ROOT / "outputs" / "result1_solution.json",
    2: PROJECT_ROOT / "outputs" / "result2_solution.json",
    3: PROJECT_ROOT / "outputs" / "result3_solution.json",
    4: PROJECT_ROOT / "outputs" / "result4_solution.json",
}
DEFAULT_CONVERGENCE_PATH = PROJECT_ROOT / "outputs" / "q3_convergence.json"
DEFAULT_SOLUTION_PATH = DEFAULT_SOLUTION_PATHS[1]
DEFAULT_FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures"

# 温度场在数小时内即趋于均匀，因此温度剖面使用早期时刻；含水率剖面覆盖全时段。
TEMPERATURE_PROFILE_TIMES = {
    1: [100.0, 300.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0],
    2: [1800.0, 3600.0, 5400.0, 7200.0, 9000.0, 10800.0],
    3: [0.25, 0.6, 1.0, 2.0, 6.0],
    4: [0.25, 0.6, 1.0, 2.0, 6.0],
}
MOISTURE_PROFILE_TIMES = {
    1: [100.0, 300.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0],
    2: [1800.0, 3600.0, 5400.0, 7200.0, 9000.0, 10800.0],
    3: [0.5, 6.0, 24.0, 48.0],
    4: [0.5, 6.0, 12.0, 24.0, 48.0],
}
# 兼容旧引用
PROFILE_TIMES_BY_PROBLEM = MOISTURE_PROFILE_TIMES
STAGE_LABELS = {
    1: "预热阶段",
    2: "变物性烘干阶段",
    3: "长期烘干阶段",
    4: "收缩烘干阶段",
}
SOURCE_TEXT_BY_PROBLEM = {
    1: (
        "数据来源：附件1、附录2；模型：一维径向传热—水分扩散；"
        "生成脚本：analysis/make_q1_figures.py"
    ),
    2: (
        "数据来源：附件1、附录3；模型：一维径向变物性传热—水分扩散；"
        "生成脚本：analysis/make_q1_figures.py"
    ),
    3: (
        "数据来源：附件1、附录3；模型：一维径向变物性传热—水分扩散（长期边界取末值）；"
        "生成脚本：analysis/make_q1_figures.py"
    ),
    4: (
        "数据来源：附件1、附件2、附录4；模型：材料坐标下的收缩圆柱传热—水分扩散；"
        "生成脚本：analysis/make_q1_figures.py"
    ),
}
# 黑白（灰度）规范：不使用彩色，靠灰阶 + 线型 + 标记 + 端点标注区分。
CENTER_COLOR = "#000000"
SURFACE_COLOR = "#595959"
FILL_COLOR = "#D9D9D9"
LINE_STYLES = ("-", "--", "-.", ":", (0, (5, 1, 1, 1)))
MARKERS = ("o", "s", "^", "D", "v", "P", "X")
GRAY_CMAP_LOW = 0.30
GRAY_CMAP_HIGH = 0.95
SOURCE_TEXT = SOURCE_TEXT_BY_PROBLEM[1]


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


def _gray_colormap():
    """截断的灰阶色带：最浅一条仍能被打印区分。"""
    base = plt.get_cmap("Greys")
    return LinearSegmentedColormap.from_list(
        "mcm_gray",
        base(np.linspace(GRAY_CMAP_LOW, GRAY_CMAP_HIGH, 256)),
    )


def _time_index(time_s: np.ndarray, target_time_s: float) -> int:
    matches = np.where(np.isclose(time_s, target_time_s))[0]
    if matches.size != 1:
        raise ValueError(f"time {target_time_s} is not unique in the solution")
    return int(matches[0])


def _format_seconds(value: float) -> str:
    return f"{value:.0f} s"


def _format_hours(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{text} h"


def _plot_profiles(
    axis,
    radius_cm: np.ndarray,
    values: np.ndarray,
    time_s: np.ndarray,
    times_s: list[float],
    ylabel: str,
    title: str,
    time_label: str = "时间 (s)",
    time_formatter=_format_seconds,
    annotation_dx: int = 6,
) -> ScalarMappable:
    norm = Normalize(vmin=min(times_s), vmax=max(times_s))
    cmap = _gray_colormap()
    for index_in_series, target_time_s in enumerate(times_s):
        index = _time_index(time_s, target_time_s)
        gray = cmap(norm(target_time_s))
        axis.plot(
            radius_cm,
            values[index],
            color=gray,
            linewidth=1.6,
            linestyle=LINE_STYLES[index_in_series % len(LINE_STYLES)],
            marker=MARKERS[index_in_series % len(MARKERS)],
            markersize=3.2,
            markevery=0.12,
            label=time_formatter(target_time_s),
        )

    for target_time_s, offset_y in [(times_s[0], 9), (times_s[-1], -11)]:
        index = _time_index(time_s, target_time_s)
        axis.annotate(
            time_formatter(target_time_s),
            xy=(radius_cm[-1], values[index, -1]),
            xytext=(annotation_dx, offset_y),
            textcoords="offset points",
            color="black",
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
    time_unit: str = "s",
    target_value: float | None = None,
    target_label: str | None = None,
) -> None:
    axis.plot(
        time_s,
        center_values,
        color=CENTER_COLOR,
        linestyle="-",
        marker="o",
        markersize=3.2,
        markevery=0.1,
        linewidth=1.8,
        label="圆心 r=0 cm",
    )
    axis.plot(
        time_s,
        surface_values,
        color=SURFACE_COLOR,
        linewidth=1.8,
        linestyle="--",
        marker="s",
        markersize=3.0,
        markevery=0.1,
        label="表面 r=2 cm",
    )
    axis.fill_between(
        time_s,
        center_values,
        surface_values,
        color=FILL_COLOR,
        alpha=0.55,
        linewidth=0,
    )
    axis.annotate(
        f"{center_values[-1]:.2f}",
        xy=(time_s[-1], center_values[-1]),
        xytext=(6, 6),
        textcoords="offset points",
        color="black",
        fontsize=8,
        annotation_clip=False,
    )
    axis.annotate(
        f"{surface_values[-1]:.2f}",
        xy=(time_s[-1], surface_values[-1]),
        xytext=(6, -12),
        textcoords="offset points",
        color="black",
        fontsize=8,
        annotation_clip=False,
    )
    if target_value is not None:
        axis.axhline(
            target_value,
            color="black",
            linewidth=1.0,
            linestyle=":",
            label=target_label or f"达标线 {target_value}",
        )
    axis.set_xlabel(f"时间 ({time_unit})")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend(loc="best")
    axis.margins(x=0.02)
    _style_axis(axis)


def _add_source_note(fig, source_text: str = SOURCE_TEXT) -> None:
    fig.text(
        0.01,
        0.01,
        source_text,
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
    convergence_path: Path | None = None,
) -> list[Path]:
    if problem not in DEFAULT_SOLUTION_PATHS:
        raise ValueError(f"unsupported problem: {problem}")
    if problem == 4:
        return _generate_problem_4_figures(solution_path, figure_dir)
    if solution_path is None:
        solution_path = DEFAULT_SOLUTION_PATHS[problem]
    if convergence_path is None:
        convergence_path = DEFAULT_CONVERGENCE_PATH
    stage_label = STAGE_LABELS[problem]
    source_text = SOURCE_TEXT_BY_PROBLEM[problem]
    long_horizon = problem == 3
    time_unit = "h" if long_horizon else "s"
    time_formatter = _format_hours if long_horizon else _format_seconds
    annotation_dx = -40 if long_horizon else 6

    with solution_path.open(encoding="utf-8") as file:
        solution = json.load(file)

    time_s = np.array(solution["time_s"], dtype=float)
    if long_horizon:
        time_s = time_s / 3600.0
    temperature_times = list(TEMPERATURE_PROFILE_TIMES[problem])
    moisture_times = list(MOISTURE_PROFILE_TIMES[problem])
    if long_horizon:
        moisture_times.append(float(time_s[-1]))
    else:
        temperature_times = [
            value for value in temperature_times if value <= time_s[-1] + 1e-9
        ]
        moisture_times = [
            value for value in moisture_times if value <= time_s[-1] + 1e-9
        ]
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
        temperature_times,
        "温度 (°C)",
        f"{stage_label}药材径向温度分布",
        time_label=f"时间 ({time_unit})",
        time_formatter=time_formatter,
        annotation_dx=annotation_dx,
    )
    colorbar = fig.colorbar(scalar_map, ax=axis, pad=0.02)
    colorbar.set_label(f"时间 ({time_unit})")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
    paths.extend(_save_figure(fig, figure_dir, f"fig1_q{problem}_temperature_profiles"))
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    scalar_map = _plot_profiles(
        axis,
        radius_cm,
        moisture,
        time_s,
        moisture_times,
        "水分浓度 (kg/kg，干基)",
        f"{stage_label}药材径向水分浓度分布",
        time_label=f"时间 ({time_unit})",
        time_formatter=time_formatter,
        annotation_dx=annotation_dx,
    )
    colorbar = fig.colorbar(scalar_map, ax=axis, pad=0.02)
    colorbar.set_label(f"时间 ({time_unit})")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
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
        time_unit=time_unit,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
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
        time_unit=time_unit,
        target_value=0.15 if long_horizon else None,
        target_label="达标线 0.15 kg/kg" if long_horizon else None,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
    paths.extend(_save_figure(fig, figure_dir, f"fig4_q{problem}_center_surface_moisture"))
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.2))
    scalar_map = _plot_profiles(
        axes[0, 0],
        radius_cm,
        temperature_c,
        time_s,
        temperature_times,
        "温度 (°C)",
        "径向温度分布",
        time_label=f"时间 ({time_unit})",
        time_formatter=time_formatter,
        annotation_dx=annotation_dx,
    )
    fig.colorbar(scalar_map, ax=axes[0, 0], fraction=0.046, pad=0.02).set_label(
        f"时间 ({time_unit})"
    )
    scalar_map = _plot_profiles(
        axes[0, 1],
        radius_cm,
        moisture,
        time_s,
        moisture_times,
        "水分浓度 (kg/kg，干基)",
        "径向水分浓度分布",
        time_label=f"时间 ({time_unit})",
        time_formatter=time_formatter,
        annotation_dx=annotation_dx,
    )
    fig.colorbar(scalar_map, ax=axes[0, 1], fraction=0.046, pad=0.02).set_label(
        f"时间 ({time_unit})"
    )
    _plot_center_surface(
        axes[1, 0],
        time_s,
        temperature_c[:, 0],
        temperature_c[:, -1],
        "温度 (°C)",
        "圆心与表面温度",
        time_unit=time_unit,
    )
    _plot_center_surface(
        axes[1, 1],
        time_s,
        moisture[:, 0],
        moisture[:, -1],
        "水分浓度 (kg/kg，干基)",
        "圆心与表面水分浓度",
        time_unit=time_unit,
        target_value=0.15 if long_horizon else None,
        target_label="达标线 0.15 kg/kg" if long_horizon else None,
    )
    fig.suptitle(f"问题{problem}：{stage_label}温度与水分浓度演化", fontsize=14)
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    _add_source_note(fig, source_text)
    paths.extend(_save_figure(fig, figure_dir, f"fig5_q{problem}_summary_2x2"))
    plt.close(fig)

    if long_horizon and convergence_path.exists():
        paths.extend(_make_convergence_figure(convergence_path, figure_dir, source_text))

    return paths


def _generate_problem_4_figures(
    solution_path: Path | None,
    figure_dir: Path,
) -> list[Path]:
    """问题 4 专用图组：半径收缩历史 + 材料坐标下的含水率/温度 + 与问题 3 对比。"""
    if solution_path is None:
        solution_path = DEFAULT_SOLUTION_PATHS[4]
    source_text = SOURCE_TEXT_BY_PROBLEM[4]
    with solution_path.open(encoding="utf-8") as file:
        solution = json.load(file)

    time_h = np.array(solution["time_s"], dtype=float) / 3600.0
    radius_cm = np.array(solution["radius_m"], dtype=float) * 100.0
    moisture = np.array(solution["moisture_dry_basis"], dtype=float)
    temperature = np.array(solution["temperature_c"], dtype=float)
    temperature_times = sorted(
        value for value in TEMPERATURE_PROFILE_TIMES[4] if value <= time_h[-1] + 1e-9
    )
    moisture_times = sorted(
        {*MOISTURE_PROFILE_TIMES[4], float(time_h[-1])}
    )
    moisture_times = [value for value in moisture_times if value <= time_h[-1] + 1e-9]

    figure_dir.mkdir(parents=True, exist_ok=True)
    _configure_style()
    paths: list[Path] = []

    attachment2 = read_attachment_2(ATTACHMENT_2_PATH)
    radius_curve = PiecewiseLinear(attachment2.time_s, attachment2.radius_cm)
    grid_time_h = np.linspace(0.0, float(attachment2.time_s[-1]) / 3600.0, 400)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    axis.plot(
        grid_time_h,
        radius_curve(grid_time_h * 3600.0),
        color=CENTER_COLOR,
        linewidth=1.8,
        label="分段线性插值",
    )
    axis.plot(
        attachment2.time_s / 3600.0,
        attachment2.radius_cm,
        linestyle="none",
        marker="o",
        markersize=3.0,
        color=SURFACE_COLOR,
        label="附件2 实测",
    )
    axis.annotate(
        f"{attachment2.radius_cm[-1]:.3f} cm",
        xy=(grid_time_h[-1], attachment2.radius_cm[-1]),
        xytext=(-60, 10),
        textcoords="offset points",
        fontsize=8,
        color=CENTER_COLOR,
    )
    axis.set_xlabel("时间 (h)")
    axis.set_ylabel("药材半径 (cm)")
    axis.set_title("药材半径随烘干时间的收缩过程")
    axis.legend(loc="best")
    _style_axis(axis)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
    paths.extend(_save_figure(fig, figure_dir, "fig1_q4_radius_history"))
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    scalar_map = _plot_profiles(
        axis,
        radius_cm,
        moisture,
        time_h,
        moisture_times,
        "水分浓度 (kg/kg，干基)",
        "收缩条件下药材内部含水率分布（材料坐标）",
        time_label="时间 (h)",
        time_formatter=_format_hours,
        annotation_dx=-40,
    )
    axis.set_xlabel("材料点初始距离 (cm)")
    colorbar = fig.colorbar(scalar_map, ax=axis, pad=0.02)
    colorbar.set_label("时间 (h)")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
    paths.extend(_save_figure(fig, figure_dir, "fig2_q4_moisture_profiles"))
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    _plot_center_surface(
        axis,
        time_h,
        moisture[:, 0],
        moisture[:, -1],
        "水分浓度 (kg/kg，干基)",
        "圆心与表面含水率随时间变化（收缩条件）",
        time_unit="h",
        target_value=0.15,
        target_label="达标线 0.15 kg/kg",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
    paths.extend(_save_figure(fig, figure_dir, "fig3_q4_center_surface_moisture"))
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    _plot_center_surface(
        axis,
        time_h,
        temperature[:, 0],
        temperature[:, -1],
        "温度 (°C)",
        "圆心与表面温度随时间变化（收缩条件）",
        time_unit="h",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
    paths.extend(_save_figure(fig, figure_dir, "fig4_q4_center_surface_temperature"))
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.2))
    scalar_map = _plot_profiles(
        axes[0, 0],
        radius_cm,
        moisture,
        time_h,
        moisture_times,
        "水分浓度 (kg/kg，干基)",
        "径向含水率分布",
        time_label="时间 (h)",
        time_formatter=_format_hours,
        annotation_dx=-40,
    )
    axes[0, 0].set_xlabel("材料点初始距离 (cm)")
    fig.colorbar(scalar_map, ax=axes[0, 0], fraction=0.046, pad=0.02).set_label("时间 (h)")
    scalar_map = _plot_profiles(
        axes[0, 1],
        radius_cm,
        temperature,
        time_h,
        temperature_times,
        "温度 (°C)",
        "径向温度分布",
        time_label="时间 (h)",
        time_formatter=_format_hours,
        annotation_dx=-40,
    )
    axes[0, 1].set_xlabel("材料点初始距离 (cm)")
    fig.colorbar(scalar_map, ax=axes[0, 1], fraction=0.046, pad=0.02).set_label("时间 (h)")
    _plot_center_surface(
        axes[1, 0],
        time_h,
        temperature[:, 0],
        temperature[:, -1],
        "温度 (°C)",
        "圆心与表面温度",
        time_unit="h",
    )
    _plot_center_surface(
        axes[1, 1],
        time_h,
        moisture[:, 0],
        moisture[:, -1],
        "水分浓度 (kg/kg，干基)",
        "圆心与表面含水率",
        time_unit="h",
        target_value=0.15,
        target_label="达标线 0.15 kg/kg",
    )
    fig.suptitle("问题4：收缩条件下温度与含水率演化", fontsize=14)
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    _add_source_note(fig, source_text)
    paths.extend(_save_figure(fig, figure_dir, "fig5_q4_summary_2x2"))
    plt.close(fig)

    q3_path = DEFAULT_SOLUTION_PATHS[3]
    if q3_path.exists():
        with q3_path.open(encoding="utf-8") as file:
            q3_solution = json.load(file)
        q3_time_h = np.array(q3_solution["time_s"], dtype=float) / 3600.0
        q3_moisture = np.array(q3_solution["moisture_dry_basis"], dtype=float)
        fig, axis = plt.subplots(figsize=(6.6, 4.4))
        axis.plot(
            q3_time_h,
            q3_moisture[:, 0],
            color=CENTER_COLOR,
            linewidth=1.8,
            label="问题3 固定半径（圆心）",
        )
        axis.plot(
            time_h,
            moisture[:, 0],
            color=SURFACE_COLOR,
            linewidth=1.8,
            linestyle="--",
            label="问题4 收缩（圆心）",
        )
        axis.axhline(0.15, color="#555555", linewidth=1.0, linestyle=":", label="达标线 0.15 kg/kg")
        axis.set_xlabel("时间 (h)")
        axis.set_ylabel("圆心含水率 (kg/kg，干基)")
        axis.set_title("固定半径与收缩条件的干燥进程对比")
        axis.legend(loc="best")
        _style_axis(axis)
        fig.tight_layout(rect=[0, 0.04, 1, 1])
        _add_source_note(fig, source_text)
        paths.extend(_save_figure(fig, figure_dir, "fig6_q4_q3_comparison"))
        plt.close(fig)

    return paths


def _make_convergence_figure(
    convergence_path: Path,
    figure_dir: Path,
    source_text: str,
) -> list[Path]:
    with convergence_path.open(encoding="utf-8") as file:
        report = json.load(file)
    runs = report["runs"]
    production_label = report["comparisons"]["production_label"]
    production_dr_prefix = production_label.split(",")[0]
    production_time_step = float(production_label.split("dt=")[1].rstrip("s"))
    spatial = [run for run in runs if run["time_step_s"] == production_time_step]
    spatial_sorted = sorted(spatial, key=lambda run: run["radial_step_m"], reverse=True)
    time_step_runs = [
        run for run in runs if run["label"].startswith(production_dr_prefix)
    ]
    time_step_sorted = sorted(time_step_runs, key=lambda run: run["time_step_s"], reverse=True)

    fig, axis = plt.subplots(figsize=(6.6, 4.4))
    axis.plot(
        [run["radial_step_m"] * 1000.0 for run in spatial_sorted],
        [run["t_f_hours"] for run in spatial_sorted],
        marker="o",
        color=CENTER_COLOR,
        linewidth=1.8,
        label="空间网格收敛（时间步 15 s）",
    )
    axis.plot(
        [run["radial_step_m"] * 1000.0 for run in time_step_sorted],
        [run["t_f_hours"] for run in time_step_sorted],
        marker="s",
        linestyle="--",
        color=SURFACE_COLOR,
        linewidth=1.8,
        label="时间步收敛（空间步长 0.0625 mm）",
    )
    for run in spatial_sorted:
        axis.annotate(
            f"{run['t_f_hours']:.2f}",
            xy=(run["radial_step_m"] * 1000.0, run["t_f_hours"]),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=CENTER_COLOR,
        )
    for run in time_step_sorted:
        axis.annotate(
            f"{run['t_f_hours']:.2f}（dt={run['time_step_s']:.0f} s）",
            xy=(run["radial_step_m"] * 1000.0, run["t_f_hours"]),
            xytext=(0, -14),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=SURFACE_COLOR,
        )
    axis.set_xscale("log")
    axis.set_xlabel("空间步长 (mm，对数坐标)")
    axis.set_ylabel("烘干时间 t_f (h)")
    axis.set_title("问题3：烘干时间对网格与时间步的收敛趋势")
    axis.legend(loc="best")
    _style_axis(axis)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    _add_source_note(fig, source_text)
    paths = _save_figure(fig, figure_dir, "fig6_q3_convergence")
    plt.close(fig)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--problem", type=int, choices=[1, 2, 3, 4], default=1)
    parser.add_argument("--solution", type=Path, default=None)
    parser.add_argument("--convergence", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    args = parser.parse_args()
    paths = generate_figures(
        args.solution, args.output_dir, args.problem, args.convergence
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
