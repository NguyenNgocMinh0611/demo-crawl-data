# Web Crawler (HTTP client tự xây dựng + Playwright tùy chọn)

Crawler có 2 tầng: **listing** (trang danh mục/tìm kiếm) -> **detail** (từng sản phẩm),
trích ra 5 trường: tên, mô tả, giá, tình trạng còn hàng và hình ảnh sản phẩm.

## Cài đặt

```
pip install -r requirements.txt
```

Mặc định crawler tải trang bằng **HTTP client tự viết** (`crawler/http_client.py`,
stdlib `urllib`: retry lùi dần, gzip, nhận diện charset): không cần trình duyệt,
không cần Docker.

Chỉ khi trang cần render bằng JavaScript mới cần Playwright:

```
playwright install chromium
```

## Chạy

### Demo quotes (trang tĩnh)

```
python main.py                                   # trang tĩnh, 3 trang
python main.py --engine chromium --start-url https://quotes.toscrape.com/js/   # trang render bằng JS
```

### Crawl sản phẩm thật (3 trang bán điện thoại)

```
python main.py --sites cellphones,tgdd,dmx --max-products 8
```

- Mặc định chỉ giữ máy **cũ/đã qua sử dụng** khớp `keyword` (xem `config.py`);
  thêm `--all-conditions` để lấy cả máy mới chính hãng.
- `--sites` chọn trang: `cellphones` (CellphoneS), `tgdd` (Thế Giới Di Động),
  `dmx` (Điện máy XANH).
- Kết quả: `data/iphone15.json` và `data/iphone15.csv` với các cột
  `name, description, price_vnd, stock, images` (+ `condition`, `url`, `source`).

### Xem crawler chạy trong cửa sổ trình duyệt thật

```
python main.py --sites cellphones --headful --slow-mo 500
```

`--headful` tự chuyển sang engine chromium (cần chạy `playwright install chromium`
trước). Cửa sổ mở ở kích thước thật, `--slow-mo` làm chậm từng thao tác để mắt theo kịp.

## Engine

| Engine | Khi nào dùng | Cần gì |
| ------ | ------------ | ------ |
| `http` (mặc định) | Trang render sẵn HTML ở server | Chỉ stdlib Python |
| `chromium` | Trang chỉ render bằng JavaScript | `playwright install chromium` |

Chọn bằng cờ `--engine http|chromium`. Lưu ý: trang tìm kiếm của CellphoneS
render bằng JavaScript, nhưng crawler dùng trang danh mục
`/hang-cu/iphone/iphone-15.html` (render sẵn ở server) nên engine `http` đủ
cho cả 3 site.

## Ghi nhận thực tế khi crawl 3 trang (tháng 11/2026)

- `cellphones.com.vn` là trang duy nhất trong 3 trang có máy cũ, phân loại
  Cũ Đẹp / Cũ Xước Cấn / Cũ Trầy Xước ngay trong tên sản phẩm.
- `thegioididong.com` và `dienmayxanh.com` không kinh doanh máy cũ; iPhone 15
  không còn nằm ở trang danh mục đầu, phải vào thẳng trang dòng sản phẩm
  `/dtdd/iphone-15`, `/dien-thoai/iphone-15` (crawler đã cấu hình sẵn như vậy).
- Crawler tuân thủ `robots.txt` và `Crawl-delay: 5` của Thegioididong
  (`crawler/robots.py` đọc và cache mỗi domain một lần).

## Test

```
pytest                                           # test parser + http client, không cần mạng
```

## Cấu trúc

```
main.py                 # luồng crawl 2 tầng, đọc robots.txt, chờ Crawl-delay
config.py               # toàn bộ cấu hình (sites, keyword, delay, engine...)
crawler/
  http_client.py        # HTTP client tự xây dựng (urllib): retry, gzip, charset
  robots.py             # robots.txt: cho phép? Crawl-delay? (có cache)
  sites.py              # adapter 3 trang: parse listing + parse detail
  browser.py            # mở Chromium (chỉ engine chromium)
  fetcher.py            # tải trang qua Playwright (chỉ engine chromium)
  parsers.py            # demo quotes (parse_quotes, find_next_url)
  storage.py            # ghi JSON + CSV, khử trùng
  utils.py              # log, utf-8 stdout, sleep lịch sự
tests/
  test_sites.py         # parser với HTML giả lập
  test_parsers.py       # demo quotes
```

## Đổi sang trang của bạn

1. Thêm một mục `Site` trong `crawler/sites.py` (URL listing + selector) và viết
   `parse_listing`/`parse_detail` nếu cấu trúc khác hai họ sẵn có.
2. Sửa `config.py` (`keyword`, `used_only`, `max_products`, `delay_*`).
3. Chỉ crawl dữ liệu công khai, tôn trọng robots.txt và điều khoản của trang.
