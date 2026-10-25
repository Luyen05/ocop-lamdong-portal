# Quy tắc nghiệp vụ

Tài liệu mô tả hệ thống làm gì và theo quy tắc nào. Chi tiết endpoint xem `docs/API.md`, cấu trúc dữ liệu xem `docs/KIEN_TRUC.md`.

- [1. Phạm vi](#1-phạm-vi)
- [2. Vai trò](#2-vai-trò)
- [3. Tài khoản](#3-tài-khoản)
- [4. Hồ sơ chủ thể](#4-hồ-sơ-chủ-thể)
- [5. Sản phẩm OCOP](#5-sản-phẩm-ocop)
- [6. Điểm du lịch và bản đồ](#6-điểm-du-lịch-và-bản-đồ)
- [7. Đánh giá](#7-đánh-giá)
- [8. Danh mục](#8-danh-mục)
- [9. Tin tức](#9-tin-tức)
- [10. Giới hạn đã biết](#10-giới-hạn-đã-biết)

## 1. Phạm vi

Cổng là nơi **công bố** thông tin sản phẩm OCOP và điểm du lịch nông nghiệp đã được kiểm duyệt. Cổng **không** chấm điểm hay cấp hạng sao OCOP:

| Bên | Trách nhiệm |
|---|---|
| Chủ thể (HTX, doanh nghiệp, hộ sản xuất) | Khai báo thông tin, ảnh, hạng sao và bản chụp giấy chứng nhận do cơ quan có thẩm quyền cấp |
| Cơ quan có thẩm quyền (ngoài hệ thống) | Quyết định hạng sao, số quyết định, ngày cấp, thời hạn |
| Quản trị viên cổng | Đối chiếu hồ sơ với giấy chứng nhận, **duyệt hiển thị**, yêu cầu bổ sung hoặc từ chối; không sửa thay nội dung của chủ thể |
| Hệ thống | Quản lý chủ thể sở hữu, slug, trạng thái, phiên bản, người và thời điểm xử lý |

Giao diện dùng cụm từ "Duyệt hiển thị", không dùng "Cấp sao". Client không bao giờ gửi `subject_id`, trạng thái kiểm duyệt, người duyệt, điểm đánh giá hay lượt xem; backend lấy chủ sở hữu từ JWT.

## 2. Vai trò

| Vai trò | Làm được |
|---|---|
| Khách | Xem sản phẩm, điểm du lịch, bản đồ, tin tức, đánh giá đã duyệt; đăng ký, đăng nhập |
| Người dùng (`user`) | Như khách, cộng: sửa hồ sơ, đổi mật khẩu, liên kết Google/Facebook, viết đánh giá, đăng ký trở thành chủ thể |
| Chủ thể (`subject`, hồ sơ đã duyệt) | Như người dùng, cộng: sửa thông tin liên hệ đơn vị, quản lý sản phẩm và điểm du lịch của mình |
| Quản trị viên (`admin`) | Tổng quan, thống kê; duyệt hồ sơ chủ thể, sản phẩm, yêu cầu thay đổi, điểm du lịch, đánh giá; quản lý người dùng, danh mục, nguồn dữ liệu |

Tài khoản quản trị không tạo được qua giao diện; xem README mục "Tạo tài khoản quản trị".

## 3. Tài khoản

**Đăng ký, đăng nhập**

- Đăng ký bằng email (không phân biệt hoa thường), mật khẩu 8–128 ký tự, họ tên, số điện thoại tùy chọn (chữ số, có thể có `+`, khoảng trắng, dấu chấm, gạch ngang, ngoặc).
- Sai mật khẩu quá **5 lần trong 15 phút cho một email** hoặc **20 lần trong 15 phút từ một IP** thì bị chặn tạm thời (HTTP 429, header `Retry-After`). Đăng nhập đúng xóa bộ đếm của email đó. Bộ đếm dùng chung với kiểm tra mật khẩu hiện tại khi đổi mật khẩu.
- Email không tồn tại và mật khẩu sai trả cùng một thông báo, cùng thời gian xử lý (không lộ email nào đã đăng ký).
- Access token (JWT) hết hạn sau 60 phút (cấu hình được). Mỗi request kiểm tra lại tài khoản còn hoạt động.

**Mật khẩu**

- Đổi mật khẩu: phải nhập đúng mật khẩu hiện tại; mật khẩu mới khác mật khẩu cũ.
- Tài khoản tạo bằng Google/Facebook chưa có mật khẩu: "Đặt mật khẩu" không cần mật khẩu hiện tại. Trước khi đặt, đăng nhập bằng email + mật khẩu với tài khoản này luôn báo sai.

**Đăng nhập Google, Facebook** (tùy chọn, bật khi có khóa trong `.env`; cách tạo khóa xem `docs/CAU_HINH.md`)

| Trường hợp | Kết quả |
|---|---|
| Tài khoản Google/Facebook đã liên kết | Đăng nhập vào tài khoản đã liên kết (nhận diện theo mã người dùng của nhà cung cấp, đổi email không ảnh hưởng) |
| Email chưa có trong hệ thống | Tạo tài khoản vai trò người dùng, không có mật khẩu |
| Email đã có tài khoản | Từ chối (`SOCIAL_EMAIL_EXISTS`): đăng nhập bằng mật khẩu rồi liên kết trong trang Tài khoản |
| Đang đăng nhập, bấm "Liên kết" | Liên kết vào tài khoản hiện tại (email hai bên không cần trùng) |
| Tài khoản Google/Facebook đã liên kết với người khác | Từ chối (`SOCIAL_ACCOUNT_IN_USE`) |
| Quản trị viên | Không đăng nhập, không liên kết bằng mạng xã hội |
| Email Google chưa xác minh, Facebook không trả email | Từ chối |
| Bỏ liên kết cách đăng nhập duy nhất (tài khoản chưa có mật khẩu) | Từ chối (`SOCIAL_UNLINK_LAST_METHOD`) |

Không tự liên kết theo email vì đăng ký bằng mật khẩu không xác minh email: nếu tự liên kết, người đăng ký trước bằng email của người khác sẽ chiếm được tài khoản khi chủ thật đăng nhập bằng Google. Facebook cũng không cam kết email trả về đã được xác nhận.

**Khóa tài khoản** (quản trị viên)

- Không tự khóa chính mình, không khóa quản trị viên còn hoạt động cuối cùng.
- Tài khoản bị khóa: không đăng nhập được; phiên đang mở kết thúc ở thao tác tiếp theo (về trang đăng nhập với thông báo).
- Khóa tài khoản chủ thể: sản phẩm, điểm du lịch của chủ thể đó ngừng hiển thị công khai; mở khóa thì hiện lại.
- Ngoại lệ: tài khoản kỹ thuật đuôi `@local.invalid` của dữ liệu nhập từ nguồn công khai luôn ở trạng thái khóa (không ai đăng nhập được) nhưng nội dung vẫn hiển thị. Đuôi `.invalid` là tên miền dành riêng (RFC 2606) nên không đăng ký được.

## 4. Hồ sơ chủ thể

```text
(người dùng gửi hồ sơ) -> pending -> approved   (vai trò đổi thành subject)
                                   -> rejected   (bắt buộc có lý do) -> sửa và gửi lại -> pending
```

- Hồ sơ gồm tên đơn vị, loại hình (hợp tác xã, doanh nghiệp, hộ sản xuất, cá nhân), mã số thuế (tùy chọn, không trùng), người đại diện, số điện thoại, email, địa chỉ, xã/phường.
- Khi được duyệt, trang đăng ký chủ thể và thanh đầu trang tự chuyển sang quyền chủ thể (kiểm tra lại khi quay lại tab và mỗi phút), không cần tải lại trang.
- Chủ thể đã duyệt tự sửa **thông tin liên hệ** (người đại diện, số điện thoại, email, địa chỉ, xã/phường). Tên, loại hình, mã số thuế gắn với pháp lý: liên hệ quản trị viên để sửa.

## 5. Sản phẩm OCOP

**Sản phẩm mới**

```text
draft -> pending -> approved
             |----> needs_revision -> (sửa) -> pending
             |----> rejected -------> (sửa) -> pending
```

1. Bản nháp chỉ cần tên và danh mục; chủ thể lưu dần từng phần.
2. Gửi duyệt yêu cầu: mô tả, hạng sao 3–5 theo giấy chứng nhận, số chứng nhận/quyết định, ngày cấp, ngày hết hạn (sau ngày cấp, chưa quá hạn), cơ quan công nhận, bản chụp giấy chứng nhận và **đúng một ảnh chính**. Thiếu gì thì `PRODUCT_SUBMISSION_INCOMPLETE` liệt kê.
3. Đang `pending` thì không sửa trực tiếp.
4. Quản trị viên duyệt hiển thị hoặc yêu cầu bổ sung (bắt buộc ghi chú). Từ chối dành cho hồ sơ giả mạo hoặc ngoài phạm vi OCOP. Quản trị viên không sửa hay nâng hạng sao.
5. Giá không bắt buộc; không có giá thì giao diện ghi "Liên hệ".

**Điều kiện hiển thị công khai** (danh sách, chi tiết, tìm kiếm, bản đồ, thống kê "đang công khai" đều dùng chung):

- sản phẩm `approved`, không phải dữ liệu demo (`is_demo`), có hạng sao và mô tả;
- có nguồn công nhận mức A/B1 **hoặc** giấy chứng nhận còn hạn đủ thông tin;
- chủ thể `approved` và tài khoản của chủ thể còn hoạt động (ngoại lệ tài khoản kỹ thuật, mục 3).

**Sửa và ngừng hiển thị sản phẩm đã duyệt**

- Không sửa trực tiếp bản đang công khai: chủ thể gửi **yêu cầu cập nhật** chứa toàn bộ dữ liệu đề xuất; bản cũ vẫn hiển thị tới khi được duyệt. Duyệt thì áp dụng trong một transaction.
- Mỗi sản phẩm chỉ có một yêu cầu đang mở. `base_version` chặn áp dụng yêu cầu tạo trên phiên bản cũ (`PRODUCT_VERSION_CONFLICT`).
- Trạng thái yêu cầu: `pending`, `needs_revision`, `approved`, `rejected`, `cancelled` (chủ thể hủy).
- Sản phẩm từng được duyệt không xóa cứng: chủ thể gửi **yêu cầu ngừng hiển thị** kèm lý do; duyệt thì chuyển `archived`, giữ ảnh, đánh giá, lịch sử. Chủ thể xóa được sản phẩm chưa từng duyệt (nháp, cần bổ sung, bị từ chối).

**Ảnh và giấy chứng nhận**

- Ảnh JPG, PNG, WebP tối đa 5 MB (kiểm tra nội dung file, không chỉ đuôi). Mỗi sản phẩm tối đa một ảnh chính.
- Giấy chứng nhận PDF, JPG, PNG tối đa 10 MB, **riêng tư**: chỉ chủ thể sở hữu và quản trị viên tải được qua API có kiểm tra quyền.
- Không xóa được ảnh, chứng nhận đang gắn với sản phẩm hoặc nằm trong yêu cầu thay đổi đang chờ.
- Ảnh có thể ghi nguồn, tác giả, giấy phép (`source_url`, `credit`, `license`); ảnh minh họa hiện nhãn "Ảnh minh họa".

**Nguồn chứng cứ** (quản trị viên): sản phẩm nhập từ nguồn công khai được gắn với văn bản, trang thông tin theo mức xác minh A (quyết định công nhận), B1 (cổng thông tin chính thức), B2, C (tham khảo). Với sản phẩm do chủ thể gửi, giấy chứng nhận là tài liệu đối chiếu chính.

## 6. Điểm du lịch và bản đồ

**Khai báo điểm** (chủ thể)

```text
draft -> pending -> approved -> (yêu cầu ngừng hiển thị được duyệt) -> archived
             |----> needs_revision -> pending
             |----> rejected
```

- Lấy vị trí bằng ghim bản đồ, GPS thiết bị, nhập tọa độ hoặc dán link Google Maps đầy đủ (link rút gọn không đọc được tọa độ).
- Vị trí phải nằm trong khung tọa độ tỉnh Lâm Đồng. Cách điểm đã duyệt khác dưới 200 m thì chỉ cảnh báo trùng, không chặn.
- Gửi duyệt cần mô tả từ 40 ký tự, ít nhất một ảnh, đủ vị trí, địa chỉ, xã/phường. Bản nháp và bản cần bổ sung được thiếu các thông tin này.
- Chủ thể gắn sản phẩm của mình vào điểm; chi tiết điểm hiện sản phẩm, chi tiết sản phẩm hiện điểm.
- Quản trị viên có thể chỉnh ghim khi duyệt (ghi vào ghi chú duyệt). Điểm đã duyệt sửa hoặc ngừng hiển thị qua yêu cầu cập nhật, giống sản phẩm.
- Điểm do quản trị viên nhập sẵn (không gắn chủ thể) luôn hiển thị khi đã duyệt.

**Bản đồ số**

- Gom cụm điểm, lọc theo loại hình và xã/phường, định vị người dùng (trình duyệt hỏi quyền).
- Tìm điểm gần nhất bằng PostGIS; chỉ đường bằng OSRM. OSRM không phản hồi thì báo lỗi và đưa liên kết chỉ đường Google Maps dự phòng.
- **Tìm điểm trải nghiệm theo sản phẩm** (`/san-pham/:slug/diem-trai-nghiem`): liệt kê các điểm đã duyệt có bán/giới thiệu sản phẩm, sắp theo khoảng cách khi người dùng cho phép định vị, mở chỉ đường trên bản đồ. Không có quyền vị trí thì vẫn xem danh sách, không sắp theo khoảng cách.

## 7. Đánh giá

- Người dùng và chủ thể đã đăng nhập viết đánh giá cho sản phẩm hoặc điểm du lịch đang công khai; quản trị viên không viết (họ là người duyệt).
- Mỗi người **một** đánh giá cho mỗi sản phẩm/điểm. Chủ thể không tự đánh giá sản phẩm, điểm của đơn vị mình.
- Nội dung: 1–5 sao, nhận xét 10–1000 ký tự.
- Đánh giá mới ở trạng thái chờ duyệt, chỉ hiện công khai khi quản trị viên duyệt. Từ chối phải có lý do; người viết thấy lý do trong trang "Đánh giá của tôi".
- Người viết sửa (quay về chờ duyệt) hoặc xóa đánh giá của mình.
- Điểm trung bình (`rating_avg`) của sản phẩm/điểm tính lại từ các đánh giá đã duyệt sau mỗi lần duyệt, từ chối, sửa, xóa; công khai chỉ hiện tên người viết, không hiện email.

## 8. Danh mục

- Danh mục có thứ tự hiển thị và trạng thái ẩn/hiện.
- Ẩn danh mục: sản phẩm thuộc danh mục **vẫn hiển thị**; danh mục chỉ biến mất khỏi bộ lọc công khai và ô chọn khi chủ thể **tạo** sản phẩm mới. Sản phẩm đang thuộc danh mục ẩn vẫn sửa được và giữ danh mục; backend chặn tạo mới hoặc chuyển sản phẩm vào danh mục ẩn (`CATEGORY_HIDDEN`).
- Tên và slug không trùng; không xóa danh mục còn sản phẩm (`CATEGORY_IN_USE`).
- Màu và biểu tượng của từng nhóm sản phẩm thống nhất ở mọi trang (`frontend/src/utils/category.ts`).

## 9. Tin tức

- Lấy từ RSS của cổng OCOP tỉnh Lâm Đồng, lưu đệm 15 phút. Nguồn lỗi thì dùng bản đã lưu (gia hạn thêm); chưa có bản lưu thì báo lỗi kèm nút "Thử lại".
- Chưa có chức năng quản trị viên tự đăng tin (bảng `news` đã có trong database).

## 10. Giới hạn đã biết

- Ảnh chưa duyệt vẫn mở được nếu biết đường dẫn (đường dẫn chứa mã ngẫu nhiên 32 ký tự, khó đoán). Quyết định giữ cách này ngày 03/10/2026.
- Chưa có quên mật khẩu qua email (chưa có dịch vụ gửi mail).
- Token đã cấp vẫn dùng được tới khi hết hạn sau khi đổi mật khẩu.
- Bộ đếm đăng nhập sai nằm trong bộ nhớ của tiến trình backend: mất khi khởi động lại; khi chạy sau proxy cần lấy IP thật của người dùng.
- Tìm kiếm phân biệt dấu: "dâu tây" tìm thấy, "dau tay" thì không.
- Chứng nhận hết hạn làm sản phẩm tự ẩn khỏi trang công khai (theo điều kiện hiển thị) nhưng chưa có thông báo nhắc chủ thể gia hạn.
