"""Khảo sát DOM thật của 3 trang: render bằng Chromium rồi dump HTML + phỏng đoán selector."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "web_crawler"))

from bs4 import BeautifulSoup  # noqa: E402
from crawler.utils import force_utf8_stdio, setup_logging  # noqa: E402
from config import Settings  # noqa: E402
from crawler.browser import open_page  # noqa: E402
from crawler.fetcher import fetch_html  # noqa: E402

force_utf8_stdio()
OUT = Path(__file__).resolve().parent / "rendered"
OUT.mkdir(exist_ok=True)

PRICE_RE = re.compile(r"(?:\d{1,3}(?:[.,]\d{3})+\s*₫|₫\s*\d{1,3}(?:[.,]\d{3})+|\d{1,3}(?:[.,]\d{3})+\s*(?:đ|VN?D))", re.I)

TARGETS = {
    "tgdd_search": "https://www.thegioididong.com/tim-kiem?q=iPhone%2015%20c%C5%A9",
    "tgdd_dtdd": "https://www.thegioididong.com/dtdd",
    "cellphones_search": "https://cellphones.com.vn/catalogsearch/result/?q=iphone%2015%20cu",
    "cellphones_iphone_cu": "https://cellphones.com.vn/dien-thoai-iphone-cu.html",
    "dmx_search": "https://www.dienmayxanh.com/tim-kiem?k=iPhone%2015%20c%C5%A9",
    "dmx_iphone": "https://www.dienmayxanh.com/dien-thoai-iphone-apple",
}


def report(name: str, html: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    (OUT / f"{name}.html").write_text(html, encoding="utf-8")
    nodes = [el for el in soup.find_all(["li", "div", "article", "a"]) if PRICE_RE.search(el.get_text(" ", strip=True))]
    # lấy những node "gọn" nhất chứa giá = khả năng là card sản phẩm
    cards = [n for n in nodes if not any(n is not m and m in n.descendants and PRICE_RE.search(m.get_text(" ", strip=True)) for m in nodes)]
    print(f"\n########## {name}  bytes={len(html)}  gia_nodes={len(nodes)}  cards={len(cards)}")
    for card in cards[:4]:
        classes = card.get("class") or []
        print(f"  tag=<{card.name}> class={' '.join(classes)[:70]}")
        print("   text:", card.get_text(" ", strip=True)[:160])
        a = card.find("a", href=True) or (card if card.name == "a" else None)
        img = card.find("img")
        print("   href:", (a["href"] if a else None))
        print("   img:", (img.get("src") or img.get("data-src") or img.get("data-original") if img else None))
        for sub in card.find_all(True, limit=14):
            sc = " ".join(sub.get("class") or [])
            if sc:
                print(f"     <{sub.name}> .{sc[:52]} :: {sub.get_text(' ', strip=True)[:60]}")


def main() -> int:
    setup_logging(ROOT / "web_crawler" / "logs")
    settings = Settings(engine="chromium", wait_selector=None, timeout_ms=45_000, max_retries=1)
    summary = {}
    with open_page(settings) as page:
        for name, url in TARGETS.items():
            print(f"\n>>> {name}: {url}", flush=True)
            try:
                html = fetch_html(page, url, settings)
            except Exception as exc:  # noqa: BLE001
                print("  LOI:", exc)
                continue
            if not html:
                print("  khong lay duoc html")
                continue
            report(name, html)
            page.wait_for_timeout(3000)
            html2 = page.content()
            report(name + "_after_wait", html2)
            summary[name] = len(re.findall(r"iPhone 15", html2, re.I))
    print("\nso lan xuat hien 'iPhone 15' sau khi render:", json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
