-- Migration tổng hợp: đưa database ở BẤT KỲ phiên bản cũ nào của dự án lên cấu trúc cuối cùng
-- (giống hệt database tạo mới từ database/schema.sql).
--
-- - Gồm nội dung các migration 001–013 (bản gốc lưu ở database/migrations/archive/), đã sửa để chạy lặp
--   lại an toàn trên database mới nhất, cộng các thay đổi cuối cùng:
--     * danh mục: is_visible, sort_order (admin ẩn/sắp xếp danh mục);
--     * đánh giá: reviewed_by, reviewed_at, rejection_reason (admin kiểm duyệt đánh giá);
--     * loại chủ thể 'company' cũ đổi thành 'enterprise';
--     * trigger updated_at bỏ qua khi chỉ tăng lượt xem.
-- - Chạy trong một transaction: lỗi ở bất kỳ bước nào thì không thay đổi gì.
-- - Chạy lặp lại an toàn. Database tạo mới từ schema.sql không cần chạy file này.
-- - Sau khi chạy, mở tools/kiem-tra-database.sql trong pgAdmin: kết quả rỗng là khớp repo.
--
-- Cách chạy (PowerShell, thư mục gốc repo):
--   Get-Content .\database\migrations\014_hoan_thien.sql -Raw -Encoding UTF8 |
--     docker compose exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
BEGIN;

