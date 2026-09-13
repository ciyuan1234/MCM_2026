# 贡献指南

感谢你愿意改进这份 2026 国赛 A 题实现。本仓库把「可追溯、可复现、可审查」写进了 [`AGENTS.md`](AGENTS.md)；贡献前请先读它和 [`docs/overview.md`](docs/overview.md)。

## 能帮上忙的方向

- 修复文档笔误、失效链接、本机路径泄漏
- 补充独立复算、敏感性实验或潜热影响的量化（见 `docs/gap_register.md`）
- 改进出图、无障碍对比度和英文说明
- 把官方论文格式落实到可编译的 LaTeX / Word（目前缺官方模板，GAP-013）

不接受：无证据地改写头条数字、覆盖 `附件/`、把未确认原型写进 `outputs/result*.xlsx`。

## 本地开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

- 计算内核用 SI 单位；输入输出层才做 cm / h / °C 转换。
- 阿伦尼乌斯项的温度必须用开尔文。
- `附件/` 只读。新结果写到 `outputs/`。
- 一次提交只做一件事，提交信息用祈使句，例如 `docs: add english readme`。

完整 60 项测试里，结论追溯依赖本地 `outputs/*_solution.json`（体积过大未入库）。没有这些文件时，请跑：

```bash
python -m pytest -q \
  tests/test_units.py \
  tests/test_material.py \
  tests/test_interpolators.py \
  tests/test_solver.py \
  tests/test_export.py \
  tests/test_q3_convergence.py \
  tests/test_q4_convergence.py
```

## 提 Issue / PR

- Issue 请写清：对应哪一问、期望行为、实际行为、复现命令。
- 改模型或阈值前，先在 Issue 里给出证据（赛题原文、运行日志、测试），不要只给「感觉应该更快」。
- PR 请说明：改了什么、怎么验证、有什么未验证范围。

赛题 PDF 与官方附件版权归组委会；请不要把本仓库当作官方题解发布渠道。
