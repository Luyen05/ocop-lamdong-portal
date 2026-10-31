# Kế hoạch cải tiến UX/UI

Căn cứ: `docs/ux-ui-audit.md` (mã vấn đề A, B, C trong tài liệu đó). Nhánh làm việc: `2312682_HaLuyen_CICDvaSEO`. Mỗi đợt một commit riêng, không đổi backend, schema hay hợp đồng API.

## Nguyên tắc

- Sửa nhỏ, có thể hoàn nguyên; dùng token và component sẵn có; không thêm thư viện.
- Ghi lại mọi thay đổi vượt phạm vi "chỉ trình bày" (router, dịch lỗi API, đọc query trong view quản trị) ở báo cáo, mục 5.
- Mọi sửa đổi đi kèm test hoặc kiểm tra tương tác; cuối đợt chạy `npm test`, `npm run type-check`, `npm run build`, axe và kiểm tra tràn ngang.
- Hạng mục cần backend hoặc thay đổi dữ liệu được tách riêng (mục 6 của audit), không làm trong kế hoạch này.

## Các đợt

| Đợt | Mục tiêu | Mã vấn đề | File chính | Phụ thuộc | Rủi ro | Hoàn thành khi |
|---|---|---|---|---|---|---|
| 1 | Tiếp cận toàn cục | A1, A2 | `styles/main.css`, `ProductCard.vue` | Không | Thay đổi nhìn thấy trên mọi nút và liên kết | axe sạch; viền focus từ 3:1 |
| 2 | Sản phẩm công khai | A3, B1 đến B7, C5 đến C10 | `ProductsView.vue`, `ProductDetailView.vue`, `PresentationGallery.vue`, `ReviewForm.vue`, `ReviewSection.vue` | Đợt 1 (thẻ) | `ProductsView` lớn, dễ hồi quy bộ lọc | Test view cũ vẫn đạt; thử URL sai, 300 ký tự, tải chậm |
| 3 | Bản đồ | A4, A5, B8 đến B12, C1 đến C4 | `LeafletMap.vue`, `MapView.vue`, `router/index.ts` | Không | Đổi `scrollBehavior` ảnh hưởng mọi trang | Enter chọn marker; chọn điểm ở 390×844 thấy thẻ; điểm tọa độ sai không làm sập bản đồ |
| 4 | Quản trị và chủ thể | A6 đến A9, B13 đến B21, C12 đến C16 | `api-error.ts`, `AdminProductsView.vue`, `AdminDashboardView.vue`, `AdminLayout.vue`, `PortalShell.vue`, `Subject*.vue`, `ConfirmDialog.vue` | Không | Đọc `route.query` trong `AdminProductsView`; thay `window.confirm` đổi luồng thao tác | Liên kết từ số liệu mở đúng danh sách; lỗi hiện trong modal; không còn `window.confirm` |
| 5 | Design system | Tài liệu hóa | `docs/design-system.md` | Đợt 1 đến 4 | Tài liệu lệch code | Mọi token và component nêu trong tài liệu có thật trong `src` |
| 6 | Nghiệm thu | Toàn bộ | Kịch bản E2E, `docs/ux-ui-improvement-report.md` | Đợt 1 đến 5 | | Báo cáo ghi đúng điều đã làm và chưa làm |

## Cách kiểm thử

1. Vitest: chạy file test liên quan sau mỗi nhóm, toàn bộ sau mỗi đợt.
2. `vue-tsc` và `vite build` sau mỗi đợt.
3. Playwright: quét lại 90 lượt tải trang (390, 768, 1440 px) lấy console, 5xx, tràn ngang, axe; kịch bản tương tác riêng cho từng đợt (bàn phím, tải chậm, lỗi 500, từ chối định vị, dữ liệu xấu qua mock).
4. Chụp ảnh và xem lại giao diện ở máy tính và điện thoại.
5. Chỉ dùng DB thử nghiệm; không thao tác phá hủy. Mock `page.route` phải khóa đúng đường dẫn để không đi thẳng tới API.

## Không làm trong đợt này

Tìm kiếm không dấu, collation tiếng Việt, chuẩn hóa địa bàn và tọa độ ở backend, quên mật khẩu, CMS tin tức. Các mục này nằm ở mục 6 của audit và ở phần đề xuất của báo cáo.