-- ============================================================================
-- Bước 001: 001_hardening.sql
-- ============================================================================
-- Apply this once in pgAdmin to an existing database created before schema.sql
-- was committed. The transaction rolls back if duplicate reviews or multiple
-- primary images violate the new unique indexes; clean those rows, then retry.

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'review_exactly_one_target') THEN
    ALTER TABLE reviews ADD CONSTRAINT review_exactly_one_target CHECK (
      (product_id IS NOT NULL AND location_id IS NULL) OR
      (product_id IS NULL AND location_id IS NOT NULL)
    );
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_subjects_geom ON subjects USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_tourism_locations_geom ON tourism_locations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_products_public_filters ON ocop_products (status, category_id, star);
CREATE INDEX IF NOT EXISTS idx_locations_public_filters ON tourism_locations (status, district, type);
CREATE INDEX IF NOT EXISTS idx_reviews_product_status ON reviews (product_id, status);
CREATE INDEX IF NOT EXISTS idx_reviews_location_status ON reviews (location_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS uq_product_primary_image ON product_images (product_id) WHERE is_primary;
CREATE UNIQUE INDEX IF NOT EXISTS uq_location_primary_image ON location_images (location_id) WHERE is_primary;
CREATE UNIQUE INDEX IF NOT EXISTS uq_news_primary_image ON news_images (news_id) WHERE is_primary;
CREATE UNIQUE INDEX IF NOT EXISTS uq_review_user_product ON reviews (user_id, product_id) WHERE product_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_review_user_location ON reviews (user_id, location_id) WHERE location_id IS NOT NULL;

CREATE OR REPLACE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_subjects_updated_at BEFORE UPDATE ON subjects
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_products_updated_at BEFORE UPDATE ON ocop_products
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_locations_updated_at BEFORE UPDATE ON tourism_locations
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_reviews_updated_at BEFORE UPDATE ON reviews
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_news_updated_at BEFORE UPDATE ON news
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- Bước 002: 002_subject_moderation.sql
-- ============================================================================
-- Apply this once to databases created before the subject application workflow.

ALTER TABLE subjects
  ADD COLUMN IF NOT EXISTS reviewed_by BIGINT REFERENCES users(id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_subjects_review_state'
  ) THEN
    ALTER TABLE subjects ADD CONSTRAINT ck_subjects_review_state CHECK (
      (status = 'pending' AND reviewed_by IS NULL AND reviewed_at IS NULL AND rejection_reason IS NULL)
      OR (status = 'approved' AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL AND rejection_reason IS NULL)
      OR (
        status = 'rejected'
        AND reviewed_by IS NOT NULL
        AND reviewed_at IS NOT NULL
        AND rejection_reason IS NOT NULL
        AND BTRIM(rejection_reason) <> ''
      )
    );
  END IF;
END $$;

-- ============================================================================
-- Bước 003: 003_sync_product_rating.sql
-- ============================================================================
-- Apply this once to databases created before the public product API.

ALTER TABLE ocop_products
  ADD COLUMN IF NOT EXISTS rating_avg NUMERIC(3, 2) NOT NULL DEFAULT 0
  CHECK (rating_avg BETWEEN 0 AND 5);

-- ============================================================================
-- Bước 004: 004_product_moderation.sql
-- ============================================================================
-- Add the product publication workflow to an existing database.

ALTER TABLE ocop_products
  ADD COLUMN IF NOT EXISTS cert_issued_at DATE,
  ADD COLUMN IF NOT EXISTS cert_expires_at DATE,
  ADD COLUMN IF NOT EXISTS issuing_authority VARCHAR(255),
  ADD COLUMN IF NOT EXISTS certificate_url VARCHAR(500),
  ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS reviewed_by BIGINT REFERENCES users(id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS review_note TEXT,
  ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

ALTER TABLE ocop_products
  ALTER COLUMN status SET DEFAULT 'draft',
  DROP CONSTRAINT IF EXISTS ocop_products_status_check,
  DROP CONSTRAINT IF EXISTS ck_product_status,
  DROP CONSTRAINT IF EXISTS ck_ocop_products_status,
  DROP CONSTRAINT IF EXISTS ck_ocop_products_review_state,
  DROP CONSTRAINT IF EXISTS product_certificate_dates;

ALTER TABLE ocop_products
  ADD CONSTRAINT ocop_products_status_check CHECK (
    status IN (
      'draft',
      'pending',
      'needs_revision',
      'approved',
      'rejected',
      'suspended',
      'archived'
    )
  ),
  ADD CONSTRAINT product_certificate_dates CHECK (
    cert_issued_at IS NULL OR cert_expires_at IS NULL OR cert_expires_at > cert_issued_at
  );

ALTER TABLE product_images
  ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500),
  ADD COLUMN IF NOT EXISTS alt_text VARCHAR(255);

UPDATE product_images
SET storage_path = 'legacy/product-images/' || id
WHERE storage_path IS NULL OR BTRIM(storage_path) = '';

ALTER TABLE product_images
  ALTER COLUMN storage_path SET NOT NULL,
  ALTER COLUMN image_url TYPE VARCHAR(1000);

DO $$
BEGIN
  -- Database đã có ràng buộc product_images_storage_path_key (bước 010) thì không tạo index trùng.
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'product_images_storage_path_key') THEN
    CREATE UNIQUE INDEX IF NOT EXISTS uq_product_images_storage_path ON product_images (storage_path);
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS product_change_requests (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES ocop_products(id) ON DELETE CASCADE,
  subject_id BIGINT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('update', 'delete')),
  proposed_data JSONB,
  reason TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'needs_revision', 'approved', 'rejected', 'cancelled')),
  base_version INTEGER NOT NULL CHECK (base_version >= 1),
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_by BIGINT REFERENCES users(id) ON DELETE RESTRICT,
  reviewed_at TIMESTAMPTZ,
  review_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT product_change_payload CHECK (
    (request_type = 'update' AND proposed_data IS NOT NULL)
    OR (request_type = 'delete' AND proposed_data IS NULL)
  )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_product_active_change_request
  ON product_change_requests (product_id)
  WHERE status IN ('pending', 'needs_revision');

DROP TRIGGER IF EXISTS trg_product_change_requests_updated_at ON product_change_requests;
CREATE TRIGGER trg_product_change_requests_updated_at
BEFORE UPDATE ON product_change_requests
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- Bước 005: 005_add_product_sources.sql
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_sources (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(500) NOT NULL,
  document_number VARCHAR(100),
  issuing_body VARCHAR(255),
  source_type VARCHAR(50) NOT NULL,
  published_at DATE,
  source_url TEXT NOT NULL UNIQUE,
  local_path VARCHAR(500),
  sha256 VARCHAR(64),
  retrieved_at DATE NOT NULL,
  CONSTRAINT data_source_sha256_format CHECK (
    sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$'
  )
);

CREATE TABLE IF NOT EXISTS product_sources (
  product_id BIGINT NOT NULL REFERENCES ocop_products(id) ON DELETE CASCADE,
  source_id BIGINT NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
  verification_level VARCHAR(2) NOT NULL
    CHECK (verification_level IN ('A', 'B1', 'B2', 'C')),
  original_address TEXT,
  evidence_role VARCHAR(30) NOT NULL
    CHECK (evidence_role IN ('recognition', 'identity', 'address', 'enrichment')),
  verified_at DATE NOT NULL,
  notes TEXT,
  PRIMARY KEY (product_id, source_id, evidence_role)
);

