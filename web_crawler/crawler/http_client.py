"""HTTP client tự xây dựng bằng stdlib (urllib) - không cần trình duyệt.

Xử lý: redirect, giải nén gzip, nhận diện charset (header Content-Type
-> <meta charset> -> utf-8), retry lùi dần khi lỗi mạng / 429 / 5xx.

Dùng cho các trang render sẵn HTML ở server. Trang chỉ render bằng
JavaScript thì dùng engine chromium (Playwright) thay thế.
"""
from __future__ import annotations

import gzip
import logging
import re
import time
import urllib.error
import urllib.request
from typing import Optional

log = logging.getLogger(__name__)

_META_CHARSET = re.compile(br"""<meta[^>]+charset\s*=\s*["']?\s*([\w-]+)""", re.I)
_RETRY_STATUS = {429, 500, 502, 503, 504}
_GZIP_MAGIC = b"\x1f\x8b"


def fetch(url: str, *, user_agent: str, timeout_ms: int = 20_000,
          max_retries: int = 3) -> Optional[str]:
    """Tải URL, trả về HTML (str) hoặc None nếu bỏ cuộc sau mọi lần thử."""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    }
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_ms / 1000) as resp:
                return _decode(resp.read(), resp.headers)
        except urllib.error.HTTPError as exc:
            if exc.code not in _RETRY_STATUS:
                log.error("HTTP %s tại %s - bỏ qua", exc.code, url)
                return None
            wait = _backoff(attempt, extra=1.0 if exc.code == 429 else 0.0)
            log.warning("HTTP %s tại %s - thử lại lần %s sau %.1fs", exc.code, url, attempt + 1, wait)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == max_retries:
                log.error("Thất bại sau %s lần thử: %s (%s)", max_retries + 1, url, exc)
                return None
            wait = _backoff(attempt)
            log.warning("Lỗi tải %s (%s) - thử lại lần %s sau %.1fs", url, exc, attempt + 1, wait)
        time.sleep(wait)
    return None


def _backoff(attempt: int, extra: float = 0.0) -> float:
    """1s, 2s, 4s... tối đa 15s; 429 cộng thêm 1s vì server yêu cầu chờ lâu hơn."""
    return min(extra + 2 ** attempt, 15.0)


def _decode(raw: bytes, headers) -> str:
    if headers.get("Content-Encoding", "").lower() == "gzip" or raw[:2] == _GZIP_MAGIC:
        raw = gzip.decompress(raw)

    enc = None
    ctype = headers.get("Content-Type", "")
    m = re.search(r"charset\s*=\s*([\w-]+)", ctype, re.I)
    if m:
        enc = m.group(1)
    if enc is None:
        m = _META_CHARSET.search(raw[:4096])
        if m:
            enc = m.group(1).decode("ascii", "ignore")

    for candidate in (enc, "utf-8"):
        if not candidate:
            continue
        try:
            return raw.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")
