# 报价测算工具

基于蒙特卡洛模拟的投标报价分析工具，帮助你在均值基准价法下找到最优报价策略。

## 快速开始

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

浏览器打开 `http://localhost:8502`。

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
