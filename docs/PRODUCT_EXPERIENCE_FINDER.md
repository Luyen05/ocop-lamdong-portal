# Product Experience Finder

Tài liệu phục vụ báo cáo và demo PR #12 `feat(products): finalize OCOP product experience`, branch `feat/product-ocop-ui-polish`. Audit ngày 07/10/2026 dựa trên code, tests và dữ liệu trong repository. Không thêm chức năng nghiệp vụ, không thay API contracts, không chạy migration hoặc seed trên database runtime trong vòng audit này.

## 1. Mục tiêu chức năng

Kết nối thông tin sản phẩm OCOP với điểm mua và trải nghiệm đã được liên kết trong dữ liệu. Người dùng xem sản phẩm, tìm điểm liên quan, chủ động cấp quyền vị trí để xem khoảng cách, rồi xem điểm đến hoặc yêu cầu chỉ đường. Chức năng tận dụng Location, Leaflet, PostGIS và OSRM hiện có của dự án.

## 2. Bài toán người dùng

Sau khi đọc về sản phẩm, người dùng cần biết mua hoặc trải nghiệm ở đâu, địa chỉ và dịch vụ nào có sẵn, ai quản lý điểm đến và đi tới đó như thế nào. Finder hiển thị các điểm liên quan tới sản phẩm; kết quả Nearby chỉ bổ sung khoảng cách cho những quan hệ đã có. Chức năng không xác nhận tồn kho tức thời hoặc tự suy luận quan hệ từ tên sản phẩm, nguyên liệu hay khoảng cách địa lý.

## 3. Luồng nghiệp vụ

```text
Product → related_locations → Experience Finder
                                 │
                  Bấm “Tìm điểm gần tôi”
                                 ↓
                    Browser Geolocation → Nearby
                                 ↓
                   Ghép khoảng cách với các relation
                                 ↓
                   Xếp điểm có khoảng cách gần trước
                                 ↓
                    Location Detail → Map
                                        ↓
                       Bấm xác nhận lấy vị trí/chỉ đường
                                        ↓
                                    OSRM Route
```

1. Product Detail tải sản phẩm theo slug và hiển thị ảnh, nguồn ảnh, badge sao OCOP, chủ thể, câu chuyện và nguồn chính thức nếu có.
2. CTA “Tìm nơi mua & trải nghiệm” mở `/san-pham/:slug/diem-trai-nghiem`. Finder tải Product và đọc `related_locations`.
3. Với từng relation, Finder tải Location Detail để bổ sung ảnh, địa chỉ, dịch vụ và đơn vị quản lý. Lỗi bổ sung không làm mất tên điểm và các action.
4. Khi người dùng bấm “Tìm điểm gần tôi”, trình duyệt xin vị trí. Finder gọi Nearby với bán kính 200 km, tối đa 50 kết quả. Chỉ lấy khoảng cách cho relation khớp `id` hoặc `slug`; bỏ qua điểm không liên quan.
5. Các điểm có khoảng cách được xếp tăng dần; relation không nằm trong kết quả vẫn hiển thị cuối danh sách với “Chưa có khoảng cách”. Đây không phải bằng chứng điểm đã đóng cửa hoặc không bán sản phẩm.
6. “Xem chi tiết” mở Location Detail. “Xem bản đồ” mở `/ban-do?diem=:slug`. “Chỉ đường” mở `/ban-do?diem=:slug&action=route`.
7. Map chọn điểm theo `diem`. Route intent chỉ hiển thị hướng dẫn xác nhận; không tự gọi GPS hoặc OSRM khi mở trang. Người dùng bấm nút chỉ đường để tính tuyến. Vị trí đã có trong Map có thể được dùng lại; Finder không truyền vị trí qua query string.
8. Tuyến thành công được vẽ trên Leaflet và hiển thị khoảng cách cùng thời gian lái xe ước tính.

## 4. Thành phần frontend

