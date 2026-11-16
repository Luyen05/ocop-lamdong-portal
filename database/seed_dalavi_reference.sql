-- Dữ liệu tham khảo đã đối chiếu cho Công ty TNHH DaLaVi.
-- Nguồn chứng nhận OCOP và thông tin sản phẩm được ghi ở product_sources.
-- Tọa độ hai cơ sở lấy từ hai liên kết Google Maps do nhóm cung cấp;
-- đây là vị trí tham khảo, không khẳng định cơ sở Păng Tiêng là điểm tham quan.
BEGIN;

INSERT INTO users (role_id, email, hashed_password, full_name, is_active)
SELECT r.id, v.email, '!disabled-dalavi-reference', v.full_name, FALSE
FROM (VALUES
  ('admin', 'dalavi-reference-import@example.com', 'Nhập dữ liệu tham khảo DaLaVi'),
  ('subject', 'dalavi-reference-subject@example.com', 'Công ty TNHH DaLaVi')
) AS v(role_name, email, full_name)
JOIN roles r ON r.name = v.role_name
ON CONFLICT (email) DO NOTHING;

DO $$
BEGIN
  IF (SELECT count(*) FROM users u JOIN roles r ON r.id = u.role_id
      WHERE NOT u.is_active AND (
        (u.email = 'dalavi-reference-import@example.com' AND r.name = 'admin') OR
        (u.email = 'dalavi-reference-subject@example.com' AND r.name = 'subject')
      )) <> 2 THEN
    RAISE EXCEPTION 'DaLaVi technical accounts missing or conflicting; review manually';
  END IF;
END $$;

INSERT INTO subjects (
  user_id, name, type, representative, phone, email, address, district,
  status, reviewed_by, reviewed_at
)
SELECT owner.id, 'Công ty TNHH DaLaVi', 'enterprise',
       'Chưa công bố', '0263.379.8888', 'info@dalavi.vn',
       'Số 27/6 Yersin, phường Xuân Hương, Đà Lạt, Lâm Đồng', 'Đà Lạt',
       'approved', admin.id, CURRENT_TIMESTAMP
FROM users owner
CROSS JOIN users admin
WHERE owner.email = 'dalavi-reference-subject@example.com'
  AND admin.email = 'dalavi-reference-import@example.com'
  AND NOT EXISTS (
    SELECT 1 FROM ocop_products WHERE slug = 'dau-tay-say-deo-dalavi'
  )
ON CONFLICT (user_id) DO NOTHING;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM subjects s
    JOIN users u ON u.id = s.user_id
    WHERE s.name IN ('Công ty TNHH DaLaVi', 'Hợp tác xã Nông nghiệp Aso Farm')
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM ocop_products
      WHERE slug = 'dau-tay-say-deo-dalavi'
    ) THEN
      RAISE EXCEPTION 'DaLaVi subject identity conflict; review manually';
    END IF;
  END IF;
END $$;

INSERT INTO data_sources (
  title, issuing_body, source_type, published_at, source_url, retrieved_at
)
VALUES
  ('Dâu tây sấy dẻo DaLaVi - trang sản phẩm', 'DaLaVi', 'manufacturer_website',
   DATE '2026-03-05', 'https://dautaydalat.vn/san-pham/dau-tay-say-deo/', DATE '2026-10-06'),
  ('Dâu tây sấy dẻo - Cổng OCOP Lâm Đồng', 'Cổng thông tin OCOP Lâm Đồng', 'government_portal',
   NULL, 'https://ocoplamdong.gov.vn/san-pham/thuc-pham-3/dau-tay-say-deo.html', DATE '2026-10-06'),
  ('Đặc sản Đà Lạt DaLaVi', 'Đặc sản Đà Lạt', 'manufacturer_website',
   DATE '2025-07-28', 'https://dacsandalat.com.vn/dac-san-da-lat-dalavi-qua-tang-dac-sac', DATE '2026-10-07'),
  ('Giấy chứng nhận OCOP Dâu tây sấy dẻo', 'UBND thành phố Đà Lạt', 'certificate',
   DATE '2023-12-08', 'https://dautaydalat.vn/wp-content/uploads/2019/10/2024-giay-chung-nhan-Ocop_20240131-dautaysaydeo.jpg', DATE '2026-10-08')
ON CONFLICT (source_url) DO NOTHING;

