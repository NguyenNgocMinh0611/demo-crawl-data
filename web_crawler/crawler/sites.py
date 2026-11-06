"""Adapter crawl sản phẩm theo từng trang bán hàng.

Mỗi site có "URL vào trang" (listing/kết quả tìm kiếm) và 2 hàm parse:
    parse_listing -> danh sách tham chiếu sản phẩm (URL + dữ liệu thô trên card)
    parse_detail  -> sản phẩm đầy đủ 5 trường: tên, mô tả, giá, tình trạng, ảnh

Thế Giới Di Động và Điện máy XANH dùng chung hạ tầng Next.js của Mobile World
(selector giống nhau, chỉ khác URL vào trang), CellphoneS là Magento.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

WS = re.compile(r"\s+")
PRICE_RE = re.compile(r"(?:\d{1,3}(?:[.,]\d{3})+)(?:\s*[đ₫])?")
USED_RE = re.compile(r"cũ|like[\s-]*new|\bold\b|đã qua sử dụng|qua sử dụng|thanh lý|máy\s*2nd", re.I)
DEAD_RE = re.compile(r"h[eế]t h[aà]ng|ng[uừ]ng kinh doanh|t[aạ]m h[eế]t|ngừng bán", re.I)
BUY_RE = re.compile(r"mua ngay|ch[ọo]n mua|đặt mua|th[aè]m vào giỏ|mua online", re.I)


def clean(text: str) -> str:
    return WS.sub(" ", (text or "")).strip()


def to_vnd(text: str) -> Optional[int]:
    """'14.990.000đ' -> 14990000."""
    m = PRICE_RE.search(text or "")
    return int(m.group(0).translate(str.maketrans("", "", ".,đ₫ "))) if m else None


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def canonical(url: str) -> str:
    """Bỏ query/fragment để khỏi crawl trùng biến thể màu/dung lượng."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def product_condition(name: str, default: str = "Mới / chính hãng") -> str:
    """Suy tình trạng máy từ tên sản phẩm (nhà bán ghi thẳng vào tên)."""
    m = re.search(r"(cũ\s*đẹp|cũ\s*xước\s*cấn?|cũ\s*trầy\s*xước|cũ|like\s*new|old)", name or "", re.I)
    if not m:
        return default
    label = clean(m.group(1)).lower()
    special = {
        "cũ đẹp": "Cũ Đẹp",
        "cũ xước cấn": "Cũ Xước Cấn",
        "cũ xước can": "Cũ Xước Cấn",
        "cũ trầy xước": "Cũ Trầy Xước",
        "cũ": "Cũ",
        "like new": "Like New",
        "old": "Old",
    }
    return special.get(label, label.title())


@dataclass(frozen=True)
class Site:
    key: str
    label: str
    listing_url: str
    parser: str  # "cellphones" | "mwg"
    product_prefix: str = ""  # chỉ tính link bắt đầu bằng path này (mwg)
    extra_listings: tuple[str, ...] = ()
    notes: str = field(default="", compare=False)


SITES: dict[str, Site] = {
    "cellphones": Site(
        key="cellphones",
        label="CellphoneS",
        # Trang danh mục "iPhone 15 cũ" render sẵn HTML ở server (dùng được
        # với HTTP client thường); trang tìm kiếm chỉ render bằng JavaScript.
        listing_url="https://cellphones.com.vn/hang-cu/iphone/iphone-15.html",
        parser="cellphones",
        notes="Nơi duy nhất trong 3 trang có máy cũ/đã qua sử dụng.",
    ),
    "tgdd": Site(
        key="tgdd",
        label="Thegioididong",
        listing_url="https://www.thegioididong.com/dtdd/iphone-15",
        parser="mwg",
        product_prefix="/dtdd/",
        notes="Không kinh doanh máy cũ - chỉ có máy mới chính hãng.",
    ),
    "dmx": Site(
        key="dmx",
        label="Dienmayxanh",
        listing_url="https://www.dienmayxanh.com/dien-thoai/iphone-15",
        parser="mwg",
        product_prefix="/dien-thoai/",
        extra_listings=("https://www.dienmayxanh.com/dien-thoai-iphone-apple?p=2",),
        notes="Không kinh doanh máy cũ - chỉ có máy mới chính hãng.",
    ),
}

# Card quảng cáo/video trên trang dòng sản phẩm, không phải sản phẩm để mua.
PROMO_NAME_RE = re.compile(r"tổng quan|overview|video|đánh giá", re.I)


# ---------------------------------------------------------------- listing ----


