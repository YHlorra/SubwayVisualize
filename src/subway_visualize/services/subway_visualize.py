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
import json
import random
from .crawler_firecrawl import collect_anchors_with_firecrawl, firecrawl_enabled, fetch_html_with_firecrawl
from .proxy_pool import safe_request, get_proxy_session
_SUBWAY_CACHE = {}
_USE_BROWSER = True
_CITY_MAP_CACHE = None
def _root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load_city_map():
    global _CITY_MAP_CACHE
    if _CITY_MAP_CACHE is not None:
        return _CITY_MAP_CACHE
    p = os.path.join(_root_dir(), 'static', 'anjuke_city_map.json')
    try:
        with open(p, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        # 仅保留高德地铁已开通的城市
        try:
            response = safe_request(
                'https://map.amap.com/service/subway?_1707184339116&srhdata=citylist.json',
                pool_name='subway',
                max_retries=3,
                retry_delay=0.6
            )
            j = response.json()
            names = set()
            for c in j.get('citylist', []):
                nm = (c.get('cityname') or '').strip()
                if nm:
                    names.add(nm)
                    base = nm[:-1] if nm.endswith('市') else nm
                    if base:
                        names.add(base)
                    if not nm.endswith('市'):
                        names.add(nm + '市')
            _CITY_MAP_CACHE = [it for it in (raw or []) if (it.get('city') in names)]
        except Exception:
            _CITY_MAP_CACHE = raw or []
    except Exception:
        _CITY_MAP_CACHE = []
    return _CITY_MAP_CACHE
def get_city_spell_by_name(name):
    m = load_city_map()
    for it in m:
        if it.get('city') == name:
            return it.get('short'), it.get('rent_subway')
    return None, None

warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = ['SimHei', 'Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def fetch_subway(Target_city):
    key = Target_city
    it = _SUBWAY_CACHE.get(key)
    if it and (time.time() - it[0] < 7200):
        return it[1]
    
    citylist = None
    for _ in range(3):
        try:
            response = safe_request(
                'https://map.amap.com/service/subway?_1707184339116&srhdata=citylist.json',
                pool_name='subway',
                max_retries=1,
                retry_delay=0.6
            )
            citylist = response.json()
            break
        except Exception:
            if _ < 2:
                time.sleep(0.6)
    
    if not isinstance(citylist, dict) or ('citylist' not in citylist):
        if it:
            return it[1]
        return None, None
    
    spell = ''
    adcode = ''
    for city in citylist['citylist']:
        if city.get('cityname') == Target_city:
            spell = city.get('spell')
            adcode = city.get('adcode')
            break
    
    if not spell or not adcode:
        if it:
            return it[1]
        return None, None
    
    city_url = f'https://map.amap.com/service/subway?_1707184339123&srhdata={adcode}_drw_{spell}.json'
    target_city = None
    
    for _ in range(3):
        try:
            response = safe_request(
                city_url,
                pool_name='subway',
                max_retries=1,
                retry_delay=0.6
            )
            target_city = response.json()
            break
        except Exception:
            if _ < 2:
                time.sleep(0.6)
    if not isinstance(target_city, dict) or ('l' not in target_city):
        if it:
            return it[1]
        return None, None
    
    name_tag = target_city.get('s', Target_city)
    result = {'name': [], 'line': [], 'lon': [], 'lat': []}
    for line in range(len(target_city['l'])):
        for stop in range(len(target_city['l'][line]['st'])):
            result['name'].append(target_city['l'][line]['st'][stop]['n'])
            result['line'].append(target_city['l'][line]['kn'] + target_city['l'][line]['la'])
            lon_lat = target_city['l'][line]['st'][stop]['sl'].split(',')
            result['lon'].append(lon_lat[0])
            result['lat'].append(lon_lat[1])
    df = pd.DataFrame(result)
    df[['lon', 'lat']] = df[['lon', 'lat']].apply(pd.to_numeric)
    geometry = [Point(lon, lat) for lon, lat in zip(df['lon'], df['lat'])]
    gdf = gpd.GeoDataFrame(df[['name', 'line']], geometry=geometry, crs='EPSG:4326')
    gdf['station_id'] = range(1, len(gdf) + 1)
    out = (gdf, name_tag)
    _SUBWAY_CACHE[key] = (time.time(), out)
    return out


def resolve_anjuke_line_codes(city_spell='xm'):
    url = f'https://{city_spell}.zu.anjuke.com/ditie/'
    try:
        html = None
        if firecrawl_enabled():
            html = fetch_html_with_firecrawl(url)
        
        if not html:
            # 使用IP池发送请求
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': f'https://{city_spell}.zu.anjuke.com/ditie/'}
            response = safe_request(
                url,
                pool_name='anjuke',
                max_retries=3,
                retry_delay=1.0,
                headers=headers,
                timeout=10
            )
            html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        mapping = {}
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().strip()
            if 'l' in href and 'ditie' in href:
                m = re.search(r'l(\d+)', href)
                if m:
                    code = f'l{m.group(1)}'
                    n = None
                    mnum = re.search(r'(\d+)号线', text)
                    if mnum:
                        n = int(mnum.group(1))
                    else:
                        for k,v in {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}.items():
                            if f'{k}号线' in text:
                                n = v
                                break
                    if n:
                        mapping[n] = code
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().strip()
            m = re.search(r'dt(\d+)', href)
            if m:
                code = f'dt{m.group(1)}'
                n = None
                mnum = re.search(r'(\d+)号线', text)
                if mnum:
                    n = int(mnum.group(1))
                else:
                    for k,v in {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}.items():
                        if f'{k}号线' in text:
                            n = v
                            break
                if n:
                    mapping[f'dt_{n}'] = code
        return mapping
    except Exception:
        return {}

def collect_anjuke_anchors(city_spell='xm'):
    url = f'https://{city_spell}.zu.anjuke.com/ditie/'
    out = []
    try:
        html = None
        if firecrawl_enabled():
            html = fetch_html_with_firecrawl(url)
        
        if not html:
            # 使用IP池发送请求
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': f'https://{city_spell}.zu.anjuke.com/ditie/'}
            response = safe_request(
                url,
                pool_name='anjuke',
                max_retries=3,
                retry_delay=1.0,
                headers=headers,
                timeout=10
            )
            html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        nodes = soup.select('.sub-items.sub-level1 a') or soup.find_all('a', href=True)
        for a in nodes:
            href = a['href']
            text = a.get_text().strip()
            out.append({'text': text, 'href': href})
    except Exception:
        return out
    return out

def resolve_anjuke_line_hrefs(city_spell='xm'):
    s = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': f'https://{city_spell}.zu.anjuke.com/ditie/'}
    url = f'https://{city_spell}.zu.anjuke.com/ditie/'
    out = {}
    try:
        html = None
        if firecrawl_enabled():
            html = fetch_html_with_firecrawl(url)
        if not html:
            r = s.get(url, headers=headers, timeout=10)
            html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().strip()
            if ('/ditie/' in href) and (('号线' in text) or re.search(r'(\d+)号线', text)):
                n = None
                mnum = re.search(r'(\d+)号线', text)
                if mnum:
                    n = int(mnum.group(1))
                else:
                    for k,v in {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}.items():
                        if f'{k}号线' in text:
                            n = v
                            break
                if n:
                    out[n] = href
    except Exception:
        return out
    return out

def fetch_anjuke_rentals_unified(city_spell='xm', line_number=1, max_pages=5, city_name=None, override_subdomain=None, override_dt_code=None, override_l_code=None):
    s = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}
    if city_name and not override_subdomain:
        short, _rent = get_city_spell_by_name(city_name)
        if isinstance(short, str) and short:
            city_spell = short
    mapping = resolve_anjuke_line_codes(city_spell)
    lcode = override_l_code or mapping.get(line_number)
    dtcode = override_dt_code or mapping.get(f'dt_{line_number}')
    # 仅使用前端页面解析的真实 href 与本地规则
    hrefs = resolve_anjuke_line_hrefs(city_spell)
    urls = []
    if dtcode:
        for p in range(1, max_pages + 1):
            urls.append(f'https://{(override_subdomain or city_spell)}.zu.anjuke.com/ditie/{dtcode}/-p{p}/')
    if hrefs.get(line_number):
        base = hrefs.get(line_number)
        if base:
            if not base.startswith('http'):
                base = f'https://{(override_subdomain or city_spell)}.zu.anjuke.com{base}'
            for p in range(1, max_pages + 1):
                if base.endswith('/'):
                    urls.append(f'{base}-p{p}/')
                else:
                    urls.append(f'{base}/-p{p}/')
    if lcode:
        urls.append(f'https://{(override_subdomain or city_spell)}.zu.anjuke.com/rmss/chuzu-49-{lcode}/')
        urls.append(f'https://{(override_subdomain or city_spell)}.zu.anjuke.com/{lcode}/')
    data = []
    rate_limited = False
    seen = set()
    for u in urls:
        try:
            html_text = None
            if _USE_BROWSER:
                try:
                    from playwright.sync_api import sync_playwright
                    with sync_playwright() as pw:
                        browser = pw.chromium.launch()
                        page = browser.new_page()
                        page.set_extra_http_headers({'User-Agent':'Mozilla/5.0'})
                        page.goto(u, wait_until='domcontentloaded')
                        page.wait_for_timeout(1500)
                        html_text = page.content()
                        browser.close()
                except Exception:
                    html_text = None
            if not html_text:
                try:
                    if firecrawl_enabled():
                        html_fc = fetch_html_with_firecrawl(u)
                        if html_fc:
                            html_text = html_fc
                except Exception:
                    html_text = None
            if not html_text:
                r = s.get(u, headers=headers, timeout=12)
                html_text = r.text
            soup = BeautifulSoup(html_text, 'html.parser')
            txt_all0 = soup.get_text() or ''
            if ('访问过于频繁' in txt_all0) or ('请稍后再试' in txt_all0) or ('验证' in txt_all0):
                rate_limited = True
                break
            scripts = soup.find_all('script')
            blob = None
            for sc in scripts:
                t = sc.get_text() or ''
                if ('__INITIAL_STATE__' in t) or ('__NUXT__' in t) or ('list' in t and 'price' in t):
                    blob = t
                    break
            items = []
            if blob:
                m = re.search(r'(\{[\s\S]*\})', blob)
                if m:
                    raw = m.group(1)
                    try:
                        obj = json.loads(raw)
                        if isinstance(obj, dict):
                            for k in ['list', 'result', 'items']:
                                if k in obj and isinstance(obj[k], list):
                                    items = obj[k]
                                    break
                    except Exception:
                        pass
            if not items:
                cards = soup.select('.zu-itemmod')
                if not cards:
                    cards = soup.select('.item,.list-item,.rent-item')
                for item in cards:
                    title_tag = item.find('h3')
                    price_tag = item.find('strong', class_='price')
                    detail_tag = item.find('p', class_='details-item')
                    address_tag = item.find('address', class_='details-item')
                    title = title_tag.get_text().strip() if title_tag else None
                    price = price_tag.get_text().strip() if price_tag else None
                    area = None
                    if detail_tag:
                        strong_tags = detail_tag.find_all('b', class_='strongbox')
                        if len(strong_tags) >= 3:
                            area = strong_tags[2].get_text().strip()
                        if area is None:
                            txt = detail_tag.get_text().strip()
                            m2 = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*平米', txt) or re.search(r'([0-9]+(?:\.[0-9]+)?)\s*m²', txt) or re.search(r'([0-9]+(?:\.[0-9]+)?)\s*m', txt)
                            if m2:
                                area = m2.group(1)
                    address = None
                    if address_tag:
                        a = address_tag.find('a')
                        address = a.get_text().strip() if a else None
                    distance = None
                    bot_tag = item.find('p', class_='bot-tag')
                    if bot_tag:
                        spans = bot_tag.find_all('span', class_='cls-common')
                        for sp in spans:
                            tx = sp.get_text().strip()
                            if '距' in tx:
                                distance = tx
                                break
                    if distance is None:
                        txt_all = item.get_text().strip()
                        m3 = re.search(r'距[^\n]{1,10}地铁[^\n]{0,20}([0-9]+)m', txt_all)
                        if m3:
                            distance = f'距地铁 {m3.group(1)}m'
                    if title and price and area:
                        key = (title, price, area, address)
                        if key in seen:
                            continue
                        seen.add(key)
                        data.append({
                            'title': title,
                            'price': float(price),
                            'area': float(area),
                            'address': address,
                            'subway_distance': distance,
                            'price_per_sqm': float(price) / float(area) if area else None
                        })
            time.sleep(random.uniform(1.0, 2.2))
        except Exception:
            continue
    df = pd.DataFrame(data)
    if rate_limited and len(df) == 0:
        raise Exception('RATE_LIMIT')
    if 'subway_distance' not in df.columns:
        df['subway_distance'] = None
    if 'price' not in df.columns:
        df['price'] = None
    if 'area' not in df.columns:
        df['area'] = None
    if 'price_per_sqm' not in df.columns:
        df['price_per_sqm'] = None
    if 'title' not in df.columns:
        df['title'] = None
    if 'address' not in df.columns:
        df['address'] = None
    df['distance_km'] = df['subway_distance'].apply(lambda x: float(re.search(r'(\d+)m', str(x)).group(1)) / 1000 if pd.notna(x) and re.search(r'(\d+)m', str(x)) else None)
    if len(df) == 0:
        df = fetch_anjuke_rentals_mobile_json(city_spell, line_number, max_pages, export_csv=False)
    return df

def fetch_anjuke_rentals_mobile_json(city_spell='xm', line_number=2, max_pages=5, export_csv=False):
    s = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}
    mapping = resolve_anjuke_line_codes(city_spell)
    lcode = mapping.get(line_number)
    dtcode = mapping.get(f'dt_{line_number}')
    hrefs = resolve_anjuke_line_hrefs(city_spell)
    urls = []
    if lcode:
        urls.append(f'https://{city_spell}.zu.anjuke.com/rmss/chuzu-49-{lcode}/')
        urls.append(f'https://{city_spell}.zu.anjuke.com/{lcode}/')
    if dtcode:
        for p in range(1, max_pages + 1):
            urls.append(f'https://{city_spell}.zu.anjuke.com/ditie/{dtcode}/-p{p}/')
    if hrefs.get(line_number):
        base = hrefs.get(line_number)
        if base and not base.startswith('http'):
            base = f'https://{city_spell}.zu.anjuke.com{base}'
        if base:
            for p in range(1, max_pages + 1):
                if base.endswith('/'):
                    urls.append(f'{base}-p{p}/')
                else:
                    urls.append(f'{base}/-p{p}/')
    data = []
    seen = set()
    for u in urls:
        try:
            r = s.get(u, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            scripts = soup.find_all('script')
            blob = None
            for sc in scripts:
                t = sc.get_text() or ''
                if ('__INITIAL_STATE__' in t) or ('__NUXT__' in t) or ('list' in t and 'price' in t):
                    blob = t
                    break
            items = []
            if blob:
                m = re.search(r'(\{[\s\S]*\})', blob)
                if m:
                    raw = m.group(1)
                    try:
                        obj = json.loads(raw)
                        if isinstance(obj, dict):
                            for k in ['list', 'result', 'items']:
                                if k in obj and isinstance(obj[k], list):
                                    items = obj[k]
                                    break
                    except Exception:
                        pass
            if not items:
                cards = soup.select('.zu-itemmod')
                for item in cards:
                    title_tag = item.find('h3')
                    price_tag = item.find('strong', class_='price')
                    detail_tag = item.find('p', class_='details-item')
                    address_tag = item.find('address', class_='details-item')
                    title = title_tag.get_text().strip() if title_tag else None
                    price = price_tag.get_text().strip() if price_tag else None
                    area = None
                    if detail_tag:
                        strong_tags = detail_tag.find_all('b', class_='strongbox')
                        if len(strong_tags) >= 3:
                            area = strong_tags[2].get_text().strip()
                        if area is None:
                            txt = detail_tag.get_text().strip()
                            m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*平米', txt) or re.search(r'([0-9]+(?:\.[0-9]+)?)\s*m²', txt)
                            if m:
                                area = m.group(1)
                    address = None
                    if address_tag:
                        a = address_tag.find('a')
                        address = a.get_text().strip() if a else None
                    distance = None
                    bot_tag = item.find('p', class_='bot-tag')
                    if bot_tag:
                        spans = bot_tag.find_all('span', class_='cls-common')
                        for sp in spans:
                            tx = sp.get_text().strip()
                            if '距' in tx:
                                distance = tx
                                break
                    if title and price and area:
                        key = (title, price, area, address)
                        if key in seen:
                            continue
                        seen.add(key)
                        data.append({
                            'title': title,
                            'price': float(price),
                            'area': float(area),
                            'address': address,
                            'subway_distance': distance,
                            'price_per_sqm': float(price) / float(area) if area else None
                        })
        except Exception:
            continue
    df = pd.DataFrame(data)
    if 'subway_distance' not in df.columns:
        df['subway_distance'] = None
    if 'price' not in df.columns:
        df['price'] = None
    if 'area' not in df.columns:
        df['area'] = None
    if 'price_per_sqm' not in df.columns:
        df['price_per_sqm'] = None
    if 'title' not in df.columns:
        df['title'] = None
    if 'address' not in df.columns:
        df['address'] = None
    if 'subway_distance' in df.columns:
        df['distance_km'] = df['subway_distance'].apply(lambda x: float(re.search(r'(\d+)m', str(x)).group(1)) / 1000 if pd.notna(x) and re.search(r'(\d+)m', str(x)) else None)
    else:
        df['distance_km'] = None
    if export_csv:
        df.to_csv('AJK.csv', index=False, encoding='utf-8-sig')
    return df

class SubwayRentalVisualizer:
    def __init__(self, subway_gdf=None, rental_df=None, city_tag=None, line_number=1):
        self.output_dir = "地铁租房指数可视化结果"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.subway_data = subway_gdf
        self.rental_data = rental_df
        self.analysis_results = None
        self.nearby_rentals_by_station = {}
        self.city_tag = city_tag or ''
        self.line_number = line_number
        numerals = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九', 10: '十'}
        cn = numerals.get(self.line_number, str(self.line_number))
        self.line_label = f"地铁{cn}号线"
        self.line_patterns = [
            f"{self.line_number}号线",
            f"地铁{self.line_number}号线",
            f"{cn}号线",
            f"地铁{cn}号线",
        ]

    def _load_subway_data(self):
        gdf = self.subway_data
        if gdf is None:
            return None
        if 'lon' not in gdf.columns:
            gdf['lon'] = gdf.geometry.x
        if 'lat' not in gdf.columns:
            gdf['lat'] = gdf.geometry.y
        return gdf

    def _extract_line_stations(self):
        if self.subway_data is None:
            return None
        stations = self.subway_data[self.subway_data['line'].str.contains('|'.join(self.line_patterns), na=False)].copy()
        return stations
    
    def _load_rental_data(self):
        return self.rental_data
    
    
    
    def analyze_rental_around_stations(self):
        if self.line_stations is None:
            return
        if self.rental_data is None:
            return
        results = []
        for idx, station in self.line_stations.iterrows():
            station_name = station['name']
            station_lat = station['lat']
            station_lon = station['lon']
            nearby_rentals = []
            if 'subway_distance' in self.rental_data.columns and 'distance_km' in self.rental_data.columns:
                station_rentals = self.rental_data[(
                    self.rental_data['subway_distance'].str.contains(station_name, na=False)) &
                    (self.rental_data['distance_km'] <= 1.0)
                ].copy()
            else:
                station_rentals = pd.DataFrame(columns=['price','area','price_per_sqm','distance_km','title','address'])
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
        self.analysis_results = pd.DataFrame(results)
        return self.analysis_results
    
    def visualize_rental_index(self):
        if self.analysis_results is None or len(self.analysis_results) == 0:
            return {}
        line_order = self.line_stations['name'].tolist()
        valid_stations = [s for s in line_order if s in self.analysis_results['station'].values]
        valid_stations = list(dict.fromkeys(valid_stations))
        self.analysis_results['station'] = pd.Categorical(self.analysis_results['station'], categories=valid_stations, ordered=True)
        sorted_by_line = self.analysis_results.sort_values('station')
        chart_files = {}
        fig, axes = plt.subplots(2, 2, figsize=(18, 14), constrained_layout=True)
        ax = axes[0][0]
        sorted_df = self.analysis_results.sort_values('min_price_per_sqm', ascending=False)
        sns.barplot(data=sorted_df, x='min_price_per_sqm', y='station', palette='viridis', ax=ax)
        ax.set_title(f'{self.city_tag}{self.line_label} - 最低单价 Top', fontsize=16)
        ax.set_xlabel('最低每平米月租金（元）', fontsize=12)
        ax.set_ylabel('站点', fontsize=12)
        ax.grid(axis='x', alpha=0.2)
        ax.bar_label(ax.containers[0], fmt='%.1f', padding=3)
        ax = axes[0][1]
        sorted_count_df = self.analysis_results.sort_values('rental_count', ascending=False)
        bars = sns.barplot(data=sorted_count_df, x='rental_count', y='station', palette='magma', ax=ax)
        ax.set_title(f'{self.city_tag}{self.line_label} - 房源数 Top', fontsize=16)
        ax.set_xlabel('房源数量（套）', fontsize=12)
        ax.set_ylabel('站点', fontsize=12)
        ax.grid(axis='x', alpha=0.2)
        bars.bar_label(bars.containers[0], fmt='%d', padding=3)
        max_count = sorted_count_df['rental_count'].max()
        ax.set_xlim(0, max_count * 1.15)
        ax = axes[1][0]
        sns.barplot(data=sorted_by_line, x='station', y='avg_price_per_sqm', palette='coolwarm', ax=ax)
        ax.set_title(f'{self.city_tag}{self.line_label} - 平均单价', fontsize=16)
        ax.set_xlabel('站点', fontsize=12)
        ax.set_ylabel('平均每平米月租金（元）', fontsize=12)
        ax.grid(axis='y', alpha=0.2)
        ax.tick_params(axis='x', labelrotation=45)
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f', padding=2)
        ax = axes[1][1]
        boxplot_data = []
        for _, station_rentals in self.nearby_rentals_by_station.items():
            for rental in station_rentals:
                if 'price_per_sqm' in rental and rental['price_per_sqm'] is not None:
                    boxplot_data.append({'station': rental['station'], 'price_per_sqm': rental['price_per_sqm']})
        boxplot_df = pd.DataFrame(boxplot_data)
        if not boxplot_df.empty:
            boxplot_df['station'] = pd.Categorical(boxplot_df['station'], categories=valid_stations, ordered=True)
            sns.boxplot(data=boxplot_df, y='station', x='price_per_sqm', palette='Set2', ax=ax)
            ax.set_title(f'{self.city_tag}{self.line_label} - 单价分布', fontsize=16)
            ax.set_xlabel('每平米月租金（元）', fontsize=12)
            ax.set_ylabel('站点', fontsize=12)
            ax.grid(axis='x', alpha=0.2)
            q1 = boxplot_df['price_per_sqm'].quantile(0.25)
            q3 = boxplot_df['price_per_sqm'].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            ax.set_xlim(max(0, lower_bound - 5), upper_bound + 10)
        else:
            ax.text(0.5, 0.5, '无足够数据生成箱线图', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        combined_path = os.path.join(self.output_dir, f"{self.city_tag}{self.line_label}租房指数可视化.png")
        fig.savefig(combined_path, dpi=300, bbox_inches='tight')
        chart_files['combined'] = combined_path
        plt.close(fig)
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        sns.barplot(data=sorted_df, x='min_price_per_sqm', y='station', palette='viridis', ax=ax1)
        ax1.set_title(f'{self.city_tag}{self.line_label} - 最低单价 Top', fontsize=16)
        ax1.set_xlabel('最低每平米月租金（元）', fontsize=12)
        ax1.set_ylabel('站点', fontsize=12)
        ax1.grid(axis='x', alpha=0.2)
        ax1.bar_label(ax1.containers[0], fmt='%.1f', padding=3)
        path1 = os.path.join(self.output_dir, f"{self.city_tag}{self.line_label}_最低单价Top.png")
        fig1.savefig(path1, dpi=300, bbox_inches='tight')
        chart_files['min_top'] = path1
        plt.close(fig1)
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        bars2 = sns.barplot(data=sorted_count_df, x='rental_count', y='station', palette='magma', ax=ax2)
        ax2.set_title(f'{self.city_tag}{self.line_label} - 房源数 Top', fontsize=16)
        ax2.set_xlabel('房源数量（套）', fontsize=12)
        ax2.set_ylabel('站点', fontsize=12)
        ax2.grid(axis='x', alpha=0.2)
        bars2.bar_label(bars2.containers[0], fmt='%d', padding=3)
        ax2.set_xlim(0, max_count * 1.15)
        path2 = os.path.join(self.output_dir, f"{self.city_tag}{self.line_label}_房源数Top.png")
        fig2.savefig(path2, dpi=300, bbox_inches='tight')
        chart_files['count_top'] = path2
        plt.close(fig2)
        fig3, ax3 = plt.subplots(figsize=(12, 8))
        sns.barplot(data=sorted_by_line, x='station', y='avg_price_per_sqm', palette='coolwarm', ax=ax3)
        ax3.set_title(f'{self.city_tag}{self.line_label} - 平均单价', fontsize=16)
        ax3.set_xlabel('站点', fontsize=12)
        ax3.set_ylabel('平均每平米月租金（元）', fontsize=12)
        ax3.grid(axis='y', alpha=0.2)
        ax3.tick_params(axis='x', labelrotation=45)
        for container in ax3.containers:
            ax3.bar_label(container, fmt='%.1f', padding=2)
        path3 = os.path.join(self.output_dir, f"{self.city_tag}{self.line_label}_平均单价.png")
        fig3.savefig(path3, dpi=300, bbox_inches='tight')
        chart_files['avg_price'] = path3
        plt.close(fig3)
        fig4, ax4 = plt.subplots(figsize=(10, 8))
        if not boxplot_df.empty:
            sns.boxplot(data=boxplot_df, y='station', x='price_per_sqm', palette='Set2', ax=ax4)
            ax4.set_title(f'{self.city_tag}{self.line_label} - 单价分布', fontsize=16)
            ax4.set_xlabel('每平米月租金（元）', fontsize=12)
            ax4.set_ylabel('站点', fontsize=12)
            ax4.grid(axis='x', alpha=0.2)
            q1 = boxplot_df['price_per_sqm'].quantile(0.25)
            q3 = boxplot_df['price_per_sqm'].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            ax4.set_xlim(max(0, lower_bound - 5), upper_bound + 10)
        else:
            ax4.text(0.5, 0.5, '无足够数据生成箱线图', ha='center', va='center', transform=ax4.transAxes, fontsize=14)
        path4 = os.path.join(self.output_dir, f"{self.city_tag}{self.line_label}_单价分布.png")
        fig4.savefig(path4, dpi=300, bbox_inches='tight')
        chart_files['boxplot'] = path4
        plt.close(fig4)
        return chart_files
    
    def run_full_analysis(self):
        self.subway_data = self._load_subway_data()
        self.line_stations = self._extract_line_stations()
        self.rental_data = self._load_rental_data()
        if self.line_stations is None:
            return
        self.analyze_rental_around_stations()
        self.visualize_rental_index()
