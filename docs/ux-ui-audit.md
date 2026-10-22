# Audit UX/UI toàn hệ thống

Ngày thực hiện: 22/10/2026. Nhánh: `2312682_HaLuyen_CICDvaSEO`. Môi trường kiểm thử: PostgreSQL 16 + PostGIS, backend FastAPI, Vite dev server, Playwright (Chromium) với dữ liệu thử nghiệm `e2e_ocop`.

Tài liệu này ghi lại hiện trạng **trước** đợt cải tiến. Kết quả sau cải tiến nằm ở `docs/ux-ui-improvement-report.md`; thứ tự thực hiện nằm ở `docs/ux-ui-improvement-plan.md`.

## 1. Kiến trúc UI hiện tại (xác định từ source)

Đề bài ban đầu nhắc Flask và template; **repo thực tế không dùng chúng**. Kiến trúc thật:

| Lớp | Công nghệ | Vị trí |
|---|---|---|
| Frontend | Vue 3 (Composition API, `<script setup>`), Vite, TypeScript, vue-router (route nạp lười), Bootstrap 5, Bootstrap Icons | `frontend/src` |
| Bản đồ | Leaflet + leaflet.markercluster | `components/map/LeafletMap.vue`, `views/MapView.vue` |
| Biểu đồ | Chart.js 4 (chỉ đăng ký thành phần cần dùng) | `components/admin/StatChart.vue` |
| Backend | FastAPI, SQLAlchemy, Pydantic | `backend/app` |
| Dữ liệu | PostgreSQL 16 + PostGIS, migration trong `database/` | |
| Kiểm thử | Vitest (frontend), pytest (backend), Playwright E2E (kịch bản ngoài repo) | |

Design tokens: `frontend/src/styles/tokens.css` (tiền tố `--ocop-*`, khu quản trị thêm `--admin-*`). Kiểu dùng chung: `styles/main.css`. Font: Be Vietnam Pro. Icon: `components/ui/AppIcon.vue` (bọc Bootstrap Icons). Khung trang: `App.vue` + `AppHeader` + `SiteFooter` (công khai), `layouts/PortalShell.vue` (quản trị và chủ thể), `components/auth/AuthLayout.vue` (đăng nhập, đăng ký).

Cách frontend gọi API: `services/http.ts` (axios), các `services/*.ts` theo từng nhóm; lỗi đi qua `services/api-error.ts`.

## 2. Danh mục trang và luồng (chỉ những gì có thật trong repo)

| Nhóm | Route | Ghi chú |
|---|---|---|
| Công khai | `/`, `/san-pham`, `/san-pham/:slug`, `/san-pham/:slug/diem-trai-nghiem`, `/diem-du-lich`, `/diem-du-lich/:slug`, `/ban-do`, `/tin-tuc` | Tin tức lấy từ nguồn RSS bên ngoài nên có thể 503 |
| Xác thực | `/dang-nhap`, `/dang-ky`, `/dang-nhap/mang-xa-hoi/:provider` | Google, Facebook |
| Người dùng | `/tai-khoan`, `/tai-khoan/danh-gia`, `/dang-ky-chu-the` | |
| Chủ thể | `/chu-the/ho-so`, `san-pham`, `san-pham/them`, `san-pham/:id/chinh-sua`, `yeu-cau/:id/chinh-sua`, `diem-du-lich`, `diem-du-lich/khai-bao`, `diem-du-lich/yeu-cau/:id`, `diem-du-lich/:id` | |
| Quản trị | `/quan-tri` (tổng quan), `ho-so-chu-the`, `san-pham`, `diem-du-lich`, `danh-gia`, `nguoi-dung`, `danh-muc` | |
| Lỗi | `/khong-co-quyen` (403), mọi đường dẫn khác (404), trang 500 khi giao diện lỗi | |

