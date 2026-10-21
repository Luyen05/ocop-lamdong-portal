"""Hỗ trợ công cụ tìm kiếm và chia sẻ mạng xã hội: robots.txt, sitemap.xml và trang HTML tĩnh cho bot.

Frontend là ứng dụng một trang (SPA) nên trình thu thập không chạy JavaScript (Facebook, Zalo, một số bot)
chỉ thấy khung rỗng. Các route ở đây không nằm dưới ``/api/v1``: Nginx chuyển ``/robots.txt``,
``/sitemap.xml`` và (với bot) ``/san-pham/<slug>``, ``/diem-du-lich/<slug>`` về đây (xem ``deploy/nginx``).
Chỉ nội dung công khai (cùng điều kiện với API công khai) mới xuất hiện.
"""

from __future__ import annotations

import json
from datetime import datetime
from html import escape
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.routes.products import public_product_filters
from app.core.config import get_settings
from app.core.database import get_db
from app.models.location import TourismLocation
from app.models.product import Product
from app.services.location_catalog import location_type_label, public_location_filters


router = APIRouter(tags=["SEO"], include_in_schema=False)

SITE_NAME = "OCOP Lâm Đồng"
DEFAULT_DESCRIPTION = (
    "Cổng thông tin nông sản OCOP và bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng: "
    "tra cứu sản phẩm đạt sao, điểm tham quan và đường đi."
)
# Trang công khai không cần đăng nhập, ưu tiên theo mức quan trọng.
STATIC_PAGES: tuple[tuple[str, str, str], ...] = (
    ("/", "daily", "1.0"),
    ("/san-pham", "daily", "0.9"),
    ("/diem-du-lich", "daily", "0.9"),
    ("/ban-do", "weekly", "0.8"),
    ("/tin-tuc", "daily", "0.6"),
)
# Các đường dẫn riêng tư hoặc không có nội dung cho tìm kiếm.
DISALLOWED_PATHS = (
    "/quan-tri",
    "/chu-the",
    "/tai-khoan",
    "/dang-nhap",
    "/dang-ky",
    "/dang-ky-chu-the",
    "/khong-co-quyen",
    "/uploads/certificates",
)
SITEMAP_LIMIT = 50_000  # giới hạn của giao thức sitemap


def site_url(path: str = "") -> str:
    return f"{get_settings().frontend_base_url}{path}"


def clip(text: str | None, limit: int = 160) -> str:
    """Rút gọn mô tả cho thẻ meta: gộp khoảng trắng, cắt tại ranh giới từ."""

    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rsplit(" ", 1)[0].rstrip(",.;:- ") + "…"


def lastmod(value: datetime | None) -> str:
    return f"<lastmod>{value.date().isoformat()}</lastmod>" if value else ""


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt() -> str:
    lines = ["User-agent: *", "Allow: /"]
    lines += [f"Disallow: {path}" for path in DISALLOWED_PATHS]
    lines += ["", f"Sitemap: {site_url('/sitemap.xml')}", ""]
    return "\n".join(lines)


@router.get("/sitemap.xml")
def sitemap_xml(db: Session = Depends(get_db)) -> Response:
    entries: list[str] = []

    def add(path: str, changefreq: str, priority: str, modified: datetime | None = None) -> None:
        entries.append(
            f"<url><loc>{xml_escape(site_url(path))}</loc>{lastmod(modified)}"
            f"<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>"
        )

    for path, changefreq, priority in STATIC_PAGES:
        add(path, changefreq, priority)
    products = db.execute(
        select(Product.slug, Product.updated_at)
        .join(Product.subject)
        .where(*public_product_filters())
        .order_by(Product.id)
        .limit(SITEMAP_LIMIT)
    ).all()
    for slug, updated_at in products:
        add(f"/san-pham/{slug}", "weekly", "0.7", updated_at)
    locations = db.execute(
        select(TourismLocation.slug, TourismLocation.updated_at)
        .where(*public_location_filters())
        .order_by(TourismLocation.id)
        .limit(SITEMAP_LIMIT)
    ).all()
    for slug, updated_at in locations:
        add(f"/diem-du-lich/{slug}", "weekly", "0.7", updated_at)

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    return Response(content=body, media_type="application/xml")


