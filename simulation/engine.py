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
                     "expected_score": 期望得分}}
    """
    start, end = bid_range
    num_steps = int(round((end - start) / bid_step)) + 1
    bid_values = [round(start + i * bid_step, 6) for i in range(num_steps)]

    results: dict[float, dict[str, float]] = {}

    for bid_self in bid_values:
        win_count = 0
        tolerance_count = 0
        total_score = 0.0

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

            total_score += my_score

        results[bid_self] = {
            "win_prob": win_count / num_simulations * 100,
            "tolerance_prob": tolerance_count / num_simulations * 100,
            "expected_score": total_score / num_simulations,
        }

    return results
