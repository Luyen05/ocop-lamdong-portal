-- Narrow Dehavi demo seed. See docs/DEHAVI_DEMO_DATA.md.
-- Requires current schema, including migrations 009/011 on older databases.
-- No existing record is updated. Review conflicts rather than overwriting them.
BEGIN;

INSERT INTO categories (name, slug, description, icon)
VALUES ('Đồ uống', 'do-uong', 'Trà, cà phê, nước ép và đồ uống', 'bi-cup-straw')
ON CONFLICT (slug) DO NOTHING;

-- Disabled technical accounts; no usable password. Never alter existing accounts.
INSERT INTO users (role_id, email, hashed_password, full_name, is_active)
SELECT r.id, v.email, '!disabled-dehavi-demo', v.full_name, FALSE
FROM (VALUES
  ('admin', 'dehavi-demo-import@local.invalid', 'Nhập dữ liệu demo Dehavi'),
  ('subject', 'public-reference-han-vinh@local.invalid', 'Dữ liệu công khai - Cà phê Hân Vinh')
) AS v(role_name, email, full_name)
JOIN roles r ON r.name = v.role_name
ON CONFLICT (email) DO NOTHING;

-- Fail atomically if a reserved account belongs to a different role/is active.
DO $$
BEGIN
  IF (SELECT count(*) FROM users u JOIN roles r ON r.id=u.role_id
      WHERE NOT u.is_active AND (
        (u.email='dehavi-demo-import@local.invalid' AND r.name='admin') OR
        (u.email='public-reference-han-vinh@local.invalid' AND r.name='subject')
      )) <> 2 THEN
    RAISE EXCEPTION 'Dehavi technical accounts missing or conflicting; review manually';
  END IF;
END $$;

INSERT INTO subjects (
  user_id, name, type, representative, phone, email, address, district,
  status, reviewed_by, reviewed_at
)
SELECT owner.id, 'Công ty TNHH Cà phê Hân Vinh', 'company',
       'Chưa xác minh người đại diện', '0973336060', 'cafehanvinh@gmail.com',
       'Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng', 'Lâm Hà',
       'approved', admin.id, CURRENT_TIMESTAMP
FROM users owner CROSS JOIN users admin
WHERE owner.email='public-reference-han-vinh@local.invalid'
  AND admin.email='dehavi-demo-import@local.invalid'
ON CONFLICT (user_id) DO NOTHING;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM subjects s JOIN users u ON u.id=s.user_id
    WHERE u.email='public-reference-han-vinh@local.invalid'
      AND s.name='Công ty TNHH Cà phê Hân Vinh'
  ) THEN
    RAISE EXCEPTION 'Han Vinh subject identity conflict; review manually';
  END IF;
END $$;

INSERT INTO ocop_products (
  subject_id, category_id, name, slug, star, price, unit,
  description, story, ingredients, usage_instructions,
  status, reviewed_by, reviewed_at, review_note, is_demo
)
SELECT s.id, c.id, 'Cà phê pha phin Dehavi Valley',
       'tham-khao-ca-phe-dehavi-valley', 4, 85000, 'gói 250g',
       'Cà phê pha phin cân bằng của Dehavi. Giá tham khảo, có thể thay đổi.',
       'Valley của Công ty TNHH Cà phê Hân Vinh. Nguồn sản phẩm: https://dehavi.com/valley',
       '70% Robusta Nam Ban và 30% Arabica Cầu Đất.',
       'Phù hợp pha phin và cà phê sữa; theo hướng dẫn trên bao bì.',
       'approved', admin.id, CURRENT_TIMESTAMP,
       'Dữ liệu demo từ nguồn công khai; recognition B1, không xác nhận hiệu lực chứng nhận.', FALSE
FROM subjects s JOIN users owner ON owner.id=s.user_id
CROSS JOIN categories c CROSS JOIN users admin
WHERE owner.email='public-reference-han-vinh@local.invalid'
  AND c.slug='do-uong' AND admin.email='dehavi-demo-import@local.invalid'
ON CONFLICT (slug) DO NOTHING;

-- Do not attach recognition evidence to a slug owned by someone else.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM ocop_products p JOIN subjects s ON s.id=p.subject_id
    JOIN users u ON u.id=s.user_id
    WHERE p.slug='tham-khao-ca-phe-dehavi-valley'
      AND p.name='Cà phê pha phin Dehavi Valley'
      AND u.email='public-reference-han-vinh@local.invalid'
  ) THEN
    RAISE EXCEPTION 'Dehavi Valley identity/ownership conflict; review manually';
  END IF;
END $$;

-- Public eligibility uses recognition evidence, NOT invented certificate dates.
-- B1 = public newspaper confirmation; C = manufacturer identity/enrichment.
INSERT INTO data_sources (title, issuing_body, source_type, source_url, retrieved_at)
VALUES
  ('Cà-phê pha phin Dehavi Valley - OCOP 4 sao', 'Báo Nhân Dân', 'government_news',
   'https://nhandan.vn/ocop/ca-phe-pha-phin-dehavi-valley-prod545.html', DATE '2026-09-29'),
  ('Dehavi Valley - thành phần và quy cách', 'Dehavi Coffee', 'manufacturer_website',
   'https://dehavi.com/valley', DATE '2026-09-29'),
  ('Công ty TNHH Cà phê Hân Vinh - văn phòng và showroom', 'Công ty TNHH Cà phê Hân Vinh', 'manufacturer_website',
   'https://hanvinhcoffee.vn/ve-chung-toi', DATE '2026-09-29'),
  ('Dehavi Showroom - trải nghiệm và trưng bày sản phẩm', 'Dehavi Coffee', 'manufacturer_website',
   'https://dehavi.com/cup-dehavi-showroom', DATE '2026-09-29'),
  ('Dehavi - chính sách mua hàng trực tiếp tại showroom', 'Dehavi Coffee', 'manufacturer_website',
   'https://dehavi.com/chinh-sach-giao-nhan-va-van-chuyen', DATE '2026-09-29')
