# Nhật ký thay đổi

Các thay đổi đáng chú ý của dự án. Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/).

## [Chưa phát hành] — nhánh `2312682_HaLuyen_HoanThienDuAn`

### Thêm

- SEO: `robots.txt`, `sitemap.xml` (trang tĩnh + sản phẩm + điểm du lịch công khai), thẻ meta/Open Graph/Twitter Card/canonical theo từng trang, `noindex` cho khu riêng tư, dữ liệu có cấu trúc JSON-LD (`Product`, `TouristAttraction`); trang HTML tĩnh cho bot Facebook/Zalo không chạy JavaScript.
- CI GitHub Actions (backend + PostGIS, dữ liệu, frontend, database khớp repo, tài liệu API, build image) và workflow triển khai tay qua SSH.
- Bản chạy thật: `docker-compose.prod.yml`, `backend/Dockerfile.prod`, `frontend/Dockerfile.prod`, cấu hình Nginx (proxy API, cache, header bảo mật, giới hạn đăng nhập), `.env.production.example`, script triển khai và sao lưu.
- Đánh giá sản phẩm và điểm du lịch: viết, sửa, xóa; quản trị viên duyệt/từ chối có lý do; điểm trung bình tự tính lại; trang "Đánh giá của tôi".
- Quản trị viên quản lý người dùng (tìm kiếm, lọc, khóa/mở khóa) và danh mục (thêm, sửa, ẩn/hiện, sắp xếp, xóa danh mục rỗng).
- Đăng nhập, đăng ký nhanh bằng Google và Facebook; liên kết/bỏ liên kết trong trang Tài khoản.
- Đổi mật khẩu; đặt mật khẩu cho tài khoản tạo bằng mạng xã hội.
- Chủ thể sửa trực tiếp thông tin liên hệ của đơn vị.
- Giới hạn đăng nhập sai (5 lần/15 phút mỗi email, 20 lần/15 phút mỗi IP).
- Tổng quan quản trị đếm sản phẩm thực sự hiển thị công khai; hàng đợi đánh giá chờ duyệt.
- Tiêu đề thẻ trình duyệt cho từng trang, link bỏ qua điều hướng, hiệu ứng chuyển trang nhẹ (tôn trọng giảm chuyển động), trạng thái lỗi có nút "Thử lại" ở mọi trang.
- `PUBLIC_BASE_URL` cho URL ảnh khi chạy sau proxy; favicon.
- Migration tổng hợp `014_hoan_thien.sql`; công cụ kiểm tra database so cả kiểu cột, ràng buộc, index.
- `tools/sinh_tai_lieu_api.py` sinh `docs/API.md` (103 endpoint) và bộ Postman từ OpenAPI.

### Sửa

- Chân trang không còn nhảy xuống khi nội dung trang công khai tải xong (CLS từ 0,8 về 0); font Google nạp không chặn hiển thị.
- Test seed ảnh Dehavi (chỉ chạy với PostGIS tạm) lệch vì lượt xem tăng giữa hai lần chạy.
- Trang duyệt hồ sơ chủ thể lỗi 500 với dữ liệu loại chủ thể `company`; lỗi 500 trả JSON có CORS.
- Backend từ chối khởi động khi `JWT_SECRET_KEY` là giá trị mẫu.
- Tin tức: không giữ khóa khi gọi mạng, dùng bản cũ khi nguồn lỗi.
- Không xóa được ảnh/chứng nhận đang dùng trong yêu cầu thay đổi đang chờ.
- Trang công khai trống với bộ seed chuẩn; nội dung chủ thể bị khóa ẩn khỏi trang công khai.
- Tài khoản bị khóa kết thúc phiên ngay; trang đăng ký chủ thể tự cập nhật khi được duyệt.
- Không tạo bản nháp trùng khi gửi duyệt lỗi; thời gian chờ tải file 120 giây; số điện thoại đúng định dạng.
- Lưu sản phẩm/điểm không báo nhầm "Không tìm thấy file ảnh" sau khi đổi nơi lưu ảnh.
- Tìm kiếm hiểu `%`, `_` theo nghĩa đen; lượt xem trang chi tiết được ghi nhận và không làm đổi `updated_at`.
- PostgreSQL và pgAdmin chỉ mở trên `127.0.0.1`.

### Thay đổi

- Tài liệu gộp còn 5 file trong `docs/` (nghiệp vụ, API, kiến trúc, dữ liệu, cấu hình); README viết lại. Kế hoạch đồ án, nhật ký giao diện và các file Word chuyển ra thư mục đồ án ngoài repo.
- Migration 001–013 chuyển vào `database/migrations/archive/`.

## Các mốc trước

| Ngày | Nội dung | PR |
|---|---|---|
| 15/10/2026 | Sửa lỗi lưu ảnh sau khi đổi nơi lưu | #14 |
| 10/10/2026 | Trải nghiệm sản phẩm OCOP, dữ liệu và ảnh Dehavi | #12 |
| 07/10/2026 | Viết lại README | #13 |
| 06/10/2026 | Lưu ảnh Cloudinary, nguồn/giấy phép ảnh (migration 012) | #11 |
| 28/09/2026 | Chủ thể khai báo điểm du lịch, admin duyệt (migration 009–011) | #7 |
| 24/09/2026 | Bản đồ số và điểm du lịch (migration 008) | #2 |
