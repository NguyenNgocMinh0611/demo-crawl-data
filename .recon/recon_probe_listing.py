"""Tìm URL listing thật sự chứa iPhone 15 trên tgdd/dmx rồi đếm card bằng parser thật."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "web_crawler"))

from config import Settings, BASE_DIR  # noqa: E402
from crawler.browser import open_page  # noqa: E402
from crawler.fetcher import fetch_html  # noqa: E402
from crawler.sites import SITES, parse_listing  # noqa: E402
from crawler.utils import force_utf8_stdio, polite_sleep, setup_logging  # noqa: E402

force_utf8_stdio()
CANDIDATES = [
    ("tgdd", "https://www.thegioididong.com/tim-kiem?q=iphone%2015"),
    ("tgdd", "https://www.thegioididong.com/dtdd/iphone-15"),
    ("tgdd", "https://www.thegioididong.com/dtdd/iphone-15-128gb"),
    ("tgdd", "https://www.thegioididong.com/dtdd/iphone-15-256gb"),
    ("dmx", "https://www.dienmayxanh.com/tim-kiem?k=iphone%2015"),
    ("dmx", "https://www.dienmayxanh.com/dien-thoai/iphone-15"),
    ("dmx", "https://www.dienmayxanh.com/dien-thoai-iphone-apple?p=2"),
    ("cellphones", "https://cellphones.com.vn/iphone-15-cu-dep.html"),
]
KW = re.compile(r"iphone\s*15", re.I)


def main() -> int:
    setup_logging(BASE_DIR / "logs")
    settings = Settings(engine="chromium", wait_selector=None, timeout_ms=40_000, max_retries=1, respect_robots=False)
    with open_page(settings) as page:
        for key, url in CANDIDATES:
            site = SITES[key]
            try:
                html = fetch_html(page, url, settings)
            except Exception as exc:  # noqa: BLE001
                print(f"{key:11s} LOI {exc}")
                continue
            if not html:
                print(f"{key:11s} khong tai duoc  {url}")
                continue
            page.wait_for_timeout(2500)
            refs = parse_listing(site, page.content())
            matched = [r["name"] for r in refs if KW.search(r["name"])]
            print(f"{key:11s} card={len(refs):3d} khop_ip15={len(matched):2d} {url}")
            for m in matched[:4]:
                print("      ", m)
            polite_sleep(2, 3)
    return 0


if __name__ == "__main__":
    sys.exit(main())
