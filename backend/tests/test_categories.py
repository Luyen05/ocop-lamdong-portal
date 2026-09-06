from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.category import Category


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
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
                Category(id=1, name="Thực phẩm", slug="thuc-pham", description="Sản phẩm thực phẩm", icon="bi-basket"),
                Category(id=2, name="Đồ uống", slug="do-uong", description="Trà và cà phê", icon="bi-cup-straw"),
                Category(id=3, name="Thảo dược", slug="thao-duoc", description=None, icon=None),
            ]
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_list_categories_supports_pagination_search_and_sort(client: TestClient) -> None:
    response = client.get(
        "/api/v1/categories",
        params={"page": 1, "page_size": 2, "search": "Th", "sort": "-name"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"id": 1, "name": "Thực phẩm", "slug": "thuc-pham", "description": "Sản phẩm thực phẩm", "icon": "bi-basket"},
            {"id": 3, "name": "Thảo dược", "slug": "thao-duoc", "description": None, "icon": None},
        ],
        "page": 1,
        "page_size": 2,
        "total": 2,
    }


def test_get_category_by_slug(client: TestClient) -> None:
    response = client.get("/api/v1/categories/do-uong")

    assert response.status_code == 200
    assert response.json()["name"] == "Đồ uống"


def test_get_category_returns_consistent_error(client: TestClient) -> None:
    response = client.get("/api/v1/categories/khong-ton-tai")

    assert response.status_code == 404
    assert response.json() == {
        "code": "CATEGORY_NOT_FOUND",
        "message": "Không tìm thấy danh mục.",
        "details": {"slug": "khong-ton-tai"},
    }


def test_list_categories_returns_consistent_validation_error(client: TestClient) -> None:
    response = client.get("/api/v1/categories", params={"page": 0})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "Dữ liệu đầu vào không hợp lệ."
    assert body["details"][0]["loc"] == ["query", "page"]
