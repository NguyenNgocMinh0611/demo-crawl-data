from config import Settings
from crawler.sites import (
    SITES,
    canonical,
    parse_detail,
    parse_listing,
    product_condition,
    to_vnd,
)

# Card của CellphoneS (Magento): h3[title] + p.text-primary-600 + ảnh media/catalog/product
CELLPHONES_LISTING = """
<html><body><div class="products-wrapper">
  <div class="product-item">
    <a href="/iphone-15-cu-dep.html">
      <img src="https://cdn2.cellphones.com.vn/insecure/rs:fill:300:300/q:100/plain/https://cellphones.com.vn/media/catalog/product/i/p/iphone15.jpg"/>
      <h3 class="mb-1" title="iPhone 15 128GB - Cũ Đẹp">iPhone 15 128GB - Cũ Đẹp</h3>
      <p class="text-primary-600">14.990.000đ</p>
      <p class="line-through">22.990.000đ</p>
    </a>
  </div>
  <div class="product-item">
    <a href="/dien-thoai-14-pro.html">
      <h3 title="iPhone 14 Pro 128GB - Cũ Đẹp">iPhone 14 Pro 128GB - Cũ Đẹp</h3>
      <p class="text-primary-600">12.990.000đ</p>
    </a>
  </div>
  <div class="product-item">
    <a href="/galaxy-s26.html">
      <h3 title="Galaxy S26 Ultra">Galaxy S26 Ultra</h3>
      <p class="text-primary-600">29.990.000đ</p>
    </a>
  </div>
</div></body></html>
"""

# Trang dòng sản phẩm của Mobile World: card = khối chứa ảnh /Products/Images/ + giá + link.
MWG_LISTING = """
<html><body><div class="grid">
  <div class="card">
    <img alt="iPhone 15 128GB" src="https://cdn.tgdd.vn/Products/Images/42/281570/iphone-15.jpg"/>
    <a href="/may-doi-tra/dtdd/iphone-15">Đổi cũ lấy mới</a>
    <a class="font-700 text-red-5" href="/dtdd/iphone-15">16.030.000</a>
    <del class="text-gray-5">21.990.000</del>
    <button>Mua ngay</button>
  </div>
  <div class="card">
    <img alt="iPhone 15 256GB Tổng Quan" src="https://cdn.tgdd.vn/Products/Images/42/281570/video-thumbvideo.jpg"/>
    <a href="/dtdd/iphone-15-256gb">21.990.000</a>
  </div>
  <div class="card">
    <img alt="OPPO A6c" src="https://cdn.tgdd.vn/Products/Images/42/111/oppo.jpg"/>
    <a href="/dtdd/oppo-a6c">4.690.000</a>
  </div>
</div></body></html>
"""

# Trang danh mục "iPhone cũ" của CellphoneS (render sẵn ở server): card
# a.product__link + h3 trong .product__name + giá .product__price--show / --through.
CELLPHONES_CATEGORY = """
<html><body><div class="swiper-slide">
  <div class="product-info-container product-item">
    <div class="product-info">
      <a rel="" href="https://cellphones.com.vn/iphone-15-plus-cu-dep.html" class="product__link button__link">
        <div class="product__image">
          <img src="https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/i/p/iphone-15-plus-256gb-color-pink-image_3_1.png"
               width="358" height="358" alt="iPhone 15 Plus 128GB - Cũ Đẹp" class="product__img"/>
        </div>
        <div class="product__name"><h3>iPhone 15 Plus 128GB - Cũ Đẹp</h3></div>
        <div class="block-box-price">
          <div class="box-info__box-price">
            <p class="product__price--show">15.890.000đ</p>
            <p class="product__price--through">22.990.000đ</p>
          </div>
        </div>
      </a>
    </div>
  </div>
  <div class="product-info-container">
    <div class="product-info">
      <a href="https://cellphones.com.vn/iphone-15-pro-max-cu-xuoc-can.html" class="product__link button__link">
        <img alt="iPhone 15 Pro Max 256GB - Cũ Xước Cấn" class="product__img" src="https://cellphones.com.vn/media/catalog/product/a/b/15pm.jpg"/>
        <div class="product__name"><h3>iPhone 15 Pro Max 256GB - Cũ Xước Cấn</h3></div>
        <p class="product__price--show">18.990.000đ</p>
        <p class="product__price--through">26.990.000đ</p>
      </a>
    </div>
  </div>
</div></body></html>
"""

