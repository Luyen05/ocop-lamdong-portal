# REST API v1

Base URL: `/api/v1`. Tất cả endpoint có biểu tượng khóa trong Swagger yêu cầu
`Authorization: Bearer <access_token>`.

## Quy ước

- Danh sách trả `{items, page, page_size, total}`.
- Lỗi trả `{code, message, details}`.
- Tọa độ đầu vào là `longitude`, `latitude`; đầu ra dùng GeoJSON `[longitude, latitude]`.
- Public chỉ đọc product/location/review `approved` và news `published`.

## Endpoint

| Nhóm | Method và path | Quyền |
|---|---|---|
| Auth | `POST /auth/register`, `POST /auth/login` | Public |
| Auth | `GET/PATCH /auth/me` | Đã đăng nhập |
| Subject application | `POST /subject-applications` | User |
| Subject application | `GET/PUT /subject-applications/me` | User hoặc subject |
| Public | `GET /categories`, `GET /products`, `GET /products/filter-options`, `GET /products/{slug}` | Public |
| Public | `GET /locations`, `GET /locations/filter-options`, `GET /locations/{slug}` | Public (đã triển khai) |
| Public | `GET /news`, `GET /news/{slug}` | Public |
| Reviews | `GET/POST /products/{id}/reviews`, `GET/POST /locations/{id}/reviews` | GET public, POST đăng nhập |
| Reviews | `PATCH/DELETE /reviews/{id}` | Chính chủ, chỉ khi pending |
| Map | `GET /map/locations`, `GET /map/nearby`, `GET /map/route` | Public (đã triển khai) |
| Subject | `GET/PATCH /subject/profile` | Subject đã duyệt |
| Subject | CRUD `/subject/products`, CRUD `/subject/locations` | Subject, giới hạn sở hữu |
| Subject | POST/DELETE `/subject/locations/{id}/products...` | Subject, giới hạn sở hữu |
| Images | Upload/sắp xếp/xóa ảnh product và location | Subject, giới hạn sở hữu |
| Admin | `/admin/users`, `/admin/subjects`, `/admin/categories` | Admin |
| Admin | `GET /admin/subject-applications` | Admin |
| Admin | `PATCH /admin/subject-applications/{id}/moderation` | Admin |
| Admin | `/admin/products`, `/admin/locations`, `/admin/reviews` | Admin |
| Admin | `/admin/news`, `/admin/news/{id}/images` | Admin |
| Admin | `GET /admin/dashboard` | Admin |

Swagger tại `/docs` là nguồn chi tiết cho query parameter, request body và response
của từng endpoint.

### Quy trình sản phẩm đã triển khai

- Chủ thể đã được duyệt tạo và sửa bản nháp tại /subject/products, sau đó gọi
  POST /subject/products/{id}/submit để gửi kiểm duyệt.
- Hạng sao do chủ thể khai báo theo giấy chứng nhận. Quản trị viên chỉ đối chiếu
  minh chứng và duyệt hiển thị, không cấp hoặc tự nâng hạng sao.
- Quản trị viên xem hàng đợi tại /admin/products và xử lý tại
  PATCH /admin/products/{id}/moderation.
- Sửa sản phẩm đã duyệt tạo yêu cầu tại
  POST /subject/products/{id}/change-requests. Phiên bản cũ vẫn công khai đến
  khi quản trị viên chấp thuận.
- Ngừng hiển thị tạo yêu cầu tại
  POST /subject/products/{id}/deletion-requests. Khi được duyệt, sản phẩm chuyển
  sang trạng thái archived và vẫn được giữ lại để bảo toàn lịch sử.

### Bản đồ số và điểm du lịch đã triển khai

- `GET /locations?search=&type=&district=&sort=name|-name|newest|rating&page=&page_size=`:
  chỉ trả điểm `approved`. `type` nhận mã loại hình (`tea_coffee_farm`,
  `fruit_garden`, `flower_garden`, `dairy_farm`, `vegetable_farm`,
  `craft_village`, `farmstay`, `other`); mã khác trả `422`.
- `GET /locations/{slug}`: chi tiết, liên hệ, nguồn dữ liệu, ảnh và các sản phẩm
  OCOP công khai được giới thiệu tại điểm. Điểm chưa duyệt trả `404 LOCATION_NOT_FOUND`.
- `GET /map/locations`: `FeatureCollection` GeoJSON, tọa độ `[longitude, latitude]`,
  lọc theo `search`, `type`, `district`.
- `GET /map/nearby?latitude=&longitude=&radius_km=25&limit=10&type=`: sắp xếp theo
  khoảng cách (mét) bằng `ST_DWithin`/`ST_Distance` trên `geography`;
  `radius_km` trong khoảng (0, 200], `limit` 1–50.
