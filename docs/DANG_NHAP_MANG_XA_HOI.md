# Đăng nhập bằng Google và Facebook

Người dùng có thể đăng nhập hoặc đăng ký nhanh bằng tài khoản Google, Facebook ở trang `/dang-nhap` và `/dang-ky`.
Chức năng là tùy chọn: chưa khai báo khóa của nhà cung cấp nào thì nút của nhà cung cấp đó không hiện, mọi chức năng khác chạy bình thường.

## 1. Cách hoạt động

Luồng OAuth 2.0 "authorization code", backend gọi Google/Facebook bằng `httpx` (không thêm thư viện, không nạp script của Google/Facebook vào trang).

1. Người dùng bấm "Tiếp tục với Google". Trình duyệt tạo `state` ngẫu nhiên (và mã PKCE với Google), lưu trong `sessionStorage` 10 phút, rồi gọi `POST /auth/social/google/authorize` để lấy địa chỉ trang đăng nhập Google.
2. Người dùng chọn tài khoản trên trang của Google/Facebook.
3. Google/Facebook trả người dùng về `FRONTEND_BASE_URL/dang-nhap/mang-xa-hoi/google` (hoặc `/facebook`) kèm `code` và `state`.
4. Trang này so `state` với giá trị đã lưu (chặn yêu cầu giả mạo), xóa `code` khỏi thanh địa chỉ, rồi gửi `code` cho `POST /auth/social/google/callback` (hoặc `/link` khi đang liên kết từ trang Tài khoản).
5. Backend dùng khóa bí mật đổi `code` lấy thông tin người dùng (mã người dùng, email, tên), rồi cấp JWT của hệ thống như đăng nhập bằng mật khẩu (hoặc lưu liên kết).

Khóa bí mật (Client Secret, App Secret) chỉ nằm ở backend, không bao giờ gửi xuống trình duyệt.

## 2. Quy tắc tài khoản

| Trường hợp | Kết quả |
|---|---|
| Tài khoản Google/Facebook đã liên kết trước đó | Đăng nhập vào tài khoản đã liên kết (nhận diện theo mã người dùng của Google/Facebook, đổi email cũng không sao) |
| Email chưa có trong hệ thống | Tạo tài khoản vai trò **người dùng**, không có mật khẩu |
| Email đã có tài khoản (bất kỳ vai trò nào) | Từ chối (409 `SOCIAL_EMAIL_EXISTS`): đăng nhập bằng email và mật khẩu, rồi liên kết trong trang **Tài khoản** |
| Người dùng đang đăng nhập bấm "Liên kết" ở trang Tài khoản | Liên kết Google/Facebook vào tài khoản đó (email hai bên không cần trùng) |
| Tài khoản Google/Facebook đã liên kết với người khác | Từ chối liên kết (409 `SOCIAL_ACCOUNT_IN_USE`) |
| Quản trị viên | Không đăng nhập, không liên kết bằng Google/Facebook (403); chỉ dùng mật khẩu |
| Người dùng tạo bằng Google rồi được duyệt thành chủ thể | Vẫn đăng nhập bằng Google được |
| Email Google chưa xác minh, tài khoản Facebook không có email | Từ chối (422) |
| Tài khoản bị khóa | Từ chối (403) |

**Vì sao không tự liên kết theo email:** đăng ký bằng mật khẩu không xác minh email, nên ai cũng có thể đăng ký trước bằng email của người khác. Nếu tự liên kết, khi chủ thật đăng nhập bằng Google, kẻ đăng ký trước vẫn vào được tài khoản bằng mật khẩu của hắn. Facebook cũng không cam kết email trả về đã được xác nhận. Vì vậy chỉ liên kết khi người dùng đã đăng nhập (chứng minh sở hữu cả hai tài khoản).

