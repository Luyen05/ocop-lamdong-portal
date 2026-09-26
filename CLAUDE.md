# CLAUDE.md — Quy tắc làm việc với repo ocop-lamdong-portal

Đồ án: **Cổng thông tin quảng bá nông sản OCOP và bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng**.
Người giao việc: Liêng Hót Ha Luyến (MSSV 2312682). Trao đổi và báo cáo bằng **tiếng Việt**, ngắn gọn.

File này là quy tắc chung cho mọi lần phát triển tiếp theo. Khi quy tắc ở đây mâu thuẫn với yêu cầu mới trong chat, làm theo yêu cầu mới và đề xuất cập nhật file này.

## 1. Git và branch

- Mỗi chức năng một branch mới, đặt tên `2312682_HaLuyen_<TenChucNang>` (ví dụ `2312682_HaLuyen_ToiUuGiaoDien`), tạo từ `main` mới nhất (`git fetch` trước).
- Trước khi tạo branch hoặc bắt đầu sửa: nếu còn thay đổi chưa commit thì **dừng lại và báo**, không tự stash, xóa hay commit hộ.
- Không sửa trực tiếp `main` hay branch chung của nhóm. Không tự merge. **Không push khi chưa được đồng ý.** Code lên `main` qua Pull Request.
- Tác giả commit: `Luyen05 <luyencc05@gmail.com>`.
- **Không thêm dòng ghi công Claude**: không `Co-Authored-By: Claude…`, không `Claude-Session: …`, không "Generated with Claude Code" trong commit hay mô tả PR.
- Mỗi trang (hoặc mỗi phần việc độc lập) một commit. Thay đổi backend là **commit riêng**, tách khỏi commit giao diện.
- Thông điệp commit dạng `loại(phạm vi): mô tả tiếng Việt có dấu`, ví dụ `feat(ui): …`, `feat(api): …`, `fix(backend): …`, `style(ui): …`, `refactor(ui): …`, `docs(ui): …`. Thân commit liệt kê ngắn các thay đổi chính.
- Git trên máy chạy trong môi trường Linux đọc ổ Windows: luôn dùng `git -c core.autocrlf=true …`, nếu không mọi file CRLF sẽ hiện là "modified". Nếu gặp `.git/index.lock` bị kẹt thì cần xin quyền xóa file.

## 2. Phạm vi thay đổi

- Khi việc được giao là **giao diện**: chỉ sửa phần trình bày (template, style, component hiển thị). Không đổi logic gọi API, router, store, tên props/emit, kiểu dữ liệu, trừ khi được cho phép rõ ràng. Mỗi lần được cho phép thì ghi lại trong báo cáo.
- **Không thêm thư viện mới khi chưa hỏi.** Đã được duyệt: Bootstrap 5, Bootstrap Icons, Leaflet + leaflet.markercluster, Chart.js 4 (chỉ đăng ký thành phần cần dùng), font Be Vietnam Pro (Google Fonts). vue-i18n đã bị bỏ, không tự thêm lại.
- Việc lớn về giao diện: **thiết kế trước trên canvas Claude Design, chờ duyệt, rồi mới code**; có backend thì làm backend sau khi giao diện được duyệt.
- Không tự quyết các vấn đề ngoài phạm vi (lưu ảnh lên Firebase/Cloudinary, bảo mật ảnh chưa duyệt…): ghi nhận vào `docs/ui-audit.md` mục 6 và hỏi.

## 3. Điểm dừng

- Việc chia theo giai đoạn. Tại mỗi **[ĐIỂM DỪNG]**: báo cáo ngắn gọn (đã làm gì, kết quả kiểm thử, câu hỏi cần quyết), rồi **chờ trả lời mới làm tiếp**.
- Có nhiều hướng làm: trình bày các phương án kèm ưu nhược điểm, để người dùng chọn.

## 4. Kiểm thử bắt buộc sau mỗi thay đổi code

Frontend (trong `frontend/`):

```
npm test            # vitest
npm run type-check  # vue-tsc --noEmit
npm run build
```

Backend (khi có sửa backend): `python -m pytest -q` trong `backend/`, hoặc `docker compose exec backend python -m pytest -q`.

- Test hỏng vì thay đổi giao diện có chủ đích thì **cập nhật test**; hỏng vì logic thì **sửa code**.
- Chức năng mới phải có test mới (backend: test API, phân quyền; frontend: test component/view).
- Với thay đổi giao diện, kiểm tra thêm:
  - Chạy axe (WCAG 2.2 AA) cho các trang bị ảnh hưởng, **không được có lỗi**.
  - Không có thanh cuộn ngang ở màn 375/390px, 1024px và 1280/1440px.
  - Chụp ảnh màn hình ở máy tính và điện thoại để tự xem lại trước khi báo cáo.
