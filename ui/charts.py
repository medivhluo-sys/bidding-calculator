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


def plot_competitor_gap_bars(
    results: dict[float, dict[str, float]],
    bid_value: float,
    competitor_labels: list[str],
) -> go.Figure:
    """选定报价下，与各对手的期望分差 ±1σ 水平条形图。

    正值（绿色）= 我高于对手，负值（红色）= 对手高于我。
    条形长度 = 均值，误差线 = ±1σ。

    Args:
        results: 模拟引擎返回的结果字典
        bid_value: 选定的报价点
        competitor_labels: 对手标签列表
    """
    # 找到最接近的报价点
    available_bids = sorted(results.keys())
    closest_bid = min(available_bids, key=lambda b: abs(b - bid_value))
    data = results[closest_bid]["competitor_gaps"]

    n = len(data)
    fig = go.Figure()

    for j in range(n):
        g = data[j]
        label = competitor_labels[j] if j < len(competitor_labels) else f"对手 {j + 1}"
        avg = g["avg_gap"]
        std = g["std_gap"]
        color = "#43A047" if avg >= 0 else "#E53935"

        # 均值条
        fig.add_trace(
            go.Bar(
                y=[label],
                x=[avg],
                orientation="h",
                name=label,
                marker=dict(color=color, opacity=0.7),
                error_x=dict(
                    type="data",
                    array=[std],
                    visible=True,
                    color="#666",
                ),
                hovertemplate=(
                    f"{label}<br>"
                    f"期望分差: %{{x:.2f}} ± {std:.2f}<br>"
                    f"胜率: {g['beat_rate']:.1f}%<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # 零分差参考线
    fig.add_vline(x=0, line_dash="solid", line_color="#333")

    # 确保 X 轴对称 — 找到最大绝对值
    max_abs = max(abs(g["avg_gap"]) + g["std_gap"] for g in data) * 1.2
    fig.update_layout(
        title=f"报价 {closest_bid} 时与各对手的分差",
        xaxis_title="期望分差（我 − 对手）← 对手高 | 我高 →",
        yaxis=dict(autorange="reversed"),  # 对手1在上
        xaxis_range=[-max_abs, max_abs],
        height=150 + n * 40,
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
