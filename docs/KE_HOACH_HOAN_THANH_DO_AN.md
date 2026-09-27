# Kế hoạch hoàn thành đồ án và tự đánh giá tiến độ

Đề tài: **Xây dựng Cổng thông tin quảng bá nông sản OCOP và bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng**
Nhóm trưởng: Liêng Hót Ha Luyến (2312682). GVHD: KS. La Quốc Thắng.

- Cập nhật lần cuối: **27/09/2026** (cuối tuần 7 theo đề cương).
- Căn cứ: đề cương ngày 10/08/2026 (lộ trình 14 tuần), tài liệu hướng dẫn nhóm 25/08/2026, mã nguồn và lịch sử commit.
- Mốc đã chốt (27/09/2026):
  - **Thứ Năm 15/10/2026: báo cáo tiến độ đợt 2** (giữa tuần 10).
  - **Chủ nhật 15/11/2026: hạn cuối nộp đồ án** (cuối tuần 14). Mọi sản phẩm nộp phải xong trước **14/11**.

Cách dùng file này:

- Mỗi phiên làm việc bắt đầu bằng việc đọc mục 4 (việc tuần hiện tại) và mục 6 (quyết định đang chờ). Claude chỉ nhận việc thuộc phần của Luyến (mục 3).
- Làm xong một việc thì đổi trạng thái, ghi commit, và thêm một dòng vào mục 7 (nhật ký).
- Ký hiệu trạng thái: ✅ xong · 🟡 đang làm hoặc làm một phần · ⬜ chưa làm · ⏸ chờ quyết định.

---

## 1. Tự đánh giá tổng quan (27/09/2026)

Tiến độ ước lượng theo khối lượng các hạng mục trong đề cương (không phải số dòng code):

| Nhóm hạng mục | Tiến độ | Nhận xét |
|---|---|---|
| Khảo sát, dữ liệu, thiết kế (tuần 1–4) | 90% | Đủ dữ liệu 77 sản phẩm OCOP và 9 điểm du lịch có nguồn. Cần rà lại sơ đồ Use Case và sơ đồ chức năng cho báo cáo cuối. |
| Cơ sở dữ liệu PostgreSQL + PostGIS | 90% | Schema, 9 migration, seed, file kiểm tra database. Còn phần review và các bảng quản trị sẽ phát sinh. |
| Backend (tuần 5–7) | 65% | Có auth JWT/RBAC, sản phẩm (công khai, chủ thể, kiểm duyệt, yêu cầu sửa, chứng nhận), hồ sơ chủ thể, bản đồ, thống kê. Thiếu API điểm du lịch cho chủ thể/admin, đánh giá, danh mục, người dùng. |
| Bản đồ số (tuần 8–9) | 85% | Clustering, lọc, định vị, điểm gần nhất, chỉ đường OSRM. Thiếu chủ thể khai báo điểm; chưa kiểm thử OSRM thật trong Docker. |
| Phân hệ chủ thể (tuần 10–11) | 55% | Quản lý sản phẩm, ảnh, chứng nhận đầy đủ. Thiếu quản lý địa điểm, cập nhật thông tin đơn vị trực tiếp. |
| Phân hệ admin (tuần 10–11) | 50% | Dashboard và thống kê Chart.js, duyệt sản phẩm, duyệt hồ sơ chủ thể. Thiếu quản lý danh mục, địa điểm, người dùng, kiểm duyệt đánh giá. |
| Giao diện UX/UI | 45% | Làm mới trang chủ, sản phẩm, tổng quan quản trị (đạt WCAG AA). Còn khoảng 10 trang dùng giao diện cũ. |
| Kiểm thử | 50% | 95 test backend, 72 test frontend, axe cho các trang đã làm. Chưa có kiểm thử E2E theo luồng và kiểm thử trên nhiều thiết bị. |
| Triển khai, SEO, lưu ảnh Firebase (tuần 13) | 5% | Mới có Docker cho môi trường phát triển. Chưa có VPS, Nginx, HTTPS, thẻ meta/chia sẻ, Firebase. |
| Tài liệu và báo cáo (tuần 13–14) | 30% | Có README, API.md, Postman, ERD, báo cáo tiến độ đợt 1. Thiếu hướng dẫn sử dụng, báo cáo tổng kết, slide, kịch bản demo. |
| **Toàn đồ án** | **khoảng 60%** | Đúng tiến độ phần lõi (sản phẩm, bản đồ); chậm ở phần quản trị và triển khai. Còn 7 tuần. |