- Tài khoản tạo bằng Google/Facebook không có mật khẩu (`users.hashed_password` trống). Đăng nhập bằng email + mật khẩu với tài khoản này luôn báo "Email hoặc mật khẩu không chính xác." Khi có chức năng đặt/quên mật khẩu, người dùng có thể đặt thêm mật khẩu.
- Trang **Tài khoản**: mục "Đăng nhập bằng" (Email và mật khẩu, Google, Facebook) và khung "Liên kết đăng nhập" để liên kết hoặc bỏ liên kết. Không bỏ được liên kết cuối cùng của tài khoản chưa có mật khẩu (tránh mất quyền vào tài khoản).
- Liên kết dùng chung địa chỉ trả về `/dang-nhap/mang-xa-hoi/<google|facebook>`, không cần khai báo thêm với Google/Facebook.
- Ảnh đại diện lấy từ Google khi tạo tài khoản; ảnh Facebook không lưu vì đường dẫn ảnh của Facebook có hạn dùng.
- Dữ liệu liên kết lưu ở bảng `user_social_accounts` (migration `013_social_login.sql`).

## 3. Tạo khóa Google

Giao diện của Google có thể đổi tên menu theo thời gian; các mục chính như sau.

1. Vào <https://console.cloud.google.com/>, đăng nhập bằng Gmail của nhóm, tạo project mới (ví dụ `ocop-lam-dong`).
2. Mở **Google Auth Platform** (trước đây là "OAuth consent screen"):
   - **Branding**: tên ứng dụng "Cổng OCOP Lâm Đồng", email hỗ trợ, email liên hệ.
   - **Audience**: chọn **External**. Khi ứng dụng ở chế độ **Testing**, chỉ tài khoản có trong danh sách **Test users** mới đăng nhập được: thêm Gmail của các thành viên và tài khoản dùng khi demo.
   - **Data access**: chỉ cần các quyền cơ bản `openid`, `email`, `profile` (không cần xin Google xét duyệt).
3. Mở **Clients** → **Create client** → loại **Web application**:
   - **Authorized redirect URIs**: thêm `http://localhost:5173/dang-nhap/mang-xa-hoi/google`.
     Khi triển khai thật, thêm `https://<tên-miền>/dang-nhap/mang-xa-hoi/google`.
   - Không cần điền "Authorized JavaScript origins".
4. Bấm **Create**, chép **Client ID** và **Client secret** vào `.env` (mục 5).

## 4. Tạo khóa Facebook

1. Vào <https://developers.facebook.com/>, đăng nhập Facebook, đăng ký tài khoản nhà phát triển nếu được hỏi.
2. **My Apps → Create App**. Ở bước chọn trường hợp sử dụng (use case), chọn **Xác thực và yêu cầu dữ liệu từ người dùng bằng Đăng nhập Facebook** (Authenticate and request data from users with Facebook Login). Đặt tên ứng dụng, chọn không liên kết doanh nghiệp.
3. Trong use case vừa thêm, mở phần **Permissions** và bật thêm quyền **email** (`public_profile` có sẵn).
4. Mở **Facebook Login → Settings**:
   - **Valid OAuth Redirect URIs**: thêm `http://localhost:5173/dang-nhap/mang-xa-hoi/facebook` (khi triển khai thêm bản `https://<tên-miền>/…`).
   - Giữ bật **Use Strict Mode for redirect URIs** và **Enforce HTTPS** (Facebook cho phép `localhost` khi ứng dụng ở chế độ phát triển).
5. **App settings → Basic**: chép **App ID** và **App Secret** (bấm "Show", có thể phải nhập lại mật khẩu Facebook).
6. Khi ứng dụng ở chế độ **Development**, chỉ tài khoản có vai trò trong ứng dụng (**App roles → Roles**: Administrators, Developers, Testers) mới đăng nhập được. Thêm Facebook của các thành viên và tài khoản demo. Muốn mọi người dùng được thì phải chuyển sang **Live**, cần trang chính sách quyền riêng tư công khai; chưa cần cho đồ án.

