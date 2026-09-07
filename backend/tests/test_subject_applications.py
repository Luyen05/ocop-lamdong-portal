from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User


@pytest.fixture
def subject_context() -> Generator[tuple[TestClient, sessionmaker], None, None]:
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
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, testing_session
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def register_and_login(client: TestClient, email: str) -> tuple[dict, str]:
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "MatKhauAnToan123",
            "full_name": "Nguyễn Văn A",
            "phone": "0912345678",
        },
    )
    assert registered.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "MatKhauAnToan123"},
    )
    assert login.status_code == 200
    return registered.json(), login.json()["access_token"]


def application_payload(tax_code: str = "HTX-001") -> dict:
    return {
        "name": "Hợp tác xã Nông nghiệp Đà Lạt",
        "type": "cooperative",
        "tax_code": tax_code,
        "representative": "Nguyễn Văn A",
        "phone": "0912345678",
        "email": "contact@example.com",
        "address": "Phường 8, thành phố Đà Lạt",
        "district": "Đà Lạt",
    }


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_admin(
    client: TestClient,
    testing_session: sessionmaker,
) -> str:
    registered, _ = register_and_login(client, "admin@example.com")
    with testing_session() as session:
        user = session.get(User, registered["id"])
        admin_role = session.get(Role, 1)
        assert user is not None
        assert admin_role is not None
        user.role = admin_role
        session.commit()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "MatKhauAnToan123"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_user_can_submit_and_read_own_application(subject_context) -> None:
    client, _ = subject_context
    registered, token = register_and_login(client, "user@example.com")

    created = client.post(
        "/api/v1/subject-applications",
        headers=auth_header(token),
        json=application_payload(),
    )
    fetched = client.get(
        "/api/v1/subject-applications/me",
        headers=auth_header(token),
    )

    assert created.status_code == 201
    assert created.json()["user_id"] == registered["id"]
    assert created.json()["status"] == "pending"
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created.json()["id"]


def test_user_cannot_create_duplicate_application(subject_context) -> None:
    client, _ = subject_context
    _, token = register_and_login(client, "user@example.com")
    first = client.post(
        "/api/v1/subject-applications",
        headers=auth_header(token),
        json=application_payload(),
    )

    duplicate = client.post(
        "/api/v1/subject-applications",
        headers=auth_header(token),
        json=application_payload("HTX-002"),
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "SUBJECT_APPLICATION_ALREADY_EXISTS"


def test_regular_user_cannot_list_admin_applications(subject_context) -> None:
    client, _ = subject_context
    _, token = register_and_login(client, "user@example.com")

    response = client.get(
        "/api/v1/admin/subject-applications",
        headers=auth_header(token),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "INSUFFICIENT_PERMISSIONS"


def test_admin_can_approve_and_grant_subject_role(subject_context) -> None:
    client, testing_session = subject_context
    applicant, applicant_token = register_and_login(client, "user@example.com")
    created = client.post(
        "/api/v1/subject-applications",
        headers=auth_header(applicant_token),
        json=application_payload(),
    )
    admin_token = make_admin(client, testing_session)

    listed = client.get(
        "/api/v1/admin/subject-applications?status=pending",
        headers=auth_header(admin_token),
    )
    approved = client.patch(
        f"/api/v1/admin/subject-applications/{created.json()['id']}/moderation",
        headers=auth_header(admin_token),
        json={"status": "approved", "note": "Hồ sơ hợp lệ."},
    )

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["applicant"]["role"] == "subject"
    with testing_session() as session:
        stored_user = session.get(User, applicant["id"])
        stored_subject = session.get(Subject, created.json()["id"])
        assert stored_user is not None
        assert stored_subject is not None
        assert stored_user.role.name == "subject"
        assert stored_subject.status == "approved"
        assert stored_subject.reviewed_by is not None
        assert stored_subject.reviewed_at is not None
        assert stored_subject.rejection_reason is None


def test_rejection_requires_note_and_user_can_resubmit(subject_context) -> None:
    client, testing_session = subject_context
    _, applicant_token = register_and_login(client, "user@example.com")
    created = client.post(
        "/api/v1/subject-applications",
        headers=auth_header(applicant_token),
        json=application_payload(),
    )
    admin_token = make_admin(client, testing_session)
    moderation_url = (
        f"/api/v1/admin/subject-applications/{created.json()['id']}/moderation"
    )

    missing_note = client.patch(
        moderation_url,
        headers=auth_header(admin_token),
        json={"status": "rejected"},
    )
    rejected = client.patch(
        moderation_url,
        headers=auth_header(admin_token),
        json={"status": "rejected", "note": "Thiếu thông tin địa chỉ."},
    )
    resubmitted = client.put(
        "/api/v1/subject-applications/me",
        headers=auth_header(applicant_token),
        json={**application_payload(), "address": "Địa chỉ đã được bổ sung, Đà Lạt"},
    )

    assert missing_note.status_code == 422
    assert rejected.status_code == 200
    assert rejected.json()["moderation_note"] == "Thiếu thông tin địa chỉ."
    assert resubmitted.status_code == 200
    assert resubmitted.json()["status"] == "pending"
    assert resubmitted.json()["moderation_note"] is None