CREATE INDEX IF NOT EXISTS idx_product_sources_source
  ON product_sources (source_id);

-- ============================================================================
-- Bước 006: 006_simplify_subject_product_flow.sql
-- ============================================================================
-- Allow subjects to save incomplete product drafts and attach a private certificate file.

ALTER TABLE ocop_products
  ALTER COLUMN star DROP NOT NULL,
  ALTER COLUMN price DROP NOT NULL,
  ALTER COLUMN unit DROP NOT NULL,
  ALTER COLUMN description DROP NOT NULL,
  ADD COLUMN IF NOT EXISTS certificate_storage_path VARCHAR(500);

CREATE UNIQUE INDEX IF NOT EXISTS uq_products_certificate_storage_path
  ON ocop_products (certificate_storage_path)
  WHERE certificate_storage_path IS NOT NULL;

-- ============================================================================
-- Bước 007: 007_hide_demo_products.sql
-- ============================================================================
ALTER TABLE ocop_products
  ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE ocop_products AS products
SET is_demo = TRUE
WHERE products.slug LIKE 'demo-workflow-%'
   OR products.cert_code LIKE 'DEMO-OCOP-%'
   OR products.subject_id IN (
     SELECT subjects.id
     FROM subjects
     JOIN users ON users.id = subjects.user_id
     WHERE users.email IN (
       'demo-subject@local.invalid',
       'chuthe.ocop.demo@example.com'
     )
   );

CREATE INDEX IF NOT EXISTS idx_products_public_visibility
  ON ocop_products (status, is_demo, category_id, star);

-- ============================================================================
-- Bước 008: 008_tourism_location_map.sql
-- ============================================================================
-- Bổ sung thông tin liên hệ, nguồn dữ liệu và index cho điểm du lịch phục vụ bản đồ số.
-- Áp dụng một lần cho database tạo trước khi có module bản đồ. Chạy lặp lại an toàn.

ALTER TABLE tourism_locations
  ADD COLUMN IF NOT EXISTS website VARCHAR(500),
  ADD COLUMN IF NOT EXISTS source_url TEXT;

CREATE INDEX IF NOT EXISTS idx_tourism_locations_subject
  ON tourism_locations (subject_id);
CREATE INDEX IF NOT EXISTS idx_location_ocop_products_product
  ON location_ocop_products (product_id);

-- ============================================================================
-- Bước 009: 009_tourism_location_submissions.sql
-- ============================================================================
-- Cho phép chủ thể khai báo điểm du lịch và gửi admin kiểm duyệt.
-- - Trạng thái theo cùng quy trình với sản phẩm: draft -> pending -> needs_revision / approved / rejected.
-- - Ghi lại cách chủ thể lấy vị trí (ghim bản đồ, GPS, dán tọa độ, link Google Maps) và độ chính xác GPS
--   để admin biết mức tin cậy khi đối chiếu.
-- - Điểm đã duyệt được sửa qua yêu cầu cập nhật (tourism_location_change_requests): điểm cũ vẫn hiển thị
--   trên bản đồ cho tới khi admin duyệt thay đổi.
-- - Ảnh điểm du lịch do chủ thể tải lên có đường dẫn lưu trữ và mô tả ảnh như ảnh sản phẩm.
-- Áp dụng cho database tạo trước migration này. Chạy lặp lại an toàn.

-- 0. Một số database cũ tạo bảng tourism_locations/location_images thiếu các cột nền đã có trong
--    schema.sql (ví dụ rating_avg), làm API bản đồ báo lỗi. Bổ sung nếu thiếu, không đổi dữ liệu đang có.
ALTER TABLE tourism_locations
  ADD COLUMN IF NOT EXISTS services TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS description TEXT,
  ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20),
  ADD COLUMN IF NOT EXISTS opening_hours VARCHAR(100),
  ADD COLUMN IF NOT EXISTS ticket_price NUMERIC(12,2) CHECK (ticket_price >= 0),
  ADD COLUMN IF NOT EXISTS website VARCHAR(500),
  ADD COLUMN IF NOT EXISTS source_url TEXT,
  ADD COLUMN IF NOT EXISTS rating_avg NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (rating_avg BETWEEN 0 AND 5),
  ADD COLUMN IF NOT EXISTS views INTEGER NOT NULL DEFAULT 0 CHECK (views >= 0),
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE location_images
  ADD COLUMN IF NOT EXISTS is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0 CHECK (sort_order >= 0);

