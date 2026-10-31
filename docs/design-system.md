# Design system (phản ánh code đang dùng)

Tài liệu này mô tả những gì **có thật** trong `frontend/src`. Nguồn sự thật là code; khi đổi token hoặc component thì cập nhật tài liệu này cùng lúc. Quy tắc làm việc nằm ở `CLAUDE.md` mục 5.

## 1. Nền tảng

Vue 3, Vite, TypeScript, Bootstrap 5 (lưới, tiện ích, một số lớp nút), Bootstrap Icons qua `AppIcon.vue`, font Be Vietnam Pro (nạp trong `index.html`, thiếu mạng thì dùng `Segoe UI`, `Arial`). Token ở `styles/tokens.css`, kiểu dùng chung ở `styles/main.css`.

## 2. Nhận diện

- Phong cách: nền sáng sương sớm, xanh dương làm màu thương hiệu, vàng dã quỳ làm màu nhấn, xanh lá chỉ mang ý nghĩa (thành công, chè/cà phê, thảo dược).
- Logo: `public/assets/brand/` gồm `bieu-tuong-{32,64,128,192,512}.png` (biểu tượng tròn), `logo-day-du.png` và `logo-day-du-320.png` (logo đầy đủ), `favicon.ico`. Ảnh chia sẻ mạng xã hội: `public/assets/images/og-default.jpg`. Đây là tài nguyên do nhóm thiết kế, **không phải biểu trưng OCOP chính thức hay biểu trưng nhà nước**; không dùng như nhận diện chính thức của chương trình OCOP.
- Vị trí dùng logo: header, chân trang, khối thương hiệu ở cột trái đăng nhập và đăng ký (biểu tượng mờ chìm làm hình nền), trang chủ (tấm logo kính mờ ở màn rộng), trang lỗi, màn hình chờ tải, thanh bên khu quản trị và chủ thể, favicon, ảnh chia sẻ.

## 3. Token (`styles/tokens.css`)

| Nhóm | Token | Ghi chú |
|---|---|---|
| Màu thương hiệu | `--ocop-mist-50…950` | Thang xám xanh. `--ocop-primary-*`, `--ocop-mint-*`, `--ocop-sage-*` là tên cũ trỏ về đây |
| Màu nhấn | `--ocop-daquy-50…800`, `--ocop-accent` | `daquy-300/400` chỉ làm nền kèm chữ `mist-950`, hoặc làm chữ trên nền tối. Chữ vàng trên nền sáng dùng `daquy-700` |
| Trạng thái | `--ocop-danger`, `-success`, `-warning`, `-info` và biến thể `-soft`, `-strong`, `-border` | Dùng cho thông báo, huy hiệu |
| Chữ | `--ocop-text-primary/secondary/muted/tertiary`, `--ocop-text-on-dark`, `--ocop-text-on-dark-muted` | Tương phản từ 4,5:1 trên nền thiết kế cho nó |
| Nền và viền | `--ocop-surface*`, `--ocop-card`, `--ocop-border*`, `--ocop-sidebar*` | |
| Phân loại | `--ocop-tone-*` (leaf, clay, rose, violet, berry, hydrangea, sky…) và `--ocop-location-*` | Nhóm sản phẩm lấy từ `utils/category.ts`, loại hình điểm du lịch từ `utils/location.ts`; cùng một nhóm phải cùng màu ở mọi nơi |
| Khu quản trị | `--admin-*` | Cùng bảng màu, thêm cỡ chữ và khoảng cách riêng cho khung quản trị |
| Chữ | `--ocop-font-family-sans`; `--ocop-font-size-caption` 12 px (nhỏ nhất được dùng), `small` 13 px, `body` 15 px, `body-lg` 16 px, `title-sm/md/lg` | Tiêu đề trang dùng `clamp()` |
| Khoảng cách | `--ocop-space-1…16` (4, 8, 12, 16, 20, 24, 32, 48, 64 px) | |
| Bo góc | `--ocop-radius-sm/md/lg/xl/pill` | |
| Đổ bóng | `--ocop-shadow-sm/card/overlay` | |
| Chiều cao control | `--ocop-control-sm/md/lg` = 40, 44, 48 px | Vùng chạm tối thiểu 44 px |
| Chuyển động | `--ocop-duration-fast/base/slow`, `--ocop-ease-out/in`, `--ocop-transition` | Tôn trọng `prefers-reduced-motion` |
| Kính mờ | `--ocop-glass-*` | Chỉ trên nền ảnh; luôn có phương án nền đặc và theo `prefers-reduced-transparency` |
| Bố cục | `--ocop-container` 1280 px, `--ocop-content` 1216 px, `--ocop-tabbar-height` | Điểm ngắt tham chiếu: 576, 768, 992, 1200 px (trùng Bootstrap) |

Quy ước: không hard-code màu, khoảng cách, bo góc hoặc cỡ chữ trong component; màu trong suốt dùng `color-mix(in srgb, var(--ocop-…) N%, transparent)`.

## 4. Kiểu dùng chung (`styles/main.css`)

