"""Ghi nguồn ảnh (source_url, credit, license): ràng buộc cơ sở dữ liệu và việc giữ nguồn khi chủ thể lưu lại ảnh."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.product import ProductImage
from test_subject_products import auth_header, product_payload, subject_product_context  # noqa: F401


def create_draft_with_attributed_image(client, testing_session) -> dict:
    created = client.post("/api/v1/subject/products", headers=auth_header(1, "subject"), json=product_payload())
    assert created.status_code == 201
    with testing_session() as session:
        image = session.query(ProductImage).one()
        image.source_url = "https://commons.wikimedia.org/wiki/File:Dau-tay.jpg"
        image.credit = "Lê Văn D"
        image.license = "CC BY 4.0"
        session.commit()
    return created.json()


def test_saving_draft_keeps_attribution_of_existing_images(subject_product_context) -> None:
    client, testing_session = subject_product_context
    draft = create_draft_with_attributed_image(client, testing_session)
    payload = product_payload()
    payload["name"] = "Cà phê Arabica Cầu Đất (đã sửa)"

    saved = client.put(f"/api/v1/subject/products/{draft['id']}", headers=auth_header(1, "subject"), json=payload)

    assert saved.status_code == 200
    with testing_session() as session:
        image = session.query(ProductImage).one()
        assert (image.source_url, image.credit, image.license) == (
            "https://commons.wikimedia.org/wiki/File:Dau-tay.jpg",
            "Lê Văn D",
            "CC BY 4.0",
        )


def test_replacing_with_a_different_image_does_not_inherit_attribution(subject_product_context) -> None:
    client, testing_session = subject_product_context
    draft = create_draft_with_attributed_image(client, testing_session)
    payload = product_payload()
    payload["images"][0]["image_url"] = "https://example.com/products/another.webp"

    saved = client.put(f"/api/v1/subject/products/{draft['id']}", headers=auth_header(1, "subject"), json=payload)

    assert saved.status_code == 200
    with testing_session() as session:
        image = session.query(ProductImage).one()
        assert (image.source_url, image.credit, image.license) == (None, None, None)


def test_image_source_url_must_be_http_link(subject_product_context) -> None:
    client, testing_session = subject_product_context
    create_draft_with_attributed_image(client, testing_session)

    with testing_session() as session:
        image = session.query(ProductImage).one()
        image.source_url = "javascript:alert(1)"
        with pytest.raises(IntegrityError):
            session.commit()
