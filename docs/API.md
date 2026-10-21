# Tài liệu REST API

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

## Mã lỗi

Mã lỗi hay gặp:

| Mã | Ý nghĩa |
|---|---|
| `VALIDATION_ERROR` | Dữ liệu gửi lên không hợp lệ; `details` liệt kê từng trường. |
| `INVALID_TOKEN` | Thiếu, sai hoặc hết hạn access token (401). |
| `INVALID_CREDENTIALS` | Sai email hoặc mật khẩu. |
| `TOO_MANY_LOGIN_ATTEMPTS` | Sai mật khẩu quá nhiều lần; xem header `Retry-After` (429). |
| `ACCOUNT_INACTIVE` | Tài khoản đã bị khóa (403); frontend kết thúc phiên. |
| `INSUFFICIENT_PERMISSIONS` | Vai trò không có quyền (403). |
| `APPROVED_SUBJECT_REQUIRED` | Cần hồ sơ chủ thể đã được duyệt. |
| `DATABASE_UNAVAILABLE` | Không kết nối được database (503). |
| `DATABASE_SCHEMA_OUTDATED` | Database chưa chạy migration mới nhất (503). |
| `INTERNAL_ERROR` | Lỗi không lường trước (500). |
| `SOCIAL_EMAIL_EXISTS` | Email Google/Facebook đã có tài khoản: đăng nhập bằng mật khẩu rồi liên kết. |
| `CATEGORY_HIDDEN` | Không tạo sản phẩm mới vào danh mục đang ẩn. |
| `CATEGORY_IN_USE` | Không xóa danh mục còn sản phẩm. |
| `LAST_ACTIVE_ADMIN` | Không khóa quản trị viên còn hoạt động cuối cùng. |
| `CANNOT_LOCK_SELF` | Không tự khóa tài khoản của mình. |
| `OWN_TARGET_REVIEW_FORBIDDEN` | Chủ thể không tự đánh giá sản phẩm/điểm của đơn vị mình. |
| `REVIEW_ALREADY_EXISTS` | Mỗi người một đánh giá cho mỗi sản phẩm/điểm. |
| `PRODUCT_VERSION_CONFLICT` | Dữ liệu đã bị người khác sửa; tải lại rồi thao tác lại. |
| `PRODUCT_SUBMISSION_INCOMPLETE` | Thiếu thông tin bắt buộc để gửi duyệt (`details` liệt kê). |
| `LOCATION_OUTSIDE_LAM_DONG` | Vị trí nằm ngoài tỉnh Lâm Đồng. |
| `ROUTING_UNAVAILABLE` | Dịch vụ chỉ đường không phản hồi (503). |
| `NEWS_SOURCE_UNAVAILABLE` | Không tải được RSS và chưa có bản lưu (503). |

Toàn bộ mã lỗi theo nhóm (thông báo chi tiết nằm trong trường `message`):

