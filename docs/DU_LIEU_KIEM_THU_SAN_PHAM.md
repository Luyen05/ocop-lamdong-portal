# Dữ liệu kiểm thử quy trình sản phẩm

## Cảnh báo

Bộ dữ liệu này chỉ dùng cho môi trường phát triển local. Giấy chứng nhận và tài
khoản đều là dữ liệu minh họa, không có giá trị pháp lý. Không chạy file seed
trên môi trường production.

## Cách nạp dữ liệu

Database hiện có cần chạy lần lượt migration 004 đến 007 trước:

    Get-Content .\database\migrations\004_product_moderation.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    Get-Content .\database\migrations\005_add_product_sources.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    Get-Content .\database\migrations\006_simplify_subject_product_flow.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    Get-Content .\database\migrations\007_hide_demo_products.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

Sau đó nạp seed:

    Get-Content .\database\seed_product_workflow.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

File có thể chạy lại và không tạo thêm bản ghi trùng.

## Tài khoản kiểm thử

Mật khẩu chung: **DemoOCOP@2026**

| Vai trò | Email | Trang sau đăng nhập |
|---|---|---|
| Quản trị viên | admin.ocop.demo@example.com | /quan-tri/san-pham |
| Chủ thể đã duyệt | chuthe.ocop.demo@example.com | /chu-the/san-pham |

## Sản phẩm mẫu

| Sản phẩm | Trạng thái | Mục đích kiểm thử |
|---|---|---|
| Trà atiso túi lọc | draft | Chỉnh sửa, xóa bản nháp và gửi duyệt |
| Mứt dâu Đà Lạt | pending | Admin duyệt hiển thị/yêu cầu bổ sung/từ chối |
| Cà phê Arabica | needs_revision | Chủ thể xem phản hồi, sửa và gửi lại |
| Hồng treo gió Đà Lạt | approved | Kiểm tra yêu cầu cập nhật trong khu vực nội bộ |
| Mật ong hoa cà phê | approved | Kiểm tra yêu cầu ngừng hiển thị |
| Bột rau má sấy lạnh | rejected | Chỉnh sửa hồ sơ bị từ chối và gửi lại |

Ngoài các trạng thái trên, seed tạo sẵn:

- Một yêu cầu cập nhật đang chờ duyệt cho sản phẩm hồng treo gió.
- Một yêu cầu ngừng hiển thị đang chờ duyệt cho sản phẩm mật ong.
- Ảnh SVG local cho từng nhóm sản phẩm.
- Giấy chứng nhận SVG có watermark **KHÔNG CÓ GIÁ TRỊ PHÁP LÝ**.

## Kết quả mong đợi

- Chủ thể nhìn thấy 6 sản phẩm thuộc đơn vị của mình.
- Admin nhìn thấy 1 sản phẩm mới ở hàng đợi kiểm duyệt.
- Admin nhìn thấy 2 yêu cầu sửa/ngừng hiển thị.
- Cả sáu sản phẩm đều được đánh dấu `is_demo` và không xuất hiện trên API công
  khai, kể cả khi trạng thái là `approved`.
- Việc duyệt mứt dâu vẫn đổi trạng thái và cho phép kiểm tra đầy đủ quy trình
  chủ thể - quản trị viên trong khu vực nội bộ.
- Sau khi admin duyệt ngừng hiển thị mật ong, sản phẩm chuyển thành archived và
  API công khai trả 404.