**Chưa triển khai (xác nhận từ route, không tự thêm):** khôi phục mật khẩu, trang chi tiết tin tức nội bộ (tin mở sang nguồn ngoài), quản lý tin tức (CMS), tìm kiếm không dấu ở backend, chỉ đường trong ứng dụng ngoài OSRM qua backend.

## 3. Phương pháp và phạm vi kiểm tra

1. Đọc code các view, component, service, router, token.
2. Quét tự động 90 lượt tải trang (khách, người dùng, chủ thể, quản trị) ở 390, 768 và 1440 px: console, request 5xx, tràn ngang, số thẻ `main`, axe-core (wcag2a, wcag2aa, wcag21aa, wcag22aa), ảnh chụp toàn trang.
3. Ba lượt kiểm tra tương tác thật bằng Playwright: (a) danh sách và chi tiết sản phẩm; (b) bản đồ và điểm du lịch; (c) quản trị, chủ thể, tài khoản và phân quyền. Gồm cả trạng thái tải chậm, lỗi 500, mất mạng, rỗng, bàn phím, định vị cho phép và từ chối.

Hạn chế: tile OpenStreetMap, Google Fonts và nguồn RSS bị sandbox chặn, nên lỗi `ERR_TUNNEL_CONNECTION_FAILED` và `503 /news` là lỗi môi trường, không tính là lỗi ứng dụng. Chưa thử bằng trình đọc màn hình thật và thiết bị cảm ứng thật.

Một sự cố khi kiểm thử (trên DB thử nghiệm, không phải dữ liệu thật): một yêu cầu ngừng hiển thị "Mật ong hoa cà phê" bị chuyển sang `needs_revision` do một route mock sai khớp mẫu; một điểm du lịch nháp tạo ra khi thử wizard đã được xóa.

## 4. Điểm mạnh đã xác nhận

- Không có tràn ngang trên 89/90 lượt tải trang (ngoại lệ ở mục A3 khi dữ liệu có URL dài).
- axe-core: chỉ còn một nhóm lỗi trên thẻ sản phẩm (A2) và một lỗi ở bảng so sánh yêu cầu (B19); mọi trang khác sạch.
- Phân quyền đúng: khách vào `/quan-tri`, `/chu-the`, `/tai-khoan` được chuyển về đăng nhập kèm `redirect`; sai vai trò vào trang 403 có lối đi tiếp; API `/admin/*`, `/subject/*` trả 401/403 đúng.
- Số liệu tổng quan quản trị khớp API thật (79/75/63 sản phẩm, 55 thiếu quyết định, 12 điểm du lịch, 36 chủ thể đã duyệt).
- Trạng thái tải, lỗi, rỗng có đủ ở các trang dữ liệu chính, kèm nút "Thử lại"; chống bấm đúp khi gửi form.
- Danh sách sản phẩm: tìm kiếm, chip bộ lọc, xóa từng bộ lọc, sắp xếp, phân trang, URL giữ trạng thái, nút Back và khôi phục vị trí cuộn đều hoạt động.
- Bản đồ: đồng bộ hai chiều danh sách và marker, deep link `?diem=`, cluster, định vị cho phép và từ chối đều xử lý đúng và không giả định vị trí; chỉ đường là thật (OSRM qua backend) kèm liên kết dự phòng sang Google Maps.
- Biểu đồ Chart.js có mô tả `aria-label`, bảng số liệu thay thế, tôn trọng giảm chuyển động.
- Hộp thoại người dùng, danh mục, đánh giá có focus trap, Esc, trả focus.

## 5. Danh sách vấn đề

Cơ sở phân loại: **P0** làm hỏng chức năng, mất dữ liệu hoặc rủi ro bảo mật; **P1** chặn hoặc làm sai lệch luồng chính, hoặc vi phạm tiêu chí tiếp cận mà quy tắc dự án yêu cầu bằng không (axe, tràn ngang); **P2** làm khó sử dụng, thiếu nhất quán hoặc số liệu mâu thuẫn nhưng có đường vòng; **P3** tinh chỉnh.