-- Hàm dùng chung của schema.sql; tạo lại (giống hệt) để trigger bên dưới luôn chạy được.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_locations_updated_at ON tourism_locations;
CREATE TRIGGER trg_locations_updated_at BEFORE UPDATE ON tourism_locations
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 1. Điểm du lịch: trạng thái kiểm duyệt, nguồn vị trí, phiên bản.
ALTER TABLE tourism_locations
  ADD COLUMN IF NOT EXISTS location_source VARCHAR(20) NOT NULL DEFAULT 'admin_import',
  ADD COLUMN IF NOT EXISTS location_accuracy_m NUMERIC(8,2),
  ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS reviewed_by BIGINT REFERENCES users(id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS review_note TEXT,
  ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

ALTER TABLE tourism_locations
  ALTER COLUMN status SET DEFAULT 'draft',
  DROP CONSTRAINT IF EXISTS tourism_locations_status_check,
  -- migration 001_hardening.sql thêm ràng buộc này chỉ cho 3 trạng thái cũ, chặn draft/needs_revision.
  DROP CONSTRAINT IF EXISTS ck_location_status,
  DROP CONSTRAINT IF EXISTS tourism_locations_location_source_check,
  DROP CONSTRAINT IF EXISTS tourism_locations_location_accuracy_check,
  DROP CONSTRAINT IF EXISTS tourism_locations_version_check;

ALTER TABLE tourism_locations
  ADD CONSTRAINT tourism_locations_status_check CHECK (
    status IN ('draft', 'pending', 'needs_revision', 'approved', 'rejected', 'archived')
  ),
  ADD CONSTRAINT tourism_locations_location_source_check CHECK (
    location_source IN ('admin_import', 'map_pin', 'device_gps', 'coordinates', 'google_maps_link')
  ),
  ADD CONSTRAINT tourism_locations_location_accuracy_check CHECK (
    location_accuracy_m IS NULL OR location_accuracy_m >= 0
  ),
  ADD CONSTRAINT tourism_locations_version_check CHECK (version >= 1);

-- Hàng chờ duyệt của admin: lọc theo trạng thái, sắp theo thời điểm gửi.
CREATE INDEX IF NOT EXISTS idx_tourism_locations_review_queue
  ON tourism_locations (status, submitted_at);

-- 2. Ảnh điểm du lịch: đường dẫn lưu trữ (ảnh chủ thể tải lên), mô tả ảnh, thời điểm tạo.
ALTER TABLE location_images
  ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500),
  ADD COLUMN IF NOT EXISTS alt_text VARCHAR(255),
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Ảnh cũ (link ngoài) không có đường dẫn lưu trữ nên chỉ bắt buộc duy nhất khi có giá trị.
CREATE UNIQUE INDEX IF NOT EXISTS uq_location_images_storage_path
  ON location_images (storage_path)
  WHERE storage_path IS NOT NULL;

-- 3. Yêu cầu cập nhật / ngừng hiển thị điểm du lịch đã duyệt.
CREATE TABLE IF NOT EXISTS tourism_location_change_requests (
  id BIGSERIAL PRIMARY KEY,
  location_id BIGINT NOT NULL REFERENCES tourism_locations(id) ON DELETE CASCADE,
  subject_id BIGINT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('update', 'delete')),
  proposed_data JSONB,
  reason TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'needs_revision', 'approved', 'rejected', 'cancelled')),
  base_version INTEGER NOT NULL CHECK (base_version >= 1),
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_by BIGINT REFERENCES users(id) ON DELETE RESTRICT,
  reviewed_at TIMESTAMPTZ,
  review_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT location_change_payload CHECK (
    (request_type = 'update' AND proposed_data IS NOT NULL)
    OR (request_type = 'delete' AND proposed_data IS NULL)
  )
);

-- Mỗi điểm chỉ có tối đa một yêu cầu đang mở.
CREATE UNIQUE INDEX IF NOT EXISTS uq_location_active_change_request
  ON tourism_location_change_requests (location_id)
  WHERE status IN ('pending', 'needs_revision');
CREATE INDEX IF NOT EXISTS idx_location_change_requests_subject
  ON tourism_location_change_requests (subject_id, status);

