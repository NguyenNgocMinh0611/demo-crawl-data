"""Cấu hình chung của crawler. Sửa tại đây hoặc ghi đè bằng tham số dòng lệnh."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class Settings:
    # --- Mục tiêu ---
    # Mặc định dùng trang sandbox dành riêng cho việc tập crawl.
    # Bản /js/ của trang này render dữ liệu bằng JavaScript -> dùng để test engine chromium.
    start_url: str = "https://quotes.toscrape.com/"
    max_pages: int = 3

    # --- Cách tải trang ---
    # "http": HTTP client tự xây dựng bằng stdlib urllib (mặc định, không cần trình duyệt).
    # "chromium": Playwright, dành cho trang chỉ render bằng JavaScript.
    engine: str = "http"  # "http" | "chromium"
    timeout_ms: int = 20_000
    wait_selector: Optional[str] = ".quote"  # đợi phần tử này xuất hiện (None = không đợi)
    user_agent: str = "Mozilla/5.0 (compatible; MyCrawler/1.0; +mailto:you@example.com)"
    # headless=False (bật bằng --headful) mở cửa sổ Chrome thật để xem crawler chạy,
    # chỉ có tác dụng với engine chromium.
    headless: bool = True
    slow_mo_ms: int = 0  # thêm chậm <ms> vào mỗi thao tác, chỉ xem được bằng mắt khi headful

    # --- Lịch sự với server ---
    delay_min: float = 1.0
    delay_max: float = 3.0
    max_retries: int = 3
    respect_robots: bool = True

    # --- Đầu ra ---
    output_dir: Path = BASE_DIR / "data"
    log_dir: Path = BASE_DIR / "logs"
    output_name: str = "quotes"

    # --- Crawl cửa hàng (iPhone 15 cũ / đã qua sử dụng) ---
    sites: str = "cellphones,tgdd,dmx"
    keyword: str = r"iphone\s*15"      # bộ lọc tên sản phẩm trên trang listing
    used_only: bool = True             # chỉ giữ máy cũ; tắt để lấy cả máy mới
    max_products: int = 8              # số trang chi tiết tối đa cho mỗi site
    product_output_name: str = "iphone15"
    # TGDĐ/DMX là app Next.js: khi dùng engine chromium, giá và khối "Mua ngay"
    # chỉ xuất hiện sau khi JS hydrate xong.
    render_wait_ms: int = 2500
