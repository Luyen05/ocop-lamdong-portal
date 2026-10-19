-- Đăng nhập bằng Google, Facebook cho người dùng.
-- - users.hashed_password cho phép trống: tài khoản tạo bằng Google/Facebook chưa có mật khẩu,
--   đăng nhập bằng email + mật khẩu sẽ luôn báo sai cho tới khi có chức năng đặt mật khẩu.
-- - user_social_accounts: mỗi dòng là một tài khoản Google/Facebook đã liên kết với một người dùng.
--   provider_user_id là mã định danh do Google/Facebook cấp (không đổi khi người dùng đổi email).
--   Mỗi người dùng liên kết tối đa một tài khoản cho mỗi nhà cung cấp.
-- Không đổi dữ liệu đang có. Chạy lặp lại an toàn.
BEGIN;

ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;

CREATE TABLE IF NOT EXISTS user_social_accounts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider VARCHAR(20) NOT NULL,
  provider_user_id VARCHAR(255) NOT NULL,
  email VARCHAR(150),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE user_social_accounts DROP CONSTRAINT IF EXISTS user_social_accounts_provider_check;
ALTER TABLE user_social_accounts
  ADD CONSTRAINT user_social_accounts_provider_check CHECK (provider IN ('google', 'facebook'));

ALTER TABLE user_social_accounts DROP CONSTRAINT IF EXISTS uq_social_account_provider_user;
ALTER TABLE user_social_accounts
  ADD CONSTRAINT uq_social_account_provider_user UNIQUE (provider, provider_user_id);

ALTER TABLE user_social_accounts DROP CONSTRAINT IF EXISTS uq_social_account_user_provider;
ALTER TABLE user_social_accounts
  ADD CONSTRAINT uq_social_account_user_provider UNIQUE (user_id, provider);

COMMIT;
