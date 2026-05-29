# bidding-calculator — 报价测算工具

基于蒙特卡洛模拟的投标报价分析工具，支持均值基准价法、多种对手分布模型、交互式图表。

## 环境要求

Python 3.12+

## 安装

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 运行

```bash
source venv/bin/activate
streamlit run app.py --server.port 8502
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
