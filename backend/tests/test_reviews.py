"""Đánh giá sản phẩm OCOP và điểm du lịch: viết, sửa, xóa, kiểm duyệt và tính lại điểm trung bình."""

from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.geometry import GeoPoint, register_sqlite_geo_functions
from app.core.security import create_access_token
from app.main import app
from app.models.category import Category
from app.models.location import TourismLocation
from app.models.product import Product
from app.models.review import Review
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User


CAU_DAT = GeoPoint(longitude=108.547398, latitude=11.879583)
COMMENT = "Trà thơm, đóng gói cẩn thận, giao hàng nhanh."


def bearer(user_id: int, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id=user_id, role=role)}"}


ADMIN = bearer(1, "admin")
OWNER = bearer(2, "subject")
USER = bearer(3, "user")
USER2 = bearer(4, "user")
OTHER_SUBJECT = bearer(5, "subject")


@pytest.fixture
def review_context() -> Generator[tuple[TestClient, sessionmaker], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", register_sqlite_geo_functions)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    Base.metadata.create_all(engine)

    with testing_session() as session:
        session.add_all(
            [
                Role(id=1, name="admin", description="Quản trị"),
                Role(id=2, name="subject", description="Chủ thể"),
                Role(id=3, name="user", description="Người dùng"),
                Category(id=1, name="Đồ uống", slug="do-uong"),
            ]
        )
        session.flush()
        session.add_all(
            [
                User(id=1, role_id=1, email="admin@example.com", hashed_password="x", full_name="Quản trị viên", is_active=True),
                User(id=2, role_id=2, email="owner@example.com", hashed_password="x", full_name="Chủ HTX Cầu Đất", is_active=True),
                User(id=3, role_id=3, email="khach@example.com", hashed_password="x", full_name="Trần Thị Khách", is_active=True),
                User(id=4, role_id=3, email="khach2@example.com", hashed_password="x", full_name="Lê Văn Hai", is_active=True),
                User(id=5, role_id=2, email="other@example.com", hashed_password="x", full_name="Chủ thể khác", is_active=True),
            ]
        )
        session.flush()
        session.add_all(
            [
                Subject(id=1, user_id=2, name="HTX Chè Cầu Đất", type="cooperative", representative="Nguyễn Văn A",
                        phone="0912345678", address="Xuân Trường, Đà Lạt", district="Đà Lạt", status="approved"),
                Subject(id=2, user_id=5, name="Nhà vườn khác", type="household", representative="Phạm Văn B",
                        phone="0912345679", address="Đơn Dương", district="Đơn Dương", status="approved"),
            ]
        )
        session.flush()
        certificate = {
            "cert_year": 2025,
            "cert_issued_at": date(2025, 1, 1),
            "cert_expires_at": date(2099, 1, 1),
            "issuing_authority": "UBND tỉnh Lâm Đồng",
        }
        session.add_all(
            [
                Product(id=1, subject_id=1, category_id=1, name="Trà xanh Cầu Đất", slug="tra-xanh-cau-dat", star=4,
                        cert_code="OCOP-LD-1", description="Trà xanh từ đồi chè Cầu Đất.", status="approved", **certificate),
                Product(id=2, subject_id=1, category_id=1, name="Trà chưa duyệt", slug="tra-chua-duyet", star=3,
                        description="Đang chờ kiểm duyệt.", status="pending"),
                TourismLocation(id=1, subject_id=1, name="Cầu Đất Farm", slug="cau-dat-farm", type="tea_coffee_farm",
                                district="Đà Lạt", address="Xuân Trường, Đà Lạt", geom=CAU_DAT, services=[],
                                status="approved"),
                TourismLocation(id=2, name="Đồi chè công cộng", slug="doi-che-cong-cong", type="tea_coffee_farm",
                                district="Đà Lạt", address="Xuân Trường, Đà Lạt", geom=CAU_DAT, services=[],
                                status="approved"),
                TourismLocation(id=3, name="Vườn chờ duyệt", slug="vuon-cho-duyet", type="fruit_garden",
                                district="Đà Lạt", address="Đà Lạt", geom=CAU_DAT, services=[], status="pending"),
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


def post_review(client: TestClient, path: str, headers: dict, rating: int = 5, comment: str = COMMENT):
    return client.post(f"/api/v1/{path}/reviews", json={"rating": rating, "comment": comment}, headers=headers)


def moderate(client: TestClient, review_id: int, action: str, reason: str | None = None):
    body = {"action": action} if reason is None else {"action": action, "reason": reason}
    return client.patch(f"/api/v1/admin/reviews/{review_id}/moderation", json=body, headers=ADMIN)


def rating_of(testing_session: sessionmaker, model, target_id: int) -> Decimal:
    with testing_session() as session:
        return Decimal(session.get(model, target_id).rating_avg)


def test_user_creates_pending_review_hidden_until_approved(review_context) -> None:
    client, testing_session = review_context

    created = post_review(client, "products/1", USER, comment=f"  {COMMENT}  ")
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "pending"
    assert body["comment"] == COMMENT
    assert body["target"] == {"type": "product", "id": 1, "name": "Trà xanh Cầu Đất", "slug": "tra-xanh-cau-dat"}

    public = client.get("/api/v1/products/1/reviews").json()
    assert public["total"] == 0
    assert public["summary"] == {"average": 0.0, "count": 0, "distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}}

    approved = moderate(client, body["id"], "approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["reviewed_by_name"] == "Quản trị viên"

    public = client.get("/api/v1/products/1/reviews").json()
    assert public["total"] == 1
    assert public["items"][0]["author_name"] == "Trần Thị Khách"
    assert "email" not in public["items"][0]
    assert "khach@example.com" not in str(public)
    assert public["summary"]["average"] == 5.0
    assert public["summary"]["distribution"]["5"] == 1
    assert rating_of(testing_session, Product, 1) == Decimal("5.00")


def test_rating_avg_recalculated_on_moderation_edit_and_delete(review_context) -> None:
    client, testing_session = review_context
    first = post_review(client, "locations/2", USER, rating=5).json()
    second = post_review(client, "locations/2", USER2, rating=4).json()
    third = post_review(client, "locations/2", OTHER_SUBJECT, rating=4).json()
    for review in (first, second, third):
        assert moderate(client, review["id"], "approve").status_code == 200
    # (5 + 4 + 4) / 3 = 4.333... làm tròn 2 chữ số.
    assert rating_of(testing_session, TourismLocation, 2) == Decimal("4.33")
    summary = client.get("/api/v1/locations/2/reviews").json()["summary"]
    assert summary == {"average": 4.33, "count": 3, "distribution": {"1": 0, "2": 0, "3": 0, "4": 2, "5": 1}}

    rejected = moderate(client, third["id"], "reject", "Nội dung không liên quan tới điểm du lịch.")
    assert rejected.status_code == 200
    assert rejected.json()["rejection_reason"] == "Nội dung không liên quan tới điểm du lịch."
    assert rating_of(testing_session, TourismLocation, 2) == Decimal("4.50")

    edited = client.patch(f"/api/v1/reviews/{first['id']}", json={"rating": 2}, headers=USER)
    assert edited.status_code == 200
    assert edited.json()["status"] == "pending"
    assert edited.json()["rating"] == 2
    assert edited.json()["comment"] == COMMENT
    assert rating_of(testing_session, TourismLocation, 2) == Decimal("4.00")

    assert client.delete(f"/api/v1/reviews/{second['id']}", headers=USER2).status_code == 204
    assert rating_of(testing_session, TourismLocation, 2) == Decimal("0.00")
    assert client.get("/api/v1/locations/2/reviews").json()["total"] == 0


def test_edit_resets_rejection_and_requires_new_approval(review_context) -> None:
    client, _ = review_context
    review = post_review(client, "products/1", USER).json()
    moderate(client, review["id"], "reject", "Thiếu thông tin về trải nghiệm thực tế.")

    mine = client.get("/api/v1/reviews/me", headers=USER).json()
    assert mine["total"] == 1
    assert mine["items"][0]["status"] == "rejected"
    assert mine["items"][0]["rejection_reason"] == "Thiếu thông tin về trải nghiệm thực tế."

    edited = client.patch(
        f"/api/v1/reviews/{review['id']}",
        json={"comment": "Đã dùng hai tháng, trà thơm và vị hậu ngọt."},
        headers=USER,
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "pending"
    assert edited.json()["rejection_reason"] is None
    assert edited.json()["reviewed_at"] is None


def test_one_review_per_user_and_target(review_context) -> None:
    client, _ = review_context
    first = post_review(client, "products/1", USER)
    assert first.status_code == 201

    duplicate = post_review(client, "products/1", USER, rating=1)
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "REVIEW_ALREADY_EXISTS"
    assert duplicate.json()["details"] == {"review_id": first.json()["id"]}

    # Cùng người nhưng đối tượng khác thì vẫn được viết.
    assert post_review(client, "locations/2", USER).status_code == 201
    filtered = client.get("/api/v1/reviews/me?product_id=1", headers=USER).json()
    assert [item["id"] for item in filtered["items"]] == [first.json()["id"]]


def test_subject_cannot_review_own_product_or_location(review_context) -> None:
    client, _ = review_context
    own_product = post_review(client, "products/1", OWNER)
    assert own_product.status_code == 403
    assert own_product.json()["code"] == "OWN_TARGET_REVIEW_FORBIDDEN"
    own_location = post_review(client, "locations/1", OWNER)
    assert own_location.status_code == 403

    # Chủ thể vẫn đánh giá được sản phẩm, điểm của đơn vị khác.
    assert post_review(client, "products/1", OTHER_SUBJECT).status_code == 201
    assert post_review(client, "locations/2", OWNER).status_code == 201


def test_admin_does_not_write_reviews(review_context) -> None:
    client, _ = review_context
    response = post_review(client, "products/1", ADMIN)
    assert response.status_code == 403
    assert response.json()["code"] == "ADMIN_CANNOT_REVIEW"


def test_only_public_targets_can_be_reviewed(review_context) -> None:
    client, _ = review_context
    for path in ("products/2", "products/999", "locations/3", "locations/999"):
        assert post_review(client, path, USER).status_code == 404
        assert client.get(f"/api/v1/{path}/reviews").status_code == 404
    assert post_review(client, "products/2", USER).json()["code"] == "PRODUCT_NOT_FOUND"
    assert post_review(client, "locations/3", USER).json()["code"] == "LOCATION_NOT_FOUND"


def test_authentication_and_validation(review_context) -> None:
    client, _ = review_context
    assert post_review(client, "products/1", {}).status_code == 401
    assert client.get("/api/v1/reviews/me").status_code == 401
    assert client.patch("/api/v1/reviews/1", json={"rating": 3}).status_code == 401
    assert client.delete("/api/v1/reviews/1").status_code == 401

    for rating, comment in ((0, COMMENT), (6, COMMENT), (5, "   ngắn   "), (5, "x" * 1001)):
        response = post_review(client, "products/1", USER, rating=rating, comment=comment)
        assert response.status_code == 422
        assert response.json()["code"] == "VALIDATION_ERROR"

    review = post_review(client, "products/1", USER).json()
    assert client.patch(f"/api/v1/reviews/{review['id']}", json={}, headers=USER).status_code == 422


def test_only_author_can_edit_or_delete(review_context) -> None:
    client, testing_session = review_context
    review = post_review(client, "products/1", USER).json()

    forbidden = client.patch(f"/api/v1/reviews/{review['id']}", json={"rating": 1}, headers=USER2)
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "REVIEW_FORBIDDEN"
    assert client.delete(f"/api/v1/reviews/{review['id']}", headers=USER2).status_code == 403
    assert client.delete(f"/api/v1/reviews/{review['id']}", headers=ADMIN).status_code == 403
    assert client.patch("/api/v1/reviews/999", json={"rating": 1}, headers=USER).status_code == 404

    with testing_session() as session:
        assert session.get(Review, review["id"]) is not None


def test_admin_moderation_rules_and_filters(review_context) -> None:
    client, _ = review_context
    product_review = post_review(client, "products/1", USER).json()
    location_review = post_review(client, "locations/2", USER2, comment="Đồi chè đẹp, đường đi hơi khó.").json()

    assert client.get("/api/v1/admin/reviews", headers=USER).status_code == 403
    assert client.get("/api/v1/admin/reviews").status_code == 401
    assert moderate(client, 999, "approve").status_code == 404

    missing_reason = moderate(client, product_review["id"], "reject", "   ")
    assert missing_reason.status_code == 422
    assert missing_reason.json()["code"] == "REJECTION_REASON_REQUIRED"
    assert client.patch(
        f"/api/v1/admin/reviews/{product_review['id']}/moderation",
        json={"action": "hide"},
        headers=ADMIN,
    ).status_code == 422

    dashboard = client.get("/api/v1/admin/dashboard", headers=ADMIN).json()
    assert dashboard["pending_reviews"] == 2

    pending = client.get("/api/v1/admin/reviews?status=pending", headers=ADMIN).json()
    assert pending["total"] == 2
    assert {item["author"]["email"] for item in pending["items"]} == {"khach@example.com", "khach2@example.com"}

    locations_only = client.get("/api/v1/admin/reviews?target=location", headers=ADMIN).json()
    assert [item["id"] for item in locations_only["items"]] == [location_review["id"]]
    assert locations_only["items"][0]["target"]["type"] == "location"

    searched = client.get("/api/v1/admin/reviews?q=Cầu Đất", headers=ADMIN).json()
    assert [item["id"] for item in searched["items"]] == [product_review["id"]]
    by_author = client.get("/api/v1/admin/reviews?q=Lê Văn", headers=ADMIN).json()
    assert [item["id"] for item in by_author["items"]] == [location_review["id"]]

    assert moderate(client, product_review["id"], "approve").status_code == 200
    again = moderate(client, product_review["id"], "approve")
    assert again.status_code == 409
    assert again.json()["code"] == "REVIEW_ALREADY_MODERATED"
    # Đánh giá đã duyệt vẫn có thể bị gỡ khi phát hiện vi phạm.
    hidden = moderate(client, product_review["id"], "reject", "Có thông tin quảng cáo.")
    assert hidden.status_code == 200
    assert hidden.json()["status"] == "rejected"

    dashboard = client.get("/api/v1/admin/dashboard", headers=ADMIN).json()
    assert dashboard["pending_reviews"] == 1
    approved_page = client.get("/api/v1/admin/reviews?status=approved", headers=ADMIN).json()
    assert approved_page["total"] == 0


def test_public_list_paginates_newest_first(review_context) -> None:
    client, _ = review_context
    ids = []
    for headers in (USER, USER2, OTHER_SUBJECT):
        review = post_review(client, "products/1", headers).json()
        moderate(client, review["id"], "approve")
        ids.append(review["id"])

    first_page = client.get("/api/v1/products/1/reviews?page=1&page_size=2").json()
    second_page = client.get("/api/v1/products/1/reviews?page=2&page_size=2").json()
    assert first_page["total"] == 3
    assert len(first_page["items"]) == 2
    assert len(second_page["items"]) == 1
    returned = [item["id"] for item in first_page["items"] + second_page["items"]]
    assert sorted(returned) == sorted(ids)


def test_database_requires_reason_for_rejected_review(review_context) -> None:
    _, testing_session = review_context
    with testing_session() as session:
        session.add(
            Review(user_id=3, product_id=1, rating=3, comment=COMMENT, status="rejected", rejection_reason="  ")
        )
        with pytest.raises(IntegrityError):
            session.commit()
