# Nhật ký thay đổi

Các thay đổi đáng chú ý của dự án. Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/).

## [Chưa phát hành] — nhánh `2312682_HaLuyen_NangCapBanDo`

### Sửa — rà soát bản đồ số, đợt 2

- Bấm "Chỉ đường" nay hiện khoảng cách, thời gian, nút "Ẩn tuyến" và liên kết Google Maps. Trước đó các mục này, cùng thông báo "ngoài bộ lọc", "chưa có tọa độ" và hướng dẫn khi mở từ liên kết chỉ đường, nằm trong một thẻ bị CSS ẩn.
- Điện thoại: thẻ điểm nằm dưới bản đồ, cao tối đa 60% màn hình, nút luôn thấy.
- Trang chi tiết điểm du lịch: hết lỗi ghi chú ảnh minh họa đẩy phần thông tin xuống dưới; nhãn loại hình đủ tương phản.
- Giảm chữ đậm, bỏ chữ viết hoa và thẻ viền trái màu, mở rộng vùng chạm trên bản đồ và trang chi tiết điểm.

### Thêm

- Tuyến tham quan (giao diện): bản đồ có mục "Tuyến tham quan"; chọn tuyến (URL `tour`) thì chỉ hiện các chặng, nối bằng đường nét đứt theo thứ tự, kèm danh sách chặng có ghi chú; tuyến không còn công khai thì tự bỏ và báo.
- Tuyến tham quan (backend): bảng `tourism_routes`, `tourism_route_stops` (migration `016_tuyen_tham_quan.sql`), `GET /tours` và `GET /tours/{slug}` (chỉ tuyến published, chỉ chặng còn công khai, đúng thứ tự), seed minh họa `seed_tuyen_tham_quan.sql`.
- Bản đồ số mới (giao diện): lớp Tất cả / Du lịch / Cửa hàng với số điểm từng lớp (lọc phía client nên chuyển lớp tức thì, lớp lưu trên URL `kind`); ghim cửa hàng và cơ sở sản xuất là hình vuông bo góc màu vàng dã quỳ, điểm du lịch giữ ghim giọt nước theo loại hình (phân biệt bằng hình dạng, không chỉ màu); thống kê đầu panel; chip lọc theo nhóm sản phẩm (`category`); lọc theo sản phẩm (`product`) với nhãn vai trò "Bán/Sản xuất/Giới thiệu tại đây" và đường nét đứt nối nơi sản xuất với nơi bán; lọc theo chủ thể (`subject`); chế độ danh sách "Danh sách / Chi tiết"; thẻ điểm có thêm điện thoại, website, giá vé (chỉ điểm du lịch), toàn bộ dịch vụ, sản phẩm kèm vai trò và liên kết "Xem nơi mua và sản xuất", liên kết chủ thể. Bộ lọc sản phẩm hoặc chủ thể không còn công khai thì tự bỏ và báo cho người dùng.
- Trang sản phẩm có mục "Mua sản phẩm này ở đâu" (danh sách điểm kèm vai trò, bản đồ nhỏ, liên kết sang bản đồ lớn theo sản phẩm và theo chủ thể); trang điểm du lịch ẩn "Giá vé" với cửa hàng và có liên kết xem các địa điểm của đơn vị trên bản đồ.
- Bản đồ GeoJSON trả thêm `contact_phone`, `website` của điểm.
- Form khai báo điểm của chủ thể có thêm loại "Cửa hàng OCOP" và "Cơ sở sản xuất".
- Bản đồ số liên kết điểm du lịch, cửa hàng, sản phẩm và chủ thể (backend): loại hình `ocop_store` (cửa hàng OCOP) và `workshop` (cơ sở sản xuất) tạo thành nhóm `shop`, suy ra từ loại hình nên không thêm cột; `location_ocop_products.role` (`produced_here`, `sold_here`, `displayed`); `/map/locations` và `/map/nearby` có tham số `kind`; `/map/locations` lọc thêm theo `product_id`, `category`, `subject_id`; `GET /products/{slug}/locations` (nơi mua, xem, sản xuất sản phẩm) và `GET /subjects/{id}` (điểm và sản phẩm của chủ thể). Danh sách `/locations` mặc định chỉ trả điểm du lịch. Migration `015_lien_ket_ban_do.sql`, seed minh họa `seed_cua_hang_ban_do.sql` (chưa xác minh, xem `docs/DU_LIEU.md`).
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
- Bản đồ GeoJSON bổ sung chủ thể và các sản phẩm OCOP công khai liên kết với từng điểm du lịch; panel bản đồ hiển thị ảnh, sản phẩm và liên kết chi tiết.
- Thẻ thông tin điểm được hiển thị nổi trực tiếp trên vùng bản đồ theo kiểu popup/card; trên điện thoại chuyển thành bottom-sheet có nút đóng, chỉ đường và xem chi tiết.
- Thẻ bản đồ neo theo marker, tự đổi phía khi marker gần mép khung nhìn; bổ sung mô tả, dịch vụ, đánh giá, giá vé và giờ mở cửa từ dữ liệu điểm đã duyệt.
- Form điểm du lịch hiển thị ảnh, nhóm ngành và hạng sao khi chọn sản phẩm OCOP; card bản đồ liệt kê tối đa ba sản phẩm đã gắn, kèm hạng sao và ảnh đại diện.
- Seed tham khảo DaLaVi: liên kết sản phẩm Dâu tây sấy dẻo 3 sao với cơ sở Păng Tiêng và cửa hàng 27/6E Yersin theo tọa độ Google Maps do nhóm cung cấp.
- Thêm 16 sản phẩm tham khảo từ Aso Farm/DaLaVi và Dalat Hasfarm ở trạng thái bản nháp; không gán hạng sao OCOP và không công khai trước khi chủ thể hoàn thiện hồ sơ.
- Sửa lỗi 500 ở danh sách hồ sơ chủ thể do email tài khoản kỹ thuật `.invalid` bị Pydantic từ chối; dùng domain ví dụ hợp lệ cho tài khoản bị khóa.
- Chuyển hồ sơ Hasfarm từ tài khoản kỹ thuật sang tài khoản chủ thể thật do nhóm cung cấp; giữ nguyên hồ sơ pending và các sản phẩm bản nháp, chưa tự động duyệt.
- Bổ sung ảnh chính CDN của Dalat Hasfarm cho 5 sản phẩm tham khảo, lưu nguồn, credit và quyền sử dụng; không thay đổi trạng thái bản nháp.
- Bổ sung 17 ảnh công khai cho 11 sản phẩm AsoFarm/DaLaVi; tổng 16 sản phẩm tham khảo đều có ảnh chính, không thay đổi số sản phẩm OCOP công khai.