**P0: không phát hiện.** Không có lỗi mất dữ liệu hay rò rỉ thông tin. Quản trị và chủ thể được bảo vệ đúng ở cả giao diện lẫn API.

### P1

| Mã | Trang / component | Bằng chứng | Tác động | Giải pháp | File | Nghiệm thu |
|---|---|---|---|---|---|---|
| A1 | Toàn site, thẻ sản phẩm, bộ lọc quản trị | `styles/main.css:76-79` viền focus 3 px `primary-500` độ đục 42% (khoảng 1,7 đến 1,9:1); `ProductCard.vue:370-374` 28% và offset âm; `AdminProductsView.vue:675` `outline:none` | Người dùng bàn phím không thấy đang ở đâu (WCAG 1.4.11, 2.4.7) | Viền đặc `--ocop-primary-700` offset dương, biến thể sáng trên nền tối, bỏ `outline:none` | `main.css`, `ProductCard.vue`, `AdminProductsView.vue` | Tương phản viền từ 3:1 trên nền sáng và nền tối |
| A2 | Thẻ sản phẩm (danh sách, trang chủ, sản phẩm liên quan) | `ProductCard.vue:46` `aria-label` chỉ là tên đè nội dung; axe `label-content-name-mismatch` (serious) 12 node ở `/san-pham`, 8 ở `/`, 3 ở chi tiết | Trình đọc và lệnh thoại không nghe giá, hạng, chủ thể; vi phạm WCAG 2.5.3; quy tắc dự án yêu cầu axe không lỗi | Bỏ `aria-label`, dùng `aria-labelledby` trỏ tiêu đề | `ProductCard.vue` | axe sạch trên `/`, `/san-pham`, chi tiết |
| A3 | Chi tiết sản phẩm | `/san-pham/tham-khao-2026-macca-bechamp` tràn 1055 px ở 390 px; `ProductDetailView.vue:26` chỉ nhận tiền tố "Nguồn sản phẩm:", dữ liệu có "Nguồn: https://…"; `.content-block p` thiếu `overflow-wrap`; 9/63 sản phẩm có URL trần | 14% sản phẩm bị vỡ bố cục trên điện thoại | `overflow-wrap:anywhere`, nhận "Nguồn:" và hiển thị nút "Xem nguồn chính thức", `min-width:0` cho cột lưới | `ProductDetailView.vue` | 9 sản phẩm không tràn ở 390/768/1440 |
| A4 | `/ban-do` marker | `LeafletMap.vue:135-143` chỉ gắn `click`; Leaflet chỉ phát `keypress` khi Enter | Marker có role button nhưng Enter không chọn được điểm | Gắn `keypress` (Enter, Space), đặt `aria-label` marker và cluster | `LeafletMap.vue` | Tab đến marker rồi Enter đổi `?diem=` |
| A5 | `/ban-do` trên mobile | `router/index.ts` `scrollBehavior` luôn `top:0` kể cả khi chỉ đổi query; thẻ chọn nằm dưới viewport (y=969 trên màn 844) | Chọn điểm xong không thấy thông tin; chọn từ danh sách thì bản đồ nhảy lên đầu | Không đặt lại cuộn khi chỉ đổi query; trên mobile cuộn thẻ chọn vào tầm nhìn | `router/index.ts`, `MapView.vue` | Ở 390×844, chọn điểm thì thẻ hiện trong viewport |
| A6 | Mọi form | `services/api-error.ts:17-19` chỉ lấy `data.message`; API 422 trả `details[].loc/msg` | Luôn thấy "Dữ liệu đầu vào không hợp lệ", không biết trường nào | Ghép tên trường tiếng Việt với lý do | `api-error.ts` | Tên quá dài hiện "Tên sản phẩm tối đa 255 ký tự" |
| A7 | Quản trị > Sản phẩm, modal duyệt | `AdminProductsView.vue:337` alert nằm sau lớp phủ modal; PATCH 500 không có phản hồi trong modal | Thao tác kiểm duyệt cốt lõi thất bại mà người duyệt không thấy | Lỗi riêng hiện trong modal, `role="alert"` | `AdminProductsView.vue` | Bơm 500 thì lỗi hiện trong modal, nút bật lại |
| A8 | Tổng quan quản trị và chuông | `AdminDashboardView.vue:39,326,371` mở `/quan-tri/san-pham` đang lọc "Chờ duyệt"; trang không đọc `route.query` | Số 55 "Thiếu số quyết định" bấm vào chỉ thấy 1 bản ghi | Đọc và ghi `tab`, `status`, `issue`, `expiry` vào URL; sửa các liên kết | `AdminProductsView.vue`, `AdminDashboardView.vue`, `AdminLayout.vue` | "Bổ sung ngay" mở danh sách 55 sản phẩm |
| A9 | Chủ thể: danh sách và form sản phẩm | Alert ở đầu trang, `top:-667` khi `scrollY=936` ở 390 px | Bấm "Gửi duyệt" xong thấy "không có gì xảy ra" | Cuộn và focus vào thông báo | `SubjectProductsView.vue`, `SubjectProductEditorView.vue`, `AdminProductsView.vue` | Ở 390 px, lỗi nằm trong khung nhìn |

