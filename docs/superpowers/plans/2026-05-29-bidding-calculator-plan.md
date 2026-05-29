# 报价测算工具 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 将报价测算脚本重构为 Streamlit 本地 Web 应用，支持多种对手分布模型、对称/非对称扣分，交互式图表展示中标概率、期望得分和风险热力图。

**Architecture:** 三层结构 — `models/`（评分公式 + 分布工厂）是纯计算层无 UI 依赖，`simulation/`（蒙特卡洛引擎）编排计算，`ui/`（参数面板 + 图表）负责 Streamlit 渲染，`app.py` 粘合三层。

**Tech Stack:** Python 3.12+, Streamlit, NumPy, Plotly, pytest

**端口:** 8002

---

### Task 0: 项目环境搭建

**Files:**
- Create: `requirements.txt`
- Create: `models/__init__.py`
- Create: `simulation/__init__.py`
- Create: `ui/__init__.py`
- Create: `CLAUDE.md`

- [ ] **Step 1: 创建 requirements.txt**

```txt
streamlit>=1.40
numpy>=2.0
plotly>=5.24
pytest>=8.0
```

- [ ] **Step 2: 创建 Python 包目录和空 `__init__.py`**

```bash
mkdir -p models simulation ui
touch models/__init__.py simulation/__init__.py ui/__init__.py
```

- [ ] **Step 3: 创建虚拟环境并安装依赖**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 4: 验证安装**

```bash
python -c "import streamlit; import numpy; import plotly; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: 创建项目 CLAUDE.md**

```markdown
# bidding-calculator — 报价测算工具

基于蒙特卡洛模拟的投标报价分析工具，支持均值基准价法、多种对手分布模型、交互式图表。

## 运行

```bash
source venv/bin/activate
streamlit run app.py --server.port 8002
```

## 架构

- `models/scoring.py` — 评分公式（确定性计算）
- `models/distribution.py` — 对手报价分布工厂
- `simulation/engine.py` — 蒙特卡洛模拟引擎
- `ui/sidebar.py` — Streamlit 侧边栏参数面板
- `ui/charts.py` — Plotly 图表渲染
- `app.py` — 应用入口

## 测试

```bash
pytest -v
```
```

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "chore: 项目环境搭建"
```

---

### Task 1: 评分公式模块

**Files:**
- Create: `tests/test_scoring.py`
- Create: `models/scoring.py`

- [ ] **Step 1: 写评分公式的测试**

```python
# tests/test_scoring.py
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
        # 均值 = 105, 基准价 = 105
        # bid0=110, 偏离率 = |110-105|/105 * 100 = 4.76%
        # 扣分 = 4.76 * 1.0 = 4.76, 得分 = 20 - 4.76 = 15.24
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -m pytest tests/test_scoring.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'models.scoring'`

- [ ] **Step 3: 实现评分公式**

```python
# models/scoring.py
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -m pytest tests/test_scoring.py -v
```
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add tests/test_scoring.py models/scoring.py
git commit -m "feat: 评分公式模块（均值基准价法，对称/非对称扣分）"
```

---

### Task 2: 分布工厂模块

**Files:**
- Create: `tests/test_distribution.py`
- Create: `models/distribution.py`

- [ ] **Step 1: 写分布模块的测试**

```python
# tests/test_distribution.py
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
        # 均值应偏向 mode（18）而非中点（15）
        avg = np.mean(samples)
        assert avg > 16.0  # 偏向高端


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
        # 多次采样，确保所有值 >= 0
        for _ in range(100):
            assert dist.sample() >= 0


class TestPERTDist:
    """PERT 分布测试"""

    def test_sample_within_bounds(self):
        dist = PERTDist(low=10, mode=15, high=20)
        np.random.seed(42)
        samples = [dist.sample() for _ in range(1000)]
        assert all(10 <= s <= 20 for s in samples)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -m pytest tests/test_distribution.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现分布工厂和分布类**

```python
# models/distribution.py
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
        # PERT 参数化：alpha = 1 + 4*(mode-low)/(high-low)
        alpha = 1.0 + 4.0 * (self.mode - self.low) / span
        beta = 1.0 + 4.0 * (self.high - self.mode) / span
        sample_01 = float(np.random.beta(alpha, beta))
        return self.low + sample_01 * span

    def __repr__(self) -> str:
        return f"PERT(low={self.low}, mode={self.mode}, high={self.high})"


# 分布注册表
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -m pytest tests/test_distribution.py -v
```
Expected: 10 passed

- [ ] **Step 5: 提交**

