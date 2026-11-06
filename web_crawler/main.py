import argparse
import logging
import re
import sys

from config import Settings
from crawler.http_client import fetch as fetch_http
from crawler.parsers import find_next_url, parse_quotes
from crawler.robots import crawl_delay, is_allowed
from crawler.sites import SITES, USED_RE, parse_detail, parse_listing
from crawler.storage import dedupe, dedupe_by, save, save_products
from crawler.utils import force_utf8_stdio, polite_sleep, setup_logging

log = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    d = Settings()
    ap = argparse.ArgumentParser(description="Web crawler: tải HTML bằng HTTP client tự xây, tùy chọn chromium cho trang JS")
    ap.add_argument("--start-url", default=d.start_url)
    ap.add_argument("--max-pages", type=int, default=d.max_pages)
    ap.add_argument("--engine", choices=["http", "chromium"], default=None,
                    help=f"mặc định {d.engine}; 'http' dùng stdlib urllib, "
                         "'chromium' dùng Playwright cho trang render bằng JS; --headful buộc dùng chromium")
    ap.add_argument("--wait-selector", default=None,
                    help=f"CSS selector cần đợi xuất hiện (mặc định {d.wait_selector!r} cho demo quotes, "
                         "bỏ trống khi crawl cửa hàng)")
    ap.add_argument("--headful", action="store_true",
                    help="mở cửa sổ trình duyệt thật để xem crawler chạy (chỉ engine chromium)")
    ap.add_argument("--slow-mo", type=int, default=d.slow_mo_ms, metavar="MS",
                    help="chậm lại MS mili-giây mỗi thao tác, dễ nhìn khi dùng --headful")
    ap.add_argument("--sites", default=None,
                    help=f"crawl sản phẩm thay vì demo quotes, vd: cellphones,tgdd,dmx (có: {','.join(SITES)})")
    ap.add_argument("--keyword", default=d.keyword,
                    help="regex lọc tên sản phẩm trên trang listing (mặc định %(default)s)")
    ap.add_argument("--all-conditions", action="store_true",
                    help="không giới hạn máy cũ, lấy cả máy mới chính hãng")
    ap.add_argument("--max-products", type=int, default=d.max_products, metavar="N",
                    help="số trang chi tiết tối đa cho mỗi site")
    return ap.parse_args()


def crawl(settings: Settings) -> list:
    if settings.respect_robots and not is_allowed(settings.start_url):
        log.error("robots.txt không cho phép crawl %s - dừng.", settings.start_url)
        return []

    if settings.engine == "chromium":
        from crawler.browser import open_page
        from crawler.fetcher import fetch_html

        with open_page(settings) as page:
            return _crawl_demo(settings, lambda url: fetch_html(page, url, settings))
    return _crawl_demo(settings, lambda url: fetch_http(
        url, user_agent=settings.user_agent, timeout_ms=settings.timeout_ms,
        max_retries=settings.max_retries,
    ))


def _crawl_demo(settings: Settings, get_html) -> list:
    items, visited = [], set()
    url = settings.start_url

    for n in range(1, settings.max_pages + 1):
        if not url or url in visited:
            break
        visited.add(url)

        log.info("[%s/%s] %s", n, settings.max_pages, url)
        html = get_html(url)
        if html is None:
            break

        found = parse_quotes(html)
        log.info("  -> %s mục", len(found))
        items.extend(found)

        url = find_next_url(html, url)
        if url:
            polite_sleep(settings.delay_min, settings.delay_max)

    return dedupe(items)


def pick_products(settings: Settings, refs: list) -> list:
    keyword = re.compile(settings.keyword, re.I)
    matched = []
    for ref in refs:
        name = ref.get("name", "")
        if not keyword.search(name):
            continue
        if settings.used_only and not USED_RE.search(name):
            continue
        matched.append(ref)
    return dedupe_by(matched, "url")[: settings.max_products]


def wait_for(site_url: str, settings: Settings) -> None:
    delay = crawl_delay(site_url, default=settings.delay_min)
    polite_sleep(delay, delay * 1.5)