### P2

| Mã | Mô tả và bằng chứng | Giải pháp | File |
|---|---|---|---|
| B1 | Enter trong ô tìm bị nuốt khi đang tải (`ProductsView.vue:289`, nút submit `:disabled="isLoading"`) | Bỏ `disabled` khi tải; đã có `latestRequestId` | `ProductsView.vue` |
| B2 | Nháp trong form xung đột khi dùng chip, sao, sắp xếp; sắp xếp với giá sai làm ô chọn lệch URL | Thống nhất một quy tắc; không để ô chọn lệch trạng thái đã áp dụng | `ProductsView.vue` |
| B3 | Từ khóa 300 ký tự làm chip rộng 2709 px, tràn 1269 px; API 422 hiện như lỗi máy chủ kèm "Thử lại" | `maxlength`, cắt chip bằng ellipsis, thông báo riêng cho 422 | `ProductsView.vue` |
| B4 | "0 sản phẩm phù hợp" hiện khi đang tải và khi lỗi | Ẩn hoặc "Đang tải…" | `ProductsView.vue` |
| B5 | Ô giá `step=1000` chặn 1500 hay 45500 (danh sách và form chủ thể) | Bỏ `step`, `inputmode="numeric"` | `ProductsView.vue`, `SubjectProductEditorView.vue` |
| B6 | Phân trang và "Thử lại" làm focus rơi về `BODY` | Giữ nav khi tải, đưa focus về vùng kết quả | `ProductsView.vue` |
| B7 | Ngăn kéo bộ lọc mobile: không focus trap, không khóa cuộn, không `role=dialog`, Esc chỉ khi focus bên trong | Hành vi hộp thoại đầy đủ, trả focus | `ProductsView.vue` |
| B8 | Bản đồ: "Điểm gần bạn" bỏ qua bộ lọc; chọn điểm ngoài bộ lọc không ra thẻ | Áp bộ lọc hoặc thêm điểm vào danh sách hiển thị kèm thông báo | `MapView.vue`, `services/locations.ts` |
| B9 | Bản đồ: bộ lọc không nằm trong URL (`location.search` rỗng), chọn điểm xóa `type`. Tìm "dau" không ra "dâu" (backend `ilike` không bỏ dấu) | Đồng bộ URL hai chiều; **tìm không dấu ghi nhận là hạng mục backend riêng** | `MapView.vue`; backend `location_catalog.py` |
| B10 | Một điểm tọa độ `null` làm sập toàn bộ marker; `[0,0]` làm `fitBounds` ra toàn cầu | Lọc tọa độ hợp lệ trong khung Lâm Đồng, thông báo số điểm bị bỏ | `LeafletMap.vue`, `MapView.vue` |
| B11 | "Chỉ đường" đặt lại view về vị trí người dùng, điểm đến có thể ra ngoài khung | `fitBounds([người dùng, điểm đến])` | `LeafletMap.vue` |
| B12 | `/ban-do` không có chú giải loại hình; `dairy_farm` (sky) và `other` (blue) gần màu | Chú giải bấm để lọc, đếm theo dữ liệu thật, kèm icon | `MapView.vue` (hoặc `MapLegend.vue`) |
| B13 | Tổng quan lỗi tải mà vẫn báo "Mọi hồ sơ đã được duyệt" (`AdminDashboardView.vue:254-258`) | Khi lỗi hiện "Chưa tải được" và "–" | `AdminDashboardView.vue` |
| B14 | Wizard điểm du lịch: "Tiếp tục" ở bước 1 tạo nháp rồi dựng lại component (`SubjectLayout.vue:54` `:key=path`) nên vẫn ở bước 1 | Key theo tên route | `SubjectLayout.vue` |
| B15 | Form sản phẩm không `maxlength`; nút "Lưu và gửi duyệt" bị khóa không nêu lý do | `maxlength` theo schema, dòng "Còn thiếu: …" | `SubjectProductEditorView.vue` |
| B16 | Badge "N yêu cầu chờ xử lý" đếm theo bộ lọc đang chọn (3 hay 2) | Đếm riêng theo `status=pending` | `AdminProductsView.vue` |
| B17 | "63 đang công khai" và "94,9% hồ sơ đã duyệt (75/79)" cùng trang, 12 sản phẩm chênh không giải thích | Ghi rõ đã duyệt và công khai | `AdminDashboardView.vue`, `AdminProductsView.vue` |
| B18 | `/quan-tri/ho-so-chu-the` ở 390 px che cột "Thao tác" (bảng 851 px, không `data-label`) | Dạng thẻ xếp chồng như trang Người dùng | `AdminSubjectApplicationsView.vue` |
| B19 | Bảng so sánh yêu cầu cập nhật vi phạm ARIA (axe critical `aria-required-children`, 11 node), hiện mã danh mục và giá thô | `<table>` thật, tên danh mục, định dạng tiền | `AdminProductsView.vue` |
| B20 | Ngăn kéo menu mobile của khu quản trị và chủ thể không quản lý focus | Focus vào menu, trap Tab, trả focus | `PortalShell.vue` |
| B21 | 7 chỗ dùng `window.confirm` cho thao tác quan trọng | `ConfirmDialog.vue` dùng chung (`alertdialog`) | `SubjectProductsView`, `SubjectLocationsView`, `SubjectLocationEditorView`, `ProductEvidenceManager`, `AdminProductsView` |

