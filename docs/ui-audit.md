# Audit UX/UI — Cổng thông tin OCOP Lâm Đồng

- Ngày audit: 25/09/2026
- Nhánh: `2312682_HaLuyen_ToiUuGiaoDien` (sau commit chuẩn hóa design token)
- Phạm vi: toàn bộ frontend, 19 trang công khai, chủ thể và quản trị

## 1. Phương pháp

| Cách kiểm tra | Chi tiết |
|---|---|
| Kiểm tra tự động khả năng truy cập | axe-core, bộ luật WCAG 2.0/2.1/2.2 mức A và AA, chạy trên 19 trang ở 2 kích thước |
| Đo trực tiếp trên trình duyệt | Cỡ chữ đã tính của mọi phần tử có chữ, kích thước vùng bấm, tràn ngang, cấu trúc heading |
| Kích thước màn hình | 375px (điện thoại) và 1280px (máy tính) |
| Dựng lại trạng thái | 15 tình huống: từ chối định vị, không có điểm gần, chỉ đường lỗi `ROUTING_UNAVAILABLE`, API lỗi, đang tải, mất ảnh nền bản đồ, tìm kiếm không có kết quả, trang 404, nguồn RSS lỗi |
| Đọc mã nguồn | Template, style và câu chữ của các file `.vue` |

Dữ liệu thử: bộ seed phát triển (60 sản phẩm công khai, 9 điểm du lịch, 3 tài khoản demo).

Mức ưu tiên:

- **Cao**: cản trở nhiệm vụ chính (tìm sản phẩm, tìm và đến điểm du lịch), hoặc thành phần cốt lõi không đạt WCAG AA.
- **Trung bình**: gây khó hiểu, tốn thao tác hoặc thiếu nhất quán giữa các trang.
- **Thấp**: chi tiết trình bày, không ảnh hưởng hoàn thành nhiệm vụ.

## 2. Số liệu tổng quan

| Trang | Chữ < 12px (điện thoại) | Vùng bấm < 24px | Lỗi tương phản (axe) | Tràn ngang 375px |
|---|---|---|---|---|
| Trang chủ `/` | 47/133 phần tử chữ | 11 | 15 | Không |
| Sản phẩm `/san-pham` | 48/135 | 6 | 28 | Không |
| Chi tiết sản phẩm | 35/84 | 8 | 9 | Không |
| Tin tức `/tin-tuc` | 24/44 | 5 | 3 | Không |
| Điểm du lịch `/diem-du-lich` | 24/131 | 14 | 3 | Không |
| Chi tiết điểm du lịch | 25/66 | 8 | 5 | Không |
| Bản đồ `/ban-do` | 24/67 | 5 | 3 | Không |
| Đăng nhập, đăng ký | 1/11, 1/16 | 1, 2 | 0 | Không |
| Tài khoản, đăng ký chủ thể | 24/51, 25/50 | 5, 5 | 4, 3 | Không |
| Khu chủ thể (3 trang) | 17–28 mỗi trang | 0–1 | 1–8 | Không |
| Quản trị (3 trang) | 13–29 mỗi trang | 0 | 3–4 | Không |

Tổng hợp: 224 lỗi tương phản màu và 113 lỗi vùng bấm (WCAG 2.2 mục 2.5.8) trên 38 lần đo. Cỡ chữ 11px là cỡ xuất hiện nhiều nhất trong nhóm chữ nhỏ (756 lần), ngoài ra còn 10px, 9px và 8px. Header và footer chung góp khoảng 24 phần tử chữ nhỏ vào mỗi trang.

### Điểm đã đạt

- Không trang nào bị tràn ngang ở 375px.
- axe không báo lỗi label form, alt ảnh hay tên nút.
- Mỗi trang có đúng một `h1` (trừ đăng nhập, đăng ký trên điện thoại, xem TK-01).
- Có vòng focus rõ ràng; có hỗ trợ `prefers-reduced-motion`.
- Bản đồ tự chuyển nguồn ảnh nền và báo lỗi khi mất ảnh nền. Chỉ đường lỗi vẫn có liên kết Google Maps dự phòng.
- Trạng thái không có kết quả ở trang sản phẩm và điểm du lịch có lời gợi ý và nút xóa lọc.