### Sửa

- Rà soát bản đồ số theo checklist unslop: gọn đầu bảng (bỏ ô thống kê lặp), không hiện số 0 khi đang tải hoặc lỗi; thẻ điểm chỉ hiện ảnh thật, nút luôn nằm ngoài vùng cuộn; cụm ghim theo hệ màu; vùng chạm 44px; chọn tuyến tham quan không làm mất bản đồ và ghi rõ đường chấm không phải đường đi.
- Rà soát giao diện và trải nghiệm toàn bộ, tập trung bản đồ (axe: không còn lỗi trên các trang đã quét):
  - Bản đồ: thẻ điểm không còn bị cắt ở mép trên/dưới (tự kẹp theo chiều cao thẻ, đặt cạnh marker, chừa chỗ cho nút phóng to); trên điện thoại thẻ gọn hơn, nút Chỉ đường luôn thấy, bản đồ tự dịch để marker đang chọn không bị thẻ che, thẻ không che dòng ghi nguồn OpenStreetMap; bỏ tooltip trùng tên bị thẻ che mất một nửa.
  - Bản đồ: chiều cao khung bản đồ trừ đủ thanh thông báo và đầu trang (trước đây đáy bản đồ, danh sách và chú thích bản quyền bị đẩy ra ngoài màn hình); nút chọn lớp không còn xuống dòng, nhãn thống kê ngắn gọn, danh sách địa điểm lên trước, tuyến tham quan gập gọn, chip nhóm sản phẩm gập trong mục "Nhóm sản phẩm", nút Danh sách/Chi tiết không xuống dòng; lớp bản đồ dùng nút bật/tắt (aria-pressed) thay cho radiogroup không có phím mũi tên.
  - Liên kết số điện thoại, website và "Xem nơi mua và sản xuất" có vùng bấm đủ lớn; nút "Bỏ lọc" ở banner đủ tương phản.
  - Trang điểm du lịch: chưa có ảnh thì dùng ảnh minh họa theo loại hình kèm ghi chú thay vì khung trống; mini map ở trang sản phẩm gom cụm để ghim không đè nhau; ô tìm kiếm, nút mở tìm kiếm và nút menu ở đầu trang đạt vùng bấm 40–44px.
  - README: thêm hướng dẫn đặt `$OutputEncoding` UTF-8 khi nạp seed/migration bằng PowerShell 5.1 (nguyên nhân làm tiếng Việt thành dấu `?`), và các migration 015, 016.
- Rà soát phong cách ở trang quản trị, chủ thể và tài khoản: chữ đậm tối đa 600 (token mới `--ocop-font-weight-semibold`), bỏ lời chào ở dashboard và trang đăng nhập, bỏ dấu chấm than ở thông báo gửi đánh giá, thay `transition: all`, bỏ viền trái màu ở ghi chú duyệt hồ sơ.
- Trang chủ chỉ tải 12 sản phẩm để chọn 8 sản phẩm nổi bật, đồng thời rút ngắn hiệu ứng hiện nội dung để giảm thời gian chờ cảm nhận.
- Các API bản đồ xem trước, tin tức và điểm du lịch trên trang chủ được lên lịch khi trình duyệt rảnh để ưu tiên nội dung đầu trang.
- Trang đăng nhập/đăng ký vừa màn hình laptop (Windows 125–150%, trình duyệt 100%): không còn tràn theo chiều dọc ở 1536×784 và 1366×650 (đăng nhập), vẫn giữ ba dòng lợi ích ở cột trái và ghi chú quyền riêng tư (chỉ ẩn ghi chú khi cao dưới 700 px); thanh thông báo đầu trang tự gọn khi màn hình thấp; nút Google/Facebook xếp hai cột.
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