DROP TRIGGER IF EXISTS trg_location_change_requests_updated_at ON tourism_location_change_requests;
CREATE TRIGGER trg_location_change_requests_updated_at BEFORE UPDATE ON tourism_location_change_requests
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- Bước 010: 010_normalize_constraint_names.sql
-- ============================================================================
-- Chuẩn hóa tên ràng buộc để database nâng cấp qua các migration 001–009 giống hệt database
-- tạo mới từ schema.sql (tools/kiem-tra-database.sql trả kết quả rỗng).
-- Không đổi dữ liệu và không đổi quy tắc kiểm tra, chỉ đặt tên/bỏ bản trùng. Chạy lặp lại an toàn;
-- với database tạo mới từ schema.sql, migration này không làm gì.

-- 1. 004 thêm cột version nhưng chưa có ràng buộc version >= 1 như schema.sql.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'ocop_products'::regclass AND conname = 'ocop_products_version_check'
  ) THEN
    ALTER TABLE ocop_products ADD CONSTRAINT ocop_products_version_check CHECK (version >= 1);
  END IF;
END $$;

-- 2. 004 tạo index duy nhất uq_product_images_storage_path; schema.sql dùng ràng buộc UNIQUE
--    product_images_storage_path_key. Chuyển index thành ràng buộc đúng tên (cùng tác dụng).
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'product_images'::regclass AND conname = 'product_images_storage_path_key'
  ) THEN
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'uq_product_images_storage_path' AND relkind = 'i') THEN
      ALTER TABLE product_images
        ADD CONSTRAINT product_images_storage_path_key UNIQUE USING INDEX uq_product_images_storage_path;
    ELSE
      ALTER TABLE product_images
        ADD CONSTRAINT product_images_storage_path_key UNIQUE (storage_path);
    END IF;
  END IF;
END $$;

-- 3. 001 thêm ck_subject_status, ck_review_status, ck_news_status trùng với ràng buộc trạng thái
--    có sẵn trong schema.sql. Chỉ bỏ bản trùng khi ràng buộc gốc của schema.sql đã có.
DO $$
DECLARE
  pair RECORD;
BEGIN
  FOR pair IN
    SELECT * FROM (VALUES
      ('subjects', 'ck_subject_status', 'subjects_status_check'),
      ('reviews', 'ck_review_status', 'reviews_status_check'),
      ('news', 'ck_news_status', 'news_status_check')
    ) AS t(table_name, duplicate_name, schema_name)
  LOOP
    IF EXISTS (
      SELECT 1 FROM pg_constraint
      WHERE conrelid = pair.table_name::regclass AND conname = pair.schema_name
    ) THEN
      EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I', pair.table_name, pair.duplicate_name);
    END IF;
  END LOOP;
END $$;

-- ============================================================================
-- Bước 011: 011_tourism_location_drafts.sql
-- ============================================================================
-- Chuẩn bị cho chức năng chủ thể khai báo điểm du lịch (API /subject/locations) và admin duyệt.
-- - Bản nháp được lưu dần theo từng phần của biểu mẫu, nên vị trí, xã/phường và địa chỉ có thể
--   còn trống khi đang soạn (draft) hoặc đang bổ sung (needs_revision). Các trạng thái còn lại
--   (chờ duyệt, đã duyệt, từ chối, ngừng hiển thị) bắt buộc đủ ba thông tin này.
-- - Thêm trạng thái archived: điểm đã duyệt được ngừng hiển thị khi admin duyệt yêu cầu của chủ thể.
-- Không đổi dữ liệu đang có. Chạy lặp lại an toàn.

ALTER TABLE tourism_locations
  ALTER COLUMN geom DROP NOT NULL,
  ALTER COLUMN district DROP NOT NULL,
  ALTER COLUMN address DROP NOT NULL;

ALTER TABLE tourism_locations
  DROP CONSTRAINT IF EXISTS tourism_locations_status_check,
  DROP CONSTRAINT IF EXISTS tourism_locations_required_fields_check;

ALTER TABLE tourism_locations
  ADD CONSTRAINT tourism_locations_status_check CHECK (
    status IN ('draft', 'pending', 'needs_revision', 'approved', 'rejected', 'archived')
  ),
  ADD CONSTRAINT tourism_locations_required_fields_check CHECK (
    status IN ('draft', 'needs_revision')
    OR (geom IS NOT NULL AND district IS NOT NULL AND address IS NOT NULL)
  );