def parse_listing(site: Site, html: str) -> list[dict]:
    soup = soup_of(html)
    refs = (parse_cellphones_listing(soup, site) if site.parser == "cellphones"
            else parse_mwg_listing(soup, site))
    for ref in refs:
        ref["source"] = site.key
        ref["site_label"] = site.label
    return refs


def parse_cellphones_listing(soup: BeautifulSoup, site: Site) -> list[dict]:
    """Card CellphoneS có 2 kiểu: trang tìm kiếm (.product-item, h3[title])
    và trang danh mục (a.product__link, h3 trong .product__name, giá
    .product__price--show / --through)."""
    out = []
    for card in soup.select(".product-item, .product-info-container"):
        anchor = card.select_one("a.product__link") or card.select_one("a[href]")
        title_el = card.select_one("h3[title]") or card.select_one(".product__name h3, h3")
        name = clean(title_el.get_text()) if title_el else ""
        if anchor is None or not name:
            continue
        price_el = card.select_one(
            "p.text-primary-600, p.product__price--show, .price-box .price, p"
        )
        img = card.select_one("img[src]")
        out.append(
            {
                "url": urljoin(site.listing_url, anchor["href"]),
                "name": name,
                "price_text": clean(price_el.get_text()) if price_el else "",
                "image": img["src"] if img else None,
            }
        )
    return out


def parse_mwg_listing(soup: BeautifulSoup, site: Site) -> list[dict]:
    """Thẻ sản phẩm của Mobile World: đi từ ảnh /Products/Images/ rồi leo lên tới card.

    Mỗi card có nhiều link biến thể (dung lượng/màu) trỏ về cùng một sản phẩm,
    nên lấy link đầu tiên của card và khử trùng theo URL đã bỏ query.
    """
    out, seen = [], set()
    is_product = lambda h: bool(h) and h.startswith(site.product_prefix)  # noqa: E731
    for img in soup.find_all("img", src=re.compile(r"/Products/Images/")):
        name = clean(img.get("alt") or img.get("aria-label") or "")
        if len(name) < 4 or PROMO_NAME_RE.search(name):
            continue
        card = _card_for(img, is_product)
        if card is None:
            continue
        anchor = card.find("a", href=is_product)
        if anchor is None:
            continue
        url = canonical(urljoin(site.listing_url, anchor["href"]))
        if url in seen:
            continue
        seen.add(url)
        price_el = card.find(string=PRICE_RE)
        out.append(
            {
                "url": url,
                "name": name,
                "price_text": clean(price_el) if price_el else "",
                "image": img["src"],
            }
        )
    return out


def _card_for(img, is_product, max_hops: int = 6):
    """Phần tử cha gần nhất vừa chứa link sản phẩm vừa chứa số tiền = card hoàn chỉnh."""
    node = img
    for _ in range(max_hops):
        node = node.parent
        if node is None or node.name == "[document]":
            return None
        if node.find("a", href=is_product) and PRICE_RE.search(clean(node.get_text(" "))):
            return node
    return None


# ----------------------------------------------------------------- detail ----


def parse_detail(site: Site, html: str, ref: dict) -> dict:
    soup = soup_of(html)
    if site.parser == "cellphones":
        name, price, old_price, stock, description, images = _cellphones_detail(soup, site, ref)
    else:
        name, price, old_price, stock, description, images = _mwg_detail(soup, site, ref)

    full_name = name or ref.get("name", "")
    return {
        "source": site.key,
        "site_label": site.label,
        "name": full_name,
        "condition": product_condition(full_name),
        "price_text": price or ref.get("price_text", ""),
        "price_vnd": to_vnd(price) or to_vnd(ref.get("price_text", "")),
        "old_price_vnd": to_vnd(old_price) if old_price else None,
        "stock": stock,
        "in_stock": bool(stock and not DEAD_RE.search(stock)),
        "description": clean(description)[:1200],
        "images": images,
        "url": ref["url"],
        "crawled_at": datetime.now().isoformat(timespec="seconds"),
    }


