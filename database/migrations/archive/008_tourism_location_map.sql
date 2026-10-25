-- Bổ sung thông tin liên hệ, nguồn dữ liệu và index cho điểm du lịch phục vụ bản đồ số.
-- Áp dụng một lần cho database tạo trước khi có module bản đồ. Chạy lặp lại an toàn.
BEGIN;

ALTER TABLE tourism_locations
  ADD COLUMN IF NOT EXISTS website VARCHAR(500),
  ADD COLUMN IF NOT EXISTS source_url TEXT;

CREATE INDEX IF NOT EXISTS idx_tourism_locations_subject
  ON tourism_locations (subject_id);
CREATE INDEX IF NOT EXISTS idx_location_ocop_products_product
  ON location_ocop_products (product_id);

COMMIT;
