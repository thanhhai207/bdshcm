"""
Generate a self-contained HTML dashboard from crawled data.
Usage: python generate_dashboard.py
"""
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.dirname(__file__)


def load_data():
    """Load the latest crawled data."""
    json_path = os.path.join(DATA_DIR, "listings_latest.json")
    csv_path = os.path.join(DATA_DIR, "listings_latest.csv")

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        raise FileNotFoundError("No data found. Run crawl.py first.")


def compute_analytics(df):
    """Compute all analytics needed for the dashboard."""
    analytics = {}

    # --- Overview stats ---
    analytics["total_listings"] = len(df)
    analytics["total_districts"] = df["district"].nunique()
    analytics["sources"] = df["source"].value_counts().to_dict()
    analytics["avg_price"] = round(df["price_billion"].mean(), 2)
    analytics["median_price"] = round(df["price_billion"].median(), 2)

    # --- Price per m² by district ---
    valid = df.dropna(subset=["price_per_m2"])
    district_stats = valid.groupby("district").agg(
        avg_price_m2=("price_per_m2", "mean"),
        median_price_m2=("price_per_m2", "median"),
        min_price_m2=("price_per_m2", "min"),
        max_price_m2=("price_per_m2", "max"),
        avg_price=("price_billion", "mean"),
        median_price=("price_billion", "median"),
        avg_area=("area_m2", "mean"),
        count=("price_per_m2", "count"),
    ).round(0).reset_index()

    district_stats = district_stats.sort_values("median_price_m2", ascending=False)
    analytics["district_stats"] = district_stats.to_dict(orient="records")

    # --- Property type breakdown ---
    type_stats = df.groupby("property_type").agg(
        count=("price_billion", "count"),
        avg_price=("price_billion", "mean"),
    ).round(2).reset_index()
    analytics["type_stats"] = type_stats.to_dict(orient="records")

    # --- Source breakdown ---
    source_stats = df.groupby("source").agg(
        count=("price_billion", "count"),
        avg_price=("price_billion", "mean"),
    ).round(2).reset_index()
    analytics["source_stats"] = source_stats.to_dict(orient="records")

    # --- Cheapest listings per district (top 5 per district) ---
    cheapest = []
    for district in df["district"].unique():
        d_df = df[df["district"] == district].nsmallest(5, "price_billion")
        for _, row in d_df.iterrows():
            cheapest.append({
                "district": row["district"],
                "title": row["title"][:80],
                "price_billion": row["price_billion"],
                "area_m2": row.get("area_m2"),
                "price_per_m2": row.get("price_per_m2"),
                "property_type": row.get("property_type", ""),
                "source": row.get("source", ""),
                "url": row.get("url", ""),
            })
    analytics["cheapest_listings"] = cheapest

    # --- Outlier detection (IQR method per district) ---
    outliers = []
    for district in valid["district"].unique():
        d_data = valid[valid["district"] == district]["price_per_m2"]
        if len(d_data) < 5:
            continue
        q1 = d_data.quantile(0.25)
        q3 = d_data.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        d_outliers = valid[(valid["district"] == district) &
                           ((valid["price_per_m2"] < lower) | (valid["price_per_m2"] > upper))]
        for _, row in d_outliers.iterrows():
            outliers.append({
                "district": district,
                "title": row["title"][:80],
                "price_billion": row["price_billion"],
                "price_per_m2": row["price_per_m2"],
                "type": "below" if row["price_per_m2"] < lower else "above",
            })
    analytics["outliers"] = outliers[:50]  # Limit to 50

    # --- Price distribution for box plot ---
    box_data = {}
    for district in valid["district"].unique():
        d_data = valid[valid["district"] == district]["price_per_m2"].dropna()
        if len(d_data) >= 3:
            box_data[district] = {
                "min": float(d_data.min()),
                "q1": float(d_data.quantile(0.25)),
                "median": float(d_data.median()),
                "q3": float(d_data.quantile(0.75)),
                "max": float(d_data.max()),
                "mean": float(d_data.mean()),
            }
    analytics["box_data"] = box_data

    # --- All listings as data points (for scatter plot) ---
    all_points = []
    for _, row in df.iterrows():
        area = row.get("area_m2")
        ppm2 = row.get("price_per_m2")
        if pd.notna(area) and pd.notna(ppm2) and area > 0 and ppm2 > 0:
            all_points.append({
                "title": str(row.get("title", ""))[:100],
                "price_billion": float(row["price_billion"]),
                "area_m2": float(area),
                "price_per_m2": float(ppm2),
                "district": row.get("district", ""),
                "property_type": row.get("property_type", ""),
                "source": row.get("source", ""),
                "url": row.get("url", ""),
                "address": str(row.get("address", ""))[:80],
            })
    analytics["all_points"] = all_points

    analytics["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return analytics


def generate_html(analytics):
    """Generate the full HTML dashboard."""

    data_json = json.dumps(analytics, ensure_ascii=False, default=str)

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HCMC Real Estate Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    line-height: 1.6;
}}
.header {{
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-bottom: 1px solid #334155;
    padding: 24px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}}
