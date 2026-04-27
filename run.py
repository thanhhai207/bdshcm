"""
One-click runner: Crawl fresh data + Generate dashboard.
Usage:
    python run.py          # Full crawl (all districts, all sources)
    python run.py --quick  # Quick crawl (7 major districts, 2 pages each)
    python run.py --demo   # Skip crawl, use sample data, generate dashboard
"""
import sys
import os
import importlib
import webbrowser

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True

# Force fresh imports (bypass stale .pyc)
for mod_name in list(sys.modules.keys()):
    if mod_name in ('crawl', 'generate_dashboard', 'config', 'utils') or mod_name.startswith('crawlers'):
        del sys.modules[mod_name]

from crawl import run_crawl
from generate_dashboard import main as generate_dashboard


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode == "--demo":
        print("Demo mode: generating sample data + dashboard...")
        from crawl import _create_sample_data, clean_data, DATA_DIR
        import pandas as pd
        os.makedirs(DATA_DIR, exist_ok=True)
        df = _create_sample_data()
        df = clean_data(df)
        df.to_csv(os.path.join(DATA_DIR, "listings_latest.csv"), index=False, encoding="utf-8-sig")
        df.to_json(os.path.join(DATA_DIR, "listings_latest.json"), orient="records", force_ascii=False, indent=2)
        print(f"Sample data: {len(df)} listings")
    elif mode == "--quick":
        quick_districts = [
            "Quận 1", "Quận 7", "Quận Bình Thạnh", "Quận Gò Vấp",
            "Thành phố Thủ Đức", "Quận Tân Bình", "Huyện Bình Chánh"
        ]
        run_crawl(districts=quick_districts, max_pages=2)
    else:
        run_crawl()

    dashboard_path = generate_dashboard()
    try:
        webbrowser.open("file://" + os.path.abspath(dashboard_path))
        print("\nDashboard opened in your browser!")
    except Exception:
        print(f"\nOpen this file in your browser:\n  {os.path.abspath(dashboard_path)}")


if __name__ == "__main__":
    main()
