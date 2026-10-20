"""Loại chủ thể trong các file seed phải khớp schema API, nếu không GET hồ sơ chủ thể lỗi 500."""

import re
from pathlib import Path
from typing import get_args

from app.schemas.subject import SubjectType


DATABASE_DIR = Path(__file__).resolve().parents[2] / "database"
SEED_FILES = sorted(DATABASE_DIR.glob("seed_*.sql"))
VALID_TYPES = set(get_args(SubjectType))


def test_seed_files_exist() -> None:
    assert SEED_FILES, "không tìm thấy file seed trong thư mục database"


def test_no_seed_uses_company_subject_type() -> None:
    offenders = [path.name for path in SEED_FILES if "'company'" in path.read_text(encoding="utf-8")]

    assert offenders == []


def test_ocop_reference_subject_types_are_valid() -> None:
    content = (DATABASE_DIR / "seed_ocop_2025_2026.sql").read_text(encoding="utf-8")
    block = content.split("WITH reference_subjects", 1)[1].split("INSERT INTO subjects", 1)[0]
    types = re.findall(r"\('[^']+@local\.invalid', '[^']*', '([a-z_]+)'", block)

    assert len(types) >= 30
    assert set(types) <= VALID_TYPES


def test_dehavi_and_public_reference_subject_types_are_valid() -> None:
    dehavi = (DATABASE_DIR / "seed_dehavi_demo.sql").read_text(encoding="utf-8")
    reference = (DATABASE_DIR / "seed_public_reference.sql").read_text(encoding="utf-8")

    dehavi_type = re.search(r"'Công ty TNHH Cà phê Hân Vinh', '([a-z_]+)'", dehavi)
    reference_type = re.search(r"reference_subjects\.name,\s*'([a-z_]+)'", reference)

    assert dehavi_type and dehavi_type.group(1) in VALID_TYPES
    assert reference_type and reference_type.group(1) in VALID_TYPES