## 5. Cấu hình

Thêm vào `.env` ở thư mục gốc repo (không commit file này):

```
FRONTEND_BASE_URL=http://localhost:5173
GOOGLE_CLIENT_ID=<Client ID>
GOOGLE_CLIENT_SECRET=<Client secret>
FACEBOOK_APP_ID=<App ID>
FACEBOOK_APP_SECRET=<App Secret>
FACEBOOK_GRAPH_VERSION=v26.0
```

- Chỉ dùng Google thì để trống hai biến `FACEBOOK_*` (và ngược lại).
- `FRONTEND_BASE_URL` phải trùng đúng địa chỉ mở trang web: nếu mở bằng `http://127.0.0.1:5173` thì địa chỉ trả về đã khai báo với Google/Facebook cũng phải là `127.0.0.1`.
- Nạp lại backend: `docker compose up -d backend`. Kiểm tra: mở <http://localhost:8000/api/v1/auth/social/providers>, kết quả phải có `"google"` và/hoặc `"facebook"`.
- Database đã có dữ liệu thì chạy migration `013_social_login.sql` (README mục 5).
- Lỡ để lộ khóa bí mật: tạo khóa mới (Google: thêm secret mới rồi xóa secret cũ trong Client; Facebook: **Reset** App Secret) và cập nhật `.env`.

## 6. Lỗi thường gặp

| Hiện tượng | Nguyên nhân và cách xử lý |
|---|---|
| Không thấy nút Google/Facebook | Thiếu ID hoặc Secret trong `.env`, hoặc chưa chạy `docker compose up -d backend` sau khi sửa `.env` |
| Google báo `redirect_uri_mismatch` | Địa chỉ trong **Authorized redirect URIs** khác `FRONTEND_BASE_URL/dang-nhap/mang-xa-hoi/google` (sai cổng, `localhost` với `127.0.0.1`, thừa dấu `/`) |
| Google báo "Access blocked … has not completed the Google verification process" | Tài khoản chưa có trong **Test users** |
| Facebook báo "URL blocked" / "Can't load URL" | Chưa thêm địa chỉ vào **Valid OAuth Redirect URIs** |
| Facebook báo ứng dụng chưa hoạt động | Tài khoản chưa có vai trò trong ứng dụng (chế độ Development) |
| "Tài khoản Facebook không cung cấp email" | Người dùng bỏ chọn chia sẻ email, hoặc tài khoản Facebook đăng ký bằng số điện thoại |
| "Email … đã có tài khoản" | Đúng quy tắc: đăng nhập bằng mật khẩu rồi bấm "Liên kết" ở trang Tài khoản |
| "Phiên đăng nhập không hợp lệ hoặc đã hết hạn" | Để trang Google/Facebook quá 10 phút, mở đường dẫn trả về ở tab khác, hoặc tải lại trang sau khi đăng nhập: bấm "Thử lại" |
| "Không kết nối được với Google/Facebook" | Máy chạy backend không ra được Internet |

## 7. Kiểm thử

- Backend: `backend/tests/test_social_login.py` (26 test) giả lập máy chủ Google/Facebook bằng `httpx.MockTransport`: tạo tài khoản, không tự liên kết theo email, liên kết và bỏ liên kết khi đã đăng nhập, quản trị viên, email chưa xác minh hoặc quá dài, thiếu email, lỗi nhà cung cấp, `appsecret_proof`.
- Frontend: `SocialLoginButtons.spec.ts`, `SocialAccountLinks.spec.ts`, `SocialLoginCallbackView.spec.ts`, `social-login.spec.ts` (PKCE theo ví dụ RFC 7636), `ProfileLoginMethods.spec.ts`.
- Thử bằng tài khoản thật: cần làm mục 3–5, sau đó đăng nhập bằng một tài khoản có trong Test users (Google) hoặc có vai trò trong ứng dụng (Facebook).
