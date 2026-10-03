# Cổng thông tin OCOP và bản đồ số du lịch nông nghiệp Lâm Đồng

Đồ án chuyên ngành: **Xây dựng Cổng thông tin quảng bá nông sản OCOP và bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng**.

Mốc: báo cáo tiến độ đợt 2 ngày **15/10/2026**, hạn nộp đồ án **15/11/2026**.
Kế hoạch chi tiết và tự đánh giá tiến độ: [`docs/KE_HOACH_HOAN_THANH_DO_AN.md`](docs/KE_HOACH_HOAN_THANH_DO_AN.md).

---

## 1. Chức năng hiện có

✅ đã xong · 🟡 làm một phần · ⬜ chưa làm (xem kế hoạch để biết tuần thực hiện).

**Người dùng, khách du lịch**

- ✅ Trang chủ: ảnh thật, tìm kiếm sản phẩm hoặc điểm du lịch, bản đồ xem trước, nhóm sản phẩm, sản phẩm nổi bật.
- ✅ Danh sách sản phẩm OCOP: tìm kiếm, lọc theo nhóm, hạng sao, địa bàn; chi tiết sản phẩm kèm điểm du lịch liên quan.
- ✅ Danh sách và chi tiết điểm du lịch nông nghiệp.
- ✅ Bản đồ số: gom cụm điểm, lọc, định vị người dùng, tìm điểm gần nhất (PostGIS), gợi ý tuyến đường (OSRM).
- ✅ Tin tức lấy từ RSS của cổng OCOP tỉnh.
- ✅ Đăng ký, đăng nhập (JWT), cập nhật hồ sơ; đăng ký trở thành chủ thể.
- ⬜ Đánh giá sản phẩm, điểm du lịch.

**Chủ thể OCOP (hợp tác xã, doanh nghiệp, hộ sản xuất)**

- ✅ Quản lý sản phẩm: bản nháp, gửi duyệt, yêu cầu sửa hoặc ngừng hiển thị sau khi duyệt, ảnh, giấy chứng nhận.
- ✅ Khai báo điểm du lịch: bản nháp, lấy vị trí bằng ghim bản đồ / GPS / tọa độ / link Google Maps, ảnh, gắn sản phẩm OCOP, gửi duyệt, yêu cầu cập nhật hoặc ngừng hiển thị.
- 🟡 Cập nhật thông tin đơn vị: hiện sửa bằng cách gửi lại hồ sơ.

**Quản trị viên**

- ✅ Tổng quan: hàng đợi việc cần xử lý, số liệu chính, thống kê và biểu đồ (Chart.js).
- ✅ Kiểm duyệt sản phẩm, yêu cầu sửa sản phẩm, nguồn chứng cứ công nhận OCOP.
- ✅ Duyệt hồ sơ đăng ký chủ thể.
- ✅ Duyệt điểm du lịch: kiểm tra vị trí trong tỉnh, cảnh báo trùng điểm trong 200 m, chỉnh ghim khi duyệt, so sánh và duyệt yêu cầu cập nhật.
- ⬜ Quản lý danh mục, quản lý người dùng, kiểm duyệt đánh giá.

Giao diện dùng bộ design token chung (bảng màu "Sương sớm & dã quỳ", font Be Vietnam Pro) và đạt WCAG 2.2 AA trên các trang đã làm mới.

## 2. Công nghệ

| Phần | Công nghệ |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, JWT, pytest |
| Frontend | Vue 3, TypeScript, Vite, Vue Router, Axios, Bootstrap 5, Leaflet + markercluster, Chart.js, Vitest |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Dịch vụ ngoài | Ảnh nền OpenStreetMap, định tuyến OSRM, RSS cổng OCOP Lâm Đồng |
| Môi trường | Docker Compose (postgres, pgadmin, backend, frontend) |

## 3. Cấu trúc thư mục

```text
backend/     API FastAPI: app/api/routes (route), app/models (model), app/schemas, tests/
frontend/    Giao diện Vue: src/views (trang), src/components, src/services (gọi API), src/styles (token)
database/    schema.sql, migrations/00x_*.sql, file seed, ERD.md, pgadmin/servers.json
data/        Dữ liệu gốc: danh sách OCOP, điểm du lịch (CSV)
docs/        Tài liệu: API, dữ liệu, quy trình kiểm duyệt, audit giao diện, kế hoạch, Postman
tools/       Script sinh seed từ dữ liệu gốc, kiểm tra database
scripts/     verify-mvp.ps1 (kiểm tra nhanh toàn hệ thống)
CLAUDE.md    Quy tắc làm việc của nhóm khi dùng Claude
```

## 4. Chạy dự án

Chỉ cần Git và Docker Desktop (đang chạy).

1. Sao chép `.env.example` thành `.env`, thay mọi giá trị `change-me`. Không commit `.env`.
2. Khởi động:

   ```powershell
   docker compose up -d --build
   docker compose ps
   ```