### P3

| Mã | Mô tả | File |
|---|---|---|
| C1 | Tooltip marker cũ không đóng khi chọn điểm khác | `LeafletMap.vue` |
| C2 | Đổi cỡ màn hình không căn lại về marker đang chọn | `LeafletMap.vue` |
| C3 | Thông báo định vị tách khỏi nút; bán kính cố định 50 km, không có lối thoát khi ở ngoài Lâm Đồng | `MapView.vue` |
| C4 | Thứ tự Tab trên mobile khác thứ tự nhìn (`order:-1`); Esc không bỏ chọn điểm | `MapView.vue` |
| C5 | Tham số URL sai tạo chip "NaN đ", "abc sao", slug thô; `star=2` hoặc `min>max` gây 422 | `ProductsView.vue` |
| C6 | Tiêu đề "3–5 sao" và nút "5 sao" không khớp dữ liệu đang có (chỉ 3 và 4 sao) | `ProductsView.vue`, `HomeBento.vue` |
| C7 | Gallery: ảnh chính lỗi thì hiện khung giữ chỗ dù còn ảnh dùng được | `PresentationGallery.vue` |
| C8 | Chi tiết sản phẩm: trạng thái tải và lỗi thiếu `role`, "!" chưa `aria-hidden`, tiêu đề tab không đổi | `ProductDetailView.vue` |
| C9 | Form đánh giá: lỗi và thành công không chuyển focus; lỗi nhận xét thiếu `role="alert"` | `ReviewForm.vue`, `ReviewSection.vue` |
| C10 | Mobile: dải chip nhóm bị cắt không có dấu hiệu cuộn; "Trang trước" xuống hai dòng ở 390 px | `ProductsView.vue` |
| C11 | Sắp xếp "Tên Z–A" đặt Đ lên đầu (collation; **hạng mục backend**) | backend `products` |
| C12 | Duyệt hoặc từ chối hồ sơ chủ thể không có thông báo thành công | `AdminSubjectApplicationsView.vue` |
| C13 | `/admin/dashboard` gọi hai lần; phân trang và hộp thoại làm focus rơi về `BODY` | `AdminLayout.vue`, `AdminDashboardView.vue` |
| C14 | Esc đóng modal duyệt mất ghi chú đã gõ; bước 1 wizard cho qua khi tên trống không báo | `AdminProductsView.vue`, `SubjectLocationEditorView.vue` |
| C15 | Danh sách chủ thể không tìm kiếm, `page_size` cố định 100; tab trạng thái cắt không gợi ý cuộn | `SubjectProductsView.vue`, `SubjectLocationsView.vue` |
| C16 | Cùng trạng thái `rejected` hiện "Cần bổ sung" phía chủ thể và "Đã từ chối" phía admin; `/chu-the/ho-so` bảo liên hệ quản trị viên nhưng không có cách liên hệ; trang 403 của người dùng thường thiếu lối "Đăng ký chủ thể" | `SubjectApplicationView.vue`, `SubjectProfileView.vue`, `ForbiddenView.vue` |
| C17 | Footer cao 855 px ở 390 px; trang tài khoản và đánh giá rỗng có khoảng trống lớn | `SiteFooter.vue`, `MyReviewsView.vue`, `ProfileView.vue` |
| C18 | Địa bàn là văn bản tự do nên biểu đồ lẫn "Đà Lạt", "xã Đức Trọng", "Lâm Hà" (**cần chuẩn hóa dữ liệu, hạng mục riêng**) | form đăng ký chủ thể, `AdminDashboardView.vue` |
| C19 | Hồ sơ bắt dán "URL ảnh đại diện" | `ProfileView.vue` |
| C20 | Công tắc "Bảng số liệu" vừa `aria-pressed` vừa đổi nhãn | `StatChart.vue` |

