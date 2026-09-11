"""Print the dimensionless metrics used in the problem 1 model rationale."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.diagnostics import q1_model_metrics


def main() -> None:
    print(json.dumps(q1_model_metrics(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