# Trang chi tiết máy cũ của CellphoneS: nút MUA NGAY thay cho khối tồn kho,
# ảnh gallery nằm trong <a href>, mô tả ở #cpsContentSEO.
CELLPHONES_USED_DETAIL = """
<html><body>
  <h1>iPhone 15 Plus 128GB - Cũ Đẹp</h1>
  <div class="sale-price">15.890.000đ</div>
  <del class="base-price">22.990.000đ</del>
  <button class="btn-cta order-button button--large order-button-full">
    <strong>MUA NGAY</strong> <span>Xem hình ảnh thực tế và chọn mua</span>
  </button>
  <div class="swiper-slide">
    <a href="https://cdn2.cellphones.com.vn/x/media/catalog/product/i/p/iphone-15-plus-256gb-color-pink-image_3_1.png"
       class="swiper-zoom-container"><img loading="lazy" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP"/></a>
  </div>
  <div class="swiper-slide">
    <a href="https://cdn2.cellphones.com.vn/x/media/catalog/product/i/p/iphone-15-plus-256gb-color-black-image_2_1.png"
       class="swiper-zoom-container"><img loading="lazy" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP"/></a>
  </div>
  <div id="cpsContentSEO">
    <p>iPhone 15 Plus 128GB cũ đẹp được trang bị màn hình Super Retina XDR OLED 6.7 inch,
    chip Apple A16 Bionic mạnh mẽ, camera kép 48MP chụp đêm xuất sắc, máy đã qua kiểm tra
    nghiêm ngặt trước khi bán lại tại CellphoneS.</p>
  </div>
  <img src="https://cdn2.cellphones.com.vn/insecure/rs:fill:50:50/q:90/plain/https://cellphones.com.vn/media/catalog/product/i/p/iphone-15-plus-cu-dep.png"/>
</body></html>
"""

CELLPHONES_DETAIL = """
<html><head><title>iPhone 15 128GB - Cũ Đẹp | Giá rẻ</title></head><body>
  <h1>iPhone 15 128GB - Cũ Đẹp</h1>
  <div class="sale-price">14.990.000đ</div>
  <div class="line-through">22.990.000đ</div>
  <div class="box-on-stock-count">Xem chi nhánh có hàng Có 4 cửa hàng có sản phẩm</div>
  <div id="productDetailV2">
    <div class="description">Sản phẩm thu lại từ khách hàng không còn nhu cầu, ngoại hình đẹp như mới,
    full chức năng, máy chính hãng VN, đã kiểm tra 100 bước tại CellphoneS.</div>
  </div>
  <img src="https://cellphones.com.vn/media/catalog/product/a/1/front.jpg"/>
  <img src="https://cellphones.com.vn/media/wysiwyg/Logo_CPS.png"/>
</body></html>
"""

MWG_DETAIL = """
<html><body>
  <h1 class="text-20 font-700">Điện thoại iPhone 15 128GB</h1>
  <div id="quang-cao">Quà 390.000₫ <del>1.000.000</del></div>
  <div class="buybox">
    <span class="text-24 font-700 text-red-5">16.030.000</span>
    <del>21.990.000</del>
    <button class="bg-blue-5">Mua ngay</button>
  </div>
  <div id="description-text-detail">Lý do nên mua iPhone 15 128GB tại Thế Giới Di Động: máy chính hãng
  Apple, mới 100%, nguyên seal, bảo hành 12 tháng, hỗ trợ trả góp 0% lãi suất.</div>
  <img src="https://cdn.tgdd.vn/Products/Images/42/281570/iphone-15-a.jpg"/>
  <img src="https://cdn.tgdd.vn/Products/Images/42/281570/Slider/thumbvideo.jpg"/>
</body></html>
"""


def ref(url="https://x/san-pham"):
    return {"url": url, "name": "iPhone 15 128GB", "price_text": "", "image": ""}


def test_parse_listing_cellphones():
    refs = parse_listing(SITES["cellphones"], CELLPHONES_LISTING)
    assert [r["name"] for r in refs] == [
        "iPhone 15 128GB - Cũ Đẹp",
        "iPhone 14 Pro 128GB - Cũ Đẹp",
        "Galaxy S26 Ultra",
    ]
    assert refs[0]["url"] == "https://cellphones.com.vn/iphone-15-cu-dep.html"
    assert refs[0]["price_text"] == "14.990.000đ"


