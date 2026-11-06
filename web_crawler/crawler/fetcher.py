import logging
import time
from typing import Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from config import Settings

log = logging.getLogger(__name__)


def fetch_rendered(page: Page, url: str, settings: Settings) -> Optional[str]:
    """Như fetch_html nhưng chờ SPA hydrate rồi đọc lại DOM.

    Thegioididong/Dienmayxanh là ứng dụng Next.js: giá, nút "Mua ngay" và khối
    mô tả chỉ xuất hiện sau khi JavaScript chạy xong.
    """
    html = fetch_html(page, url, settings)
    if html is None:
        return None
    wait_ms = getattr(settings, "render_wait_ms", 0)
    if wait_ms:
        page.wait_for_timeout(wait_ms)
        return page.content()
    return html


def fetch_html(page: Page, url: str, settings: Settings) -> Optional[str]:
    """Tải trang, retry với backoff khi lỗi/429/503. Trả về HTML hoặc None nếu thất bại."""
    for attempt in range(1, settings.max_retries + 1):
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=settings.timeout_ms)
            status = resp.status if resp else None

            if status in (429, 503):
                wait = 5 * 2 ** attempt
                log.warning("HTTP %s tại %s - chờ %ss (lần %s)", status, url, wait, attempt)
                time.sleep(wait)
                continue
            if status is not None and status >= 400:
                log.error("HTTP %s tại %s - bỏ qua", status, url)
                return None

            if settings.wait_selector:
                try:
                    page.wait_for_selector(settings.wait_selector, timeout=5_000)
                except PlaywrightError:
                    log.warning("Không thấy selector %r tại %s", settings.wait_selector, url)

            return page.content()
        except PlaywrightError as exc:
            wait = 2 ** attempt
            log.warning("Lỗi tải %s: %s - thử lại sau %ss (lần %s)", url, exc, wait, attempt)
            time.sleep(wait)

    log.error("Thất bại sau %s lần: %s", settings.max_retries, url)
    return None
