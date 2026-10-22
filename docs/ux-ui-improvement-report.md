# Báo cáo cải tiến UX/UI

Ngày: 22/10/2026. Nhánh: `2312682_HaLuyen_CICDvaSEO`. Tài liệu liên quan: `docs/ux-ui-audit.md` (hiện trạng trước cải tiến), `docs/ux-ui-improvement-plan.md` (kế hoạch), `docs/design-system.md` (design system sau cải tiến).

Báo cáo chia mọi hạng mục thành bốn nhóm: **đã sửa và đã kiểm thử**, **đã sửa nhưng chưa kiểm thử đầy đủ**, **đã xác định nhưng chưa sửa**, **không làm được**. Chỉ ghi kết quả đã chạy thật; chỗ nào chưa chạy thì nói rõ.

## 1. Tổng quan hiện trạng ban đầu

Repo thực tế là Vue 3 + Vite + TypeScript + Bootstrap 5 ở frontend, FastAPI + SQLAlchemy ở backend, PostgreSQL 16 + PostGIS; **không dùng Flask hay template** như đề bài nhắc. Đã có sẵn bộ token (`styles/tokens.css`), khung trang, các component trạng thái tải/lỗi, hộp thoại có bẫy focus, biểu đồ có bảng số liệu thay thế. Audit (xem `ux-ui-audit.md`) quét 90 lượt tải trang (khách, người dùng, chủ thể, quản trị; 390, 768, 1440 px) và ba lượt tương tác thật. Kết quả: **không có lỗi P0** (không mất dữ liệu, không rò rỉ, phân quyền đúng ở giao diện lẫn API); 9 vấn đề P1, 21 vấn đề P2, 20 vấn đề P3.

## 2. Phát hiện chính

- **Tiếp cận:** viền focus quá nhạt (khoảng 1,7 đến 1,9:1), thẻ sản phẩm đè `aria-label` làm trình đọc mất giá, hạng, chủ thể (axe `label-content-name-mismatch`, serious), marker bản đồ không chọn được bằng Enter, bảng so sánh yêu cầu vi phạm ARIA.
- **Điện thoại:** 9/63 sản phẩm có URL nguồn trần làm trang chi tiết tràn 1055 px ở 390 px; chọn điểm trên bản đồ xong thẻ thông tin nằm dưới khung nhìn và trang bị cuộn về đầu; thông báo lỗi ở đầu trang nằm ngoài khung nhìn.
- **Luồng quản trị:** lỗi 422 luôn hiện "Dữ liệu đầu vào không hợp lệ"; lỗi duyệt sản phẩm nằm sau lớp phủ modal; số "55 thiếu số quyết định" bấm vào chỉ thấy 1 bản ghi vì trang không đọc URL.
- **Dữ liệu xấu:** một điểm du lịch có tọa độ `null` làm sập mọi marker; tham số URL sai tạo chip "NaN đ".
- **Nhất quán:** 7 chỗ dùng `window.confirm`; "Cần bổ sung" và "Đã từ chối" cùng một trạng thái.

## 3. Thay đổi đã thực hiện

Sáu commit, theo đợt của kế hoạch. Không đổi backend, schema hay hợp đồng API.

| Đợt | Commit | Nội dung |
|---|---|---|
| Đăng nhập | `2ff730a` | Cột trái dùng khối thương hiệu cùng kiểu header, biểu tượng mờ chìm làm hình nền thay cho thẻ trắng nổi (theo phản hồi người dùng) |
| Docs | `9d44dc9` | `ux-ui-audit.md`, `ux-ui-improvement-plan.md` |
| 1 Tiếp cận toàn cục | `ebfbff5` | Viền focus đặc 3 px `--ocop-primary-700`, nền tối dùng `--ocop-daquy-300` |
| 2 Sản phẩm | `df28721` | Thẻ, danh sách, chi tiết, gallery, đánh giá |
| 3 Bản đồ | `56a017f` | Marker, chú giải, URL, mobile, tọa độ lỗi |
| 4 Quản trị, chủ thể | `cd69623` | Lỗi 422, modal duyệt, liên kết số liệu, `ConfirmDialog`, menu mobile |
| 5 Tài liệu | commit `docs(ui): design system…` và `docs: cập nhật CHANGELOG…` | `design-system.md`, CHANGELOG, README |

Chi tiết theo khu vực:

**Toàn site.** Viền focus đặc, offset dương, đổi màu theo nền (A1). Thẻ sản phẩm bỏ `aria-label`, tên truy cập lấy từ nội dung hiển thị; nhãn nhóm đậm hơn để đạt 4,5:1 (A2).

