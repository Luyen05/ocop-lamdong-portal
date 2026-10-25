"""Sinh docs/API.md và docs/postman/OCOP-Lam-Dong.postman_collection.json từ OpenAPI của backend.

Chạy (từ thư mục backend, để import được app):

    cd backend
    python ../tools/sinh_tai_lieu_api.py

Không cần database. Chạy lại mỗi khi thêm, sửa hoặc xóa endpoint; kết quả ổn định (sắp xếp cố định).
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("JWT_SECRET_KEY", "api-doc-generation-only-secret-0123456789")

from app.main import app  # noqa: E402

PREFIX = "/api/v1"

TAG_TITLES = {
    "System": "Hệ thống",
    "Authentication": "Tài khoản và xác thực",
    "Categories": "Danh mục (công khai)",
    "Products": "Sản phẩm (công khai)",
    "Locations": "Điểm du lịch (công khai)",
    "Map": "Bản đồ số",
    "News": "Tin tức",
    "Reviews": "Đánh giá",
    "Subject applications": "Hồ sơ đăng ký chủ thể",
    "Subject": "Khu chủ thể",
    "Admin": "Quản trị",
}
TAG_ORDER = list(TAG_TITLES)

# Mô tả tiếng Việt cho endpoint chưa có docstring (khóa: method + đường dẫn không có /api/v1).
DESCRIPTIONS = {
    ("GET", "/health"): "Kiểm tra API đang chạy.",
    ("GET", "/health/database"): "Kiểm tra kết nối database.",
    ("POST", "/auth/register"): "Đăng ký tài khoản người dùng bằng email và mật khẩu.",
    ("POST", "/auth/login"): "Đăng nhập, nhận access token (JWT). Sai quá nhiều lần trả 429.",
    ("GET", "/auth/me"): "Thông tin tài khoản đang đăng nhập (kèm has_password, social_providers).",
    ("PATCH", "/auth/me"): "Sửa họ tên, số điện thoại, ảnh đại diện.",
    ("POST", "/auth/social/{provider}/authorize"): "Tạo địa chỉ trang đăng nhập Google/Facebook (state do frontend tạo; Google cần PKCE).",
    ("POST", "/auth/social/{provider}/callback"): "Hoàn tất đăng nhập Google/Facebook, nhận JWT.",
    ("POST", "/subject-applications"): "Gửi hồ sơ đăng ký trở thành chủ thể OCOP.",
    ("GET", "/subject-applications/me"): "Xem hồ sơ chủ thể của tôi và kết quả duyệt.",
    ("PUT", "/subject-applications/me"): "Sửa và gửi lại hồ sơ bị từ chối.",
    ("GET", "/admin/dashboard"): "Số liệu tổng quan và hàng đợi việc cần duyệt.",
    ("GET", "/admin/subject-applications"): "Danh sách hồ sơ chủ thể (lọc trạng thái, tìm kiếm, phân trang).",
    ("PATCH", "/admin/subject-applications/{application_id}/moderation"): "Duyệt hoặc từ chối (kèm lý do) hồ sơ chủ thể.",
    ("GET", "/admin/products"): "Danh sách sản phẩm để kiểm duyệt.",
    ("GET", "/admin/products/{product_id}"): "Chi tiết sản phẩm để kiểm duyệt.",
    ("PATCH", "/admin/products/{product_id}/moderation"): "Duyệt, yêu cầu bổ sung hoặc từ chối sản phẩm.",
    ("GET", "/admin/products/{product_id}/certificate"): "Tải giấy chứng nhận OCOP của sản phẩm (file riêng tư).",
    ("GET", "/admin/products/{product_id}/evidence"): "Các nguồn chứng cứ gắn với sản phẩm.",
    ("POST", "/admin/products/{product_id}/evidence"): "Gắn nguồn chứng cứ (quyết định công nhận, trang thông tin) cho sản phẩm.",
    ("PATCH", "/admin/products/{product_id}/evidence/{source_id}/{evidence_role}"): "Sửa liên kết nguồn chứng cứ.",
    ("DELETE", "/admin/products/{product_id}/evidence/{source_id}/{evidence_role}"): "Bỏ liên kết nguồn chứng cứ.",
    ("GET", "/admin/product-change-requests"): "Danh sách yêu cầu sửa/ngừng hiển thị sản phẩm.",
    ("GET", "/admin/product-change-requests/{request_id}"): "Chi tiết yêu cầu, so sánh với sản phẩm hiện tại.",
    ("PATCH", "/admin/product-change-requests/{request_id}/moderation"): "Duyệt, yêu cầu bổ sung hoặc từ chối yêu cầu thay đổi sản phẩm.",
    ("GET", "/admin/data-sources"): "Danh sách nguồn dữ liệu (văn bản, trang thông tin).",
    ("POST", "/admin/data-sources"): "Thêm nguồn dữ liệu.",
    ("PATCH", "/admin/data-sources/{source_id}"): "Sửa nguồn dữ liệu.",
    ("GET", "/admin/locations"): "Danh sách điểm du lịch để kiểm duyệt.",
    ("GET", "/admin/locations/{location_id}"): "Chi tiết điểm du lịch để kiểm duyệt.",
    ("PATCH", "/admin/locations/{location_id}/moderation"): "Duyệt (có thể chỉnh ghim), yêu cầu bổ sung hoặc từ chối điểm du lịch.",
    ("GET", "/admin/location-change-requests"): "Danh sách yêu cầu cập nhật/ngừng hiển thị điểm du lịch.",
    ("GET", "/admin/location-change-requests/{request_id}"): "Chi tiết yêu cầu cập nhật điểm du lịch.",
    ("PATCH", "/admin/location-change-requests/{request_id}/moderation"): "Duyệt hoặc từ chối yêu cầu cập nhật điểm du lịch.",
    ("GET", "/admin/users"): "Danh sách tài khoản (tìm theo email/tên, lọc vai trò, trạng thái).",
    ("PATCH", "/admin/users/{user_id}/status"): "Khóa hoặc mở khóa tài khoản.",
    ("GET", "/admin/categories"): "Danh sách danh mục, gồm cả danh mục ẩn và số sản phẩm.",
    ("POST", "/admin/categories"): "Thêm danh mục.",
    ("PATCH", "/admin/categories/{category_id}"): "Sửa, ẩn/hiện, đổi thứ tự danh mục.",
    ("DELETE", "/admin/categories/{category_id}"): "Xóa danh mục chưa có sản phẩm.",
    ("GET", "/admin/reviews"): "Danh sách đánh giá để kiểm duyệt.",
    ("PATCH", "/admin/reviews/{review_id}/moderation"): "Duyệt hoặc từ chối (kèm lý do) đánh giá.",
    ("GET", "/subject/profile"): "Thông tin đơn vị của chủ thể.",
    ("PATCH", "/subject/profile"): "Sửa thông tin liên hệ của đơn vị (tên, loại, mã số thuế do admin sửa).",
    ("GET", "/subject/products"): "Sản phẩm của tôi (mọi trạng thái).",
    ("POST", "/subject/products"): "Tạo bản nháp sản phẩm.",
    ("GET", "/subject/products/{product_id}"): "Chi tiết sản phẩm của tôi.",
    ("PUT", "/subject/products/{product_id}"): "Lưu toàn bộ bản nháp sản phẩm.",
    ("PATCH", "/subject/products/{product_id}"): "Lưu một phần bản nháp sản phẩm.",
    ("DELETE", "/subject/products/{product_id}"): "Xóa sản phẩm chưa được duyệt.",
    ("POST", "/subject/products/{product_id}/submit"): "Gửi sản phẩm để quản trị viên duyệt.",
    ("POST", "/subject/products/{product_id}/change-requests"): "Gửi yêu cầu sửa sản phẩm đã duyệt.",
    ("POST", "/subject/products/{product_id}/deletion-requests"): "Gửi yêu cầu ngừng hiển thị sản phẩm đã duyệt.",
    ("GET", "/subject/product-change-requests"): "Yêu cầu thay đổi sản phẩm của tôi.",
    ("GET", "/subject/product-change-requests/{request_id}"): "Chi tiết yêu cầu thay đổi sản phẩm.",
    ("PUT", "/subject/product-change-requests/{request_id}"): "Sửa và gửi lại yêu cầu cần bổ sung.",
    ("POST", "/subject/product-change-requests/{request_id}/cancel"): "Hủy yêu cầu thay đổi đang chờ.",
    ("POST", "/subject/product-images"): "Tải ảnh sản phẩm (JPG, PNG, WebP; tối đa 5 MB).",
    ("DELETE", "/subject/product-images/{file_name}"): "Xóa ảnh vừa tải chưa gắn vào sản phẩm.",
    ("POST", "/subject/product-certificates"): "Tải giấy chứng nhận OCOP (PDF, JPG, PNG; tối đa 10 MB; riêng tư).",
    ("DELETE", "/subject/product-certificates/{file_name}"): "Xóa giấy chứng nhận vừa tải chưa gắn vào sản phẩm.",
    ("GET", "/subject/product-certificates/products/{product_id}"): "Tải giấy chứng nhận của sản phẩm của tôi.",
    ("GET", "/subject/locations"): "Điểm du lịch của tôi.",
    ("POST", "/subject/locations"): "Tạo bản nháp điểm du lịch.",
    ("GET", "/subject/locations/{location_id}"): "Chi tiết điểm du lịch của tôi.",
    ("PATCH", "/subject/locations/{location_id}"): "Lưu bản nháp điểm du lịch.",
    ("DELETE", "/subject/locations/{location_id}"): "Xóa điểm du lịch chưa được duyệt.",
    ("POST", "/subject/locations/{location_id}/submit"): "Gửi điểm du lịch để quản trị viên duyệt.",
    ("POST", "/subject/locations/{location_id}/change-requests"): "Gửi yêu cầu cập nhật điểm đã duyệt.",
    ("POST", "/subject/locations/{location_id}/deletion-requests"): "Gửi yêu cầu ngừng hiển thị điểm đã duyệt.",
    ("GET", "/subject/location-change-requests"): "Yêu cầu cập nhật điểm du lịch của tôi.",
    ("GET", "/subject/location-change-requests/{request_id}"): "Chi tiết yêu cầu cập nhật điểm du lịch.",
    ("PUT", "/subject/location-change-requests/{request_id}"): "Sửa và gửi lại yêu cầu cần bổ sung.",
    ("POST", "/subject/location-change-requests/{request_id}/cancel"): "Hủy yêu cầu cập nhật đang chờ.",
    ("POST", "/subject/location-images"): "Tải ảnh điểm du lịch.",
    ("DELETE", "/subject/location-images/{file_name}"): "Xóa ảnh điểm du lịch chưa gắn vào điểm.",
    ("GET", "/categories"): "Danh mục đang hiển thị, sắp theo thứ tự.",
    ("GET", "/categories/{slug}"): "Chi tiết danh mục.",
    ("GET", "/news"): "Tin tức lấy từ RSS cổng OCOP tỉnh (có bộ nhớ đệm).",
    ("GET", "/products"): "Danh sách sản phẩm công khai: tìm kiếm, lọc nhóm, hạng sao, địa bàn, giá; sắp xếp; phân trang.",
    ("GET", "/products/filter-options"): "Giá trị cho bộ lọc sản phẩm (địa bàn).",
    ("GET", "/products/{slug}"): "Chi tiết sản phẩm công khai (tăng lượt xem).",
    ("GET", "/locations"): "Danh sách điểm du lịch công khai.",
    ("GET", "/locations/filter-options"): "Giá trị cho bộ lọc điểm du lịch (loại hình, địa bàn).",
    ("GET", "/locations/{slug}"): "Chi tiết điểm du lịch công khai (tăng lượt xem).",
    ("GET", "/products/{product_id}/reviews"): "Đánh giá đã duyệt của sản phẩm, kèm tóm tắt điểm.",
    ("POST", "/products/{product_id}/reviews"): "Viết đánh giá sản phẩm (chờ duyệt).",
    ("GET", "/locations/{location_id}/reviews"): "Đánh giá đã duyệt của điểm du lịch, kèm tóm tắt điểm.",
    ("POST", "/locations/{location_id}/reviews"): "Viết đánh giá điểm du lịch (chờ duyệt).",
    ("PATCH", "/reviews/{review_id}"): "Sửa đánh giá của tôi (quay về chờ duyệt).",
    ("DELETE", "/reviews/{review_id}"): "Xóa đánh giá của tôi.",
}

ERROR_NOTES = {
    "VALIDATION_ERROR": "Dữ liệu gửi lên không hợp lệ; `details` liệt kê từng trường.",
    "INVALID_TOKEN": "Thiếu, sai hoặc hết hạn access token (401).",
    "INVALID_CREDENTIALS": "Sai email hoặc mật khẩu.",
    "TOO_MANY_LOGIN_ATTEMPTS": "Sai mật khẩu quá nhiều lần; xem header `Retry-After` (429).",
    "ACCOUNT_INACTIVE": "Tài khoản đã bị khóa (403); frontend kết thúc phiên.",
    "INSUFFICIENT_PERMISSIONS": "Vai trò không có quyền (403).",
    "APPROVED_SUBJECT_REQUIRED": "Cần hồ sơ chủ thể đã được duyệt.",
    "DATABASE_UNAVAILABLE": "Không kết nối được database (503).",
    "DATABASE_SCHEMA_OUTDATED": "Database chưa chạy migration mới nhất (503).",
    "INTERNAL_ERROR": "Lỗi không lường trước (500).",
    "SOCIAL_EMAIL_EXISTS": "Email Google/Facebook đã có tài khoản: đăng nhập bằng mật khẩu rồi liên kết.",
    "CATEGORY_HIDDEN": "Không tạo sản phẩm mới vào danh mục đang ẩn.",
    "CATEGORY_IN_USE": "Không xóa danh mục còn sản phẩm.",
    "LAST_ACTIVE_ADMIN": "Không khóa quản trị viên còn hoạt động cuối cùng.",
    "CANNOT_LOCK_SELF": "Không tự khóa tài khoản của mình.",
    "OWN_TARGET_REVIEW_FORBIDDEN": "Chủ thể không tự đánh giá sản phẩm/điểm của đơn vị mình.",
    "REVIEW_ALREADY_EXISTS": "Mỗi người một đánh giá cho mỗi sản phẩm/điểm.",
    "PRODUCT_VERSION_CONFLICT": "Dữ liệu đã bị người khác sửa; tải lại rồi thao tác lại.",
    "PRODUCT_SUBMISSION_INCOMPLETE": "Thiếu thông tin bắt buộc để gửi duyệt (`details` liệt kê).",
    "LOCATION_OUTSIDE_LAM_DONG": "Vị trí nằm ngoài tỉnh Lâm Đồng.",
    "ROUTING_UNAVAILABLE": "Dịch vụ chỉ đường không phản hồi (503).",
    "NEWS_SOURCE_UNAVAILABLE": "Không tải được RSS và chưa có bản lưu (503).",
}

NOT_ERROR_CODES = {
    "CASCADE", "RESTRICT", "NFKD", "OSRM", "WEBP", "RIFF", "TEXT", "S256", "INVALID_RESPONSE",
    "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET", "PRODUCT_IMAGE", "LOCATION_IMAGE",
    "HTTP_ERROR",
}

ERROR_GROUPS = [
    ("Chung", ("VALIDATION", "INTERNAL", "DATABASE", "INVALID_TOKEN", "INSUFFICIENT", "ROLE_")),
    ("Tài khoản", ("INVALID_CRED", "TOO_MANY", "ACCOUNT", "EMAIL", "PASSWORD", "CURRENT_PASSWORD", "INVALID_CURRENT",
                   "USER", "LAST_ACTIVE", "CANNOT_LOCK", "SOCIAL")),
    ("Chủ thể", ("SUBJECT", "APPROVED_SUBJECT", "INACTIVE_APPLICANT")),
    ("Sản phẩm, chứng nhận, ảnh", ("PRODUCT", "CERTIFICATE", "INVALID_CERTIFICATE", "IMAGE", "INVALID_IMAGE",
                                   "ACTIVE_PRODUCT", "APPROVED_PRODUCT", "DELETION", "PROPOSED_PRODUCT",
                                   "INVALID_PRICE", "DATA_SOURCE", "REJECTION")),
    ("Điểm du lịch, bản đồ", ("LOCATION", "ACTIVE_LOCATION", "APPROVED_LOCATION", "PROPOSED_LOCATION", "INVALID_COORD",
                              "MAPS_LINK", "SHORT_MAPS", "ORIGIN", "ROUTE", "ROUTING")),
    ("Danh mục, đánh giá, tin tức", ("CATEGORY", "REVIEW", "OWN_TARGET", "ADMIN_CANNOT", "NEWS")),
]


def collect_error_codes() -> list[str]:
    pattern = re.compile(r'"([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+|[A-Z]{4,})"')
    codes: set[str] = set()
    for path in (ROOT / "backend" / "app").rglob("*.py"):
        for code in pattern.findall(path.read_text(encoding="utf-8")):
            if code not in NOT_ERROR_CODES and "_" in code:
                codes.add(code)
    return sorted(codes)


def group_of(code: str) -> str:
    for title, prefixes in ERROR_GROUPS:
        if code.startswith(prefixes):
            return title
    return "Khác"


def access_of(path: str, op: dict) -> str:
    short = path.removeprefix(PREFIX)
    if short.startswith("/admin"):
        return "Quản trị viên"
    if short.startswith("/subject/"):
        return "Chủ thể đã duyệt"
    if op.get("security"):
        return "Đã đăng nhập"
    return "Công khai"


def operations():
    spec = app.openapi()
    items = []
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            tag = (op.get("tags") or ["System"])[0]
            items.append((tag, path, method.upper(), op))
    order = {tag: index for index, tag in enumerate(TAG_ORDER)}
    items.sort(key=lambda item: (order.get(item[0], 99), item[1], ["GET", "POST", "PUT", "PATCH", "DELETE"].index(item[2])))
    return spec, items


def describe(method: str, path: str, op: dict) -> str:
    short = path.removeprefix(PREFIX)
    text = (op.get("description") or "").strip().split("\n")[0].strip()
    return DESCRIPTIONS.get((method, short)) or text or op.get("summary", "")


HEADER = """# Tài liệu REST API

