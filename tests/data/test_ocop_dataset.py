from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "data" / "ocop" / "ocop_records.json"
MANIFEST_PATH = ROOT / "data" / "ocop" / "source_manifest.csv"
WORKBOOK_PATH = ROOT / "data" / "ocop" / "ocop_lamdong_2025_2026.xlsx"
DOCX_PATH = ROOT / "docs" / "PHU_LUC_NGUON_DU_LIEU_OCOP_2025_2026.docx"
SEED_PATH = ROOT / "database" / "seed_ocop_2025_2026.sql"
PUBLIC_ROUTE_PATH = ROOT / "backend" / "app" / "api" / "routes" / "products.py"


def load_dataset() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def load_sources() -> list[dict[str, str]]:
    with MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def product_rows(dataset: dict) -> list[dict]:
    return [
        {**product, "batch": batch}
        for batch in dataset["batches"]
        for product in batch["products"]
    ]


def test_dataset_has_target_size_and_all_legacy_regions() -> None:
    rows = product_rows(load_dataset())
    regions = {row["batch"]["legacy_region"] for row in rows}

    assert len(rows) == 60
    assert 50 <= len(rows) <= 100
    assert {"Lâm Đồng cũ", "Bình Thuận cũ", "Đắk Nông cũ"} <= regions


def test_public_records_use_only_confirmed_primary_sources() -> None:
    dataset = load_dataset()
    source_levels = {source["source_id"]: source["verification_level"] for source in load_sources()}

    for batch in dataset["batches"]:
        assert source_levels[batch["source_id"]] in {"A", "B1"}
        if batch["publish_eligible"]:
            assert batch["verification_level"] in {"A", "B1"}
        if batch.get("secondary_source_id"):
            assert source_levels[batch["secondary_source_id"]] == "B2"


def test_ratings_dates_and_unique_products_are_consistent() -> None:
    rows = product_rows(load_dataset())
    record_ids = [row["record_id"] for row in rows]
    natural_keys = [
        (row["product_name"].casefold().strip(), row["subject_name"].casefold().strip())
        for row in rows
    ]

    assert len(record_ids) == len(set(record_ids))
    assert len(natural_keys) == len(set(natural_keys))
    assert all(3 <= row["batch"]["star_rating"] <= 5 for row in rows)

    for row in rows:
        issued = row["batch"].get("cert_issued_at")
        expires = row["batch"].get("cert_expires_at")
        if issued and expires:
            assert date.fromisoformat(expires) > date.fromisoformat(issued)


def test_changed_addresses_have_a_legal_mapping_or_documented_issue() -> None:
    dataset = load_dataset()
    mapped_current_communes = {item["current_commune"] for item in dataset["admin_mappings"]}

    for row in product_rows(dataset):
        if row["original_address"] == row["current_address"]:
            continue
        if row["current_commune"]:
            assert row["current_commune"] in mapped_current_communes
        else:
            assert row.get("notes"), row["record_id"]


def test_local_source_files_match_manifest_hashes() -> None:
    local_sources = [source for source in load_sources() if source["local_file"]]
    assert len(local_sources) == 10

    for source in local_sources:
        path = ROOT / source["local_file"]
        assert path.is_file(), source["source_id"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]


def test_reused_2026_slugs_remain_stable() -> None:
    expected = {
        "tham-khao-2026-mam-nem-seagull",
        "tham-khao-2026-nam-fresh-cordyceps-vietnam",
        "tham-khao-2026-nam-cordyceps-vietnam-say-thang-hoa",
        "tham-khao-2026-bechamp-coffee-natural-nang-vang",
        "tham-khao-2026-bechamp-coffee-gu-manh",
        "tham-khao-2026-bechamp-coffee-hoa-tan-nam-linh-chi",
        "tham-khao-2026-macca-bechamp",
        "tham-khao-2026-bechamp-coffee-honey-nang-vang",
        "tham-khao-2026-cao-atiso-hoang-an",
    }
    actual = {
        row["slug"]
        for row in product_rows(load_dataset())
        if row["batch"]["batch_id"] == "LD-3981-2026"
    }
    assert actual == expected


def test_seed_is_idempotent_by_design_and_avoids_real_accounts() -> None:
    seed = SEED_PATH.read_text(encoding="utf-8")

    assert "ON CONFLICT (slug) DO UPDATE" in seed
    assert "ON CONFLICT (source_url) DO UPDATE" in seed
    assert "ON CONFLICT (product_id, source_id, evidence_role) DO UPDATE" in seed
    assert "@local.invalid" in seed
    assert "is_active = FALSE" in seed
    assert "'liên hệ chủ thể'" in seed
    assert "public-reference.svg" in seed
    assert not re.search(r"\b0(?:\d[ .-]?){9,10}\b", seed)


def test_public_api_route_requires_approved_product_and_subject() -> None:
    route = PUBLIC_ROUTE_PATH.read_text(encoding="utf-8")

    assert 'Product.status == "approved"' in route
    assert 'Subject.status == "approved"' in route


def test_workbook_contains_exact_required_sheets() -> None:
    with zipfile.ZipFile(WORKBOOK_PATH) as archive:
        workbook_xml = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    names = [sheet.attrib["name"] for sheet in workbook_xml.findall("main:sheets/main:sheet", namespace)]

    assert names == ["README", "PRODUCTS", "SOURCES", "ADMIN_MAPPING", "ISSUES"]


def test_docx_contains_required_sections_and_disclaimer() -> None:
    with zipfile.ZipFile(DOCX_PATH) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")

    for phrase in (
        "Phạm vi và mục đích",
        "Cấp độ tin cậy của nguồn",
        "Danh sách 60 sản phẩm đã chuẩn hóa",
        "Ánh xạ địa chỉ trước và sau sắp xếp",
        "không thay thế cơ sở dữ liệu hành chính chính thức",
    ):
        assert phrase in document_xml
