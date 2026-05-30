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


def _rgba(hex_color: str, alpha: float) -> str:
    """将 #RRGGBB 十六进制颜色转为 rgba(r, g, b, alpha) 字符串。"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# 对手分差图的颜色调色板
_GAP_COLORS = [
    "#E53935", "#1E88E5", "#43A047", "#FB8C00",
    "#8E24AA", "#00ACC1", "#FFB300", "#5E35B1",
]


def plot_competitor_gaps(
    results: dict[float, dict[str, float]],
    competitor_labels: list[str],
    mode: str = "gap",
) -> go.Figure:
    """与各对手的对比曲线。

    mode="gap": 期望分差（正值 = 我高于对手，负值 = 对手高于我）
    mode="beat_rate": 胜率（我得分高于该对手的概率 %）

    Args:
        results: 模拟引擎返回的结果字典
        competitor_labels: 对手标签列表
        mode: "gap" 或 "beat_rate"
    """
    bids = list(results.keys())
    n_competitors = len(results[bids[0]]["competitor_gaps"])

    fig = go.Figure()

    for j in range(n_competitors):
        gaps = [results[b]["competitor_gaps"][j] for b in bids]
        avg_gaps = [g["avg_gap"] for g in gaps]
        std_gaps = [g["std_gap"] for g in gaps]

        if mode == "beat_rate":
            values = [g["beat_rate"] for g in gaps]
        else:
            values = avg_gaps

        label = competitor_labels[j] if j < len(competitor_labels) else f"对手 {j + 1}"
        color = _GAP_COLORS[j % len(_GAP_COLORS)]

        if mode == "beat_rate":
            hovertemplate = f"{label}<br>报价: %{{x}}<br>胜率: %{{y:.1f}}%<extra></extra>"
        else:
            hovertemplate = f"{label}<br>报价: %{{x}}<br>期望分差: %{{y:.2f}} ± %{{customdata:.2f}}<extra></extra>"

        fig.add_trace(
            go.Scatter(
                x=bids,
                y=values,
                mode="lines+markers",
                name=label,
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=hovertemplate,
                customdata=std_gaps,
            )
        )

        # 期望分差模式下添加 ±1σ 阴影带
        if mode != "beat_rate":
            upper = [a + s for a, s in zip(avg_gaps, std_gaps)]
            lower = [a - s for a, s in zip(avg_gaps, std_gaps)]
            fig.add_trace(
                go.Scatter(
                    x=bids + bids[::-1],
                    y=upper + lower[::-1],
                    fill="toself",
                    fillcolor=_rgba(color, 0.15),
                    line=dict(width=0),
                    name=f"{label} ±1σ",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    if mode == "beat_rate":
        # 50% 参考线
        fig.add_hline(y=50, line_dash="dash", line_color="#999", annotation_text="50%")
        fig.update_layout(
            title="对各对手的胜率",
            xaxis_title="你的报价",
            yaxis_title="胜率 (%)",
            yaxis_range=[0, 105],
            hovermode="x unified",
        )
    else:
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