## 3. Bảng tổng hợp vấn đề

Tổng cộng 42 vấn đề: 10 mức Cao, 24 mức Trung bình, 8 mức Thấp.

Trạng thái: **Chưa xử lý**, **Đang xử lý**, **Đã xử lý**.

### 3.1. Toàn cục (header, footer, token, thành phần chung)

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| G-01 | Khả năng truy cập | Chữ quá nhỏ: 30–50% phần tử chữ mỗi trang dưới 12px, nhiều nhất là 11px, có cả 8–9px ở trang quản trị và chủ thể | Đo cỡ chữ đã tính; token `--ocop-font-size-xs` (11px), `-2xs` (10px) | Cao | Nâng `-xs`, `-2xs` lên tối thiểu 12px ngay trong `tokens.css`; mô tả, giá, địa chỉ trên điện thoại dùng tối thiểu 14px; bỏ hẳn 8–9px | Đã xử lý (bước 0) |
| G-02 | Tương phản | Một số cặp token không đạt 4.5:1, lặp lại trên hầu hết các trang | `--ocop-warning` trên `--ocop-warning-soft` 3.96 (chip "Chờ duyệt", nhãn "Cổng thông tin", ghi chú kiểm duyệt); `--ocop-text-tertiary` trên nền trắng 2.63 (nhãn "Chủ thể" ở thẻ sản phẩm); `--ocop-neutral-500` trên nền footer 3.10; `--ocop-text-on-dark-muted` 3.23; `--ocop-sidebar-muted` trên nền trắng 1.91 (khu chủ thể); `--ocop-slate` trên `--ocop-surface-muted` 4.32 (tiêu đề bảng); `--ocop-blue` trên `--ocop-info-soft` 4.44 | Cao | Chỉnh token, áp dụng toàn cục: warning chữ `#9c6300` (4.69), tertiary `#65758c` (4.69), footer phụ `#8192aa` (4.65), chữ phụ trên nền tối `#9fadc4` (4.60); với `--ocop-sidebar-muted` trên nền trắng thì đổi sang dùng `--ocop-text-secondary`; tiêu đề bảng dùng `--ocop-text-muted` | Đã xử lý (bước 0) |
| G-03 | Huy hiệu sao OCOP | Huy hiệu sao, tín hiệu quan trọng nhất của sản phẩm, có chữ trắng trên nền cam `#ff9500`, tỉ lệ 2.20. Có hai cách ghi: "OCOP 3 sao" (thẻ) và "3 sao OCOP" (chi tiết). Cùng một icon ngôi sao được dùng cho điểm đánh giá của người dùng | `ProductCard.vue` `.star-badge`, `ProductDetailView.vue` `.ocop-badge`, axe color-contrast | Cao | Tạo một component huy hiệu sao OCOP dùng chung: hiện số sao bằng icon lặp (3–5 sao) kèm chữ "OCOP 3 sao"; màu đạt chuẩn (nền `#b45309` chữ trắng 5.02, hoặc nền cam chữ nâu đậm 4.66); điểm đánh giá của người dùng dùng nhãn và kiểu khác | Chưa xử lý |
| G-04 | Vùng bấm | 5 liên kết footer chỉ cao 18px trên mọi trang; nút "Thử lại", "Xóa lọc", liên kết "Xem tất cả" nhỏ; đa số control dưới 44px trên điện thoại (trang sản phẩm: 24/36) | axe target-size; đo kích thước vùng bấm | Cao | Nút và liên kết điều hướng trên điện thoại cao tối thiểu 44px (dùng token `--ocop-control-md` hiện có nhưng chưa được dùng); tăng khoảng cách dòng liên kết footer | Đang xử lý: phần toàn cục xong ở bước 0; nút tự viết của từng trang xử lý khi thiết kế lại trang |
| G-05 | Thuật ngữ | Một khái niệm nhiều tên: menu "Khám phá Lâm Đồng", trang "Điểm đến trải nghiệm", breadcrumb "Điểm du lịch", trang chủ "Điểm đến canh nông tiêu biểu", nút "Điểm du lịch canh nông". Bản đồ: "Bản đồ" / "Bản đồ số GIS & Chỉ đường" / "Bản đồ số Lâm Đồng". Tin tức: "Tin tức" / "Tin tức & Sự kiện OCOP" / "Hoạt động OCOP Lâm Đồng" | Đọc template: "điểm đến" 13 lần, "điểm du lịch" 24 lần | Trung bình | Chốt bảng thuật ngữ và dùng giống nhau ở menu, tiêu đề trang, breadcrumb, footer: "Sản phẩm OCOP", "Điểm du lịch", "Bản đồ số", "Tin tức" | Chưa xử lý |
| G-06 | Câu chữ nút, tiêu đề | Trang chủ và footer viết hoa mọi chữ ("Tra Cứu Ngay", "Khám Phá Bản Đồ Số GIS", "Mở Bản Đồ Số Toàn Màn Hình", "Danh Mục Hệ Thống"), các trang khác viết hoa chữ đầu câu | `HomeHero.vue`, `HomeMapPreview.vue`, `TourismSection.vue`, `FeaturedProducts.vue`, `SiteFooter.vue` | Trung bình | Thống nhất viết hoa chữ đầu câu; nhãn nút bắt đầu bằng động từ ngắn ("Tìm sản phẩm", "Mở bản đồ") | Chưa xử lý |
| G-07 | Nội dung | Thuật ngữ kỹ thuật hiện với du khách: "GIS", "Bản đồ số PostGIS & Leaflet", "Phát triển với Vue 3 / FastAPI / PostGIS", "OSRM (OpenStreetMap)", "Số liệu trực tiếp từ database" | Footer, `HomeMapPreview.vue`, `MapView.vue`, `AdminDashboardView.vue` | Trung bình | Đổi sang lời người dùng hiểu được; thông tin công nghệ chuyển về README hoặc trang giới thiệu | Chưa xử lý |
| G-08 | Footer trên điện thoại | Footer cao khoảng 1.230px ở 375px (4 thẻ thống kê, 2 nhóm liên kết, khối minh bạch), lặp ở mọi trang, kể cả trang bản đồ | Đo phần tử `footer` ở 375px | Trung bình | Rút gọn footer trên điện thoại: bỏ thẻ thống kê, gom nhóm liên kết dạng thu gọn; trang bản đồ dùng footer tối giản | Chưa xử lý |
| G-09 | Trạng thái đang tải | Không nhất quán: chỉ trang chủ và tin tức có skeleton. Trang sản phẩm chỉ đổi chữ nút thành "Đang tải...". Danh sách điểm du lịch và bản đồ hiện "0 điểm đến đang hiển thị" trong lúc tải | Dựng lại tình huống API chậm 4–5 giây | Trung bình | Skeleton dùng chung cho lưới thẻ và danh sách; không hiện số 0 khi chưa có dữ liệu | Chưa xử lý |
| G-10 | Thành phần dùng chung | Nút, chip trạng thái, hộp lỗi và hộp rỗng được viết riêng ở từng trang, ví dụ 4 kiểu chip trạng thái với tên class khác nhau (`status-chip`, `status-badge`, `status`, `issue-chip`) | Đọc mã nguồn | Trung bình | Tách component trình bày: chip trạng thái, hộp trạng thái rỗng, hộp lỗi có nút thử lại, tiêu đề trang | Chưa xử lý |
| G-11 | Bố cục | Nút "về đầu trang" nổi đè lên nội dung cuối danh sách trên điện thoại, đè cả nút đóng thẻ điểm đã chọn ở bản đồ | Ảnh chụp bản đồ 375px | Trung bình | Chừa khoảng trống cuối trang, ẩn nút ở trang bản đồ hoặc dời vị trí khi có thanh nổi | Chưa xử lý |
| G-12 | Nhất quán màu | Một số thành phần còn màu mặc định của Bootstrap, lệch token: `.btn-outline-success` `#198754` (4.28), liên kết `#0d6efd` (4.25), `.text-secondary` `#6c757d` (4.17) | axe, trang chi tiết điểm du lịch và tài khoản | Thấp | Ánh xạ đủ biến `--bs-*` sang token, hoặc thay bằng class của dự án | Chưa xử lý |

