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
| Public | `GET /categories`, `GET /products`, `GET /products/{slug}` | Public |
| Public | `GET /locations`, `GET /locations/{slug}` | Public |
| Public | `GET /news`, `GET /news/{slug}` | Public |
| Reviews | `GET/POST /products/{id}/reviews`, `GET/POST /locations/{id}/reviews` | GET public, POST đăng nhập |
| Reviews | `PATCH/DELETE /reviews/{id}` | Chính chủ, chỉ khi pending |
| Map | `GET /map/locations`, `GET /map/nearby`, `GET /map/route` | Public |
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

## Quy trình trạng thái

- Hồ sơ subject: user tạo `pending`; admin chuyển `approved/rejected`. Khi approved,
  backend tự cấp role `subject`; khi rejected tự trả về role `user`.
- Product/location do subject tạo hoặc sửa luôn về `pending`.
- Review mới luôn `pending`; chỉ review `approved` được tính vào `rating_avg`.
- News dùng `draft/published/archived`; `published_at` được backend quản lý.