| Thành phần | Trách nhiệm |
| --- | --- |
| `ProductsView.vue` | Danh sách, tìm kiếm, bộ lọc và mở sản phẩm |
| `ProductDetailView.vue` | Nội dung sản phẩm, chứng nhận, nguồn, CTA Finder |
| `ProductExperienceView.vue` | Relations, bổ sung Location Detail, GPS chủ động, ghép Nearby và action |
| `LocationDetailView.vue` | Ảnh, địa chỉ, giờ mở cửa, dịch vụ, chủ thể, sản phẩm tại điểm và mini-map |
| `LocationsView.vue` | Danh sách điểm đến độc lập với Finder |
| `MapView.vue` | Điểm đang chọn, Nearby của Map, route intent, yêu cầu tuyến và summary |
| `LeafletMap.vue` | Marker, tile, vị trí người dùng và đường tuyến |
| `PresentationGallery.vue` | Ảnh chính, chọn ảnh, attribution và fallback khi lỗi/thiếu ảnh |
| `ProductCard.vue` | Ảnh, sao OCOP, tên, danh mục, chủ thể và giá |
| `services/products.ts`, `services/locations.ts` | Gọi API hiện có |
| `utils/location.ts` | Định dạng mét/km, thời gian, giá vé và URL ngoài an toàn |

Finder dùng một card mỗi hàng, desktop từ 768 px chia media/content 42%/58%, mobile xếp ảnh trên và nội dung dưới. Ô media được giữ cả khi bổ sung Location Detail đang tải hoặc lỗi. CTA lần lượt là Chỉ đường, Xem bản đồ, Xem chi tiết. Location Detail reuse ProductCard trong wrapper riêng; 1–2 sản phẩm dùng layout rộng và horizontal từ 768 px, hai card chia cột từ 1200 px. Một card vẫn chiếm cả hàng.

## 5. API sử dụng

Các đường dẫn dưới đây có prefix `/api/v1` theo backend. Frontend cấu hình base URL bằng `VITE_API_BASE_URL`.

| GET endpoint | Input/chức năng |
| --- | --- |
| `/products` | Danh sách theo search, category, star, district, giá, sort và phân trang |
| `/products/filter-options`, `/categories` | Tùy chọn danh sách sản phẩm |
| `/products/{slug}` | Product Detail, images, recognition_sources, related_locations |
| `/locations`, `/locations/filter-options` | Danh sách và bộ lọc điểm đến |
| `/locations/{slug}` | Ảnh, liên hệ, giờ mở cửa, dịch vụ, subject và products |
| `/map/locations` | GeoJSON của điểm public, dùng chọn điểm và marker |
| `/map/nearby` | latitude, longitude, radius_km, limit, type tùy chọn; trả distance_m |
| `/map/route` | destination là slug; from_latitude/from_longitude; trả distance_m, duration_s, geometry |

Finder dùng Nearby 200 km/50 kết quả; Map dùng 50 km/5 kết quả. Hai màn hình có phạm vi riêng, không coi toàn bộ Nearby của Map là các điểm bán sản phẩm. Route frontend có timeout 20 giây; các API thông thường có timeout 10 giây.

## 6. Dữ liệu Product–Location

`location_ocop_products` lưu quan hệ nhiều–nhiều giữa `ocop_products` và `tourism_locations`. Product Detail trả relation summary gồm id, name, slug, type_label và district. Finder gọi Location Detail vì relation summary không chứa toàn bộ ảnh/địa chỉ/dịch vụ.

Location Detail trả danh sách sản phẩm public tại điểm. Product và Location dùng bộ lọc công khai hiện có; điểm chưa duyệt không xuất hiện trong `related_locations`. Quan hệ Product–Location tách biệt với quan hệ subject: chung chủ thể không tự động chứng minh mọi sản phẩm đều được bán tại mọi điểm của chủ thể.

## 7. Vai trò PostGIS

Điểm được lưu bằng `GEOMETRY(Point, 4326)`, theo WGS84. Thứ tự PostGIS/GeoJSON là **longitude, latitude**; geolocation trả các thuộc tính latitude và longitude riêng.

