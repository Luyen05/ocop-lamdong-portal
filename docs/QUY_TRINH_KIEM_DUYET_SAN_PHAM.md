# Quy trình quản lý và kiểm duyệt sản phẩm OCOP

## 1. Phạm vi của hệ thống

Hệ thống là cổng quản lý và công bố thông tin sản phẩm OCOP. Quản trị viên của
hệ thống không chấm điểm hoặc cấp hạng sao OCOP. Chủ thể khai báo hạng sao theo
giấy chứng nhận do cơ quan có thẩm quyền cấp; quản trị viên chỉ đối chiếu hồ sơ
và quyết định có cho phép thông tin đó xuất hiện trên cổng hay không.

Trên giao diện sử dụng cụm từ **Duyệt hiển thị**, không sử dụng **Cấp sao**.

## 2. Quyền của các vai trò

- `subject`: chỉ quản lý sản phẩm thuộc hồ sơ chủ thể gắn với JWT của mình.
- `admin`: xem hồ sơ, đối chiếu chứng nhận và xử lý yêu cầu kiểm duyệt.
- `user` và khách: chỉ đọc sản phẩm đã duyệt của chủ thể đã duyệt.

Client không được gửi `subject_id`, trạng thái kiểm duyệt, người duyệt, điểm
đánh giá hoặc lượt xem.

## 3. Sản phẩm mới

```text
draft -> pending -> approved
             |----> needs_revision -> pending
             |----> rejected ------> pending (sau khi chỉnh sửa)
```

1. Chủ thể tạo và chỉnh sửa bản nháp.
2. Chủ thể cung cấp thông tin sản phẩm, hạng sao theo giấy chứng nhận, số chứng
   nhận/quyết định, ngày cấp, ngày hết hạn, cơ quan cấp, đường dẫn minh chứng và
   ít nhất một ảnh sản phẩm.
3. Khi gửi duyệt, sản phẩm chuyển sang `pending` và không còn được sửa trực tiếp.
4. Quản trị viên có thể duyệt, yêu cầu bổ sung hoặc từ chối. Yêu cầu bổ sung và
   từ chối bắt buộc có ghi chú.
5. Chỉ sản phẩm `approved` thuộc chủ thể `approved` mới xuất hiện công khai.

## 4. Cập nhật sản phẩm đã duyệt

Không sửa trực tiếp bản sản phẩm đang công khai. Chủ thể gửi một yêu cầu cập
nhật chứa toàn bộ dữ liệu đề xuất. Trong thời gian chờ duyệt, phiên bản hiện tại
vẫn xuất hiện công khai.

```text
approved v1 + update request pending
                  |----> approved: áp dụng v2 trong một transaction
                  |----> needs_revision: chủ thể sửa và gửi lại
                  |----> rejected: giữ nguyên v1
```

Mỗi sản phẩm chỉ có một yêu cầu thay đổi đang hoạt động. `base_version` ngăn việc
áp dụng yêu cầu đã được tạo trên một phiên bản sản phẩm cũ.

## 5. Ngừng hiển thị sản phẩm

- Chủ thể được xóa cứng bản nháp của chính mình.
- Sản phẩm từng được duyệt không được xóa cứng. Chủ thể phải gửi yêu cầu ngừng
  hiển thị và nêu rõ lý do.
- Khi quản trị viên duyệt yêu cầu, sản phẩm chuyển sang `archived`; ảnh, đánh
  giá, liên kết và lịch sử kiểm duyệt vẫn được giữ lại.
- Quản trị viên có thể chuyển sản phẩm sang `suspended` ngay khi có dấu hiệu vi
  phạm, nhưng phải ghi lý do. Khôi phục sản phẩm cũng phải được ghi nhận.

## 6. Trạng thái yêu cầu thay đổi

Yêu cầu cập nhật hoặc ngừng hiển thị sử dụng các trạng thái:

- `pending`: chờ quản trị viên xử lý.
- `needs_revision`: cần chủ thể sửa hoặc bổ sung.
- `approved`: đã được áp dụng.
- `rejected`: bị từ chối, dữ liệu công khai không thay đổi.
- `cancelled`: chủ thể hủy trước khi quản trị viên xử lý.

## 7. Quy tắc chứng nhận

- Hạng sao phải từ 3 đến 5 và là hạng ghi trên giấy chứng nhận.
- Số chứng nhận, ngày cấp, ngày hết hạn và cơ quan cấp là bắt buộc khi gửi duyệt.
- Ngày hết hạn phải sau ngày cấp.
- Quản trị viên không sửa hoặc nâng hạng sao khi duyệt. Nếu thông tin không khớp,
  quản trị viên yêu cầu chủ thể chỉnh sửa hoặc từ chối hồ sơ.
- Sản phẩm chưa có chứng nhận có thể được lưu ở trạng thái `draft`, nhưng không
  được gửi duyệt hoặc xuất hiện công khai.

## 8. Nhật ký và tính toàn vẹn dữ liệu

- Lưu người xử lý, thời gian xử lý và ghi chú ở mọi quyết định kiểm duyệt.
- Việc áp dụng yêu cầu cập nhật hoặc lưu trữ phải chạy trong một transaction.
- Backend luôn kiểm tra quyền sở hữu từ JWT, không tin `subject_id` từ frontend.
- API công khai tiếp tục lọc cả `Product.status = approved` và
  `Subject.status = approved`.