**Danh sách và chi tiết sản phẩm** (`ProductsView`, `ProductDetailView`, `ProductCard`, `PresentationGallery`, `ReviewForm`, `ReviewSection`). Nút "Xem nguồn chính thức", `overflow-wrap` và `min-width:0` (A3); Enter khi đang tải không bị nuốt (B1); nháp bộ lọc không bị mất, ô sắp xếp không lệch URL (B2); `maxlength`, chip cắt bằng ellipsis, lỗi 422 riêng (B3); dòng đếm không hiện "0 sản phẩm" khi đang tải hoặc lỗi (B4); ô giá nhận số lẻ (B5); phân trang và "Thử lại" giữ focus (B6); ngăn kéo bộ lọc mobile là hộp thoại có bẫy Tab, khóa cuộn, Esc, trả focus (B7); chuẩn hóa tham số URL sai (C5); gallery tự chuyển ảnh khi ảnh chính lỗi (C7); `role` cho trạng thái tải/lỗi chi tiết (C8); form đánh giá chuyển focus tới lỗi hoặc kết quả (C9); dải chip nhóm có dấu hiệu cuộn (C10). Tiện ích mới: `utils/product-filters.ts`, `utils/product-story.ts`, `composables/useFocusTrap.ts`.

**Bản đồ** (`LeafletMap`, `MapView`, `MapLegend`, `router/scroll.ts`). Enter/Space chọn marker, nhãn marker và cụm đọc được (A4); router không đặt lại cuộn khi chỉ đổi query, mobile cuộn thẻ chọn vào khung nhìn và có nút "Xem trên bản đồ" (A5); "Điểm gần bạn" áp bộ lọc, có chọn bán kính 10/25/50/100 km (B8, C3); bộ lọc `search/type/district` đồng bộ hai chiều với URL (B9, phần giao diện); điểm có tọa độ ngoài khung Lâm Đồng (vĩ độ 10,2 đến 12,6; kinh độ 106,6 đến 109,0) bị bỏ khỏi bản đồ và có thông báo số điểm bị bỏ (B10); "Chỉ đường" căn cả hai điểm (B11); chú giải loại hình bấm để lọc, có icon và chữ (B12); tooltip cũ đóng khi chọn điểm khác (C1); Esc bỏ chọn (C4, phần Esc); `ResizeObserver` gọi `invalidateSize` (C2, phần đã có).

**Quản trị và chủ thể.** `api-error.ts` dịch 422 sang câu tiếng Việt theo trường (A6); lỗi duyệt hiện ngay trong modal với `role="alert"` (A7); bộ lọc sản phẩm quản trị nằm trên URL (`tab`, `status`, `q`, `level`, `verification`, `issue`, `expiry`, `page`) và các liên kết ở tổng quan, chuông thông báo mở đúng danh sách (A8); thông báo thành công/lỗi tự cuộn và focus vào khung nhìn qua `useFlashFocus` (A9, C12); tổng quan không báo sai "Mọi hồ sơ đã được duyệt" khi lỗi tải (B13); wizard điểm du lịch không dựng lại ở lần "Tiếp tục" đầu (B14); form sản phẩm có `maxlength` theo schema và dòng "Còn thiếu: …" (B15); huy hiệu chờ duyệt đếm riêng theo `status=pending` (B16); giải thích chênh lệch "đã duyệt" và "đang công khai" (B17); hồ sơ chủ thể dạng thẻ trên mobile (B18); bảng so sánh yêu cầu dùng `<table>` thật (B19); menu trượt mobile quản lý focus (B20); `ConfirmDialog` dùng chung thay toàn bộ `window.confirm` (B21); chỉ gọi lại `/admin/dashboard` khi đổi trang (C13); Esc đóng modal duyệt hỏi trước nếu đã gõ ghi chú, bước 1 wizard báo khi tên trống (C14); "Cần bổ sung" dùng chung cả hai phía (C16); liên hệ quản trị viên có email và điện thoại thật lấy từ `constants/contact.ts` (cùng nguồn với chân trang), trang 403 của người dùng thường có lối "Đăng ký làm chủ thể" (C16); nhãn ô ảnh đại diện rõ hơn (C19, chỉ phần nhãn và hướng dẫn); công tắc "Bảng số liệu" chỉ còn đổi nhãn, bỏ `aria-pressed` (C20).

## 4. File đã thay đổi