- Trong Docker, thư viện frontend nằm ở volume `frontend_node_modules`. Khi `package.json` đổi, phải chạy `docker compose restart frontend` (container tự `npm install` lúc khởi động) hoặc `docker compose exec frontend npm install`, và nhắc người dùng làm việc này.

## 5. Quy tắc thiết kế giao diện

- **Chỉ dùng biến design token** (`--ocop-*` trong `frontend/src/styles/tokens.css`), không hard-code màu, khoảng cách, bo góc, cỡ chữ. Biểu đồ Chart.js đọc màu từ token lúc vẽ.
- Bảng màu "Sương sớm & dã quỳ" lấy theo ảnh thật Đà Lạt:
  - `mist-50…950` là xám xanh thông ấm, dùng làm nền và chữ.
  - `daquy-50…800` là vàng dã quỳ. Chỉ dùng làm nền (chữ `mist-950`) hoặc đặt trên nền tối. Chữ vàng trên nền sáng thì dùng `daquy-700`.
  - Các tone leaf, clay, berry, hydrangea, sky dùng cho ý nghĩa và nhóm sản phẩm.
- Màu và icon của từng nhóm sản phẩm lấy từ `frontend/src/utils/category.ts`. Màu loại hình điểm du lịch lấy từ `frontend/src/utils/location.ts`. Cùng một nhóm thì màu phải giống nhau ở mọi nơi.
- Class dùng chung trong `main.css`: `.ocop-section-head`, `.ocop-eyebrow`, `.ocop-section-title`, `.ocop-btn-main` / `-accent` / `-ghost`… Tái sử dụng trước khi viết style mới.
- Trợ năng:
  - Tương phản chữ ≥ 4.5:1 (chữ lớn ≥ 3:1).
  - Vùng chạm ≥ 44px.
  - Dùng đúng thẻ (`button`, `a`, `label`) và có focus rõ ràng.
  - Biểu đồ phải có mô tả hoặc bảng số liệu thay thế.
  - Tôn trọng `prefers-reduced-motion` và `prefers-reduced-transparency`.
- Tránh các "mẫu AI sáo mòn": gradient loang, thẻ viền trái màu, emoji thay icon.
- Mẫu thiết kế đã dùng, cần giữ đồng bộ: bento grid, glassmorphism có dự phòng, toggle group, bottom tab bar trên điện thoại, header thu gọn khi cuộn, carousel + chip, faceted search, task queue ở dashboard, container query cho thẻ. Tham khảo tên mẫu ở namethatui.com.
- Câu chữ hướng tới người dân, không dùng thuật ngữ kỹ thuật ở trang công khai. Tiêu đề phải khớp dữ liệu thật (ví dụ không ghi "5 sao" khi dữ liệu là 3–4 sao).
- **Không bịa dữ liệu.** Dùng số liệu thật từ database hoặc placeholder ghi rõ. Mọi trang phải có đủ trạng thái đang tải, rỗng và lỗi (có nút "Thử lại").
- Ảnh: chỉ dùng ảnh thật có giấy phép (Unsplash, có ghi nguồn trong `src/constants/photos.ts`) hoặc ảnh do nhóm cung cấp. Luôn có phương án dự phòng khi ảnh lỗi.

## 6. Kiến trúc và lệnh hữu ích

- Frontend Vue 3 + Vite + TypeScript (`frontend/`). Backend FastAPI + SQLAlchemy + JWT (`backend/`). PostgreSQL 16 + PostGIS (`database/`: `schema.sql`, `migrations/00x_*.sql`, các file seed).
- Chạy toàn bộ bằng Docker: `docker compose up -d` gồm các service `postgres`, `pgadmin`, `backend` (uvicorn `--reload`, gắn `backend/app`) và `frontend` (Vite dev, cổng 5173).
- Database đã có dữ liệu thì chạy migration mới bằng lệnh trong README (mục "Migration cho database đã có dữ liệu"). Không dùng `docker compose down -v` nếu chưa được đồng ý.
- API quản trị nằm dưới `/api/v1/admin/*` và chỉ role `admin` gọi được. Hiện có: `dashboard`, `statistics`, `products`, `subject-applications`, `data-sources`, `product-change-requests`.
- Bản đồ: `/api/v1/locations`, `/api/v1/map/locations` (GeoJSON), `/map/nearby`, `/map/route` (OSRM). Frontend ở `/ban-do`, `/diem-du-lich`.

## 7. Tài liệu cần cập nhật khi làm

- `docs/ui-audit.md`:
  - Bảng lỗi theo mã: G-, TC-, SP-, QT-…
  - Mục 5 là nhật ký xử lý. Mỗi đợt thêm một mục ghi ngày, việc đã làm và số liệu kiểm thử.
  - Mục 6 ghi những việc ngoài phạm vi.
- Tài liệu dự án trên claude.ai (Project) ghi tiến độ từng nhánh. Cập nhật sau mỗi điểm dừng quan trọng.
