"""报价评分公式 — 均值基准价法。

所有计算均为确定性：给定报价列表和评分参数，返回对应的得分列表。
"""


def calculate_scores(
    bids: list[float],
    *,
    benchmark_coefficient: float = 1.0,
    max_score: float = 20.0,
    deduction_up: float = 1.0,
    deduction_down: float = 1.0,
    min_score: float = 0.0,
) -> list[float]:
    """基于均值基准价法计算各报价得分。

    Args:
        bids: 所有报价列表（含自己和对手）
        benchmark_coefficient: 均值折算系数，1.0 = 纯均值
        max_score: 价格分满分
        deduction_up: 上偏（高于基准价）每 1% 扣分
        deduction_down: 下偏（低于基准价）每 1% 扣分
        min_score: 最低保底分

    Returns:
        与 bids 等长的得分列表
    """
    if not bids:
        return []

    mean_price = sum(bids) / len(bids)
    benchmark = mean_price * benchmark_coefficient

    scores = []
    for bid in bids:
        deviation_pct = abs(bid - benchmark) / benchmark * 100

        if bid > benchmark:
            penalty = deviation_pct * deduction_up
        else:
            penalty = deviation_pct * deduction_down

        score = max_score - penalty
        score = max(score, min_score)
        scores.append(score)

    return scores