Backend dùng `ST_DWithin` để lọc theo bán kính và `ST_Distance` để tính khoảng cách trên kiểu `geography`, đơn vị mét; kết quả sắp tăng dần theo khoảng cách, rồi id. Khoảng cách Nearby là khoảng cách địa lý trực tiếp giữa hai điểm, không phải chiều dài đường lái xe. SQLite trong tests đăng ký các hàm Haversine thay thế; tests PostGIS tách biệt kiểm tra dữ liệu và flow trên PostgreSQL thật.

## 8. Vai trò Browser Geolocation

`navigator.geolocation.getCurrentPosition` cung cấp vị trí xuất phát khi người dùng bấm nút. Options hiện tại: `enableHighAccuracy: false`, timeout 10.000 ms, `maximumAge: 60.000` ms. Vị trí phụ thuộc trình duyệt/thiết bị và quyền truy cập; không cam kết độ chính xác GPS đo đạc.

Mở Product, Finder, Location hoặc Map với route intent không tự xin GPS. Geolocation cần môi trường trình duyệt cho phép, thường là HTTPS hoặc localhost. Finder giữ vị trí ở biến của lần gọi để truy vấn Nearby; không ghi vị trí này vào database hoặc URL. Backend nhận tọa độ trong query request để tính khoảng cách/tuyến.

## 9. Vai trò OSRM

Backend `services/routing.py` gọi OSRM `route/v1/driving` với thứ tự longitude,latitude cho điểm xuất phát và điểm đến, yêu cầu GeoJSON. Backend kiểm tra response, khoảng cách/thời gian và xử lý lỗi dịch vụ; frontend vẽ geometry bằng Leaflet.

OSRM cung cấp tuyến đường bộ và thời gian ước tính. Summary dùng `formatDistance` và `formatDuration`, hiển thị “khoảng … lái xe”. Không mô tả đây là điều hướng từng chặng, dự báo giao thông thời gian thực hoặc bảo đảm thời gian đến. API hiện có giới hạn điểm xuất phát trong khung bao Việt Nam (latitude 8–23,5; longitude 102–110).

## 10. Xử lý quyền vị trí và lỗi

| State | Hành vi hiện tại |
| --- | --- |
| Product/Finder loading | Detail có skeleton; Finder có thông báo role=status |
| Product API error/404 | Hiển thị lỗi; Product Detail phân biệt 404, có link quay lại; Finder hiển thị message API và nút Thử lại |
| Không có related_locations | Empty state rõ ràng, không gọi Location/GPS/Nearby |
| Location enrichment loading | Thông báo tải; giữ ô media và action, địa chỉ ghi Đang tải |
| Location enrichment error | Giữ relation summary/action; báo thông tin bổ sung chưa tải được, không giả định thiếu dữ liệu |
| Location Detail loading/error/404 | Skeleton; thông báo lỗi hoặc không tìm thấy; link quay lại danh sách |
| GPS idle | Nút Tìm điểm gần tôi và hint xin quyền sau khi bấm |
| GPS loading | Nút disabled và đổi text; ngăn bấm lặp trong Finder |
| Permission denied | Hướng dẫn bật quyền rồi thử lại; không gọi Nearby/Route khi chưa có vị trí |
| GPS unavailable/timeout/unsupported | Message riêng; nút Finder được bật lại |
| Nearby API failure | Hiển thị lỗi, giữ các relation; bấm lại nút để thử lại |
| Nearby không khớp relation | Giữ điểm, ghi chưa có khoảng cách; không bổ sung điểm không liên quan |
| Route loading/error | Nút Map disabled khi định vị/tìm đường; có message lỗi và Google Maps fallback |
| Route success | Polyline, khoảng cách đường đi và thời gian ước tính |
| Ảnh đang tải | Khung có tỷ lệ cố định để giữ chỗ; chưa có spinner tải riêng từng ảnh |
| Ảnh thiếu/lỗi | Gallery/ProductCard chuyển fallback rõ ràng, không dùng ảnh giả; gallery không hiện credit của ảnh bị lỗi |
| Mobile/accessibility | Stack responsive, actions wrap, alt ảnh, label/aria cho gallery và map, focus-visible chung, status/alert cho Finder và route |