```bash
git add tests/test_distribution.py models/distribution.py
git commit -m "feat: 分布工厂模块（Uniform/Triangular/Normal/PERT）"
```

---

### Task 3: 蒙特卡洛模拟引擎

**Files:**
- Create: `tests/test_engine.py`
- Create: `simulation/engine.py`

- [ ] **Step 1: 写模拟引擎的测试**

```python
# tests/test_engine.py
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

        # 两次结果应完全一致
        for k in result1:
            assert result1[k]["win_prob"] == pytest.approx(result2[k]["win_prob"])
            assert result1[k]["expected_score"] == pytest.approx(result2[k]["expected_score"])

    def test_win_probability_range(self):
        """中标概率应在 0-100% 之间"""
        dists = [UniformDist(30, 42)]  # 1个对手
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
        # 三家都报 50，每人概率约 33%
        assert 25.0 < result[50.0]["win_prob"] < 45.0

    def test_single_bid_always_wins(self):
        """只有一个投标人时，中标概率 100%"""
        result = run_simulation(
            bid_range=(30, 30),
            bid_step=1.0,
            competitor_dists=[],  # 无对手
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
        # 30, 35, 40 → 3 个点
        assert len(result) == 3
        assert 30.0 in result
        assert 35.0 in result
        assert 40.0 in result
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -m pytest tests/test_engine.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现模拟引擎**

```python
# simulation/engine.py
"""蒙特卡洛模拟引擎。

对每个候选报价，根据竞争对手分布重复采样 N 次，
统计中标概率和期望得分。
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
        benchmark_coefficient: 基准价折算系数
        max_score: 满分
        deduction_up: 上偏每 1% 扣分
        deduction_down: 下偏每 1% 扣分
        min_score: 最低保底分

    Returns:
        {bid_value: {"win_prob": 中标概率%, "expected_score": 期望得分}}
    """
    # 生成报价扫描点
    start, end = bid_range
    num_steps = int(round((end - start) / bid_step)) + 1
    bid_values = [round(start + i * bid_step, 6) for i in range(num_steps)]

    results: dict[float, dict[str, float]] = {}

    for bid_self in bid_values:
        win_count = 0
        total_score = 0.0

        for _ in range(num_simulations):
            # 采对手报价
            competitor_bids = [d.sample() for d in competitor_dists]
            all_bids = [bid_self] + competitor_bids

            # 计算得分
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
            if my_score >= best_score:
                win_count += 1
            total_score += my_score

        results[bid_self] = {
            "win_prob": win_count / num_simulations * 100,
            "expected_score": total_score / num_simulations,
        }

    return results
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -m pytest tests/test_engine.py -v
```
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add tests/test_engine.py simulation/engine.py
git commit -m "feat: 蒙特卡洛模拟引擎"
```

---

### Task 4: 图表渲染模块

**Files:**
- Create: `ui/charts.py`

Streamlit 渲染层不强制 TDD（UI 行为通过手动验证），但确保函数签名清晰、可独立导入测试。

- [ ] **Step 1: 实现图表渲染函数**

```python
# ui/charts.py
"""图表渲染 — 基于 Plotly 生成交互式图表。"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_win_probability(results: dict[float, dict[str, float]]) -> go.Figure:
    """中标概率曲线图。

    Args:
        results: 模拟引擎返回的结果字典

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
    competitor_dists_info: list[dict],
    bid_step: float,
    num_simulations: int,
) -> go.Figure:
    """风险热力图：你的报价 × 对手策略空间下的中标概率。

    通过对每个报价点记录其得分分布，展示不同报价在不同对手
    情景下的风险水平。

    Args:
        results: 模拟引擎返回的结果字典
        competitor_dists_info: 对手分布描述列表 [{"label": "对手A", ...}, ...]
        bid_step: 扫描步长
        num_simulations: 模拟次数

    Returns:
        Plotly Figure 对象
    """
    bids = list(results.keys())
    win_probs = [results[b]["win_prob"] for b in bids]

    # 单维度热力：报价 vs 中标概率，用颜色深度表示
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

    # 添加风险分区线
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
        建议文本
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
        # 找回最高概率的报价
        best_bid = max(results, key=lambda b: results[b]["win_prob"])
        best_prob = results[best_bid]["win_prob"]
        return (
            f"⚠️ 无报价达到 {threshold:.0f}% 安全阈值。\n\n"
            f"最佳可行报价：**{best_bid:.1f}**，中标概率 **{best_prob:.1f}%**"
        )
```