## 6. Hạng mục xác định nhưng nằm ngoài phạm vi UX/UI (ghi nhận, không sửa)

1. Tìm kiếm không dấu cho địa điểm (cần `unaccent` hoặc cột chuẩn hóa: thay đổi schema).
2. Sắp xếp tên theo thứ tự tiếng Việt (collation PostgreSQL).
3. Chuẩn hóa địa bàn thành danh mục, kiểm trùng tọa độ khi lưu điểm du lịch, giới hạn tọa độ trong khung Lâm Đồng ở backend.
4. Tham số lọc "hết hạn" và "thiếu quyết định" cho `/admin/products` nếu chưa có; sẽ chỉ dùng tham số đã có.
5. Nguồn tin RSS bên ngoài không phản hồi (503) trong môi trường kiểm thử.
6. Ảnh sản phẩm ngoài (Cloudinary) và kho ảnh đã ghi ở `ui-audit.md` mục 6.

## 7. Tình trạng các hạng mục đã xử lý ở đợt trước (22/10/2026, trước audit này)

Thanh tiến trình và khung xương khi chờ tải, thông báo ngoại tuyến, phục hồi lỗi tải mã trang, trang 404/403/500 dùng chung, logo thương hiệu, bố cục đăng nhập và đăng ký vừa màn hình laptop: xem `CHANGELOG.md` và `ui-audit.md` mục 5.
