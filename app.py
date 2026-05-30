"""报价测算工具 — Streamlit 应用入口。

启动: streamlit run app.py --server.port 8502
"""

import sys
import json
import streamlit as st
import numpy as np

# 确保项目根目录在 sys.path 中
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.distribution import create_distribution, BaseDistribution
from simulation.engine import run_simulation
from ui.sidebar import render_sidebar
from ui.charts import (
    plot_tolerance_probability,
    plot_competitor_gap_bars,
    get_best_recommendation,
)

st.set_page_config(
    page_title="报价测算工具",
    page_icon="📊",
    layout="wide",
)

st.title("📊 报价测算工具")
st.caption("蒙特卡洛模拟 · 均值基准价法 · 容忍分差分析")

# 侧边栏参数
params = render_sidebar()

# 检测参数是否变化，变化时清除缓存
params_hash = json.dumps(params, sort_keys=True, default=str)
if "params_hash" not in st.session_state:
    st.session_state.params_hash = None
if "results" not in st.session_state:
    st.session_state.results = None

params_changed = st.session_state.params_hash != params_hash

# 模拟按钮
run_button = st.sidebar.button("▶ 开始测算", type="primary", use_container_width=True)

if run_button or (st.session_state.results is not None and not params_changed):
    # 仅在首次点击或参数未变时使用缓存
    if st.session_state.results is None or params_changed:
        # 构建分布列表
        try:
            competitor_dists: list[BaseDistribution] = []
            for comp in params["competitors"]:
                dist = create_distribution(comp["dist_type"], **comp["params"])
                competitor_dists.append(dist)
        except ValueError as e:
            st.error(f"参数错误：{e}")
            st.stop()

        if params["bid_min"] >= params["bid_max"]:
            st.error("报价扫描下限必须小于上限")
            st.stop()

        with st.spinner(f"正在模拟 {params['num_simulations']:,} 次..."):
            results = run_simulation(
                bid_range=(params["bid_min"], params["bid_max"]),
                bid_step=params["bid_step"],
                competitor_dists=competitor_dists,
                num_simulations=params["num_simulations"],
                tolerance=params["tolerance"],
                benchmark_coefficient=params["benchmark_coefficient"],
                max_score=params["max_score"],
                deduction_up=params["deduction_up"],
                deduction_down=params["deduction_down"],
                min_score=params["min_score"],
            )

        st.session_state.results = results
        st.session_state.params_hash = params_hash

    results = st.session_state.results
    tol = params["tolerance"]

    if run_button:
        st.success(f"模拟完成！共 {len(results)} 个报价点，每个模拟 {params['num_simulations']:,} 次")

    # 视角一：容忍分差概率
    st.subheader("🎯 分差 ≤ %s 分的概率" % tol)
    st.plotly_chart(
        plot_tolerance_probability(results, tol),
        use_container_width=True,
    )
    st.markdown(get_best_recommendation(results, tol))

    # 视角二：选定报价下的对手分差剖面
    competitor_labels = [c["label"] for c in params["competitors"]]
    available_bids = sorted(results.keys())
    best_bid = max(results, key=lambda b: results[b]["tolerance_prob"])

    st.subheader("⚔️ 对手分差剖面")
    selected_bid = st.select_slider(
        "选择报价点查看分差（无需重跑模拟）",
        options=available_bids,
        value=best_bid,
        help="切换报价点，查看该点下与各对手的分差概率分布",
    )
    st.plotly_chart(
        plot_competitor_gap_bars(results, selected_bid, competitor_labels),
        use_container_width=True,
    )

    # 原始数据（折叠）
    with st.expander("📋 原始数据"):
        st.dataframe(
            {
                "报价": list(results.keys()),
                f"分差≤{tol}分的概率(%)": [
                    f"{results[b]['tolerance_prob']:.2f}" for b in results
                ],
                "严格中标概率(%)": [
                    f"{results[b]['win_prob']:.2f}" for b in results
                ],
                "期望得分": [f"{results[b]['expected_score']:.2f}" for b in results],
            },
            use_container_width=True,
        )
else:
    st.info("👈 在左侧配置参数和容忍分差，点击「开始测算」")