def test_parse_listing_cellphones_trang_danh_muc():
    refs = parse_listing(SITES["cellphones"], CELLPHONES_CATEGORY)
    assert [r["name"] for r in refs] == [
        "iPhone 15 Plus 128GB - Cũ Đẹp",
        "iPhone 15 Pro Max 256GB - Cũ Xước Cấn",
    ]
    assert refs[0]["url"] == "https://cellphones.com.vn/iphone-15-plus-cu-dep.html"
    assert refs[0]["price_text"] == "15.890.000đ"
    assert "iphone-15-plus-256gb-color-pink" in refs[0]["image"]


def test_parse_listing_mwg_bỏ_qua_card_video_va_link_doi_tra():
    refs = parse_listing(SITES["tgdd"], MWG_LISTING)
    assert [r["name"] for r in refs] == ["iPhone 15 128GB", "OPPO A6c"]
    assert refs[0]["url"] == "https://www.thegioididong.com/dtdd/iphone-15"


def test_parse_detail_cellphones():
    item = parse_detail(SITES["cellphones"], CELLPHONES_DETAIL, ref())
    assert item["name"] == "iPhone 15 128GB - Cũ Đẹp"
    assert item["condition"] == "Cũ Đẹp"
    assert item["price_vnd"] == 14990000
    assert item["old_price_vnd"] == 22990000
    assert item["stock"] == "Còn hàng (4 chi nhánh)"
    assert item["in_stock"] is True
    assert "Sản phẩm thu lại từ khách hàng" in item["description"]
    assert item["images"] == ["https://cellphones.com.vn/media/catalog/product/a/1/front.jpg"]


def test_parse_detail_cellphones_may_cu_nut_mua_ngay():
    item = parse_detail(SITES["cellphones"], CELLPHONES_USED_DETAIL, ref())
    assert item["old_price_vnd"] == 22990000
    assert item["stock"] == "Còn hàng - Mua ngay"
    assert item["in_stock"] is True
    assert "camera kép 48MP" in item["description"]
    assert item["images"] == [
        "https://cdn2.cellphones.com.vn/x/media/catalog/product/i/p/iphone-15-plus-256gb-color-pink-image_3_1.png",
        "https://cdn2.cellphones.com.vn/x/media/catalog/product/i/p/iphone-15-plus-256gb-color-black-image_2_1.png",
        "https://cellphones.com.vn/media/catalog/product/i/p/iphone-15-plus-cu-dep.png",
    ]


def test_parse_detail_mwg():
    item = parse_detail(SITES["tgdd"], MWG_DETAIL, ref("https://www.thegioididong.com/dtdd/iphone-15"))
    assert item["name"] == "iPhone 15 128GB"
    assert item["condition"] == "Mới / chính hãng"
    assert item["price_vnd"] == 16030000
    assert item["old_price_vnd"] == 21990000, "không lấy giá gạch ngang của banner quà tặng"
    assert item["stock"] == "Còn hàng - Mua ngay"
    assert item["description"].startswith("Lý do nên mua")
    assert item["images"] == ["https://cdn.tgdd.vn/Products/Images/42/281570/iphone-15-a.jpg"]


def test_to_vnd_va_product_condition():
    assert to_vnd("Chỉ còn 14.990.000đ thôi") == 14990000
    assert to_vnd("không có giá") is None
    assert product_condition("iPhone 15 128GB - Cũ Xước Cấn") == "Cũ Xước Cấn"
    assert product_condition("iPhone 15 Pro Max - Like New") == "Like New"
    assert product_condition("iPhone 15 128GB") == "Mới / chính hãng"


def test_canonical_loai_bo_query_cua_bien_the():
    assert canonical("https://a.com/dtdd/iphone-15?code=0131#x") == "https://a.com/dtdd/iphone-15"


def test_pick_products_chi_giữ_máy_cũ_không_phải_máy_mới():
    from main import pick_products

    refs = parse_listing(SITES["cellphones"], CELLPHONES_LISTING)
    used = pick_products(Settings(keyword=r"iphone\s*15", used_only=True, max_products=8), refs)
    assert [r["name"] for r in used] == ["iPhone 15 128GB - Cũ Đẹp"]

    everything = pick_products(Settings(keyword=r"iphone\s*15", used_only=False, max_products=8), refs)
    assert len(everything) == 1  # cùng số lượng vì card iPhone 15 duy nhất đã là máy cũ