INSERT INTO ocop_products (
  subject_id, category_id, name, slug, star, price, unit, cert_code,
  cert_year, cert_issued_at, cert_expires_at, issuing_authority,
  certificate_url, description, story, ingredients, usage_instructions,
  status, reviewed_by, reviewed_at, review_note, is_demo
)
SELECT subject.id, category.id, 'Dâu tây sấy dẻo DaLaVi',
       'dau-tay-say-deo-dalavi', 3, 95000, 'Hộp 150 g', '3761/QĐ-UBND',
       2023, DATE '2023-12-08', DATE '2026-12-08',
       'UBND thành phố Đà Lạt',
       'https://dautaydalat.vn/wp-content/uploads/2019/10/2024-giay-chung-nhan-Ocop_20240131-dautaysaydeo.jpg',
       'Dâu tây tươi Đà Lạt được sấy dẻo tự nhiên, đóng hộp quà 150 g. Giá trên website là giá tham khảo và có thể thay đổi.',
       'DaLaVi là thương hiệu đặc sản Đà Lạt của Công ty TNHH DaLaVi. Sản phẩm được chứng nhận OCOP 3 sao năm 2023 theo Quyết định 3761/QĐ-UBND.',
       'Quả dâu tây tươi, đường.',
       'Bảo quản ở nhiệt độ thường. Sau khi mở túi nên cho vào hộp kín và để trong tủ lạnh. Hạn sử dụng 6 tháng.',
       'approved', admin.id, CURRENT_TIMESTAMP,
       'Dữ liệu tham khảo từ nguồn công khai; cần chủ thể xác nhận lại thông tin khi tiếp nhận hồ sơ chính thức.',
       FALSE
FROM subjects subject
JOIN users owner ON owner.id = subject.user_id
JOIN categories category ON category.slug = 'thuc-pham'
CROSS JOIN users admin
WHERE owner.email = 'dalavi-reference-subject@example.com'
  AND admin.email = 'dalavi-reference-import@example.com'
ON CONFLICT (slug) DO NOTHING;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM ocop_products p
    JOIN subjects s ON s.id = p.subject_id
    JOIN users u ON u.id = s.user_id
    WHERE p.slug = 'dau-tay-say-deo-dalavi'
  ) THEN
    RAISE EXCEPTION 'DaLaVi product identity/ownership conflict; review manually';
  END IF;
END $$;

WITH evidence(source_url, verification_level, evidence_role, notes) AS (
  VALUES
    ('https://dautaydalat.vn/san-pham/dau-tay-say-deo/', 'C', 'identity',
     'Nguồn của đơn vị: tên sản phẩm, quy cách, thành phần, giá tham khảo và thông tin kinh doanh.'),
    ('https://ocoplamdong.gov.vn/san-pham/thuc-pham-3/dau-tay-say-deo.html', 'B1', 'recognition',
     'Cổng thông tin OCOP Lâm Đồng ghi sản phẩm Dâu tây sấy dẻo hạng 3 sao.'),
    ('https://dacsandalat.com.vn/dac-san-da-lat-dalavi-qua-tang-dac-sac', 'C', 'address',
     'Nguồn công khai ghi Công ty TNHH DaLaVi và cửa hàng tại 27/6E Yersin.'),
    ('https://dautaydalat.vn/wp-content/uploads/2019/10/2024-giay-chung-nhan-Ocop_20240131-dautaysaydeo.jpg', 'A', 'recognition',
     'Ảnh giấy chứng nhận ghi 3 sao, Công ty TNHH DALAVI, Quyết định 3761/QĐ-UBND ngày 08/12/2023.')
)
INSERT INTO product_sources (
  product_id, source_id, verification_level, evidence_role,
  original_address, verified_at, notes
)
SELECT product.id, source.id, evidence.verification_level, evidence.evidence_role,
       CASE WHEN evidence.evidence_role IN ('address', 'recognition')
            THEN 'Số 27/6 Yersin, phường 10, thành phố Đà Lạt'
            ELSE NULL END,
       DATE '2026-10-08', evidence.notes
FROM evidence
JOIN data_sources source ON source.source_url = evidence.source_url
JOIN ocop_products product ON product.slug = 'dau-tay-say-deo-dalavi'
ON CONFLICT (product_id, source_id, evidence_role) DO NOTHING;

INSERT INTO tourism_locations (
  subject_id, name, slug, type, district, address, geom, contact_phone,
  services, description, website, source_url, status, location_source,
  reviewed_by, reviewed_at, review_note
)
SELECT subject.id, location.name, location.slug, 'other', location.district,
       location.address, ST_SetSRID(ST_MakePoint(location.longitude, location.latitude), 4326),
       '0263.379.8888', location.services, location.description,
       'https://dautaydalat.vn/', location.maps_url, 'approved', 'google_maps_link',
       admin.id, CURRENT_TIMESTAMP, location.review_note