- Bố cục: `.site-container`, `.site-content`.
- Tiêu đề khu vực: `.ocop-section-head`, `.ocop-eyebrow`, `.ocop-section-title`, `.ocop-section-copy`, `.ocop-link-more`.
- Nút: `.ocop-btn-main` (hành động chính), `.ocop-btn-accent` (nhấn vàng), `.ocop-btn-ghost` (phụ); ghi đè `.btn-success`, `.btn-outline-success` của Bootstrap theo bảng màu.
- Chuyển động: `.ocop-fade-*`, `.ocop-rise-*`, `.ocop-pop-*`, `.ocop-list-*`, `.ocop-enter`, `.reveal`.
- Trạng thái tải: `.ocop-skeleton`.
- **Viền focus** (`:focus-visible`): outline đặc 3 px `--ocop-primary-700`, offset 2 px; trên nền tối (`.announcement-bar`, `.auth-intro`, lớp `.on-dark`) đổi sang `--ocop-daquy-300`. Không đặt `outline:none` riêng cho từng control; nếu cần chỉnh thì dùng cùng màu và độ dày.

## 5. Component dùng chung

| Nhóm | Component | Dùng cho |
|---|---|---|
| Biểu tượng | `ui/AppIcon.vue` | Mọi icon (không dùng emoji thay icon) |
| Trạng thái tải | `ui/RouteProgress.vue`, `ui/PageSkeleton.vue` | Thanh tiến trình đầu trang; khung xương cả trang (có biểu tượng nhấp nháy) |
| Thông báo toàn cục | `ui/GlobalStatus.vue` | Ngoại tuyến, đã kết nối lại, không mở được trang (kèm "Thử lại") |
| Lỗi trang | `ui/ErrorPage.vue`, `views/NotFoundView.vue`, `ForbiddenView.vue`, `ServerErrorView.vue` | 404, 403, 500 cùng một khung |
| Trạng thái dữ liệu | `ui/StatusPanel.vue` | Đang tải, rỗng, lỗi có nút "Thử lại" ở các trang dữ liệu |
| Hộp thoại xác nhận | `ui/ConfirmDialog.vue` + `composables/useConfirmDialog.ts` | Mọi xác nhận quan trọng (thay `window.confirm`): `role="alertdialog"`, focus vào nút an toàn, bẫy Tab, Esc, trả focus |
| Ảnh banner | `ui/PhotoBanner.vue` | Tiêu đề trang có ảnh, có phương án dự phòng |
| Cuộn | `ui/ScrollToTop.vue` | |
| Thẻ sản phẩm | `products/ProductCard.vue` | Thẻ có vòng focus ngoài, tên truy cập lấy từ nội dung hiển thị |
| Bản đồ | `map/LeafletMap.vue`, `map/MapLegend.vue` | Bản đồ; chú giải loại hình bấm để lọc (icon + chữ, không chỉ màu) |
| Khung trang | `AppHeader`, `SiteFooter`, `MobileTabBar`, `layouts/PortalShell.vue`, `auth/AuthLayout.vue` | Công khai, khu quản trị và chủ thể, đăng nhập |
| Biểu đồ | `admin/StatChart.vue` | Chart.js, có mô tả và bảng số liệu thay thế |

Composable trợ năng: `useDialogFocus` (hộp thoại: focus, Esc, khóa cuộn, trả focus), `useFocusTrap` (bẫy Tab cho ngăn kéo), `useFlashFocus` (cuộn và focus vào thông báo vừa hiện, thuộc tính `data-flash`).

## 6. Mẫu trạng thái

- **Đang tải:** skeleton cùng kích thước nội dung (tránh nhảy bố cục), `aria-busy` hoặc `role="status"`. Chờ chuyển trang: thanh tiến trình sau 150 ms.
- **Rỗng:** nêu lý do và đường đi tiếp (ví dụ nút "Xóa bộ lọc").
- **Lỗi:** thông báo bằng tiếng Việt, không lộ lỗi kỹ thuật, có nút "Thử lại" khi thử lại có ích; lỗi 422 dịch theo trường (`services/api-error.ts`). Thông báo thành công hoặc lỗi sau thao tác phải nằm trong khung nhìn (`useFlashFocus`), `role="status"` hoặc `role="alert"`.
- **Thành công:** thông báo ngắn, tự nêu việc đã làm; hộp thoại nguy hiểm dùng `ConfirmDialog`.

## 7. Trợ năng

Tương phản chữ từ 4,5:1 (chữ lớn 3:1), viền focus từ 3:1, vùng chạm từ 44 px, nhãn cho mọi control, bẫy focus và trả focus ở hộp thoại, `prefers-reduced-motion` và `prefers-reduced-transparency`, biểu đồ có bảng số liệu thay thế, tên truy cập của liên kết chứa nội dung nhìn thấy (WCAG 2.5.3). Kiểm tra bằng axe-core (wcag2a, wcag2aa, wcag21aa, wcag22aa); mục tiêu là không có lỗi.

## 8. Hình ảnh

Chỉ dùng ảnh có giấy phép (Unsplash, nguồn ghi trong `constants/photos.ts`) hoặc ảnh nhóm cung cấp; luôn có phương án dự phòng khi ảnh lỗi (khung giữ chỗ theo màu nhóm). Ảnh sản phẩm lưu ở backend, đường dẫn trong `product_images`.
