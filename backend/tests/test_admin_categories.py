from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.category import Category
from app.models.product import Product
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User


ADMIN_ID = 1
SUBJECT_USER_ID = 2
PLAIN_USER_ID = 3


@pytest.fixture
def category_context() -> Generator[tuple[TestClient, sessionmaker], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        session.add_all(
            [
                Role(id=1, name="admin", description="Quản trị"),
                Role(id=2, name="subject", description="Chủ thể"),
                Role(id=3, name="user", description="Người dùng"),
            ]
        )
        session.flush()
        session.add_all(
            [
                User(id=ADMIN_ID, role_id=1, email="admin@example.com", hashed_password="x", full_name="Quản trị"),
                User(id=SUBJECT_USER_ID, role_id=2, email="htx@example.com", hashed_password="x", full_name="Chủ HTX"),
                User(id=PLAIN_USER_ID, role_id=3, email="khach@example.com", hashed_password="x", full_name="Khách"),
                Category(id=1, name="Thực phẩm", slug="thuc-pham", sort_order=2),
                Category(id=2, name="Đồ uống", slug="do-uong", sort_order=1),
                Category(id=3, name="Thảo dược", slug="thao-duoc", sort_order=2),
                Category(id=4, name="Sinh vật cảnh", slug="sinh-vat-canh", sort_order=0, is_visible=False),
            ]
        )
        session.flush()
        session.add(
            Subject(
                id=1,
                user_id=SUBJECT_USER_ID,
                name="HTX Cầu Đất",
                type="cooperative",
                representative="Nguyễn Văn A",
                phone="0912345678",
                address="Đà Lạt",
                district="Đà Lạt",
                status="approved",
            )
        )
        session.flush()
        session.add_all(
            [
                Product(
                    id=1,
                    subject_id=1,
                    category_id=2,
                    name="Cà phê Cầu Đất",
                    slug="ca-phe-cau-dat",
                    star=4,
                    price=Decimal("150000"),
                    cert_code="OCOP-LD-001",
                    cert_issued_at=date(2025, 1, 1),
                    cert_expires_at=date(2099, 1, 1),
                    issuing_authority="UBND tỉnh Lâm Đồng",
                    description="Cà phê rang xay từ Cầu Đất.",
                    status="approved",
                ),
                Product(
                    id=2,
                    subject_id=1,
                    category_id=4,
                    name="Lan hồ điệp",
                    slug="lan-ho-diep",
                    star=4,
                    price=Decimal("300000"),
                    cert_code="OCOP-LD-002",
                    cert_issued_at=date(2025, 1, 1),
                    cert_expires_at=date(2099, 1, 1),
                    issuing_authority="UBND tỉnh Lâm Đồng",
                    description="Lan hồ điệp trồng tại Đà Lạt.",
                    status="approved",
                ),
                Product(
                    id=3,
                    subject_id=1,
                    category_id=4,
                    name="Bản nháp lan",
                    slug="ban-nhap-lan",
                    status="draft",
                ),
            ]
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, testing_session
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def auth(user_id: int, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id=user_id, role=role)}"}


ADMIN = auth(ADMIN_ID, "admin")
SUBJECT = auth(SUBJECT_USER_ID, "subject")


@pytest.mark.parametrize(("user_id", "role"), [(SUBJECT_USER_ID, "subject"), (PLAIN_USER_ID, "user")])
def test_admin_category_endpoints_reject_non_admin(category_context, user_id: int, role: str) -> None:
    client, _ = category_context
    headers = auth(user_id, role)

    assert client.get("/api/v1/admin/categories", headers=headers).status_code == 403
    assert client.post("/api/v1/admin/categories", json={"name": "Mới"}, headers=headers).status_code == 403
    assert client.patch("/api/v1/admin/categories/1", json={"is_visible": False}, headers=headers).status_code == 403
    assert client.delete("/api/v1/admin/categories/3", headers=headers).status_code == 403


def test_admin_lists_all_categories_with_product_counts(category_context) -> None:
    client, _ = category_context

    response = client.get("/api/v1/admin/categories", headers=ADMIN)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 4
    assert [(item["slug"], item["product_count"], item["is_visible"]) for item in body["items"]] == [
        ("sinh-vat-canh", 2, False),
        ("do-uong", 1, True),
        ("thao-duoc", 0, True),
        ("thuc-pham", 0, True),
    ]


def test_public_categories_hide_hidden_and_follow_sort_order(category_context) -> None:
    client, _ = category_context

    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["items"]] == ["do-uong", "thao-duoc", "thuc-pham"]
    assert response.json()["total"] == 3
    assert "is_visible" not in response.json()["items"][0]


def test_hidden_category_products_stay_public(category_context) -> None:
    client, _ = category_context

    products = client.get("/api/v1/products", params={"sort": "name"}).json()
    assert [item["slug"] for item in products["items"]] == ["ca-phe-cau-dat", "lan-ho-diep"]
    assert client.get("/api/v1/products/lan-ho-diep").status_code == 200
    by_category = client.get("/api/v1/products", params={"category": "sinh-vat-canh"}).json()
    assert by_category["total"] == 1


