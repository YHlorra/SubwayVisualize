# SubwayVisualize
本项目是一个综合性的数据分析和可视化项目，旨在分析厦门市地铁一号线周边租房市场情况。项目通过爬取高德地图的地铁站点数据和安居客平台的租房信息，结合地理空间分析和数据可视化技术，为租房者提供地铁沿线租房决策支持。

**​数据声明**: 本项目数据来源于高x地图和安x客平台，所有数据仅供参考，不构成任何投资或租房建议。数据采集时可能存在延迟或误差，请以官方发布信息为准。

# 功能特点
🚇 地铁站点数据获取与处理  
🏠 租房信息网络爬虫  
📊 空间数据分析与可视化  
📈 租房指数计算与图表展示  
🌆 多城市支持（可轻松修改为其他城市）  

# 数据来源
**​地铁数据**: 高德地图API (https://map.amap.com/service/subway)  
**​租房数据**: 安居客租房平台 (https://xm.zu.anjuke.com)

# 项目结构
├── main.py                    # 主程序文件  
├── 厦门市地铁.xlsx            # 地铁站点数据（自动生成）  
├── 地铁空间数据/              # 地理空间数据文件夹（自动生成）  
│   ├── 厦门地铁.gpkg  
│   └── 厦门地铁.shp    
├── AJK.csv                   # 租房数据（自动生成）  
└── 地铁租房指数可视化结果/    # 分析结果（自动生成）  
    ├── 地铁租房指数分析结果.xlsx  
    └── 厦门地铁一号线租房指数可视化.png  
# 代码结构
main.py  
├── get_railway_stop()         # 获取地铁站点数据（支持多城市）  
├── Geopandas_Change()         # 转换地理空间数据  
├── fetch_anjuke_rentals()     # 爬取租房数据（支持多城市）  
└── SubwayRentalVisualizer类   # 分析与可视化  
    ├── __init__()             # 初始化  
    ├── _load_subway_data()    # 加载地铁数据  
    ├── _extract_line_stations() # 提取线路信息  
    ├── _load_rental_data()    # 加载租房数据  
    ├── analyze_rental_around_stations() # 分析租房指数  
    └── visualize_rental_index() # 可视化结果  
# 安装与使用
## 环境要求
Python 3.7+  
以下Python库：  
pandas  
matplotlib  
seaborn  
geopandas  
requests  
beautifulsoup4  
geopy  
shapely  
## 安装步骤
### 克隆项目到本地

```bash
git clone https://github.com/yourusername/xiamen-subway-rental-analysis.git
cd xiamen-subway-rental-analysis
```
## 安装依赖库
```bash
pip install -r requirements.txt
```
### 运行程序（默认分析厦门市）
```bash
python main.py
```
如需分析其他城市，修改代码中的城市名称：
```python
#在main.py中将"厦门市"改为目标城市
get_railway_stop("北京市")  # 改为你想要分析的城市
```
# 使用说明
程序会自动从高x地图API获取指定城市的地铁站点数据  
爬取安x客网站上该城市地铁线路周边的租房信息  
分析每个地铁站周边1公里范围内的租房情况  
生成可视化图表和分析报告  
## 输出结果
程序运行后将生成以下结果：
**​数据分析表格​**：
包含各站点租房数量、平均价格等指标
**​可视化图表​**：
各站点最低每平米月租金对比  
各站点房源数量对比  
各站点平均每平米月租金对比  
每平米租金分布箱线图  

# 注意事项
网络爬虫部分依赖于网站结构，如果网站改版可能需要调整代码  
程序运行需要网络连接以获取实时数据  
**​数据仅供参考，实际租房价格请以实地考察和官方信息为准**
不同城市的安居客网址结构可能不同，需要相应调整
# 免责声明
本项目所有数据均来自公开网络平台，仅供学习和研究使用。数据准确性、完整性和时效性无法保证，不构成任何投资建议或租房决策依据。使用者应自行判断数据的可靠性，并对基于此数据做出的任何决定负责。
# 贡献指南
欢迎提交Issue和Pull Request来改进本项目。特别是： 

**增加对新城市的支持  
优化爬虫稳定性  
改进可视化效果  
添加新的分析维度**
# 许可证
本项目采用MIT许可证。详情请参阅LICENSE文件。
# 联系方式
如有问题或建议，请通过以下方式联系：
提交GitHub Issue  
发送邮件至: 2553490479@qq.com
