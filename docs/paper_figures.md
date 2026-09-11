# 论文图目录

| 图号 | 文件前缀 | 中文图注 | 数据来源 | 状态 |
| --- | --- | --- | --- | --- |
| 图 1 | `fig1_q1_temperature_profiles` | 预热阶段药材径向温度分布 | `result1_solution.json` | 已生成 |
| 图 2 | `fig2_q1_moisture_profiles` | 预热阶段药材径向水分浓度分布 | 同上 | 已生成 |
| 图 3 | `fig3_q1_center_surface_temperature` | 圆心与表面温度随时间变化 | 同上 | 已生成 |
| 图 4 | `fig4_q1_center_surface_moisture` | 圆心与表面水分浓度随时间变化 | 同上 | 已生成 |
| 图 5 | `fig5_q1_summary_2x2` | 问题1温度与水分浓度演化汇总 | 同上 | 已生成 |
| 图 6 | `fig1_q2_temperature_profiles` | 问题2径向温度分布 | `result2_solution.json` | 已生成 |
| 图 7 | `fig2_q2_moisture_profiles` | 问题2径向水分浓度分布 | 同上 | 已生成 |
| 图 8 | `fig3_q2_center_surface_temperature` | 问题2圆心与表面温度 | 同上 | 已生成 |
| 图 9 | `fig4_q2_center_surface_moisture` | 问题2圆心与表面水分浓度 | 同上 | 已生成 |
| 图 10 | `fig5_q2_summary_2x2` | 问题2演化汇总 | 同上 | 已生成 |

每张图同时输出 `.png`、`.pdf` 和 `.svg`，统一放在 `outputs/figures/`。所有图必须标注坐标、单位、图例、时间基准、数据来源和模型来源。

## 对比图计划

| 编号 | 对比内容 | 放置位置 | 前置条件 | 状态 |
| --- | --- | --- | --- | --- |
| C-01 | 隐式有限体积对显式有限差分 | 验证或附录 | EXP-001 扩展、独立复算 | 待开始 |
| C-02 | 常数物性对附录 3 变物性 | 正文 | 问题 2 基准完成 | 待开始 |
| C-03 | 长期边界保持与扰动 | 正文 | EXP-002 | 待开始 |
| C-04 | 是否考虑收缩、半径插值方式 | 正文 | EXP-003 | 待开始 |