def test_admin_creates_category_with_generated_slug(category_context) -> None:
    client, _ = category_context

    response = client.post(
        "/api/v1/admin/categories",
        json={"name": "  Nông sản tươi  ", "description": "Rau, củ, quả", "icon": "bi-basket"},
        headers=ADMIN,
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "name": "Nông sản tươi",
        "slug": "nong-san-tuoi",
        "description": "Rau, củ, quả",
        "icon": "bi-basket",
        "is_visible": True,
        "sort_order": 0,
        "product_count": 0,
    }

    duplicate_slug_name = client.post(
        "/api/v1/admin/categories",
        json={"name": "Nong san tuoi"},
        headers=ADMIN,
    )
    assert duplicate_slug_name.status_code == 201
    assert duplicate_slug_name.json()["slug"] == "nong-san-tuoi-2"


def test_admin_category_duplicate_name_or_slug_conflicts(category_context) -> None:
    client, _ = category_context

    same_name = client.post("/api/v1/admin/categories", json={"name": "Đồ uống"}, headers=ADMIN)
    assert same_name.status_code == 409
    assert same_name.json()["code"] == "CATEGORY_NAME_EXISTS"

    same_slug = client.post(
        "/api/v1/admin/categories",
        json={"name": "Đồ uống đóng chai", "slug": "do-uong"},
        headers=ADMIN,
    )
    assert same_slug.status_code == 409
    assert same_slug.json()["code"] == "CATEGORY_SLUG_EXISTS"

    rename = client.patch("/api/v1/admin/categories/1", json={"name": "Thảo dược"}, headers=ADMIN)
    assert rename.status_code == 409
    assert rename.json()["code"] == "CATEGORY_NAME_EXISTS"

    bad_slug = client.patch("/api/v1/admin/categories/1", json={"slug": "Có dấu"}, headers=ADMIN)
    assert bad_slug.status_code == 422


def test_admin_updates_category_fields(category_context) -> None:
    client, _ = category_context

    response = client.patch(
        "/api/v1/admin/categories/2",
        json={
            "name": "Đồ uống OCOP",
            "slug": "do-uong-ocop",
            "description": "Trà, cà phê",
            "icon": "bi-cup",
            "is_visible": False,
            "sort_order": 5,
        },
        headers=ADMIN,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "do-uong-ocop"
    assert body["is_visible"] is False
    assert body["sort_order"] == 5
    assert body["product_count"] == 1
    assert "do-uong-ocop" not in [item["slug"] for item in client.get("/api/v1/categories").json()["items"]]

    empty = client.patch("/api/v1/admin/categories/2", json={}, headers=ADMIN)
    assert empty.status_code == 422
    negative = client.patch("/api/v1/admin/categories/2", json={"sort_order": -1}, headers=ADMIN)
    assert negative.status_code == 422
    null_name = client.patch("/api/v1/admin/categories/2", json={"name": None}, headers=ADMIN)
    assert null_name.status_code == 422
    missing = client.patch("/api/v1/admin/categories/99", json={"is_visible": True}, headers=ADMIN)
    assert missing.status_code == 404
    assert missing.json()["code"] == "CATEGORY_NOT_FOUND"


def test_delete_category_only_when_empty(category_context) -> None:
    client, testing_session = category_context

    in_use = client.delete("/api/v1/admin/categories/2", headers=ADMIN)
    assert in_use.status_code == 409
    assert in_use.json()["code"] == "CATEGORY_IN_USE"
    assert in_use.json()["details"] == {"product_count": 1}

    deleted = client.delete("/api/v1/admin/categories/3", headers=ADMIN)
    assert deleted.status_code == 204
    with testing_session() as session:
        assert session.get(Category, 3) is None
    assert client.delete("/api/v1/admin/categories/3", headers=ADMIN).status_code == 404


def test_subject_cannot_create_product_in_hidden_category(category_context) -> None:
    client, _ = category_context

    hidden = client.post(
        "/api/v1/subject/products",
        json={"category_id": 4, "name": "Lan mới"},
        headers=SUBJECT,
    )
    assert hidden.status_code == 422
    assert hidden.json()["code"] == "CATEGORY_HIDDEN"

    visible = client.post(
        "/api/v1/subject/products",
        json={"category_id": 2, "name": "Trà mới"},
        headers=SUBJECT,
    )
    assert visible.status_code == 201

    move_to_hidden = client.patch(
        f"/api/v1/subject/products/{visible.json()['id']}",
        json={"category_id": 4},
        headers=SUBJECT,
    )
    assert move_to_hidden.status_code == 422
    assert move_to_hidden.json()["code"] == "CATEGORY_HIDDEN"


def test_product_already_in_hidden_category_stays_editable(category_context) -> None:
    client, _ = category_context

    response = client.patch(
        "/api/v1/subject/products/3",
        json={"category_id": 4, "name": "Bản nháp lan hồ điệp"},
        headers=SUBJECT,
    )

    assert response.status_code == 200
    assert response.json()["category_id"] == 4
    assert response.json()["name"] == "Bản nháp lan hồ điệp"
