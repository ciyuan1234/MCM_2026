<p align="center">
  <img src="docs/assets/banner.png" alt="CUMCM 2026 Problem A: herb drying" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/CUMCM-2026%20Problem%20A-1f6feb?style=flat-square" alt="CUMCM 2026 A">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-60%20passed-2ea44f?style=flat-square" alt="60 tests">
  <img src="https://img.shields.io/github/stars/ciyuan1234/MCM_2026?style=flat-square&color=e8c872" alt="Stars">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square" alt="MIT">
</p>

<p align="center">
  <a href="README.md">中文</a>
  ·
  <a href="docs/overview.md">Overview</a>
  ·
  <a href="docs/paper_draft.md">Paper draft</a>
</p>

# CUMCM 2026 Problem A · Herb drying

Open repository for **CUMCM 2026 Problem A**: problem statement, solver, result workbooks, paper figures, and a paper draft.

A freshly harvested cylindrical herb dries in a hot-air oven. Heat moves inward; moisture moves outward. This repo solves all four questions with **1-D radial heat–moisture diffusion** and an **implicit finite-volume scheme**, from constant properties through variable properties, a process endpoint, and a shrinking boundary. Every headline number traces to code, tests, and files under `outputs/`.

If this helped you, please **star** the repo.

## What’s in the repo

| Item | Path |
| --- | --- |
| Problem PDF | [`A题.pdf`](A题.pdf) |
| Official attachments (read-only) | [`附件/`](附件/) |
| Solver | [`src/`](src/) · [`analysis/solve.py`](analysis/solve.py) |
| Result workbooks | [`outputs/result1.xlsx`](outputs/result1.xlsx) – [`result4.xlsx`](outputs/result4.xlsx) |
| Figures (PNG / PDF / SVG) | [`outputs/figures/`](outputs/figures/) |
| Paper draft | [`docs/paper_draft.md`](docs/paper_draft.md) |
| Numbers and evidence | [`docs/overview.md`](docs/overview.md) |

## Answers

| Q | Setup | Result |
| --- | --- | --- |
| 1 | 30 min preheat, constant properties | Surface heats and dries first; at 1800 s the center is still **2.5500 kg/kg** |
| 2 | 3 h, variable properties | Heat transfer is done (ΔT = **0.117 °C**); center moisture **1.7662 kg/kg**, far from target |
| 3 | Full cycle, fixed radius | Time to 0.15 kg/kg at the center: **57.2667 h** |
| 4 | Full cycle, shrinkage | Radius 2.000 → 1.198 cm gives **50.8500 h**, **11.2% faster** |

Question 4 is the industrial question: **does shrinkage speed drying or slow it down?** Shorter path accelerates; denser tissue decelerates. Decomposition: properties **+71.9 h**, geometry **−78.3 h**. The two large effects nearly cancel.

## Quick start

Python 3.11+. Filled workbooks already live in `outputs/`.

```bash
git clone https://github.com/ciyuan1234/MCM_2026.git
cd MCM_2026
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

```bash
python analysis/solve.py --problem 1   # likewise 2, 3, 4
python analysis/make_q1_figures.py --problem 1
```

Add `--no-build-xlsx` if the Node workbook builder is missing. Fine-grid `outputs/*_solution.json` files exceed 100 MB and are gitignored.

## Citation

```bibtex
@software{mcm2026_herb_drying,
  title  = {CUMCM 2026 Problem A: Herb Drying},
  author = {ciyuan1234},
  year   = {2026},
  url    = {https://github.com/ciyuan1234/MCM_2026}
}
```

Code and docs: [MIT](LICENSE). The contest PDF and official attachments remain copyright of the organizing committee.

Companion AI workflow: [ciyuan1234/MCM_skills](https://github.com/ciyuan1234/MCM_skills)
