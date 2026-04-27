"""
Shared utility functions for parsing prices, areas, and classifying property types.
"""
import re


def parse_price(price_str):
    """
    Parse Vietnamese real estate price string to float (in billions VND).
    Examples:
        "3.5 tỷ" -> 3.5
        "850 triệu" -> 0.85
        "12,5 tỷ" -> 12.5
        "3 tỷ 500 triệu" -> 3.5
        "2.100.000.000" -> 2.1
    """
    if not price_str:
        return None

    price_str = price_str.strip().lower()

    # Filter out "thỏa thuận" (negotiable) or "liên hệ" (contact)
    if any(x in price_str for x in ["thỏa thuận", "liên hệ", "thoả thuận", "contact"]):
        return None

    try:
        # Pattern: X tỷ Y triệu
        m = re.search(r'(\d[\d.,]*)\s*tỷ\s*(\d[\d.,]*)\s*(triệu|tr)', price_str)
        if m:
            ty = float(m.group(1).replace(",", ".").replace("..", "."))
            trieu = float(m.group(2).replace(",", ".").replace("..", "."))
            return round(ty + trieu / 1000, 3)

        # Pattern: X tỷ
        m = re.search(r'(\d[\d.,]*)\s*tỷ', price_str)
        if m:
            val = m.group(1).replace(",", ".")
            # Handle "3.500" meaning 3500 (not 3.5)
            # If there's exactly one dot and 3 digits after it, it's thousands
            parts = val.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                val = val.replace(".", "")
                return round(float(val) / 1000, 3) if float(val) > 100 else float(val)
            return round(float(val.replace("..", ".")), 3)

        # Pattern: X triệu or X tr
        m = re.search(r'(\d[\d.,]*)\s*(triệu|tr)', price_str)
        if m:
            val = float(m.group(1).replace(",", ".").replace("..", "."))
            return round(val / 1000, 3)

        # Pattern: raw number (VND)
        m = re.search(r'(\d[\d.,]+)', price_str)
        if m:
            val = m.group(1).replace(".", "").replace(",", "")
            num = float(val)
            if num > 1e8:  # More than 100 million VND
                return round(num / 1e9, 3)

    except (ValueError, TypeError):
        pass

    return None


def parse_area(area_str):
    """
    Parse area string to float (in m²).
    Examples:
        "85 m²" -> 85.0
        "120.5m2" -> 120.5
        "65,3 m²" -> 65.3
    """
    if not area_str:
        return None

    try:
        m = re.search(r'(\d[\d.,]*)\s*m[²2]?', area_str, re.IGNORECASE)
        if m:
            val = m.group(1).replace(",", ".")
            return float(val)
    except (ValueError, TypeError):
        pass

    return None


def classify_property_type(text):
    """Classify property type from title/description text."""
    text = text.lower()

    if any(kw in text for kw in ["căn hộ", "chung cư", "apartment", "condo", "penthouse"]):
        return "apartment"
    elif any(kw in text for kw in ["biệt thự", "villa"]):
        return "villa"
    elif any(kw in text for kw in ["đất nền", "đất thổ", "lô đất", "đất bán", "mặt bằng"]):
        return "land"
    elif any(kw in text for kw in ["nhà", "nhà phố", "nhà riêng", "nhà mặt tiền", "house", "townhouse"]):
        return "house"
    else:
        return "other"


def format_price_vnd(price_billion):
    """Format price in billions to readable Vietnamese string."""
    if price_billion is None:
        return "N/A"
    if price_billion >= 1:
        return f"{price_billion:.1f} tỷ"
    else:
        return f"{price_billion * 1000:.0f} triệu"


def format_price_per_m2(price_per_m2):
    """Format price per m2 to readable string."""
    if price_per_m2 is None:
        return "N/A"
    if price_per_m2 >= 1e6:
        return f"{price_per_m2/1e6:.1f} tr/m²"
    else:
        return f"{price_per_m2:,.0f} đ/m²"
