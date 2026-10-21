# Cấu hình và triển khai

- [1. Biến môi trường](#1-biến-môi-trường)
- [2. Lưu ảnh trên Cloudinary](#2-lưu-ảnh-trên-cloudinary)
- [3. Đăng nhập Google, Facebook](#3-đăng-nhập-google-facebook)
- [4. Triển khai thật](#4-triển-khai-thật)

Mọi cấu hình nằm trong file `.env` ở thư mục gốc repo (tạo từ `.env.example`, **không commit**). Sau khi sửa `.env`, chạy `docker compose up -d` để tạo lại container có thay đổi.

## 1. Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `lamdong_ocop`, `postgres`, (bắt buộc) | Database PostgreSQL trong Docker |
| `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD` | (bắt buộc) | Tài khoản đăng nhập pgAdmin (`http://127.0.0.1:5050`) |
| `DATABASE_URL` | | Chỉ cần khi chạy backend ngoài Docker; Docker Compose tự ghép |
| `JWT_SECRET_KEY` | (bắt buộc) | Khóa ký token, ≥ 32 ký tự. **Phải đổi**: backend từ chối khởi động nếu giữ giá trị mẫu của `.env.example`. Tạo bằng `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Thời hạn token (1–1440 phút) |
| `CORS_ORIGINS` | `http://localhost:5173` | Địa chỉ frontend được gọi API, phân tách bằng dấu phẩy |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Địa chỉ API mà frontend gọi |
| `VITE_MAP_TILE_URL` | | (Tùy chọn, trong `frontend/.env`) nguồn ảnh nền bản đồ ưu tiên; mặc định OpenStreetMap, lỗi thì chuyển sang OpenStreetMap Humanitarian |
| `IMAGE_STORAGE` | `local` | `local` (thư mục `backend/uploads`) hoặc `cloudinary` |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_FOLDER` | | Bắt buộc khi `IMAGE_STORAGE=cloudinary` (mục 2) |
| `PUBLIC_BASE_URL` | | Địa chỉ công khai của backend để ghép URL ảnh lưu cục bộ khi chạy sau proxy/tên miền; trống thì lấy theo request |
| `FRONTEND_BASE_URL` | `http://localhost:5173` | Địa chỉ trang web; Google/Facebook trả người dùng về `FRONTEND_BASE_URL/dang-nhap/mang-xa-hoi/<google\|facebook>` |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | | Bật đăng nhập Google (mục 3); trống thì ẩn nút |
| `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, `FACEBOOK_GRAPH_VERSION` | `v26.0` | Bật đăng nhập Facebook (mục 3); trống thì ẩn nút |
| `NEWS_RSS_URL`, `NEWS_RSS_TIMEOUT_SECONDS`, `NEWS_RSS_MAX_BYTES`, `NEWS_CACHE_TTL_SECONDS` | RSS cổng OCOP tỉnh, 8 giây, 1 MB, 900 giây | Nguồn tin tức |
| `OSRM_BASE_URL`, `OSRM_TIMEOUT_SECONDS` | máy chủ OSRM công khai, 8 giây | Dịch vụ chỉ đường |

## 2. Lưu ảnh trên Cloudinary

1. Tạo tài khoản Cloudinary gói Free (không cần thẻ thanh toán).
2. Ở trang **Dashboard**, chép Cloud name, API key, API secret vào `.env`; đặt `IMAGE_STORAGE=cloudinary`.
3. Chạy `docker compose up -d backend`. Thiếu một trong ba khóa thì backend báo lỗi khi khởi động (xem `docker compose logs backend`).

- Backend gọi API Cloudinary bằng `httpx` (upload, xóa, kiểm tra tồn tại có chữ ký); không cần thư viện của Cloudinary.
- Ảnh đã lưu cục bộ trước đó vẫn dùng được. Giấy chứng nhận sản phẩm luôn lưu cục bộ (riêng tư).
- Gói Free có hạn mức (khoảng 25 credit/tháng). Hết hạn mức hoặc dịch vụ lỗi thì đặt lại `IMAGE_STORAGE=local`.
- Lỡ để lộ API secret: tạo khóa mới trên Cloudinary và cập nhật `.env`.

## 3. Đăng nhập Google, Facebook

Quy tắc tài khoản xem `docs/NGHIEP_VU.md` mục 3. Luồng OAuth 2.0 "authorization code": trình duyệt tạo `state` (và PKCE với Google), Google/Facebook trả về `/dang-nhap/mang-xa-hoi/<nhà cung cấp>`, backend dùng khóa bí mật đổi mã lấy thông tin người dùng rồi cấp JWT. Khóa bí mật chỉ nằm ở backend.

### Google

Giao diện Google có thể đổi tên menu theo thời gian.

1. Vào <https://console.cloud.google.com/>, tạo project (ví dụ `ocop-lam-dong`).
2. Mở **Google Auth Platform**:
   - **Branding**: tên ứng dụng, email hỗ trợ, email liên hệ.
   - **Audience**: chọn **External**. Ở chế độ **Testing**, chỉ tài khoản trong **Test users** đăng nhập được: thêm Gmail của thành viên và tài khoản demo.
   - **Data access**: chỉ cần `openid`, `email`, `profile` (không cần Google xét duyệt).
3. **Clients → Create client → Web application**. **Authorized redirect URIs**: `http://localhost:5173/dang-nhap/mang-xa-hoi/google` (triển khai thật thêm `https://<tên-miền>/dang-nhap/mang-xa-hoi/google`). Không cần "Authorized JavaScript origins".
4. Chép **Client ID**, **Client secret** vào `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.

### Facebook

1. Vào <https://developers.facebook.com/> → **My Apps → Create App**, chọn trường hợp sử dụng **Authenticate and request data from users with Facebook Login**, không liên kết doanh nghiệp.
2. Trong use case, mở **Permissions**, bật thêm **email**.
3. **Facebook Login → Settings → Valid OAuth Redirect URIs**: `http://localhost:5173/dang-nhap/mang-xa-hoi/facebook` (triển khai thật thêm bản `https`). Giữ bật **Use Strict Mode** và **Enforce HTTPS** (`localhost` được phép ở chế độ phát triển).
4. **App settings → Basic**: chép **App ID**, **App Secret** vào `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`.
5. Ở chế độ **Development**, chỉ tài khoản có vai trò trong ứng dụng (**App roles → Roles**) đăng nhập được. Chuyển **Live** cần trang chính sách quyền riêng tư công khai.

### Kiểm tra và lỗi thường gặp

Sau khi điền khóa, chạy `docker compose up -d backend` rồi mở <http://localhost:8000/api/v1/auth/social/providers>: kết quả phải có `"google"` và/hoặc `"facebook"`.

| Hiện tượng | Cách xử lý |
|---|---|
| Không thấy nút Google/Facebook | Thiếu ID hoặc Secret, hoặc chưa tạo lại container backend sau khi sửa `.env` |
| Google báo `redirect_uri_mismatch` | Địa chỉ đã khai báo khác `FRONTEND_BASE_URL/dang-nhap/mang-xa-hoi/google` (sai cổng, `localhost` khác `127.0.0.1`, thừa dấu `/`) |
| Google báo "Access blocked … verification process" | Tài khoản chưa có trong **Test users** |
| Facebook báo "URL blocked" | Chưa thêm địa chỉ vào **Valid OAuth Redirect URIs** |
| Facebook báo ứng dụng chưa hoạt động | Tài khoản chưa có vai trò trong ứng dụng |
| "Tài khoản Facebook không cung cấp email" | Người dùng bỏ chia sẻ email, hoặc tài khoản Facebook đăng ký bằng số điện thoại |
| "Phiên đăng nhập không hợp lệ hoặc đã hết hạn" | Để trang Google/Facebook quá 10 phút, mở đường dẫn trả về ở tab khác, hoặc tải lại trang: bấm "Thử lại" |
| "Không kết nối được với Google/Facebook" | Máy chạy backend không ra được Internet |

Lỡ để lộ khóa bí mật: Google tạo secret mới rồi xóa secret cũ trong Client; Facebook bấm **Reset** App Secret; cập nhật `.env`.

## 4. Triển khai thật

Docker Compose trong repo dành cho **môi trường phát triển** (backend `--reload`, frontend chạy Vite dev server). Trước khi đưa lên máy chủ công khai:

- [ ] Đặt `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `PGADMIN_DEFAULT_PASSWORD` mạnh, riêng cho máy chủ.
- [ ] Không nạp seed demo (`seed_dev.sql`, `seed_product_workflow.sql` có mật khẩu công khai); dùng dữ liệu nhập tay.
- [ ] Frontend: `npm run build`, phục vụ thư mục `dist/` bằng Nginx (cấu hình chuyển mọi đường dẫn về `index.html` cho Vue Router).
- [ ] Backend: chạy `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers` (không `--reload`) sau Nginx; đặt `PUBLIC_BASE_URL`, `FRONTEND_BASE_URL`, `CORS_ORIGINS`, `VITE_API_BASE_URL` theo tên miền thật.
- [ ] HTTPS (ví dụ Let's Encrypt); thêm địa chỉ `https` vào Google/Facebook.
- [ ] Nginx: `client_max_body_size 12m` (ảnh 5 MB, chứng nhận 10 MB); giới hạn tần suất cho `/api/v1/auth/login` nếu chạy nhiều tiến trình backend (bộ đếm đăng nhập sai nằm trong bộ nhớ từng tiến trình).
- [ ] Không mở cổng PostgreSQL (5432) và pgAdmin ra Internet (Compose đã chỉ mở trên `127.0.0.1`).
- [ ] Sao lưu database định kỳ: `pg_dump -Fc` (lệnh mẫu trong README), lưu ngoài máy chủ; giữ volume `backend_uploads` nếu lưu ảnh cục bộ hoặc dùng Cloudinary.
- [ ] Database đã có dữ liệu: chạy `database/migrations/014_hoan_thien.sql`, rồi `tools/kiem-tra-database.sql` phải trả rỗng.
