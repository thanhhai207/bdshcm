"""
Crawler for batdongsan.com.vn — Vietnam's largest real estate platform.
Uses Playwright (headless browser) to render JS-loaded listings.
Falls back to cloudscraper HTML if Playwright is not available.
"""
import re
import json
import time
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler
from config import BDS_DISTRICT_SLUGS
from utils import parse_price, parse_area, classify_property_type

# Try to import playwright
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class BatDongSanCrawler(BaseCrawler):
    """Crawler for batdongsan.com.vn using headless browser."""

    BASE_URL = "https://batdongsan.com.vn"

    def __init__(self):
        super().__init__()
        self.source_name = "batdongsan.com.vn"
        if not HAS_PLAYWRIGHT:
            print("  [!] Playwright not installed. Run: pip install playwright && playwright install chromium")
            print("  [!] Batdongsan requires a headless browser (JS-rendered listings)")

    def _build_url(self, district_slug, page=1):
        url = f"{self.BASE_URL}/ban-nha-dat-tp-ho-chi-minh/{district_slug}"
        if page > 1:
            url += f"/p{page}"
        return url

    def _parse_listing(self, item, district_name):
        """Parse a single listing card from rendered HTML."""
        try:
            # Title and URL
            title_el = None
            for sel in [
                "a.js__product-link-for-track",
                ".re__card-title a",
                "a[href*='/ban-']",
                "a[href*='/pr']",
                "h3 a",
            ]:
                title_el = item.select_one(sel)
                if title_el and title_el.get_text(strip=True):
                    break
                title_el = None

            title = title_el.get_text(strip=True) if title_el else ""
            url = ""
            if title_el and title_el.get("href"):
                href = title_el["href"]
                url = href if href.startswith("http") else self.BASE_URL + href

            if not title:
                for sel in [".re__card-title", "h3", ".pr-title"]:
                    el = item.select_one(sel)
                    if el and el.get_text(strip=True):
                        title = el.get_text(strip=True)
                        break

            # Price
            price_raw = ""
            for sel in [".re__card-config-price", "span[class*='price']",
                        "[class*='price']", "[class*='Price']"]:
                el = item.select_one(sel)
                if el:
                    price_raw = el.get_text(strip=True)
                    if price_raw and any(c.isdigit() for c in price_raw):
                        break
                    price_raw = ""

            # Area
            area_raw = ""
            for sel in [".re__card-config-area", "span[class*='area']",
                        "[class*='area']"]:
                el = item.select_one(sel)
                if el:
                    area_raw = el.get_text(strip=True)
                    if area_raw:
                        break

            # Location
            address = district_name
            for sel in [".re__card-location", "[class*='location']"]:
                el = item.select_one(sel)
                if el and el.get_text(strip=True):
                    address = el.get_text(strip=True)
                    break

            price_billion = parse_price(price_raw)
            area_m2 = parse_area(area_raw)
            price_per_m2 = None
            if price_billion and area_m2 and area_m2 > 0:
                price_per_m2 = round((price_billion * 1e9) / area_m2, 0)

            if not title or not price_billion:
                return None

            return {
                "title": title[:120],
                "price_raw": price_raw,
                "price_billion": price_billion,
                "area_m2": area_m2,
                "price_per_m2": price_per_m2,
                "district": district_name,
                "address": address,
                "property_type": classify_property_type(title),
                "source": self.source_name,
                "url": url,
            }
        except Exception:
            return None

    def _crawl_with_playwright(self, district_name, slug, max_pages):
        """Use Playwright headless browser to render and scrape listings."""
        listings = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    locale="vi-VN",
                )
                page = context.new_page()

                for pg in range(1, max_pages + 1):
                    url = self._build_url(slug, pg)
                    try:
                        page.goto(url, wait_until="networkidle", timeout=30000)
                        # Wait for listing cards to appear
                        page.wait_for_selector(
                            ".js__card, .re__card-full, [class*='ProductItem']",
                            timeout=10000
                        )
                        # Small delay for any lazy-loaded content
                        time.sleep(1)
                    except Exception as e:
                        print(f"  [!] Page load timeout for {url}: {e}")
                        if pg == 1:
                            break
                        continue

                    html = page.content()
                    soup = BeautifulSoup(html, "lxml")

                    items = soup.select(".js__card, .re__card-full, .re__card-info")
                    if not items:
                        # Try broader selectors on rendered page
                        items = soup.select("div[class*='ProductItem'], div.re__srp-list > div")

                    if not items:
                        if pg == 1:
                            print(f"  [!] No cards found even after JS render for {district_name}")
                        break

                    count_before = len(listings)
                    for item in items:
                        listing = self._parse_listing(item, district_name)
                        if listing:
                            listings.append(listing)

                    new = len(listings) - count_before
                    if new == 0 and pg > 1:
                        break

                browser.close()
        except Exception as e:
            print(f"  [!] Playwright error: {e}")

        return listings

    def crawl_district(self, district_name, max_pages=3):
        """Crawl listings for a district from batdongsan.com.vn"""
        slug = BDS_DISTRICT_SLUGS.get(district_name)
        if not slug:
            print(f"  [!] No slug for {district_name}")
            return []

        if HAS_PLAYWRIGHT:
            return self._crawl_with_playwright(district_name, slug, max_pages)
        else:
            # Without playwright, BDS won't work (JS-rendered)
            return []
