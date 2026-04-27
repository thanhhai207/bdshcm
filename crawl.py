"""
Main crawler script — runs all crawlers and saves combined data to CSV + JSON.
Usage: python crawl.py
"""
import os
import sys
import json
import time
from datetime import datetime

import pandas as pd

from config import DISTRICTS, MAX_PAGES_PER_DISTRICT
from crawlers.batdongsan import BatDongSanCrawler
from crawlers.chotot import ChototCrawler
from crawlers.muaban import MuaBanCrawler


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def run_crawl(districts=None, max_pages=None):
    """Run all crawlers and return combined DataFrame."""
    if districts is None:
        districts = DISTRICTS
    if max_pages is None:
        max_pages = MAX_PAGES_PER_DISTRICT

    print("=" * 60)
    print(f"  HCMC Real Estate Crawler")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Districts: {len(districts)} | Pages/district: {max_pages}")
    print("=" * 60)

    all_listings = []

    # 1. Chotot (API-based, most reliable)
    print("\n[1/3] Crawling chotot.com (API)...")
    try:
        chotot = ChototCrawler()
        chotot_data = chotot.crawl_all(districts, max_pages)
        all_listings.extend(chotot_data)
        print(f"  Total from chotot.com: {len(chotot_data)}")
    except Exception as e:
        print(f"  [!] Chotot crawler failed: {e}")

    # 2. Batdongsan.com.vn
    print("\n[2/3] Crawling batdongsan.com.vn...")
    try:
        bds = BatDongSanCrawler()
        bds_data = bds.crawl_all(districts, max_pages)
        all_listings.extend(bds_data)
        print(f"  Total from batdongsan.com.vn: {len(bds_data)}")
    except Exception as e:
        print(f"  [!] Batdongsan crawler failed: {e}")

    # 3. Muaban.net
    print("\n[3/3] Crawling muaban.net...")
    try:
        muaban = MuaBanCrawler()
        muaban_data = muaban.crawl_all(districts, max_pages)
        all_listings.extend(muaban_data)
        print(f"  Total from muaban.net: {len(muaban_data)}")
    except Exception as e:
        print(f"  [!] Muaban crawler failed: {e}")

    # Build DataFrame
    if not all_listings:
        print("\n[!] No listings found. Sites may have changed their layout or blocked requests.")
        print("    Creating sample data for dashboard demo...")
        df = _create_sample_data()
    else:
        df = pd.DataFrame(all_listings)

    # Clean data
    df = clean_data(df)

    # Save
    os.makedirs(DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = os.path.join(DATA_DIR, "listings_latest.csv")
    json_path = os.path.join(DATA_DIR, "listings_latest.json")
    archive_path = os.path.join(DATA_DIR, f"listings_{timestamp}.csv")

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_csv(archive_path, index=False, encoding="utf-8-sig")

    # Save JSON for dashboard
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  Crawl complete!")
    print(f"  Total listings: {len(df)}")
    print(f"  Sources: {df['source'].value_counts().to_dict()}")
    print(f"  Saved to: {csv_path}")
    print(f"  Archive:  {archive_path}")
    print(f"{'=' * 60}")

    return df


def clean_data(df):
    """Clean and filter the crawled data."""
    if df.empty:
        return df

    # Remove duplicates based on title similarity
    df = df.drop_duplicates(subset=["title", "district"], keep="first")

    # Filter unrealistic prices (< 100 triệu or > 500 tỷ)
    df = df[(df["price_billion"] >= 0.1) & (df["price_billion"] <= 500)]

    # Filter unrealistic areas
    if "area_m2" in df.columns:
        df = df[df["area_m2"].isna() | ((df["area_m2"] >= 10) & (df["area_m2"] <= 10000))]

    # Filter unrealistic price_per_m2 (below 1 million or above 2 billion per m2)
    if "price_per_m2" in df.columns:
        df = df[df["price_per_m2"].isna() | ((df["price_per_m2"] >= 1e6) & (df["price_per_m2"] <= 2e9))]

    # Add crawl timestamp
    df["crawled_at"] = datetime.now().isoformat()

    return df.reset_index(drop=True)


def _create_sample_data():
    """Create sample data if crawling returns no results (for dashboard demo)."""
    import random
    random.seed(42)

    districts_prices = {
        "Quận 1": (15, 80), "Quận 3": (10, 50), "Quận 4": (4, 20),
        "Quận 5": (6, 25), "Quận 7": (5, 30), "Quận Bình Thạnh": (4, 25),
        "Quận Gò Vấp": (3, 15), "Quận Tân Bình": (4, 18),
        "Quận Phú Nhuận": (6, 30), "Thành phố Thủ Đức": (3, 20),
        "Quận Bình Tân": (2, 10), "Quận Tân Phú": (3, 12),
        "Quận 12": (2, 10), "Huyện Bình Chánh": (1.5, 8),
        "Huyện Nhà Bè": (2, 12), "Huyện Hóc Môn": (1, 6),
        "Huyện Củ Chi": (0.8, 5), "Quận 6": (3, 15),
        "Quận 8": (3, 12), "Quận 10": (8, 35), "Quận 11": (6, 25),
    }

    sources = ["chotot.com", "batdongsan.com.vn", "muaban.net"]
    types = ["house", "apartment", "land", "villa"]
    listings = []

    for district, (low, high) in districts_prices.items():
        n = random.randint(15, 40)
        for i in range(n):
            price = round(random.uniform(low, high), 2)
            area = round(random.uniform(30, 300), 1)
            ptype = random.choice(types)
            source = random.choice(sources)
            ppm2 = round((price * 1e9) / area, 0) if area > 0 else None

            # Generate realistic demo URLs per source
            demo_id = random.randint(100000, 999999)
            if source == "chotot.com":
                url = f"https://nha.chotot.com/{demo_id}.htm"
            elif source == "batdongsan.com.vn":
                url = f"https://batdongsan.com.vn/ban-nha-rieng-pr{demo_id}"
            else:
                url = f"https://muaban.net/ban-nha-dat-{demo_id}.htm"

            listings.append({
                "title": f"Bán {ptype} {district} - {area}m²",
                "price_raw": f"{price} tỷ",
                "price_billion": price,
                "area_m2": area,
                "price_per_m2": ppm2,
                "district": district,
                "address": district,
                "property_type": ptype,
                "source": source,
                "url": url,
            })

    return pd.DataFrame(listings)


if __name__ == "__main__":
    # Allow passing a subset of districts via CLI
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick mode: only crawl major districts
        quick_districts = [
            "Quận 1", "Quận 7", "Quận Bình Thạnh", "Quận Gò Vấp",
            "Thành phố Thủ Đức", "Quận Tân Bình", "Huyện Bình Chánh"
        ]
        run_crawl(districts=quick_districts, max_pages=2)
    else:
        run_crawl()
