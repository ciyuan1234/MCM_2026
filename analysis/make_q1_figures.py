"""Generate paper figures for problem 1 from the saved solution."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOLUTION_PATH = PROJECT_ROOT / "outputs" / "result1_solution.json"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures"


def main() -> None:
    with SOLUTION_PATH.open(encoding="utf-8") as file:
        solution = json.load(file)

    time_s = np.array(solution["time_s"], dtype=float)
    radius_cm = np.array(solution["radius_m"], dtype=float) * 100.0
    temperature_c = np.array(solution["temperature_c"], dtype=float)
    moisture = np.array(solution["moisture_dry_basis"], dtype=float)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    profile_times = [100.0, 300.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0]

    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for target_time in profile_times:
        index = int(np.where(np.isclose(time_s, target_time))[0][0])
        ax.plot(radius_cm, temperature_c[index], label=f"{target_time:.0f} s")
    ax.set_xlabel("Radial distance from center (cm)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Problem 1: radial temperature profiles")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig1_q1_temperature_profiles.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for target_time in profile_times:
        index = int(np.where(np.isclose(time_s, target_time))[0][0])
        ax.plot(radius_cm, moisture[index], label=f"{target_time:.0f} s")
    ax.set_xlabel("Radial distance from center (cm)")
    ax.set_ylabel("Moisture content (kg/kg, dry basis)")
    ax.set_title("Problem 1: radial moisture profiles")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig2_q1_moisture_profiles.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(time_s, temperature_c[:, 0], label="Center r=0 cm")
    ax.plot(time_s, temperature_c[:, -1], label="Surface r=2 cm")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Problem 1: center and surface temperature")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig3_q1_center_surface_temperature.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(time_s, moisture[:, 0], label="Center r=0 cm")
    ax.plot(time_s, moisture[:, -1], label="Surface r=2 cm")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Moisture content (kg/kg, dry basis)")
    ax.set_title("Problem 1: center and surface moisture")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig4_q1_center_surface_moisture.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