---

## 2. Đối chiếu chức năng với đề cương

### 2.1 Phân hệ người dùng

| Chức năng (đề cương 2.5) | Trạng thái | Ghi chú |
|---|---|---|
| Trang chủ | ✅ | Thiết kế lại, ảnh thật, tìm kiếm hai chế độ, bản đồ xem trước |
| Danh sách, tìm kiếm, bộ lọc sản phẩm | ✅ | Lọc theo nhóm, hạng sao, địa bàn; giao diện mới |
| Chi tiết sản phẩm | 🟡 | Chạy đúng, giao diện cũ |
| Danh sách, chi tiết địa điểm | 🟡 | Chạy đúng, giao diện cũ; tiêu đề còn "Điểm đến trải nghiệm" |
| Bản đồ: clustering, định vị, điểm gần nhất, tuyến đường | ✅ | Ảnh nền OpenStreetMap (bỏ CARTO 26/09) |
| Đăng ký, đăng nhập, hồ sơ | ✅ | Giao diện cũ |
| Đánh giá sản phẩm/địa điểm | ⬜ | Bảng `reviews` đã có, chưa có API và giao diện |
| Tin tức | 🟡 | Lấy RSS từ cổng OCOP tỉnh; chưa có tin do admin đăng (xem quyết định Q3) |

### 2.2 Phân hệ chủ thể

| Chức năng | Trạng thái | Ghi chú |
|---|---|---|
| Đăng ký trở thành chủ thể | ✅ | Admin duyệt hồ sơ |
| Quản lý sản phẩm | ✅ | Nháp, gửi duyệt, yêu cầu sửa sau duyệt, giấy chứng nhận |
| Quản lý hình ảnh | 🟡 | Ảnh sản phẩm lưu trong `backend/uploads`; chưa có Firebase; ảnh chưa duyệt vẫn mở được bằng link |
| Quản lý địa điểm | 🟡 | Migration 009 xong (27/09); còn API, giao diện, ảnh điểm |
| Cập nhật thông tin đơn vị | 🟡 | Xem được hồ sơ; sửa phải gửi lại hồ sơ |

### 2.3 Phân hệ admin

| Chức năng | Trạng thái | Ghi chú |
|---|---|---|
| Dashboard, thống kê, biểu đồ | ✅ | API `/admin/statistics`, Chart.js |
| Kiểm duyệt sản phẩm và yêu cầu sửa | ✅ | Giao diện cũ, chữ nhỏ (QT-04) |
| Duyệt hồ sơ chủ thể | ✅ | Giao diện cũ, vỡ bố cục ở điện thoại (QT-01) |
| Quản lý địa điểm (duyệt điểm chủ thể khai báo) | ⬜ | Tuần 8–9 |
| Quản lý danh mục | ⬜ | Tuần 10 |
| Quản lý người dùng | ⬜ | Tuần 10 |
| Kiểm duyệt đánh giá | ⬜ | Tuần 10 |

### 2.4 Kỹ thuật, triển khai, tài liệu

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| PostgreSQL + PostGIS, migration | ✅ | `tools/kiem-tra-database.sql` để kiểm tra database khớp repo |
| JWT, phân quyền admin/subject/user | ✅ | |
| Chart.js cho dashboard | ✅ | |
| Firebase Storage cho ảnh | ⏸ | Đề cương cam kết; chờ quyết định Q2 |
| Responsive, trợ năng | 🟡 | 3 trang đạt; các trang khác làm ở tuần 11 |
| Triển khai Cloud/VPS, Nginx, HTTPS | ⬜ | Tuần 13; chờ quyết định Q4 |
| SEO cơ bản, chia sẻ mạng xã hội | ⬜ | Tuần 12 |
| API documentation (Swagger, API.md, Postman) | 🟡 | Cần bổ sung các endpoint mới |
| ERD, Database schema | ✅ | `database/ERD.md`; cập nhật ảnh ERD cho báo cáo |
| Hướng dẫn cài đặt | 🟡 | README; cần bản cho môi trường triển khai |
| Hướng dẫn sử dụng (người dùng, chủ thể, admin) | ⬜ | Tuần 13 |
| Báo cáo tổng kết, slide, demo | ⬜ | Tuần 14; đã có báo cáo tiến độ đợt 1 |

