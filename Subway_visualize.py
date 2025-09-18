import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import os
import warnings
import re
import time
import requests
from bs4 import BeautifulSoup
from geopy.distance import geodesic
from shapely.geometry import Point

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.family'] = ['SimHei', 'Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def get_railway_stop(Target_city):
    citylist = requests.get(url='https://map.amap.com/service/subway?_1707184339116&srhdata=citylist.json').json()
    spell = ''
    adcode = ''
    for city in citylist['citylist']:
        if city['cityname'] == Target_city:
            spell = city['spell']
            adcode = city['adcode']
            break
    if spell == '':
        print('城市名输入错误')
    else:
        city_url = f'https://map.amap.com/service/subway?_1707184339123&srhdata={adcode}_drw_{spell}.json'
        target_city = requests.get(url=city_url).json()
        filename = target_city['s']
        result = {'name': [], 'line': [], 'lon': [], 'lat': [],
                  }
    for line in range(len(target_city['l'])):
        for stop in range(len(target_city['l'][line]['st'])):
            result['name'].append(target_city['l'][line]['st'][stop]['n'])
            result['line'].append(target_city['l'][line]['kn'] + target_city['l'][line]['la'])
            lon_lat = target_city['l'][line]['st'][stop]['sl'].split(',')
            result['lon'].append(lon_lat[0])
            result['lat'].append(lon_lat[1])
    data = pd.DataFrame(result)
    data[['lon', 'lat']] = data[['lon', 'lat']].apply(pd.to_numeric)
    data.to_excel((f'{filename}.xlsx'), index=False)
    return filename


def Geopandas_Change():
    file_path = f'{filename}.xlsx'
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    print("原始数据列名:", df.columns.tolist())
    print("数据样例:")
    print(df.head(3))
    df['lon'] = pd.to_numeric(df['lon'])
    df['lat'] = pd.to_numeric(df['lat'])
    geometry = [Point(lon, lat) for lon, lat in zip(df['lon'], df['lat'])]
    gdf = gpd.GeoDataFrame(
        df[['name', 'line']],
        geometry=geometry,
        crs="EPSG:4326"
    )
    gdf['station_id'] = range(1, len(gdf) + 1)
    print("\n地理数据信息:")
    print(f"总站点数: {len(gdf)}")
    print(f"地铁线路数: {gdf['line'].nunique()}")
    print(f"空间范围: {gdf.total_bounds}")
    output_dir = '地铁空间数据'
    os.makedirs(output_dir, exist_ok=True)
    gpkg_path = os.path.join(output_dir, f'{filename}.gpkg')
    gdf.to_file(gpkg_path, layer='地铁站点', driver='GPKG', encoding='utf-8')
    shp_path = os.path.join(output_dir, f'{filename}.shp')
    gdf.to_file(shp_path, encoding='utf-8')
    print("\n处理完成! 保存结果:")
    print(f"1. GeoPackage文件: {gpkg_path}")
    print(f"2. Shapefile文件组: {shp_path}")

def fetch_anjuke_rentals(max_pages=10):
    headers = {
            'User-Agent': '浏览器参数',
            'Cookie': '你的cookie',
            'Referer': f'https://xm.zu.anjuke.com/ditie/'
        }

    all_data = []

    for page in range(1, max_pages + 1):
        try:
            url = f'https://xm.zu.anjuke.com/ditie/dt157/-p{page}/'
            response = requests.get(url, headers=headers)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            rental_items = soup.find_all('div', class_='zu-itemmod')
            for item in rental_items:
                try:
                    title_tag = item.find('h3').find('a').find('b', class_='strongbox')
                    title = title_tag.get_text().strip() if title_tag else None
                    price_tag = item.find('div', class_='zu-side').find('strong', class_='price')
                    price = price_tag.get_text().strip() if price_tag else None
                    detail_tag = item.find('p', class_='details-item')
                    area = None
                    if detail_tag:
                        strong_tags = detail_tag.find_all('b', class_='strongbox')
                        if len(strong_tags) >= 3:
                            area = strong_tags[2].get_text().strip()

                    bot_tag = item.find('p', class_='bot-tag')
                    subway_distance = None
                    if bot_tag:
                        subway_spans = bot_tag.find_all('span', class_='cls-common')
                        for span in subway_spans:
                            text = span.get_text().strip()
                            if '距1号线' in text:  #此处要根据你的地铁线路去调整
                                subway_distance = text
                                break

                    address_tag = item.find('address', class_='details-item')
                    address = None
                    if address_tag:
                        address_link = address_tag.find('a')
                        address = address_link.get_text().strip() if address_link else None

                    if title and price and area:
                        all_data.append({
                            'title': title,
                            'price': float(price),
                            'area': float(area),
                            'subway_distance': subway_distance,
                            'address': address,
                            'price_per_sqm': float(price) / float(area) if area else None
                            })

                except Exception as e:
                    print(f"处理房源项时出错: {str(e)}")
                    continue

            print(f"已爬取第{page}页数据，累计{len(all_data)}条房源")
            time.sleep(2)

        except Exception as e:
            print(f"第{page}页爬取出错: {str(e)}")
            continue
    AjK=pd.DataFrame(all_data)
    AjK.to_csv("AJK.csv")


