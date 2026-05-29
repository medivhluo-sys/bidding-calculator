import numpy as np
import pytest
from models.distribution import create_distribution, UniformDist, TriangularDist, \
    NormalDist, PERTDist


class TestCreateDistribution:
    """分布工厂函数测试"""

    def test_create_uniform(self):
        dist = create_distribution("uniform", low=10, high=20)
        assert isinstance(dist, UniformDist)

    def test_create_triangular(self):
        dist = create_distribution("triangular", low=10, mode=15, high=20)
        assert isinstance(dist, TriangularDist)

    def test_create_normal(self):
        dist = create_distribution("normal", mu=15, sigma=3)
        assert isinstance(dist, NormalDist)

    def test_create_pert(self):
        dist = create_distribution("pert", low=10, mode=15, high=20)
        assert isinstance(dist, PERTDist)

    def test_create_unknown_distribution(self):
        with pytest.raises(ValueError, match="未知分布"):
            create_distribution("unknown", low=1, high=2)


class TestUniformDist:
    """均匀分布测试"""

    def test_sample_within_bounds(self):
        dist = UniformDist(low=10, high=20)
        np.random.seed(42)
        samples = [dist.sample() for _ in range(1000)]
        assert all(10 <= s <= 20 for s in samples)

    def test_repr(self):
        dist = UniformDist(low=10, high=20)
        assert "Uniform" in repr(dist)
        assert "10" in repr(dist)
        assert "20" in repr(dist)


class TestTriangularDist:
    """三角分布测试"""

    def test_sample_within_bounds(self):
        dist = TriangularDist(low=10, mode=15, high=20)
        np.random.seed(42)
        samples = [dist.sample() for _ in range(1000)]
        assert all(10 <= s <= 20 for s in samples)

    def test_mode_near_center_of_mass(self):
        """三角分布的众数应该在 mode 附近"""
        dist = TriangularDist(low=10, mode=18, high=20)
        np.random.seed(42)
        samples = [dist.sample() for _ in range(5000)]
        avg = np.mean(samples)
        assert avg > 15.8  # 偏向高端（理论均值 16.0，给抽样误差留余量）


class TestNormalDist:
    """正态分布测试"""

    def test_sample_around_mean(self):
        dist = NormalDist(mu=50, sigma=5)
        np.random.seed(42)
        samples = [dist.sample() for _ in range(5000)]
        avg = np.mean(samples)
        assert 49.5 < avg < 50.5

    def test_negative_clamped_to_zero(self):
        """正态分布可能产生负值，应被截断到 0"""
        dist = NormalDist(mu=2, sigma=10)
        np.random.seed(42)
        for _ in range(100):
            assert dist.sample() >= 0


class TestPERTDist:
    """PERT 分布测试"""

    def test_sample_within_bounds(self):
        dist = PERTDist(low=10, mode=15, high=20)
        np.random.seed(42)
        samples = [dist.sample() for _ in range(1000)]
        assert all(10 <= s <= 20 for s in samples)