- `GET /map/route?destination={slug}&from_latitude=&from_longitude=`: tuyến đường
  bộ từ vị trí người dùng qua OSRM. Điểm xuất phát ngoài Việt Nam trả
  `422 ORIGIN_OUT_OF_RANGE`; không có tuyến trả `422 ROUTE_NOT_FOUND`; OSRM lỗi
  hoặc quá thời gian chờ trả `503 ROUTING_UNAVAILABLE`.
- `GET /products/{slug}` bổ sung `related_locations`: các điểm du lịch đã duyệt có
  giới thiệu sản phẩm.

### Khai báo và duyệt điểm du lịch đã triển khai

- Chủ thể đã duyệt tạo bản nháp tại `POST /subject/locations` (chỉ cần `name`, `type`),
  lưu dần bằng `PATCH /subject/locations/{id}` và gửi duyệt bằng
  `POST /subject/locations/{id}/submit`. Chỉ `draft` và `needs_revision` được sửa/gửi;
  `rejected` là kết thúc (được xóa, khai báo lại thành điểm mới).
- Vị trí gửi kèm `latitude`, `longitude` và `location_source`
  (`map_pin`, `device_gps`, `coordinates`, `google_maps_link`); `location_accuracy_m`
  chỉ dùng với `device_gps`.
- `GET /subject/locations/position-check?latitude=&longitude=&exclude_id=`: vị trí có
  nằm trong khung tỉnh Lâm Đồng không, điểm đã duyệt gần nhất và cảnh báo trùng khi
  cách dưới 200 m (chỉ cảnh báo, không chặn).
- `POST /subject/locations/parse-coordinates` `{text}`: đọc tọa độ thập phân,
  độ-phút-giây hoặc link Google Maps đầy đủ. Link rút gọn trả
  `422 SHORT_MAPS_LINK_UNSUPPORTED`.
- Gửi duyệt cần đủ vị trí, xã/phường, địa chỉ, mô tả ≥ 40 ký tự và đúng một ảnh chính;
  thiếu trả `422 LOCATION_SUBMISSION_INCOMPLETE` kèm `missing_fields`; ngoài tỉnh trả
  `422 LOCATION_OUTSIDE_LAM_DONG`.
- Ảnh tải lên tại `POST /subject/location-images` (JPEG/PNG/WebP ≤ 5 MB); ảnh tạm xóa bằng
  `DELETE /subject/location-images/{file}`. Nơi lưu theo biến `IMAGE_STORAGE`: `local` phục vụ ở
  `/uploads/locations/...`, `cloudinary` trả đường dẫn https của Cloudinary trong `image_url`
  (`storage_path` vẫn dạng `locations/<chủ thể>/<uuid>.<đuôi>`). Cloudinary lỗi trả
  `502 IMAGE_STORAGE_UNAVAILABLE`. Ảnh sản phẩm (`POST /subject/product-images`) làm tương tự.
- Ảnh trong `GET /locations/{slug}` và `GET /products/{slug}` có thêm `source_url`, `credit`, `license`
  (có thể `null`): ảnh lấy từ web để minh họa ghi nguồn, tác giả và giấy phép; trang công khai nên hiện
  chú thích "Ảnh minh họa" kèm `credit` khi các trường này có giá trị. Ảnh chủ thể tự tải lên để trống.
- `product_ids` chỉ nhận sản phẩm OCOP đã duyệt của chính chủ thể.
- Admin xem hàng đợi `GET /admin/locations` (lọc `status`, `origin=subject|import`,
  `type`, `location_source`, `search`; có `status_counts`) và xử lý
  `PATCH /admin/locations/{id}/moderation` `{status, note, latitude?, longitude?}`.
  Tọa độ admin chỉnh được ghi vào ghi chú duyệt để chủ thể biết.
- Điểm đã duyệt: `POST /subject/locations/{id}/change-requests` (gửi đủ thông tin mới)
  hoặc `/deletion-requests` (lý do); điểm cũ vẫn hiển thị tới khi admin duyệt tại
  `PATCH /admin/location-change-requests/{id}/moderation`. Ngừng hiển thị chuyển điểm
  sang `archived`. Yêu cầu tạo trước khi điểm đổi phiên bản trả
  `409 LOCATION_VERSION_CONFLICT`.

## Quy trình trạng thái

- Hồ sơ subject: user tạo `pending`; admin chuyển `approved/rejected`. Khi approved,
  backend tự cấp role `subject`; khi rejected tự trả về role `user`.
- Sản phẩm mới đi qua draft -> pending -> approved. Sản phẩm đã duyệt sử dụng
  yêu cầu thay đổi riêng. Điểm du lịch dùng cùng quy trình (mục trên).
- Review mới luôn `pending`; chỉ review `approved` được tính vào `rating_avg`.
- News dùng `draft/published/archived`; `published_at` được backend quản lý.

