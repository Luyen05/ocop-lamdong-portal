"""GET/PATCH /subject/profile: chủ thể đã duyệt sửa thông tin liên hệ của đơn vị."""

from app.models.subject import Subject
from app.models.user import User
from test_subject_products import auth_header, subject_product_context  # noqa: F401


URL = "/api/v1/subject/profile"


def test_approved_subject_reads_profile(subject_product_context) -> None:
    client, _ = subject_product_context

    response = client.get(URL, headers=auth_header(1, "subject"))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "HTX Đà Lạt"
    assert body["status"] == "approved"


def test_approved_subject_updates_contact_fields(subject_product_context) -> None:
    client, testing_session = subject_product_context

    response = client.patch(
        URL,
        headers=auth_header(1, "subject"),
        json={
            "representative": "  Trần Thị B ",
            "phone": "0909123456",
            "email": "HTX@Example.com",
            "address": "12 Trần Phú, phường Xuân Hương - Đà Lạt",
            "district": "phường Xuân Hương - Đà Lạt",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["representative"] == "Trần Thị B"
    assert body["phone"] == "0909123456"
    assert body["email"].lower() == "htx@example.com"
    assert body["district"] == "phường Xuân Hương - Đà Lạt"
    assert body["name"] == "HTX Đà Lạt"
    assert body["status"] == "approved"
    with testing_session() as session:
        subject = session.get(Subject, 1)
        assert subject.address == "12 Trần Phú, phường Xuân Hương - Đà Lạt"
        assert subject.status == "approved"
    # Chủ thể khác không bị ảnh hưởng.
    assert client.get(URL, headers=auth_header(2, "subject")).json()["representative"] == "Nguyễn Văn B"


def test_partial_update_and_clearing_email(subject_product_context) -> None:
    client, _ = subject_product_context
    headers = auth_header(1, "subject")
    client.patch(URL, headers=headers, json={"email": "htx@example.com"})

    response = client.patch(URL, headers=headers, json={"email": "  "})

    assert response.status_code == 200
    assert response.json()["email"] is None
    assert response.json()["phone"] == "0912345678"


def test_locked_identity_fields_are_rejected(subject_product_context) -> None:
    client, _ = subject_product_context

    for payload in (
        {"name": "Tên mới"},
        {"type": "enterprise", "phone": "0909123456"},
        {"tax_code": "0123456789"},
    ):
        response = client.patch(URL, headers=auth_header(1, "subject"), json=payload)
        assert response.status_code == 422
        assert response.json()["code"] == "SUBJECT_IDENTITY_LOCKED"
        assert "quản trị viên" in response.json()["message"]

    assert client.get(URL, headers=auth_header(1, "subject")).json()["phone"] == "0912345678"


def test_contact_fields_are_validated(subject_product_context) -> None:
    client, _ = subject_product_context
    headers = auth_header(1, "subject")

    for payload in (
        {},
        {"phone": "123"},
        {"representative": "A"},
        {"address": "abc"},
        {"district": None},
        {"email": "khong-phai-email"},
        {"status": "pending"},
    ):
        response = client.patch(URL, headers=headers, json=payload)
        assert response.status_code == 422, payload


def test_regular_user_and_admin_are_forbidden(subject_product_context) -> None:
    client, _ = subject_product_context

    for user_id, role in ((3, "user"), (4, "admin")):
        assert client.get(URL, headers=auth_header(user_id, role)).status_code == 403
        assert client.patch(URL, headers=auth_header(user_id, role), json={"phone": "0909123456"}).status_code == 403
    assert client.get(URL).status_code == 401


def test_subject_without_approved_profile_is_forbidden(subject_product_context) -> None:
    client, testing_session = subject_product_context
    with testing_session() as session:
        session.add(
            User(id=5, role_id=2, email="pending@example.com", hashed_password="x", full_name="Chờ duyệt", is_active=True)
        )
        session.flush()
        session.add(
            Subject(
                id=5,
                user_id=5,
                name="HTX chờ duyệt",
                type="cooperative",
                representative="Lê Văn C",
                phone="0911222333",
                address="Bảo Lộc",
                district="Bảo Lộc",
                status="pending",
            )
        )
        session.commit()

    read = client.get(URL, headers=auth_header(5, "subject"))
    patched = client.patch(URL, headers=auth_header(5, "subject"), json={"phone": "0909123456"})

    assert read.status_code == 403
    assert patched.status_code == 403
    assert patched.json()["code"] == "APPROVED_SUBJECT_REQUIRED"