class SubwayRentalVisualizer:
    def __init__(self):
        # 结果保存路径
        self.output_dir = "地铁租房指数可视化结果"

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.subway_data = self._load_subway_data()
        self.line_stations = self._extract_line_stations()
        self.rental_data = self._load_rental_data()
        self.analysis_results = None
        self.nearby_rentals_by_station = {}


    def _load_subway_data(self):
        try:
            gdf = gpd.read_file(fr'地铁空间数据\{filename}.gpkg')

            if 'name' not in gdf.columns and '名称' in gdf.columns:
                gdf['name'] = gdf['名称']
            if 'line' not in gdf.columns and '线路' in gdf.columns:
                gdf['line'] = gdf['线路']

            if 'lon' not in gdf.columns:
                gdf['lon'] = gdf.geometry.x
            if 'lat' not in gdf.columns:
                gdf['lat'] = gdf.geometry.y

            return gdf
        except Exception as e:
            print(f"读取地铁数据出错: {e}")

    def _extract_line_stations(self):
        if self.subway_data is None:
            return None

        # 可能的线路名称格式：'1号线', '地铁1号线', '地铁一号线'
        line1_patterns = ['1号线', '地铁1号线', '地铁一号线']
        line1_stations = self.subway_data[self.subway_data['line'].str.contains('|'.join(line1_patterns), na=False)].copy()
        print(f"提取到地铁一号线站点数量: {len(line1_stations)}")
        
        # 显示站点列表
        print("地铁一号线站点列表:")
        for idx, row in line1_stations.iterrows():
            print(f"{row['name']} - 经纬度: ({row['lon']}, {row['lat']})")
        
        return line1_stations
    
    def _load_rental_data(self):
        try:
            rental_data = pd.read_csv('AJK.csv', encoding='utf-8-sig')
            print(f"成功加载房源数据，共{len(rental_data)}条记录")

            def extract_distance(distance_str):
                if pd.isna(distance_str):
                    return None
                match = re.search(r'(\d+)m', str(distance_str))
                if match:
                    return float(match.group(1)) / 1000  # 转换为公里
                return None
            rental_data['distance_km'] = rental_data['subway_distance'].apply(extract_distance)
            if 'price_per_sqm' not in rental_data.columns:
                rental_data['price_per_sqm'] = rental_data['price'] / rental_data['area']
            return rental_data
        except Exception as e:
            print(f"加载租房数据出错: {e}")
            return None
    
    def _calculate_distance(self, point1, point2):
        return geodesic(point1, point2).km
    
    def analyze_rental_around_stations(self):
        if self.line_stations is None:
            print("没有地铁一号线数据，无法进行分析")
            return
        
        if self.rental_data is None:
            print("没有房源数据，无法进行分析")
            return

        results = []
        
        print("开始分析每个地铁站周边1公里范围内的租房数据...")
        
        for idx, station in self.line_stations.iterrows():
            station_name = station['name']
            station_lat = station['lat']
            station_lon = station['lon']

            nearby_rentals = []
            station_rentals = self.rental_data[(
                self.rental_data['subway_distance'].str.contains(station_name, na=False)) &
                (self.rental_data['distance_km'] <= 1.0)
            ].copy()
            valid_rentals = station_rentals.dropna(subset=['price', 'area', 'price_per_sqm'])
            for _, rental in valid_rentals.iterrows():
                nearby_rentals.append({
                    'station': station_name,
                    'distance': rental['distance_km'],
                    'price': rental['price'],
                    'area': rental['area'],
                    'price_per_sqm': rental['price_per_sqm'],
                    'title': rental['title'],
                    'address': rental['address']
                })

            if nearby_rentals:
                self.nearby_rentals_by_station[station_name] = nearby_rentals

            if nearby_rentals:
                nearby_df = pd.DataFrame(nearby_rentals)

                result = {
                    'station': station_name,
                    'station_lat': station_lat,
                    'station_lon': station_lon,
                    'rental_count': len(nearby_df),
                    'avg_price': nearby_df['price'].mean(),
                    'avg_price_per_sqm': nearby_df['price_per_sqm'].mean(),
                    'min_price_per_sqm': nearby_df['price_per_sqm'].min(),
                    'max_price_per_sqm': nearby_df['price_per_sqm'].max()
                }

                if not nearby_df.empty:
                    min_price_idx = nearby_df['price_per_sqm'].idxmin()
                    result['cheapest_rental_info'] = nearby_df.loc[min_price_idx].to_dict()
                
                results.append(result)
                
                print(f"{station_name}: 分析了{len(nearby_df)}套房源数据，平均每平米租金{result['avg_price_per_sqm']:.2f}元")

        self.analysis_results = pd.DataFrame(results)
        print("分析完成")

        if not self.analysis_results.empty:
            excel_path = os.path.join(self.output_dir, "地铁租房指数分析结果.xlsx")
            self.analysis_results.to_excel(excel_path, index=False)
            print(f"分析结果已保存到: {excel_path}")
        
        return self.analysis_results
    
    def visualize_rental_index(self):
        """可视化厦门地铁一号线租房指数"""
        if self.analysis_results is None or len(self.analysis_results) == 0:
            print("没有分析结果或结果为空，无法进行可视化")
            return
        
        print("开始生成可视化图表...")
        
        # 创建一个大图
        plt.figure(figsize=(24, 20))

        # 1. 各站点周边每平米月租金最低价格柱状图（降序）
        plt.subplot(2, 2, 1)
        sorted_df = self.analysis_results.sort_values('min_price_per_sqm', ascending=False)
        sns.barplot(data=sorted_df, x='min_price_per_sqm', y='station', palette='viridis')
        plt.title(f'{filename}地铁一号线各站点1公里范围内最低每平米月租金（降序）', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('最低每平米月租金（元）', fontsize=14)
        plt.ylabel('站点名称', fontsize=14)
        plt.grid(axis='x', alpha=0.3)
        

        for i, value in enumerate(sorted_df['min_price_per_sqm']):
            plt.text(value + 0.5, i, f'{value:.2f}', va='center', fontsize=12, fontweight='bold')

        # 2. 各站点周边房源数量柱状图（降序排序）
        plt.subplot(2, 2, 2)
        sorted_count_df = self.analysis_results.sort_values('rental_count', ascending=False)
        bars = sns.barplot(data=sorted_count_df, x='rental_count', y='station', palette='magma')
        plt.title(f'{filename}地铁一号线各站点1公里范围内房源数量（降序排序）', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('房源数量（套）', fontsize=14)
        plt.ylabel('站点名称', fontsize=14)
        plt.grid(axis='x', alpha=0.3)

        bars.bar_label(bars.containers[0], fmt='%d', label_type='edge', fontsize=12, fontweight='bold', padding=5)
        max_count = sorted_count_df['rental_count'].max()
        plt.xlim(0, max_count * 1.15)
        
        # 3. 各站点周边平均每平米月租金柱状图
        plt.subplot(2, 2, 3)

        line1_order = self.line_stations['name'].tolist()
        valid_stations = [station for station in line1_order if station in self.analysis_results['station'].values]
        self.analysis_results['station'] = pd.Categorical(self.analysis_results['station'], categories=valid_stations, ordered=True)
        sorted_by_line = self.analysis_results.sort_values('station')
        
        sns.barplot(data=sorted_by_line, x='station', y='avg_price_per_sqm', palette='coolwarm')
        plt.title(f'{filename}地铁一号线各站点1公里范围内平均每平米月租金', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('站点名称', fontsize=14)
        plt.ylabel('平均每平米月租金（元）', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        

        for i, value in enumerate(sorted_by_line['avg_price_per_sqm']):
            plt.text(i, value + 0.5, f'{value:.2f}', ha='center', fontsize=10, fontweight='bold')
        
        # 4. 每平米租金分布箱线图
        plt.subplot(2, 2, 4)
        boxplot_data = []
        for _, station_rentals in self.nearby_rentals_by_station.items():
            for rental in station_rentals:
                if 'price_per_sqm' in rental and rental['price_per_sqm'] is not None:
                    boxplot_data.append({
                        'station': rental['station'],
                        'price_per_sqm': rental['price_per_sqm']
                    })
        

        boxplot_df = pd.DataFrame(boxplot_data)
        if not boxplot_df.empty:
            boxplot_df['station'] = pd.Categorical(boxplot_df['station'], categories=valid_stations, ordered=True)
            

            sns.boxplot(data=boxplot_df, y='station', x='price_per_sqm', palette='Set2')
            plt.title(f'{filename}地铁一号线各站点1公里范围内每平米月租金分布', fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('每平米月租金（元）', fontsize=14)
            plt.ylabel('站点名称', fontsize=14)
            plt.grid(axis='x', alpha=0.3)

            q1 = boxplot_df['price_per_sqm'].quantile(0.25)
            q3 = boxplot_df['price_per_sqm'].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            plt.xlim(max(0, lower_bound - 5), upper_bound + 10)
        else:
            plt.text(0.5, 0.5, '无足够数据生成箱线图', ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
        
        plt.tight_layout()

        chart_path = os.path.join(self.output_dir, "厦门地铁一号线租房指数可视化.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"可视化图表已保存到: {chart_path}")
        plt.show()
    
    def run_full_analysis(self):

        if self.line_stations is None:
            print("无法提取地铁一号线数据，分析终止")
            return
        self.analyze_rental_around_stations()
        self.visualize_rental_index()

if __name__ == "__main__":
    filename=get_railway_stop("厦门市")
    Geopandas_Change()
    fetch_anjuke_rentals()

    visualizer = SubwayRentalVisualizer()
    visualizer.run_full_analysis()