- **Chung:** `DATABASE_ERROR`, `DATABASE_SCHEMA_OUTDATED`, `DATABASE_UNAVAILABLE`, `INSUFFICIENT_PERMISSIONS`, `INTERNAL_ERROR`, `INVALID_TOKEN`, `ROLE_CONFIGURATION_ERROR`, `VALIDATION_ERROR`
- **Tài khoản:** `ACCOUNT_INACTIVE`, `CANNOT_LOCK_SELF`, `CURRENT_PASSWORD_REQUIRED`, `EMAIL_ALREADY_EXISTS`, `INVALID_CREDENTIALS`, `INVALID_CURRENT_PASSWORD`, `LAST_ACTIVE_ADMIN`, `PASSWORD_UNCHANGED`, `SOCIAL_ACCOUNT_CONFLICT`, `SOCIAL_ACCOUNT_IN_USE`, `SOCIAL_ACCOUNT_NOT_LINKED`, `SOCIAL_AUTH_FAILED`, `SOCIAL_EMAIL_EXISTS`, `SOCIAL_EMAIL_REQUIRED`, `SOCIAL_EMAIL_UNVERIFIED`, `SOCIAL_LOGIN_NOT_ALLOWED`, `SOCIAL_PKCE_REQUIRED`, `SOCIAL_PROVIDER_DISABLED`, `SOCIAL_PROVIDER_UNAVAILABLE`, `SOCIAL_UNLINK_LAST_METHOD`, `TOO_MANY_LOGIN_ATTEMPTS`, `USER_NOT_FOUND`
- **Chủ thể:** `APPROVED_SUBJECT_CANNOT_RESUBMIT`, `APPROVED_SUBJECT_REQUIRED`, `INACTIVE_APPLICANT`, `SUBJECT_APPLICANT_NOT_FOUND`, `SUBJECT_APPLICATION_ALREADY_EXISTS`, `SUBJECT_APPLICATION_ALREADY_REVIEWED`, `SUBJECT_APPLICATION_CONFLICT`, `SUBJECT_APPLICATION_NOT_ALLOWED`, `SUBJECT_APPLICATION_NOT_FOUND`, `SUBJECT_IDENTITY_LOCKED`
- **Sản phẩm, chứng nhận, ảnh:** `ACTIVE_PRODUCT_CHANGE_REQUEST_EXISTS`, `APPROVED_PRODUCT_REQUIRED`, `CERTIFICATE_EXPIRED`, `CERTIFICATE_NOT_ACTIVE`, `CERTIFICATE_TOO_LARGE`, `DATA_SOURCE_NOT_FOUND`, `DATA_SOURCE_URL_EXISTS`, `DELETION_REASON_REQUIRED`, `IMAGE_STORAGE_UNAVAILABLE`, `IMAGE_TOO_LARGE`, `INVALID_CERTIFICATE_CONTENT`, `INVALID_CERTIFICATE_DATES`, `INVALID_CERTIFICATE_TYPE`, `INVALID_IMAGE_CONTENT`, `INVALID_IMAGE_TYPE`, `INVALID_PRICE_RANGE`, `PRODUCT_ALREADY_REVIEWED`, `PRODUCT_CANNOT_BE_DELETED`, `PRODUCT_CANNOT_BE_SUBMITTED`, `PRODUCT_CERTIFICATE_FILE_MISSING`, `PRODUCT_CERTIFICATE_IN_USE`, `PRODUCT_CERTIFICATE_NOT_FOUND`, `PRODUCT_CERTIFICATE_NOT_OWNED`, `PRODUCT_CHANGE_REQUEST_ALREADY_REVIEWED`, `PRODUCT_CHANGE_REQUEST_CANNOT_BE_CANCELLED`, `PRODUCT_CHANGE_REQUEST_CONFLICT`, `PRODUCT_CHANGE_REQUEST_NOT_EDITABLE`, `PRODUCT_CHANGE_REQUEST_NOT_FOUND`, `PRODUCT_CONFLICT`, `PRODUCT_EVIDENCE_LINK_EXISTS`, `PRODUCT_EVIDENCE_LINK_NOT_FOUND`, `PRODUCT_FOR_CHANGE_REQUEST_NOT_FOUND`, `PRODUCT_IMAGE_NOT_FOUND`, `PRODUCT_IMAGE_NOT_OWNED`, `PRODUCT_NAME_REQUIRED`, `PRODUCT_NOT_EDITABLE`, `PRODUCT_NOT_FOUND`, `PRODUCT_NOT_PUBLIC`, `PRODUCT_SUBJECT_INACTIVE`, `PRODUCT_SUBMISSION_INCOMPLETE`, `PRODUCT_UPDATE_CONFLICT`, `PRODUCT_VERSION_CONFLICT`, `PROPOSED_PRODUCT_DATA_REQUIRED`, `REJECTION_REASON_REQUIRED`
- **Điểm du lịch, bản đồ:** `ACTIVE_LOCATION_CHANGE_REQUEST_EXISTS`, `APPROVED_LOCATION_REQUIRED`, `INVALID_COORDINATES`, `LOCATION_ALREADY_REVIEWED`, `LOCATION_CANNOT_BE_DELETED`, `LOCATION_CANNOT_BE_SUBMITTED`, `LOCATION_CHANGE_REQUEST_ALREADY_REVIEWED`, `LOCATION_CHANGE_REQUEST_CANNOT_BE_CANCELLED`, `LOCATION_CHANGE_REQUEST_CONFLICT`, `LOCATION_CHANGE_REQUEST_NOT_EDITABLE`, `LOCATION_CHANGE_REQUEST_NOT_FOUND`, `LOCATION_CONFLICT`, `LOCATION_FOR_CHANGE_REQUEST_NOT_FOUND`, `LOCATION_IMAGE_NOT_FOUND`, `LOCATION_IMAGE_NOT_OWNED`, `LOCATION_IMAGE_USED_ELSEWHERE`, `LOCATION_MODERATION_CONFLICT`, `LOCATION_NOT_EDITABLE`, `LOCATION_NOT_FOUND`, `LOCATION_NOT_PUBLIC`, `LOCATION_OUTSIDE_LAM_DONG`, `LOCATION_PRODUCT_INVALID`, `LOCATION_SUBJECT_INACTIVE`, `LOCATION_SUBMISSION_INCOMPLETE`, `LOCATION_UPDATE_CONFLICT`, `LOCATION_VERSION_CONFLICT`, `MAPS_LINK_WITHOUT_COORDINATES`, `ORIGIN_OUT_OF_RANGE`, `PROPOSED_LOCATION_DATA_REQUIRED`, `ROUTE_NOT_FOUND`, `ROUTING_UNAVAILABLE`, `SHORT_MAPS_LINK_UNSUPPORTED`
- **Danh mục, đánh giá, tin tức:** `ADMIN_CANNOT_REVIEW`, `CATEGORY_CONFLICT`, `CATEGORY_HIDDEN`, `CATEGORY_IN_USE`, `CATEGORY_NAME_EXISTS`, `CATEGORY_NOT_FOUND`, `CATEGORY_REQUIRED`, `CATEGORY_SLUG_EXISTS`, `NEWS_SOURCE_UNAVAILABLE`, `OWN_TARGET_REVIEW_FORBIDDEN`, `REVIEW_ALREADY_EXISTS`, `REVIEW_ALREADY_MODERATED`, `REVIEW_FORBIDDEN`, `REVIEW_NOT_FOUND`

