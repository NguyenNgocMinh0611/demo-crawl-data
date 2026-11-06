"""Render trang chi tiết bằng Chromium rồi probe selector tên/giá/tình trạng/mô tả/ảnh."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "web_crawler"))

from bs4 import BeautifulSoup  # noqa: E402
from config import Settings  # noqa: E402
from crawler.browser import open_page  # noqa: E402
from crawler.fetcher import fetch_html  # noqa: E402
from crawler.utils import force_utf8_stdio, setup_logging  # noqa: E402

force_utf8_stdio()
OUT = Path(__file__).resolve().parent / "rendered"

URLS = [
    ("cell", "https://cellphones.com.vn/iphone-15-cu-dep.html"),
    ("tgdd", "https://www.thegioididong.com/dtdd/iphone-15"),
    ("dmx", "https://www.dienmayxanh.com/dien-thoai/iphone-15-128gb"),
]
STOCK = re.compile(r"còn hàng|hết hàng|ngừng kinh doanh|tạm hết|còn làm giá|mua ngay|đặt mua|hết", re.I)
PRICE = re.compile(r"^[\d.,]{5,}\s*[đ₫]$")


def probe(name: str, html: str) -> None:
    (OUT / f"detail_{name}.html").write_text(html, encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    print(f"\n{'='*24} {name} bytes={len(html)}")
    h1 = soup.find(["h1"], class_=True) or soup.find("h1")
    print("  H1:", h1.get_text(" ", strip=True)[:70], "| class=", " ".join(h1.get("class") or [])[:60])
    hits, prices = [], []
    for el in soup.find_all(["span", "div", "p", "a", "button", "strong", "li"], recursive=True):
        t = el.get_text(" ", strip=True)
        if len(t) > 40:
            continue
        if STOCK.search(t):
            hits.append((el.name, " ".join(el.get("class") or []), t))
        if PRICE.match(t):
            prices.append((el.name, " ".join(el.get("class") or []), t))
    uniq = []
    for h in hits:
        if h not in uniq:
            uniq.append(h)
    print("  STOCK ứng viên:")
    for h in uniq[:10]:
        print(f"    <{h[0]}> .{h[1][:56]} :: {h[2][:36]}")
    print("  PRICE ứng viên:", prices[:4])
    imgs = [i.get("src") or i.get("data-src") for i in soup.find_all("img") if (i.get("src") or i.get("data-src"))]
    gal = [x for x in imgs if re.search(r"product|catalog|media|thumb", x, re.I)]
    print(f"  IMG total={len(imgs)} gallery-ish={len(gal)}")
    for g in gal[:4]:
        print("    ", g[:110])
    desc = [el for el in soup.find_all(["div", "section", "article"]) if 150 < len(el.get_text(" ", strip=True)) < 3000 and not el.find_all(["div", "section"])]
    print("  DESC lá:")
    for d in desc[:6]:
        print(f"    <{d.name}> .{' '.join(d.get('class') or [])[:50]} len={len(d.get_text(strip=True))} :: {d.get_text(' ', strip=True)[:70]}")


def main() -> int:
    setup_logging(ROOT / "web_crawler" / "logs")
    settings = Settings(engine="chromium", wait_selector=None, timeout_ms=45_000, max_retries=1, user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ))
    with open_page(settings) as page:
        for name, url in URLS:
            print(f"\n>>> {name} {url}", flush=True)
            try:
                html = fetch_html(page, url, settings)
            except Exception as exc:  # noqa: BLE001
                print("  LOI:", exc)
                continue
            page.wait_for_timeout(4000)
            probe(name, page.content())
    return 0


if __name__ == "__main__":
    sys.exit(main())