Từ `8b17d6f` đến nay: 71 file, 5.012 dòng thêm, 524 dòng bỏ (`git diff --stat 8b17d6f..HEAD`). Nhóm chính:

- Styles: `styles/main.css`.
- Component dùng chung mới: `ui/ConfirmDialog.vue`, `map/MapLegend.vue`.
- Composable mới: `useConfirmDialog.ts`, `useFlashFocus.ts`, `useFocusTrap.ts`, `useAdminDashboard.ts`; sửa `useDialogFocus.ts`.
- Util mới: `utils/product-filters.ts`, `utils/product-story.ts`, `router/scroll.ts`, `constants/contact.ts`; sửa `utils/location.ts`, `services/api-error.ts`, `router/index.ts`.
- View: `ProductsView`, `ProductDetailView`, `MapView`, `ForbiddenView`, `ProfileView`, `admin/AdminProductsView`, `admin/AdminDashboardView`, `admin/AdminSubjectApplicationsView`, `subject/SubjectLocationEditorView`, `SubjectLocationsView`, `SubjectProductEditorView`, `SubjectProductsView`, `SubjectProfileView`.
- Component: `ProductCard`, `PresentationGallery`, `ReviewForm`, `ReviewSection`, `LeafletMap`, `StatChart`, `ProductEvidenceManager`, `AuthLayout`.
- Layout: `PortalShell`, `AdminLayout`, `SubjectLayout`.
- Test: 27 file test thêm hoặc sửa cùng thư mục `__tests__`.
- Tài liệu: `docs/ux-ui-audit.md`, `ux-ui-improvement-plan.md`, `design-system.md`, `ux-ui-improvement-report.md`, `CHANGELOG.md`, `README.md`.

## 5. Thay đổi có thể ảnh hưởng logic hoặc API

Không đổi endpoint, schema, quyền hay định dạng dữ liệu. Các thay đổi sau nằm ngoài việc "chỉ trình bày" và cần người review lưu ý:

1. **Router `scrollBehavior`** (`router/scroll.ts`): không đặt lại vị trí cuộn khi cùng một route chỉ đổi query (hiện áp dụng cho `/ban-do`). Các trang khác giữ hành vi cũ; có test.
2. **Bộ lọc sản phẩm công khai:** tham số URL sai (số không hợp lệ, `star` ngoài 3 đến 5, `min > max`) được chuẩn hóa hoặc bỏ trước khi gọi API thay vì gây 422; từ khóa giới hạn độ dài; sắp xếp theo giá khi chưa có giá không còn làm ô chọn lệch URL.
3. **`api-error.ts`:** lỗi 422 (`details[].loc/msg`) giờ được dịch sang tiếng Việt theo trường; các mã lỗi khác giữ nguyên thông điệp. Trường chưa có trong bảng dịch dùng tên gốc.
4. **`AdminProductsView`:** đọc và ghi `route.query`; có thêm một lượt GET danh sách chờ duyệt để đếm huy hiệu độc lập bộ lọc; bộ lọc "sắp hết hạn" và "thiếu quyết định" áp dụng phía client trên các trang đã tải (gọi nhiều trang khi tập dữ liệu lớn, xem mục 7).
5. **`MapView`:** URL là nguồn sự thật cho `search`, `type`, `district`, `diem`, bán kính; "Điểm gần bạn" lọc phía client sau khi lấy dữ liệu; điểm có tọa độ ngoài khung Lâm Đồng không được vẽ (dữ liệu trong DB không đổi).
6. **`utils/location.ts`:** loại hình `other` đổi từ xanh dương sang xám trung tính (`--ocop-neutral-900`) để không trùng `dairy_farm`; ảnh hưởng mọi nơi dùng màu loại hình.
7. **`useDialogFocus`:** mở rộng để hộp thoại mới dùng chung; các hộp thoại cũ (người dùng, danh mục, đánh giá) giữ hành vi, test cũ vẫn đạt.
8. **`window.confirm` → `ConfirmDialog`:** các thao tác xác nhận trở nên bất đồng bộ (`await confirm(...)`); logic gọi API sau khi xác nhận không đổi.
9. **Trang chủ và trang công khai:** `ProductCard` và `main.css` ảnh hưởng mọi trang công khai. Các file này thuộc phần của thành viên khác trong nhóm nên cần Thái và Thuận xem lại khi mở pull request.

## 6. Kết quả kiểm thử thật