-- ============================================================================
-- Bước 012: 012_image_attribution.sql
-- ============================================================================
-- Ghi nguồn, tác giả và giấy phép cho ảnh (ảnh lấy từ web dùng để minh họa phải ghi rõ nguồn).
-- - source_url: trang gốc của ảnh (http/https).
-- - credit: tên tác giả hoặc nơi đăng ảnh, hiện kèm ảnh trên trang công khai.
-- - license: giấy phép sử dụng, ví dụ "CC BY-SA 4.0", "Unsplash License", "Được chủ vườn cho phép".
-- Cả ba cột cho phép trống: ảnh chủ thể tự tải lên không cần ghi nguồn.
-- Không đổi dữ liệu đang có. Chạy lặp lại an toàn.

ALTER TABLE location_images
  ADD COLUMN IF NOT EXISTS source_url VARCHAR(500),
  ADD COLUMN IF NOT EXISTS credit VARCHAR(255),
  ADD COLUMN IF NOT EXISTS license VARCHAR(100);

ALTER TABLE product_images
  ADD COLUMN IF NOT EXISTS source_url VARCHAR(500),
  ADD COLUMN IF NOT EXISTS credit VARCHAR(255),
  ADD COLUMN IF NOT EXISTS license VARCHAR(100);

ALTER TABLE location_images DROP CONSTRAINT IF EXISTS location_images_source_url_check;
ALTER TABLE location_images
  ADD CONSTRAINT location_images_source_url_check CHECK (
    source_url IS NULL OR source_url LIKE 'http://%' OR source_url LIKE 'https://%'
  );

ALTER TABLE product_images DROP CONSTRAINT IF EXISTS product_images_source_url_check;
ALTER TABLE product_images
  ADD CONSTRAINT product_images_source_url_check CHECK (
    source_url IS NULL OR source_url LIKE 'http://%' OR source_url LIKE 'https://%'
  );

-- ============================================================================
-- Bước 013: 013_social_login.sql
-- ============================================================================
-- Đăng nhập bằng Google, Facebook cho người dùng.
-- - users.hashed_password cho phép trống: tài khoản tạo bằng Google/Facebook chưa có mật khẩu,
--   đăng nhập bằng email + mật khẩu sẽ luôn báo sai cho tới khi có chức năng đặt mật khẩu.
-- - user_social_accounts: mỗi dòng là một tài khoản Google/Facebook đã liên kết với một người dùng.
--   provider_user_id là mã định danh do Google/Facebook cấp (không đổi khi người dùng đổi email).
--   Mỗi người dùng liên kết tối đa một tài khoản cho mỗi nhà cung cấp.
-- Không đổi dữ liệu đang có. Chạy lặp lại an toàn.

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

-- ============================================================================
-- Bước 014: thay đổi cuối cùng
-- ============================================================================

-- Danh mục: ẩn khỏi bộ lọc và ô chọn khi tạo sản phẩm mới; thứ tự hiển thị.
ALTER TABLE categories
  ADD COLUMN IF NOT EXISTS is_visible BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_sort_order_check;
ALTER TABLE categories ADD CONSTRAINT categories_sort_order_check CHECK (sort_order >= 0);

-- Đánh giá: lưu vết kiểm duyệt; từ chối phải có lý do.
ALTER TABLE reviews
  ADD COLUMN IF NOT EXISTS reviewed_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
UPDATE reviews SET rejection_reason = 'Không đạt yêu cầu kiểm duyệt.'
WHERE status = 'rejected' AND (rejection_reason IS NULL OR length(trim(rejection_reason)) = 0);
ALTER TABLE reviews DROP CONSTRAINT IF EXISTS reviews_rejection_reason_check;
ALTER TABLE reviews ADD CONSTRAINT reviews_rejection_reason_check CHECK (
  status <> 'rejected'
  OR (rejection_reason IS NOT NULL AND length(trim(rejection_reason)) > 0)
);

-- Loại chủ thể: dữ liệu cũ dùng 'company' (API chỉ nhận 4 loại) làm trang duyệt hồ sơ lỗi.
UPDATE subjects SET type = 'enterprise' WHERE type = 'company';

-- updated_at: không đổi khi chỉ tăng lượt xem (danh sách của chủ thể sắp theo updated_at).
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  IF (to_jsonb(NEW) - 'views' - 'updated_at') = (to_jsonb(OLD) - 'views' - 'updated_at') THEN
    NEW.updated_at = OLD.updated_at;
  ELSE
    NEW.updated_at = CURRENT_TIMESTAMP;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMIT;
