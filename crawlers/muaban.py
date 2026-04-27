"""
Crawler for muaban.net real estate listings.
Uses https://muaban.net/bat-dong-san as entry point.
Finds listing detail links and extracts price/area from parent containers.
"""
import re
import json
import time
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler
from utils import parse_price, parse_area, classify_property_type

# Try playwright for muaban too
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class MuaBanCrawler(BaseCrawler):
    """Crawler for muaban.net"""

    BASE_URL = "https://muaban.net"
    LISTING_URL = "https://muaban.net/bat-dong-san"

    def __init__(self):
        super().__init__()
        self.source_name = "muaban.net"
        self.session.headers.update({
            "Referer": "https://muaban.net/",
        })

    def _slug_to_district(self, text):
        """Extract district name from URL slug or text."""
        mappings = [
            (r'quan-1(?:\b|[/-])', "Quận 1"), (r'quan-3(?:\b|[/-])', "Quận 3"),
            (r'quan-4(?:\b|[/-])', "Quận 4"), (r'quan-5(?:\b|[/-])', "Quận 5"),
            (r'quan-6(?:\b|[/-])', "Quận 6"), (r'quan-7(?:\b|[/-])', "Quận 7"),
            (r'quan-8(?:\b|[/-])', "Quận 8"), (r'quan-10(?:\b|[/-])', "Quận 10"),
            (r'quan-11(?:\b|[/-])', "Quận 11"), (r'quan-12(?:\b|[/-])', "Quận 12"),
            (r'quan-binh-tan', "Quận Bình Tân"),
            (r'quan-binh-thanh', "Quận Bình Thạnh"),
            (r'quan-go-vap', "Quận Gò Vấp"),
            (r'quan-phu-nhuan', "Quận Phú Nhuận"),
            (r'quan-tan-binh', "Quận Tân Bình"),
            (r'quan-tan-phu', "Quận Tân Phú"),
            (r'thu-duc', "Thành phố Thủ Đức"),
            (r'huyen-binh-chanh', "Huyện Bình Chánh"),
            (r'huyen-nha-be', "Huyện Nhà Bè"),
            (r'huyen-hoc-mon', "Huyện Hóc Môn"),
            (r'huyen-cu-chi', "Huyện Củ Chi"),
            (r'huyen-can-gio', "Huyện Cần Giờ"),
        ]
        for pattern, name in mappings:
            if re.search(pattern, text, re.I):
                return name
        return ""

    def _district_from_text(self, text):
        """Extract district from Vietnamese text."""
        patterns = [
            (r'Quận\s*1\b', "Quận 1"), (r'Quận\s*3\b', "Quận 3"),
            (r'Quận\s*4\b', "Quận 4"), (r'Quận\s*5\b', "Quận 5"),
            (r'Quận\s*6\b', "Quận 6"), (r'Quận\s*7\b', "Quận 7"),
            (r'Quận\s*8\b', "Quận 8"), (r'Quận\s*10\b', "Quận 10"),
            (r'Quận\s*11\b', "Quận 11"), (r'Quận\s*12\b', "Quận 12"),
            (r'Bình Tân', "Quận Bình Tân"),
            (r'Bình Thạnh', "Quận Bình Thạnh"),
            (r'Gò Vấp', "Quận Gò Vấp"),
            (r'Phú Nhuận', "Quận Phú Nhuận"),
            (r'Tân Bình', "Quận Tân Bình"),
            (r'Tân Phú', "Quận Tân Phú"),
            (r'Thủ Đức', "Thành phố Thủ Đức"),
            (r'Bình Chánh', "Huyện Bình Chánh"),
            (r'Nhà Bè', "Huyện Nhà Bè"),
            (r'Hóc Môn', "Huyện Hóc Môn"),
            (r'Củ Chi', "Huyện Củ Chi"),
            (r'Cần Giờ', "Huyện Cần Giờ"),
        ]
        for pattern, name in patterns:
            if re.search(pattern, text):
                return name
        return ""

    def _parse_from_html(self, html, district_set):
        """Parse listings from muaban HTML using link-based detection."""
        soup = BeautifulSoup(html, "lxml")
        listings = []
        seen_urls = set()

        # Strategy: find all <a> tags whose href looks like a listing detail page
        # Pattern: /bat-dong-san/ban-<type>-<location>/<slug>
        # The key is having at least 2 path segments after /bat-dong-san/
        all_links = soup.find_all("a", href=True)

        for link in all_links:
            href = link.get("href", "")
            title = link.get_text(strip=True)

            # Must be a detail page link (has slug after location)
            if not re.search(r'/bat-dong-san/.+/.+', href):
                continue

            # Must have a meaningful title (not just location text)
            if not title or len(title) < 15:
                continue

            # Skip location-only links like "Quận 11, " or "TP.HCM"
            if len(title) < 30 and re.match(r'^(Quận|Huyện|Phường|TP|Thành phố|Xã)', title):
                continue

            full_url = href if href.startswith("http") else self.BASE_URL + href
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Walk up to find container with price
            container = link
            card_text = ""
            for _ in range(8):
                container = container.parent
                if container is None or container.name == "body":
                    break
                card_text = container.get_text(" ", strip=True)
                if re.search(r'\d[\d.,]*\s*(?:tỷ|triệu)', card_text, re.I) and len(card_text) > 50:
                    break

            # Extract price
            price_raw = ""
            pm = re.search(r'(\d[\d.,]*\s*(?:tỷ|triệu))', card_text, re.I)
            if pm:
                price_raw = pm.group(1)

            # Extract area
            area_raw = ""
            am = re.search(r'(\d[\d.,]*)\s*m[²2]', card_text, re.I)
            if am:
                area_raw = am.group(0)

            # Extract district from URL and text
            district = self._slug_to_district(href)
            if not district:
                district = self._district_from_text(card_text)

            # Filter: only HCMC and must be "ho-chi-minh" or matching district
            if "ho-chi-minh" not in href and district not in district_set:
                continue

            price_billion = parse_price(price_raw)
            area_m2 = parse_area(area_raw)
            price_per_m2 = None
            if price_billion and area_m2 and area_m2 > 0:
                price_per_m2 = round((price_billion * 1e9) / area_m2, 0)

            if not price_billion:
                continue

            listings.append({
                "title": title[:120],
                "price_raw": price_raw,
                "price_billion": price_billion,
                "area_m2": area_m2,
                "price_per_m2": price_per_m2,
                "district": district,
                "address": district,
                "property_type": classify_property_type(title),
                "source": self.source_name,
                "url": full_url,
            })

        return listings

    def _crawl_with_playwright(self, districts, max_pages):
        """Use Playwright to render muaban pages."""
        listings = []
        district_set = set(districts)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    locale="vi-VN",
                )
                page = context.new_page()

                total_pages = max_pages * 3
                for pg in range(1, total_pages + 1):
                    url = self.LISTING_URL if pg == 1 else f"{self.LISTING_URL}?page={pg}"
                    try:
                        page.goto(url, wait_until="networkidle", timeout=30000)
                        time.sleep(2)  # Let content settle
                    except Exception as e:
                        print(f"  [!] Page load error: {e}")
                        break

                    html = page.content()
                    page_listings = self._parse_from_html(html, district_set)

                    if pg == 1:
                        print(f"  [muaban/playwright] Page 1: {len(page_listings)} listings")

                    listings.extend(page_listings)

                    if not page_listings:
                        break

                browser.close()
        except Exception as e:
            print(f"  [!] Playwright error: {e}")

        return listings

    def _crawl_with_requests(self, districts, max_pages):
        """Fallback: use cloudscraper/requests."""
        listings = []
        district_set = set(districts)
        total_pages = max_pages * 3

        for pg in range(1, total_pages + 1):
            url = self.LISTING_URL if pg == 1 else f"{self.LISTING_URL}?page={pg}"
            resp = self._get(url)
            if not resp:
                break

            page_listings = self._parse_from_html(resp.text, district_set)

            if pg == 1:
                print(f"  [muaban/requests] Page 1: {len(page_listings)} listings")
                if not page_listings and len(resp.text) > 10000:
                    # Page loaded but no listings found - might be JS rendered
                    print(f"  [!] Page has {len(resp.text)}B but no parseable listings")
                    print(f"  [!] Muaban may require Playwright. Install: pip install playwright && playwright install chromium")

            listings.extend(page_listings)
            if not page_listings and pg > 1:
                break

        return listings

    def crawl_district(self, district_name, max_pages=3):
        """Not used — muaban crawls centrally."""
        return []

    def crawl_all(self, districts, max_pages=3):
        """Crawl muaban.net listings."""
        print(f"[{self.source_name}] Crawling bat-dong-san listings...")
        district_set = set(districts)

        if HAS_PLAYWRIGHT:
            listings = self._crawl_with_playwright(districts, max_pages)
        else:
            listings = self._crawl_with_requests(districts, max_pages)

        # Filter to target districts
        filtered = [l for l in listings if l["district"] in district_set or l["district"] == ""]

        from collections import Counter
        dist_counts = Counter(l["district"] for l in filtered if l["district"])
        for d, c in sorted(dist_counts.items()):
            print(f"  -> {d}: {c} listings")
        print(f"  Total from muaban.net: {len(filtered)}")

        return filtered
