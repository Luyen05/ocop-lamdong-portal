-- Cho phép chủ thể khai báo điểm du lịch và gửi admin kiểm duyệt.
-- - Trạng thái theo cùng quy trình với sản phẩm: draft -> pending -> needs_revision / approved / rejected.
-- - Ghi lại cách chủ thể lấy vị trí (ghim bản đồ, GPS, dán tọa độ, link Google Maps) và độ chính xác GPS
--   để admin biết mức tin cậy khi đối chiếu.
-- - Điểm đã duyệt được sửa qua yêu cầu cập nhật (tourism_location_change_requests): điểm cũ vẫn hiển thị
--   trên bản đồ cho tới khi admin duyệt thay đổi.
-- - Ảnh điểm du lịch do chủ thể tải lên có đường dẫn lưu trữ và mô tả ảnh như ảnh sản phẩm.
-- Áp dụng cho database tạo trước migration này. Chạy lặp lại an toàn.
BEGIN;

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
  DROP CONSTRAINT IF EXISTS tourism_locations_location_source_check,
  DROP CONSTRAINT IF EXISTS tourism_locations_location_accuracy_check,
  DROP CONSTRAINT IF EXISTS tourism_locations_version_check;

ALTER TABLE tourism_locations
  ADD CONSTRAINT tourism_locations_status_check CHECK (
    status IN ('draft', 'pending', 'needs_revision', 'approved', 'rejected')
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

COMMIT;
