"""
Configuration for HCMC Real Estate Crawler
"""

# Ho Chi Minh City Districts
DISTRICTS = [
    "Quận 1", "Quận 3", "Quận 4", "Quận 5", "Quận 6", "Quận 7", "Quận 8",
    "Quận 10", "Quận 11", "Quận 12", "Quận Bình Tân", "Quận Bình Thạnh",
    "Quận Gò Vấp", "Quận Phú Nhuận", "Quận Tân Bình", "Quận Tân Phú",
    "Thành phố Thủ Đức", "Huyện Bình Chánh", "Huyện Cần Giờ",
    "Huyện Củ Chi", "Huyện Hóc Môn", "Huyện Nhà Bè"
]

# Slug mappings for batdongsan.com.vn
BDS_DISTRICT_SLUGS = {
    "Quận 1": "quan-1",
    "Quận 3": "quan-3",
    "Quận 4": "quan-4",
    "Quận 5": "quan-5",
    "Quận 6": "quan-6",
    "Quận 7": "quan-7",
    "Quận 8": "quan-8",
    "Quận 10": "quan-10",
    "Quận 11": "quan-11",
    "Quận 12": "quan-12",
    "Quận Bình Tân": "quan-binh-tan",
    "Quận Bình Thạnh": "quan-binh-thanh",
    "Quận Gò Vấp": "quan-go-vap",
    "Quận Phú Nhuận": "quan-phu-nhuan",
    "Quận Tân Bình": "quan-tan-binh",
    "Quận Tân Phú": "quan-tan-phu",
    "Thành phố Thủ Đức": "thanh-pho-thu-duc",
    "Huyện Bình Chánh": "huyen-binh-chanh",
    "Huyện Cần Giờ": "huyen-can-gio",
    "Huyện Củ Chi": "huyen-cu-chi",
    "Huyện Hóc Môn": "huyen-hoc-mon",
    "Huyện Nhà Bè": "huyen-nha-be",
}

# Note: Chotot crawler no longer needs district codes — it fetches all HCMC
# listings and uses the area_name field from the API response for district names.

# Property type labels
PROPERTY_TYPES = {
    "house": "Nhà riêng",
    "apartment": "Căn hộ",
    "land": "Đất nền",
    "villa": "Biệt thự",
    "other": "Khác",
}

# Request settings — mimic a real Chrome browser
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
}

REQUEST_DELAY = (1.5, 3.0)  # Random delay range in seconds between requests
MAX_PAGES_PER_DISTRICT = 3  # Pages to crawl per district per source
MAX_RETRIES = 2
REQUEST_TIMEOUT = 15
