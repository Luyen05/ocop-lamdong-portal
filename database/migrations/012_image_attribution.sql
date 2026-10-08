-- Ghi nguồn, tác giả và giấy phép cho ảnh (ảnh lấy từ web dùng để minh họa phải ghi rõ nguồn).
-- - source_url: trang gốc của ảnh (http/https).
-- - credit: tên tác giả hoặc nơi đăng ảnh, hiện kèm ảnh trên trang công khai.
-- - license: giấy phép sử dụng, ví dụ "CC BY-SA 4.0", "Unsplash License", "Được chủ vườn cho phép".
-- Cả ba cột cho phép trống: ảnh chủ thể tự tải lên không cần ghi nguồn.
-- Không đổi dữ liệu đang có. Chạy lặp lại an toàn.
BEGIN;

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

COMMIT;
