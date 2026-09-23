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

## Quy trình trạng thái

- Hồ sơ subject: user tạo `pending`; admin chuyển `approved/rejected`. Khi approved,
  backend tự cấp role `subject`; khi rejected tự trả về role `user`.
- Sản phẩm mới đi qua draft -> pending -> approved. Sản phẩm đã duyệt sử dụng
  yêu cầu thay đổi riêng; địa điểm sẽ được hoàn thiện ở module sau.
- Review mới luôn `pending`; chỉ review `approved` được tính vào `rating_avg`.
- News dùng `draft/published/archived`; `published_at` được backend quản lý.