3. Mở:

   | Dịch vụ | Địa chỉ |
   |---|---|
   | Trang web | http://localhost:5173 |
   | API và Swagger | http://localhost:8000/docs |
   | pgAdmin | http://localhost:5050 |

   pgAdmin đăng nhập bằng `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD` trong `.env`; server "LamDong PostgreSQL" có sẵn, mật khẩu kết nối là `POSTGRES_PASSWORD`.

Lần đầu (volume PostgreSQL trống), Docker tự chạy `database/schema.sql`, `seed_dev.sql` và `seed_tourism_locations.sql` (9 điểm du lịch). Nạp thêm dữ liệu sản phẩm và tài khoản demo:

```powershell
Get-Content .\database\seed_public_reference.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Get-Content .\database\seed_ocop_2025_2026.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Get-Content .\database\seed_product_workflow.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Tài khoản demo (chỉ dùng khi phát triển, mật khẩu `DemoOCOP@2026`):

| Tài khoản | Vai trò |
|---|---|
| `admin.ocop.demo@example.com` | Quản trị viên |
| `chuthe.ocop.demo@example.com` | Chủ thể đã duyệt, có sản phẩm ở đủ các trạng thái |
| `ungvien.ocop.demo@example.com` | Người dùng đang chờ duyệt hồ sơ chủ thể |

Chi tiết dữ liệu kiểm thử: [`docs/DU_LIEU_KIEM_THU_SAN_PHAM.md`](docs/DU_LIEU_KIEM_THU_SAN_PHAM.md).

Lệnh thường dùng:

```powershell
docker compose logs -f backend        # xem log (backend, frontend, postgres)
docker compose restart frontend       # sau khi package.json đổi: container tự npm install khi khởi động
docker compose down                   # dừng, giữ nguyên dữ liệu
```

Không dùng `docker compose down -v`: lệnh này xóa cả database và ảnh đã tải lên (khi `IMAGE_STORAGE=local`).

### Lưu ảnh: cục bộ hoặc Cloudinary

Ảnh sản phẩm và ảnh điểm du lịch do chủ thể tải lên được lưu theo biến `IMAGE_STORAGE` trong `.env`:

- `local` (mặc định): lưu trong thư mục `backend/uploads`. Không cần cấu hình gì, dùng khi phát triển và chạy kiểm thử.
- `cloudinary`: tải lên Cloudinary. Cần tài khoản Cloudinary (gói Free, không cần thẻ) và điền `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`. Thiếu một biến thì backend báo lỗi khi khởi động. Sau khi đổi `.env`, chạy `docker compose up -d backend` để nạp lại.

File giấy chứng nhận sản phẩm luôn lưu cục bộ và chỉ tải được qua API có kiểm tra quyền. Ảnh đã lưu cục bộ trước đó vẫn dùng được; chuyển chúng lên Cloudinary bằng script riêng (sẽ có ở bước sau).

## 5. Database và migration

- Database mới tạo từ `database/schema.sql` luôn là phiên bản mới nhất, không cần chạy migration.
- Database đã có dữ liệu: sau mỗi lần `git pull`, chạy các migration chưa chạy theo thứ tự (từ file đầu tiên chưa chạy tới 011). Mọi migration chạy lặp lại an toàn. Ví dụ:

  ```powershell
  Get-Content .\database\migrations\009_tourism_location_submissions.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
  Get-Content .\database\migrations\010_normalize_constraint_names.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
  Get-Content .\database\migrations\011_tourism_location_drafts.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
  ```

| Migration | Nội dung |
|---|---|
| 001_hardening | Ràng buộc, index, trigger cập nhật thời gian |
| 002_subject_moderation | Kiểm duyệt hồ sơ chủ thể |
| 003_sync_product_rating | Cột điểm đánh giá sản phẩm |
| 004_product_moderation | Quy trình kiểm duyệt sản phẩm, yêu cầu sửa |
| 005_add_product_sources | Nguồn chứng cứ công nhận OCOP |
| 006_simplify_subject_product_flow | Bản nháp sản phẩm, giấy chứng nhận riêng tư |
| 007_hide_demo_products | Ẩn dữ liệu demo khỏi trang công khai |
| 008_tourism_location_map | Thông tin điểm du lịch cho bản đồ số |
| 009_tourism_location_submissions | Chủ thể khai báo điểm du lịch, admin duyệt, yêu cầu cập nhật |
| 010_normalize_constraint_names | Chuẩn hóa tên ràng buộc để database nâng cấp giống hệt database tạo mới |
| 011_tourism_location_drafts | Bản nháp điểm du lịch được thiếu vị trí/địa chỉ; trạng thái ngừng hiển thị (archived) |

**Kiểm tra database khớp repo:** mở `tools/kiem-tra-database.sql` trong Query Tool của pgAdmin và chạy.
Kết quả rỗng là khớp; dòng `thieu_so_voi_repo` là migration chưa chạy; dòng `thua_ngoai_repo` là thay đổi làm thẳng trên database mà repo không có.

**Quy tắc:** mọi thay đổi database phải là một migration mới trong repo, cập nhật cùng lúc `schema.sql`, model và `tools/kiem-tra-database.sql` (sinh lại bằng `tools/sinh_kiem_tra_database.py`). Không sửa thẳng database bằng pgAdmin hay công cụ khác.

## 6. Kiểm thử

```powershell
docker compose exec backend python -m pytest -q      # backend: 138 test
docker compose exec frontend npm test                # frontend: 111 test
docker compose exec frontend npm run type-check
docker compose exec frontend npm run build
.\scripts\verify-mvp.ps1                             # kiểm tra nhanh toàn hệ thống, chỉ đọc dữ liệu
```

Pull Request phải qua đủ test, type-check và build. Thay đổi giao diện kiểm tra thêm trợ năng (axe, WCAG 2.2 AA) và không tràn ngang ở màn 375px.

## 7. API

Tài liệu đầy đủ ở Swagger (`/docs`) và [`docs/API.md`](docs/API.md). Các nhóm endpoint dưới `/api/v1`:

| Nhóm | Endpoint chính | Quyền |
|---|---|---|
| Tài khoản | `POST /auth/register`, `POST /auth/login`, `GET/PATCH /auth/me` | Công khai / đăng nhập |
| Công khai | `GET /categories`, `/products`, `/products/{slug}`, `/locations`, `/locations/{slug}`, `/news` | Công khai |
| Bản đồ | `GET /map/locations` (GeoJSON), `/map/nearby`, `/map/route` | Công khai |
| Hồ sơ chủ thể | `POST /subject-applications`, `GET/PUT /subject-applications/me` | Người dùng |
| Chủ thể | `/subject/products` (CRUD, `submit`, `change-requests`, `deletion-requests`), `/subject/product-images`, `/subject/product-certificates`, `/subject/product-change-requests` | Chủ thể |
| Chủ thể – điểm du lịch | `/subject/locations` (CRUD, `submit`, `position-check`, `parse-coordinates`, `change-requests`, `deletion-requests`), `/subject/location-images`, `/subject/location-change-requests` | Chủ thể |
| Quản trị | `/admin/dashboard`, `/admin/statistics`, `/admin/products` (duyệt, chứng cứ), `/admin/product-change-requests`, `/admin/subject-applications`, `/admin/data-sources`, `/admin/locations` (duyệt, chỉnh ghim), `/admin/location-change-requests` | Admin |

Backend kiểm tra vai trò trong database ở mỗi lần gọi; sửa JWT hay hiện nút trên giao diện không làm tăng quyền.

## 8. Quy trình làm việc nhóm

- Mỗi chức năng một nhánh `2312682_HaLuyen_<TenChucNang>` (hoặc tên theo người làm), tạo từ `main` mới nhất.
- Không sửa trực tiếp `main`. Code lên `main` qua Pull Request, có người review.
- Commit dạng `loại(phạm vi): mô tả tiếng Việt`, ví dụ `feat(api): …`, `fix(ui): …`, `docs: …`. Backend và giao diện là các commit riêng.
- Không commit `.env`, file sao lưu `.dump`, `node_modules`, khóa Cloudinary.
- Khi làm cùng Claude: quy tắc chi tiết trong [`CLAUDE.md`](CLAUDE.md).

## 9. Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [`docs/KE_HOACH_HOAN_THANH_DO_AN.md`](docs/KE_HOACH_HOAN_THANH_DO_AN.md) | Kế hoạch tới khi nộp, tự đánh giá tiến độ, phân công |
| [`database/ERD.md`](database/ERD.md) | Sơ đồ quan hệ dữ liệu |
| [`docs/API.md`](docs/API.md), [`docs/postman/`](docs/postman/) | Hợp đồng API, bộ Postman |
| [`docs/QUY_TRINH_KIEM_DUYET_SAN_PHAM.md`](docs/QUY_TRINH_KIEM_DUYET_SAN_PHAM.md) | Quy trình kiểm duyệt sản phẩm |
| [`docs/DU_LIEU_THAM_KHAO_CONG_KHAI.md`](docs/DU_LIEU_THAM_KHAO_CONG_KHAI.md) | Nguồn dữ liệu sản phẩm OCOP |
| [`docs/DU_LIEU_DIEM_DU_LICH.md`](docs/DU_LIEU_DIEM_DU_LICH.md) | Dữ liệu điểm du lịch, bản đồ, định tuyến |
| [`docs/DU_LIEU_KIEM_THU_SAN_PHAM.md`](docs/DU_LIEU_KIEM_THU_SAN_PHAM.md) | Tài khoản và dữ liệu kiểm thử |
| [`docs/ui-audit.md`](docs/ui-audit.md) | Đánh giá và nhật ký cải thiện giao diện |
| `docs/*.docx` | Phân tích yêu cầu, phụ lục nguồn dữ liệu, hướng dẫn nhóm |
