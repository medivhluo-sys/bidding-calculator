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

## 密码设置

公有部署需设置访问密码：

- **本地开发**：创建 `.streamlit/secrets.toml`，写入 `APP_PASSWORD = "你的密码"`
- **Streamlit Cloud**：在 App Settings → Secrets 中设置 `APP_PASSWORD = "你的密码"`

不设密码时本地可直接访问。

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

## 线上地址

手机端访问（无需电脑开机）：`https://bidding-calculator-wsq2qct7wnwsvlbsjbhtk3.streamlit.app`

## 修订与同步

代码推送后 Streamlit Cloud 自动重新部署，无需手动操作。

```bash
cd ~/agents/work/bidding-calculator
source venv/bin/activate

# 1. 修改代码
# 2. 运行测试确认
pytest -v

# 3. 提交
git add -A && git commit -m "描述改动内容"

# 4. 推送 GitHub（自动触发 Streamlit Cloud 更新）
export GH_TOKEN="你的 GitHub PAT"
gh auth setup-git
git push
```

推送后等待 1-2 分钟，刷新手机网址即可看到最新版。

## 技术栈

- Web 框架：Streamlit
- 图表：Plotly
- 数值计算：NumPy
- 部署：GitHub + Streamlit Cloud（自动同步）
