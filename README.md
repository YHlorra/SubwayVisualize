# 轨住图谱

<p align="center">
  <img src="https://my-buxket.oss-cn-beijing.aliyuncs.com/20251116084911.png" alt="示意图" width="70%"/>
</p>

<p align="center">
  “轨住图谱”是一个专注于城市地铁沿线租房分析的可视化工具。它能自动汇集并分析公开的地铁与房源数据，将繁杂的信息转化为一目了然的分析图表，帮助你更直观地了解不同站点的租金水平，做出更聪明的租房决策。
</p>

---

### ⚠️ 重要声明

本项目为个人学习与技术交流的开源实践，**严禁用于任何商业用途**。

所有数据均采集自公开网络资源，项目本身不对数据的准确性、完整性或时效性提供任何保证。所有分析结果仅供参考，不构成任何投资或决策建议。

在进行租房等实际决策时，请务必通过官方和正规渠道获取并核实信息，注意防范风险。

---

## 目录

- [功能特点](#功能特点)
- [上手指南](#上手指南)
  - [环境要求](#环境要求)
  - [安装与运行](#安装与运行)
  - [通过-Docker-部署-推荐](#通过-docker-部署-推荐)
- [接口说明](#接口说明)
- [常见问题](#常见问题)
- [项目结构](#项目结构)
- [如何贡献](#如何贡献)
- [鸣谢](#鸣谢)
- [许可证](#许可证)

## 功能特点

- 自动获取并处理多城市的地铁线路和站点数据。
- 抓取指定地铁线路周边的租房信息。
- 对租房数据进行清洗、分析，并生成可视化图表。
- 支持多城市，动态适应不同城市的数据源。

## 上手指南

请遵循以下步骤在你的本地环境中运行本项目。

### 环境要求

- Python 3.x
- 一个能够连接网络的环境

### 安装与运行

1.  **克隆仓库**
    ```bash
    git clone https://github.com/your_username/your_repository.git
    ```

2.  **安装依赖**
    进入项目目录，然后运行：
    ```bash
    pip install -r requirements.txt
    ```

3.  **启动服务**
    -   **方式一**：通过 `serve.py` 启动 (推荐)
        ```bash
        python serve.py
        ```
    -   **方式二**：使用 PowerShell 脚本 (仅限 Windows)
        ```powershell
        powershell -ExecutionPolicy Bypass -File start.ps1
        ```
    服务启动后，默认监听 `5000` 端口。

4.  **访问应用**
    打开浏览器，访问 `http://127.0.0.1:5000/` 即可开始使用。

### 通过 Docker 部署 (推荐)

如果你熟悉 Docker，我们强烈推荐使用容器化方式来运行本项目，这样可以免去环境配置的麻烦。

1.  **构建镜像**
    在项目根目录下运行：
    ```bash
    docker build -t subway-visualize .
    ```

2.  **运行容器**
    ```bash
    docker run -d -p 5000:5000 -a_name subway-app subway-visualize
    ```
    -   `-d`：在后台运行容器。
    -   `-p 5000:5000`：将主机的 5000 端口映射到容器的 5000 端口。
    -   `-a_name subway-app`：为容器指定一个名称，方便管理。

3.  **访问应用**
    打开浏览器，访问 `http://127.0.0.1:5000/`。

4.  **查看日志或停止容器**
    ```bash
    # 查看实时日志
    docker logs -f subway-app

    # 停止并移除容器
    docker stop subway-app
    docker rm subway-app
    ```

## 接口说明

项目提供以下后端接口：

-   `GET /api/cities`：返回所有已开通地铁的城市列表。
-   `GET|POST /api/subway?city=城市名`：获取指定城市的地铁线路、站点信息。
-   `POST /api/analyze`：执行核心分析任务。
    -   **参数**: `city` (城市名), `line` (线路编号), `pages` (抓取页数)。
    -   **返回**: 成功时返回分析图表；失败时返回错误信息。

## 常见问题

-   **提示“城市名称不正确或未开通地铁”**
    请确保从前端页面的下拉列表中选择城市，不要手动输入。

-   **提示“访问过于频繁”或“未获取到有效房源数据”**
    这通常是由于目标网站的反爬虫机制导致。请尝试以下操作：
    1.  减少“抓取页数” (`pages` 参数)。
    2.  等待几分钟后重试。
    3.  更换其他地铁线路进行尝试。
    4.  配置并启用 Firecrawl 等更强的抓取服务。

## 项目结构

核心文件与目录说明如下：

-   `src/subway_visualize/app.py`：Flask 路由与参数校验。
-   `src/subway_visualize/services/subway_visualize.py`：核心服务，负责数据抓取、清洗与可视化。
-   `src/subway_visualize/templates/index.html`：前端页面。
-   `src/subway_visualize/static/`：存放 CSS、JSON 等静态资源。
-   `serve.py`：项目统一启动入口。
-   `requirements.txt`：Python 依赖包列表。
-   `.env.example`：环境变量配置示例。

## 如何贡献

我们非常欢迎社区的贡献！你可以通过以下方式参与：

1.  **Fork** 本项目。
2.  创建你的特性分支 (`git checkout -b feature/NewFeature`)。
3.  提交你的代码 (`git commit -m 'Add some NewFeature'`)。
4.  将你的分支推送到远程 (`git push origin feature/NewFeature`)。
5.  创建一个 **Pull Request**。

## 鸣谢

感谢所有为本项目提供灵感和支持的朋友。

如果这个项目对你有帮助，可以请我喝杯咖啡！

<p align="center">
  <img src="https://my-buxket.oss-cn-beijing.aliyuncs.com/-aef07b0450feff4.jpg" alt="赞赏码" width="300"/>
</p>

## 许可证

本项目基于 [MIT License](LICENSE) 开源。