Môi trường: PostgreSQL 16 + PostGIS, backend FastAPI, Vite dev server, Playwright (Chromium) với DB thử nghiệm `e2e_ocop` (bộ dữ liệu tách riêng, không phải dữ liệu chính).

**Đã chạy và đạt:**

- Vitest: **77 file, 415 test đạt** (cuối đợt 4).
- `vue-tsc` không lỗi; `vite build` thành công.
- Sản phẩm: axe-core (wcag2a, wcag2aa, wcag21aa, wcag22aa) sạch trên `/`, `/san-pham`, chi tiết; không tràn ngang ở 390, 768, 1440 px, kể cả 9 sản phẩm URL nguồn trần; ngăn kéo bộ lọc dùng được bằng bàn phím.
- Bản đồ: 119 bước tương tác đạt (Enter chọn marker, chọn điểm ở 390×844 thấy thẻ, tọa độ `null` không làm sập, bộ lọc trên URL, Esc, định vị cho phép và từ chối); axe sạch.
- Quản trị và chủ thể: axe sạch, không tràn ngang; liên kết tổng quan mở đúng danh sách; lỗi 500 hiện trong modal; thao tác ghi được mock hoặc chặn.
- Quét lại 90 lượt tải trang sau cải tiến: xem mục 6.1.

### 6.1 Quét lại toàn site sau cải tiến

Quét lại đúng 90 lượt tải trang như audit (30 đường dẫn của khách, người dùng, chủ thể, quản trị; 390, 768, 1440 px; Chromium), sau khi gộp cả bốn đợt:

| Chỉ số | Trước (lượt quét ngay trước đợt 2 đến 4) | Sau |
|---|---|---|
| Tràn ngang | 0 | 0 |
| Lỗi axe-core | 9 lượt tải, cùng một lỗi `label-content-name-mismatch` trên thẻ sản phẩm | **0** |
| Lỗi console ứng dụng | 0 | 0 |
| Mỗi trang đúng một `main` | đạt | đạt (90/90) |
| Request 5xx | 6, đều là `503 /api/v1/news` | 6, đều là `503 /api/v1/news` (nguồn RSS bị sandbox chặn, lỗi môi trường) |

Lưu ý khi đọc bảng: lượt quét "trước" là lượt gần nhất sau khi sửa trang chi tiết sản phẩm tràn ngang và chưa sửa thẻ sản phẩm. Lỗi tràn 1055 px của audit gốc (A3) và lỗi ARIA của bảng so sánh yêu cầu (B19) chỉ xuất hiện ở trạng thái dữ liệu cụ thể (URL nguồn dài, mở modal so sánh), nên được kiểm riêng ở các kịch bản tương tác ở trên, không nằm trong con số 90 lượt tải này. Quét tải trang không thay thế được kiểm tra tương tác.

## 7. Lỗi và hạng mục còn lại

**Đã xác định nhưng chưa sửa (thuộc UX/UI):**

- C6: tiêu đề "3–5 sao" và nút "5 sao" (`seo.ts`, `HomeBento.vue`) chưa khớp dữ liệu (hiện chỉ có 3 và 4 sao); chưa sửa vì nằm ở trang chủ, cần thống nhất nội dung với người phụ trách.
- C4: thứ tự Tab trên mobile của `/ban-do` vẫn theo DOM, khác thứ tự nhìn do `order`; mới xử lý phần Esc.
- C17: chân trang vẫn cao (855 px ở 390 px) và trang tài khoản/đánh giá rỗng còn khoảng trống lớn.
- C15: danh sách sản phẩm và điểm của chủ thể chưa có ô tìm kiếm; `page_size` vẫn cố định.
- C19: ô ảnh đại diện vẫn là URL (chỉ đổi nhãn, thêm hướng dẫn); tải ảnh lên cần thêm endpoint.
- C2: đổi cỡ màn hình đã gọi `invalidateSize` nhưng chưa tự căn lại về marker đang chọn.
- Khoảng chạm của `.btn-sm` ở bản đồ vẫn dưới 44 px; màu cụm marker trên bản đồ chưa chuyển sang token; `tea_coffee` và `vegetable` có màu khá gần nhau; token `--ocop-location-other` chỉ còn nằm trong `tokens.css`.
- Thông tin liên hệ còn lặp ở `constants/contact.ts` và `SiteFooter.vue`.
- Bộ lọc "sắp hết hạn" phía client phải gọi nhiều trang khi dữ liệu lớn; nên thêm tham số ở backend.
- `markercluster.zoomToShowLayer` có một trường hợp biên chưa kiểm tra (chọn điểm đang nằm trong cụm ở mức thu phóng cao).
- Một bước E2E trong kịch bản đóng modal duyệt bằng Esc không ổn định (đôi lần thất bại); chưa xác định do kịch bản hay do giao diện. Khi chạy tay, Esc hoạt động.

