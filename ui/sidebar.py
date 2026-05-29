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
