-- Chuẩn hóa tên ràng buộc để database nâng cấp qua các migration 001–009 giống hệt database
-- tạo mới từ schema.sql (tools/kiem-tra-database.sql trả kết quả rỗng).
-- Không đổi dữ liệu và không đổi quy tắc kiểm tra, chỉ đặt tên/bỏ bản trùng. Chạy lặp lại an toàn;
-- với database tạo mới từ schema.sql, migration này không làm gì.
BEGIN;

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

COMMIT;
