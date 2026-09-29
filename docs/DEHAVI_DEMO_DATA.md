# Dehavi Valley → Hân Vinh → Dehavi Showroom

Chuẩn bị dữ liệu ngày 29/09/2026 trên main `0aa5404`. Đây là dữ liệu tham khảo
phục vụ demo, không phải hồ sơ hành chính hoặc xác nhận hiệu lực chứng nhận.
Seed đã được kiểm tra trong PostGIS tách biệt; chưa nạp vào DB demo local.

## Evidence và phạm vi xác minh

| Dữ kiện | Nguồn | Cách lưu |
| --- | --- | --- |
| Valley OCOP 4 sao Lâm Đồng | https://nhandan.vn/ocop/ca-phe-pha-phin-dehavi-valley-prod545.html | `product_sources`: recognition, B1 |
| Valley: 70% Robusta Nam Ban, 30% Arabica Cầu Đất | https://dehavi.com/valley | enrichment, C |
| Công ty TNHH Cà phê Hân Vinh và showroom tại Đông Anh 2 | https://hanvinhcoffee.vn/ve-chung-toi | identity/address, C |
| Showroom có thưởng thức cà phê, quan sát sản xuất và trưng bày sản phẩm công ty | https://dehavi.com/cup-dehavi-showroom | enrichment, C; `tourism_locations.source_url` |
| Mua trực tiếp tại Dehavi Showroom | https://dehavi.com/chinh-sach-giao-nhan-va-van-chuyen | enrichment, C; review note của location |

Thuận đã xác minh nguồn Nhân Dân ngoài repo. Audit ngày 29/09 đọc được kết quả
chỉ mục xác nhận 4 sao nhưng không tải được toàn trang; giới hạn này được lưu
trong `product_sources.notes`. Nguồn B1 không phải quyết định A hoặc bản chụp
chứng nhận. Không gán số chứng nhận, ngày cấp, ngày hết hạn hay cơ quan cấp
chưa đối chiếu. Khi tạo mới, các trường chứng nhận chưa xác minh để NULL.
Seed không sửa chứng nhận hoặc thông tin đã có; dữ liệu cũ cần review riêng.

Liên kết Valley với showroom dựa trên danh mục sản phẩm của hãng và chính sách
mua trực tiếp tại showroom; không cam kết tồn kho tức thời. Arabica Cầu Đất
chỉ là nguồn nguyên liệu. Không tạo bất kỳ liên kết nào với Cầu Đất Farm.

## Tọa độ

- Người đối chiếu: Thuận, thành viên dự án; cung cấp trong session 29/09/2026.
- Phương pháp: **manual verification from Google Maps by project member**.
  Đây không phải dữ liệu GPS đo đạc hiện trường.
- Địa điểm: **Dehavi Showroom**, Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng.
- Tọa độ ghim gốc: latitude `11.842185897748251`, longitude `108.34119094061145`.
- Tọa độ lưu: latitude `11.842186`, longitude `108.341191`.
- PostGIS: `ST_SetSRID(ST_MakePoint(108.341191, 11.842186), 4326)`.
- `location_source='coordinates'`: thành viên cung cấp tọa độ, chưa lưu URL ghim.
  Không gán `google_maps_link` khi chưa có liên kết, không bịa độ chính xác GPS.
- Nguồn chính thức của showroom xác nhận địa điểm/dịch vụ, không được mô tả
  là nguồn tọa độ. Tọa độ cũ `11.8415315,108.3412915` không được dùng.

## File seed và record dự kiến

Chỉ dùng **`database/seed_dehavi_demo.sql`**. Broad seed
`database/seed_public_reference.sql` được giữ nguyên như main; không chạy file
đó để nạp case này. Không sửa schema, migration, generator hoặc API/core.

Seed dùng một transaction và chỉ INSERT, không UPDATE/DELETE/TRUNCATE/DROP.
Khi chưa có dữ liệu, phạm vi tối đa là:

| Bảng | Record được thêm |
| --- | --- |
| categories | 1 danh mục `do-uong` nếu chưa có; không sửa danh mục đã có |
| users | 2 tài khoản bị khóa: `dehavi-demo-import@local.invalid`, `public-reference-han-vinh@local.invalid` |
| subjects | 1 Công ty TNHH Cà phê Hân Vinh, địa chỉ Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng |
| ocop_products | 1 `tham-khao-ca-phe-dehavi-valley`, tên Cà phê pha phin Dehavi Valley, 4 sao |
| data_sources | 5 URL trong bảng evidence |
| product_sources | 6 links: recognition B1; identity/address/enrichment C |
| tourism_locations | 1 `dehavi-showroom`, type `other`, subject Hân Vinh |
| location_ocop_products | 1 quan hệ Valley ↔ Showroom |

Tài khoản kỹ thuật không có password dùng được, không hoạt động; không thay
account đã có. Nếu email kỹ thuật đang active/sai role, subject sai identity
hoặc slug Valley thuộc subject khác thì seed báo lỗi và rollback transaction.
Không tạo các sản phẩm Rowoa/Pine Forest, không sửa subject/product khác.

