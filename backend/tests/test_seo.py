import json
import re
from xml.etree import ElementTree

from fastapi.testclient import TestClient

from test_locations import location_client  # noqa: F401  (fixture dùng chung)

SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def sitemap_urls(client: TestClient) -> list[str]:
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    root = ElementTree.fromstring(response.text)
    return [node.text for node in root.findall("s:url/s:loc", SITEMAP_NS)]


def test_robots_chan_khu_rieng_tu_va_tro_toi_sitemap(location_client: TestClient) -> None:
    text = location_client.get("/robots.txt").text

    assert "User-agent: *" in text
    assert "Disallow: /quan-tri" in text
    assert "Disallow: /chu-the" in text
    assert "Disallow: /tai-khoan" in text
    assert "Sitemap: http://localhost:5173/sitemap.xml" in text


def test_sitemap_chi_co_noi_dung_cong_khai(location_client: TestClient) -> None:
    urls = sitemap_urls(location_client)

    assert "http://localhost:5173/" in urls
    assert "http://localhost:5173/san-pham" in urls
    assert "http://localhost:5173/san-pham/tra-xanh-cau-dat" in urls
    assert "http://localhost:5173/diem-du-lich/cau-dat-farm" in urls
    assert "http://localhost:5173/diem-du-lich/nong-trai-dalat-milk" in urls
    # Sản phẩm chờ duyệt và điểm chờ duyệt không được lộ.
    assert not any("tra-chua-duyet" in url for url in urls)
    assert not any("vuon-cho-duyet" in url for url in urls)
    assert len(urls) == len(set(urls))


def test_trang_chia_se_san_pham_co_og_va_json_ld(location_client: TestClient) -> None:
    response = location_client.get("/san-pham/tra-xanh-cau-dat")

    assert response.status_code == 200
    html = response.text
    assert "<title>Trà xanh Cầu Đất – OCOP 4 sao | OCOP Lâm Đồng</title>" in html
    assert '<link rel="canonical" href="http://localhost:5173/san-pham/tra-xanh-cau-dat">' in html
    assert 'property="og:title"' in html and 'name="twitter:card" content="summary"' in html
    data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html).group(1))
    assert data["@type"] == "Product"
    assert data["offers"]["price"] == "120000"
    assert data["brand"]["name"] == "HTX Chè Cầu Đất"


def test_trang_chia_se_diem_du_lich_co_toa_do_va_anh(location_client: TestClient) -> None:
    response = location_client.get("/diem-du-lich/cau-dat-farm")

    assert response.status_code == 200
    html = response.text
    assert 'property="og:image" content="https://example.com/cau-dat.jpg"' in html
    assert 'name="twitter:card" content="summary_large_image"' in html
    data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html).group(1))
    assert data["@type"] == "TouristAttraction"
    assert data["geo"]["latitude"] == 11.879583
    assert data["openingHours"] == "07:00 - 19:00"


def test_trang_chia_se_khong_lo_noi_dung_chua_duyet(location_client: TestClient) -> None:
    assert location_client.get("/san-pham/tra-chua-duyet").status_code == 404
    assert location_client.get("/diem-du-lich/vuon-cho-duyet").status_code == 404
    assert location_client.get("/san-pham/khong-ton-tai").status_code == 404


def test_trang_chia_se_thoat_ky_tu_dac_biet(location_client: TestClient) -> None:
    from sqlalchemy import update

    from app.core.database import get_db
    from app.main import app
    from app.models.product import Product

    session = next(app.dependency_overrides[get_db]())
    session.execute(
        update(Product)
        .where(Product.id == 1)
        .values(description='Hạt "ngon" </script><b>x</b> & thơm')
    )
    session.commit()

    html = location_client.get("/san-pham/tra-xanh-cau-dat").text

    assert "</script><b>" not in html
    assert "<b>x</b>" not in html
    assert "&lt;/script&gt;" in html
