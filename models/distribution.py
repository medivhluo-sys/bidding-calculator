"""竞争对手报价分布模型。

每种分布封装其参数和采样逻辑，对外暴露统一的 sample() 接口。
"""

import abc
import numpy as np


class BaseDistribution(abc.ABC):
    """分布抽象基类"""

    @abc.abstractmethod
    def sample(self) -> float:
        """从分布中抽取一个随机样本"""
        ...


class UniformDist(BaseDistribution):
    """均匀分布 U(min, max)"""

    def __init__(self, low: float, high: float):
        if low > high:
            raise ValueError(f"Uniform: low({low}) 不能大于 high({high})")
        self.low = low
        self.high = high

    def sample(self) -> float:
        return float(np.random.uniform(self.low, self.high))

    def __repr__(self) -> str:
        return f"Uniform(low={self.low}, high={self.high})"


class TriangularDist(BaseDistribution):
    """三角分布 Tri(min, mode, max)"""

    def __init__(self, low: float, mode: float, high: float):
        if not (low <= mode <= high):
            raise ValueError(
                f"Triangular: 需要 low({low}) <= mode({mode}) <= high({high})"
            )
        self.low = low
        self.mode = mode
        self.high = high

    def sample(self) -> float:
        return float(np.random.triangular(self.low, self.mode, self.high))

    def __repr__(self) -> str:
        return f"Triangular(low={self.low}, mode={self.mode}, high={self.high})"


class NormalDist(BaseDistribution):
    """正态分布 N(μ, σ)，负值截断为 0"""

    def __init__(self, mu: float, sigma: float):
        if sigma <= 0:
            raise ValueError(f"Normal: sigma({sigma}) 必须 > 0")
        self.mu = mu
        self.sigma = sigma

    def sample(self) -> float:
        return max(0.0, float(np.random.normal(self.mu, self.sigma)))

    def __repr__(self) -> str:
        return f"Normal(mu={self.mu}, sigma={self.sigma})"


class PERTDist(BaseDistribution):
    """PERT 分布 PERT(min, mode, max)

    基于 Beta 分布的 PERT 近似：α = 1 + 4*(mode-low)/(high-low),
    β = 1 + 4*(high-mode)/(high-low)，然后缩放到 [low, high]。
    """

    def __init__(self, low: float, mode: float, high: float):
        if not (low <= mode <= high):
            raise ValueError(
                f"PERT: 需要 low({low}) <= mode({mode}) <= high({high})"
            )
        self.low = low
        self.mode = mode
        self.high = high

    def sample(self) -> float:
        span = self.high - self.low
        if span == 0:
            return self.low
        alpha = 1.0 + 4.0 * (self.mode - self.low) / span
        beta = 1.0 + 4.0 * (self.high - self.mode) / span
        sample_01 = float(np.random.beta(alpha, beta))
        return self.low + sample_01 * span

    def __repr__(self) -> str:
        return f"PERT(low={self.low}, mode={self.mode}, high={self.high})"


_DISTRIBUTION_REGISTRY: dict[str, type[BaseDistribution]] = {
    "uniform": UniformDist,
    "triangular": TriangularDist,
    "normal": NormalDist,
    "pert": PERTDist,
}


def create_distribution(dist_type: str, **kwargs) -> BaseDistribution:
    """分布工厂函数。

    Args:
        dist_type: 分布类型名称 ("uniform" | "triangular" | "normal" | "pert")
        **kwargs: 传递给具体分布构造函数的参数
            - uniform: low, high
            - triangular: low, mode, high
            - normal: mu, sigma
            - pert: low, mode, high

    Returns:
        BaseDistribution 实例

    Raises:
        ValueError: 未知的分布类型
    """
    dist_type_lower = dist_type.lower()
    if dist_type_lower not in _DISTRIBUTION_REGISTRY:
        raise ValueError(
            f"未知分布类型: '{dist_type}'，"
            f"支持: {list(_DISTRIBUTION_REGISTRY.keys())}"
        )
    return _DISTRIBUTION_REGISTRY[dist_type_lower](**kwargs)
