from crawler.parsers import find_next_url, parse_quotes
from crawler.storage import dedupe

SAMPLE = """
<html><body>
  <div class="quote">
    <span class="text">“Hello world.”</span>
    <span>by <small class="author">Alice</small></span>
    <div class="tags"><a class="tag">intro</a><a class="tag">test</a></div>
  </div>
  <div class="quote">
    <span class="text">“Second.”</span>
    <small class="author">Bob</small>
  </div>
  <nav><ul class="pager"><li class="next"><a href="/page/2/">Next</a></li></ul></nav>
</body></html>
"""


def test_parse_quotes():
    items = parse_quotes(SAMPLE)
    assert len(items) == 2
    assert items[0] == {"text": "“Hello world.”", "author": "Alice", "tags": ["intro", "test"]}
    assert items[1]["tags"] == []


def test_find_next_url():
    assert find_next_url(SAMPLE, "https://example.com/") == "https://example.com/page/2/"
    assert find_next_url("<html></html>", "https://example.com/") is None


def test_dedupe():
    a = {"text": "x", "author": "y", "tags": []}
    b = {"text": "z", "author": "y", "tags": []}
    assert dedupe([a, dict(a), b]) == [a, b]
