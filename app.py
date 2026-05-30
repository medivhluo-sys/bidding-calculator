"""报价测算工具 — Streamlit 应用入口。

启动: streamlit run app.py --server.port 8502
"""

import sys
import streamlit as st

# 确保项目根目录在 sys.path 中
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.distribution import create_distribution, BaseDistribution
from simulation.engine import run_simulation
from ui.sidebar import render_sidebar
from ui.charts import plot_tolerance_probability, get_best_recommendation

st.set_page_config(
    page_title="报价测算工具",
    page_icon="📊",
    layout="wide",
)

st.title("📊 报价测算工具")
st.caption("蒙特卡洛模拟 · 均值基准价法 · 容忍分差分析")

# 侧边栏参数
params = render_sidebar()

# 主区域：容忍分差滑块（核心交互控件）
st.subheader("🎯 分差容忍度")
tolerance = st.slider(
    "与最高分的分差 ≤ N 分视为安全",
    min_value=0.0,
    max_value=10.0,
    value=3.0,
    step=0.5,
    help="若你的得分不低于最高分 - N 分，则视为该次模拟中安全。N=0 即严格中标。",
)

# 模拟按钮
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
        results = run_simulation(
            bid_range=(params["bid_min"], params["bid_max"]),
            bid_step=params["bid_step"],
            competitor_dists=competitor_dists,
            num_simulations=params["num_simulations"],
            tolerance=tolerance,
            benchmark_coefficient=params["benchmark_coefficient"],
            max_score=params["max_score"],
            deduction_up=params["deduction_up"],
            deduction_down=params["deduction_down"],
            min_score=params["min_score"],
        )

    st.success(f"模拟完成！共 {len(results)} 个报价点，每个模拟 {params['num_simulations']:,} 次")

    # 核心图表
    st.plotly_chart(
        plot_tolerance_probability(results, tolerance),
        use_container_width=True,
    )

    # 建议
    st.markdown(get_best_recommendation(results, tolerance))

    # 原始数据（折叠）
    with st.expander("📋 原始数据"):
        st.dataframe(
            {
                "报价": list(results.keys()),
                f"分差≤{tolerance}分的概率(%)": [
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
    st.info("👈 在左侧配置参数，调整上方分差容忍度，点击「开始测算」")
