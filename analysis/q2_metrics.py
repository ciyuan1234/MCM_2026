"""Print problem 2 property ranges over the computed 3-hour solution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.diagnostics import q2_property_ranges  # noqa: E402


def main() -> None:
    with (PROJECT_ROOT / "outputs" / "result2_solution.json").open(
        encoding="utf-8"
    ) as file:
        solution = json.load(file)
    print(
        json.dumps(
            q2_property_ranges(
                np.array(solution["moisture_dry_basis"], dtype=float),
                np.array(solution["temperature_c"], dtype=float) + 273.15,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
