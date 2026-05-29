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
