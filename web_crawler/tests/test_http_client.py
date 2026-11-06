"""Test HTTP client tự xây dựng bằng http.server chạy tại chỗ (không cần mạng)."""
import gzip
import http.server
import threading

import pytest

from crawler.http_client import fetch

HITS = []


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        HITS.append(self.path)
        if self.path == "/plain":
            body = ("<html><head><meta charset=\"utf-8\"><title>x</title></head>"
                    "<body>có hàng</body></html>").encode("utf-8")
            self._send(200, body, {"Content-Type": "text/html"})
        elif self.path == "/gzip":
            body = gzip.compress("tên sản phẩm có dấu".encode("utf-8"))
            self._send(200, body, {"Content-Type": "text/html; charset=utf-8",
                                   "Content-Encoding": "gzip"})
        elif self.path == "/charset":
            body = "<meta charset='windows-1258'>giá 14.990.000đ".encode("windows-1258")
            self._send(200, body, {"Content-Type": "text/html"})
        elif self.path == "/flaky":
            if sum(1 for p in HITS if p == "/flaky") == 1:
                self._send(503, b"busy", {})
            else:
                self._send(200, b"ok after retry", {"Content-Type": "text/html"})
        else:
            self._send(404, b"not found", {})

    def _send(self, status, body, headers):
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def server_url():
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    thread.join(timeout=5)


def test_decode_theo_meta_charset(server_url):
    html = fetch(f"{server_url}/plain", user_agent="test", timeout_ms=5000, max_retries=1)
    assert "có hàng" in html


def test_gzip_va_charset_header(server_url):
    html = fetch(f"{server_url}/gzip", user_agent="test", timeout_ms=5000, max_retries=1)
    assert html == "tên sản phẩm có dấu"


def test_charset_trong_meta_khong_phai_utf8(server_url):
    html = fetch(f"{server_url}/charset", user_agent="test", timeout_ms=5000, max_retries=1)
    assert "14.990.000đ" in html


def test_retry_khi_503(server_url):
    html = fetch(f"{server_url}/flaky", user_agent="test", timeout_ms=5000, max_retries=3)
    assert html == "ok after retry"
    assert HITS.count("/flaky") == 2


def test_404_tra_ve_none(server_url):
    assert fetch(f"{server_url}/missing", user_agent="test", timeout_ms=5000, max_retries=1) is None
