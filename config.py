"""
Configuration for Vietnam Real Estate Crawler
"""

# --- REGIONS ---
# Each region has a chotot region_v2 code and a list of districts/areas to track.

# Chotot region codes
CHOTOT_REGIONS = {
    "HCMC": 13000,
    "Bình Dương": 12000,
    "Khánh Hòa": 38000,   # Nha Trang is in Khánh Hòa province
}

# Ho Chi Minh City Districts
HCMC_DISTRICTS = [
    "Quận 1", "Quận 3", "Quận 4", "Quận 5", "Quận 6", "Quận 7", "Quận 8",
    "Quận 10", "Quận 11", "Quận 12", "Quận Bình Tân", "Quận Bình Thạnh",
    "Quận Gò Vấp", "Quận Phú Nhuận", "Quận Tân Bình", "Quận Tân Phú",
    "Thành phố Thủ Đức", "Huyện Bình Chánh", "Huyện Cần Giờ",
    "Huyện Củ Chi", "Huyện Hóc Môn", "Huyện Nhà Bè"
]

# Bình Dương Districts
BINH_DUONG_DISTRICTS = [
    "Thành phố Thủ Dầu Một", "Thành phố Dĩ An", "Thành phố Thuận An",
    "Thành phố Tân Uyên", "Thành phố Bến Cát", "Huyện Bàu Bàng",
    "Huyện Bắc Tân Uyên", "Huyện Dầu Tiếng", "Huyện Phú Giáo",
]

# Nha Trang / Khánh Hòa Districts
NHA_TRANG_DISTRICTS = [
    "Thành phố Nha Trang", "Thành phố Cam Ranh", "Huyện Cam Lâm",
    "Huyện Diên Khánh", "Huyện Ninh Hòa",
]

# Combined list of all tracked areas
DISTRICTS = HCMC_DISTRICTS + BINH_DUONG_DISTRICTS + NHA_TRANG_DISTRICTS

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

# Slug mappings for batdongsan.com.vn — Bình Dương
BDS_BINH_DUONG_SLUGS = {
    "Thành phố Thủ Dầu Một": "thanh-pho-thu-dau-mot",
    "Thành phố Dĩ An": "thanh-pho-di-an",
    "Thành phố Thuận An": "thanh-pho-thuan-an",
    "Thành phố Tân Uyên": "thanh-pho-tan-uyen",
    "Thành phố Bến Cát": "thanh-pho-ben-cat",
    "Huyện Bàu Bàng": "huyen-bau-bang",
    "Huyện Bắc Tân Uyên": "huyen-bac-tan-uyen",
    "Huyện Dầu Tiếng": "huyen-dau-tieng",
    "Huyện Phú Giáo": "huyen-phu-giao",
}

# Slug mappings for batdongsan.com.vn — Khánh Hòa (Nha Trang)
BDS_NHA_TRANG_SLUGS = {
    "Thành phố Nha Trang": "thanh-pho-nha-trang",
    "Thành phố Cam Ranh": "thanh-pho-cam-ranh",
    "Huyện Cam Lâm": "huyen-cam-lam",
    "Huyện Diên Khánh": "huyen-dien-khanh",
    "Huyện Ninh Hòa": "huyen-ninh-hoa",
}

# Note: Chotot crawler fetches by region and uses area_name from API response.

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
