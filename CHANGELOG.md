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
- Hiệu ứng chờ tải trang: thanh tiến trình trên đầu khi chuyển trang hoặc chờ API (hiện sau 150 ms để không nhấp nháy), khung xương trang cho lần mở đầu, thông báo ngoại tuyến/đã kết nối lại, thông báo "Chưa mở được trang" kèm nút Thử lại khi tải mã trang thất bại (tự tải lại một lần nếu nghi bản mới vừa triển khai), trang lỗi chung "Đã xảy ra sự cố" khi giao diện gặp lỗi khi dựng.
- Trang 404 hiện địa chỉ đã mở, lối về đúng khu (quản trị/chủ thể), nút Quay lại và ô tìm sản phẩm; trang 403 dùng chung khung với 404 và 500.
- Logo thương hiệu mới (biểu tượng + logo đầy đủ) ở đầu trang, chân trang (logo lớn), cột trái đăng nhập/đăng ký (khối thương hiệu cùng kiểu header, biểu tượng mờ chìm làm hình nền), tấm logo kính mờ ở trang chủ, trang lỗi, màn hình chờ tải, khu quản trị/chủ thể, favicon và ảnh chia sẻ.
- Hộp xác nhận dùng chung (`ConfirmDialog`) thay `window.confirm`; thông báo thành công/lỗi sau thao tác tự cuộn vào khung nhìn; chú giải bản đồ bấm để lọc loại hình; bộ lọc bản đồ và bộ lọc quản trị sản phẩm lưu trên URL; liên kết từ số liệu tổng quan mở đúng danh sách đã lọc.
- Tài liệu `docs/ux-ui-audit.md`, `docs/ux-ui-improvement-plan.md`, `docs/design-system.md`, `docs/ux-ui-improvement-report.md`.
- `PUBLIC_BASE_URL` cho URL ảnh khi chạy sau proxy; favicon.
- Migration tổng hợp `014_hoan_thien.sql`; công cụ kiểm tra database so cả kiểu cột, ràng buộc, index.
- `tools/sinh_tai_lieu_api.py` sinh `docs/API.md` (103 endpoint) và bộ Postman từ OpenAPI.

### Sửa

- Trang đăng nhập/đăng ký vừa màn hình laptop (Windows 125–150%, trình duyệt 100%): không còn tràn theo chiều dọc ở 1536×784 và 1366×650 (đăng nhập); thanh thông báo đầu trang tự gọn khi màn hình thấp; nút Google/Facebook xếp hai cột.
- Thẻ lỗi 404 không còn tràn ngang trên màn hình 375 px.
- Viền focus đặc 3 px, tương phản từ 3:1 trên mọi nền (nền tối dùng màu dã quỳ); tên truy cập của thẻ sản phẩm chứa nội dung nhìn thấy; màu chữ nhãn nhóm sản phẩm đạt 4,5:1.
- Danh sách và chi tiết sản phẩm: không tràn ngang trên điện thoại, ngăn kéo bộ lọc có bẫy phím Tab, biểu mẫu đánh giá đưa focus vào thông báo, liên kết nguồn thành nút "Xem nguồn chính thức", trạng thái tải/lỗi/rỗng nhất quán.
- Bản đồ số: chọn điểm bằng Enter/Space, chọn điểm trên điện thoại cuộn tới thẻ chi tiết, điểm có tọa độ ngoài Lâm Đồng bị bỏ khỏi bản đồ thay vì làm sập, tuyến đường tự thu phóng vừa khung, Esc bỏ chọn, vị trí cuộn của trang đúng khi đổi trang.
- Quản trị và chủ thể: lỗi 422 hiện bằng tiếng Việt theo trường, lỗi duyệt hiện ngay trong modal, danh sách hồ sơ chủ thể dạng thẻ trên điện thoại, menu điện thoại, trang 403 riêng.
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