### 3.2. Trang chủ `/`

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| TC-01 | Phân cấp thông tin | Hero có ô tìm kiếm cùng 3 nút có trọng số ngang nhau; trên điện thoại hero cao 635px trên màn hình 740px | Đo phần tử ở 375px | Trung bình | Một hành động chính (tìm sản phẩm hoặc điểm du lịch) và 2 lối tắt dạng chip; giảm chiều cao hero trên điện thoại | Chưa xử lý |
| TC-02 | Điều hướng | Danh mục sản phẩm trượt ngang trên điện thoại, thẻ bị cắt, không có dấu hiệu còn nội dung để cuộn | Ảnh chụp 375px | Trung bình | Lưới 2–3 cột gọn, hoặc giữ trượt ngang nhưng thêm chỉ dấu và nút "Xem tất cả" rõ ràng | Chưa xử lý |
| TC-03 | Mật độ nội dung | Sản phẩm nổi bật và điểm du lịch tiêu biểu hiện 1 cột trên điện thoại, mỗi thẻ cao 440–480px, phần lớn là ảnh minh họa "DỮ LIỆU THAM KHẢO"; trang chủ cao 6.867px | Ảnh chụp toàn trang 375px | Trung bình | Thẻ gọn 2 cột trên điện thoại; ảnh tỉ lệ thấp hơn; tên, huy hiệu sao, địa bàn lên trước | Chưa xử lý |
| TC-04 | Vùng bấm | Marker trên bản đồ xem trước bị che một phần, vùng bấm còn 12px | axe target-size | Thấp | Tăng vùng bấm của marker, hoặc cả khung bản đồ xem trước là một liên kết | Chưa xử lý |