Finder dùng generation để bỏ qua response cũ khi đổi slug/unmount, gồm Product, Location enrichment, GPS và Nearby. Vòng audit không thay logic business hoặc Map core. Không có browser E2E mới trong vòng này; responsive được đối chiếu CSS và component tests, chưa phải xác nhận screenshot mới trên thiết bị thật.

## 11. Case study Dehavi

```text
Cà phê pha phin Dehavi Valley (OCOP 4 sao)
  → Công ty TNHH Cà phê Hân Vinh
  → relation tới Dehavi Showroom
  → tọa độ (11.842186, 108.341191)
  → Nearby từ vị trí người dùng
  → Map chọn showroom
  → OSRM Route sau thao tác xác nhận
```

Product slug: `tham-khao-ca-phe-dehavi-valley`. Location slug: `dehavi-showroom`. Showroom ở Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng; media seed ghi giờ mở cửa `06:30–17:30`. Giá trong dữ liệu là tham khảo; ảnh Valley thể hiện bao bì 500gr, trong khi giá/unit seed sản phẩm là gói 250g: ảnh minh họa dòng sản phẩm, không dùng để suy ra quy cách bán hoặc thay giá.

Tọa độ gốc do Thuận đối chiếu thủ công từ Google Maps ngày 29/09/2026: latitude `11.842185897748251`, longitude `108.34119094061145`; lưu làm tròn 6 chữ số. Nguồn showroom xác nhận địa điểm/dịch vụ, không phải nguồn đo tọa độ. Chưa lưu URL ghim Google Maps. Không nối sản phẩm tới Cầu Đất Farm chỉ vì Arabica Cầu Đất xuất hiện trong nguồn nguyên liệu.

GET API public trên backend runtime đã xác nhận Product có 1 ảnh và relation tới showroom; Location có 1 ảnh, giờ mở cửa `06:30–17:30` và relation ngược về Valley; Map trả tọa độ GeoJSON `[108.341191, 11.842186]`. Nearby với điểm xuất phát kiểm tra đúng tọa độ showroom trả `distance_m=0.0`; đây là smoke check bằng tọa độ cố định, không phải kết quả GPS người dùng. Route live từ tọa độ kiểm tra Đà Lạt `(11.9404, 108.4383)` tới showroom trả HTTP 200, provider OSRM, `distance_m=25182.4`, `duration_s=1416.0`, geometry 1011 điểm. Các con số này ghi lại lần kiểm tra, không hardcode trong UI hoặc cam kết cho lần demo sau. Các ghi chú “Runtime chưa apply” trong `DEHAVI_DEMO_DATA.md` là lịch sử audit 29/09, không phải kết luận hiện tại. Session này không apply lại dữ liệu.

## 12. Nguồn dữ liệu và hình ảnh

Các nguồn sau được ghi trong dữ liệu dự án, không được tái xác minh trực tuyến trong vòng code audit này:

| Nguồn lưu trong repository | Vai trò |
| --- | --- |
| `https://nhandan.vn/ocop/ca-phe-pha-phin-dehavi-valley-prod545.html` | Recognition B1 cho Valley 4 sao; không thay quyết định/chứng nhận A |
| `https://dehavi.com/valley` | Thành phần/câu chuyện sản phẩm, nguồn ảnh Valley |
| `https://hanvinhcoffee.vn/ve-chung-toi` | Identity Hân Vinh và địa chỉ |
| `https://dehavi.com/cup-dehavi-showroom` | Showroom, trải nghiệm và nguồn ảnh |
| `https://dehavi.com/chinh-sach-giao-nhan-va-van-chuyen` | Cơ sở liên kết mua trực tiếp tại showroom |

Ảnh external lưu URL CDN `bizweb.dktcdn.net` trong `database/seed_dehavi_media.sql`; không hardcode URL Dehavi vào view. Credit: `Dehavi Coffee / Công ty TNHH Cà phê Hân Vinh`. `license` để NULL: không suy diễn giấy phép mở hoặc quyền sử dụng thương mại. Gallery hiển thị nguồn ảnh và credit; nguồn chính thức trong story được tách khỏi paragraph, kiểm tra bằng `safeExternalUrl`, mở tab mới với `noopener noreferrer`.

