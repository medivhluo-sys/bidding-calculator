"""蒙特卡洛模拟引擎。

对每个候选报价，根据竞争对手分布重复采样 N 次，
统计严格中标概率、容忍分差概率和期望得分。
"""

import numpy as np
from models.scoring import calculate_scores
from models.distribution import BaseDistribution


def run_simulation(
    bid_range: tuple[float, float],
    bid_step: float,
    competitor_dists: list[BaseDistribution],
    num_simulations: int = 10000,
    *,
    tolerance: float = 0.0,
    benchmark_coefficient: float = 1.0,
    max_score: float = 20.0,
    deduction_up: float = 1.0,
    deduction_down: float = 1.0,
    min_score: float = 0.0,
) -> dict[float, dict[str, float]]:
    """运行蒙特卡洛模拟。

    Args:
        bid_range: 你的报价扫描范围 (min, max)
        bid_step: 扫描步长
        competitor_dists: 各竞争对手的报价分布列表
        num_simulations: 每个报价点的模拟次数
        tolerance: 容忍分差，得分 ≥ 最高分 - tolerance 即视为安全
        benchmark_coefficient: 基准价折算系数
        max_score: 满分
        deduction_up: 上偏每 1% 扣分
        deduction_down: 下偏每 1% 扣分
        min_score: 最低保底分

    Returns:
        {bid_value: {"win_prob": 严格中标概率%, "tolerance_prob": 容忍分差概率%,
                     "expected_score": 期望得分,
                     "competitor_gaps": [{"avg_gap": 平均分差, "beat_rate": 胜率%}, ...]}}
    """
    start, end = bid_range
    num_steps = int(round((end - start) / bid_step)) + 1
    bid_values = [round(start + i * bid_step, 6) for i in range(num_steps)]

    results: dict[float, dict[str, float]] = {}

    # 分差分布的分桶边界和标签
    GAP_BINS = [-1e9, -3, -1, 0, 1, 3, 1e9]
    GAP_LABELS = [
        "落后 >3分", "落后 1~3分", "落后 <1分",
        "领先 <1分", "领先 1~3分", "领先 >3分",
    ]

    for bid_self in bid_values:
        win_count = 0
        tolerance_count = 0
        total_score = 0.0
        n_competitors = len(competitor_dists)
        n_bins = len(GAP_BINS) - 1
        # gap_hist[j][k] = 对手 j 落在第 k 个桶的次数
        gap_hist = [[0] * n_bins for _ in range(n_competitors)]

        for _ in range(num_simulations):
            competitor_bids = [d.sample() for d in competitor_dists]
            all_bids = [bid_self] + competitor_bids

            scores = calculate_scores(
                all_bids,
                benchmark_coefficient=benchmark_coefficient,
                max_score=max_score,
                deduction_up=deduction_up,
                deduction_down=deduction_down,
                min_score=min_score,
            )

            my_score = scores[0]
            best_score = max(scores)

            # 并列时随机择一胜出；单独胜出时 tied_indices == [0] 恒为 True
            tied_indices = [i for i, s in enumerate(scores) if s == best_score]
            if np.random.choice(tied_indices) == 0:
                win_count += 1

            # 容忍分差：得分不低于最高分 - tolerance
            if my_score >= best_score - tolerance:
                tolerance_count += 1

            # 与每个对手的分差——落入对应分桶
            for j in range(n_competitors):
                gap = my_score - scores[j + 1]
                # 找到 gap 落入的桶
                for k in range(n_bins):
                    if GAP_BINS[k] <= gap < GAP_BINS[k + 1]:
                        gap_hist[j][k] += 1
                        break

            total_score += my_score

        n = num_simulations
        results[bid_self] = {
            "win_prob": win_count / n * 100,
            "tolerance_prob": tolerance_count / n * 100,
            "expected_score": total_score / n,
            "gap_bins": GAP_LABELS,
            "competitor_gaps": [
                {
                    "histogram": [gap_hist[j][k] / n * 100 for k in range(n_bins)],
                }
                for j in range(n_competitors)
            ],
        }

    return results
