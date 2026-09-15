from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.news import News, NewsImage
from app.models.role import Role
from app.models.user import User


@pytest.fixture
def news_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        session.add(User(
            id=1,
            role=Role(id=3, name="user", description="Người dùng"),
            email="author@example.com",
            hashed_password="not-used",
            full_name="Tác giả",
        ))
        session.flush()
        for news_id, slug, state, day, title, category, summary in [
            (1, "older", "published", 1, "Coffee harvest", "Events", "Older story"),
            (2, "newer", "published", 3, "Local fair", "Events", "Coffee producers"),
            (3, "tied", "published", 3, "Tea award", "Awards", "Regional award"),
            (4, "draft", "draft", None, "Coffee draft", "Events", "Hidden"),
            (5, "archived", "archived", 5, "Coffee archive", "Events", "Hidden"),
        ]:
            session.add(News(
                id=news_id,
                author_id=1,
                title=title,
                slug=slug,
                category=category,
                summary=summary,
                content=f"Content for {slug}",
                views=17,
                status=state,
                published_at=datetime(2026, 1, day, tzinfo=timezone.utc) if day else None,
                created_at=datetime(2026, 1, 10 - news_id, tzinfo=timezone.utc),
                updated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            ))
        session.flush()
        session.add_all([
            NewsImage(id=1, news_id=1, image_url="https://example.com/1.webp", sort_order=2),
            NewsImage(id=2, news_id=1, image_url="https://example.com/2.webp", sort_order=1),
            NewsImage(id=3, news_id=1, image_url="https://example.com/3.webp", sort_order=1),
            NewsImage(
                id=4, news_id=1, image_url="https://example.com/primary.webp",
                is_primary=True, sort_order=9,
            ),
            NewsImage(id=5, news_id=2, image_url="https://example.com/secondary.webp"),
        ])
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_list_only_published_in_publication_order(news_client: TestClient) -> None:
    response = news_client.get("/api/v1/news")
    assert response.status_code == 200
    body = response.json()
    assert (body["page"], body["page_size"], body["total"]) == (1, 12, 3)
    assert [item["slug"] for item in body["items"]] == ["tied", "newer", "older"]
    assert [item["primary_image_url"] for item in body["items"]] == [
        None, None, "https://example.com/primary.webp",
    ]
    assert set(body["items"][0]) == {
        "id", "title", "slug", "category", "summary", "primary_image_url", "published_at",
    }


@pytest.mark.parametrize("page,slugs", [(1, ["tied", "newer"]), (2, ["older"]), (3, [])])
def test_pagination(news_client: TestClient, page: int, slugs: list[str]) -> None:
    response = news_client.get("/api/v1/news", params={"page": page, "page_size": 2})
    assert response.status_code == 200
    body = response.json()
    assert (body["page"], body["page_size"], body["total"]) == (page, 2, 3)
    assert [item["slug"] for item in body["items"]] == slugs


@pytest.mark.parametrize("params,slugs", [
    ({"search": " COFFEE "}, ["newer", "older"]),
    ({"category": " eVeNtS "}, ["newer", "older"]),
    ({"category": "Event"}, []),
    ({"search": "coffee", "category": "Awards"}, []),
    ({"search": "missing"}, []),
])
def test_public_filters(news_client: TestClient, params: dict, slugs: list[str]) -> None:
    response = news_client.get("/api/v1/news", params=params)
    assert response.status_code == 200
    assert response.json()["total"] == len(slugs)
    assert [item["slug"] for item in response.json()["items"]] == slugs


def test_filtered_pagination(news_client: TestClient) -> None:
    response = news_client.get(
        "/api/v1/news", params={"search": "coffee", "page": 2, "page_size": 1},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [item["slug"] for item in response.json()["items"]] == ["older"]


@pytest.mark.parametrize("params", [
    {"page": 0}, {"page": -1}, {"page_size": 0}, {"page_size": 101},
    {"page": "invalid"}, {"search": ""}, {"category": ""},
])
def test_invalid_query(news_client: TestClient, params: dict) -> None:
    response = news_client.get("/api/v1/news", params=params)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_published_detail_and_read_only_views(news_client: TestClient) -> None:
    for _ in range(2):
        response = news_client.get("/api/v1/news/older")
        assert response.status_code == 200
        body = response.json()
        assert body["content"] == "Content for older"
        assert body["views"] == 17
        assert body["published_at"].startswith("2026-01-01T00:00:00")
        assert body["updated_at"].startswith("2026-02-01T00:00:00")
        assert body["primary_image_url"] == "https://example.com/primary.webp"
        assert [image["id"] for image in body["images"]] == [4, 2, 3, 1]
        assert body["images"][0] == {
            "id": 4, "image_url": "https://example.com/primary.webp",
            "is_primary": True, "sort_order": 9,
        }
        assert not {"status", "author_id", "created_at"}.intersection(body)

    for session in app.dependency_overrides[get_db]():
        assert session.get(News, 1).views == 17


def test_detail_without_images(news_client: TestClient) -> None:
    response = news_client.get("/api/v1/news/tied")
    assert response.status_code == 200
    assert response.json()["images"] == []
    assert response.json()["primary_image_url"] is None


@pytest.mark.parametrize("slug", ["draft", "archived", "missing"])
def test_hidden_and_missing_details(news_client: TestClient, slug: str) -> None:
    response = news_client.get(f"/api/v1/news/{slug}")
    assert response.status_code == 404
    assert response.json() == {
        "code": "NEWS_NOT_FOUND",
        "message": "Không tìm thấy bài viết.",
        "details": {"slug": slug},
    }