FROM subjects subject
JOIN ocop_products product ON product.subject_id = subject.id
CROSS JOIN users admin
CROSS JOIN (VALUES
  ('Cơ sở DaLaVi - Păng Tiêng', 'dalavi-co-so-pang-tieng', 'Đà Lạt',
   'Păng Tiêng, Phường 7, thành phố Đà Lạt, Lâm Đồng',
   108.3474974::double precision, 11.9908572::double precision,
   ARRAY['Liên hệ chủ thể']::TEXT[],
   'Cơ sở/trụ sở liên quan đến DaLaVi tại khu vực Păng Tiêng. Tọa độ lấy từ liên kết Google Maps do nhóm cung cấp; nguồn hiện có chưa xác nhận đây là điểm tham quan mở cửa.',
   'https://www.google.com/maps/place/P%C4%83ng+Ti%C3%AAng,+Ph%C6%B0%E1%BB%9Dng+7,+Tp.+%C4%90%C3%A0+L%E1%BA%A1t,+L%C3%A2m+%C4%90%E1%BB%93ng,+Vi%E1%BB%87t+Nam/@11.9893517,108.3421948,16.08z/data=!4m6!3m5!1s0x31716df058ee4927:0x2de8171a85d90161!8m2!3d11.9908572!4d108.3474974!16s%2Fg%2F1hhxrst2d?hl=vi&entry=ttu&g_ep=EgoyMDI2MTEwOS4wIKXMDSoASAFQAw%3D%3D',
   'Tọa độ tham khảo từ liên kết Google Maps; chưa có nguồn độc lập xác nhận hoạt động đón khách.'),
  ('Cửa hàng DaLaVi - 27/6E Yersin', 'dalavi-cua-hang-yersin', 'Đà Lạt',
   '27/6E Yersin, phường Xuân Hương, Đà Lạt, Lâm Đồng',
   108.4494328::double precision, 11.9430553::double precision,
   ARRAY['Mua sản phẩm DaLaVi', 'Liên hệ chủ thể']::TEXT[],
   'Cửa hàng DaLaVi tại địa chỉ ghi trên hồ sơ và các nguồn công khai của đơn vị. Tọa độ lấy từ liên kết Google Maps do nhóm cung cấp.',
   'https://www.google.com/maps/search/27%2F6E+Yersin,+P.+Xu%C3%A2n+H%C6%B0%C6%A1ng+-+%C4%90%C3%A0+L%E1%BA%A1t,+T.+L%C3%A2m+%C4%90%E1%BB%93ng/@11.9430553,108.4494328,17.93z?hl=vi&entry=ttu&g_ep=EgoyMDI2MTEwOS4wIKXMDSoASAFQAw%3D%3D',
   'Địa chỉ 27/6 Yersin được ghi trên giấy chứng nhận và nguồn công khai của DaLaVi; tọa độ lấy từ liên kết Google Maps do nhóm cung cấp.')
) AS location(name, slug, district, address, longitude, latitude, services, description, maps_url, review_note)
WHERE product.slug = 'dau-tay-say-deo-dalavi'
  AND admin.email = 'dalavi-reference-import@example.com'
ON CONFLICT (slug) DO NOTHING;

UPDATE tourism_locations
SET name = 'Cơ sở DaLaVi - Păng Tiêng',
    address = 'Păng Tiêng, Phường 7, thành phố Đà Lạt, Lâm Đồng',
    services = ARRAY['Liên hệ chủ thể']::TEXT[],
    description = 'Cơ sở/trụ sở liên quan đến DaLaVi tại khu vực Păng Tiêng. Tọa độ lấy từ liên kết Google Maps do nhóm cung cấp; nguồn hiện có chưa xác nhận đây là điểm tham quan mở cửa.',
    website = 'https://dautaydalat.vn/'
WHERE slug = 'dalavi-co-so-pang-tieng';

UPDATE tourism_locations
SET name = 'Cửa hàng DaLaVi - 27/6E Yersin',
    address = '27/6E Yersin, phường Xuân Hương, Đà Lạt, Lâm Đồng',
    services = ARRAY['Mua sản phẩm DaLaVi', 'Liên hệ chủ thể']::TEXT[],
    description = 'Cửa hàng DaLaVi tại địa chỉ ghi trên hồ sơ và các nguồn công khai của đơn vị. Tọa độ lấy từ liên kết Google Maps do nhóm cung cấp.',
    website = 'https://dautaydalat.vn/'
WHERE slug = 'dalavi-cua-hang-yersin';

INSERT INTO location_ocop_products (location_id, product_id)
SELECT location.id, product.id
FROM tourism_locations location
JOIN ocop_products product ON product.slug = 'dau-tay-say-deo-dalavi'
WHERE location.slug IN ('dalavi-co-so-pang-tieng', 'dalavi-cua-hang-yersin')
ON CONFLICT (location_id, product_id) DO NOTHING;

-- Phân loại cho bản đồ: cơ sở là nơi sản xuất, cửa hàng là nơi bán (migration 015).
UPDATE tourism_locations SET type = 'workshop'
WHERE slug = 'dalavi-co-so-pang-tieng' AND type = 'other';
UPDATE tourism_locations SET type = 'ocop_store'
WHERE slug = 'dalavi-cua-hang-yersin' AND type = 'other';
UPDATE location_ocop_products lop SET role = 'produced_here'
FROM tourism_locations l
WHERE l.id = lop.location_id AND l.slug = 'dalavi-co-so-pang-tieng';

COMMIT;