- [ ] **Step 2: 验证 Plotly 图表可正常创建（不渲染）**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -c "
from ui.charts import plot_win_probability, plot_expected_score, plot_risk_heatmap, get_best_recommendation
results = {30.0: {'win_prob': 75.0, 'expected_score': 17.5}, 35.0: {'win_prob': 85.0, 'expected_score': 18.2}}
fig1 = plot_win_probability(results)
fig2 = plot_expected_score(results)
fig3 = plot_risk_heatmap(results, [], 5.0, 1000)
rec = get_best_recommendation(results)
print(f'Charts OK, recommendation: {rec[:50]}...')
"
```
Expected: `Charts OK, recommendation: ...`

- [ ] **Step 3: 提交**

```bash
git add ui/charts.py
git commit -m "feat: Plotly 图表渲染（中标概率/期望得分/风险热力）"
```

---

### Task 5: 侧边栏参数面板

**Files:**
- Create: `ui/sidebar.py`

- [ ] **Step 1: 实现侧边栏参数面板**

```python
# ui/sidebar.py
"""Streamlit 侧边栏 — 参数配置面板。"""

import streamlit as st
from models.distribution import create_distribution


def render_sidebar() -> dict:
    """渲染侧边栏参数面板，返回用户配置的参数字典。

    Returns:
        {
            "benchmark_method": "mean" | "coefficient",
            "benchmark_coefficient": float,
            "max_score": float,
            "deduction_up": float,
            "deduction_down": float,
            "min_score": float,
            "competitors": [{"label": str, "dist_type": str, "params": dict}, ...],
            "bid_min": float,
            "bid_max": float,
            "bid_step": float,
            "num_simulations": int,
        }
    """
    st.sidebar.header("📋 基准价设置")

    benchmark_method = st.sidebar.selectbox(
        "计算方法",
        options=["mean", "coefficient"],
        format_func=lambda x: "均值法" if x == "mean" else "均值 × 折算系数",
        help="均值法：直接取所有报价的算术平均作为基准价；折算系数法：均值乘以一个系数",
    )

    benchmark_coefficient = 1.0
    if benchmark_method == "coefficient":
        benchmark_coefficient = st.sidebar.number_input(
            "折算系数",
            min_value=0.5,
            max_value=1.5,
            value=0.95,
            step=0.01,
            help="乘以均值得到基准价，如 0.95 即基准价为均值的 95%",
        )

    st.sidebar.header("📋 扣分规则")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        max_score = st.number_input(
            "满分", min_value=1.0, max_value=100.0, value=20.0, step=1.0,
        )
    with col2:
        min_score = st.number_input(
            "最低分", min_value=0.0, max_value=100.0, value=0.0, step=1.0,
        )

    deduction_up = st.sidebar.number_input(
        "上偏扣分（高于基准价每 1% 扣 N 分）",
        min_value=0.0, max_value=10.0, value=1.0, step=0.1,
    )
    deduction_down = st.sidebar.number_input(
        "下偏扣分（低于基准价每 1% 扣 N 分）",
        min_value=0.0, max_value=10.0, value=1.0, step=0.1,
    )

    st.sidebar.header("📋 竞争对手")

    # 动态添加/删除对手
    if "competitor_count" not in st.session_state:
        st.session_state.competitor_count = 3

    def add_competitor():
        st.session_state.competitor_count += 1

    def remove_competitor():
        if st.session_state.competitor_count > 1:
            st.session_state.competitor_count -= 1

    col_add, col_remove = st.sidebar.columns(2)
    with col_add:
        st.button("+ 添加对手", on_click=add_competitor, use_container_width=True)
    with col_remove:
        st.button("- 移除对手", on_click=remove_competitor, use_container_width=True)

    DIST_OPTIONS = ["triangular", "uniform", "normal", "pert"]
    DIST_LABELS = {
        "triangular": "三角分布 Tri",
        "uniform": "均匀分布 Uni",
        "normal": "正态分布 Norm",
        "pert": "PERT 分布",
    }

    competitors = []
    for i in range(st.session_state.competitor_count):
        with st.sidebar.expander(f"对手 {i + 1}", expanded=(i < 3)):
            dist_type = st.selectbox(
                "分布类型",
                options=DIST_OPTIONS,
                format_func=lambda x: DIST_LABELS[x],
                key=f"dist_type_{i}",
            )

            if dist_type in ("triangular", "pert"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    low = st.number_input("最低", value=30.0, step=1.0, key=f"low_{i}")
                with c2:
                    mode = st.number_input("最可能", value=35.0, step=1.0, key=f"mode_{i}")
                with c3:
                    high = st.number_input("最高", value=42.0, step=1.0, key=f"high_{i}")
                params = {"low": low, "mode": mode, "high": high}

            elif dist_type == "uniform":
                c1, c2 = st.columns(2)
                with c1:
                    low = st.number_input("最低", value=30.0, step=1.0, key=f"uni_low_{i}")
                with c2:
                    high = st.number_input("最高", value=42.0, step=1.0, key=f"uni_high_{i}")
                params = {"low": low, "high": high}

            elif dist_type == "normal":
                c1, c2 = st.columns(2)
                with c1:
                    mu = st.number_input("均值 μ", value=35.0, step=1.0, key=f"mu_{i}")
                with c2:
                    sigma = st.number_input(
                        "标准差 σ", min_value=0.1, value=3.0, step=0.5, key=f"sigma_{i}",
                    )
                params = {"mu": mu, "sigma": sigma}

            competitors.append({
                "label": f"对手 {i + 1}",
                "dist_type": dist_type,
                "params": params,
            })

    st.sidebar.header("📋 你的报价")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        bid_min = st.number_input("扫描下限", value=30.0, step=1.0)
    with col2:
        bid_max = st.number_input("扫描上限", value=42.0, step=1.0)

    bid_step = st.number_input(
        "扫描步长", min_value=0.1, value=0.5, step=0.1,
        help="步长越小结果越精细但计算量越大",
    )

    st.sidebar.header("📋 模拟设置")

    num_simulations = st.select_slider(
        "模拟次数",
        options=[100, 500, 1000, 5000, 10000, 50000],
        value=10000,
        help="次数越多结果越稳定但耗时越长。调参时可用 500-1000 快速预览",
    )

    return {
        "benchmark_method": benchmark_method,
        "benchmark_coefficient": benchmark_coefficient,
        "max_score": max_score,
        "deduction_up": deduction_up,
        "deduction_down": deduction_down,
        "min_score": min_score,
        "competitors": competitors,
        "bid_min": bid_min,
        "bid_max": bid_max,
        "bid_step": bid_step,
        "num_simulations": num_simulations,
    }
```

- [ ] **Step 2: 验证模块可正常导入**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -c "from ui.sidebar import render_sidebar; print('sidebar module OK')"
```
Expected: `sidebar module OK`

- [ ] **Step 3: 提交**

```bash
git add ui/sidebar.py
git commit -m "feat: Streamlit 侧边栏参数面板"
```

---

### Task 6: 应用入口 & 粘合层

**Files:**
- Create: `app.py`

- [ ] **Step 1: 实现 Streamlit 主入口**

```python
# app.py
"""报价测算工具 — Streamlit 应用入口。

启动: streamlit run app.py --server.port 8002
"""

import sys
import streamlit as st
import numpy as np

# 确保项目根目录在 sys.path 中
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.distribution import create_distribution, BaseDistribution
from simulation.engine import run_simulation
from ui.sidebar import render_sidebar
from ui.charts import (
    plot_win_probability,
    plot_expected_score,
    plot_risk_heatmap,
    get_best_recommendation,
)

st.set_page_config(
    page_title="报价测算工具",
    page_icon="📊",
    layout="wide",
)

st.title("📊 报价测算工具")
st.caption("蒙特卡洛模拟 · 均值基准价法 · 中标概率分析")

# 侧边栏参数
params = render_sidebar()

# 主区域
tab1, tab2, tab3 = st.tabs(["🎯 中标概率", "📈 期望得分", "🔥 风险热力"])

# 模拟按钮在侧边栏底部触发
run_button = st.sidebar.button("▶ 开始测算", type="primary", use_container_width=True)

if run_button:
    # 构建分布列表
    try:
        competitor_dists: list[BaseDistribution] = []
        for comp in params["competitors"]:
            dist = create_distribution(comp["dist_type"], **comp["params"])
            competitor_dists.append(dist)
    except ValueError as e:
        st.error(f"参数错误：{e}")
        st.stop()

    # 校验报价范围
    if params["bid_min"] >= params["bid_max"]:
        st.error("报价扫描下限必须小于上限")
        st.stop()

    # 运行模拟
    with st.spinner(f"正在模拟 {params['num_simulations']:,} 次..."):
        np.random.seed(None)  # 每次运行使用不同的随机序列
        results = run_simulation(
            bid_range=(params["bid_min"], params["bid_max"]),
            bid_step=params["bid_step"],
            competitor_dists=competitor_dists,
            num_simulations=params["num_simulations"],
            benchmark_coefficient=params["benchmark_coefficient"],
            max_score=params["max_score"],
            deduction_up=params["deduction_up"],
            deduction_down=params["deduction_down"],
            min_score=params["min_score"],
        )

    st.success(f"模拟完成！共 {len(results)} 个报价点，每个模拟 {params['num_simulations']:,} 次")

    # 渲染图表
    with tab1:
        st.plotly_chart(
            plot_win_probability(results),
            use_container_width=True,
        )
        st.markdown(get_best_recommendation(results))

    with tab2:
        st.plotly_chart(
            plot_expected_score(results, max_score=params["max_score"]),
            use_container_width=True,
        )

    with tab3:
        st.plotly_chart(
            plot_risk_heatmap(
                results,
                competitor_dists_info=params["competitors"],
                bid_step=params["bid_step"],
                num_simulations=params["num_simulations"],
            ),
            use_container_width=True,
        )

    # 原始数据（折叠）
    with st.expander("📋 原始数据"):
        st.dataframe(
            {
                "报价": list(results.keys()),
                "中标概率(%)": [f"{results[b]['win_prob']:.2f}" for b in results],
                "期望得分": [f"{results[b]['expected_score']:.2f}" for b in results],
            },
            use_container_width=True,
        )
else:
    st.info("👈 在左侧配置参数后，点击「开始测算」按钮")
```

- [ ] **Step 2: 验证应用可导入无语法错误**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -c "
import ast
with open('app.py') as f:
    ast.parse(f.read())
print('app.py syntax OK')
"
```
Expected: `app.py syntax OK`

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "feat: Streamlit 应用入口，粘合全部模块"
```

---

### Task 7: 端到端验证 & README

**Files:**
- Create: `README.md`

- [ ] **Step 1: 运行全部单元测试确认回归**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && python -m pytest tests/ -v
```
Expected: 21 passed (6 scoring + 10 distribution + 5 engine)

- [ ] **Step 2: Streamlit 冒烟测试（启动→加载→退出）**

```bash
cd ~/agents/work/bidding-calculator && source venv/bin/activate && timeout 5 streamlit run app.py --server.port 8002 --server.headless true 2>&1 || true
```
Expected: Streamlit 正常启动，无 import 错误

- [ ] **Step 3: 写 README**

```markdown
# 📊 报价测算工具

基于蒙特卡洛模拟的投标报价分析工具，帮助你在均值基准价法下找到最优报价策略。

## 快速开始

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8002
```

浏览器打开 `http://localhost:8002`。

## 功能

- **均值基准价法**：支持纯均值或带折算系数的基准价
- **对称/非对称扣分**：上下偏离可设定不同扣分力度
- **4 种对手分布模型**：均匀、三角、正态、PERT
- **蒙特卡洛模拟**：模拟次数可调，平衡速度与精度
- **三大图表**：中标概率曲线、期望得分曲线、风险热力图
- **最佳报价建议**：自动识别高安全报价区间

## 使用流程

1. 在左侧配置基准价计算方式和扣分规则
2. 添加竞争对手并设定其报价分布
3. 设定自己的报价扫描范围和步长
4. 选择模拟次数（调参用 500-1000，最终确认用 10000+）
5. 点击「开始测算」，查看图表和建议

## 项目结构

```
bidding-calculator/
├── app.py              # Streamlit 入口
├── models/
│   ├── scoring.py      # 评分公式
│   └── distribution.py # 对手报价分布
├── simulation/
│   └── engine.py       # 蒙特卡洛模拟
├── ui/
│   ├── sidebar.py      # 参数面板
│   └── charts.py       # 图表渲染
├── tests/              # 单元测试
└── requirements.txt
```

## 分享

- **本地分享**：同事 clone 仓库后执行上述启动命令
- **Streamlit Cloud**：推送到 GitHub 后在 [Streamlit Cloud](https://streamlit.io/cloud) 一键部署

## 许可

内部使用工具。
```

- [ ] **Step 4: 删除旧的测算脚本（已迁移到新工具）**

```bash
# 旧文件保留在桌面作为参考，不做删除
echo "旧脚本已迁移至 ~/agents/work/bidding-calculator/"
```

- [ ] **Step 5: 最终提交**

```bash
git add README.md && git commit -m "docs: README 使用说明"
```

---

## 自审检查清单

- [x] **Spec 覆盖**：评分公式 ✅ Task 1 / 分布模型 ✅ Task 2 / 模拟引擎 ✅ Task 3 / 图表 ✅ Task 4 / 参数面板 ✅ Task 5 / 入口 ✅ Task 6
- [x] **无占位符**：所有步骤包含完整代码，无 TBD/TODO
- [x] **类型一致性**：`run_simulation` 返回 `dict[float, dict[str, float]]`，所有消费方（charts.py, app.py）使用相同结构
- [x] **端口已注册**：8002 → bidding-calculator