> Tệp này được sinh tự động bằng `tools/sinh_tai_lieu_api.py` từ OpenAPI của backend. Đừng sửa tay phần
> danh sách endpoint: sửa docstring hoặc bảng mô tả trong script rồi chạy lại.

- **Base URL:** `/api/v1` (môi trường phát triển: `http://localhost:8000/api/v1`).
- **Tài liệu tương tác:** Swagger UI tại `http://localhost:8000/docs`, ReDoc tại `/redoc`, OpenAPI JSON tại `/openapi.json`.
- **Postman:** `docs/postman/OCOP-Lam-Dong.postman_collection.json` (request `POST /auth/login` tự lưu token vào biến `token`).

## Quy ước

| Nội dung | Quy ước |
|---|---|
| Xác thực | `Authorization: Bearer <access_token>`; token lấy từ `POST /auth/login` hoặc đăng nhập Google/Facebook, hết hạn sau `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (mặc định 60 phút). |
| Phân quyền | `/admin/*`: quản trị viên. `/subject/*`: chủ thể đã được duyệt. Mọi request kiểm tra lại tài khoản còn hoạt động. |
| Lỗi | `{"code": "MA_LOI", "message": "Thông báo tiếng Việt", "details": ...}`. |
| Phân trang | Query `page` (từ 1), `page_size`; kết quả `{"items": [...], "page", "page_size", "total"}`. |
| Tọa độ | Đầu vào `latitude`, `longitude` (WGS84); GeoJSON đầu ra theo thứ tự `[longitude, latitude]`. |
| Thời gian | ISO 8601 có múi giờ; ngày dạng `YYYY-MM-DD`. |
| Dữ liệu công khai | Chỉ sản phẩm, điểm du lịch, đánh giá đã duyệt và đủ điều kiện hiển thị (xem `docs/NGHIEP_VU.md`). |
"""


def build_markdown(items, codes) -> str:
    lines = [HEADER]
    lines.append("## Mã lỗi\n")
    lines.append("Mã lỗi hay gặp:\n")
    lines.append("| Mã | Ý nghĩa |\n|---|---|")
    for code, note in ERROR_NOTES.items():
        lines.append(f"| `{code}` | {note} |")
    grouped: dict[str, list[str]] = defaultdict(list)
    for code in codes:
        grouped[group_of(code)].append(code)
    lines.append("\nToàn bộ mã lỗi theo nhóm (thông báo chi tiết nằm trong trường `message`):\n")
    for title, _ in ERROR_GROUPS + [("Khác", ())]:
        if grouped.get(title):
            lines.append(f"- **{title}:** " + ", ".join(f"`{code}`" for code in grouped[title]))
    lines.append(f"\n## Danh sách endpoint ({len(items)})\n")
    by_tag: dict[str, list] = defaultdict(list)
    for tag, path, method, op in items:
        by_tag[tag].append((path, method, op))
    for tag in sorted(by_tag, key=lambda t: TAG_ORDER.index(t) if t in TAG_ORDER else 99):
        lines.append(f"### {TAG_TITLES.get(tag, tag)}\n")
        lines.append("| Method | Đường dẫn | Quyền | Mô tả |\n|---|---|---|---|")
        for path, method, op in by_tag[tag]:
            short = path.removeprefix(PREFIX)
            lines.append(f"| `{method}` | `{short}` | {access_of(path, op)} | {describe(method, path, op)} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def example_from_schema(schema: dict, components: dict, depth: int = 0):
    if depth > 4:
        return None
    if "$ref" in schema:
        return example_from_schema(components[schema["$ref"].split("/")[-1]], components, depth + 1)
    for key in ("anyOf", "oneOf", "allOf"):
        if key in schema:
            options = [item for item in schema[key] if item.get("type") != "null"]
            return example_from_schema(options[0], components, depth + 1) if options else None
    if "example" in schema:
        return schema["example"]
    if "default" in schema and schema["default"] is not None:
        return schema["default"]
    if "enum" in schema:
        return schema["enum"][0]
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})
        keys = [k for k in properties if k in required] or list(properties)[:6]
        return {key: example_from_schema(properties[key], components, depth + 1) for key in keys}
    if kind == "array":
        item = example_from_schema(schema.get("items", {}), components, depth + 1)
        return [item] if item is not None else []
    if kind == "integer":
        return max(1, schema.get("minimum", 1))
    if kind == "number":
        return 0
    if kind == "boolean":
        return True
    if kind == "string":
        fmt = schema.get("format")
        if fmt == "email":
            return "nguoidung@example.com"
        if fmt == "date":
            return "2026-01-01"
        if fmt == "date-time":
            return "2026-01-01T00:00:00+07:00"
        if fmt in ("uri", "url"):
            return "https://example.com"
        if fmt == "password":
            return "MatKhauAnToan123"
        return "chuoi"
    return None


def build_postman(spec, items) -> dict:
    components = spec.get("components", {}).get("schemas", {})
    folders: dict[str, list] = defaultdict(list)
    for tag, path, method, op in items:
        short = path.removeprefix(PREFIX)
        segments = [f":{seg[1:-1]}" if seg.startswith("{") else seg for seg in short.strip("/").split("/")]
        query = [
            {"key": p["name"], "value": "", "disabled": not p.get("required", False)}
            for p in op.get("parameters", [])
            if p.get("in") == "query"
        ]
        variables = [
            {"key": p["name"], "value": "1"}
            for p in op.get("parameters", [])
            if p.get("in") == "path"
        ]
        raw = "{{baseUrl}}/" + "/".join(segments)
        request: dict = {
            "method": method,
            "header": [],
            "url": {"raw": raw, "host": ["{{baseUrl}}"], "path": segments, "query": query, "variable": variables},
            "description": describe(method, path, op),
        }
        if access_of(path, op) == "Công khai":
            request["auth"] = {"type": "noauth"}
        content = op.get("requestBody", {}).get("content", {})
        if "application/json" in content:
            body = example_from_schema(content["application/json"].get("schema", {}), components)
            request["header"].append({"key": "Content-Type", "value": "application/json"})
            request["body"] = {"mode": "raw", "raw": json.dumps(body, ensure_ascii=False, indent=2)}
        elif "multipart/form-data" in content:
            request["body"] = {"mode": "formdata", "formdata": [{"key": "file", "type": "file", "src": []}]}
        entry = {"name": f"{method} {short}", "request": request}
        if method == "POST" and short == "/auth/login":
            request["body"]["raw"] = json.dumps(
                {"email": "admin.ocop.demo@example.com", "password": "DemoOCOP@2026"}, ensure_ascii=False, indent=2
            )
            entry["event"] = [{
                "listen": "test",
                "script": {"type": "text/javascript", "exec": [
                    "if (pm.response.code === 200) {",
                    "  pm.collectionVariables.set('token', pm.response.json().access_token);",
                    "}",
                ]},
            }]
        folders[tag].append(entry)
    return {
        "info": {
            "name": "OCOP Lâm Đồng API",
            "description": "Sinh tự động bằng tools/sinh_tai_lieu_api.py. Chạy 'POST /auth/login' trước để lưu token.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {"type": "bearer", "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}]},
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000/api/v1"},
            {"key": "token", "value": ""},
        ],
        "item": [
            {"name": TAG_TITLES.get(tag, tag), "item": folders[tag]}
            for tag in sorted(folders, key=lambda t: TAG_ORDER.index(t) if t in TAG_ORDER else 99)
        ],
    }


def main() -> None:
    spec, items = operations()
    codes = collect_error_codes()
    (ROOT / "docs" / "API.md").write_text(build_markdown(items, codes), encoding="utf-8")
    postman = build_postman(spec, items)
    out = ROOT / "docs" / "postman" / "OCOP-Lam-Dong.postman_collection.json"
    out.write_text(json.dumps(postman, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(len(folder["item"]) for folder in postman["item"])
    print(f"docs/API.md: {len(items)} endpoint, {len(codes)} mã lỗi; Postman: {total} request.")


if __name__ == "__main__":
    main()
