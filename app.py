"""报价测算工具 — Streamlit 应用入口。

启动: streamlit run app.py --server.port 8502
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
            plot_risk_heatmap(results),
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
