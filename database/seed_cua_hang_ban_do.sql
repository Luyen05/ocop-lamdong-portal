-- Cửa hàng và cơ sở sản xuất MINH HỌA để bản đồ có đủ liên kết chủ thể - sản phẩm - địa điểm.
--
-- CHÚ Ý: đây là dữ liệu do nhóm tạo để trình diễn, CHƯA xác minh ngoài thực địa.
--   - Vị trí là tọa độ trung tâm thị trấn/thành phố (cộng độ lệch nhỏ cố định), không phải địa chỉ thật.
--   - Mô tả và ghi chú duyệt đều ghi rõ "minh họa"; không có source_url.
--   - Thay bằng dữ liệu thật sau khi chủ thể khai báo hoặc nhóm xác minh (xem docs/DU_LIEU.md).
-- Chạy lặp lại an toàn (ON CONFLICT DO NOTHING). Chạy sau seed_ocop_2025_2026.sql, seed_product_workflow.sql.
BEGIN;

-- 1. Cơ sở sản xuất minh họa: tối đa 8 chủ thể đã duyệt có sản phẩm đã duyệt.
WITH area_center(district, latitude, longitude) AS (
  VALUES
    ('Đà Lạt',    11.9404::double precision, 108.4383::double precision),
    ('Bảo Lộc',   11.5480, 107.8077),
    ('Đức Trọng', 11.7333, 108.3667),
    ('Di Linh',   11.5833, 108.0667),
    ('Lâm Hà',    11.8845, 108.2190),
    ('Đơn Dương', 11.7667, 108.5833),
    ('Bảo Lâm',   11.5333, 107.7833),
    ('Lạc Dương', 12.0167, 108.4333)
), picked_subjects AS (
  SELECT s.id, s.name, s.address, s.district,
         row_number() OVER (ORDER BY count(p.id) DESC, s.id) AS rank
  FROM subjects s
  JOIN ocop_products p ON p.subject_id = s.id AND p.status = 'approved'
  WHERE s.status = 'approved'
  GROUP BY s.id
), admin_user AS (
  SELECT u.id FROM users u JOIN roles r ON r.id = u.role_id
  WHERE r.name = 'admin' ORDER BY u.id LIMIT 1
)
INSERT INTO tourism_locations (
  subject_id, name, slug, type, district, address, geom, services, description,
  status, location_source, reviewed_by, reviewed_at, review_note
)
SELECT ps.id,
       'Cơ sở sản xuất ' || ps.name,
       'co-so-san-xuat-minh-hoa-' || ps.id,
       'workshop',
       COALESCE(ps.district, 'Đà Lạt'),
       COALESCE(NULLIF(ps.address, ''), 'Lâm Đồng'),
       ST_SetSRID(ST_MakePoint(
         COALESCE(ac.longitude, 108.4383) + ((hashtext(ps.id::text) % 100) / 100.0 - 0.5) * 0.02,
         COALESCE(ac.latitude, 11.9404) + ((hashtext(ps.id::text || 'y') % 100) / 100.0 - 0.5) * 0.02
       ), 4326),
       ARRAY['Liên hệ chủ thể']::TEXT[],
       '[Dữ liệu minh họa] Cơ sở sản xuất của ' || ps.name || '. Vị trí là tọa độ tham khảo theo khu vực, chưa xác minh thực địa.',
       'approved', 'admin_import', admin_user.id, CURRENT_TIMESTAMP,
       'Dữ liệu minh họa do nhóm tạo để trình diễn liên kết bản đồ; cần xác minh vị trí thật.'
FROM picked_subjects ps
CROSS JOIN admin_user
LEFT JOIN area_center ac ON ac.district = ps.district
WHERE ps.rank <= 8
ON CONFLICT (slug) DO NOTHING;

-- Sản phẩm đã duyệt của chủ thể được sản xuất tại cơ sở của chính chủ thể (tối đa 5 sản phẩm mỗi cơ sở).
INSERT INTO location_ocop_products (location_id, product_id, role)
SELECT l.id, ranked.id, 'produced_here'
FROM tourism_locations l
JOIN LATERAL (
  SELECT p.id FROM ocop_products p
  WHERE p.subject_id = l.subject_id AND p.status = 'approved'
  ORDER BY p.star DESC NULLS LAST, p.name LIMIT 5
) ranked ON TRUE
WHERE l.slug LIKE 'co-so-san-xuat-minh-hoa-%'
ON CONFLICT (location_id, product_id) DO NOTHING;