### 3.3. Bản đồ số `/ban-do`

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| BD-01 | Điều hướng (điện thoại) | Bấm marker thì thẻ điểm đã chọn hiện ở y ≈ 930px, hoặc y ≈ 1.220px nếu đã định vị (nằm dưới danh sách điểm gần). Trang không tự cuộn, màn hình chỉ cao 740px nên người dùng không thấy phản hồi | Đo vị trí phần tử sau khi bấm marker ở 375px | Cao | Thẻ điểm đã chọn dạng bottom sheet nổi trên bản đồ, có nút chỉ đường, xem chi tiết và đóng | Chưa xử lý |
| BD-02 | Bố cục (điện thoại) | Bản đồ cao 459px; ô tìm kiếm và bộ lọc nằm dưới bản đồ; cả trang cao 2.882px, trong đó footer chiếm 1.227px | Đo phần tử ở 375px | Cao | Bố cục dạng ứng dụng: bản đồ gần toàn màn hình, thanh tìm kiếm và lọc nổi phía trên, danh sách điểm dạng bảng kéo lên | Chưa xử lý |
| BD-03 | Trạng thái lỗi, đang tải | Khi API bản đồ lỗi, thông báo nằm ở panel dưới bản đồ (ngoài màn hình đầu trên điện thoại), bản đồ trống, tiêu đề ghi "0 điểm đến đang hiển thị". Lúc đang tải cũng hiện "0 điểm đến" | Dựng lại API lỗi và API chậm | Cao | Lớp thông báo ngay trên bản đồ kèm nút "Thử lại"; trạng thái đang tải trên bản đồ; ẩn số đếm khi chưa có dữ liệu | Chưa xử lý |
| BD-04 | Trạng thái chưa cấp quyền định vị | Chỉ có một dòng chữ nhỏ màu cam, không hướng dẫn bật lại quyền, không có cách thay thế | Dựng lại từ chối quyền định vị | Trung bình | Hộp thông báo có hướng dẫn ngắn và cách thay thế: chọn địa bàn, xem tất cả điểm | Chưa xử lý |
| BD-05 | Trạng thái không có điểm gần | Chỉ có dòng "Không có điểm du lịch nào trong bán kính 50 km", không có bước tiếp theo | Dựng lại vị trí ở Hà Nội | Trung bình | Thêm hành động "Xem tất cả điểm" và gợi ý địa bàn gần nhất có điểm | Chưa xử lý |
| BD-06 | Trạng thái chỉ đường lỗi | Thông báo `ROUTING_UNAVAILABLE` đúng nội dung và có liên kết Google Maps dự phòng, nhưng liên kết nhỏ (vùng bấm dưới 24px), chữ lỗi nhỏ | Dựng lại OSRM không phản hồi | Trung bình | Liên kết dự phòng thành nút phụ rõ ràng ngay cạnh thông báo lỗi | Chưa xử lý |
| BD-07 | Chú giải | Bản đồ chính không có chú giải loại hình (trang chủ thì có); marker chỉ phân biệt bằng màu và icon nhỏ | Ảnh chụp 1280px và 375px | Trung bình | Chú giải thu gọn được, dùng chung màu token `--ocop-location-*` | Chưa xử lý |