def render_share_page(
    *,
    title: str,
    description: str,
    path: str,
    image: str | None,
    json_ld: dict,
    heading: str,
    details: list[str],
) -> HTMLResponse:
    canonical = site_url(path)
    full_title = f"{title} | {SITE_NAME}"
    meta = [
        f'<meta name="description" content="{escape(description, quote=True)}">',
        f'<link rel="canonical" href="{escape(canonical, quote=True)}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        '<meta property="og:locale" content="vi_VN">',
        f'<meta property="og:title" content="{escape(full_title, quote=True)}">',
        f'<meta property="og:description" content="{escape(description, quote=True)}">',
        f'<meta property="og:url" content="{escape(canonical, quote=True)}">',
        f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">',
        f'<meta name="twitter:title" content="{escape(full_title, quote=True)}">',
        f'<meta name="twitter:description" content="{escape(description, quote=True)}">',
    ]
    if image:
        meta.append(f'<meta property="og:image" content="{escape(image, quote=True)}">')
        meta.append(f'<meta name="twitter:image" content="{escape(image, quote=True)}">')
    # "</" trong JSON có thể đóng thẻ script sớm; thay bằng dạng thoát hợp lệ.
    ld = json.dumps(json_ld, ensure_ascii=False).replace("</", "<\\/")
    items = "".join(f"<li>{escape(line)}</li>" for line in details if line)
    document = (
        '<!doctype html><html lang="vi"><head><meta charset="utf-8">'
        f"<title>{escape(full_title)}</title>"
        + "".join(meta)
        + f'<script type="application/ld+json">{ld}</script></head><body>'
        f"<h1>{escape(heading)}</h1><p>{escape(description)}</p><ul>{items}</ul>"
        f'<p><a href="{escape(canonical, quote=True)}">Xem trên {SITE_NAME}</a></p>'
        "</body></html>"
    )
    return HTMLResponse(document)


def price_text(price: float | None, unit: str | None) -> str:
    if not price or price <= 0:
        return ""
    value = f"{price:,.0f}".replace(",", ".")
    return f"Giá tham khảo: {value} đ" + (f"/{unit}" if unit else "")


def product_json_ld(product: Product, canonical: str, image: str | None) -> dict:
    data: dict = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": clip(product.description, 500),
        "url": canonical,
        "category": product.category.name,
        "brand": {"@type": "Brand", "name": product.subject.name},
        "additionalProperty": {
            "@type": "PropertyValue",
            "name": "Xếp hạng OCOP",
            "value": f"{product.star} sao",
        },
    }
    if image:
        data["image"] = image
    if product.price and product.price > 0:
        data["offers"] = {
            "@type": "Offer",
            "price": str(int(product.price)),
            "priceCurrency": "VND",
            "url": canonical,
        }
    return data


@router.get("/san-pham/{slug}", response_class=HTMLResponse)
def product_share_page(slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    product = db.scalar(
        select(Product)
        .join(Product.subject)
        .where(Product.slug == slug, *public_product_filters())
        .options(
            joinedload(Product.category),
            joinedload(Product.subject),
            selectinload(Product.images),
        )
    )
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Không tìm thấy sản phẩm.")
    canonical = site_url(f"/san-pham/{product.slug}")
    image = product.images[0].image_url if product.images else None
    description = clip(product.description) or DEFAULT_DESCRIPTION
    return render_share_page(
        title=f"{product.name} – OCOP {product.star} sao",
        description=description,
        path=f"/san-pham/{product.slug}",
        image=image,
        json_ld=product_json_ld(product, canonical, image),
        heading=product.name,
        details=[
            f"Sản phẩm OCOP {product.star} sao, nhóm {product.category.name}",
            f"Đơn vị sản xuất: {product.subject.name}",
            price_text(float(product.price) if product.price is not None else None, product.unit),
        ],
    )


def location_json_ld(location: TourismLocation, canonical: str, image: str | None) -> dict:
    data: dict = {
        "@context": "https://schema.org",
        "@type": "TouristAttraction",
        "name": location.name,
        "description": clip(location.description, 500),
        "url": canonical,
        "touristType": location_type_label(location.type),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": location.address or "",
            "addressRegion": "Lâm Đồng",
            "addressCountry": "VN",
        },
    }
    if location.geom is not None:
        data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": location.geom.latitude,
            "longitude": location.geom.longitude,
        }
    if location.opening_hours:
        data["openingHours"] = location.opening_hours
    if image:
        data["image"] = image
    return data


@router.get("/diem-du-lich/{slug}", response_class=HTMLResponse)
def location_share_page(slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    location = db.scalar(
        select(TourismLocation)
        .where(TourismLocation.slug == slug, *public_location_filters())
        .options(selectinload(TourismLocation.images))
    )
    if location is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Không tìm thấy điểm du lịch.")
    canonical = site_url(f"/diem-du-lich/{location.slug}")
    image = location.images[0].image_url if location.images else None
    description = clip(location.description) or clip(
        f"{location_type_label(location.type)} tại {location.district or 'Lâm Đồng'}. {location.address or ''}"
    )
    return render_share_page(
        title=f"{location.name} – Du lịch nông nghiệp Lâm Đồng",
        description=description or DEFAULT_DESCRIPTION,
        path=f"/diem-du-lich/{location.slug}",
        image=image,
        json_ld=location_json_ld(location, canonical, image),
        heading=location.name,
        details=[
            location_type_label(location.type),
            f"Địa chỉ: {location.address}" if location.address else "",
            f"Giờ mở cửa: {location.opening_hours}" if location.opening_hours else "",
        ],
    )
