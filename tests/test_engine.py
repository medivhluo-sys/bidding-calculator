import numpy as np
import pytest
from models.distribution import UniformDist
from simulation.engine import run_simulation


class TestRunSimulation:
    """蒙特卡洛模拟引擎测试"""

    def test_deterministic_with_seed(self):
        """固定随机种子时应产出可复现结果"""
        np.random.seed(42)
        dists = [UniformDist(10, 20), UniformDist(10, 20), UniformDist(10, 20)]
        result1 = run_simulation(
            bid_range=(15, 16),
            bid_step=1.0,
            competitor_dists=dists,
            num_simulations=500,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )

        np.random.seed(42)
        result2 = run_simulation(
            bid_range=(15, 16),
            bid_step=1.0,
            competitor_dists=dists,
            num_simulations=500,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )

        for k in result1:
            assert result1[k]["win_prob"] == pytest.approx(result2[k]["win_prob"])
            assert result1[k]["expected_score"] == pytest.approx(result2[k]["expected_score"])

    def test_win_probability_range(self):
        """中标概率应在 0-100% 之间"""
        dists = [UniformDist(30, 42)]
        result = run_simulation(
            bid_range=(30, 40),
            bid_step=2.0,
            competitor_dists=dists,
            num_simulations=1000,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        for bid_val, data in result.items():
            assert 0.0 <= data["win_prob"] <= 100.0
            assert data["expected_score"] >= 0

    def test_identical_bids_all_win(self):
        """所有报价相同时，每人中标概率接近 1/N"""
        dists = [UniformDist(50, 50), UniformDist(50, 50)]
        result = run_simulation(
            bid_range=(50, 50),
            bid_step=1.0,
            competitor_dists=dists,
            num_simulations=2000,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        assert 25.0 < result[50.0]["win_prob"] < 45.0

    def test_single_bid_always_wins(self):
        """只有一个投标人时，中标概率 100%"""
        result = run_simulation(
            bid_range=(30, 30),
            bid_step=1.0,
            competitor_dists=[],
            num_simulations=100,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        assert result[30.0]["win_prob"] == 100.0
        assert result[30.0]["expected_score"] == 20.0

    def test_bid_range_steps(self):
        """验证 bid_range 和 bid_step 生成的报价点数量"""
        dists = [UniformDist(30, 42)]
        result = run_simulation(
            bid_range=(30, 40),
            bid_step=5.0,
            competitor_dists=dists,
            num_simulations=100,
        )
        assert len(result) == 3
        assert 30.0 in result
        assert 35.0 in result
        assert 40.0 in result

    def test_tolerance_zero_gte_win_prob(self):
        """tolerance=0 时，tolerance_prob >= win_prob（因为 win_prob 有随机平局拆分）"""
        dists = [UniformDist(30, 42)]
        np.random.seed(42)
        result = run_simulation(
            bid_range=(30, 40),
            bid_step=5.0,
            competitor_dists=dists,
            num_simulations=500,
            tolerance=0.0,
        )
        for data in result.values():
            # tolerance 计数所有达到最高分的（含平局），win_prob 随机拆分平局
            assert data["tolerance_prob"] >= data["win_prob"]

    def test_tolerance_larger_gives_higher_prob(self):
        """tolerance 增大时 tolerance_prob 应 >= 小 tolerance 的结果"""
        dists = [UniformDist(30, 42)]
        np.random.seed(42)
        result_small = run_simulation(
            bid_range=(35, 35),
            bid_step=1.0,
            competitor_dists=dists,
            num_simulations=500,
            tolerance=1.0,
        )
        np.random.seed(42)
        result_large = run_simulation(
            bid_range=(35, 35),
            bid_step=1.0,
            competitor_dists=dists,
            num_simulations=500,
            tolerance=3.0,
        )
        assert result_large[35.0]["tolerance_prob"] >= result_small[35.0]["tolerance_prob"]

    def test_tolerance_prob_is_percentage(self):
        """tolerance_prob 应在 0-100% 之间"""
        dists = [UniformDist(30, 42)]
        result = run_simulation(
            bid_range=(30, 40),
            bid_step=5.0,
            competitor_dists=dists,
            num_simulations=500,
            tolerance=3.0,
        )
        for data in result.values():
            assert 0.0 <= data["tolerance_prob"] <= 100.0

    def test_competitor_gaps_structure(self):
        """验证 competitor_gaps 字段存在且数据合理"""
        dists = [UniformDist(30, 42), UniformDist(35, 42)]
        result = run_simulation(
            bid_range=(35, 35),
            bid_step=1.0,
            competitor_dists=dists,
            num_simulations=500,
        )
        gaps = result[35.0]["competitor_gaps"]
        bins = result[35.0]["gap_bins"]
        assert len(gaps) == 2  # 两个对手
        assert len(bins) == 6  # 6 个分桶
        for g in gaps:
            hist = g["histogram"]
            assert len(hist) == 6
            # 所有桶的概率之和约等于 100%
            assert 95.0 <= sum(hist) <= 105.0

    def test_competitor_gaps_zero_competitors(self):
        """无对手时 competitor_gaps 为空列表"""
        result = run_simulation(
            bid_range=(35, 35),
            bid_step=1.0,
            competitor_dists=[],
            num_simulations=100,
        )
        assert result[35.0]["competitor_gaps"] == []
