"""Kiểm tra model khớp migration 009, 011: trạng thái, nguồn vị trí, bản nháp, yêu cầu cập nhật điểm du lịch."""

from collections.abc import Generator
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.geometry import GeoPoint, register_sqlite_geo_functions
from app.models.location import LocationImage, TourismLocation, TourismLocationChangeRequest
from app.models.role import Role
from app.models.subject import Subject
from app.models.user import User


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", register_sqlite_geo_functions)
    # SQLite chỉ kiểm tra khóa ngoại khi bật PRAGMA này.
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        role = Role(id=2, name="subject", description="Chủ thể")
        db.add_all(
            [
                role,
                User(id=1, role=role, email="farm@example.com", hashed_password="x", full_name="Nhà vườn", is_active=True),
                Subject(
                    id=1,
                    user_id=1,
                    name="HTX Cầu Đất",
                    type="cooperative",
                    representative="Nguyễn Văn A",
                    phone="0912345678",
                    address="Đà Lạt",
                    district="Đà Lạt",
                    status="approved",
                ),
            ]
        )
        db.commit()
        yield db
    Base.metadata.drop_all(engine)


def new_location(**overrides) -> TourismLocation:
    values = {
        "name": "Vườn dâu Cầu Đất",
        "slug": "vuon-dau-cau-dat",
        "type": "fruit_garden",
        "district": "Đà Lạt",
        "address": "Xuân Trường, Đà Lạt",
        "geom": GeoPoint(longitude=108.5474, latitude=11.8796),
        "services": [],
    }
    values.update(overrides)
    return TourismLocation(**values)


def test_new_location_defaults_to_draft_imported_version_one(session: Session) -> None:
    location = new_location()
    session.add(location)
    session.commit()

    assert location.status == "draft"
    assert location.location_source == "admin_import"
    assert location.version == 1
    assert location.submitted_at is None
    assert location.reviewed_by is None


def test_subject_declared_location_keeps_source_and_gps_accuracy(session: Session) -> None:
    location = new_location(subject_id=1, location_source="device_gps", location_accuracy_m=Decimal("12.5"), status="pending")
    session.add(location)
    session.commit()
    session.refresh(location)

    assert location.subject.name == "HTX Cầu Đất"
    assert location.location_source == "device_gps"
    assert location.location_accuracy_m == Decimal("12.50")


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "published"},
        {"location_source": "geocoder"},
        {"location_accuracy_m": Decimal("-1")},
        {"version": 0},
    ],
)
def test_location_rejects_invalid_values(session: Session, overrides: dict) -> None:
    session.add(new_location(**overrides))

    with pytest.raises(IntegrityError):
        session.commit()


def test_only_drafts_may_miss_position_district_or_address(session: Session) -> None:
    empty = {"geom": None, "district": None, "address": None}
    session.add_all(
        [
            new_location(slug="nhap", status="draft", **empty),
            new_location(slug="bo-sung", status="needs_revision", **empty),
            new_location(slug="ngung", status="archived"),
        ]
    )
    session.commit()

    for missing in ("geom", "district", "address"):
        session.add(new_location(slug=f"cho-duyet-{missing}", status="pending", **{missing: None}))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_delete_request_stores_real_null_payload(session: Session) -> None:
    location = new_location(subject_id=1, status="approved")
    session.add(location)
    session.commit()

    session.add(
        TourismLocationChangeRequest(
            location_id=location.id,
            subject_id=1,
            request_type="delete",
            proposed_data=None,
            reason="Tạm dừng đón khách",
            base_version=1,
        )
    )
    session.commit()

    assert session.execute(
        text("SELECT proposed_data IS NULL FROM tourism_location_change_requests")
    ).scalar_one() == 1


def test_change_request_payload_must_match_type(session: Session) -> None:
    location = new_location(subject_id=1, status="approved")
    session.add(location)
    session.commit()

    session.add(
        TourismLocationChangeRequest(
            location_id=location.id,
            subject_id=1,
            request_type="update",
            proposed_data={"name": "Vườn dâu Cầu Đất mới", "latitude": 11.88, "longitude": 108.55},
            base_version=location.version,
        )
    )
    session.commit()
    assert location.change_requests[0].status == "pending"

    session.add(
        TourismLocationChangeRequest(
            location_id=location.id,
            subject_id=1,
            request_type="delete",
            proposed_data={"name": "không hợp lệ"},
            base_version=1,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_location_removes_images_and_change_requests(session: Session) -> None:
    location = new_location(subject_id=1, status="approved")
    location.images.append(
        LocationImage(image_url="/uploads/locations/1/a.webp", storage_path="locations/1/a.webp", alt_text="Vườn dâu")
    )
    session.add(location)
    session.flush()
    session.add(TourismLocationChangeRequest(location_id=location.id, subject_id=1, request_type="delete", base_version=1))
    session.commit()

    session.delete(location)
    session.commit()

    assert session.query(LocationImage).count() == 0
    assert session.query(TourismLocationChangeRequest).count() == 0
