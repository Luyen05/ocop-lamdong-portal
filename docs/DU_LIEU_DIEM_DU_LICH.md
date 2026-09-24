# Dữ liệu điểm du lịch nông nghiệp và bản đồ số

Tài liệu mô tả bộ dữ liệu khảo sát điểm du lịch nông nghiệp dùng cho bản đồ số,
cách nạp vào PostgreSQL/PostGIS và giới hạn sử dụng.

## Phạm vi khảo sát

- Thời điểm thu thập: 23/09/2026.
- Phạm vi: tỉnh Lâm Đồng. Đợt đầu tập trung khu vực Đà Lạt, Lạc Dương, Đơn Dương
  và Bảo Lâm. Khu vực Bình Thuận và Đắk Nông trước đây chưa có điểm nào.
- Tiêu chí chọn: điểm tham quan gắn với sản xuất nông nghiệp (đồi chè, vườn cà
  phê, vườn trái cây, vườn hoa, nông trại), đang đón khách và có tọa độ công khai.
- Nguồn: trang địa điểm công khai trên Foody.vn. Mỗi dòng dữ liệu lưu đường dẫn
  nguồn ở cột `source_url`, hiển thị ở trang chi tiết điểm du lịch.
- Mô tả ngắn do nhóm tự viết, không sao chép nội dung từ nguồn.

## Tệp dữ liệu

| Tệp | Vai trò |
|---|---|
| `data/tourism/diem_du_lich_nong_nghiep_2026.csv` | Bộ dữ liệu khảo sát gốc (UTF-8) |
| `tools/build_tourism_seed.py` | Kiểm tra dữ liệu và sinh file seed |
| `database/seed_tourism_locations.sql` | Seed PostGIS, chạy lặp lại an toàn theo `slug` |
| `database/migrations/008_tourism_location_map.sql` | Bổ sung cột `website`, `source_url` và index |

Các cột CSV:

| Cột | Ý nghĩa |
|---|---|
| `slug` | Định danh URL, chữ thường không dấu, duy nhất |
| `type` | Mã loại hình: `tea_coffee_farm`, `fruit_garden`, `flower_garden`, `dairy_farm`, `vegetable_farm`, `craft_village`, `farmstay`, `other` |
| `district` | Địa bàn theo tên quen thuộc với du khách |
| `latitude`, `longitude` | Tọa độ WGS84 (EPSG:4326) |
| `ticket_price` | Giá vé tham khảo (đồng). Để trống nếu chưa rõ, `0` nếu miễn phí |
| `services` | Các dịch vụ trải nghiệm, phân tách bằng dấu `\|` |
| `source_url` | Nguồn công khai dùng để đối chiếu |

Script sinh seed dừng với thông báo lỗi khi slug trùng hoặc sai định dạng, loại
hình không hợp lệ, giá vé âm, nguồn không dùng `https` hoặc tọa độ nằm ngoài
khung bao tỉnh Lâm Đồng (vĩ độ 10,3–12,95; kinh độ 107,0–109,3).

## Cập nhật dữ liệu

1. Sửa hoặc thêm dòng trong file CSV.
2. Sinh lại seed:

   ```powershell
   python tools/build_tourism_seed.py
   ```

3. Nạp vào database đang chạy (không xóa dữ liệu, chỉ cập nhật theo `slug`):

   ```powershell
   Get-Content .\database\seed_tourism_locations.sql -Raw | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
   ```

Khi chạy lại, seed cập nhật thông tin mô tả và tọa độ nhưng giữ nguyên trạng thái
kiểm duyệt, điểm đánh giá và lượt xem. Database tạo mới bằng Docker tự nạp file
này sau `schema.sql` và `seed_dev.sql`.

## Quy tắc công khai và bản đồ

- API công khai (`/locations`, `/map/*`) chỉ trả điểm có `status = 'approved'`.
  Điểm `pending` hoặc `rejected` không xuất hiện trong danh sách, bản đồ, tìm
  điểm gần hay chỉ đường.
- Tọa độ lưu ở cột `geom GEOMETRY(Point, 4326)`. Khoảng cách và bán kính tính bằng
  `ST_Distance`/`ST_DWithin` trên kiểu `geography` (đơn vị mét).
- Chỉ đường: backend gọi OSRM (`OSRM_BASE_URL`, mặc định máy chủ công khai của
  dự án OSRM), giới hạn thời gian chờ `OSRM_TIMEOUT_SECONDS` và chỉ nhận điểm xuất
  phát trong lãnh thổ Việt Nam. Khi OSRM lỗi, API trả `503 ROUTING_UNAVAILABLE`,
  giao diện vẫn có liên kết mở chỉ đường bằng Google Maps.
- Ảnh nền bản đồ mặc định lấy từ CARTO Voyager (dữ liệu OpenStreetMap); nếu
  không tải được sẽ tự chuyển sang máy chủ tile của OpenStreetMap. Có thể đặt nguồn
  ưu tiên bằng biến `VITE_MAP_TILE_URL` khai báo trong `frontend/.env`.

## Giới hạn

- Dữ liệu chỉ dùng cho đồ án, không phải cơ sở dữ liệu hành chính chính thức.
  Giờ mở cửa, giá vé và liên hệ có thể đã thay đổi sau thời điểm thu thập.
- Tọa độ lấy từ nguồn công khai, chưa kiểm chứng thực địa.
- Các điểm chưa gắn với chủ thể OCOP (`subject_id = NULL`) và chưa liên kết sản
  phẩm. Việc chủ thể tự khai báo địa điểm và liên kết sản phẩm thuộc module quản
  lý địa điểm tiếp theo.
- Hình ảnh: chưa có ảnh thật; giao diện dùng ảnh minh họa theo loại hình.