---

## 3. Phân công

Theo phân công của nhóm trưởng:

| Thành viên | Phụ trách |
|---|---|
| Liêng Hót Ha Luyến (nhóm trưởng, làm cùng Claude) | Phân hệ **admin**, phân hệ **chủ thể**, chức năng **tài khoản người dùng** (đăng ký, đăng nhập, hồ sơ, đánh giá), backend và database cho các phần này, triển khai |
| Nguyễn Quốc Thái, Nguyễn Khiêm Thuận | **Trang chủ và các trang công khai**: sản phẩm, chi tiết sản phẩm, điểm du lịch, chi tiết điểm, bản đồ, tin tức, trang lỗi; SEO và hiệu năng trang công khai |

Lưu ý phối hợp:

- Nhánh giao diện `2312682_HaLuyen_ToiUuGiaoDien` đã sửa trang chủ và trang sản phẩm (phần của Thái, Thuận), nên hai bạn cần review PR này trước khi merge.
- Chỗ giao nhau (sản phẩm gắn với điểm, đánh giá): Luyến làm API và phần nhập liệu, Thái, Thuận hiển thị trên trang công khai; thống nhất định dạng dữ liệu API trước khi làm.

## Mốc quan trọng

| Ngày | Mốc | Cần có để trình bày |
|---|---|---|
| 15/10/2026 | Báo cáo tiến độ đợt 2 | Chủ thể khai báo điểm và admin duyệt chạy được (tuần 8–9), thống kê quản trị, giao diện đã làm mới, số liệu tiến độ |
| 15/11/2026 | Hạn cuối nộp đồ án | Toàn bộ chức năng theo đề cương, bản triển khai, báo cáo tổng kết, slide, hướng dẫn |

## 4. Kế hoạch chi tiết từng tuần (tuần 8–14)

Mỗi việc làm trên nhánh riêng `2312682_HaLuyen_<TenChucNang>`, theo quy tắc trong `CLAUDE.md`. Giao diện lớn thiết kế trên canvas trước, chờ duyệt rồi mới code; backend là commit riêng.

### Tuần 8 (28/09 – 04/10): Chủ thể khai báo và admin duyệt điểm du lịch, phần thiết kế và backend

Nhánh: `2312682_HaLuyen_KhaiBaoDiemDuLich`

| # | Việc | Phụ trách | Trạng thái | Tiêu chí xong |
|---|---|---|---|---|
| 8.1 | Migration 009: trạng thái kiểm duyệt, nguồn vị trí, yêu cầu cập nhật | Luyến | ✅ | Chạy lặp lại an toàn, cấu trúc khớp schema.sql (commit 8385d89, 0710abf, a52b7f6) |
| 8.2 | Tạo lại database sạch, dọn thư mục đồ án, thêm kiểm tra database | Luyến | ✅ | `kiem-tra-database.sql` trả rỗng (commit a7eb63b) |
| 8.3 | Gộp nhánh giao diện và dọn dẹp vào main (kèm 4 sửa lỗi trang sản phẩm của Thuận) | Luyến | ✅ | Gộp local 27/09 (merge ee2610a và merge vào main); nhóm trưởng push |
| 8.4 | Thiết kế canvas: form khai báo điểm (ô chọn vị trí: ghim bản đồ, GPS, dán tọa độ/link Google Maps), trang admin duyệt điểm, việc chờ duyệt trên dashboard | Luyến | ✅ | Nhóm trưởng đã duyệt 27/09 (canvas "OCOP – Khai báo và duyệt điểm du lịch"): bắt buộc mô tả ≥ 40 ký tự và ≥ 1 ảnh; kiểm tra Lâm Đồng bằng khung tọa độ; điểm cách điểm đã duyệt < 200 m chỉ cảnh báo; điện thoại chia 5 bước |
| 8.5 | API chủ thể: tạo, sửa, xóa bản nháp, gửi duyệt, xem danh sách điểm của mình | Luyến | ⬜ | Kiểm tra quyền sở hữu; điểm nằm trong Lâm Đồng; test |
| 8.6 | API admin: danh sách chờ duyệt, xem chi tiết, chỉnh vị trí, duyệt / cần bổ sung / từ chối | Luyến | ⬜ | Ghi người duyệt, ngày duyệt, ghi chú; test |
| 8.7 | API yêu cầu cập nhật / ngừng hiển thị điểm đã duyệt | Luyến | ⬜ | Điểm cũ vẫn hiển thị tới khi duyệt; đối chiếu `version`; test |