def crawl_products(settings: Settings) -> list:
    if settings.engine == "chromium":
        from crawler.browser import open_page
        from crawler.fetcher import fetch_rendered

        with open_page(settings) as page:
            return _crawl_products_with(settings, lambda url: fetch_rendered(page, url, settings))
    return _crawl_products_with(settings, lambda url: fetch_http(
        url, user_agent=settings.user_agent, timeout_ms=settings.timeout_ms,
        max_retries=settings.max_retries,
    ))


def _crawl_products_with(settings: Settings, get_html) -> list:
    items, visited = [], set()
    keys = [k.strip() for k in settings.sites.split(",") if k.strip()]

    for key in keys:
        site = SITES.get(key)
        if site is None:
            log.error("Không có site %r - chọn một trong: %s", key, ", ".join(SITES))
            continue

        refs = []
        for listing_url in (site.listing_url, *site.extra_listings):
            if settings.respect_robots and not is_allowed(listing_url):
                log.warning("robots.txt không cho phép crawl %s", listing_url)
                continue
            log.info("[%s] trang listing: %s", site.label, listing_url)
            html = get_html(listing_url)
            if not html:
                continue
            found = parse_listing(site, html)
            log.info("  -> %s link sản phẩm", len(found))
            refs.extend(found)
            wait_for(listing_url, settings)

        chosen = pick_products(settings, refs)
        log.info("[%s] %s sản phẩm khớp bộ lọc %r", site.label, len(chosen), settings.keyword)

        for n, ref in enumerate(chosen, 1):
            url = ref["url"]
            if url in visited:
                continue
            if settings.respect_robots and not is_allowed(url):
                log.warning("  robots.txt chặn %s - bỏ qua", url)
                continue
            visited.add(url)

            wait_for(url, settings)
            log.info("  [%s/%s] %s", n, len(chosen), url)
            html = get_html(url)
            if not html:
                continue
            product = parse_detail(site, html, ref)
            items.append(product)
            log.info(
                "      %s | %s | %s | %s | %s ảnh",
                product["name"][:48],
                product["condition"],
                product["price_text"].strip() or "chưa rõ giá",
                product["stock"] or "chưa rõ hàng",
                len(product["images"]),
            )

    return dedupe_by(items, "url")


def main() -> int:
    force_utf8_stdio()
    args = parse_args()
    defaults = Settings()
    auto_engine = args.engine is None and args.headful
    product_mode = args.sites is not None
    wait_selector = args.wait_selector if args.wait_selector is not None else (
        None if product_mode else defaults.wait_selector
    )
    settings = Settings(
        start_url=args.start_url,
        max_pages=args.max_pages,
        engine=args.engine or ("chromium" if args.headful else defaults.engine),
        wait_selector=wait_selector or None,
        headless=not args.headful,
        slow_mo_ms=max(0, args.slow_mo),
        sites=args.sites or defaults.sites,
        keyword=args.keyword,
        used_only=not args.all_conditions,
        max_products=args.max_products,
    )
    setup_logging(settings.log_dir)
    if auto_engine:
        log.info("--headful cần cửa sổ trình duyệt thật -> dùng engine chromium.")

    try:
        items = crawl_products(settings) if product_mode else crawl(settings)
    except Exception as exc:  # noqa: BLE001
        log.exception("Crawler gặp lỗi: %s", exc)
        if settings.engine == "http":
            log.error("Gợi ý: nếu trang chỉ render bằng JavaScript, thử --engine chromium "
                      "(cần chạy: playwright install chromium)")
        return 1

    if not items:
        log.warning("Không thu được dữ liệu nào.")
        return 1

    if product_mode:
        json_path, csv_path = save_products(items, settings.output_dir, settings.product_output_name)
    else:
        json_path, csv_path = save(items, settings.output_dir, settings.output_name)
    log.info("Xong: %s mục -> %s , %s", len(items), json_path, csv_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