def _cellphones_detail(soup, site, ref):
    h1 = soup.find("h1")
    name = clean(h1.get_text()) if h1 else ref.get("name", "")

    price_el = soup.select_one(".sale-price") or soup.select_one(".item-variant-price")
    price = clean(price_el.get_text()) if price_el else ""
    old_el = soup.select_one("del.base-price, .line-through, .old-price, del")
    old_price = clean(old_el.get_text()) if old_el else ""

    stock = ""
    count = soup.select_one(".box-on-stock-count")
    if count:
        n = re.search(r"c[óo]\s+(\d+)", clean(count.get_text()), re.I)
        stock = f"Còn hàng ({n.group(1)} chi nhánh)" if n else "Còn hàng"
    if not stock:
        # Trang máy cũ không có khối tồn kho mà thay bằng nút "MUA NGAY".
        buy_btn = soup.select_one("button.order-button")
        if buy_btn and BUY_RE.search(clean(buy_btn.get_text())):
            stock = "Còn hàng - Mua ngay"
    if not stock:
        body = clean(soup.get_text(" "))
        dead = DEAD_RE.search(body)
        if dead and (h1 is None or dead.start() < 4000):
            stock = "Hết hàng / ngừng kinh doanh"
        elif BUY_RE.search(body):
            stock = "Còn hàng"

    desc_parts = []
    for el in soup.select(
        "#productDetailV2 .description, .cps-block-description .description, "
        ".box-content .description, #cpsContentSEO p"
    ):
        text = clean(el.get_text(" "))
        if len(text) > 60 and text not in desc_parts:
            desc_parts.append(text)
    description = " | ".join(desc_parts[:3])

    images = _images(soup, r"/media/catalog/product/")
    return name, price, old_price, stock, description, images


def _mwg_detail(soup, site, ref):
    h1 = soup.find("h1")
    name = clean(h1.get_text()) if h1 else ref.get("name", "")
    name = re.sub(r"^(điện thoại|máy tính bảng|laptop)\s+", "", name, flags=re.I)

    price_el = _find_price_el(soup)
    price = clean(price_el.get_text(" ")) if price_el else ""
    old_price = _old_price_in(_buy_box(price_el))

    candidates = [clean(el.get_text(" ")) for el in soup.select("#description-text-detail, #description-product-detail")]
    candidates += [
        clean(el.get_text(" "))
        for el in soup.find_all(["div", "section"])
        if not el.find_all(["div", "section"])
    ]
    description = max((c for c in candidates if 60 < len(c) < 2500), key=len, default="")

    return name, price, old_price, _mwg_stock(price_el), description, _images(soup, r"/Products/Images/")


def _find_price_el(soup):
    """Giá hiện tại của Mobile World nằm trong khối màu đỏ; nếu không thì là số tiền đầu tiên."""
    for el in soup.find_all(["span", "p", "div"], class_=re.compile(r"text-red")):
        if PRICE_RE.fullmatch(clean(el.get_text(" "))):
            return el
    for el in soup.find_all(["span", "p"]):
        if PRICE_RE.fullmatch(clean(el.get_text())):
            return el
    return None


def _buy_box(price_el):
    """Khối quanh giá, dùng riêng để không lấy nhầm banner 'Quà 390.000₫' của cả trang."""
    node = price_el
    for _ in range(6):
        if node is None:
            return None
        if node.find(["del", "s"], string=PRICE_RE):
            return node
        node = node.parent
    return price_el.parent if price_el else None


def _old_price_in(box) -> str:
    if box is None:
        return ""
    el = box.find(["del", "s"], string=PRICE_RE)
    return clean(el.get_text()) if el else ""


def _mwg_stock(price_el) -> str:
    """Mobile World không in chữ 'Còn hàng' mà thay bằng nút mua.

    Chỉ xét khối quanh giá: tìm trong cả trang sẽ ăn nhầm chữ 'hết' trong
    phần bình luận của khách.
    """
    node = price_el
    for _ in range(8):
        if node is None:
            break
        labels = [clean(el.get_text(" ")) for el in node.find_all(["button", "a"])]
        labels = [t for t in labels if len(t) < 40]
        dead = next((t for t in labels if DEAD_RE.search(t)), None)
        if dead:
            return dead
        buy = next((t for t in labels if BUY_RE.search(t)), None)
        if buy:
            return f"Còn hàng - {buy}"
        node = node.parent
    return ""


NOISE_IMG_RE = re.compile(r"thumbvideo|logo|icon|avatar|banner|voucher|sprite|\.svg|\.gif", re.I)


def _images(soup, pattern: str, limit: int = 10) -> list[str]:
    """Ảnh sản phẩm từ <img src> lẫn <a href> (gallery của CellphoneS để ảnh
    trong href, <img> bên trong chỉ là placeholder lazy-load)."""
    out, seen = [], set()
    for tag in soup.find_all(["img", "a"]):
        src = tag.get("src") or tag.get("href") or ""
        if not re.search(pattern, src, re.I):
            continue
        if NOISE_IMG_RE.search(src):
            continue
        if src.startswith("//"):
            src = "https:" + src
        base = _original_image(src).split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        out.append(base)
        if len(out) >= limit:
            break
    return out


def _original_image(src: str) -> str:
    """URL qua imgproxy (\\|/plain/\\|) trả về ảnh gốc, không bị ép còn thumbnail 80px."""
    _, _, origin = src.partition("/plain/")
    return origin if origin.startswith("http") else src
