from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.category import Category
from app.models.product import Product, ProductImage
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User


@pytest.fixture
def product_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        role = Role(id=3, name="user", description="Người dùng")
        users = [
            User(
                id=1,
                role=role,
                email="subject@example.com",
                hashed_password="not-used",
                full_name="Chủ thể một",
                is_active=True,
            ),
            User(
                id=2,
                role_id=3,
                email="pending@example.com",
                hashed_password="not-used",
                full_name="Chủ thể hai",
                is_active=True,
            ),
        ]
        categories = [
            Category(id=1, name="Thực phẩm", slug="thuc-pham"),
            Category(id=2, name="Đồ uống", slug="do-uong"),
        ]
        subjects = [
            Subject(
                id=1,
                user_id=1,
                name="Hợp tác xã Cầu Đất",
                type="cooperative",
                representative="Nguyễn Văn A",
                phone="0912345678",
                address="Đà Lạt",
                district="Đà Lạt",
                status="approved",
            ),
            Subject(
                id=2,
                user_id=2,
                name="Cơ sở chờ duyệt",
                type="business",
                representative="Nguyễn Văn B",
                phone="0987654321",
                address="Bảo Lộc",
                district="Bảo Lộc",
                status="pending",
            ),
        ]
        products = [
            Product(
                id=1,
                subject_id=1,
                category_id=2,
                name="Cà phê Arabica Cầu Đất",
                slug="ca-phe-arabica-cau-dat",
                star=5,
                price=Decimal("180000"),
                unit="hộp 500g",
                description="Cà phê rang xay nguyên chất từ Cầu Đất.",
                rating_avg=Decimal("4.80"),
                status="approved",
            ),
            Product(
                id=2,
                subject_id=1,
                category_id=1,
                name="Mứt dâu Đà Lạt",
                slug="mut-dau-da-lat",
                star=4,
                price=Decimal("95000"),
                unit="hũ 300g",
                description="Mứt dâu làm từ trái dâu tươi.",
                rating_avg=Decimal("4.25"),
                status="approved",
            ),
            Product(
                id=3,
                subject_id=1,
                category_id=1,
                name="Sản phẩm chưa duyệt",
                slug="san-pham-chua-duyet",
                star=3,
                price=Decimal("50000"),
                unit="gói",
                description="Không được xuất hiện công khai.",
                status="pending",
            ),
            Product(
                id=4,
                subject_id=2,
                category_id=2,
                name="Sản phẩm của chủ thể chờ duyệt",
                slug="san-pham-chu-the-cho-duyet",
                star=5,
                price=Decimal("200000"),
                unit="hộp",
                description="Không được xuất hiện công khai.",
                status="approved",
            ),
        ]
        session.add_all([*users, *categories, *subjects, *products])
        session.flush()
        session.add(
            ProductImage(
                id=1,
                product_id=1,
                image_url="https://example.com/coffee.webp",
                is_primary=True,
                sort_order=0,
            )
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_list_products_only_returns_approved_content(product_client: TestClient) -> None:
    response = product_client.get("/api/v1/products", params={"sort": "name"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["slug"] for item in body["items"]] == [
        "ca-phe-arabica-cau-dat",
        "mut-dau-da-lat",
    ]
    assert body["items"][0]["primary_image_url"] == "https://example.com/coffee.webp"
    assert body["items"][0]["subject"]["district"] == "Đà Lạt"


def test_list_products_supports_public_filters(product_client: TestClient) -> None:
    response = product_client.get(
        "/api/v1/products",
        params={
            "search": "Cầu Đất",
            "category": "do-uong",
            "star": 5,
            "district": "Đà Lạt",
            "min_price": 150000,
            "max_price": 190000,
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["slug"] == "ca-phe-arabica-cau-dat"


def test_list_products_rejects_invalid_price_range(product_client: TestClient) -> None:
    response = product_client.get(
        "/api/v1/products",
        params={"min_price": 200000, "max_price": 100000},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_PRICE_RANGE"