### Tuần 9 (05/10 – 11/10): Điểm du lịch, phần giao diện

| # | Việc | Phụ trách | Trạng thái | Tiêu chí xong |
|---|---|---|---|---|
| 9.1 | Khu chủ thể: danh sách điểm, form khai báo với ô chọn vị trí | Luyến | ⬜ | Chạy trên điện thoại (GPS); axe 0 lỗi |
| 9.2 | Ảnh điểm du lịch: tải lên, chọn ảnh chính, xóa | Luyến | ⬜ | Dùng cùng cơ chế lưu ảnh với sản phẩm (theo Q2) |
| 9.3 | Liên kết sản phẩm của chủ thể với điểm du lịch | Luyến (chủ thể gắn sản phẩm); Thái, Thuận (hiển thị trên trang chi tiết) | ⬜ | Chi tiết điểm hiện sản phẩm, chi tiết sản phẩm hiện điểm |
| 9.4 | Trang admin duyệt điểm, thêm việc chờ duyệt vào dashboard và thống kê | Luyến | ⬜ | Hàng đợi và số liệu cập nhật đúng |
| 9.5 | Kiểm thử luồng: chủ thể khai báo → admin duyệt → điểm hiện trên bản đồ | Luyến | ⬜ | Test tự động và chạy thử bằng tài khoản demo |

### Tuần 10 (12/10 – 18/10): Báo cáo tiến độ đợt 2 (15/10), đánh giá và các chức năng quản trị còn thiếu

| # | Việc | Phụ trách | Trạng thái | Tiêu chí xong |
|---|---|---|---|---|
| 10.0a | Chuẩn bị báo cáo tiến độ đợt 2: cập nhật báo cáo và slide (dựa trên báo cáo đợt 1), số liệu tiến độ lấy từ file này | Cả nhóm | ⬜ | Xong trước 13/10 |
| 10.0b | Kịch bản và dữ liệu demo đợt 2: luồng chủ thể khai báo điểm → admin duyệt → điểm hiện trên bản đồ, thống kê quản trị | Luyến | ⬜ | Diễn tập trơn tru trên máy demo trước 14/10 |
| 10.0c | **Báo cáo tiến độ đợt 2 (15/10)** | Cả nhóm | ⬜ | Ghi nhận góp ý của GVHD vào mục 7 |
| 10.1 | API và giao diện đánh giá sản phẩm/điểm (mỗi người một đánh giá, chờ duyệt) | Luyến (API, form đánh giá); Thái, Thuận (hiển thị đánh giá trên trang chi tiết) | ⬜ | Tính lại `rating_avg` khi duyệt; test |
| 10.2 | Admin kiểm duyệt đánh giá | Luyến | ⬜ | Duyệt / từ chối có lý do |
| 10.3 | Admin quản lý danh mục (thêm, sửa, ẩn) | Luyến | ⬜ | Không xóa danh mục đang có sản phẩm |
| 10.4 | Admin quản lý người dùng (tìm kiếm, khóa/mở khóa, xem vai trò) | Luyến | ⬜ | Không tự khóa chính mình; test phân quyền |
| 10.5 | Bỏ các mục "Sắp có" trong thanh bên quản trị | Luyến | ⬜ | Mục nào chưa làm thì ẩn |