ON CONFLICT (source_url) DO NOTHING;

WITH evidence(source_url, evidence_role, verification_level, notes) AS (
  VALUES
    ('https://nhandan.vn/ocop/ca-phe-pha-phin-dehavi-valley-prod545.html', 'recognition', 'B1',
     'Nguồn xác nhận Valley OCOP 4 sao Lâm Đồng; Thuận đã đối chiếu ngoài repo. Audit 2026-09-29 đọc được kết quả chỉ mục, không tải được toàn trang. Không xác nhận số chứng nhận, ngày cấp hoặc ngày hết hạn.'),
    ('https://dehavi.com/valley', 'enrichment', 'C',
     '70% Robusta Nam Ban, 30% Arabica Cầu Đất. Cầu Đất là nguồn nguyên liệu, không phải quan hệ với Cầu Đất Farm. Giá là tham khảo, không phải cam kết giá hiện tại.'),
    ('https://hanvinhcoffee.vn/ve-chung-toi', 'identity', 'C',
     'Dehavi Coffee là thương hiệu của Công ty TNHH Cà phê Hân Vinh; website công ty liệt kê Dehavi Coffee Showroom.'),
    ('https://hanvinhcoffee.vn/ve-chung-toi', 'address', 'C',
     'Văn phòng và showroom tại Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng. Giữ địa chỉ nguồn, không tự ánh xạ địa giới.'),
    ('https://dehavi.com/cup-dehavi-showroom', 'enrichment', 'C',
     'Showroom có thưởng thức cà phê, quan sát quá trình sản xuất và trưng bày sản phẩm công ty.'),
    ('https://dehavi.com/chinh-sach-giao-nhan-va-van-chuyen', 'enrichment', 'C',
     'Hãng cho phép mua hàng trực tiếp tại Dehavi Showroom. Liên kết Valley với điểm trưng bày/bán sản phẩm Dehavi, không khẳng định tồn kho tức thời.')
)
INSERT INTO product_sources (
  product_id, source_id, evidence_role, verification_level, original_address, verified_at, notes
)
SELECT p.id, s.id, e.evidence_role, e.verification_level,
       'Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng', DATE '2026-09-29', e.notes
FROM evidence e
JOIN data_sources s ON s.source_url = e.source_url
CROSS JOIN ocop_products p
WHERE p.slug = 'tham-khao-ca-phe-dehavi-valley'
ON CONFLICT (product_id, source_id, evidence_role) DO NOTHING;

-- Requires current schema (including migrations 009 and 011 on older databases).
-- Coordinates: manual verification from Google Maps by project member Thuận,
-- supplied on 2026-09-29. Raw lat/lon: 11.842185897748251, 108.34119094061145.
-- Rounded lat/lon: 11.842186, 108.341191. No independently retrieved Maps URL.
-- The official source_url below proves showroom identity/services, NOT coordinates.
INSERT INTO tourism_locations (
  subject_id, name, slug, type, district, address, geom, contact_phone,
  services, description, website, source_url, status, location_source,
  reviewed_by, reviewed_at, review_note
)
SELECT subject.id, 'Dehavi Showroom', 'dehavi-showroom', 'other', 'Lâm Hà',
       'Khu Đông Anh 2, Nam Ban, Lâm Hà, Lâm Đồng',
       ST_SetSRID(ST_MakePoint(108.341191, 11.842186), 4326), '0973336060',
       ARRAY['Thưởng thức cà phê', 'Quan sát quá trình sản xuất', 'Trưng bày và bán sản phẩm Dehavi']::TEXT[],
       'Showroom của Công ty TNHH Cà phê Hân Vinh: thưởng thức cà phê, quan sát và cảm nhận quá trình sản xuất, tìm hiểu sản phẩm công ty. Có mua hàng trực tiếp theo chính sách của Dehavi; không cam kết tồn kho từng sản phẩm.',
       'https://dehavi.com/', 'https://dehavi.com/cup-dehavi-showroom',
       'approved', 'coordinates', admin.id, CURRENT_TIMESTAMP,
       'Dữ liệu demo được thành viên dự án đối chiếu, không phải xác nhận hành chính. Tọa độ: manual verification from Google Maps by project member Thuận, 2026-09-29; raw latitude=11.842185897748251, longitude=108.34119094061145; rounded latitude=11.842186, longitude=108.341191. Chưa lưu URL ghim Google Maps. Nguồn chủ thể: https://hanvinhcoffee.vn/ve-chung-toi ; mua trực tiếp: https://dehavi.com/chinh-sach-giao-nhan-va-van-chuyen'
FROM subjects subject
JOIN users owner ON owner.id = subject.user_id
CROSS JOIN users admin
WHERE owner.email = 'public-reference-han-vinh@local.invalid'
  AND admin.email = 'dehavi-demo-import@local.invalid'
ON CONFLICT (slug) DO NOTHING;

-- Do not claim ownership or create a relation if this slug belongs to someone else.
INSERT INTO location_ocop_products (location_id, product_id)
SELECT location.id, product.id
FROM tourism_locations location
JOIN ocop_products product ON product.subject_id = location.subject_id
JOIN subjects subject ON subject.id = location.subject_id
JOIN users owner ON owner.id = subject.user_id
WHERE location.slug = 'dehavi-showroom'
  AND product.slug = 'tham-khao-ca-phe-dehavi-valley'
  AND owner.email = 'public-reference-han-vinh@local.invalid'
ON CONFLICT (location_id, product_id) DO NOTHING;

COMMIT;
