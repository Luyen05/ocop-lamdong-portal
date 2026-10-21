<div align="center">

# Cổng thông tin OCOP và bản đồ số du lịch nông nghiệp Lâm Đồng

**Quảng bá sản phẩm OCOP đã được kiểm duyệt và dẫn đường tới các điểm du lịch nông nghiệp của tỉnh Lâm Đồng.**

Vue 3 · FastAPI · PostgreSQL + PostGIS · Docker

[Tính năng](#tính-năng) · [Bắt đầu nhanh](#bắt-đầu-nhanh) · [Cấu hình](#cấu-hình) · [Database](#database-và-migration) · [Kiểm thử](#kiểm-thử) · [Tài liệu](#tài-liệu)

</div>

---

Đồ án chuyên ngành **"Xây dựng Cổng thông tin quảng bá nông sản OCOP và bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng"**, Trường Đại học Đà Lạt.

- **Nhóm:** Liêng Hót Ha Luyến (nhóm trưởng), Nguyễn Quốc Thái, Nguyễn Khiêm Thuận.
- **Giảng viên hướng dẫn:** Trần Ngô Như Khánh.

## Mục lục

- [Tính năng](#tính-năng)
- [Công nghệ](#công-nghệ)
- [Bắt đầu nhanh](#bắt-đầu-nhanh)
- [Dữ liệu ban đầu](#dữ-liệu-ban-đầu)
- [Cấu hình](#cấu-hình)
- [Database và migration](#database-và-migration)
- [Kiểm thử](#kiểm-thử)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Trang và API](#trang-và-api)
- [Tài liệu](#tài-liệu)
- [Xử lý sự cố](#xử-lý-sự-cố)
- [Quy trình đóng góp](#quy-trình-đóng-góp)
- [Giới hạn đã biết](#giới-hạn-đã-biết)

## Tính năng

**Khách và người dùng**

- Trang chủ với tìm kiếm sản phẩm/điểm du lịch, bản đồ xem trước, nhóm sản phẩm, sản phẩm nổi bật.
- Danh sách sản phẩm OCOP: tìm kiếm, lọc theo nhóm, hạng sao, địa bàn, giá; chi tiết có thư viện ảnh (ghi nguồn), thông tin công nhận OCOP, điểm du lịch liên quan.
- Tìm điểm mua và trải nghiệm của một sản phẩm, sắp theo khoảng cách tới người dùng.
- Danh sách và chi tiết điểm du lịch nông nghiệp (dịch vụ, giờ mở cửa, giá vé, sản phẩm bán tại điểm).
- Bản đồ số: gom cụm, lọc, định vị, điểm gần nhất (PostGIS), chỉ đường (OSRM, dự phòng Google Maps).
- Đánh giá sản phẩm và điểm du lịch (chờ duyệt trước khi hiển thị), trang "Đánh giá của tôi".
- Tin tức từ RSS cổng OCOP tỉnh.
- Tài khoản: đăng ký, đăng nhập (giới hạn sai mật khẩu), đăng nhập Google/Facebook, liên kết tài khoản, đổi/đặt mật khẩu, hồ sơ cá nhân, đăng ký trở thành chủ thể.

**Chủ thể OCOP** (hợp tác xã, doanh nghiệp, hộ sản xuất)

- Sửa thông tin liên hệ của đơn vị.
- Quản lý sản phẩm: bản nháp, gửi duyệt, ảnh, giấy chứng nhận riêng tư, yêu cầu sửa hoặc ngừng hiển thị sau khi duyệt.
- Khai báo điểm du lịch: ghim bản đồ, GPS, tọa độ hoặc link Google Maps; kiểm tra vị trí trong tỉnh, cảnh báo trùng điểm; ảnh; gắn sản phẩm; yêu cầu cập nhật.

**Quản trị viên**

- Tổng quan: hàng đợi việc cần duyệt, số liệu, biểu đồ thống kê (Chart.js).
- Duyệt hồ sơ chủ thể, sản phẩm, yêu cầu thay đổi, điểm du lịch (chỉnh ghim khi duyệt), đánh giá.
- Quản lý người dùng (tìm kiếm, khóa/mở khóa), danh mục (thêm, sửa, ẩn, sắp xếp), nguồn dữ liệu và chứng cứ công nhận.

Giao diện đáp ứng từ điện thoại đến máy tính, dùng bộ design token chung, hướng tới WCAG 2.2 AA. Quy tắc nghiệp vụ chi tiết: [`docs/NGHIEP_VU.md`](docs/NGHIEP_VU.md).

## Công nghệ

| Phần | Công nghệ |
|---|---|
| Frontend | Vue 3, TypeScript, Vite, Vue Router, Axios, Bootstrap 5, Bootstrap Icons, Leaflet + markercluster, Chart.js |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2, PyJWT, pwdlib (Argon2), httpx |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Kiểm thử | pytest, Vitest, Vue Test Utils |
| Dịch vụ ngoài | Cloudinary (tùy chọn), OpenStreetMap, OSRM, RSS cổng OCOP Lâm Đồng, Google/Facebook OAuth (tùy chọn) |
| Môi trường | Docker Compose: `postgres`, `pgadmin`, `backend`, `frontend` |

Kiến trúc, cấu trúc mã nguồn, sơ đồ dữ liệu: [`docs/KIEN_TRUC.md`](docs/KIEN_TRUC.md).

## Bắt đầu nhanh

### Yêu cầu

- Git và Docker Desktop (Windows: bật WSL 2) đang chạy.
- Các cổng còn trống: `5173` (web), `8000` (API), `5432` (PostgreSQL), `5050` (pgAdmin).
- Không cần cài Python, Node trên máy khi chạy bằng Docker.

Các lệnh dưới đây chạy trong PowerShell tại thư mục gốc repo (Linux/macOS dùng lệnh tương đương).

### 1. Lấy mã nguồn

```powershell
git clone https://github.com/Luyen05/ocop-lamdong-portal.git
cd ocop-lamdong-portal
```

### 2. Tạo file cấu hình

```powershell
Copy-Item .env.example .env
notepad .env
```

Trong `.env`, bắt buộc sửa:

- Mọi giá trị `change-me` (mật khẩu PostgreSQL, mật khẩu pgAdmin).
- `JWT_SECRET_KEY`: chuỗi ngẫu nhiên ≥ 32 ký tự. Backend **từ chối khởi động** nếu giữ giá trị mẫu. Tạo nhanh: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- `PGADMIN_DEFAULT_EMAIL`: email bình thường (pgAdmin từ chối đuôi `.local`, `.invalid`).

Không commit `.env`.

### 3. Khởi động

```powershell
docker compose up -d --build
docker compose ps
```

Đợi `lamdong-postgres` và `lamdong-backend` báo `healthy` (lần đầu vài phút để tải image và cài thư viện).

| Dịch vụ | Địa chỉ |
|---|---|
| Trang web | <http://localhost:5173> |
| API (Swagger) | <http://localhost:8000/docs> |
| pgAdmin | <http://127.0.0.1:5050> (đăng nhập bằng `PGADMIN_DEFAULT_EMAIL`/`PGADMIN_DEFAULT_PASSWORD`; server "LamDong PostgreSQL" có sẵn, mật khẩu là `POSTGRES_PASSWORD`) |

Lần đầu (volume trống), Docker tự tạo database từ `database/schema.sql` và nạp `seed_dev.sql` (6 nhóm sản phẩm, vài sản phẩm demo bị ẩn) cùng `seed_tourism_locations.sql` (9 điểm du lịch).

### 4. Tạo tài khoản quản trị

Trang đăng ký chỉ tạo tài khoản người dùng. Đăng ký một tài khoản ở `/dang-ky` (ví dụ `admin.ocop@gmail.com`), rồi nâng quyền:

```powershell
"UPDATE users SET role_id = (SELECT id FROM roles WHERE name = 'admin') WHERE email = 'admin.ocop@gmail.com';" | docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

`UPDATE 1` là thành công. Đăng xuất rồi đăng nhập lại để vào `/quan-tri`.

### Cập nhật lên code mới

```powershell
git switch main
git pull
docker compose up -d --build      # build lại khi requirements.txt, Dockerfile hoặc docker-compose.yml đổi
docker compose restart frontend   # khi frontend/package.json đổi (container tự npm install)
```

Database đã có dữ liệu thì chạy migration (mục [Database và migration](#database-và-migration)).

### Chạy không dùng Docker

Vẫn cần PostgreSQL 16 + PostGIS (có thể chỉ chạy `docker compose up -d postgres`). Backend đọc `.env` ở thư mục gốc, dùng `DATABASE_URL` trỏ tới `localhost:5432`.

```powershell
# Backend (Python 3.12)
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (Node 22), cửa sổ khác
cd frontend
npm install
npm run dev
```

## Dữ liệu ban đầu

**Bản demo và báo cáo: nhập tay qua giao diện** (không dùng seed demo):

1. Mỗi chủ thể đăng ký một tài khoản ở `/dang-ky` (quy ước email: tên chủ thể + vai trò + `@gmail.com`), rồi gửi hồ sơ ở `/dang-ky-chu-the`.
2. Quản trị viên duyệt ở `/quan-tri/ho-so-chu-the`; trang của chủ thể tự chuyển sang quyền chủ thể.
3. Chủ thể thêm sản phẩm ở `/chu-the/san-pham/them` (lưu nháp chỉ cần tên và nhóm; gửi duyệt cần mô tả, hạng sao 3–5, thông tin và bản chụp giấy chứng nhận còn hạn, đúng một ảnh chính), khai báo điểm ở `/chu-the/diem-du-lich/khai-bao`.
4. Quản trị viên duyệt ở `/quan-tri/san-pham`, `/quan-tri/diem-du-lich`.

**Phát triển và kiểm thử: nạp seed** (sản phẩm OCOP tham khảo có nguồn, sản phẩm ở đủ trạng thái, tài khoản demo):

```powershell
foreach ($seed in 'seed_public_reference','seed_ocop_2025_2026','seed_product_workflow','seed_dehavi_demo','seed_dehavi_media') {
  Get-Content ".\database\$seed.sql" -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
}
```

Sau khi nạp: 61 sản phẩm và 10 điểm du lịch hiển thị công khai. Tài khoản demo (mật khẩu `DemoOCOP@2026`, **không dùng cho bản triển khai**): `admin.ocop.demo@example.com` (quản trị), `chuthe.ocop.demo@example.com` (chủ thể), `ungvien.ocop.demo@example.com` (người dùng có hồ sơ chủ thể đang chờ). Chi tiết: [`docs/DU_LIEU.md`](docs/DU_LIEU.md).

## Cấu hình

Mọi cấu hình nằm trong `.env`; danh sách đầy đủ ở [`docs/CAU_HINH.md`](docs/CAU_HINH.md). Sau khi sửa, chạy `docker compose up -d`.

| Tính năng | Biến | Ghi chú |
|---|---|---|
| Lưu ảnh trên Cloudinary | `IMAGE_STORAGE=cloudinary`, `CLOUDINARY_*` | Mặc định `local` (thư mục `backend/uploads`) |
| Đăng nhập Google | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Trống thì ẩn nút; địa chỉ trả về `http://localhost:5173/dang-nhap/mang-xa-hoi/google` |
| Đăng nhập Facebook | `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` | Trống thì ẩn nút; địa chỉ trả về `.../dang-nhap/mang-xa-hoi/facebook` |
| Chạy sau tên miền/proxy | `PUBLIC_BASE_URL`, `FRONTEND_BASE_URL`, `CORS_ORIGINS`, `VITE_API_BASE_URL` | Xem mục triển khai trong `docs/CAU_HINH.md` |

## Database và migration

- **Database mới:** tạo từ `database/schema.sql`, không cần migration.
- **Database đã có dữ liệu** (sau mỗi lần cập nhật code): chạy migration tổng hợp. File chạy trong một transaction, chạy lặp lại an toàn, đưa database ở bất kỳ phiên bản cũ nào lên phiên bản hiện tại:

  ```powershell
  Get-Content .\database\migrations\014_hoan_thien.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
  ```

- **Kiểm tra database khớp repo:** chạy `tools/kiem-tra-database.sql` trong pgAdmin (Query Tool) hoặc:

  ```powershell
  Get-Content .\tools\kiem-tra-database.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
  ```

  Kết quả rỗng là khớp; `thieu_so_voi_repo` là chưa chạy migration; `thua_ngoai_repo` là thay đổi làm ngoài repo.

- **Sao lưu** trước khi thao tác lớn (không commit file `.dump`):

  ```powershell
  docker compose exec -T postgres sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/backup.dump'
  docker compose cp postgres:/tmp/backup.dump .\backup.dump
  ```

- **Quy tắc:** mọi thay đổi database là một migration mới trong `database/migrations/`, cập nhật cùng lúc `schema.sql`, model và file kiểm tra (`tools/sinh_kiem_tra_database.py`). Không sửa thẳng database bằng pgAdmin. Các migration cũ 001–013 lưu ở `database/migrations/archive/`.
- Không dùng `docker compose down -v`: lệnh này xóa database và ảnh đã tải lên.

## Kiểm thử

```powershell
docker compose exec backend python -m pytest -q    # backend: 272 đạt, 9 bỏ qua
docker compose exec frontend npm test              # frontend: 272 test trong 59 file
docker compose exec frontend npm run type-check
docker compose exec frontend npm run build
python -m pytest -q tests/data                     # dữ liệu OCOP gốc (cần Python trên máy)
.\scripts\verify-mvp.ps1                           # kiểm tra nhanh toàn hệ thống đang chạy (chỉ đọc)
```

9 test backend bỏ qua là test seed Dehavi, chỉ chạy với PostGIS tạm riêng ([`docs/DU_LIEU.md`](docs/DU_LIEU.md) mục 7). Dịch vụ ngoài (Google, Facebook, Cloudinary, OSRM, RSS) đều được giả lập trong test.

## Cấu trúc thư mục

```text
.
├── backend/              API FastAPI
│   ├── app/              api/routes, core, models, schemas, services, main.py
│   └── tests/            Test pytest
├── frontend/             Ứng dụng Vue 3
│   └── src/              views, layouts, components, services, stores, router, styles…
├── database/
│   ├── schema.sql        Cấu trúc database đầy đủ (dùng khi tạo mới)
│   ├── migrations/       014_hoan_thien.sql (nâng cấp database cũ), archive/ 001–013
│   └── seed_*.sql        Dữ liệu ban đầu và dữ liệu mẫu
├── data/                 Dữ liệu gốc OCOP, điểm du lịch (để sinh seed)
├── tools/                Sinh seed, sinh tài liệu API, kiểm tra database
├── tests/data/           Test dữ liệu gốc
├── docs/                 Tài liệu, Postman, văn bản nguồn OCOP
├── scripts/              verify-mvp.ps1
├── docker-compose.yml
├── CHANGELOG.md
└── CLAUDE.md             Quy tắc làm việc của nhóm khi dùng Claude
```

## Trang và API

| Khu vực | Đường dẫn |
|---|---|
| Công khai | `/`, `/san-pham`, `/san-pham/:slug`, `/san-pham/:slug/diem-trai-nghiem`, `/diem-du-lich`, `/diem-du-lich/:slug`, `/ban-do`, `/tin-tuc` |
| Tài khoản | `/dang-nhap`, `/dang-ky`, `/dang-nhap/mang-xa-hoi/:provider`, `/tai-khoan`, `/tai-khoan/danh-gia`, `/dang-ky-chu-the` |
| Chủ thể | `/chu-the/ho-so`, `/chu-the/san-pham`, `/chu-the/san-pham/them`, `/chu-the/diem-du-lich`, `/chu-the/diem-du-lich/khai-bao` |
| Quản trị | `/quan-tri`, `/quan-tri/ho-so-chu-the`, `/quan-tri/san-pham`, `/quan-tri/diem-du-lich`, `/quan-tri/danh-gia`, `/quan-tri/nguoi-dung`, `/quan-tri/danh-muc` |

API REST dưới `/api/v1` (103 endpoint): danh sách đầy đủ, quyền, mã lỗi ở [`docs/API.md`](docs/API.md) (sinh tự động từ OpenAPI bằng `tools/sinh_tai_lieu_api.py`), Swagger tại `/docs`, bộ Postman ở [`docs/postman/`](docs/postman/). Backend kiểm tra vai trò từ database ở mỗi request; sửa JWT hay hiện nút trên giao diện không làm tăng quyền.

## Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [`docs/NGHIEP_VU.md`](docs/NGHIEP_VU.md) | Quy tắc nghiệp vụ: vai trò, tài khoản, kiểm duyệt sản phẩm/điểm/đánh giá, danh mục, điều kiện hiển thị công khai |
| [`docs/API.md`](docs/API.md) | REST API: quy ước, mã lỗi, toàn bộ endpoint |
| [`docs/KIEN_TRUC.md`](docs/KIEN_TRUC.md) | Kiến trúc, cấu trúc mã nguồn, xác thực, lưu file, sơ đồ dữ liệu, migration, kiểm thử |
| [`docs/DU_LIEU.md`](docs/DU_LIEU.md) | Dữ liệu, file seed, nguồn và mức xác minh, tài khoản demo, tái tạo dữ liệu |
| [`docs/CAU_HINH.md`](docs/CAU_HINH.md) | Biến môi trường, Cloudinary, khóa Google/Facebook, danh sách kiểm tra khi triển khai |
| [`docs/sources/ocop/`](docs/sources/ocop/README.md) | Văn bản hành chính dùng kiểm chứng dữ liệu OCOP |
| [`CHANGELOG.md`](CHANGELOG.md) | Các thay đổi chính theo phiên bản |

## Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| Backend không khởi động, log báo `JWT_SECRET_KEY` | Đổi `JWT_SECRET_KEY` khác giá trị mẫu (mục Bắt đầu nhanh, bước 2) rồi `docker compose up -d backend` |
| Backend không khởi động sau khi bật Cloudinary | Thiếu một trong ba biến `CLOUDINARY_*`; xem `docker compose logs backend` |
| API trả `DATABASE_SCHEMA_OUTDATED` | Chạy `database/migrations/014_hoan_thien.sql` |
| Sản phẩm vừa thêm không thấy ở trang công khai | Chưa được duyệt hoặc chưa đủ điều kiện hiển thị (`docs/NGHIEP_VU.md` mục 5) |
| pgAdmin báo sai mật khẩu dù `.env` đúng | pgAdmin chỉ tạo tài khoản ở lần chạy đầu. Xóa riêng volume pgAdmin: `docker compose stop pgadmin`, `docker compose rm -f pgadmin`, `docker volume ls --filter name=pgadmin`, `docker volume rm <tên>`, `docker compose up -d pgadmin` |
| pgAdmin báo "The CSRF token is invalid" | Mở `http://127.0.0.1:5050` hoặc cửa sổ ẩn danh (cookie cũ của `localhost`) |
| Lệnh `psql` truyền qua tham số bị mất dấu ngoặc kép | Windows PowerShell 5.1 làm mất `"` lồng trong tham số; gửi SQL qua stdin như các lệnh trong README |
| Script `.ps1` vỡ chữ tiếng Việt | Lưu script dạng "UTF-8 with BOM" (PowerShell 5.1) |
| Mọi file báo "modified" sau khi clone trên Windows | Dùng `git -c core.autocrlf=true …` |
| Cổng 5432 hoặc 5050 đã bị dùng | Tắt PostgreSQL/pgAdmin khác hoặc container của dự án khác |

## Quy trình đóng góp

- Mỗi chức năng một nhánh `2312682_HaLuyen_<TenChucNang>` (hoặc theo tên người làm) tạo từ `main` mới nhất. Không sửa trực tiếp `main`; code vào `main` qua Pull Request có người review.
- Commit dạng `loại(phạm vi): mô tả tiếng Việt`, ví dụ `feat(api): …`, `fix(ui): …`, `docs: …`; backend và giao diện là các commit riêng.
- Pull Request phải qua đủ test, type-check, build. Thay đổi giao diện kiểm tra thêm trợ năng (axe, WCAG 2.2 AA) và không tràn ngang ở 375/1024/1440 px.
- Thêm hoặc sửa endpoint: chạy lại `cd backend; python ../tools/sinh_tai_lieu_api.py` để cập nhật `docs/API.md` và Postman.
- Không commit `.env`, `.dump`, `node_modules`, khóa bí mật.
- Làm việc cùng Claude: quy tắc chi tiết trong [`CLAUDE.md`](CLAUDE.md).

## Giới hạn đã biết

- Chưa có quên mật khẩu qua email; tin tức do quản trị viên tự đăng chưa làm (đang dùng RSS).
- Ảnh chưa duyệt vẫn mở được nếu biết đường dẫn (đường dẫn ngẫu nhiên 32 ký tự).
- Tìm kiếm phân biệt dấu ("dâu tây" tìm thấy, "dau tay" thì không).
- Docker Compose trong repo dành cho môi trường phát triển; triển khai thật xem `docs/CAU_HINH.md` mục 4.

Dữ liệu sản phẩm, điểm du lịch trong repo chỉ phục vụ học tập, không thay thế cơ sở dữ liệu OCOP chính thức.