### Tuần 11 (19/10 – 25/10): Lưu ảnh, thông tin đơn vị, giao diện các trang còn lại

| # | Việc | Phụ trách | Trạng thái | Tiêu chí xong |
|---|---|---|---|---|
| 11.1 | Lưu ảnh theo quyết định Q2 (Firebase Storage hoặc giữ lưu cục bộ); chặn xem ảnh chưa duyệt | Luyến | ⏸ | Ảnh chưa duyệt không mở được bằng link công khai |
| 11.2 | Chủ thể cập nhật thông tin đơn vị trực tiếp (thay đổi quan trọng cần admin duyệt) | Luyến | ⬜ | Test |
| 11.3 | Giao diện mới: danh sách và chi tiết điểm du lịch, chi tiết sản phẩm | Thái, Thuận | ⬜ | Theo design token; axe 0 lỗi; không tràn ngang |
| 11.4 | Giao diện mới: trang quản trị con (duyệt sản phẩm, hồ sơ chủ thể), khu chủ thể | Luyến | ⬜ | Sửa QT-01, QT-04 |
| 11.5 | Giao diện mới: đăng nhập, đăng ký, hồ sơ, tin tức, trang lỗi | Luyến (đăng nhập, đăng ký, hồ sơ); Thái, Thuận (tin tức, trang lỗi) | ⬜ | |

### Tuần 12 (26/10 – 01/11): Kiểm thử tổng thể, SEO, tài liệu API

| # | Việc | Phụ trách | Trạng thái | Tiêu chí xong |
|---|---|---|---|---|
| 12.1 | Kiểm thử E2E các luồng chính (Playwright): khách, chủ thể, admin | Cả nhóm (mỗi người viết cho phần mình) | ⬜ | Chạy lại được bằng một lệnh |
| 12.2 | Kiểm tra responsive (375, 768, 1024, 1440px) và trợ năng toàn bộ trang | Cả nhóm | ⬜ | axe 0 lỗi |
| 12.3 | SEO cơ bản: title/description từng trang, thẻ Open Graph khi chia sẻ sản phẩm/điểm | Thái, Thuận | ⬜ | Chia sẻ link lên Facebook hiện đúng ảnh và tiêu đề |
| 12.4 | Hiệu năng: nén ảnh, lazy load, kích thước gói JS | Thái, Thuận | ⬜ | Lighthouse Performance ≥ 80 trên máy tính |
| 12.5 | Cập nhật `docs/API.md` và Postman cho mọi endpoint | Luyến | ⬜ | Khớp Swagger |
| 12.6 | Kiểm tra bảo mật cơ bản: phân quyền, upload file, giới hạn tần suất đăng nhập | Luyến | ⬜ | Danh sách kiểm tra có kết quả |

### Tuần 13 (02/11 – 08/11): Triển khai và hướng dẫn

| # | Việc | Phụ trách | Trạng thái | Tiêu chí xong |
|---|---|---|---|---|
| 13.1 | Chọn nơi triển khai (Q4), cấu hình Docker production, Nginx, HTTPS | Luyến | ⏸ | Truy cập được bằng tên miền hoặc IP công khai |
| 13.2 | Sao lưu database định kỳ trên máy chủ, biến môi trường production | Luyến | ⬜ | Không lộ secret |
| 13.3 | Hướng dẫn cài đặt (dev và production) | Luyến | ⬜ | Người khác làm theo chạy được |
| 13.4 | Hướng dẫn sử dụng cho người dùng, chủ thể, admin (có ảnh chụp) | Cả nhóm (mỗi người viết phần mình) | ⬜ | |

### Tuần 14 (09/11 – 15/11): Báo cáo, slide, demo — nộp đồ án trước 15/11