Không tạo số chứng nhận, ngày cấp/hết hạn hoặc cơ quan cấp chưa có bằng chứng. Thiếu chi tiết chứng nhận hiển thị gọn; badge sao OCOP vẫn là cue chính. Xem thêm [dữ liệu Dehavi và lịch sử xác minh](DEHAVI_DEMO_DATA.md). Không chạy các SQL seed từ tài liệu này trên runtime.

## 13. Kiểm thử

Kết quả vòng cuối: frontend **7 suites / 63 tests PASS**; backend Product, Location/Map và attribution **34 PASS**; Dehavi seed/media trên PostGIS tạm **9 PASS**. Type-check, production build và `git diff --check` PASS. Backend có một cảnh báo deprecation `anyio.abc.BlockingPortal` của test dependency; không có test thất bại.

Frontend command tại repo root (Windows dùng `npm.cmd` để tránh PowerShell ExecutionPolicy):

```powershell
npm.cmd --prefix frontend run test -- src/views/__tests__/ProductsView.spec.ts src/views/__tests__/ProductDetailView.spec.ts src/views/__tests__/ProductExperienceView.spec.ts src/views/__tests__/LocationDetailView.spec.ts src/views/__tests__/LocationsView.spec.ts src/views/__tests__/MapView.spec.ts src/components/products/__tests__/ProductCard.spec.ts
npm.cmd --prefix frontend run type-check
npm.cmd --prefix frontend run build
git diff --check
```

Backend chạy `tests/test_products.py`, `tests/test_locations.py`, `tests/test_image_attribution.py` trong container tạm `--network none`, SQLite in-memory, app/tests mount read-only. OSRM được mock. Dehavi tests dùng mechanism `seeded_dehavi` hiện có: DSN phải là DB `dehavi_seed_test`, host `127.0.0.1`, cờ `DEHAVI_ISOLATED_POSTGIS=1`; container PostGIS tạm không host port, không mạng app, dữ liệu tmpfs. SQL seed/media chỉ chạy trong fixture test này. Không dùng `DATABASE_URL` runtime để kiểm thử seed.

Tests kiểm tra public filtering, relation hai chiều, GeoJSON đúng thứ tự, Nearby/sort/limit, routing errors, GPS sau click, route intent, lỗi quyền vị trí, ảnh/attribution và media idempotence. Tests mới xác nhận Finder giữ hai ô media/content khi Location enrichment chậm/lỗi và không ghi nhầm “Chưa cập nhật” khi request chưa thành công.

Giới hạn: component tests không xác nhận tile/image CDN trên mạng thật hoặc tuyến OSRM live; smoke check API runtime và OSRM live được ghi riêng ở mục 11. Screenshot review các vòng trước do người dùng cung cấp bối cảnh; vòng này không chụp lại. Không coi kết quả mock là chứng minh tuyến đường thực tế.

Kết quả search code cuối vòng:

