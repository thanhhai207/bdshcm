"""
Crawler for nha.chotot.com — uses their public JSON API.
Strategy: fetch listings from multiple regions, use area_name for district.
"""
from crawlers.base import BaseCrawler
from config import CHOTOT_REGIONS
from utils import classify_property_type


class ChototCrawler(BaseCrawler):
    """Crawler for chotot.com real estate listings via API."""

    API_URL = "https://gateway.chotot.com/v1/public/ad-listing"

    def __init__(self):
        super().__init__()
        self.source_name = "chotot.com"

    def _parse_api_listing(self, ad, valid_regions):
        """Parse a single listing from Chotot API response."""
        try:
            # Verify region
            region = ad.get("region_v2", ad.get("region", 0))
            region_name = ad.get("region_name", "")
            if region not in valid_regions:
                return None

            title = ad.get("subject", "")
            price_raw = ad.get("price_string", "")
            price_vnd = ad.get("price", 0)

            price_billion = round(price_vnd / 1e9, 2) if price_vnd else None
            if price_billion and price_billion < 0.01:
                return None

            area_m2 = ad.get("size", None)
            if area_m2:
                area_m2 = float(area_m2)

            price_per_m2 = None
            if price_billion and area_m2 and area_m2 > 0:
                price_per_m2 = round((price_billion * 1e9) / area_m2, 0)

            chotot_type = ad.get("category_name", "")
            prop_type = classify_property_type(title + " " + chotot_type)

            list_id = ad.get("list_id", ad.get("ad_id", ""))
            url = f"https://nha.chotot.com/{list_id}.htm" if list_id else ""

            district = ad.get("area_name", "")

            address = district
            ward = ad.get("ward_name", "")
            street = ad.get("street_name", "")
            if street:
                address = f"{street}, {ward}, {district}" if ward else f"{street}, {district}"
            elif ward:
                address = f"{ward}, {district}"

            if not title or not price_billion or not district:
                return None

            return {
                "title": title,
                "price_raw": price_raw,
                "price_billion": price_billion,
                "area_m2": area_m2,
                "price_per_m2": price_per_m2,
                "district": district,
                "address": address,
                "property_type": prop_type,
                "source": self.source_name,
                "url": url,
            }
        except Exception:
            return None

    def _crawl_region(self, region_name, region_code, district_set, max_pages):
        """Crawl all listings in a single chotot region."""
        listings = []
        items_per_page = 50
        total_pages = min(max_pages * 7, 20)  # Up to 20 pages per region

        for page in range(total_pages):
            params = {
                "region_v2": region_code,
                "cg": 1000,
                "o": page * items_per_page,
                "page": page + 1,
                "st": "s,k",
                "limit": items_per_page,
                "key_param_included": "true",
            }

            resp = self._get(self.API_URL, params=params)
            if not resp:
                break

            try:
                data = resp.json()
                ads = data.get("ads", [])
                total = data.get("total", 0)

                if page == 0:
                    print(f"  [chotot] {region_name}: {total} listings available")

                if not ads:
                    break

                for ad in ads:
                    listing = self._parse_api_listing(ad, {region_code})
                    if listing and listing["district"] in district_set:
                        listings.append(listing)

                if (page + 1) * items_per_page >= min(total, 1000):
                    break

            except Exception as e:
                print(f"  [!] JSON parse error: {e}")
                break

        return listings

    def crawl_district(self, district_name, max_pages=3):
        """Not used — chotot crawls by region via crawl_all."""
        return []

    def crawl_all(self, districts, max_pages=3):
        """Crawl listings from all configured chotot regions."""
        district_set = set(districts)
        all_listings = []

        for region_name, region_code in CHOTOT_REGIONS.items():
            print(f"[{self.source_name}] Crawling {region_name} (region {region_code})...")
            region_listings = self._crawl_region(
                region_name, region_code, district_set, max_pages
            )
            all_listings.extend(region_listings)

        # Report per-district counts
        from collections import Counter
        dist_counts = Counter(l["district"] for l in all_listings)
        for d, c in sorted(dist_counts.items()):
            print(f"  -> {d}: {c} listings")
        print(f"  Total from chotot.com: {len(all_listings)}")

        return all_listings
