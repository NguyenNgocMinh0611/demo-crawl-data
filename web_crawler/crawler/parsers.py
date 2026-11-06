"""Parser thuần HTML -> dữ liệu. Không phụ thuộc trình duyệt nên test offline được.

Muốn crawl trang khác: viết hàm parse_xxx + find_next_url tương ứng rồi đổi trong main.py.
"""
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_quotes(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for block in soup.select("div.quote"):
        text_el = block.select_one("span.text")
        author_el = block.select_one("small.author")
        if not text_el or not author_el:
            continue
        items.append(
            {
                "text": text_el.get_text(strip=True),
                "author": author_el.get_text(strip=True),
                "tags": [t.get_text(strip=True) for t in block.select("a.tag")],
            }
        )
    return items


def find_next_url(html: str, current_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one("li.next > a")
    if link and link.get("href"):
        return urljoin(current_url, link["href"])
    return None
