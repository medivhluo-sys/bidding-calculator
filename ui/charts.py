"""图表渲染 — 基于 Plotly 生成交互式图表。"""

import plotly.graph_objects as go


def plot_tolerance_probability(
    results: dict[float, dict[str, float]],
    tolerance: float,
) -> go.Figure:
    """容忍分差概率曲线图。

    Args:
        results: 模拟引擎返回的结果字典
        tolerance: 容忍分差

    Returns:
        Plotly Figure 对象
    """
    bids = list(results.keys())
    probs = [results[b]["tolerance_prob"] for b in bids]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=bids,
            y=probs,
            mode="lines+markers",
            name="容忍概率",
            line=dict(color="#00338D", width=2),
            marker=dict(size=6),
            hovertemplate="报价: %{x}<br>概率: %{y:.1f}%<extra></extra>",
        )
    )

    # 四条置信线
    for level, color in [
        (99, "#00695C"),
        (95, "#2E7D32"),
        (90, "#FF9800"),
        (80, "#9E9E9E"),
    ]:
        fig.add_hline(
            y=level,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{level}%",
        )

    # 标注最佳报价
    best_idx = max(range(len(probs)), key=lambda i: probs[i])
    best_bid = bids[best_idx]
    best_prob = probs[best_idx]
    fig.add_annotation(
        x=best_bid,
        y=best_prob,
        text=f"最佳: {best_bid}",
        showarrow=True,
        arrowhead=1,
        ax=40,
        ay=-40,
    )

    fig.update_layout(
        title=f"分差 ≤ {tolerance} 分的概率 vs 报价",
        xaxis_title="你的报价",
        yaxis_title="概率 (%)",
        yaxis_range=[0, 105],
        hovermode="x unified",
    )
    return fig


# 对手分差图的颜色调色板
_GAP_COLORS = [
    "#E53935", "#1E88E5", "#43A047", "#FB8C00",
    "#8E24AA", "#00ACC1", "#FFB300", "#5E35B1",
]


def plot_competitor_gaps(
    results: dict[float, dict[str, float]],
    competitor_labels: list[str],
) -> go.Figure:
    """与各对手的期望分差曲线。

    正值 = 我得分高于该对手，负值 = 我低于该对手。

    Args:
        results: 模拟引擎返回的结果字典
        competitor_labels: 对手标签列表（如 ["对手 1", "对手 2"]）

    Returns:
        Plotly Figure 对象
    """
    bids = list(results.keys())
    n_competitors = len(results[bids[0]]["competitor_gaps"])

    fig = go.Figure()

    for j in range(n_competitors):
        gaps = [results[b]["competitor_gaps"][j]["avg_gap"] for b in bids]
        label = competitor_labels[j] if j < len(competitor_labels) else f"对手 {j + 1}"
        color = _GAP_COLORS[j % len(_GAP_COLORS)]

        fig.add_trace(
            go.Scatter(
                x=bids,
                y=gaps,
                mode="lines+markers",
                name=label,
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=f"{label}<br>报价: %{{x}}<br>期望分差: %{{y:.2f}}<extra></extra>",
            )
        )

    # 零分差参考线
    fig.add_hline(y=0, line_dash="solid", line_color="#333", annotation_text="持平线")

    fig.update_layout(
        title="与各对手的期望分差",
        xaxis_title="你的报价",
        yaxis_title="期望分差（我 − 对手）",
        hovermode="x unified",
    )
    return fig


def get_best_recommendation(
    results: dict[float, dict[str, float]],
    tolerance: float,
    threshold: float = 95.0,
) -> str:
    """根据容忍分差概率生成最佳报价建议。

    Args:
        results: 模拟引擎返回的结果字典
        tolerance: 容忍分差
        threshold: 置信阈值（默认 95%）

    Returns:
        建议文本（Markdown 格式）
    """
    high_confidence = [
        (bid, results[bid]["tolerance_prob"])
        for bid in results
        if results[bid]["tolerance_prob"] >= threshold
    ]

    if high_confidence:
        best = max(high_confidence, key=lambda x: x[1])
        bids_in_range = sorted([b for b, p in high_confidence])
        return (
            f"**建议报价区间**：{min(bids_in_range):.1f} ~ {max(bids_in_range):.1f}，"
            f"分差 ≤ {tolerance} 分的概率 ≥ {threshold:.0f}%\n\n"
            f"最佳报价点：**{best[0]:.1f}**，概率 **{best[1]:.1f}%**"
        )
    else:
        best_bid = max(results, key=lambda b: results[b]["tolerance_prob"])
        best_prob = results[best_bid]["tolerance_prob"]
        return (
            f"⚠️ 无报价达到 {threshold:.0f}% 置信度（分差 ≤ {tolerance} 分）。\n\n"
            f"最佳可行报价：**{best_bid:.1f}**，概率 **{best_prob:.1f}%**"
        )
