-- Liên kết dữ liệu bản đồ: điểm du lịch và cửa hàng, sản phẩm, chủ thể.
--
-- - location_ocop_products.role: vai trò của sản phẩm tại điểm (sản xuất, bán, trưng bày).
--   Dữ liệu cũ mặc định là 'sold_here'.
-- - Loại hình mới 'ocop_store' (cửa hàng OCOP) và 'workshop' (cơ sở sản xuất) KHÔNG cần đổi cột:
--   tourism_locations.type là chuỗi tự do. Nhóm "cửa hàng" (shop) được suy ra từ loại hình trong
--   backend (SHOP_LOCATION_TYPES); các loại còn lại là điểm du lịch.
-- - Hai điểm DaLaVi nhập trước đây dùng loại 'other': chuyển thành cơ sở sản xuất và cửa hàng.
-- - Chạy trong một transaction, chạy lặp lại an toàn. Database tạo mới từ schema.sql không cần chạy file này.
-- - Sau khi chạy, mở tools/kiem-tra-database.sql trong pgAdmin: kết quả rỗng là khớp repo.
BEGIN;

ALTER TABLE location_ocop_products
  ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'sold_here';
ALTER TABLE location_ocop_products DROP CONSTRAINT IF EXISTS location_ocop_products_role_check;
ALTER TABLE location_ocop_products ADD CONSTRAINT location_ocop_products_role_check
  CHECK (role IN ('produced_here', 'sold_here', 'displayed'));

UPDATE tourism_locations SET type = 'workshop'
WHERE slug = 'dalavi-co-so-pang-tieng' AND type = 'other';
UPDATE tourism_locations SET type = 'ocop_store'
WHERE slug = 'dalavi-cua-hang-yersin' AND type = 'other';

UPDATE location_ocop_products lop SET role = 'produced_here'
FROM tourism_locations l
WHERE l.id = lop.location_id AND l.slug = 'dalavi-co-so-pang-tieng';

COMMIT;