### 3.4. Điểm du lịch `/diem-du-lich`, `/diem-du-lich/:slug`

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| DL-01 | Mật độ nội dung | Trên điện thoại, bộ lọc đặt trước kết quả, thẻ 1 cột cao; 9 điểm mà trang cao 6.612px | Ảnh chụp 375px | Trung bình | Bộ lọc thu gọn, thẻ gọn hoặc dạng danh sách; nút "Xem trên bản đồ" nổi | Chưa xử lý |
| DL-02 | Trạng thái lỗi | Khi API lỗi, ô chọn loại hình và địa bàn trống mà không có thông báo; nút "Thử lại" nhỏ | Dựng lại API lỗi | Trung bình | Hộp lỗi dùng chung (G-10), vô hiệu bộ lọc kèm giải thích | Chưa xử lý |
| DL-03 | Nhất quán màu | Nút "Chỉ đường bằng Google Maps" và liên kết nguồn dùng màu Bootstrap mặc định (G-12) | axe | Thấp | Dùng kiểu nút và liên kết của dự án | Chưa xử lý |
| DL-04 | Trang không tìm thấy | Tiêu đề và mô tả lặp y hệt ("Không tìm thấy điểm du lịch" hai lần), không có gợi ý | Dựng lại slug sai | Thấp | Mô tả khác tiêu đề; gợi ý điểm du lịch khác và nút mở bản đồ | Chưa xử lý |

### 3.5. Sản phẩm `/san-pham`, `/san-pham/:slug`

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| SP-01 | Tìm sản phẩm (điện thoại) | Khối bộ lọc 6 trường mở sẵn, đặt trước kết quả; sản phẩm đầu tiên nằm ở y ≈ 970px, tức phải cuộn quá một màn hình mới thấy | Đo phần tử ở 375px | Cao | Nút "Bộ lọc" mở ngăn trượt; hiện chip các bộ lọc đang áp dụng ngay trên kết quả | Chưa xử lý |
| SP-02 | Mật độ nội dung | 1 cột trên điện thoại, mỗi thẻ cao 448px, 12 thẻ mỗi trang, trang cao 7.963px | Ảnh chụp 375px | Cao | Lưới 2 cột thẻ gọn trên điện thoại (dùng chung thẻ với TC-03) | Chưa xử lý |
| SP-03 | Thẻ sản phẩm | Nhãn "Chủ thể" tương phản 2.63; huy hiệu sao lỗi màu (G-03); nhãn giá "Liên hệ" dùng màu nhấn như một mức giá | axe | Trung bình | Sửa theo G-02, G-03; "Liên hệ" trình bày khác với giá thật | Chưa xử lý |
| SP-04 | Phân cấp trang chi tiết | Khối "Liên hệ" nền xanh là khối nổi nhất nhưng không có hành động; hạng sao chỉ là chip nhỏ cạnh danh mục | Ảnh chụp 1280px | Trung bình | Đưa huy hiệu sao lên vị trí nổi bật cạnh tên sản phẩm; khối liên hệ dẫn tới chủ thể hoặc điểm du lịch liên quan | Chưa xử lý |
| SP-05 | Trang không tìm thấy | Giống DL-04 | Dựng lại slug sai | Thấp | Như DL-04, gợi ý sản phẩm cùng danh mục | Chưa xử lý |

### 3.6. Tin tức `/tin-tuc`

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| TT-01 | Trạng thái lỗi | Khi RSS lỗi, trang báo lỗi rõ và có nút thử lại, nhưng vẫn hiện "0 bài viết từ Cổng TTĐT OCOP Lâm Đồng" cùng lúc | Dựng lại RSS lỗi | Thấp | Ẩn số đếm khi đang lỗi | Chưa xử lý |

