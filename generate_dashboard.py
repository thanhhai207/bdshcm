"""
Generate a self-contained HTML dashboard from crawled data.
Usage: python generate_dashboard.py
"""
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")


def load_data():
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
    analytics = {}
    analytics["total_listings"] = len(df)
    analytics["total_districts"] = df["district"].nunique()
    analytics["sources"] = df["source"].value_counts().to_dict()
    analytics["avg_price"] = round(df["price_billion"].mean(), 2)
    analytics["median_price"] = round(df["price_billion"].median(), 2)

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

    type_stats = df.groupby("property_type").agg(
        count=("price_billion", "count"),
        avg_price=("price_billion", "mean"),
    ).round(2).reset_index()
    analytics["type_stats"] = type_stats.to_dict(orient="records")

    source_stats = df.groupby("source").agg(
        count=("price_billion", "count"),
        avg_price=("price_billion", "mean"),
    ).round(2).reset_index()
    analytics["source_stats"] = source_stats.to_dict(orient="records")

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
    analytics["outliers"] = outliers[:50]

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
    data_json = json.dumps(analytics, ensure_ascii=False, default=str)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    html = template.replace("%%DATA_JSON%%", data_json)
    return html


def main():
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} listings")
    print("Computing analytics...")
    analytics = compute_analytics(df)
    print(f"  {len(analytics.get('all_points', []))} data points for scatter plot")
    print("Generating dashboard...")
    html = generate_html(analytics)
    output_path = os.path.join(OUTPUT_DIR, "dashboard.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
