# Dữ liệu kiểm thử quy trình sản phẩm

## Cảnh báo

Bộ dữ liệu này chỉ dùng cho môi trường phát triển local. Giấy chứng nhận và tài
khoản đều là dữ liệu minh họa, không có giá trị pháp lý. Không chạy file seed
trên môi trường production.

## Cách nạp dữ liệu

Database hiện có cần chạy migration 004 trước:

    Get-Content .\database\migrations\004_product_moderation.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

Sau đó nạp dữ liệu:

    Get-Content .\database\seed_product_workflow.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

File seed có thể chạy lại mà không tạo trùng tài khoản, chủ thể, sản phẩm, ảnh
hoặc yêu cầu mẫu.

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
| Hồng treo gió Đà Lạt | approved | Kiểm tra API công khai và yêu cầu cập nhật |
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
- Sản phẩm hồng treo gió và mật ong xuất hiện trên API công khai khi chưa xử lý
  yêu cầu thay đổi.
- Sản phẩm draft, pending, needs_revision và rejected không xuất hiện công khai.
- Sau khi admin duyệt mứt dâu, sản phẩm này xuất hiện ở trang sản phẩm công khai.
- Sau khi admin duyệt ngừng hiển thị mật ong, sản phẩm chuyển thành archived và
  API công khai trả 404.