### 3.7. Đăng nhập, đăng ký, tài khoản

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| TK-01 | Cấu trúc, thương hiệu | Trên điện thoại không có `h1` vì phần giới thiệu (chứa `h1`) bị ẩn; logo tròn chữ "O" khác logo ở header | Đo heading, ảnh chụp 375px | Trung bình | Tiêu đề form là `h1` trên điện thoại; dùng chung logo thương hiệu | Chưa xử lý |
| TK-02 | Tương phản | Mô tả trang tài khoản dùng `.text-secondary` của Bootstrap (4.17) | axe | Thấp | Theo G-12 | Chưa xử lý |

### 3.8. Khu chủ thể `/chu-the/*`

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| CT-01 | Bố cục (điện thoại) | Hai thanh đầu trang chồng nhau (thanh thương hiệu nền tối và thanh tiêu đề nền trắng) đẩy nội dung chính xuống y ≈ 250px; nhãn phụ "Quản lý nội dung OCOP", "Chủ thể OCOP" tương phản 1.91 | Ảnh chụp 375px, axe | Trung bình | Gộp thành một thanh; nhãn phụ theo G-02 | Chưa xử lý |
| CT-02 | Form dài | Form thêm sản phẩm 1 cột, cao khoảng 2.600px trên điện thoại; khối tiến độ hồ sơ chữ 11px màu nhạt (3.23) | Ảnh chụp 375px, axe | Trung bình | Mục lục neo tới từng phần, nút lưu cố định ở đáy màn hình, tiến độ hồ sơ đủ tương phản | Chưa xử lý |
| CT-03 | Cỡ chữ | Chữ 9px ở thông tin tệp chứng nhận | `SubjectProductEditorView.vue` | Thấp | Theo G-01 | Chưa xử lý |

### 3.9. Quản trị `/quan-tri/*`

| ID | Khía cạnh | Vấn đề | Bằng chứng | Ưu tiên | Đề xuất hướng sửa | Trạng thái |
|---|---|---|---|---|---|---|
| QT-01 | Responsive | Bảng hồ sơ chủ thể ở 375px: cột bị ép, tên đơn vị xuống dòng từng chữ, cột thứ ba bị cắt | Ảnh chụp 375px | Cao | Trên điện thoại chuyển mỗi hàng thành thẻ; giữ bảng trên máy tính | Chưa xử lý |
| QT-02 | Nội dung dashboard | Dashboard chỉ có 4 thẻ số liệu và không có biểu đồ; còn các khối nội dung dành cho người phát triển ("Kế hoạch tiếp theo", "Module quản trị ưu tiên", "Nền tảng hiện có", "Số liệu trực tiếp từ database") | Ảnh chụp, `AdminDashboardView.vue` | Trung bình | Thay bằng hàng việc cần xử lý (hồ sơ và sản phẩm chờ duyệt). Nếu muốn có biểu đồ (sản phẩm theo hạng sao, theo địa bàn) thì phải thêm Chart.js, là thư viện mới nên cần xin ý kiến trước | Chưa xử lý |
| QT-03 | Điều hướng | Sidebar có 5 mục bị vô hiệu kèm nhãn "Sắp phát triển" chữ 8px (Điểm du lịch, Chủ thể/HTX, Người dùng, Đánh giá, Bài viết) | `AdminLayout.vue` | Trung bình | Ẩn các mục chưa có hoặc gom vào một nhóm "Sắp có" | Chưa xử lý |
| QT-04 | Cỡ chữ, tương phản | Trang duyệt sản phẩm dùng nhiều chữ 9–11px; chip trạng thái "Chờ duyệt", "Thiếu quyết định" tương phản 3.96 | Đo cỡ chữ, axe | Trung bình | Theo G-01, G-02, G-10 | Chưa xử lý |

## 4. Đề xuất thứ tự thiết kế lại

