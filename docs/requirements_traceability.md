# 题目要求追溯表

- 版本日期：2026-09-11
- 依据：`A题.pdf`

| 题目 | 要求 | 输入 | 输出 | 当前证据 | 状态 |
| --- | --- | --- | --- | --- | --- |
| 问题 1 | 建立预热阶段温度与水分浓度模型 | 附件 1、附录 2、初始条件 | 表 1、表 2、`result1.xlsx` | `docs/problem_1_model.md`、`outputs/result1.xlsx` | 已实现，用户已确认 |
| 问题 2 | 建立全过程模型，统一采用附录 3 | 附件 1、附录 3、初始条件 | 表 3、表 4、`result2.xlsx` | `docs/problem_2_model.md`、`outputs/result2.xlsx` | 已实现，用户已确认 |
| 问题 3 | 确定各处水分浓度低于 0.15 kg/kg 的烘干时间 | 附件 1、附录 3 | 表 5、`result3.xlsx` | 模型文档编写中（`docs/problem_3_model.md`） | 进行中 |
| 问题 4 | 根据附件 2 考虑尺寸变化并确定烘干时长 | 附件 1、附件 2、附录 4 | 表 6、`result4.xlsx` | 尚未建立 | 待开始 |
| 全局 | 论文按竞赛格式规范排版 | 官方格式规范文件 | 论文 | 文件尚未提供 | 阻塞 |

## 公式与参数来源

| 内容 | 来源 | 记录位置 |
| --- | --- | --- |
| 几何尺寸、初始温度、初始含水率 | 题目正文 | `docs/problem_1_model.md` |
| 附件 1 温湿度、附件 2 半径 | 附件原文件 | `docs/data_dictionary.md` |
| 问题 1 物性参数 | 附录 2 | `docs/problem_1_model.md` |
| 问题 2/3 经验公式 | 附录 3 | `docs/problem_2_model.md` |
| 问题 4 经验公式 | 附录 4 | 待问题 4 模型文档 |
| 一维径向、无潜热、线性插值 | 新增假设 | `docs/problem_1_model.md`、`docs/data_processing.md` |

## 输出网格追溯

| 文件 | 时间范围与间隔 | 距离范围与间隔 | sheet |
| --- | --- | --- | --- |
| `result1.xlsx` | 0～1800 s，1 s | 0～2 cm，0.1 cm | 温度、水分浓度 |
| `result2.xlsx` | 0～10800 s，1 s | 0～2 cm，0.1 cm | 温度、水分浓度 |
| `result3.xlsx` | 0～结束，60 s | 0～2 cm，0.1 cm | Sheet1 |
| `result4.xlsx` | 0～结束，60 s | 0～表面，0.1 cm | Sheet1 |

## 单位约定追溯

| 量 | 题目/附件 | 计算内核 | 输出 | 证据 |
| --- | --- | --- | --- | --- |
| 半径 | cm，首次为 2 cm | m，首次为 0.02 m | cm | `src/config.py`、`src/units.py` |
| 到中心距离 | cm，0～2 cm | m，0～0.02 m | cm | `src/export_xlsx.py`、结果模板 |
| 温度 | °C | K | °C | `src/material.py`、附件 1 |
| 时间 | s 或 h | s | s 或 h | `src/config.py`、结果模板 |
| 水分浓度 | kg/kg | kg/kg | kg/kg | 题目、附录 2～4 |

## 模型选择依据追溯

| 使用模型 | 推导依据 | 量化依据 | 证据 |
| --- | --- | --- | --- |
| 径向一维传热—扩散模型 | 能量守恒、Fourier 定律、质量守恒、Fick 定律、轴对称 | `L/R=12.5`，热渗透深度约 1.74 cm，水分渗透深度约 0.30 cm | `docs/problem_1_model.md`、`analysis/model_metrics.py` |
| 非稳态而非稳态 | 预热阶段只有 30 min，温度尚未达到平衡 | `Fo=0.76` | `docs/problem_1_model.md` |
| 非集总模型 | 内部径向温度和水分布不均匀 | `Bi=1.39` | `docs/problem_1_model.md` |
| 采用 `D(C)` | 附录 2 直接给出浓度依赖扩散系数 | `D(2.55)=4.94e-9 m2/s` | `src/material.py` |
| 采用 Robin 边界 | 题目给出 `h` 和 `hm` | `Bi=1.39`，传质 Biot 数约 3.24 | `docs/problem_1_model.md` |