.header h1 {{
    font-size: 1.75rem;
    font-weight: 700;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.header .meta {{
    font-size: 0.85rem;
    color: #94a3b8;
}}
.container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px;
}}
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
}}
.stat-card {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}}
.stat-card .value {{
    font-size: 2rem;
    font-weight: 700;
    color: #38bdf8;
}}
.stat-card .label {{
    font-size: 0.85rem;
    color: #94a3b8;
    margin-top: 4px;
}}
.chart-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 32px;
}}
.chart-card {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 24px;
}}
.chart-card.full {{
    grid-column: 1 / -1;
}}
.chart-card h2 {{
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 16px;
    color: #f1f5f9;
}}
.chart-container {{
    position: relative;
    width: 100%;
    max-height: 450px;
}}
/* Filters */
.filters {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 24px;
    align-items: center;
}}
.filters label {{
    font-size: 0.85rem;
    color: #94a3b8;
}}
.filters select, .filters input {{
    background: #1e293b;
    border: 1px solid #475569;
    color: #e2e8f0;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.9rem;
}}
.filters select:focus, .filters input:focus {{
    outline: none;
    border-color: #38bdf8;
}}
/* Table */
.table-wrapper {{
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid #334155;
    margin-bottom: 32px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}}
thead th {{
    background: #1e293b;
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    color: #94a3b8;
    border-bottom: 1px solid #334155;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
}}
thead th:hover {{
    color: #38bdf8;
}}
thead th.sorted-asc::after {{ content: " ▲"; color: #38bdf8; }}
thead th.sorted-desc::after {{ content: " ▼"; color: #38bdf8; }}
tbody td {{
    padding: 10px 16px;
    border-bottom: 1px solid #1e293b;
}}
tbody tr {{
    background: #0f172a;
}}
tbody tr:hover {{
    background: #1e293b;
}}
tbody tr.highlight {{
    background: #172554;
    border-left: 3px solid #38bdf8;
}}
a {{ color: #38bdf8; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}}
.badge-house {{ background: #164e63; color: #67e8f9; }}
.badge-apartment {{ background: #1e3a5f; color: #93c5fd; }}
.badge-land {{ background: #365314; color: #a3e635; }}
.badge-villa {{ background: #4c1d95; color: #c4b5fd; }}
.badge-other {{ background: #374151; color: #9ca3af; }}
.badge-below {{ background: #065f46; color: #6ee7b7; }}
.badge-above {{ background: #7f1d1d; color: #fca5a5; }}
.tabs {{
    display: flex;
    gap: 4px;
    margin-bottom: 20px;
    border-bottom: 1px solid #334155;
    padding-bottom: 0;
}}
.tab {{
    padding: 10px 20px;
    cursor: pointer;
    border-radius: 8px 8px 0 0;
    font-weight: 500;
    font-size: 0.9rem;
    color: #94a3b8;
    transition: all 0.2s;
    border: 1px solid transparent;
    border-bottom: none;
    margin-bottom: -1px;
}}
.tab:hover {{ color: #e2e8f0; background: #1e293b; }}
.tab.active {{
    background: #1e293b;
    color: #38bdf8;
    border-color: #334155;
    border-bottom-color: #1e293b;
}}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.section-title {{
    font-size: 1.3rem;
    font-weight: 700;
    margin: 32px 0 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid #334155;
}}
#pointPopup a.popup-link {{
    display: inline-block;
    margin-top: 12px;
    padding: 8px 20px;
    background: #38bdf8;
    color: #0f172a;
    font-weight: 600;
    border-radius: 8px;
    text-decoration: none;
    transition: background 0.2s;
}}
#pointPopup a.popup-link:hover {{ background: #7dd3fc; }}
.legend-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px 16px;
    margin-top: 12px;
    padding: 12px;
    background: #0f172a;
    border-radius: 8px;
}}
.legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    color: #94a3b8;
    cursor: pointer;
    opacity: 1;
    transition: opacity 0.2s;
}}
.legend-item.dimmed {{ opacity: 0.3; }}
.legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}}
@media (max-width: 768px) {{
    .chart-grid {{ grid-template-columns: 1fr; }}
    .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .header {{ padding: 16px; }}
    .container {{ padding: 16px; }}
}}
</style>
</head>
<body>

<div class="header">
    <div>
        <h1>HCMC Real Estate Dashboard</h1>
        <div class="meta">Ho Chi Minh City Property Price Analysis</div>
    </div>
    <div class="meta" id="genTime"></div>
</div>

<div class="container">
    <!-- Stats Overview -->
    <div class="stats-grid" id="statsGrid"></div>

    <!-- Tabs -->
    <div class="tabs" id="mainTabs">
        <div class="tab active" data-tab="distribution">Distribution</div>
        <div class="tab" data-tab="overview">Overview</div>
        <div class="tab" data-tab="compare">District Compare</div>
        <div class="tab" data-tab="cheapest">Cheapest Listings</div>
        <div class="tab" data-tab="outliers">Outlier Detection</div>
    </div>

    <!-- Tab: Distribution (scatter plot — each listing is a data point) -->
    <div class="tab-content active" id="tab-distribution">
        <div class="filters">
            <label>District:</label>
            <select id="scatterDistrictFilter"><option value="all">All Districts</option></select>
            <label>Type:</label>
            <select id="scatterTypeFilter">
                <option value="all">All Types</option>
                <option value="house">House</option>
                <option value="apartment">Apartment</option>
                <option value="land">Land</option>
                <option value="villa">Villa</option>
            </select>
            <label>Source:</label>
            <select id="scatterSourceFilter"><option value="all">All Sources</option></select>
            <label>Color by:</label>
            <select id="scatterColorBy">
                <option value="district">District</option>
                <option value="property_type">Property Type</option>
                <option value="source">Source</option>
            </select>
            <label>X axis:</label>
            <select id="scatterXAxis">
                <option value="area_m2">Area (m²)</option>
                <option value="price_billion">Price (tỷ)</option>
            </select>
            <label>Y axis:</label>
            <select id="scatterYAxis">
                <option value="price_per_m2">Price per m²</option>
                <option value="price_billion">Price (tỷ)</option>
                <option value="area_m2">Area (m²)</option>
            </select>
        </div>
        <p style="color:#94a3b8; margin-bottom:8px; font-size:0.85rem;">
            Each dot is one listing. Click any point to open it on the original website. Hover for details.
        </p>
        <div class="chart-card full" style="position:relative;">
            <h2 id="scatterTitle">Price per m² vs Area — All Districts</h2>
            <div style="position:relative; height:550px;">
                <canvas id="chartScatter"></canvas>
            </div>
            <div id="scatterPointCount" style="text-align:right; font-size:0.8rem; color:#64748b; margin-top:8px;"></div>
        </div>
        <!-- Detail popup on click -->
        <div id="pointPopup" style="display:none; position:fixed; z-index:999; background:#1e293b; border:1px solid #38bdf8; border-radius:12px; padding:20px; max-width:420px; box-shadow: 0 8px 32px #00000088;">
            <div id="popupClose" style="position:absolute; top:8px; right:14px; cursor:pointer; color:#94a3b8; font-size:1.2rem;">&times;</div>
            <div id="popupContent"></div>
        </div>
    </div>

    <!-- Tab: Overview -->
    <div class="tab-content" id="tab-overview">
        <div class="chart-grid">
            <div class="chart-card full">
                <h2>Median Price per m² by District (VND)</h2>
                <div class="chart-container"><canvas id="chartDistrictPrice"></canvas></div>
            </div>
            <div class="chart-card">
                <h2>Listings by Property Type</h2>
                <div class="chart-container"><canvas id="chartPropType"></canvas></div>
            </div>
            <div class="chart-card">
                <h2>Listings by Source</h2>
                <div class="chart-container"><canvas id="chartSource"></canvas></div>
            </div>
            <div class="chart-card full">
                <h2>Price Range by District (min / Q1 / median / Q3 / max)</h2>
                <div class="chart-container"><canvas id="chartBoxPlot"></canvas></div>
            </div>
        </div>
    </div>

    <!-- Tab: District Compare -->
    <div class="tab-content" id="tab-compare">
        <div class="filters">
            <label>Compare:</label>
            <select id="compareDistrict1"></select>
            <span style="color:#64748b">vs</span>
            <select id="compareDistrict2"></select>
        </div>
        <div class="chart-grid">
            <div class="chart-card full">
                <h2>Side-by-Side Comparison</h2>
                <div class="chart-container"><canvas id="chartCompare"></canvas></div>
            </div>
        </div>
        <div id="compareTable"></div>
    </div>

    <!-- Tab: Cheapest Listings -->
    <div class="tab-content" id="tab-cheapest">
        <div class="filters">
            <label>District:</label>
            <select id="cheapDistrictFilter"><option value="all">All Districts</option></select>
            <label>Type:</label>
            <select id="cheapTypeFilter">
                <option value="all">All Types</option>
                <option value="house">House</option>
                <option value="apartment">Apartment</option>
                <option value="land">Land</option>
                <option value="villa">Villa</option>
            </select>
            <label>Max Price:</label>
            <input type="number" id="cheapMaxPrice" placeholder="e.g. 5 (tỷ)" step="0.5" style="width:120px">
        </div>
        <div class="table-wrapper">
            <table id="cheapTable">
                <thead>
                    <tr>
                        <th data-sort="district">District</th>
                        <th data-sort="title">Title</th>
                        <th data-sort="price_billion">Price (tỷ)</th>
                        <th data-sort="area_m2">Area (m²)</th>
                        <th data-sort="price_per_m2">Price/m²</th>
                        <th data-sort="property_type">Type</th>
                        <th data-sort="source">Source</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <!-- Tab: Outliers -->
    <div class="tab-content" id="tab-outliers">
        <p style="color:#94a3b8; margin-bottom:16px;">
            Properties with price/m² outside 1.5× IQR range for their district — potential deals (below) or overpriced (above).
        </p>
        <div class="table-wrapper">
            <table id="outlierTable">
                <thead>
                    <tr>
                        <th>District</th>
                        <th>Title</th>
                        <th>Price (tỷ)</th>
                        <th>Price/m²</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
</div>

<script>
// ====== DATA ======
const DATA = {data_json};

// ====== HELPERS ======
function fmtM2(v) {{
    if (!v) return 'N/A';
    return (v / 1e6).toFixed(1) + ' tr/m²';
}}
function fmtBillion(v) {{
    if (v == null) return 'N/A';
    return v >= 1 ? v.toFixed(1) + ' tỷ' : (v*1000).toFixed(0) + ' tr';
}}
function fmtArea(v) {{
    if (!v) return 'N/A';
    return v.toFixed(0) + ' m²';
}}
function badge(type) {{
    const labels = {{house:'Nhà',apartment:'Căn hộ',land:'Đất',villa:'Biệt thự',other:'Khác'}};
    return `<span class="badge badge-${{type}}">${{labels[type]||type}}</span>`;
}}

// ====== TABS ======
document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    }});
}});

// ====== RENDER ======
function render() {{
    // Generated time
    document.getElementById('genTime').textContent = 'Generated: ' + DATA.generated_at;

    // Stats cards
    const stats = [
        {{ value: DATA.total_listings, label: 'Total Listings' }},
        {{ value: DATA.total_districts, label: 'Districts Covered' }},
        {{ value: Object.keys(DATA.sources).length, label: 'Data Sources' }},
        {{ value: fmtBillion(DATA.median_price), label: 'Median Price' }},
        {{ value: fmtBillion(DATA.avg_price), label: 'Average Price' }},
    ];
    document.getElementById('statsGrid').innerHTML = stats.map(s =>
        `<div class="stat-card"><div class="value">${{s.value}}</div><div class="label">${{s.label}}</div></div>`
    ).join('');

    renderDistrictChart();
    renderPropTypeChart();
    renderSourceChart();
    renderBoxPlot();
    populateFilters();
    renderCheapestTable();
    renderOutlierTable();
    initScatter();
}}

// ====== CHARTS ======
const COLORS = ['#38bdf8','#818cf8','#f472b6','#34d399','#fbbf24','#fb923c','#a78bfa','#22d3ee','#f87171','#4ade80'];

function renderDistrictChart() {{
    const ds = DATA.district_stats.sort((a,b) => b.median_price_m2 - a.median_price_m2);
    new Chart(document.getElementById('chartDistrictPrice'), {{
        type: 'bar',
        data: {{
            labels: ds.map(d => d.district.replace('Quận ','Q').replace('Huyện ','H.').replace('Thành phố ','')),
            datasets: [
                {{
                    label: 'Median Price/m²',
                    data: ds.map(d => d.median_price_m2),
                    backgroundColor: '#38bdf8',
                    borderRadius: 4,
                }},
                {{
                    label: 'Average Price/m²',
                    data: ds.map(d => d.avg_price_m2),
                    backgroundColor: '#818cf844',
                    borderColor: '#818cf8',
                    borderWidth: 1,
                    borderRadius: 4,
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                tooltip: {{
                    callbacks: {{
                        label: ctx => ctx.dataset.label + ': ' + fmtM2(ctx.raw)
                    }}
                }}
            }},
            scales: {{
                y: {{
                    ticks: {{ callback: v => (v/1e6).toFixed(0) + 'tr', color: '#94a3b8' }},
                    grid: {{ color: '#1e293b' }}
                }},
                x: {{
                    ticks: {{ color: '#94a3b8', maxRotation: 45 }},
                    grid: {{ display: false }}
                }}
            }}
        }}
    }});
}}

function renderPropTypeChart() {{
    const ts = DATA.type_stats;
    const labels = {{house:'Nhà riêng',apartment:'Căn hộ',land:'Đất nền',villa:'Biệt thự',other:'Khác'}};
    new Chart(document.getElementById('chartPropType'), {{
        type: 'doughnut',
        data: {{
            labels: ts.map(t => labels[t.property_type] || t.property_type),
            datasets: [{{ data: ts.map(t => t.count), backgroundColor: COLORS }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'right', labels: {{ color: '#94a3b8' }} }}
            }}
        }}
    }});
}}

function renderSourceChart() {{
    const ss = DATA.source_stats;
    new Chart(document.getElementById('chartSource'), {{
        type: 'doughnut',
        data: {{
            labels: ss.map(s => s.source),
            datasets: [{{ data: ss.map(s => s.count), backgroundColor: ['#38bdf8','#818cf8','#f472b6','#34d399'] }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'right', labels: {{ color: '#94a3b8' }} }}
            }}
        }}
    }});
}}

function renderBoxPlot() {{
    const bd = DATA.box_data;
    const districts = Object.keys(bd).sort((a,b) => bd[b].median - bd[a].median);
    const labels = districts.map(d => d.replace('Quận ','Q').replace('Huyện ','H.').replace('Thành phố ',''));

    new Chart(document.getElementById('chartBoxPlot'), {{
        type: 'bar',
        data: {{
            labels: labels,
            datasets: [
                {{
                    label: 'Min',
                    data: districts.map(d => bd[d].min),
                    backgroundColor: '#334155',
                    borderRadius: 2,
                }},
                {{
                    label: 'Q1–Median',
                    data: districts.map(d => bd[d].median - bd[d].q1),
                    backgroundColor: '#38bdf866',
                    borderRadius: 2,
                }},
                {{
                    label: 'Median–Q3',
                    data: districts.map(d => bd[d].q3 - bd[d].median),
                    backgroundColor: '#818cf866',
                    borderRadius: 2,
                }},
                {{
                    label: 'Q3–Max',
                    data: districts.map(d => bd[d].max - bd[d].q3),
                    backgroundColor: '#33415566',
                    borderRadius: 2,
                }},
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                tooltip: {{
                    callbacks: {{
                        afterBody: (items) => {{
                            const idx = items[0].dataIndex;
                            const d = districts[idx];
                            return `Min: ${{fmtM2(bd[d].min)}}\\nQ1: ${{fmtM2(bd[d].q1)}}\\nMedian: ${{fmtM2(bd[d].median)}}\\nQ3: ${{fmtM2(bd[d].q3)}}\\nMax: ${{fmtM2(bd[d].max)}}`;
                        }}
                    }}
                }},
                legend: {{ display: false }}
            }},
            scales: {{
                x: {{ stacked: true, ticks: {{ color: '#94a3b8', maxRotation: 45 }}, grid: {{ display: false }} }},
                y: {{
                    stacked: true,
                    ticks: {{ callback: v => (v/1e6).toFixed(0) + 'tr', color: '#94a3b8' }},
                    grid: {{ color: '#1e293b' }}
                }}
            }}
        }}
    }});
}}

// ====== FILTERS & TABLES ======
function populateFilters() {{
    const districts = DATA.district_stats.map(d => d.district).sort();
    // Cheapest filter
    const cf = document.getElementById('cheapDistrictFilter');
    districts.forEach(d => {{
        const opt = document.createElement('option');
        opt.value = d; opt.textContent = d;
        cf.appendChild(opt);
    }});
    // Compare dropdowns
    const c1 = document.getElementById('compareDistrict1');
    const c2 = document.getElementById('compareDistrict2');
    districts.forEach((d, i) => {{
        const o1 = document.createElement('option'); o1.value = d; o1.textContent = d;
        const o2 = document.createElement('option'); o2.value = d; o2.textContent = d;
        if (i === 0) o1.selected = true;
        if (i === 1) o2.selected = true;
        c1.appendChild(o1); c2.appendChild(o2);
    }});
    c1.addEventListener('change', renderCompare);
    c2.addEventListener('change', renderCompare);
    renderCompare();

    // Cheapest filters
    document.getElementById('cheapDistrictFilter').addEventListener('change', renderCheapestTable);
    document.getElementById('cheapTypeFilter').addEventListener('change', renderCheapestTable);
    document.getElementById('cheapMaxPrice').addEventListener('input', renderCheapestTable);
}}

let compareChart = null;
function renderCompare() {{
    const d1 = document.getElementById('compareDistrict1').value;
    const d2 = document.getElementById('compareDistrict2').value;
    const s1 = DATA.district_stats.find(d => d.district === d1);
    const s2 = DATA.district_stats.find(d => d.district === d2);
    if (!s1 || !s2) return;

    if (compareChart) compareChart.destroy();
    const metrics = ['median_price_m2','avg_price_m2','avg_price','avg_area','count'];
    const labels = ['Median ₫/m²','Avg ₫/m²','Avg Price (tỷ)','Avg Area (m²)','Listings'];

    // Normalize for radar
    const max_vals = metrics.map(m => Math.max(s1[m]||1, s2[m]||1));
    compareChart = new Chart(document.getElementById('chartCompare'), {{
        type: 'radar',
        data: {{
            labels: labels,
            datasets: [
                {{
                    label: d1,
                    data: metrics.map((m,i) => ((s1[m]||0)/max_vals[i]*100).toFixed(1)),
                    borderColor: '#38bdf8', backgroundColor: '#38bdf822', pointBackgroundColor: '#38bdf8',
                }},
                {{
                    label: d2,
                    data: metrics.map((m,i) => ((s2[m]||0)/max_vals[i]*100).toFixed(1)),
                    borderColor: '#f472b6', backgroundColor: '#f472b622', pointBackgroundColor: '#f472b6',
                }},
            ]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            scales: {{
                r: {{
                    ticks: {{ display: false }},
                    grid: {{ color: '#334155' }},
                    poin