# 验证矩阵

- 版本日期：2026-09-12
- 说明：本表把 `AGENTS.md` 的验证要求映射到当前证据；四问与实验均已完成，跨问一致性见 `docs/overview.md` 第 6 节。

| 验证项 | 要求 | 问题 1 证据 | 状态 |
| --- | --- | --- | --- |
| 初值检查 | `t=0` 与题设一致 | `tests/test_solver.py::test_initial_condition_is_preserved` | 通过 |
| 零驱动 | 无驱动时不变化 | `tests/test_solver.py::test_zero_drive_does_not_change_state` | 通过 |
| 趋势检查 | 更热、更干边界下趋势正确 | `tests/test_solver.py::test_heating_and_drying_trends` | 通过 |
| 守恒检查 | 内部变化与边界通量一致 | 热量误差 `1.5047e-12`，水分误差 `1.2213e-14` | 通过 |
| 空间收敛 | 至少两组空间网格 | `dr=0.125 mm` 对 `dr=0.0625 mm`：最大水分差 `3.51e-4 kg/kg` | 通过 |
| 时间收敛 | 至少两组时间步 | `dt=1 s` 对 `dt=0.5 s`：最大水分差 `2.04e-4 kg/kg` | 通过 |
| 回归检查 | 小规模确定性算例 | `tests/test_solver.py::test_deterministic_regression_case` | 通过 |
| 数据完整性 | 无缺失、重复、倒序、非有限值 | `tests/test_interpolators.py` | 通过 |
| 插值端点 | 端点外保持最后值 | `tests/test_interpolators.py::test_piecewise_linear_exact_nodes_and_endpoint_hold` | 通过 |
| 模板回读 | 导出后关键单元格与内存一致 | `analysis/solve.py` 调用 `verify_result1_workbook` | 通过 |
| 运行记录 | 输入、参数、代码哈希、命令、环境 | `outputs/run_manifest.json` | 通过 |
| 模型选择量级检查 | 判断是否可集总、可稳态、可一维化 | `analysis/model_metrics.py`、`tests/test_model_metrics.py` | 通过 |
| 结论数值追溯 | 结论中的关键值来自结果文件 | `tests/test_q1_conclusion.py` | 通过 |
| 独立复算 | 独立实现或不同数值方案复核 | 问题 1：EXP-Q1-001 独立显式差分；问题 3：EXP-Q3-001 独立节点中心差分 + BDF | 已完成 |
| 问题 2 物性公式 | 附录 3 公式正确 | `tests/test_material.py::test_q2_properties_match_appendix_3` | 通过 |
| 问题 2 回归 | 变物性小规模确定性算例 | `tests/test_solver.py::test_q2_deterministic_regression_case` | 通过 |
| 问题 2 水分守恒 | 内部水分变化与边界通量一致 | 相对误差 `2.3637e-15` | 通过 |
| 问题 2 离散残差 | 离散热方程线性系统闭合 | 最大残差 `6.0203e-16` | 通过 |
| 问题 2 空间收敛 | 至少两组空间网格 | `dr=0.125/0.0625 mm`：最大水分差 `1.89e-5 kg/kg` | 通过 |
| 问题 2 时间收敛 | 至少两组时间步 | `dt=1/0.5 s`：最大水分差 `4.57e-5 kg/kg` | 通过 |
| 问题 2 模板回读 | `result2.xlsx` 与内存结果一致 | `tests/test_result2.py` | 通过 |
| 问题 2 结论追溯 | 结论关键值来自结果文件 | `tests/test_q2_conclusion.py` | 通过 |
| 问题 2 物性范围 | 量化附录 3 必要性 | `analysis/q2_metrics.py`、`tests/test_q2_metrics.py` | 通过 |
| 问题 3 初值 | `t=0` 时 `T=28 °C`、`C=2.55 kg/kg` | `tests/test_solver.py::test_initial_condition_is_preserved`、`tests/test_q3_solver.py` | 通过 |
| 问题 3 零驱动 | 空气状态等于药材初始状态时不变化 | `tests/test_q3_solver.py::test_q3_zero_drive_keeps_initial_state` | 通过 |
| 问题 3 圆心判据 | 圆心是空间最大含水率位置且单调下降 | `tests/test_q3_solver.py::test_q3_center_is_last_position_to_dry`、`tests/test_result3.py` | 通过 |
| 问题 3 表面/圆心先达标 | 表面先接近空气含水率，圆心最后达标 | `tests/test_q3_solver.py::test_q3_surface_reaches_air_moisture_before_center_reaches_target` | 通过 |
| 问题 3 水分守恒 | 内部变化与边界通量一致 | `outputs/run_manifest_q3.json`：`5.24e-14` | 通过 |
| 问题 3 离散残差 | 离散热方程线性系统闭合 | `outputs/run_manifest_q3.json`：`1.57e-13` | 通过 |
| 问题 3 时间收敛 | `dt=15 s` 对 `dt=30 s` | `outputs/q3_convergence.json`：`Δt_f = 0.0131 h`（阈值 0.0167 h） | 通过 |
| 问题 3 预热段时间步精度 | 对 `dt=5 s` 参考 `0.5 h` 表面含水率偏差 | `dt=30 s`：`2.28e-3`（不达标）；`dt=15 s`：`9.1e-4`（阈值 `1e-3`） | 通过（15 s） |
| 问题 3 空间收敛（`t_f`） | 生产网格 `0.03125 mm` 对 `0.015625 mm` | `Δt_f = 0.0539 h`（阈值 0.5 h） | 通过 |
| 问题 3 空间收敛（含水率场） | 生产网格对 `0.015625 mm` 的 6 h 采样场 | `3.754e-4 kg/kg`（阈值 `1e-3`） | 通过 |
| 问题 3 网格细化前的问题记录 | `0.0625 mm` 对 `0.03125 mm` 的近表面带 | `2.252e-3 kg/kg` 超阈值，据此细化网格（GAP-029） | 已关闭 |
| 问题 3 短窗口中网格收敛 | `0.125` 对 `0.0625 mm`，2 h 窗口 | `tests/test_q3_solver.py::test_q3_grid_convergence_over_short_window` | 通过 |
| 问题 3 模板回读 | `result3.xlsx` 单表 `Sheet1` 与内存结果一致 | `tests/test_result3.py` | 通过 |
| 问题 3 结论追溯 | 结论关键值来自结果文件 | `tests/test_q3_conclusion.py` | 通过 |
| 问题 4 常数半径回归 | 泛化求解器与 `solve_constant_radius` 完全一致 | `tests/test_q4_solver.py::test_constant_radius_path_is_unchanged_by_generalization` | 通过（逐数组相等） |
| 问题 4 收缩物理 | 收缩条件比固定几何更快失水 | `tests/test_q4_solver.py::test_shrinking_domain_dries_faster_than_frozen_geometry` | 通过 |
| 问题 4 圆心判据 | 圆心是空间最大含水率且单调下降 | `tests/test_q4_solver.py`、`tests/test_result4.py` | 通过 |
| 问题 4 水分守恒 | 表面通量按 `2πR(t)` 计 | `outputs/run_manifest_q4.json`：`5.34e-15` | 通过 |
| 问题 4 离散残差 | 离散热方程线性系统闭合 | `outputs/run_manifest_q4.json`：`2.24e-13` | 通过 |
| 问题 4 半径检查 | 单调不增、端点保持、非正半径拒绝 | `tests/test_q4_solver.py` | 通过 |
| 问题 4 模板回读 | `result4.xlsx` 单表与内存一致，末列 `药材表面` | `tests/test_result4.py` | 通过 |
| 问题 4 结论追溯 | 结论值来自结果文件，并锁定与问题 3 的差值 | `tests/test_q4_conclusion.py` | 通过 |
| 问题 4 网格收敛 | `0.03125` 对 `0.015625 mm` | `Δt_f = 0.0058 h`（阈值 0.5 h）；场差 `5.26e-5 kg/kg`（阈值 `1e-3`） | 通过 |
| 问题 4 时间步收敛 | `15` 对 `30 s` | `Δt_f = 0.0099 h`（阈值 0.0167 h） | 通过 |
| 问题 1 独立复算（EXP-Q1-001） | 独立显式差分对高分辨率参考 | 5 项测试通过；促成生产网格细化（G-023） | 已完成 |
| 问题 3 长期边界（EXP-002） | 三种边界处理对比 | `+0.36 h`（阈值 1 h），区间 57.25～57.61 h | 已完成 |
| 问题 3 独立复算（EXP-Q3-001） | 独立实现 0～24 h 轨迹 | 圆心含水率最大差 `7.5e-4 kg/kg`、里程碑时刻相对差 ≤0.42% | 已完成 |
| 问题 4 半径处理（EXP-003） | 分段线性 / 平滑 / 全程末值半径 | 平滑 `+0.0132 h`（通过）；忽略收缩 `−3.2820 h`（超阈值，须报告区间） | 已完成 |
| 跨问参数一致性 | 表面系数与阈值四问同源 | `h=25`、`hm=8e-7`、`C ≤ 0.15` 在四份模型文档中一致 | 通过 |
| 跨问结果一致性 | 文档头条数字与结果文件一致 | `docs/overview.md` 第 5 节对照表；问题 1、2 结果在问题 3、4 实现后零变化（常数半径回归） | 通过 |