| Thứ tự | Trang | Lý do | Vấn đề xử lý |
|---|---|---|---|
| 0 | Nền tảng: token tương phản, cỡ chữ, vùng bấm | Sửa ở `tokens.css` là cải thiện mọi trang cùng lúc và làm nền cho thiết kế từng trang | G-01, G-02, G-04 |
| 1 | Trang chủ, kèm header, footer, thẻ sản phẩm, huy hiệu sao | Trang vào đầu tiên; tạo sẵn các thành phần dùng chung cho các trang sau | G-03, G-05 đến G-08, G-10, TC-01 đến TC-04 |
| 2 | Bản đồ số | Nhiều vấn đề mức Cao nhất; nhiệm vụ cốt lõi của đồ án | BD-01 đến BD-07, G-09, G-11 |
| 3 | Danh sách và chi tiết sản phẩm | Nhiệm vụ tìm sản phẩm OCOP trên điện thoại | SP-01 đến SP-05 |
| 4 | Danh sách và chi tiết điểm du lịch | Dùng lại thẻ và bộ lọc của bước 3 | DL-01 đến DL-04, G-12 |
| 5 | Quản trị: dashboard, hồ sơ chủ thể, duyệt sản phẩm | Yêu cầu responsive cho dashboard quản trị | QT-01 đến QT-04 |
| 6 | Khu chủ thể | Người dùng phụ, form dài | CT-01 đến CT-03 |
| 7 | Tin tức; đăng nhập, đăng ký, tài khoản; trang lỗi | Ít vấn đề, chủ yếu mức Thấp | TT-01, TK-01, TK-02 |

## 5. Nhật ký xử lý

### Bước 0: tương phản, cỡ chữ, vùng bấm (25/09/2026)

- Token màu chữ chỉnh vừa đủ đạt 4.5:1 trên nền được thiết kế: `--ocop-slate` `#617068`, `--ocop-text-tertiary` `#627289`, `--ocop-warning` `#9c6300`, `--ocop-blue` và `--ocop-info` `#2475a2`, `--ocop-neutral-500` `#607087`; `--ocop-text-on-dark-muted` sáng lên `#9faec4` (chỉ dùng trên nền tối).
- Sửa 4 chỗ dùng token sai nền: dòng cuối footer, nhãn phụ ở thanh tiêu đề khu chủ thể, danh sách tiến độ hồ sơ sản phẩm.
- Bỏ token cỡ chữ `xs` (11px), `2xs` (10px) và các giá trị 8px, 9px, 0.72rem; cỡ nhỏ nhất là `--ocop-font-size-caption` (12px), kể cả chú thích trong tooltip bản đồ.
- Vùng bấm: liên kết footer tối thiểu 24px, trên thiết bị cảm ứng 44px; trên thiết bị cảm ứng `.btn`, `.form-control`, `.form-select` cao tối thiểu 44px (`--ocop-control-md`).
- Nhãn mục chưa có ở sidebar quản trị đổi "Sắp phát triển" thành "Sắp có" để không bị xuống dòng khi tăng cỡ chữ.

| Chỉ số (19 trang x 2 kích thước) | Trước | Sau |
|---|---|---|
| Lỗi tương phản (axe) | 224 | 46: 38 là huy hiệu sao (G-03), 8 là màu mặc định Bootstrap (G-12) |
| Lỗi vùng bấm (axe) | 113 | 3: marker bản đồ xem trước ở trang chủ (TC-04) |
| Phần tử chữ dưới 12px | 906 | 0 |
| Control dưới 44px trên điện thoại cảm ứng | 283/366 | 190/366 (còn lại là nút tự viết trong từng trang) |
| Trang bị tràn ngang ở 375px | 0 | 0 |

## 6. Ngoài phạm vi giao diện (ghi nhận, không sửa trong nhánh này)

- Quản trị chưa có module quản lý điểm du lịch (mục "Sắp phát triển" ở sidebar).
- Tìm điểm gần đang cố định bán kính 50 km; nếu muốn cho người dùng mở rộng bán kính thì cần kiểm tra API có nhận tham số bán kính hay không.
- Trang chi tiết sản phẩm chưa có số điện thoại hay kênh liên hệ của chủ thể trong dữ liệu trả về.
- Biểu đồ dashboard cần thư viện Chart.js, hiện chưa có trong `package.json`.
