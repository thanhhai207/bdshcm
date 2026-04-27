"""
Base crawler class with shared functionality.
Supports cloudscraper (for anti-bot bypass) with fallback to requests.
"""
import time
import random
import subprocess
import json
import requests
from abc import ABC, abstractmethod
from config import REQUEST_HEADERS, REQUEST_DELAY, MAX_RETRIES, REQUEST_TIMEOUT

# Try to import cloudscraper for Cloudflare bypass
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False


class BaseCrawler(ABC):
    """Base class for all real estate crawlers."""

    def __init__(self):
        if HAS_CLOUDSCRAPER:
            self.session = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
            )
            print(f"  [cloudscraper] Anti-bot bypass enabled")
        else:
            self.session = requests.Session()
            print(f"  [requests] Basic mode (install cloudscraper for better results)")
        self.session.headers.update(REQUEST_HEADERS)
        self.source_name = "unknown"

    def _get(self, url, params=None):
        """Make a GET request with retry logic and rate limiting."""
        for attempt in range(MAX_RETRIES + 1):
            try:
                time.sleep(random.uniform(*REQUEST_DELAY))
                resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 403:
                    if attempt < MAX_RETRIES:
                        wait = 5 * (attempt + 1)
                        print(f"  [!] 403 for {url}, retrying in {wait}s...")
                        time.sleep(wait)
                        # Rotate user-agent on retry
                        ua_list = [
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
                        ]
                        self.session.headers["User-Agent"] = random.choice(ua_list)
                        continue
                    print(f"  [!] Access denied (403) for {url}")
                    return None
                elif resp.status_code == 429:
                    wait = 10 * (attempt + 1)
                    print(f"  [!] Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"  [!] HTTP {resp.status_code} for {url}")
            except requests.exceptions.Timeout:
                print(f"  [!] Timeout for {url} (attempt {attempt+1})")
            except requests.exceptions.RequestException as e:
                print(f"  [!] Request error: {e}")
        return None

    def _get_with_curl(self, url):
        """Fallback: use system curl for sites that block Python requests."""
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "-L",
                    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "-H", "Accept-Language: vi-VN,vi;q=0.9,en-US;q=0.8",
                    "-H", "Accept-Encoding: gzip, deflate",
                    "--compressed",
                    "--max-time", "20",
                    url,
                ],
                capture_output=True, text=True, timeout=25,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception as e:
            print(f"  [!] Curl fallback failed: {e}")
        return None

    @abstractmethod
    def crawl_district(self, district_name, max_pages=3):
        pass

    def crawl_all(self, districts, max_pages=3):
        """Crawl all districts and return combined results."""
        all_listings = []
        for district in districts:
            print(f"[{self.source_name}] Crawling {district}...")
            try:
                listings = self.crawl_district(district, max_pages)
                all_listings.extend(listings)
                print(f"  -> Found {len(listings)} listings")
            except Exception as e:
                print(f"  [!] Error crawling {district}: {e}")
        return all_listings
