# Dữ liệu và nguồn

Tài liệu mô tả dữ liệu đi kèm repo: dữ liệu gốc, file seed, nguồn kiểm chứng, tài khoản demo và cách tái tạo.

- [1. Nguyên tắc](#1-nguyên-tắc)
- [2. Các file seed](#2-các-file-seed)
- [3. Mức xác minh nguồn](#3-mức-xác-minh-nguồn)
- [4. Sản phẩm OCOP tham khảo](#4-sản-phẩm-ocop-tham-khảo)
- [5. Điểm du lịch nông nghiệp](#5-điểm-du-lịch-nông-nghiệp)
- [6. Dữ liệu kiểm thử quy trình](#6-dữ-liệu-kiểm-thử-quy-trình)
- [7. Ví dụ đầy đủ: Dehavi](#7-ví-dụ-đầy-đủ-dehavi)
- [8. Ảnh](#8-ảnh)
- [9. Tái tạo dữ liệu](#9-tái-tạo-dữ-liệu)

## 1. Nguyên tắc

- **Không bịa dữ liệu.** Thông tin chưa có nguồn thì để trống; giá không công bố thì để trống hoặc ghi "liên hệ chủ thể", không ước lượng.
- Dữ liệu chỉ phục vụ đồ án (phát triển, kiểm thử, demo), **không** thay thế cơ sở dữ liệu OCOP chính thức. Hạng sao, giá, địa chỉ, giờ mở cửa có thể thay đổi sau ngày thu thập.
- Bản nộp và buổi demo dùng dữ liệu **nhập tay qua giao diện** (quyết định 07/10/2026). Các seed ở mục 2 dùng cho phát triển và kiểm thử.
- Số điện thoại, email cá nhân xuất hiện trên báo không đưa vào dữ liệu công khai.

## 2. Các file seed

Database mới tạo bằng Docker tự chạy `schema.sql`, `seed_dev.sql`, `seed_tourism_locations.sql`. Các seed còn lại nạp tay theo thứ tự dưới đây (lệnh trong README); mọi seed chạy lặp lại không tạo bản ghi trùng.

| Thứ tự | File | Nội dung | Sau khi nạp (tích lũy) |
|---|---|---|---|
| 1 | `seed_dev.sql` | 6 danh mục, 4 sản phẩm demo (ẩn khỏi trang công khai), 2 tài khoản demo bị khóa | 4 sản phẩm |
| 2 | `seed_tourism_locations.sql` | 9 điểm du lịch nông nghiệp đã duyệt (sinh từ CSV, mục 5) | 9 điểm |
| 3 | `seed_public_reference.sql` | 16 sản phẩm tham khảo từ nguồn công khai, 7 chủ thể kỹ thuật | 20 sản phẩm |
| 4 | `seed_ocop_2025_2026.sql` | Sản phẩm OCOP 2025–2026 sinh từ `data/ocop`, kèm 17 văn bản nguồn | 71 sản phẩm, 34 chủ thể |
| 5 | `seed_product_workflow.sql` | 6 sản phẩm và 3 tài khoản để trình diễn quy trình kiểm duyệt (mục 6) | 77 sản phẩm, 10 điểm |
| 6 | `seed_dehavi_demo.sql` | Ví dụ đầy đủ sản phẩm → chủ thể → điểm Dehavi Showroom (mục 7) | 11 điểm, 22 nguồn |
| 7 | `seed_dehavi_media.sql` | Ảnh chính thức có ghi nguồn cho Dehavi Valley và Dehavi Showroom | |

Nạp đủ 7 file: **61 sản phẩm** và **10 điểm du lịch** hiển thị công khai (còn lại là dữ liệu demo, nháp, chờ duyệt hoặc thiếu nguồn công nhận).

**Tài khoản kỹ thuật `@local.invalid`:** chủ thể nhập từ nguồn công khai được gắn với tài khoản kỹ thuật luôn ở trạng thái khóa, không đăng nhập được. Nội dung của chúng vẫn hiển thị (xem `docs/NGHIEP_VU.md` mục 3).

## 3. Mức xác minh nguồn

| Mức | Ý nghĩa | Cách dùng |
|---|---|---|
| A | Quyết định công nhận chính thức có chữ ký, hoặc phụ lục sản phẩm | Đủ để công khai nếu đủ trường bắt buộc |
| B1 | Báo hoặc cổng cơ quan nhà nước xác nhận đã công nhận/trao chứng nhận | Công khai được, ghi rõ giới hạn của nguồn |
| B2 | Đề xuất, chấm điểm trước khi có kết quả công nhận | Chỉ dữ liệu chờ xác minh, không công khai |
| C | Website chủ thể hoặc nguồn thương mại | Chỉ bổ sung mô tả, quy cách, giá, ảnh; không xác nhận hạng sao |

Văn bản hành chính dùng làm bằng chứng được lưu trong `docs/sources/ocop/` (danh mục và giải thích trong `docs/sources/ocop/README.md`). Bài báo, trang thông tin chỉ lưu liên kết trong `data/ocop/source_manifest.csv` để repo không quá lớn. Mỗi nguồn trong database (`data_sources`) có số văn bản, cơ quan ban hành, ngày, URL, đường dẫn file và SHA-256.

## 4. Sản phẩm OCOP tham khảo

- **`seed_public_reference.sql`** (thu thập 10/09/2026): 16 sản phẩm của 7 chủ thể (Trà Ngọc Duy, Cà phê Hân Vinh/Dehavi, Seagull, Ceres, HTX Bechamp Đắk Nông, Atiso Hoàng An…) từ cổng thông tin tỉnh, chuyên trang OCOP Báo Nhân Dân và website chủ thể. Sản phẩm không công bố giá lưu `price = 0`, đơn vị "liên hệ chủ thể". Ảnh là SVG minh họa cục bộ. Chạy lại không đưa sản phẩm admin đã `suspended`/`archived` trở lại `approved`.
- **`seed_ocop_2025_2026.sql`**: sinh từ `data/ocop/ocop_records.json` và `ocop_lamdong_2025_2026.xlsx` bằng `tools/build_ocop_seed.mjs`; mỗi sản phẩm gắn với văn bản nguồn theo mức xác minh. Phạm vi là tỉnh Lâm Đồng sau sắp xếp đơn vị hành chính (gồm khu vực Bình Thuận, Đắk Nông trước đây); địa chỉ giữ theo nguồn, chỉ thêm địa chỉ hiện hành khi có ánh xạ theo Nghị quyết 1671/NQ-UBTVQH15.
- Số liệu tổng quan của tỉnh (527 chủ thể, 941 sản phẩm sau đợt 1/2026, theo Tạp chí Khoa học và Công nghệ Việt Nam) chỉ để tham khảo, không phải số bản ghi cần nhập.

## 5. Điểm du lịch nông nghiệp

- **Nguồn:** khảo sát ngày 23/09/2026, trang địa điểm công khai trên Foody.vn; mô tả do nhóm tự viết. Đợt đầu tập trung Đà Lạt, Lạc Dương, Đơn Dương, Bảo Lâm.
- **Tiêu chí chọn:** điểm tham quan gắn với sản xuất nông nghiệp (đồi chè, cà phê, vườn trái cây, vườn hoa, nông trại), đang đón khách, có tọa độ công khai. Tọa độ chưa kiểm chứng thực địa.
- **Dữ liệu gốc:** `data/tourism/diem_du_lich_nong_nghiep_2026.csv` (UTF-8). Các cột chính: `slug`, `type` (`tea_coffee_farm`, `fruit_garden`, `flower_garden`, `dairy_farm`, `vegetable_farm`, `craft_village`, `farmstay`, `other`), `district`, `latitude`, `longitude` (WGS84), `ticket_price` (đồng; trống là chưa rõ, `0` là miễn phí), `services` (phân tách bằng `|`), `source_url`.
- **Sinh seed:** `python tools/build_tourism_seed.py`. Script dừng khi slug trùng, loại hình sai, giá âm, nguồn không phải `https`, hoặc tọa độ ngoài khung tỉnh Lâm Đồng (vĩ độ 10,3–12,95; kinh độ 107,0–109,3). Chạy lại seed cập nhật mô tả, tọa độ nhưng giữ trạng thái duyệt, điểm đánh giá, lượt xem.
- Các điểm này do quản trị viên nhập (không gắn chủ thể) và chưa có ảnh thật; giao diện dùng ảnh dự phòng theo loại hình.

## 6. Dữ liệu kiểm thử quy trình

`seed_product_workflow.sql` chỉ dùng cho môi trường phát triển. Giấy chứng nhận là SVG có dòng **KHÔNG CÓ GIÁ TRỊ PHÁP LÝ**.

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản trị viên | `admin.ocop.demo@example.com` | `DemoOCOP@2026` |
| Chủ thể đã duyệt | `chuthe.ocop.demo@example.com` | `DemoOCOP@2026` |
| Người dùng có hồ sơ chủ thể đang chờ | `ungvien.ocop.demo@example.com` | `DemoOCOP@2026` |

> **Cảnh báo:** mật khẩu demo được công bố trong repo. Không nạp seed này vào database triển khai thật.

Chủ thể demo có 6 sản phẩm ở đủ các trạng thái: bản nháp (Trà atiso túi lọc), chờ duyệt (Mứt dâu Đà Lạt), cần bổ sung (Cà phê Arabica), đã duyệt (Hồng treo gió Đà Lạt – kèm yêu cầu cập nhật đang chờ; Mật ong hoa cà phê – kèm yêu cầu ngừng hiển thị đang chờ), bị từ chối (Bột rau má sấy lạnh). Tất cả có cờ `is_demo` nên không xuất hiện ở trang công khai kể cả khi đã duyệt. Chạy lại file seed để đưa dữ liệu demo về trạng thái ban đầu sau khi luyện demo.

## 7. Ví dụ đầy đủ: Dehavi

Chuỗi dữ liệu minh họa trọn chức năng "tìm điểm trải nghiệm theo sản phẩm":

```text
Cà phê pha phin Dehavi Valley (OCOP 4 sao, nguồn B1)
  → Công ty TNHH Cà phê Hân Vinh
  → Dehavi Showroom (Khu Đông Anh 2, Nam Ban, Lâm Hà) — tọa độ 11.842186, 108.341191
  → điểm gần nhất (PostGIS) → chỉ đường (OSRM)
```

- Slug: sản phẩm `tham-khao-ca-phe-dehavi-valley`, điểm `dehavi-showroom`.
- Nguồn: Báo Nhân Dân (công nhận 4 sao, mức B1), website Dehavi và Hân Vinh (thành phần, địa chỉ, dịch vụ showroom, mua trực tiếp; mức C). Không gán số chứng nhận, ngày cấp, cơ quan cấp chưa đối chiếu.
- Tọa độ do thành viên dự án đối chiếu thủ công trên Google Maps (29/09/2026), làm tròn 6 chữ số; `location_source = 'coordinates'`; không phải GPS đo hiện trường.
- Liên kết sản phẩm ↔ điểm dựa trên chính sách mua trực tiếp tại showroom; không liên kết với Cầu Đất Farm dù nguyên liệu có Arabica Cầu Đất.
- `seed_dehavi_demo.sql` chỉ INSERT trong một transaction, không sửa dữ liệu đã có. Test riêng `backend/tests/test_dehavi_seed.py` và `test_dehavi_media_seed.py` chỉ chạy với một PostGIS tạm tên `dehavi_seed_test` tại `127.0.0.1` (biến `DEHAVI_SEED_TEST_DATABASE_URL`, `DEHAVI_ISOLATED_POSTGIS=1`), không bao giờ chạy trên database demo; mặc định được bỏ qua.

## 8. Ảnh

- Chỉ dùng ảnh có giấy phép (Unsplash, ghi nguồn trong `frontend/src/constants/photos.ts`), ảnh do đơn vị cho phép, hoặc ảnh nhóm tự chụp. Ảnh minh họa luôn có nhãn "Ảnh minh họa".
- Mỗi ảnh lưu được nguồn (`source_url`), tác giả (`credit`), giấy phép (`license`); để trống `license` khi chưa rõ quyền dùng, không suy diễn.
- Ảnh Dehavi (`seed_dehavi_media.sql`) là ảnh CDN chính thức của đơn vị, credit "Dehavi Coffee / Công ty TNHH Cà phê Hân Vinh", `license` để trống. `storage_path` dạng `external/...` chỉ để định danh, không phải file tải lên.
- Ảnh tải lên lưu cục bộ (`backend/uploads`) hoặc Cloudinary (xem `docs/CAU_HINH.md`). Luôn có ảnh dự phòng khi ảnh lỗi.

## 9. Tái tạo dữ liệu

| Việc | Lệnh |
|---|---|
| Tải lại văn bản PDF nguồn | `tools/download_ocop_sources.ps1` (sau đó cập nhật SHA-256 trong `data/ocop/source_manifest.csv`) |
| Sinh bảng tổng hợp Excel | `node tools/build_ocop_workbook.mjs` |
| Sinh seed sản phẩm OCOP | `node tools/build_ocop_seed.mjs` |
| Sinh phụ lục nguồn (Word, ghi vào `artifacts/`, không commit) | `python tools/build_ocop_appendix.py` (cần `python-docx`) |
| Sinh seed điểm du lịch | `python tools/build_tourism_seed.py` |
| Kiểm tra dữ liệu gốc | `python -m pytest -q tests/data` (thư mục gốc repo) |
