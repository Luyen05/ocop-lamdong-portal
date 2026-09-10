# Danh mục nguồn dữ liệu OCOP Lâm Đồng 2025–2026

Thư mục này lưu các văn bản hành chính quan trọng dùng để kiểm chứng bộ dữ liệu mẫu của đồ án. Các bài báo và trang thông tin điện tử chỉ được lưu liên kết trong `data/ocop/source_manifest.csv` để tránh làm repository quá lớn.

## Phạm vi

- Địa bàn: tỉnh Lâm Đồng sau sắp xếp, bao gồm khu vực Lâm Đồng, Bình Thuận và Đắk Nông trước đây.
- Thời điểm nguồn: từ ngày 01/01/2025 đến ngày chốt dữ liệu 10/09/2026.
- Mục đích: dữ liệu mẫu có truy xuất nguồn phục vụ phát triển, kiểm thử và báo cáo đồ án; không thay thế cơ sở dữ liệu hành chính chính thức.
- Địa chỉ: giữ nguyên địa chỉ trong nguồn và chỉ thêm địa chỉ hiện hành khi có ánh xạ theo Nghị quyết 1671/NQ-UBTVQH15.

## Mức độ kiểm chứng

| Mức | Ý nghĩa | Cách sử dụng |
| --- | --- | --- |
| A | Quyết định chính thức có chữ ký hoặc phụ lục sản phẩm | Có thể tạo dữ liệu công khai nếu đủ trường bắt buộc |
| B1 | Báo hoặc cổng cơ quan nhà nước xác nhận đã công nhận/trao giấy chứng nhận | Có thể công khai nhưng phải ghi rõ giới hạn của nguồn |
| B2 | Đề xuất, chấm điểm hoặc đánh giá trước khi có kết quả công nhận | Chỉ tạo dữ liệu chờ xác minh, không công khai |
| C | Website chủ thể hoặc nguồn thương mại | Chỉ bổ sung mô tả, quy cách, giá hoặc ảnh; không xác nhận hạng sao |

## Văn bản được lưu cục bộ

### Năm 2025

- Nghị quyết 202/2025/QH15 về sắp xếp đơn vị hành chính cấp tỉnh.
- Nghị quyết 1671/NQ-UBTVQH15 về sắp xếp đơn vị hành chính cấp xã của tỉnh Lâm Đồng.
- Quyết định 1489/QĐ-TTg sửa đổi Bộ tiêu chí và quy trình OCOP.
- Quyết định 643/QĐ-UBND kiện toàn Hội đồng đánh giá, phân hạng sản phẩm OCOP tỉnh Lâm Đồng.
- Quyết định 1253/QĐ-UBND ban hành Quy chế hoạt động của Hội đồng OCOP tỉnh Lâm Đồng.
- Quyết định 858/QĐ-UBND tỉnh Đắk Nông công nhận 5 sản phẩm OCOP 4 sao.
- Quyết định 1887/QĐ-UBND huyện Đắk Song công nhận 8 sản phẩm OCOP 3 sao.
- Quyết định 768/QĐ-UBND huyện Cư Jút công nhận 2 sản phẩm OCOP 3 sao.

### Năm 2026

- Quyết định 26/2026/QĐ-TTg ban hành Bộ tiêu chí và quy trình OCOP mới.
- Quyết định 3981/QĐ-UBND tỉnh Lâm Đồng công nhận 9 sản phẩm OCOP 3 sao đợt 1 năm 2026.

## Nguồn trực tuyến chính

- [Nghị quyết 202/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=213930&pageid=27160)
- [Nghị quyết 1671/NQ-UBTVQH15](https://xaydungchinhsach.chinhphu.vn/toan-van-nghi-quyet-so-1671-nq-ubtvqh15-sap-xep-cac-dvhc-cap-xa-cua-tinh-lam-dong-nam-2025-119250616201715664.htm)
- [Quyết định 1489/QĐ-TTg](https://vanban.chinhphu.vn/?classid=2&docid=214441&pageid=27160)
- [Quyết định 26/2026/QĐ-TTg](https://vanban.chinhphu.vn/?classid=1&docid=218267&orggroupid=3&pageid=27160)
- [Cổng thông tin OCOP Lâm Đồng](https://ocoplamdong.gov.vn/)
- [Đức Trọng trao chứng nhận 22 sản phẩm OCOP](https://baolamdong.vn/duc-trong-trao-giay-chung-nhan-22-san-pham-ocop-277131.html)
- [Bình Thuận trao chứng nhận 21 sản phẩm OCOP 4 sao](https://baolamdong.vn/trao-giay-chung-nhan-san-pham-ocop-4-sao-cho-21-san-pham-280929.html)
- [Tánh Linh công nhận thêm 3 sản phẩm OCOP 3 sao](https://baolamdong.vn/bbt/tanh-linh-cong-nhan-them-3-san-pham-ocop-3-sao-130891.html)

## Cập nhật nguồn

Chạy `tools/download_ocop_sources.ps1` để tải lại các PDF hành chính. Sau khi tải, phải cập nhật SHA-256 trong `data/ocop/source_manifest.csv` và kiểm tra rằng tệp mở được trước khi dùng làm bằng chứng.