## Danh sách endpoint (103)

### Hệ thống

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/health/database` | Công khai | Kiểm tra kết nối database. |
| `GET` | `/health` | Công khai | Kiểm tra API đang chạy. |

### Tài khoản và xác thực

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `POST` | `/auth/change-password` | Đã đăng nhập | Đổi mật khẩu; tài khoản tạo bằng Google/Facebook (chưa có mật khẩu) thì đặt mật khẩu lần đầu. |
| `POST` | `/auth/login` | Công khai | Đăng nhập, nhận access token (JWT). Sai quá nhiều lần trả 429. |
| `GET` | `/auth/me` | Đã đăng nhập | Thông tin tài khoản đang đăng nhập (kèm has_password, social_providers). |
| `PATCH` | `/auth/me` | Đã đăng nhập | Sửa họ tên, số điện thoại, ảnh đại diện. |
| `POST` | `/auth/register` | Công khai | Đăng ký tài khoản người dùng bằng email và mật khẩu. |
| `GET` | `/auth/social/providers` | Công khai | Nhà cung cấp đã khai báo khóa; frontend chỉ hiện nút của các nhà cung cấp này. |
| `DELETE` | `/auth/social/{provider}` | Đã đăng nhập | Bỏ liên kết; không cho bỏ nếu đó là cách đăng nhập duy nhất (tài khoản chưa có mật khẩu). |
| `POST` | `/auth/social/{provider}/authorize` | Công khai | Tạo địa chỉ trang đăng nhập Google/Facebook (state do frontend tạo; Google cần PKCE). |
| `POST` | `/auth/social/{provider}/callback` | Công khai | Hoàn tất đăng nhập Google/Facebook, nhận JWT. |
| `POST` | `/auth/social/{provider}/link` | Đã đăng nhập | Người dùng đang đăng nhập liên kết thêm Google/Facebook (bước cuối của luồng như /callback). |

### Danh mục (công khai)

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/categories` | Công khai | Danh mục đang hiển thị, sắp theo thứ tự. |
| `GET` | `/categories/{slug}` | Công khai | Chi tiết danh mục. |

### Sản phẩm (công khai)

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/products` | Công khai | Danh sách sản phẩm công khai: tìm kiếm, lọc nhóm, hạng sao, địa bàn, giá; sắp xếp; phân trang. |
| `GET` | `/products/filter-options` | Công khai | Giá trị cho bộ lọc sản phẩm (địa bàn). |
| `GET` | `/products/{slug}` | Công khai | Chi tiết sản phẩm công khai (tăng lượt xem). |

### Điểm du lịch (công khai)

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/locations` | Công khai | Danh sách điểm du lịch công khai. |
| `GET` | `/locations/filter-options` | Công khai | Giá trị cho bộ lọc điểm du lịch (loại hình, địa bàn). |
| `GET` | `/locations/{slug}` | Công khai | Chi tiết điểm du lịch công khai (tăng lượt xem). |

