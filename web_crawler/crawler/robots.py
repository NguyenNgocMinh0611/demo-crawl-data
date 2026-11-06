import logging
import re
import time
import urllib.request
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

log = logging.getLogger(__name__)

# robots.txt chỉ cần đọc một lần cho mỗi domain khi crawl nhiều URL.
_CACHE: dict[str, tuple[RobotFileParser | None, str, float]] = {}
CRAWL_DELAY_RE = re.compile(r"^\s*crawl-delay\s*:\s*([\d.]+)", re.I | re.M)
CACHE_TTL = 3600.0
ROBOTS_UA = "Mozilla/5.0 (compatible; MyCrawler/1.0)"


def _load(origin: str) -> tuple[RobotFileParser | None, str]:
    cached = _CACHE.get(origin)
    if cached and time.time() - cached[2] < CACHE_TTL:
        return cached[0], cached[1]

    rp, text = None, ""
    robots_url = f"{origin}/robots.txt"
    try:
        request = urllib.request.Request(robots_url, headers={"User-Agent": ROBOTS_UA})
        with urllib.request.urlopen(request, timeout=20) as response:
            text = response.read().decode("utf-8", errors="replace")
        rp = RobotFileParser(robots_url)
        rp.parse(text.splitlines())
    except Exception as exc:  # noqa: BLE001
        log.warning("Không đọc được %s (%s) - coi như được phép", robots_url, exc)
        rp = None
    _CACHE[origin] = (rp, text, time.time())
    return rp, text


def _origin(url: str) -> str:
    parts = urlparse(url)
    return f"{parts.scheme}://{parts.netloc}"


def is_allowed(url: str, user_agent: str = "*") -> bool:
    """Kiểm tra robots.txt. Không đọc được file thì coi như được phép (và cảnh báo)."""
    rp, _ = _load(_origin(url))
    return True if rp is None else rp.can_fetch(user_agent, url)


def crawl_delay(url: str, default: float = 1.0) -> float:
    """Đọc Crawl-delay của site (Thegioididong yêu cầu 5s giữa hai request)."""
    _, text = _load(_origin(url))
    matches = [float(m.group(1)) for m in CRAWL_DELAY_RE.finditer(text)]
    return max(default, min(matches)) if matches else default
