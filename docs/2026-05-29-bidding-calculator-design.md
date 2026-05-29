# 报价测算工具 — 设计文档

## 1. 项目概述

将现有报价测算脚本（蒙特卡洛模拟 + 均值基准价评分法）重构为基于 Streamlit 的本地 Web 应用，支持对称/非对称扣分、多种对手报价分布模型，并提供交互式图表分析。

**目标用户**：投标决策者，可分享给同事使用。

## 2. 技术选型

| 层次 | 选型 | 理由 |
|------|------|------|
| Web 框架 | Streamlit | 纯 Python、零前端、分享方便 |
| 图表 | Plotly | 交互式、支持折线/热力图、Steamlit 原生集成 |
| 数值计算 | NumPy | 蒙特卡洛采样、分布生成 |
| 项目结构 | 独立 Git 仓库 `~/Projects/bidding-calculator/` | 独立版本控制、可分享 |

## 3. 核心模型

### 3.1 评分公式（确定性）

```
基准价 = mean(所有报价) × 折算系数
偏离率 = |报价 - 基准价| / 基准价 × 100%
扣分 = 偏离率 × 扣分系数（上偏/下偏可不同）
得分 = max(满分 - 扣分, 最低分)
```

参数：
- `benchmark_coefficient`：折算系数，默认 1.0（纯均值）
- `max_score`：满分，默认 20
- `deduction_up`：上偏每 1% 扣分，默认 1.0
- `deduction_down`：下偏每 1% 扣分，默认 1.0
- `min_score`：保底分，默认 0

### 3.2 竞争对手报价分布（概率模型）

为每个竞争对手独立配置一种分布：

| 分布 | 参数 | 适用场景 |
|------|------|----------|
| 均匀 Uniform | min, max | 完全不了解对手 |
| 正态 Normal | μ, σ | 了解对手成本中枢 |
| 三角 Triangular | min, mode, max | **默认推荐**：能估最可能值及上下界 |
| PERT | min, mode, max | 类似三角但尾部更厚 |

### 3.3 蒙特卡洛模拟（外层引擎）

```
for 你的报价 bid_self in [min, max] step 步长:
    胜出次数 = 0
    for i in range(模拟次数):
        对手报价 = [dist.sample() for dist in 对手分布列表]
        所有报价 = [bid_self] + 对手报价
        得分列表 = 评分公式(所有报价)
        if 得分列表[0] == max(得分列表):
            胜出次数 += 1
    中标概率[bid_self] = 胜出次数 / 模拟次数
```

## 4. UI 布局

单页 Streamlit 应用，左侧参数 + 右侧结果：

### 左侧 Sidebar：参数配置

```
📋 基准价设置
  [计算方法: 均值法 | 均值×系数]
  [折算系数: 1.0_________] （仅"均值×系数"时显示）

📋 扣分规则
  [满分: 20______]
  [上偏扣分: 1.0___ 分/1%]
  [下偏扣分: 1.0___ 分/1%]
  [最低分: 0______]

📋 竞争对手
  [+ 添加对手]
  对手 1: [分布: Tri ▾] [min:30] [mode:35] [max:42]
  对手 2: [分布: Tri ▾] [min:28] [mode:33] [max:40]
  对手 3: [分布: Tri ▾] [min:35] [mode:38] [max:42]

📋 你的报价
  [扫描范围: 30___ 到 42___]
  [步长: 0.5___]

📋 模拟设置
  [模拟次数: 10,000___]
  [▶ 开始测算]
```

### 右侧主区域：分析结果

```
[中标概率] [期望得分] [风险热力]  ← Tab 切换

┌──────────────────────────────────┐
│  📈 中标概率 vs 你的报价          │
│  折线图，X=报价 Y=概率%           │
│  标注最佳区间                     │
└──────────────────────────────────┘

💡 建议：报价区间 36.5-38.0，中标概率 > 85%
```

## 5. 项目文件结构

```
bidding-calculator/
├── app.py                  # Streamlit 入口
├── models/
│   ├── __init__.py
│   ├── scoring.py          # 评分公式
│   └── distribution.py     # 分布工厂（Uniform/Normal/Triangular/PERT）
├── simulation/
│   ├── __init__.py
│   └── engine.py           # 蒙特卡洛模拟引擎
├── ui/
│   ├── __init__.py
│   ├── sidebar.py          # 左侧参数面板
│   └── charts.py           # 图表渲染
├── requirements.txt        # streamlit, numpy, plotly
├── README.md               # 使用说明
└── .gitignore
```

## 6. 分享方式

- **本地运行**：`pip install -r requirements.txt && streamlit run app.py`
- **内部分享**：同事 clone 后同上命令
- **Streamlit Cloud**（可选）：推送到 GitHub 后在 Streamlit Cloud 一键部署，生成公网链接

## 7. 不做的事（YAGNI）

- 不导出 PDF/Excel 报告
- 不分位数分析 / 敏感性分析（后续可加）
- 不支持「低价基准法」
- 不做用户认证/多用户

## 8. 与原脚本的对应关系

| 原脚本 | 新工具 |
|--------|--------|
| `get_bidding_score()` | `models/scoring.py` |
| `random.randint()` 硬编码对手 | `models/distribution.py` 可配置分布 |
| 硬编码 bid0 范围 | UI 参数输入 |
| `print()` 文本输出 | Plotly 图表 |
| `safe_count / 10000` | `simulation/engine.py` 可配置模拟次数 |