### Bản đồ số

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/map/locations` | Công khai | Trả các điểm đã duyệt dưới dạng GeoJSON FeatureCollection. |
| `GET` | `/map/nearby` | Công khai | Tìm điểm đã duyệt gần nhất trong bán kính, sắp xếp theo khoảng cách. |
| `GET` | `/map/route` | Công khai | Gợi ý tuyến đường bộ từ vị trí người dùng tới một điểm du lịch đã duyệt. |

### Tin tức

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/news` | Công khai | Tin tức lấy từ RSS cổng OCOP tỉnh (có bộ nhớ đệm). |

### Đánh giá

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/locations/{location_id}/reviews` | Công khai | Đánh giá đã duyệt của điểm du lịch, kèm tóm tắt điểm. |
| `POST` | `/locations/{location_id}/reviews` | Đã đăng nhập | Viết đánh giá điểm du lịch (chờ duyệt). |
| `GET` | `/products/{product_id}/reviews` | Công khai | Đánh giá đã duyệt của sản phẩm, kèm tóm tắt điểm. |
| `POST` | `/products/{product_id}/reviews` | Đã đăng nhập | Viết đánh giá sản phẩm (chờ duyệt). |
| `GET` | `/reviews/me` | Đã đăng nhập | Mọi đánh giá của tài khoản hiện tại; lọc theo product_id/location_id để biết đã đánh giá chưa. |
| `PATCH` | `/reviews/{review_id}` | Đã đăng nhập | Sửa đánh giá của tôi (quay về chờ duyệt). |
| `DELETE` | `/reviews/{review_id}` | Đã đăng nhập | Xóa đánh giá của tôi. |

### Hồ sơ đăng ký chủ thể

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `POST` | `/subject-applications` | Đã đăng nhập | Gửi hồ sơ đăng ký trở thành chủ thể OCOP. |
| `GET` | `/subject-applications/me` | Đã đăng nhập | Xem hồ sơ chủ thể của tôi và kết quả duyệt. |
| `PUT` | `/subject-applications/me` | Đã đăng nhập | Sửa và gửi lại hồ sơ bị từ chối. |

### Khu chủ thể

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/subject/location-change-requests` | Chủ thể đã duyệt | Yêu cầu cập nhật điểm du lịch của tôi. |
| `GET` | `/subject/location-change-requests/{request_id}` | Chủ thể đã duyệt | Chi tiết yêu cầu cập nhật điểm du lịch. |
| `PUT` | `/subject/location-change-requests/{request_id}` | Chủ thể đã duyệt | Sửa và gửi lại yêu cầu cần bổ sung. |
| `POST` | `/subject/location-change-requests/{request_id}/cancel` | Chủ thể đã duyệt | Hủy yêu cầu cập nhật đang chờ. |
| `POST` | `/subject/location-images` | Chủ thể đã duyệt | Tải ảnh điểm du lịch. |
| `DELETE` | `/subject/location-images/{file_name}` | Chủ thể đã duyệt | Xóa ảnh điểm du lịch chưa gắn vào điểm. |
| `GET` | `/subject/locations` | Chủ thể đã duyệt | Điểm du lịch của tôi. |
| `POST` | `/subject/locations` | Chủ thể đã duyệt | Tạo bản nháp điểm du lịch. |
| `POST` | `/subject/locations/parse-coordinates` | Chủ thể đã duyệt | Đọc tọa độ dán vào (thập phân hoặc độ-phút-giây) hay link Google Maps đầy đủ. |
| `GET` | `/subject/locations/position-check` | Chủ thể đã duyệt | Kiểm tra ghim ngay khi chủ thể chọn vị trí: trong tỉnh chưa, có điểm đã duyệt nào quá gần không. |
| `GET` | `/subject/locations/{location_id}` | Chủ thể đã duyệt | Chi tiết điểm du lịch của tôi. |
| `PATCH` | `/subject/locations/{location_id}` | Chủ thể đã duyệt | Lưu bản nháp điểm du lịch. |
| `DELETE` | `/subject/locations/{location_id}` | Chủ thể đã duyệt | Xóa điểm du lịch chưa được duyệt. |
| `POST` | `/subject/locations/{location_id}/change-requests` | Chủ thể đã duyệt | Gửi yêu cầu cập nhật điểm đã duyệt. |
| `POST` | `/subject/locations/{location_id}/deletion-requests` | Chủ thể đã duyệt | Gửi yêu cầu ngừng hiển thị điểm đã duyệt. |
| `POST` | `/subject/locations/{location_id}/submit` | Chủ thể đã duyệt | Gửi điểm du lịch để quản trị viên duyệt. |
| `POST` | `/subject/product-certificates` | Chủ thể đã duyệt | Tải giấy chứng nhận OCOP (PDF, JPG, PNG; tối đa 10 MB; riêng tư). |
| `GET` | `/subject/product-certificates/products/{product_id}` | Chủ thể đã duyệt | Tải giấy chứng nhận của sản phẩm của tôi. |
| `DELETE` | `/subject/product-certificates/{file_name}` | Chủ thể đã duyệt | Xóa giấy chứng nhận vừa tải chưa gắn vào sản phẩm. |
| `GET` | `/subject/product-change-requests` | Chủ thể đã duyệt | Yêu cầu thay đổi sản phẩm của tôi. |
| `GET` | `/subject/product-change-requests/{request_id}` | Chủ thể đã duyệt | Chi tiết yêu cầu thay đổi sản phẩm. |
| `PUT` | `/subject/product-change-requests/{request_id}` | Chủ thể đã duyệt | Sửa và gửi lại yêu cầu cần bổ sung. |
| `POST` | `/subject/product-change-requests/{request_id}/cancel` | Chủ thể đã duyệt | Hủy yêu cầu thay đổi đang chờ. |
| `POST` | `/subject/product-images` | Chủ thể đã duyệt | Tải ảnh sản phẩm (JPG, PNG, WebP; tối đa 5 MB). |
| `DELETE` | `/subject/product-images/{file_name}` | Chủ thể đã duyệt | Xóa ảnh vừa tải chưa gắn vào sản phẩm. |
| `GET` | `/subject/products` | Chủ thể đã duyệt | Sản phẩm của tôi (mọi trạng thái). |
| `POST` | `/subject/products` | Chủ thể đã duyệt | Tạo bản nháp sản phẩm. |
| `GET` | `/subject/products/{product_id}` | Chủ thể đã duyệt | Chi tiết sản phẩm của tôi. |
| `PUT` | `/subject/products/{product_id}` | Chủ thể đã duyệt | Lưu toàn bộ bản nháp sản phẩm. |
| `PATCH` | `/subject/products/{product_id}` | Chủ thể đã duyệt | Lưu một phần bản nháp sản phẩm. |
| `DELETE` | `/subject/products/{product_id}` | Chủ thể đã duyệt | Xóa sản phẩm chưa được duyệt. |
| `POST` | `/subject/products/{product_id}/change-requests` | Chủ thể đã duyệt | Gửi yêu cầu sửa sản phẩm đã duyệt. |
| `POST` | `/subject/products/{product_id}/deletion-requests` | Chủ thể đã duyệt | Gửi yêu cầu ngừng hiển thị sản phẩm đã duyệt. |
| `POST` | `/subject/products/{product_id}/submit` | Chủ thể đã duyệt | Gửi sản phẩm để quản trị viên duyệt. |
| `GET` | `/subject/profile` | Chủ thể đã duyệt | Thông tin đơn vị của chủ thể. |
| `PATCH` | `/subject/profile` | Chủ thể đã duyệt | Sửa thông tin liên hệ của đơn vị (tên, loại, mã số thuế do admin sửa). |