-- 2. Điểm giới thiệu và bán sản phẩm OCOP minh họa (không thuộc chủ thể nào).
WITH admin_user AS (
  SELECT u.id FROM users u JOIN roles r ON r.id = u.role_id
  WHERE r.name = 'admin' ORDER BY u.id LIMIT 1
)
INSERT INTO tourism_locations (
  name, slug, type, district, address, geom, opening_hours, services, description,
  status, location_source, reviewed_by, reviewed_at, review_note
)
SELECT shop.name, shop.slug, 'ocop_store', shop.district, shop.address,
       ST_SetSRID(ST_MakePoint(shop.longitude, shop.latitude), 4326),
       '08:00 - 20:00',
       ARRAY['Mua sản phẩm OCOP', 'Quà tặng đặc sản']::TEXT[],
       '[Dữ liệu minh họa] Điểm giới thiệu và bán sản phẩm OCOP tại ' || shop.district
         || '. Tên và vị trí là minh họa, chưa xác minh thực địa.',
       'approved', 'admin_import', admin_user.id, CURRENT_TIMESTAMP,
       'Dữ liệu minh họa do nhóm tạo để trình diễn liên kết bản đồ; cần xác minh vị trí thật.'
FROM admin_user
CROSS JOIN (VALUES
  ('Điểm giới thiệu sản phẩm OCOP - Đà Lạt (minh họa)', 'diem-ocop-minh-hoa-da-lat',
   'Đà Lạt', 'Khu vực trung tâm Đà Lạt, Lâm Đồng', 11.9436::double precision, 108.4380::double precision),
  ('Điểm giới thiệu sản phẩm OCOP - Bảo Lộc (minh họa)', 'diem-ocop-minh-hoa-bao-loc',
   'Bảo Lộc', 'Khu vực trung tâm Bảo Lộc, Lâm Đồng', 11.5480, 107.8077),
  ('Điểm giới thiệu sản phẩm OCOP - Đức Trọng (minh họa)', 'diem-ocop-minh-hoa-duc-trong',
   'Đức Trọng', 'Khu vực thị trấn Liên Nghĩa, Đức Trọng, Lâm Đồng', 11.7333, 108.3667),
  ('Điểm giới thiệu sản phẩm OCOP - Di Linh (minh họa)', 'diem-ocop-minh-hoa-di-linh',
   'Di Linh', 'Khu vực thị trấn Di Linh, Lâm Đồng', 11.5833, 108.0667),
  ('Điểm giới thiệu sản phẩm OCOP - Lâm Hà (minh họa)', 'diem-ocop-minh-hoa-lam-ha',
   'Lâm Hà', 'Khu vực thị trấn Nam Ban, Lâm Hà, Lâm Đồng', 11.8845, 108.2190)
) AS shop(name, slug, district, address, latitude, longitude)
ON CONFLICT (slug) DO NOTHING;

-- Mỗi điểm bán nhận mỗi nhóm sản phẩm một sản phẩm đã duyệt, chọn theo băm cố định để các điểm không giống nhau.
INSERT INTO location_ocop_products (location_id, product_id, role)
SELECT l.id, picked.id, 'sold_here'
FROM tourism_locations l
JOIN LATERAL (
  SELECT ranked.id FROM (
    SELECT p.id,
           row_number() OVER (PARTITION BY p.category_id ORDER BY md5(p.slug || l.slug)) AS rn
    FROM ocop_products p
    WHERE p.status = 'approved'
  ) ranked WHERE ranked.rn = 1
) picked ON TRUE
WHERE l.slug LIKE 'diem-ocop-minh-hoa-%'
ON CONFLICT (location_id, product_id) DO NOTHING;

-- 3. Điểm du lịch có sẵn giới thiệu sản phẩm của chính chủ thể (nếu có) với vai trò "trưng bày".
INSERT INTO location_ocop_products (location_id, product_id, role)
SELECT l.id, p.id, 'displayed'
FROM tourism_locations l
JOIN ocop_products p ON p.subject_id = l.subject_id AND p.status = 'approved'
WHERE l.subject_id IS NOT NULL
  AND l.type NOT IN ('ocop_store', 'workshop')
ON CONFLICT (location_id, product_id) DO NOTHING;

COMMIT;
