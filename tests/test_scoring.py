import pytest
from models.scoring import calculate_scores


class TestCalculateScores:
    """评分公式单元测试"""

    def test_basic_scoring_symmetric(self):
        """对称扣分：四家报价，均值基准价法"""
        bids = [100, 100, 100, 100]
        scores = calculate_scores(
            bids,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        # 全部等于均值，无人扣分
        assert scores == pytest.approx([20.0, 20.0, 20.0, 20.0])

    def test_above_benchmark_penalty(self):
        """上偏扣分：报价高于基准价"""
        bids = [110, 100, 100, 110]  # mean=105
        scores = calculate_scores(
            bids,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        # bid0=110, bid1=100, bid2=100, bid3=110
        # 偏离率 = 5/105*100 = 4.76%, 扣 4.76, 得 15.24
        assert scores[0] == pytest.approx(15.238, abs=0.01)
        assert scores[1] == pytest.approx(15.238, abs=0.01)

    def test_asymmetric_deduction(self):
        """非对称扣分：上偏扣分重，下偏扣分轻"""
        bids = [110, 90, 100, 100]  # mean=100
        scores = calculate_scores(
            bids,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=2.0,    # 上偏 1% 扣 2 分
            deduction_down=0.5,  # 下偏 1% 扣 0.5 分
            min_score=0,
        )
        # bid0=110: 偏离率 10%, 上偏扣 10*2 = 20, 得 0
        # bid1=90:  偏离率 10%, 下偏扣 10*0.5 = 5, 得 15
        assert scores[0] == pytest.approx(0.0, abs=0.01)
        assert scores[1] == pytest.approx(15.0, abs=0.01)

    def test_min_score_floor(self):
        """最低分保底：得分不低于 min_score"""
        bids = [200, 100, 100, 100]  # mean=125
        scores = calculate_scores(
            bids,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=10,
        )
        # bid0=200: 偏离率 = 75/125*100 = 60%, 扣 60, 得 -40 → 保底 10
        assert scores[0] == 10.0

    def test_benchmark_coefficient(self):
        """折算系数：基准价 = 均值 × 系数"""
        bids = [100, 100, 100, 100]  # mean=100
        scores = calculate_scores(
            bids,
            benchmark_coefficient=0.95,  # 基准价 = 95
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        # 偏离率 = |100-95|/95 * 100 = 5.26%, 扣 5.26, 得 14.74
        assert scores[0] == pytest.approx(14.737, abs=0.01)

    def test_zero_bids(self):
        """空列表边界：空报价返回空列表"""
        scores = calculate_scores([], benchmark_coefficient=1.0, max_score=20,
                                  deduction_up=1.0, deduction_down=1.0, min_score=0)
        assert scores == []

    def test_zero_benchmark_all_zero_bids(self):
        """零基准价：所有报价为 0 时，全员得满分不除零"""
        bids = [0.0, 0.0, 0.0]
        scores = calculate_scores(
            bids,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        assert scores == [20.0, 20.0, 20.0]

    def test_zero_benchmark_zero_coefficient(self):
        """零基准价：折算系数为 0 导致基准价为 0，全员得满分不除零"""
        bids = [100, 110, 90]
        scores = calculate_scores(
            bids,
            benchmark_coefficient=0.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        assert scores == [20.0, 20.0, 20.0]

    def test_bid_equals_benchmark_explicit(self):
        """报价恰好等于基准价时，偏离率为 0，得满分"""
        bids = [100, 100, 100, 100]
        scores = calculate_scores(
            bids,
            benchmark_coefficient=1.0,
            max_score=20,
            deduction_up=1.0,
            deduction_down=1.0,
            min_score=0,
        )
        assert scores == pytest.approx([20.0, 20.0, 20.0, 20.0])