### Quản trị

| Method | Đường dẫn | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/admin/access` | Quản trị viên | Xác nhận JWT hiện tại thuộc một tài khoản admin đang hoạt động. |
| `GET` | `/admin/categories` | Quản trị viên | Danh sách danh mục, gồm cả danh mục ẩn và số sản phẩm. |
| `POST` | `/admin/categories` | Quản trị viên | Thêm danh mục. |
| `PATCH` | `/admin/categories/{category_id}` | Quản trị viên | Sửa, ẩn/hiện, đổi thứ tự danh mục. |
| `DELETE` | `/admin/categories/{category_id}` | Quản trị viên | Xóa danh mục chưa có sản phẩm. |
| `GET` | `/admin/dashboard` | Quản trị viên | Số liệu tổng quan và hàng đợi việc cần duyệt. |
| `GET` | `/admin/data-sources` | Quản trị viên | Danh sách nguồn dữ liệu (văn bản, trang thông tin). |
| `POST` | `/admin/data-sources` | Quản trị viên | Thêm nguồn dữ liệu. |
| `PATCH` | `/admin/data-sources/{source_id}` | Quản trị viên | Sửa nguồn dữ liệu. |
| `GET` | `/admin/location-change-requests` | Quản trị viên | Danh sách yêu cầu cập nhật/ngừng hiển thị điểm du lịch. |
| `GET` | `/admin/location-change-requests/{request_id}` | Quản trị viên | Chi tiết yêu cầu cập nhật điểm du lịch. |
| `PATCH` | `/admin/location-change-requests/{request_id}/moderation` | Quản trị viên | Duyệt hoặc từ chối yêu cầu cập nhật điểm du lịch. |
| `GET` | `/admin/locations` | Quản trị viên | Danh sách điểm du lịch để kiểm duyệt. |
| `GET` | `/admin/locations/{location_id}` | Quản trị viên | Chi tiết điểm du lịch để kiểm duyệt. |
| `PATCH` | `/admin/locations/{location_id}/moderation` | Quản trị viên | Duyệt (có thể chỉnh ghim), yêu cầu bổ sung hoặc từ chối điểm du lịch. |
| `GET` | `/admin/product-change-requests` | Quản trị viên | Danh sách yêu cầu sửa/ngừng hiển thị sản phẩm. |
| `GET` | `/admin/product-change-requests/{request_id}` | Quản trị viên | Chi tiết yêu cầu, so sánh với sản phẩm hiện tại. |
| `PATCH` | `/admin/product-change-requests/{request_id}/moderation` | Quản trị viên | Duyệt, yêu cầu bổ sung hoặc từ chối yêu cầu thay đổi sản phẩm. |
| `GET` | `/admin/products` | Quản trị viên | Danh sách sản phẩm để kiểm duyệt. |
| `GET` | `/admin/products/{product_id}` | Quản trị viên | Chi tiết sản phẩm để kiểm duyệt. |
| `GET` | `/admin/products/{product_id}/certificate` | Quản trị viên | Tải giấy chứng nhận OCOP của sản phẩm (file riêng tư). |
| `GET` | `/admin/products/{product_id}/evidence` | Quản trị viên | Các nguồn chứng cứ gắn với sản phẩm. |
| `POST` | `/admin/products/{product_id}/evidence` | Quản trị viên | Gắn nguồn chứng cứ (quyết định công nhận, trang thông tin) cho sản phẩm. |
| `PATCH` | `/admin/products/{product_id}/evidence/{source_id}/{evidence_role}` | Quản trị viên | Sửa liên kết nguồn chứng cứ. |
| `DELETE` | `/admin/products/{product_id}/evidence/{source_id}/{evidence_role}` | Quản trị viên | Bỏ liên kết nguồn chứng cứ. |
| `PATCH` | `/admin/products/{product_id}/moderation` | Quản trị viên | Duyệt, yêu cầu bổ sung hoặc từ chối sản phẩm. |
| `GET` | `/admin/reviews` | Quản trị viên | Danh sách đánh giá để kiểm duyệt. |
| `PATCH` | `/admin/reviews/{review_id}/moderation` | Quản trị viên | Duyệt hoặc từ chối (kèm lý do) đánh giá. |
| `GET` | `/admin/statistics` | Quản trị viên | Số liệu thống kê toàn cổng cho trang tổng quan quản trị (chỉ đọc). |
| `GET` | `/admin/subject-applications` | Quản trị viên | Danh sách hồ sơ chủ thể (lọc trạng thái, tìm kiếm, phân trang). |
| `PATCH` | `/admin/subject-applications/{application_id}/moderation` | Quản trị viên | Duyệt hoặc từ chối (kèm lý do) hồ sơ chủ thể. |
| `GET` | `/admin/users` | Quản trị viên | Danh sách tài khoản (tìm theo email/tên, lọc vai trò, trạng thái). |
| `PATCH` | `/admin/users/{user_id}/status` | Quản trị viên | Khóa hoặc mở khóa tài khoản. |
