"""In ra 1 card sản phẩm đầy đủ của mỗi trang để thiết kế selector."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "web_crawler"))
from bs4 import BeautifulSoup  # noqa: E402
from crawler.utils import force_utf8_stdio  # noqa: E402

force_utf8_stdio()
HERE = Path(__file__).resolve().parent / "rendered"

PATTERNS = {
    "tgdd_dtdd_after_wait.html": r"^/phone/",
    "cellphones_search_after_wait.html": r"\.html$",
    "dmx_iphone_after_wait.html": r"^/dien-thoai/",
}
KEYWORD = re.compile(r"iphone 15", re.I)


def card_of(el):
    """Leo lên các phần tử cha tới khi có cả img lẫn link sản phẩm."""
    node = el
    for _ in range(8):
        node = node.parent
        if node is None:
            return None
        if node.find("img") and node.name in ("li", "div", "article"):
            return node
    return None


for fname, pat in PATTERNS.items():
    path = HERE / fname
    if not path.exists():
        print("thieu file", fname)
        continue
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    links = [a for a in soup.find_all("a", href=re.compile(pat)) if a.get_text(" ", strip=True)]
    print(f"\n{'='*30}{fname}  so link san pham = {len(links)}")
    picked = [a for a in links if KEYWORD.search(a.get_text(" ", strip=True))] or links[:1]
    for a in picked[:2]:
        c = card_of(a)
        print(f"--- link: {a['href']} | text: {a.get_text(' ', strip=True)[:60]}")
        print(f"    card tag=<{c.name if c else None}> class={' '.join((c.get('class') or []))[:60] if c else ''}")
        if c:
            print(re.sub(r">\s+<", ">\n<", str(c))[:1400])
