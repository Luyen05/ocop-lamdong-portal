# Cổng thông tin OCOP và bản đồ số du lịch nông nghiệp Lâm Đồng

Đồ án chuyên ngành: **Xây dựng Cổng thông tin quảng bá nông sản OCOP và bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng**.

- Nhóm: Liêng Hót Ha Luyến (nhóm trưởng), Nguyễn Quốc Thái, Nguyễn Khiêm Thuận. GVHD: KS. La Quốc Thắng.
- Mốc: báo cáo tiến độ đợt 2 ngày **15/10/2026**, hạn nộp đồ án **15/11/2026**.
- Kế hoạch chi tiết và tự đánh giá tiến độ: [`docs/KE_HOACH_HOAN_THANH_DO_AN.md`](docs/KE_HOACH_HOAN_THANH_DO_AN.md).
- README cập nhật lần cuối: **07/10/2026** (theo `main` sau khi gộp PR #11).

---

## 1. Chức năng hiện có

✅ đã xong · 🟡 làm một phần · ⬜ chưa làm (xem kế hoạch để biết tuần thực hiện).

**Người dùng, khách du lịch**

- ✅ Trang chủ: ảnh thật, tìm kiếm sản phẩm hoặc điểm du lịch, bản đồ xem trước, nhóm sản phẩm, sản phẩm nổi bật.
- ✅ Danh sách sản phẩm OCOP: tìm kiếm, lọc theo nhóm, hạng sao, địa bàn; chi tiết sản phẩm kèm điểm du lịch liên quan.
- ✅ Tìm điểm trải nghiệm của một sản phẩm (`/san-pham/:slug/diem-trai-nghiem`).
- ✅ Danh sách và chi tiết điểm du lịch nông nghiệp.
- ✅ Bản đồ số: gom cụm điểm, lọc, định vị người dùng, tìm điểm gần nhất (PostGIS), gợi ý tuyến đường (OSRM).
- ✅ Tin tức lấy từ RSS của cổng OCOP tỉnh.
- ✅ Đăng ký, đăng nhập (JWT), cập nhật hồ sơ; đăng ký trở thành chủ thể.
- ⬜ Đánh giá sản phẩm, điểm du lịch.

Tìm kiếm hiện phân biệt dấu: gõ "dâu tây" sẽ tìm thấy, gõ "dau tay" thì không. Trang công khai chỉ hiện sản phẩm đã duyệt và có chứng nhận còn hạn hoặc nguồn công nhận (xem [`docs/QUY_TRINH_KIEM_DUYET_SAN_PHAM.md`](docs/QUY_TRINH_KIEM_DUYET_SAN_PHAM.md)).

**Chủ thể OCOP (hợp tác xã, doanh nghiệp, hộ sản xuất)**

- ✅ Quản lý sản phẩm: bản nháp, gửi duyệt, yêu cầu sửa hoặc ngừng hiển thị sau khi duyệt, ảnh, giấy chứng nhận.
- ✅ Khai báo điểm du lịch: bản nháp, lấy vị trí bằng ghim bản đồ / GPS / tọa độ / link Google Maps, ảnh, gắn sản phẩm OCOP, gửi duyệt, yêu cầu cập nhật hoặc ngừng hiển thị.
- ✅ Ảnh lưu cục bộ hoặc trên Cloudinary; mỗi ảnh có thể ghi nguồn, tác giả, giấy phép.
- 🟡 Cập nhật thông tin đơn vị: hiện sửa bằng cách gửi lại hồ sơ.

**Quản trị viên**

- ✅ Tổng quan: hàng đợi việc cần xử lý, số liệu chính, thống kê và biểu đồ (Chart.js).
- ✅ Kiểm duyệt sản phẩm, yêu cầu sửa sản phẩm, nguồn chứng cứ công nhận OCOP.
- ✅ Duyệt hồ sơ đăng ký chủ thể.
- ✅ Duyệt điểm du lịch: kiểm tra vị trí trong tỉnh, cảnh báo trùng điểm trong 200 m, chỉnh ghim khi duyệt, so sánh và duyệt yêu cầu cập nhật.
- ⬜ Quản lý danh mục, quản lý người dùng, kiểm duyệt đánh giá. Chưa có trang tạo tài khoản quản trị (xem mục 4.4).

Giao diện dùng bộ design token chung (font Be Vietnam Pro, tông xanh trời Đà Lạt cho khu công khai và quản trị) và đạt WCAG 2.2 AA trên các trang đã làm mới.

## 2. Công nghệ

| Phần | Công nghệ |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, JWT, httpx, pytest |
| Frontend | Vue 3, TypeScript, Vite, Vue Router, Axios, Bootstrap 5, Leaflet + markercluster, Chart.js, Vitest |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Dịch vụ ngoài | Cloudinary (lưu ảnh, tùy chọn), ảnh nền OpenStreetMap, định tuyến OSRM, RSS cổng OCOP Lâm Đồng |
| Môi trường | Docker Compose (postgres, pgadmin, backend, frontend) |

## 3. Cấu trúc thư mục

```text
backend/     API FastAPI: app/api/routes (route), app/models (model), app/schemas, app/services, tests/
frontend/    Giao diện Vue: src/views (trang), src/components, src/services (gọi API), src/styles (token)
database/    schema.sql, migrations/0xx_*.sql, file seed, ERD.md, pgadmin/servers.json
data/        Dữ liệu gốc: danh sách OCOP, điểm du lịch (CSV)
docs/        Tài liệu: API, dữ liệu, quy trình kiểm duyệt, audit giao diện, kế hoạch, Postman, nguồn OCOP
tools/       Script sinh seed từ dữ liệu gốc, kiểm tra database
scripts/     verify-mvp.ps1 (kiểm tra nhanh toàn hệ thống)
CLAUDE.md    Quy tắc làm việc của nhóm khi dùng Claude
```

## 4. Chạy dự án

Các lệnh dưới đây chạy trong PowerShell, tại thư mục gốc của repo.

### 4.1. Cần cài

- Git và Docker Desktop (bật WSL 2, đang chạy).
- Các cổng còn trống: `5173` (web), `8000` (API), `5432` (PostgreSQL), `5050` (pgAdmin). Nếu máy đã có PostgreSQL chạy ở cổng 5432, tắt nó trước.
- Không cần cài Python hay Node trên máy nếu chạy bằng Docker.

### 4.2. Chạy lần đầu

1. Lấy mã nguồn:

   ```powershell
   git clone https://github.com/Luyen05/ocop-lamdong-portal.git
   cd ocop-lamdong-portal
   ```

2. Tạo file cấu hình: sao chép `.env.example` thành `.env` rồi sửa:
   - Thay mọi giá trị `change-me` (mật khẩu PostgreSQL, mật khẩu pgAdmin).
   - `JWT_SECRET_KEY`: chuỗi ngẫu nhiên dài ít nhất 32 ký tự.
   - `PGADMIN_DEFAULT_EMAIL`: email có đuôi bình thường như `admin@example.com`. pgAdmin từ chối đuôi `.local`, `.invalid` và email có dấu chấm ngay trước `@`.
   - Không commit `.env`.

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

3. Khởi động toàn bộ:

   ```powershell
   docker compose up -d --build
   docker compose ps
   ```

   Đợi đến khi `lamdong-postgres` báo `healthy`. Lần đầu mất vài phút vì phải tải image và cài thư viện.

4. Mở:

   | Dịch vụ | Địa chỉ |
   |---|---|
   | Trang web | http://localhost:5173 |
   | API và Swagger | http://localhost:8000/docs |
   | pgAdmin | http://localhost:5050 |

   pgAdmin đăng nhập bằng `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD` trong `.env`. Server "LamDong PostgreSQL" có sẵn; mật khẩu kết nối là `POSTGRES_PASSWORD`.

Lần đầu (volume PostgreSQL trống), Docker tự chạy `database/schema.sql`, `seed_dev.sql` (6 nhóm sản phẩm, 4 sản phẩm demo bị ẩn khỏi trang công khai, 2 tài khoản demo bị khóa) và `seed_tourism_locations.sql` (9 điểm du lịch). Sau đó chọn một trong hai cách ở mục 4.3.

### 4.3. Dữ liệu: dùng dữ liệu demo hoặc nhập tay

**Cách A: nạp dữ liệu demo** (sản phẩm OCOP tham khảo có nguồn, sản phẩm ở đủ các trạng thái kiểm duyệt, tài khoản demo):

```powershell
Get-Content .\database\seed_public_reference.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Get-Content .\database\seed_ocop_2025_2026.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Get-Content .\database\seed_product_workflow.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
# Tùy chọn: chuỗi Dehavi Valley → Hân Vinh → Dehavi Showroom (xem docs/DEHAVI_DEMO_DATA.md)
Get-Content .\database\seed_dehavi_demo.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Tài khoản demo (chỉ dùng khi phát triển, mật khẩu `DemoOCOP@2026`):

| Tài khoản | Vai trò |
|---|---|
| `admin.ocop.demo@example.com` | Quản trị viên |
| `chuthe.ocop.demo@example.com` | Chủ thể đã duyệt, có sản phẩm ở đủ các trạng thái |
| `ungvien.ocop.demo@example.com` | Người dùng đang chờ duyệt hồ sơ chủ thể |

Chi tiết dữ liệu kiểm thử: [`docs/DU_LIEU_KIEM_THU_SAN_PHAM.md`](docs/DU_LIEU_KIEM_THU_SAN_PHAM.md).

**Cách B: bắt đầu trống và nhập tay qua giao diện.** Không chạy các seed ở cách A. Tạo tài khoản quản trị theo mục 4.4, sau đó:

1. Đăng ký tài khoản ở `/dang-ky` (mỗi chủ thể một tài khoản, vì một tài khoản chỉ gắn với một hồ sơ chủ thể).
2. Gửi hồ sơ chủ thể ở `/dang-ky-chu-the`.
3. Admin duyệt ở `/quan-tri/ho-so-chu-the`. Tài khoản chủ thể đăng nhập lại để nhận quyền mới.
4. Chủ thể thêm sản phẩm ở `/chu-the/san-pham/them`, lưu nháp rồi gửi duyệt.
5. Admin duyệt ở `/quan-tri/san-pham`.

Lưu nháp chỉ cần tên và nhóm sản phẩm. Gửi duyệt cần đủ mô tả, hạng sao 3 đến 5, mã chứng nhận, ngày cấp, ngày hết hạn còn hiệu lực, cơ quan công nhận, file hoặc đường dẫn giấy chứng nhận và đúng một ảnh chính.

### 4.4. Tạo tài khoản quản trị

Trang đăng ký chỉ tạo tài khoản người dùng thường. Để có tài khoản quản trị:

1. Đăng ký một tài khoản ở `/dang-ky`, ví dụ `admin.ocop@gmail.com`.
2. Nâng quyền bằng lệnh dưới đây (đổi email nếu cần), rồi đăng xuất và đăng nhập lại:

   ```powershell
   "UPDATE users SET role_id = (SELECT id FROM roles WHERE name = 'admin') WHERE email = 'admin.ocop@gmail.com';" | docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
   ```

   Kết quả `UPDATE 1` là thành công; `UPDATE 0` nghĩa là email chưa đăng ký hoặc gõ sai.

### 4.5. Cập nhật lên code mới nhất

Mỗi lần lấy code mới từ GitHub:

```powershell
git switch main
git pull
docker compose up -d --build     # build lại backend khi requirements.txt hoặc Dockerfile đổi
docker compose restart frontend  # khi frontend/package.json đổi: container tự npm install lúc khởi động
```

Sau đó chạy các migration mới (nếu có) theo mục 5 và chạy `tools/kiem-tra-database.sql` để chắc database khớp repo.

### 4.6. Lưu ảnh: cục bộ hoặc Cloudinary

Ảnh sản phẩm và ảnh điểm du lịch do chủ thể tải lên được lưu theo biến `IMAGE_STORAGE` trong `.env`:

- `local` (mặc định): lưu trong thư mục `backend/uploads`. Không cần cấu hình gì, dùng khi phát triển và chạy kiểm thử.
- `cloudinary`: tải lên Cloudinary. Cần tài khoản Cloudinary (gói Free, không cần thẻ) và điền `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` lấy ở trang Dashboard của Cloudinary. Thiếu một biến thì backend báo lỗi khi khởi động.

Sau khi đổi `.env`, chạy `docker compose up -d backend` để nạp lại. Không commit khóa Cloudinary; nếu lỡ để lộ, tạo khóa mới trên Cloudinary.

File giấy chứng nhận sản phẩm luôn lưu cục bộ và chỉ tải được qua API có kiểm tra quyền. Ảnh đã lưu cục bộ trước đó vẫn dùng được.

### 4.7. Chạy không dùng Docker (tùy chọn)

Vẫn cần PostgreSQL 16 + PostGIS. Cách đơn giản nhất là chỉ chạy database bằng Docker: `docker compose up -d postgres`.

```powershell
# Backend (Python 3.12), cửa sổ thứ nhất
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (Node 22, giống image Docker), cửa sổ thứ hai
cd frontend
npm install
npm run dev
```

Backend đọc `.env` ở thư mục gốc repo; khi chạy ngoài Docker nó dùng `DATABASE_URL` trong file đó (trỏ tới `localhost:5432`).

### 4.8. Lệnh thường dùng

```powershell
docker compose ps                     # xem trạng thái các container
docker compose logs -f backend        # xem log (backend, frontend, postgres, pgadmin)
docker compose restart backend        # khởi động lại một dịch vụ
docker compose down                   # dừng, giữ nguyên dữ liệu
```

Không dùng `docker compose down -v`: lệnh này xóa cả database và ảnh đã tải lên (khi `IMAGE_STORAGE=local`).

### 4.9. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân và cách xử lý |
|---|---|
| pgAdmin báo "Incorrect username or password" dù `.env` đúng | pgAdmin chỉ tạo tài khoản ở lần chạy đầu và lưu trong volume; sửa `.env` sau đó không có tác dụng. Đăng nhập sai 3 lần thì bị khóa. Xóa riêng volume pgAdmin (không ảnh hưởng database): `docker compose stop pgadmin`, `docker compose rm -f pgadmin`, `docker volume ls --filter name=pgadmin` để xem tên, `docker volume rm <tên volume>`, rồi `docker compose up -d pgadmin` |
| pgAdmin báo "The CSRF token is invalid" | Trình duyệt còn cookie cũ của `localhost` (cookie không phân biệt cổng, có thể của pgAdmin dự án khác). Mở `http://127.0.0.1:5050` hoặc cửa sổ ẩn danh |
| Trình duyệt tự điền mật khẩu cũ | Xóa ô mật khẩu và gõ tay; kiểm tra số ký tự trước khi bấm Login |
| Script `.ps1` báo lỗi lạ với chữ tiếng Việt bị vỡ (`Lá»—i…`) | Windows PowerShell 5.1 đọc file UTF-8 không có BOM theo bảng mã cũ. Lưu script dạng "UTF-8 with BOM" |
| Lệnh `psql` truyền qua tham số bị mất dấu ngoặc kép | Windows PowerShell 5.1 làm mất `"` lồng trong tham số. Gửi SQL qua stdin như các lệnh trong README (`Get-Content … -Raw \| docker compose exec -T …`) |
| Backend không khởi động sau khi bật Cloudinary | Thiếu một trong ba biến `CLOUDINARY_*`; xem `docker compose logs backend` |
| Trang web không thấy sản phẩm vừa thêm | Sản phẩm nháp hoặc chờ duyệt không hiện ở trang công khai; xem điều kiện ở mục 1 |
| Cổng 5432 hoặc 5050 đã bị dùng | Tắt PostgreSQL/pgAdmin khác trên máy, hoặc dừng container của dự án khác |

## 5. Database và migration

- Database mới tạo từ `database/schema.sql` luôn là phiên bản mới nhất, không cần chạy migration.
- Database đã có dữ liệu: sau mỗi lần `git pull`, chạy các migration chưa chạy theo thứ tự (từ file đầu tiên chưa chạy tới 012). Mọi migration chạy lặp lại an toàn. Ví dụ:

  ```powershell
  Get-Content .\database\migrations\011_tourism_location_drafts.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
  Get-Content .\database\migrations\012_image_attribution.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
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
| 012_image_attribution | Ghi nguồn, tác giả, giấy phép cho ảnh sản phẩm và ảnh điểm du lịch |

**Kiểm tra database khớp repo:** mở `tools/kiem-tra-database.sql` trong Query Tool của pgAdmin và chạy.
Kết quả rỗng là khớp; dòng `thieu_so_voi_repo` là migration chưa chạy; dòng `thua_ngoai_repo` là thay đổi làm thẳng trên database mà repo không có.

**Sao lưu trước khi làm việc lớn với dữ liệu:**

```powershell
docker compose exec -T postgres sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/backup.dump'
docker compose cp postgres:/tmp/backup.dump .\backup.dump
```

Không commit file `.dump`; lưu ngoài repo.

**Quy tắc:** mọi thay đổi database phải là một migration mới trong repo, cập nhật cùng lúc `schema.sql`, model và `tools/kiem-tra-database.sql` (sinh lại bằng `tools/sinh_kiem_tra_database.py`). Không sửa thẳng database bằng pgAdmin hay công cụ khác.

## 6. Kiểm thử

```powershell
docker compose exec backend python -m pytest -q      # backend: 148 test chạy, 8 test bỏ qua
docker compose exec frontend npm test                # frontend: 154 test trong 40 file
docker compose exec frontend npm run type-check
docker compose exec frontend npm run build
.\scripts\verify-mvp.ps1                             # kiểm tra nhanh toàn hệ thống, chỉ đọc dữ liệu
```

Số test đo ngày 07/10/2026 trên `main`. 8 test backend bị bỏ qua là test seed Dehavi, chỉ chạy với một PostGIS tạm riêng qua biến `DEHAVI_SEED_TEST_DATABASE_URL` (xem `docs/DEHAVI_DEMO_DATA.md`), không bao giờ chạy trên database demo.

Pull Request phải qua đủ test, type-check và build. Thay đổi giao diện kiểm tra thêm trợ năng (axe, WCAG 2.2 AA) và không tràn ngang ở màn 375px.

## 7. Trang giao diện và API

**Trang chính**

| Khu vực | Đường dẫn |
|---|---|
| Công khai | `/`, `/san-pham`, `/san-pham/:slug`, `/san-pham/:slug/diem-trai-nghiem`, `/diem-du-lich`, `/diem-du-lich/:slug`, `/ban-do`, `/tin-tuc` |
| Tài khoản | `/dang-nhap`, `/dang-ky`, `/tai-khoan`, `/dang-ky-chu-the` |
| Chủ thể | `/chu-the/ho-so`, `/chu-the/san-pham`, `/chu-the/san-pham/them`, `/chu-the/diem-du-lich`, `/chu-the/diem-du-lich/khai-bao` |
| Quản trị | `/quan-tri`, `/quan-tri/ho-so-chu-the`, `/quan-tri/san-pham`, `/quan-tri/diem-du-lich` |

**API** (tài liệu đầy đủ ở Swagger `/docs` và [`docs/API.md`](docs/API.md)), các nhóm endpoint dưới `/api/v1`:

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

- Mỗi chức năng một nhánh `2312682_HaLuyen_<TenChucNang>` (hoặc tên theo người làm), tạo từ `main` mới nhất (`git fetch` trước).
- Không sửa trực tiếp `main`. Code lên `main` qua Pull Request, có người review.
- Commit dạng `loại(phạm vi): mô tả tiếng Việt`, ví dụ `feat(api): …`, `fix(ui): …`, `docs: …`. Backend và giao diện là các commit riêng.
- Trên Windows dùng `git -c core.autocrlf=true …` nếu thấy mọi file đều báo "modified" vì khác kiểu xuống dòng.
- Không commit `.env`, file sao lưu `.dump`, `node_modules`, khóa Cloudinary.
- Khi làm cùng Claude: quy tắc chi tiết trong [`CLAUDE.md`](CLAUDE.md).

## 9. Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [`docs/KE_HOACH_HOAN_THANH_DO_AN.md`](docs/KE_HOACH_HOAN_THANH_DO_AN.md) | Kế hoạch tới khi nộp, tự đánh giá tiến độ, phân công |
| [`database/ERD.md`](database/ERD.md) | Sơ đồ quan hệ dữ liệu |
| [`docs/API.md`](docs/API.md), [`docs/postman/`](docs/postman/) | Hợp đồng API, bộ Postman |
| [`docs/QUY_TRINH_KIEM_DUYET_SAN_PHAM.md`](docs/QUY_TRINH_KIEM_DUYET_SAN_PHAM.md) | Quy trình kiểm duyệt sản phẩm, điều kiện hiển thị công khai |
| [`docs/DU_LIEU_THAM_KHAO_CONG_KHAI.md`](docs/DU_LIEU_THAM_KHAO_CONG_KHAI.md) | Nguồn dữ liệu sản phẩm OCOP |
| [`docs/sources/ocop/README.md`](docs/sources/ocop/README.md) | Văn bản hành chính dùng kiểm chứng dữ liệu, mức xác minh A/B1/B2/C |
| [`docs/DU_LIEU_DIEM_DU_LICH.md`](docs/DU_LIEU_DIEM_DU_LICH.md) | Dữ liệu điểm du lịch, bản đồ, định tuyến |
| [`docs/DU_LIEU_KIEM_THU_SAN_PHAM.md`](docs/DU_LIEU_KIEM_THU_SAN_PHAM.md) | Tài khoản và dữ liệu kiểm thử |
| [`docs/DEHAVI_DEMO_DATA.md`](docs/DEHAVI_DEMO_DATA.md) | Dữ liệu demo chuỗi Dehavi Valley → Dehavi Showroom |
| [`docs/ui-audit.md`](docs/ui-audit.md) | Đánh giá và nhật ký cải thiện giao diện |
| `docs/*.docx` | Phân tích yêu cầu, phụ lục nguồn dữ liệu, hướng dẫn nhóm |
