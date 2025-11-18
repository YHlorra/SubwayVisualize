# 轨住图谱

重要提示：本项目数据来自网络公开信息，可能存在不准确或虚假，仅供参考；租房务必谨慎，务必自行核实并当面确认，避免风险。

![示意图](https://my-buxket.oss-cn-beijing.aliyuncs.com/20251116084911.png)

一个“地铁租房数据可视化”项目，支持多城市。后端基于 Flask，前端为简易页面，数据源为高德地铁与安居客租房。

**数据声明**：数据均来自公开网站，仅供学习与参考，不构成任何建议。

## 功能特点

- 地铁站点数据获取与处理
- 租房数据抓取与清洗
- 空间分析与图表可视化
- 多城市支持，城市代码统一来自安居客城市页

## 数据来源

- 地铁：`https://map.amap.com/service/subway`
- 安居客城市页：`https://www.anjuke.com/sy-city.html`
- 安居客租房入口示例：`https://cs.zu.anjuke.com/ditie/`

## 运行与使用

- 安装依赖：

```bash
pip install -r requirements.txt
```

- 启动服务：`python serve.py`（Waitress 监听 5000 端口）
- 或使用脚本：`powershell -ExecutionPolicy Bypass -File start.ps1`
- 访问页面：打开浏览器访问 `http://127.0.0.1:5000/`

## 前后端接口

- `GET /api/cities`：返回地铁已开通城市列表（高德）
- `GET|POST /api/subway?city=城市名`：返回该城市地铁站点、线路与安居客城市缩写 `city_spell`
- `POST /api/analyze`：参数：`city`、`line`（数字）、`pages`（抓取页数）、`city_spell`（可选）。返回图表与分析结果；遇到限流或无数据时返回友好错误。

## 常见错误与解决

- `城市名称不正确或未开通地铁`：请从下拉列表选择有效城市
- `未识别到城市代码，请从列表选择城市后重试`：请勿手输拼音，直接选择城市名
- `访问过于频繁，请稍后再试或降低抓取页数`：降低 `pages`，间隔几分钟重试
- `未获取到有效房源数据`：可能访问频率过高或线路入口暂无数据。请减少抓取页数、稍后再试或更换线路

## 目录结构（核心）

- `src/subway_visualize/app.py`：Flask 路由与参数校验、错误提示
- `src/subway_visualize/main.py`：生产服务入口（Waitress 监听 5000）
- `src/subway_visualize/templates/index.html`：前端页面
- `src/subway_visualize/static/style.css`：样式文件
- `src/subway_visualize/static/anjuke_city_map.json`：安居客城市与子域缩写映射
- `src/subway_visualize/services/subway_visualize.py`：数据抓取、解析与可视化
- `src/subway_visualize/services/crawler_firecrawl.py`：抓取辅助（如启用 Firecrawl）
- `src/subway_visualize/config.py`：配置与环境变量读取
- `requirements.txt`：依赖列表
- `start.ps1`：Windows 启动脚本
- `serve.py`：统一启动入口（自动注入 src 并启动服务）
- `.env.example`：环境变量示例
- `.gitignore`：包含 `miniprogram/`（小程序目录，已忽略不随仓库提交）

## 关键实现说明

- 城市缩写解析统一：通过 `get_city_spell_by_name` 从 `anjuke_city_map.json` 获取安居客缩写；后端不再依赖高德 `spell` 或本地硬编码字典
- 抓取限流处理：识别“访问过于频繁/请稍后再试/验证”等提示，触发限流并返回友好错误；增加随机等待与页面停留时间降低触发概率
- 可视化输出：生成多类图表与综合图，并支持前端下载
- 下载优化：前端直接使用浏览器保存图片（data URL），无需后端参与，提升可用性与易发现性
- 状态栏：图表区下方实时显示任务进度（开始分析 / 已加载地铁线路 / 开始抓取房产 / 已获取房产数量 / 生成图表 / 分析完成），遇到问题显示错误代码与解决建议

## 注意事项

- 网站结构或策略变更可能影响抓取，需要适配
- 避免短时间大量请求，建议减小抓取页数并分时段重试

### 关于 Firecrawl

- 若未启用 Firecrawl，部分城市与线路页面因动态渲染或反爬策略，抓取可能失败或返回空数据。
- 常见表现：页面提示“访问过于频繁/请稍后再试/验证”，或分析结果显示“未获取到有效房源数据”。
- 建议：
  - 启用 Firecrawl
  - 将抓取页数 `pages` 调小，并分时段重试。
  - 对于频繁失败的线路，尝试更换线路或稍后再试。

## 许可证

MIT

## 反馈

欢迎提交 Issue 或 PR 改进项目
