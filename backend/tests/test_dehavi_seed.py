"""Opt-in integration tests against a disposable, isolated PostGIS container.

Never uses DATABASE_URL or the demo database. See docs/DEHAVI_DEMO_DATA.md.
"""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.services import routing


PRODUCT = "tham-khao-ca-phe-dehavi-valley"
LOCATION = "dehavi-showroom"
SUBJECT = "Công ty TNHH Cà phê Hân Vinh"
RECOGNITION = "https://nhandan.vn/ocop/ca-phe-pha-phin-dehavi-valley-prod545.html"


@pytest.fixture
def seeded_dehavi():
    dsn = os.environ.get("DEHAVI_SEED_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Requires explicitly configured disposable PostGIS; never uses demo DB")
    url = make_url(dsn)
    assert os.environ.get("DEHAVI_ISOLATED_POSTGIS") == "1"
    assert url.database == "dehavi_seed_test"
    assert url.host == "127.0.0.1"
    sql_dir = Path(os.environ.get("DEHAVI_SEED_SQL_DIR", Path(__file__).resolve().parents[2] / "database"))
    schema = "dehavi_test_" + uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as connection:
        # Test DB only. Each test gets its own schema; the container is discarded.
        connection.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        connection.execute(f'CREATE SCHEMA "{schema}"')
        connection.execute(f'SET search_path TO "{schema}", public')
        connection.execute((sql_dir / "schema.sql").read_text(encoding="utf-8"), prepare=False)
        # Existing unrelated records must survive even the first seed unchanged.
        connection.execute("""
            INSERT INTO users (role_id,email,hashed_password,full_name,is_active)
            SELECT id,'unrelated-' || name || '@local.invalid','!disabled','Unrelated',FALSE
            FROM roles WHERE name IN ('admin','subject');
            INSERT INTO subjects (user_id,name,type,representative,phone,address,district,status,reviewed_by,reviewed_at)
            SELECT owner.id,'Unrelated company','company','Unknown','Unknown','Other address','Other district',
                   'approved',admin.id,CURRENT_TIMESTAMP
            FROM users owner CROSS JOIN users admin
            WHERE owner.email='unrelated-subject@local.invalid' AND admin.email='unrelated-admin@local.invalid';
            INSERT INTO categories (name,slug,description) VALUES ('Đồ uống','do-uong','Existing category description');
            INSERT INTO ocop_products (subject_id,category_id,name,slug,status)
            SELECT s.id,c.id,'Unrelated product','unrelated-product','rejected' FROM subjects s CROSS JOIN categories c;
            INSERT INTO tourism_locations (name,slug,type,district,address,geom,status,subject_id)
            SELECT 'Cầu Đất Farm','cau-dat-farm','tea_coffee_farm','Đà Lạt','Cầu Đất',
                   ST_SetSRID(ST_MakePoint(108.547398,11.879583),4326),'approved',id FROM subjects;
        """, prepare=False)
        protected = {}
        for table in ('users', 'subjects', 'categories', 'ocop_products', 'tourism_locations'):
            protected[table] = dict(connection.execute(f'SELECT id,row_to_json(t)::text FROM {table} t').fetchall())

        def seed():
            connection.execute((sql_dir / "seed_dehavi_demo.sql").read_text(encoding="utf-8"), prepare=False)
            for table, rows in protected.items():
                current = dict(connection.execute(f'SELECT id,row_to_json(t)::text FROM {table} t').fetchall())
                assert all(current[key] == value for key, value in rows.items()), table

        seed()
        engine = create_engine(
            url.set(drivername="postgresql+psycopg"),
            connect_args={"options": f"-csearch_path={schema},public"},
        )

        def override_db():
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_db] = override_db
        try:
            with TestClient(app) as client:
                yield client, connection, seed
        finally:
            app.dependency_overrides.pop(get_db, None)
            engine.dispose()


