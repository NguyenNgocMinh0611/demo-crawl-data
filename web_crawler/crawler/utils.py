import io
import logging
import random
import sys
import time
from pathlib import Path


class _MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int) -> None:
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


def force_utf8_stdio() -> None:
    """Ép stdout/stderr dùng UTF-8.

    Mặc định trên Windows, khi redirect ra file/pipe, Python dùng codepage hệ
    điều hành (cp1252) và mọi dòng log tiếng Việt sẽ ném UnicodeEncodeError,
    logging in kèm traceback đỏ.
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, OSError, ValueError):
            buffer = getattr(stream, "buffer", None)
            if buffer is not None:
                setattr(
                    sys,
                    name,
                    io.TextIOWrapper(buffer, encoding="utf-8", errors="backslashreplace", line_buffering=True),
                )


def setup_logging(log_dir: Path) -> None:
    force_utf8_stdio()
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    # Log thường ra stdout; chỉ WARNING/ERROR mới ra stderr để terminal không tô đỏ mọi thứ.
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(_MaxLevelFilter(logging.INFO))
    stdout_handler.setFormatter(fmt)
    root.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(fmt)
    root.addHandler(stderr_handler)

    file_handler = logging.FileHandler(log_dir / "crawler.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


def polite_sleep(low: float, high: float) -> None:
    """Nghỉ ngẫu nhiên giữa các request để không dồn dập lên server."""
    time.sleep(random.uniform(low, high))
