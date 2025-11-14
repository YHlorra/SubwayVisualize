from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os, io, base64, time
import pandas as pd
import requests
import re
from services.subway_visualize import (
    fetch_subway,
    SubwayRentalVisualizer,
    fetch_anjuke_rentals_unified,
    get_city_spell_by_name,
)

app = Flask(__name__)
CORS(app)

CITY_CACHE = {"ts": 0, "list": []}

def _fetch_cities():
    try:
        s = requests.Session()
        j = s.get('https://map.amap.com/service/subway?_1707184339116&srhdata=citylist.json', timeout=10).json()
        out = []
        for c in j.get('citylist', []):
            out.append({"name": c.get("cityname"), "spell": c.get("spell"), "adcode": c.get("adcode")})
        return [x for x in out if x.get("name")]
    except Exception:
        return []

def _get_cities_cached():
    now = time.time()
    if CITY_CACHE["list"] and now - CITY_CACHE["ts"] < 7200:
        return CITY_CACHE["list"]
    lst = _fetch_cities()
    if lst:
        CITY_CACHE["list"] = lst
        CITY_CACHE["ts"] = now
    return CITY_CACHE["list"]

def _normalize_city_name(name: str) -> str:
    nm = (name or '').strip()
    if not nm:
        return '厦门市'
    lst = _get_cities_cached()
    names = [c.get('name') for c in lst if c.get('name')]
    if nm in names:
        return nm
    if (not nm.endswith('市')) and ((nm + '市') in names):
        return nm + '市'
    base = nm[:-1] if nm.endswith('市') else nm
    for n in names:
        if n.startswith(base):
            return n
    if not nm.endswith('市'):
        return nm + '市'
    return nm

def _resolve_spell_by_name(name):
    nm = _normalize_city_name(name)
    short, _ = get_city_spell_by_name(nm)
    if isinstance(short, str) and short:
        return short
    if nm.endswith('市'):
        short2, _ = get_city_spell_by_name(nm[:-1])
        if isinstance(short2, str) and short2:
            return short2
    return None

def _guess_anjuke_subdomain(city_name):
    override = _resolve_spell_by_name(city_name)
    if override:
        return override
    for c in _get_cities_cached():
        if c.get("name") == city_name:
            spell = c.get("spell") or ""
            if spell:
                return spell
            break
    return None

@app.route("/api/cities", methods=["GET"])
def list_cities():
    data = _get_cities_cached()
    return jsonify(data)

@app.route("/api/subway", methods=["GET", "POST"])
def get_subway():
    city_raw = (request.args.get("city") or (request.json or {}).get("city") or "厦门市")
    city = _normalize_city_name(city_raw)
    gdf, city_tag = fetch_subway(city)
    if gdf is None:
        return jsonify({"error": "城市名称不正确或未开通地铁"}), 400
    if "lon" not in gdf.columns:
        gdf["lon"] = gdf.geometry.x
    if "lat" not in gdf.columns:
        gdf["lat"] = gdf.geometry.y
    lines = gdf["line"].drop_duplicates().tolist()
    stations = []
    for _, row in gdf.iterrows():
        lon_val = row["lon"] if "lon" in gdf.columns else row.geometry.x
        lat_val = row["lat"] if "lat" in gdf.columns else row.geometry.y
        stations.append({
            "name": row["name"],
            "line": row["line"],
            "lon": float(lon_val),
            "lat": float(lat_val),
        })
    city_spell = _resolve_spell_by_name(city)
    return jsonify({"city_tag": city_tag, "city_spell": city_spell, "lines": lines, "stations": stations})

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    city = _normalize_city_name(data.get("city", "厦门市"))
    line_number = int(data.get("line", 2))
    max_pages = int(data.get("pages", 10))
    short0, _rent0 = get_city_spell_by_name(city)
    if not short0 and city.endswith('市'):
        short0, _rent0 = get_city_spell_by_name(city[:-1])
    city_spell = (short0 or (data.get("city_spell") or _resolve_spell_by_name(city) or ""))
    print("ANALYZE_CITY", city)

    gdf, city_tag = fetch_subway(city)
    if gdf is None:
        try:
            from urllib.parse import quote
            r0 = requests.get(f'http://127.0.0.1:5000/api/subway?city={quote(city)}', timeout=5)
            j0 = r0.json()
            st = j0.get('stations') or []
            df0 = pd.DataFrame(st)
            from shapely.geometry import Point
            import geopandas as gpd
            geometry0 = [Point(x, y) for x, y in zip(df0['lon'], df0['lat'])]
            gdf = gpd.GeoDataFrame(df0[['name','line']], geometry=geometry0, crs='EPSG:4326')
            gdf['station_id'] = range(1, len(gdf) + 1)
            city_tag = j0.get('city_tag') or city
        except Exception:
            return jsonify({"error": "城市无效或未开通地铁"}), 400
    if not city_spell:
        print("ANALYZE_ERR", "未识别到城市拼写", city)
        return jsonify({"error": "未识别到城市代码，请从列表选择城市后重试"}), 400
    try:
        rentals_df = fetch_anjuke_rentals_unified(
            city_spell,
            line_number,
            max_pages,
            city_name=city,
        )
    except Exception as e:
        em = str(e) if e else ""
        print("ANALYZE_ERR", "安居客数据抓取失败", em)
        if "RATE_LIMIT" in em:
            return jsonify({"error": "访问过于频繁，请稍后再试或降低抓取页数"}), 429
        return jsonify({"error": "安居客抓取失败，请稍后再试或减少页数"}), 400
    vis = SubwayRentalVisualizer(subway_gdf=gdf, rental_df=rentals_df, city_tag=city_tag, line_number=line_number)
    vis.run_full_analysis()
    results = vis.analysis_results
    if results is None or len(results) == 0:
        try:
            n = 0
            if isinstance(rentals_df, pd.DataFrame):
                n = len(rentals_df)
            print("ANALYZE_ERR", "未获取到有效房源数据", "df_len", n, "city", city, "spell", city_spell, "line", line_number)
        except Exception:
            pass
        return jsonify({"error": "未获取到有效房源数据：可能访问频率过高或线路入口暂无数据。请减少抓取页数、稍后再试或更换线路"}), 400
    chart_files = vis.visualize_rental_index()
    combined_path = chart_files.get("combined")
    charts = []
    for name, path in chart_files.items():
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        charts.append({"name": os.path.basename(path), "key": name, "b64": b64})
    combined_b64 = None
    combined_name = None
    if combined_path and os.path.exists(combined_path):
        with open(combined_path, "rb") as f:
            combined_b64 = base64.b64encode(f.read()).decode()
        combined_name = os.path.basename(combined_path)
    return jsonify({
        "table": results.to_dict(orient="records"),
        "charts": charts,
        "chart_b64": combined_b64,
        "chart_name": combined_name
    })



@app.route("/api/download/chart", methods=["POST"])
def download_chart():
    chart_b64 = request.json.get("chart_b64")
    chart_name = request.json.get("chart_name", "chart.png")
    img_bytes = base64.b64decode(chart_b64)
    return send_file(
        io.BytesIO(img_bytes),
        mimetype="image/png",
        as_attachment=True,
        download_name=chart_name
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/index.html")
def home_alias():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