| # | Việc | Phụ trách | Trạng thái | Tiêu chí xong |
|---|---|---|---|---|
| 14.1 | Báo cáo tổng kết: phân tích, thiết kế (Use Case, ERD, API, phân quyền), kết quả, khó khăn | Cả nhóm | ⬜ | Theo mẫu của khoa |
| 14.2 | Slide thuyết trình và kịch bản demo | Cả nhóm | ⬜ | Demo 3 vai: khách, chủ thể, admin |
| 14.3 | Dữ liệu demo sạch, tài khoản demo, diễn tập demo | Cả nhóm | ⬜ | Chạy trọn kịch bản không lỗi |
| 14.4 | Rà soát mã nguồn, README, gắn tag phiên bản nộp | Luyến | ⬜ | Tag `v1.0` trên main |
| 14.5 | **Nộp đồ án** (mã nguồn, báo cáo, slide, tài liệu) | Cả nhóm | ⬜ | Nộp xong trước 15/11 |

---

## 5. Rủi ro và cách xử lý

| Rủi ro | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Database các máy lệch nhau do sửa ngoài repo | Lỗi chỉ xảy ra trên một máy, mất thời gian dò | Chỉ sửa qua migration; chạy `tools/kiem-tra-database.sql` sau mỗi lần pull |
| PR chờ review lâu, các nhánh chồng lên nhau | Xung đột khi merge | Merge PR giao diện ngay tuần 8; mỗi nhánh nhỏ, một mục tiêu |
| Firebase cần tài khoản, khóa dịch vụ và có thể phát sinh phí | Trễ tuần 11 | Chốt Q2 trong tuần 8; nếu không kịp thì giữ lưu cục bộ và giải thích trong báo cáo |
| Chưa có VPS/tên miền | Không demo được bản trực tuyến | Chốt Q4 sớm; phương án dự phòng: demo bằng Docker trên máy |
| Dịch vụ ngoài (OSRM, ảnh nền bản đồ) thay đổi chính sách | Chức năng bản đồ lỗi lúc demo | Đã có nguồn dự phòng; kiểm tra lại trước buổi demo |
| Khối lượng dồn cho nhóm trưởng | Trễ các tuần cuối | Giữ đúng phân công ở mục 3; phần công khai giao cho Thái, Thuận |
| Sửa chồng lên phần của thành viên khác | Xung đột, mất công sửa lại | Trang công khai chỉ sửa khi đã báo và được người phụ trách review |

---

## 6. Quyết định đang chờ nhóm trưởng

| Mã | Câu hỏi | Cần trước |
|---|---|---|
| Q2 | Lưu ảnh: dùng Firebase Storage như đề cương, hay giữ lưu cục bộ trên máy chủ | Tuần 10 |
| Q3 | Tin tức: chỉ lấy RSS từ cổng OCOP tỉnh, hay thêm chức năng admin tự đăng tin | Tuần 10 |
| Q4 | Nơi triển khai: VPS (nhà cung cấp nào), cloud miễn phí, hay chỉ demo bằng Docker | Tuần 12 |

---

## 7. Nhật ký cập nhật

| Ngày | Nội dung | Commit / tài liệu |
|---|---|---|
| 24/09/2026 | Merge PR #2 bản đồ số và điểm du lịch vào main | f39c33c |
| 26/09/2026 | Hoàn thành giao diện trang chủ, sản phẩm, tổng quan quản trị; API và biểu đồ thống kê; CLAUDE.md; push nhánh giao diện | 4c74369 … 32595e6 |
| 26/09/2026 | Migration 009 cho khai báo điểm du lịch; bỏ ảnh nền CARTO | 8385d89, 8ab93fb |
| 27/09/2026 | Duyệt thiết kế khai báo/duyệt điểm (8.4); gộp main mới (PR #3–#6 của Thuận) vào nhánh, viết lại README; gộp nhánh vào main | ee2610a, commit này |
| 27/09/2026 | Chốt mốc: báo cáo tiến độ đợt 2 ngày 15/10, hạn nộp đồ án 15/11 (Q1) | Mục Mốc quan trọng |
| 27/09/2026 | Chốt phân công: Luyến làm admin, chủ thể, tài khoản người dùng; Thái, Thuận làm trang chủ và trang công khai (Q5) | Mục 3 |
| 27/09/2026 | Sửa migration 009 cho database cũ; tạo lại database sạch; dọn thư mục đồ án và nhánh git; thêm kiểm tra database, pgAdmin giữ tài khoản; lập kế hoạch này | 0710abf, a52b7f6, a7eb63b |