def test_seed_public_product_location_chain(seeded_dehavi):
    client, db, _ = seeded_dehavi
    listing = client.get("/api/v1/products", params={"search": "Dehavi Valley"})
    assert listing.status_code == 200
    assert [p["slug"] for p in listing.json()["items"]] == [PRODUCT]
    response = client.get(f"/api/v1/products/{PRODUCT}")
    assert response.status_code == 200
    product = response.json()
    assert product["star"] == 4
    assert product["subject"]["name"] == SUBJECT
    assert db.execute("SELECT count(*) FROM ocop_products WHERE slug <> 'unrelated-product'").fetchone()[0] == 1
    assert db.execute("SELECT address FROM subjects WHERE name=%s", (SUBJECT,)).fetchone()[0] == "Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng"
    assert "70% Robusta Nam Ban" in product["ingredients"]
    assert "30% Arabica Cầu Đất" in product["ingredients"]
    assert product["cert_code"] is None
    assert product["cert_issued_at"] is None
    assert product["cert_expires_at"] is None
    assert [(s["source_url"], s["verification_level"]) for s in product["recognition_sources"]] == [(RECOGNITION, "B1")]
    assert [item["slug"] for item in product["related_locations"]] == [LOCATION]

    listing = client.get("/api/v1/locations", params={"search": "Dehavi"})
    assert listing.status_code == 200
    assert [item["slug"] for item in listing.json()["items"]] == [LOCATION]
    response = client.get(f"/api/v1/locations/{LOCATION}")
    assert response.status_code == 200
    location = response.json()
    assert location["name"] == "Dehavi Showroom"
    assert location["subject"]["id"] == product["subject"]["id"]
    assert location["subject"]["name"] == SUBJECT
    assert location["type"] == "other"
    assert location["address"] == "Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng"
    assert [p["slug"] for p in location["products"]] == [PRODUCT]
    assert location["source_url"] == "https://dehavi.com/cup-dehavi-showroom"
    assert client.get("/api/v1/locations/cau-dat-farm").json()["products"] == []
    assert db.execute("SELECT count(*) FROM product_sources ps JOIN ocop_products p ON p.id=ps.product_id WHERE p.slug=%s", (PRODUCT,)).fetchone()[0] == 6


def test_seed_postgis_map_nearby_and_route_destination(seeded_dehavi, monkeypatch):
    client, db, _ = seeded_dehavi
    longitude, latitude, srid, provenance = db.execute(
        "SELECT ST_X(geom), ST_Y(geom), ST_SRID(geom), review_note FROM tourism_locations WHERE slug=%s", (LOCATION,)
    ).fetchone()
    assert (longitude, latitude, srid) == (108.341191, 11.842186, 4326)
    assert "manual verification from Google Maps by project member Thuận" in provenance
    assert "11.842185897748251" in provenance
    assert "108.34119094061145" in provenance
    response = client.get("/api/v1/map/locations", params={"search": "Dehavi"})
    assert response.status_code == 200
    features = response.json()["features"]
    assert len(features) == 1
    assert features[0]["properties"]["slug"] == LOCATION
    assert features[0]["geometry"]["coordinates"] == [longitude, latitude]
    nearby = client.get("/api/v1/map/nearby", params={"latitude": latitude, "longitude": longitude, "radius_km": 0.1})
    assert nearby.status_code == 200
    assert [(p["slug"], p["distance_m"]) for p in nearby.json()["items"]] == [(LOCATION, 0)]

    requests = []

    def osrm_response(request):
        requests.append(request)
        return httpx.Response(200, json={"code": "Ok", "routes": [{
            "distance": 1000, "duration": 120,
            "geometry": {"type": "LineString", "coordinates": [[108.34, 11.84], [longitude, latitude]]},
        }]})

    monkeypatch.setattr(routing, "_create_client", lambda timeout: httpx.Client(transport=httpx.MockTransport(osrm_response)))
    route = client.get("/api/v1/map/route", params={"destination": LOCATION, "from_latitude": 11.84, "from_longitude": 108.34})
    assert route.status_code == 200
    assert "/108.340000,11.840000;108.341191,11.842186" in str(requests[0].url)


