# 轨住图谱 (Subway Rent Map)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ⚠️ 数据声明

本工具所有数据均通过公开网络渠道获取，仅用于学习交流与技术研究，不保证其准确性、完整性与时效性。所有分析结果仅供参考，不构成任何租房、投资或其他决策建议。请用户在实际租房过程中谨慎核实信息，注意防范风险。

## 介绍

一个为“地铁通勤族”设计的租房数据可视化工具，帮助你快速概览城市地铁沿线的租金水平。

轨住图谱是一个开源的地铁沿线租房数据分析与可视化工具。它能帮助用户在选择租房地点时，将通勤便利性（地铁）与生活成本（租金）结合起来，做出更明智的决策。

![示意图](https://my-buxket.oss-cn-beijing.aliyuncs.com/20251116084911.png)

## 🔥 功能与特色

- **🗺️ 多城市支持**: 自动获取并展示已开通地铁的城市列表。
- **🚇 线路数据整合**: 清晰展示指定城市的所有地铁线路及站点信息。
- **📈 租金数据分析**: 抓取并分析地铁站点周边的租房数据。
- **📊 丰富图表可视化**: 生成包括“租金价格箱线图”、“房源数量统计图”在内的多种图表。
- **🌐 Web 界面**: 提供简洁的 Web 界面进行交互式查询与结果展示。
- **🐳 Docker 支持**: 支持 Docker 一键启动，简化部署流程。

## 🚀 快速开始

你可以选择以下任意一种方式来运行本项目。

### 方式一：使用 Docker (推荐)

确保你的环境中已安装 Docker 和 Docker Compose。

```bash
# 1. 克隆项目到本地
git clone https://github.com/your-username/SubwayVisualize.git
cd SubwayVisualize

# 2. 使用 Docker Compose 启动服务
docker compose up -d

# 3. 访问应用
# 打开浏览器访问: http://127.0.0.1:5000/
```

### 方式二：本地 Python 环境

```bash
# 1. 克隆项目到本地
git clone https://github.com/your-username/SubwayVisualize.git
cd SubwayVisualize

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python serve.py

# 4. 访问应用
# 打开浏览器访问: http://127.0.0.1:5000/
```

## 📁 核心目录结构

```
src/subway_visualize/
├── app.py
├── main.py
├── services/
│   ├── subway_visualize.py
│   └── crawler_firecrawl.py
├── templates/index.html
└── static/
serve.py
requirements.txt
Dockerfile
docker-compose.yml
```

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request 来帮助改进项目。

## 📝 许可证

本项目采用 MIT 许可证。
