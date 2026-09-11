# 验证矩阵

- 版本日期：2026-09-11
- 说明：本表把 `AGENTS.md` 的验证要求映射到当前证据；问题 2～4 完成后继续追加。

| 验证项 | 要求 | 问题 1 证据 | 状态 |
| --- | --- | --- | --- |
| 初值检查 | `t=0` 与题设一致 | `tests/test_solver.py::test_initial_condition_is_preserved` | 通过 |
| 零驱动 | 无驱动时不变化 | `tests/test_solver.py::test_zero_drive_does_not_change_state` | 通过 |
| 趋势检查 | 更热、更干边界下趋势正确 | `tests/test_solver.py::test_heating_and_drying_trends` | 通过 |
| 守恒检查 | 内部变化与边界通量一致 | 热量误差 `1.5047e-12`，水分误差 `1.2213e-14` | 通过 |
| 空间收敛 | 至少两组空间网格 | `dr=2 mm`、`dr=1 mm`、`dr=0.5 mm` 比较 | 通过 |
| 时间收敛 | 至少两组时间步 | `dt=2 s` 对 `dt=1 s` 比较 | 通过 |
| 回归检查 | 小规模确定性算例 | `tests/test_solver.py::test_deterministic_regression_case` | 通过 |
| 数据完整性 | 无缺失、重复、倒序、非有限值 | `tests/test_interpolators.py` | 通过 |
| 插值端点 | 端点外保持最后值 | `tests/test_interpolators.py::test_piecewise_linear_exact_nodes_and_endpoint_hold` | 通过 |
| 模板回读 | 导出后关键单元格与内存一致 | `analysis/solve.py` 调用 `verify_result1_workbook` | 通过 |
| 运行记录 | 输入、参数、代码哈希、命令、环境 | `outputs/run_manifest.json` | 通过 |
| 模型选择量级检查 | 判断是否可集总、可稳态、可一维化 | `analysis/model_metrics.py`、`tests/test_model_metrics.py` | 通过 |
| 结论数值追溯 | 结论中的关键值来自结果文件 | `tests/test_q1_conclusion.py` | 通过 |
| 独立复算 | 独立实现或不同数值方案复核 | 尚未执行 | 待开始 |
| 问题 2 验证 | 变物性全过程 | `tests/test_material.py`、`tests/test_solver.py::test_q2_deterministic_regression_case`、`tests/test_result2.py` | 通过 |
| 问题 3 验证 | 圆心达标时间 | 尚未建立 | 待开始 |
| 问题 4 验证 | 移动边界和半径处理 | 尚未建立 | 待开始 |