Các record đã có dùng `ON CONFLICT DO NOTHING`: không sửa tọa độ, status,
review note, ownership, chứng nhận hoặc nội dung đã review. Không khôi phục
archived/rejected thành approved. Nếu showroom trùng slug nhưng thuộc chủ thể
khác hoặc chưa có chủ thể, giữ nguyên và không thêm relation. Phải review riêng
nếu dữ liệu có sẵn khác case này. Product/subject/location mới được approved
cho demo; review note ghi đây là dữ liệu dự án, không phải phê duyệt hành chính.

Subject.geom không nhận tọa độ showroom vì chưa xác minh vị trí trụ sở pháp lý.
Giá Valley 85.000 đồng/gói 250g chỉ là giá tham khảo nguồn, có thể thay đổi.
Không ước lượng giờ mở cửa, giá vé hoặc độ chính xác GPS. Không thêm ảnh giả
bao bì/showroom; UI dùng fallback khi chưa có ảnh. Ảnh đã có được giữ nguyên.

## Runtime chưa apply

Runtime audit: Valley/Hân Vinh chưa có, 60 product public; Location/Map có
blocker `DATABASE_SCHEMA_OUTDATED`. Trước runtime apply phải phối hợp Luyến
đồng bộ migrations **009/011** (và kiểm tra các migration phụ thuộc còn thiếu).
Session này không chạy migration hoặc seed trên `lamdong_ocop`.

Sau khi schema được đồng bộ và được phép apply, chỉ nạp
**`database/seed_dehavi_demo.sql`**, không phải toàn bộ `seed_public_reference.sql`.
Lệnh tham khảo từ repo root, chưa được chạy trên runtime:

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new()
Get-Content .\database\seed_dehavi_demo.sql -Raw -Encoding UTF8 | docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## Kiểm tra trong môi trường tách biệt

`backend/tests/test_dehavi_seed.py` mặc định skip nếu không truyền DSN test.
Test không dùng `DATABASE_URL`. Chỉ chấp nhận DB `dehavi_seed_test` tại
`127.0.0.1` và cờ `DEHAVI_ISOLATED_POSTGIS=1`; phải chạy trong container tạm,
không mở cổng host, không nối mạng ứng dụng. Dữ liệu thử được nạp từ SQL thật
vào schema mới cho mỗi test. Test dùng `schema.sql` hiện tại, không chứng minh
việc nâng cấp một database cũ đã thành công.

Ví dụ PowerShell tại repo root, dùng các Docker image đã có trên máy:

```powershell
$repoRoot = (Get-Location).Path
$backendImage = docker inspect --format '{{.Image}}' lamdong-backend
docker run -d --pull never --name dehavi-seed-test --network none --tmpfs /var/lib/postgresql/data -e POSTGRES_DB=dehavi_seed_test -e POSTGRES_PASSWORD=dehavi-test-only postgis/postgis:16-3.4
docker exec dehavi-seed-test pg_isready -U postgres -d dehavi_seed_test
# Chờ pg_isready báo accepting connections rồi chạy:
docker run --rm --pull never --network container:dehavi-seed-test -e DEHAVI_ISOLATED_POSTGIS=1 -e DEHAVI_SEED_TEST_DATABASE_URL=postgresql://postgres:dehavi-test-only@127.0.0.1:5432/dehavi_seed_test -e DEHAVI_SEED_SQL_DIR=/seed -v "${repoRoot}/database:/seed:ro" -v "${repoRoot}/backend/app:/app/app:ro" -v "${repoRoot}/backend/tests:/app/tests:ro" $backendImage python -m pytest -q -p no:cacheprovider tests/test_dehavi_seed.py
docker rm -f dehavi-seed-test
```

Kiểm tra: public Product API + recognition B1 + related_locations; Location API
kèm subject và danh sách `products`; GeoJSON đúng longitude/latitude; Nearby tính
bằng PostGIS; Route gửi đúng điểm showroom tới OSRM; chạy lại không nhân đôi,
giữ moderation, không chiếm slug khác chủ thể; bỏ recognition thì Valley bị
ẩn dù còn nguồn C. OSRM được mock, không xác nhận tuyến đường thực tế.

Kết quả kiểm tra ngày 29/09/2026:

| Nhóm kiểm tra | Kết quả |
| --- | --- |
| Seed Dehavi hẹp + API trên PostGIS tạm | 8 PASS |
| Bộ dữ liệu OCOP hiện có | 10 PASS |
| Backend Product/Location/Map regression | 31 PASS |
| Frontend: 4 suite Product + Location Detail + Map | 34 PASS |
| Frontend type-check | PASS |

Frontend ở đây được kiểm tra bằng component tests, chưa có browser E2E với
case Dehavi trên runtime. Sau test, API demo vẫn không có Dehavi và Location
vẫn trả 503 do schema cũ; không seed hoặc migration nào được apply vào DB demo.

Sau khi có phê duyệt apply và runtime schema phù hợp, các URL demo dự kiến:

- `/san-pham/tham-khao-ca-phe-dehavi-valley`
- `/diem-du-lich/dehavi-showroom`
- `/ban-do` (tìm Dehavi Showroom, Nearby / Route)

Các URL này chưa phải bằng chứng case đã được nạp vào frontend/backend demo.