**Thuộc backend hoặc dữ liệu, không sửa trong đợt này (đã ghi ở `ux-ui-audit.md` mục 6):**

- B9: tìm kiếm không dấu ("dau" không ra "dâu") cần `unaccent` hoặc cột chuẩn hóa.
- C11: sắp xếp tên theo thứ tự tiếng Việt (collation PostgreSQL).
- C18: địa bàn là văn bản tự do nên biểu đồ lẫn "Đà Lạt", "xã Đức Trọng", "Lâm Hà"; cần chuẩn hóa thành danh mục.
- Giới hạn tọa độ trong khung Lâm Đồng và kiểm trùng tọa độ ở backend khi lưu điểm.
- Quên mật khẩu, trang chi tiết tin tức nội bộ, quản lý tin tức (CMS): chưa có trong sản phẩm.

## 8. Điều không kiểm chứng được

- **Trình đọc màn hình thật** (NVDA, VoiceOver, TalkBack) và **thiết bị cảm ứng thật**: chưa thử; chỉ kiểm bằng axe-core, cây trợ năng và Playwright.
- **Tile OpenStreetMap, Google Fonts và nguồn RSS bị sandbox chặn:** bản đồ kiểm thử không có ảnh nền, font dự phòng được dùng, `/tin-tuc` trả 503. Các lỗi `ERR_TUNNEL_CONNECTION_FAILED` và 503 trong quét là lỗi môi trường. Giao diện bản đồ với tile thật chưa được nhìn thấy.
- **Đăng nhập Google/Facebook thật:** không có khóa; chỉ kiểm bằng giả lập.
- **Trình duyệt khác Chromium** (Safari, Firefox) chưa thử; `color-mix`, `:where`, `:focus-visible`, `backdrop-filter` cần các trình duyệt hiện đại.
- **Tương phản viền focus** đo bằng giá trị token, chưa đo bằng công cụ trên ảnh chụp từng nền.
- **Tải thật, mạng chậm thật và dữ liệu lớn** chưa thử; mạng chậm chỉ mô phỏng bằng chặn và trì hoãn request.
- **Bản triển khai thật (Nginx, HTTPS):** chưa kiểm; mọi thử nghiệm ở dev server.

**Sự cố khi kiểm thử cần ghi nhận:** trong đợt kiểm tra quản trị, một route mock sai mẫu cho một lệnh PATCH đi thẳng tới API thật của **DB thử nghiệm `e2e_ocop`** và chuyển một yêu cầu ngừng hiển thị sang `needs_revision` (đợt audit đầu cũng có một sự cố tương tự với yêu cầu "Mật ong hoa cà phê" và một điểm nháp, đã xóa). Dữ liệu chính của dự án không bị ảnh hưởng. Các kịch bản sau đó khóa mock theo đường dẫn đầy đủ và chặn mọi `PATCH/POST/DELETE` không được mock.

## 9. Đề xuất bước tiếp theo

1. Mở pull request từ nhánh `2312682_HaLuyen_CICDvaSEO`; nhờ Thái và Thuận xem các file công khai chung (`ProductCard`, `main.css`, `HomeBento`, `AppHeader`, `SiteFooter`), quyết định nội dung "3–5 sao" (C6).
2. Chạy thử trên thiết bị thật: iPhone/Android (cảm ứng, bàn phím ảo), và một trình đọc màn hình ở luồng bản đồ, bộ lọc sản phẩm, duyệt sản phẩm.
3. Backend (đợt riêng): tìm kiếm không dấu, collation tiếng Việt, tham số `expiry` và `missing_decision` cho `/admin/products`, chuẩn hóa địa bàn, kiểm tọa độ khi lưu điểm.
4. Thêm tải ảnh đại diện từ máy (cần endpoint), ô tìm kiếm cho danh sách của chủ thể.
5. Đưa kịch bản Playwright (hiện ở ngoài repo) vào CI dưới dạng smoke test cho các luồng chính, kèm axe.
6. Gộp thông tin liên hệ về một nguồn duy nhất, chuyển màu cụm marker sang token.
7. Lập quy trình kiểm tra tương phản tự động cho token mỗi khi đổi `tokens.css`.