@pytest.mark.parametrize('moderation', ['archived', 'rejected'])
def test_repeat_seed_preserves_moderation_and_existing_location(seeded_dehavi, moderation):
    client, db, seed = seeded_dehavi
    before = db.execute("SELECT row_to_json(l)::text FROM tourism_locations l WHERE slug='cau-dat-farm'").fetchone()[0]
    tables = ('users','subjects','categories','ocop_products','tourism_locations','data_sources','product_sources','location_ocop_products')
    counts = {table: db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in tables}
    db.execute("UPDATE ocop_products SET status=%s WHERE slug=%s", (moderation, PRODUCT))
    db.execute("UPDATE tourism_locations SET status=%s, review_note='Reviewer decision', geom=ST_SetSRID(ST_MakePoint(108.34,11.84),4326) WHERE slug=%s", (moderation, LOCATION))
    db.execute("UPDATE subjects SET status='rejected', rejection_reason='Reviewer decision' WHERE name=%s", (SUBJECT,))
    seed()
    assert {table: db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in tables} == counts
    assert db.execute("SELECT status,rejection_reason FROM subjects WHERE name=%s", (SUBJECT,)).fetchone() == ('rejected', 'Reviewer decision')
    assert db.execute("SELECT row_to_json(l)::text FROM tourism_locations l WHERE slug='cau-dat-farm'").fetchone()[0] == before
    assert db.execute("SELECT status,review_note,ST_X(geom),ST_Y(geom) FROM tourism_locations WHERE slug=%s", (LOCATION,)).fetchone() == (moderation, 'Reviewer decision', 108.34, 11.84)
    assert client.get(f"/api/v1/products/{PRODUCT}").status_code == 404
    assert client.get(f"/api/v1/locations/{LOCATION}").status_code == 404


@pytest.mark.parametrize('other_owner', [False, True])
def test_existing_showroom_slug_with_other_owner_is_not_claimed(seeded_dehavi, other_owner):
    _, db, seed = seeded_dehavi
    db.execute("DELETE FROM location_ocop_products WHERE location_id=(SELECT id FROM tourism_locations WHERE slug=%s)", (LOCATION,))
    subject_id = db.execute("SELECT id FROM subjects WHERE name='Unrelated company'").fetchone()[0] if other_owner else None
    db.execute("UPDATE tourism_locations SET subject_id=%s, review_note='Existing location' WHERE slug=%s", (subject_id, LOCATION))
    seed()
    assert db.execute("SELECT subject_id,review_note FROM tourism_locations WHERE slug=%s", (LOCATION,)).fetchone() == (subject_id, 'Existing location')
    assert db.execute("SELECT count(*) FROM location_ocop_products WHERE location_id=(SELECT id FROM tourism_locations WHERE slug=%s)", (LOCATION,)).fetchone()[0] == 0


def test_manufacturer_sources_alone_do_not_make_valley_public(seeded_dehavi):
    client, db, _ = seeded_dehavi
    db.execute("DELETE FROM product_sources WHERE product_id=(SELECT id FROM ocop_products WHERE slug=%s) AND evidence_role='recognition'", (PRODUCT,))
    assert client.get(f"/api/v1/products/{PRODUCT}").status_code == 404
    assert client.get("/api/v1/products", params={"search": "Dehavi Valley"}).json()["total"] == 0
    assert client.get(f"/api/v1/locations/{LOCATION}").json()["products"] == []


def test_foreign_product_owner_aborts_seed_atomically(seeded_dehavi):
    _, db, seed = seeded_dehavi
    db.execute("UPDATE ocop_products SET subject_id=(SELECT id FROM subjects WHERE name='Unrelated company') WHERE slug=%s", (PRODUCT,))
    before = db.execute("SELECT row_to_json(p)::text FROM ocop_products p WHERE slug=%s", (PRODUCT,)).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException, match='identity/ownership conflict'):
        seed()
    db.execute('ROLLBACK')
    assert db.execute("SELECT row_to_json(p)::text FROM ocop_products p WHERE slug=%s", (PRODUCT,)).fetchone()[0] == before