| Nhóm kết quả | Phân loại và quyết định |
| --- | --- |
| TODO, FIXME, console.log, debugger, alert( | Không có trong frontend production Vue/TS; payload kiểm tra `javascript:alert(1)` trong tests là test bảo mật hợp lệ |
| Raw Dehavi URL | Có trong SQL dữ liệu và tests nguồn; không có URL hãng hardcode trong frontend production code |
| Localhost | `services/http.ts` có fallback phát triển `http://localhost:8000/api/v1`; compose và `.env.example` dùng mặc định local. Đây là cấu hình chung hiện có, không sửa trong Product flow. Deploy ngoài local phải đặt `VITE_API_BASE_URL` phù hợp |
| Localhost trong fixture | `src/test/location-fixtures.ts` là dữ liệu kiểm thử, không endpoint production |
| Tiếng Việt lỗi encoding | Không có pattern mojibake `Ã`, `á»` hoặc ký tự replacement trong production Vue/TS |
| “Chưa cập nhật” | Fallback hợp lệ cho chứng nhận/ngày, liên hệ, giờ mở cửa và địa chỉ thiếu; giữ nguyên ngoài demo. Finder phân biệt request chậm/lỗi với thiếu dữ liệu thật |
| Placeholder | Skeleton loading, input hints và fallback ảnh rõ ràng; không phải dữ liệu demo bịa. Dehavi runtime có ảnh, địa chỉ và giờ mở cửa nên không cần bổ sung dữ liệu |

Audit DoD không tìm thấy blocker nghiệp vụ trong flow đã kiểm tra. Gap presentation thực tế là metadata Finder bị đặt vào cột ảnh khi Location enrichment chưa thành công; đã sửa bằng wrapper giữ ô media và feedback. Khung giữ chỗ ảnh hiện có không có spinner từng ảnh; không redesign vì đã giữ layout và có fallback khi lỗi.

## 14. Phân chia phạm vi thành viên

**Thuận:** Product module; Product Experience Finder; Product↔Location integration; data/media integration; Nearby integration trong Product flow; demo end-to-end.

**Luyến:** Map/Location core; Leaflet; PostGIS foundation; OSRM routing foundation.

Finder của Thuận gọi và tích hợp các nền tảng Map/Location do Luyến phụ trách. Báo cáo phân biệt phần tích hợp luồng Product với phần xây dựng nền tảng; không nhận Leaflet, PostGIS hoặc OSRM routing foundation là phần của Thuận.

## 15. Kịch bản demo 2–3 phút

Chuẩn bị trang demo đang chạy, mạng tới API/CDN/tile/OSRM và trình duyệt cho phép geolocation. Dùng vị trí thật trong Việt Nam; Nearby chỉ hiện khoảng cách showroom nếu điểm nằm trong 200 km và 50 kết quả. Không thay tọa độ hoặc bịa kết quả để demo.

| Thời gian | Thao tác và lời nói |
| --- | --- |
| 0:00–0:25 | Từ danh sách Sản phẩm tìm “Dehavi Valley”, mở detail. “Đây là sản phẩm OCOP 4 sao của Công ty TNHH Cà phê Hân Vinh. Trang có ảnh thật, nguồn ảnh, câu chuyện và link nguồn chính thức.” |
| 0:25–0:55 | Bấm “Tìm nơi mua & trải nghiệm”. “Finder lấy các điểm đã liên kết với sản phẩm. Dehavi Showroom có ảnh, địa chỉ, dịch vụ và đơn vị quản lý; trang chưa tự xin vị trí.” |
| 0:55–1:20 | Bấm “Tìm điểm gần tôi”, cho phép vị trí. “Nearby dùng PostGIS tính khoảng cách địa lý và xếp điểm có khoảng cách gần trước. Điểm ngoài phạm vi vẫn được giữ, không tự thêm điểm không liên quan.” |
| 1:20–1:45 | Bấm “Xem chi tiết”. Chỉ ảnh, giờ mở cửa 06:30–17:30, dịch vụ, sản phẩm OCOP và mini-map. “Sản phẩm và điểm đến liên kết hai chiều.” |
| 1:45–2:00 | Quay lại Finder, bấm “Xem bản đồ”. “Bản đồ chọn đúng showroom, chưa tự gọi GPS hoặc tính tuyến.” |
| 2:00–2:35 | Quay lại Finder, bấm “Chỉ đường”; trên Map bấm “Lấy vị trí & chỉ đường”. “Sau xác nhận, Map dùng vị trí xuất phát và OSRM để tìm đường.” Chỉ polyline, distance và duration: “Đây là khoảng cách đường lái xe, khác khoảng cách Nearby.” |
| 2:35–2:50 | “Thuận phụ trách Product/Finder và tích hợp dữ liệu, Nearby trong Product flow. Luyến phụ trách Map/Location, Leaflet, PostGIS và nền tảng OSRM.” |

Nếu quyền bị từ chối: trình bày message, bật quyền rồi thử lại. Nếu OSRM live lỗi: chỉ message và Google Maps fallback, ghi nhận là nhánh lỗi; không nói đã tính tuyến thành công. Để demo đủ nhánh thành công, cần kiểm tra các dịch vụ và vị trí xuất phát trước buổi trình bày.
