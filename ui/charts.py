"""图表渲染 — 基于 Plotly 生成交互式图表。"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_win_probability(results: dict[float, dict[str, float]]) -> go.Figure:
    """中标概率曲线图。

    Args:
        results: 模拟引擎返回的结果字典 {bid: {"win_prob": %, "expected_score": score}}

    Returns:
        Plotly Figure 对象
    """
    bids = list(results.keys())
    win_probs = [results[b]["win_prob"] for b in bids]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=bids,
            y=win_probs,
            mode="lines+markers",
            name="中标概率",
            line=dict(color="#00338D", width=2),
            marker=dict(size=6),
            hovertemplate="报价: %{x}<br>中标概率: %{y:.1f}%<extra></extra>",
        )
    )

    # 标注最佳报价
    best_idx = max(range(len(win_probs)), key=lambda i: win_probs[i])
    best_bid = bids[best_idx]
    best_prob = win_probs[best_idx]
    fig.add_annotation(
        x=best_bid,
        y=best_prob,
        text=f"最佳: {best_bid} ({best_prob:.1f}%)",
        showarrow=True,
        arrowhead=1,
        ax=40,
        ay=-40,
    )

    fig.update_layout(
        title="中标概率 vs 报价",
        xaxis_title="你的报价",
        yaxis_title="中标概率 (%)",
        yaxis_range=[0, 105],
        hovermode="x unified",
    )
    return fig


def plot_expected_score(results: dict[float, dict[str, float]],
                        max_score: float = 20.0) -> go.Figure:
    """期望得分曲线图。

    Args:
        results: 模拟引擎返回的结果字典
        max_score: 满分分值，用于设定 Y 轴上限

    Returns:
        Plotly Figure 对象
    """
    bids = list(results.keys())
    scores = [results[b]["expected_score"] for b in bids]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=bids,
            y=scores,
            mode="lines+markers",
            name="期望得分",
            line=dict(color="#2E7D32", width=2),
            marker=dict(size=6),
            hovertemplate="报价: %{x}<br>期望得分: %{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="期望得分 vs 报价",
        xaxis_title="你的报价",
        yaxis_title="期望得分",
        yaxis_range=[0, max_score * 1.05],
        hovermode="x unified",
    )
    return fig


def plot_risk_heatmap(
    results: dict[float, dict[str, float]],
) -> go.Figure:
    """风险热力图：你的报价 vs 中标概率，用颜色深度表示风险水平。

    Args:
        results: 模拟引擎返回的结果字典
        competitor_dists_info: 对手分布描述列表
        bid_step: 扫描步长
        num_simulations: 模拟次数

    Returns:
        Plotly Figure 对象
    """
    bids = list(results.keys())
    win_probs = [results[b]["win_prob"] for b in bids]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=bids,
            y=win_probs,
            marker=dict(
                color=win_probs,
                colorscale=[
                    [0, "#EF5350"],      # 红色 = 低概率
                    [0.5, "#FFC107"],    # 黄色 = 中等
                    [1, "#4CAF50"],      # 绿色 = 高概率
                ],
                cmin=0,
                cmax=100,
                colorbar=dict(title="中标概率%"),
            ),
            hovertemplate="报价: %{x}<br>中标概率: %{y:.1f}%<extra></extra>",
        )
    )

    # 风险分区线
    fig.add_hline(y=80, line_dash="dash", line_color="green",
                  annotation_text="高安全区 (>80%)")
    fig.add_hline(y=50, line_dash="dash", line_color="orange",
                  annotation_text="竞争区 (50-80%)")

    fig.update_layout(
        title="风险热力：报价 vs 中标概率",
        xaxis_title="你的报价",
        yaxis_title="中标概率 (%)",
        yaxis_range=[0, 105],
    )
    return fig


def get_best_recommendation(
    results: dict[float, dict[str, float]],
    threshold: float = 80.0,
) -> str:
    """根据模拟结果生成最佳报价建议文本。

    Args:
        results: 模拟引擎返回的结果字典
        threshold: 高安全区阈值（默认 80%）

    Returns:
        建议文本（Markdown 格式）
    """
    high_confidence = [
        (bid, results[bid]["win_prob"])
        for bid in results
        if results[bid]["win_prob"] >= threshold
    ]

    if high_confidence:
        best = max(high_confidence, key=lambda x: x[1])
        bids_in_range = sorted([b for b, p in high_confidence])
        return (
            f"**建议报价区间**：{min(bids_in_range):.1f} ~ {max(bids_in_range):.1f}，"
            f"中标概率均 ≥ {threshold:.0f}%\n\n"
            f"最佳报价点：**{best[0]:.1f}**，中标概率 **{best[1]:.1f}%**"
        )
    else:
        best_bid = max(results, key=lambda b: results[b]["win_prob"])
        best_prob = results[best_bid]["win_prob"]
        return (
            f"⚠️ 无报价达到 {threshold:.0f}% 安全阈值。\n\n"
            f"最佳可行报价：**{best_bid:.1f}**，中标概率 **{best_prob:.1f}%**"
        )
