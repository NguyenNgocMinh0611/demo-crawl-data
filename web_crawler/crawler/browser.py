"""Mở trình duyệt Chromium và trả về một Page của Playwright (chỉ khi --engine chromium)."""
import logging
from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import Page, sync_playwright

from config import Settings

log = logging.getLogger(__name__)


@contextmanager
def open_page(settings: Settings) -> Iterator[Page]:
    with sync_playwright() as p:
        log.info(
            "Khởi động Chromium %s%s...",
            "headless" if settings.headless else "cửa sổ thật",
            f" (slow_mo={settings.slow_mo_ms}ms)" if settings.slow_mo_ms else "",
        )
        browser = p.chromium.launch(headless=settings.headless, slow_mo=settings.slow_mo_ms)
        try:
            # no_viewport để trang chiếm hết cửa sổ khi bật --headful.
            context = browser.new_context(
                user_agent=settings.user_agent,
                no_viewport=not settings.headless,
            )
            page = context.new_page()
            yield page
        finally:
            browser.close()
