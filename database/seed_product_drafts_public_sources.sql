-- Sản phẩm tham khảo lưu ở trạng thái bản nháp.
-- Không gán hạng sao OCOP và không xuất hiện ở API công khai.
-- Nguồn Aso Farm/DaLaVi và Dalat Hasfarm chỉ dùng để chủ thể hoàn thiện hồ sơ.
BEGIN;

INSERT INTO users (role_id, email, hashed_password, full_name, is_active)
SELECT role.id, 'hasfarm-reference-subject@example.com',
       '!disabled-reference-draft', 'Dalat Hasfarm', FALSE
FROM roles role
WHERE role.name = 'subject'
  AND NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'hasfarm-reference-subject@example.com'
  )
  AND NOT EXISTS (
    SELECT 1 FROM subjects WHERE name = 'Công ty TNHH Dalat Hasfarm'
  );

INSERT INTO subjects (
  user_id, name, type, representative, phone, email, address, district, status
)
SELECT owner.id, 'Công ty TNHH Dalat Hasfarm', 'enterprise',
       'Chưa công bố', '1800 1143', NULL,
       'Địa chỉ chưa công bố trong nguồn khảo sát', 'Đà Lạt', 'pending'
FROM users owner
WHERE owner.email = 'hasfarm-reference-subject@example.com'
  AND NOT EXISTS (
    SELECT 1 FROM subjects WHERE name = 'Công ty TNHH Dalat Hasfarm'
  )
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO data_sources (title, issuing_body, source_type, source_url, retrieved_at)
VALUES
  ('Danh mục sản phẩm Aso Farm/DaLaVi', 'Aso Farm', 'manufacturer_website',
   'https://dautaydalat.vn/', DATE '2026-11-12'),
  ('Danh mục Dâu Tây Hasfarm', 'Dalat Hasfarm', 'manufacturer_website',
   'https://dalathasfarm.com/c/dau-tay-hasfarm/', DATE '2026-11-12')
ON CONFLICT (source_url) DO NOTHING;

WITH aso_products(name, slug, price, unit, source_url, description) AS (
  VALUES
    ('Dâu tây giống Nhật Bản', 'tham-khao-aso-dau-tay-giong-nhat-ban', 120000, 'hộp 250 g',
     'https://dautaydalat.vn/san-pham/dau-tay-giong-nhat-ban/',
     'Dâu tây giống Nhật Bản được Aso Farm giới thiệu là trồng trong nhà kính tại Đà Lạt. Giá tham khảo từ website.'),
    ('Dâu tây giống Hàn Quốc', 'tham-khao-aso-dau-tay-giong-han-quoc', NULL, NULL,
     'https://dautaydalat.vn/san-pham/dau-tay-giong-han-quoc/',
     'Sản phẩm dâu tươi giống Hàn Quốc do Aso Farm giới thiệu trên website.'),
    ('Dâu mỹ Albion', 'tham-khao-aso-dau-my-albion', NULL, NULL,
     'https://dautaydalat.vn/san-pham/dau-my-albion/',
     'Sản phẩm dâu tươi giống Albion do Aso Farm giới thiệu trên website.'),
    ('Dâu tây Bạch tuyết', 'tham-khao-aso-dau-tay-bach-tuyet', NULL, NULL,
     'https://dautaydalat.vn/san-pham/dau-tay-bach-tuyet/',
     'Sản phẩm dâu tươi Bạch tuyết do Aso Farm giới thiệu trên website.'),
    ('Dâu tây Mỹ Đá', 'tham-khao-aso-dau-tay-my-da', NULL, NULL,
     'https://dautaydalat.vn/san-pham/dau-tay-my-da/',
     'Sản phẩm dâu tươi Mỹ Đá do Aso Farm giới thiệu trên website.'),
    ('Hộp dâu tây trái tim', 'tham-khao-aso-hop-dau-tay-trai-tim', NULL, NULL,
     'https://dautaydalat.vn/san-pham/hop-dau-tay-trai-tim/',
     'Hộp dâu tây do Aso Farm giới thiệu trên website.'),
    ('Hộp quà Dâu tây', 'tham-khao-aso-hop-qua-dau-tay', NULL, NULL,
     'https://dautaydalat.vn/san-pham/hop-qua-dau-tay/',
     'Hộp quà dâu tây do Aso Farm giới thiệu trên website.'),
    ('Nước cốt dâu tây', 'tham-khao-aso-nuoc-cot-dau-tay', 50000, 'chai 350 ml',
     'https://dautaydalat.vn/san-pham/nuoc-cot-day-tay/',
     'Nước cốt dâu tây chai 350 ml do Aso Farm giới thiệu. Giá tham khảo từ website.'),
    ('Mứt dâu tây DaLaVi', 'tham-khao-aso-mut-dau-tay-dalavi', 80000, 'hũ 500 g',
     'https://dautaydalat.vn/san-pham/mut-dau-tay/',
     'Mứt dâu tây thành phần gồm dâu tươi, đường cát và mạch nha. Giá tham khảo từ website.'),
    ('Kẹo hương dâu tây', 'tham-khao-aso-keo-huong-dau-tay', 50000, NULL,
     'https://dautaydalat.vn/san-pham/keo-dau-tay/',
     'Kẹo hương dâu tây do Aso Farm giới thiệu trên website. Giá tham khảo từ website.'),
    ('Muối trái cây DaLaVi', 'tham-khao-aso-muoi-trai-cay', NULL, NULL,
     'https://dautaydalat.vn/san-pham/muoi-trai-cay/',
     'Muối trái cây DaLaVi do Aso Farm giới thiệu trên website.')
)
INSERT INTO ocop_products (
  subject_id, category_id, name, slug, price, unit, description, status, is_demo
)
SELECT subject.id, category.id, item.name, item.slug, item.price, item.unit,
       item.description, 'draft', FALSE
FROM aso_products item
JOIN categories category ON category.slug = 'thuc-pham'
JOIN subjects subject ON subject.name = 'Hợp tác xã Nông nghiệp Aso Farm'
ON CONFLICT (slug) DO NOTHING;

WITH hasfarm_products(name, slug, price, unit) AS (
  VALUES
    ('Dâu Tây Hasfarm Premium 500g', 'tham-khao-hasfarm-dau-tay-premium-500g', 287100, 'hộp 500 g'),
    ('Combo Món Quà Yêu Thương 044', 'tham-khao-hasfarm-combo-mon-qua-044', 900000, 'combo'),
    ('Combo Món Quà Yêu Thương 003', 'tham-khao-hasfarm-combo-mon-qua-003', 790000, 'combo'),
    ('Dâu Tây Hasfarm Premium 230g', 'tham-khao-hasfarm-dau-tay-premium-230g', 199000, 'hộp 230 g'),
    ('Dâu Tây Hasfarm Grade A 500g', 'tham-khao-hasfarm-dau-tay-grade-a-500g', 260100, 'hộp 500 g')
)
INSERT INTO ocop_products (
  subject_id, category_id, name, slug, price, unit, description, status, is_demo
)
SELECT subject.id, category.id, item.name, item.slug, item.price, item.unit,
       'Sản phẩm thương mại do Dalat Hasfarm giới thiệu trên trang bán hàng. Giá tham khảo, chưa có nguồn xác nhận OCOP.',
       'draft', FALSE
FROM hasfarm_products item
JOIN categories category ON category.slug = 'thuc-pham'
JOIN subjects subject ON subject.name = 'Công ty TNHH Dalat Hasfarm'
ON CONFLICT (slug) DO NOTHING;

WITH hasfarm_images(slug, image_url, source_url, storage_path) AS (
  VALUES
    ('tham-khao-hasfarm-dau-tay-premium-500g',
     'https://storage.googleapis.com/cdn_dlhf_vn/public/products/S010/S0100100/z3953984004100_aefc04b533572355c4719b77ac695a0c_800x800.jpg',
     'https://dalathasfarm.com/a5/dau-tay-hasfarm-premium-500gr-p1442.html',
     'external/product-images/hasfarm-dau-tay-premium-500g.jpg'),
    ('tham-khao-hasfarm-combo-mon-qua-044',
     'https://storage.googleapis.com/cdn_dlhf_vn/public/products/WPA0/WPA0044/z4202536861939_3aa188950d93fb11e4d49761d70fbd2a_800x800.jpg',
     'https://dalathasfarm.com/a5/combo-mon-qua-yeu-thuong-044-p218.html',
     'external/product-images/hasfarm-combo-mon-qua-044.jpg'),
    ('tham-khao-hasfarm-combo-mon-qua-003',
     'https://storage.googleapis.com/cdn_dlhf_vn/public/products/CB2X/CB2XMAS003/z3953798569096_bf0cacd78f05d7418e8bdad1a5a8782c_800x800.jpg',
     'https://dalathasfarm.com/a5/combo-mon-qua-yeu-thuong-003-p1498.html',
     'external/product-images/hasfarm-combo-mon-qua-003.jpg'),
    ('tham-khao-hasfarm-dau-tay-premium-230g',
     'https://storage.googleapis.com/cdn_dlhf_vn/public/products/S010/S0100400-AHG230/1794300324_6af2d9a45eafc.jpg',
     'https://dalathasfarm.com/a5/dau-tay-hasfarm-premium-230gr-p3530.html',
     'external/product-images/hasfarm-dau-tay-premium-230g.jpg'),
    ('tham-khao-hasfarm-dau-tay-grade-a-500g',
     'https://storage.googleapis.com/cdn_dlhf_vn/public/products/S010/S0100500-A01/1794294383_6af2c26f804b0.jpg',
     'https://dalathasfarm.com/a5/dau-tay-hasfarm-grade-a-500gr-p1675.html',
     'external/product-images/hasfarm-dau-tay-grade-a-500g.jpg')
)
INSERT INTO product_images (
  product_id, storage_path, image_url, alt_text, is_primary, sort_order,
  source_url, credit, license
)
SELECT product.id, item.storage_path, item.image_url, product.name, TRUE, 0,
       item.source_url, 'Dalat Hasfarm', 'Được chủ thể cho phép'
FROM hasfarm_images item
JOIN ocop_products product ON product.slug = item.slug
WHERE NOT EXISTS (
  SELECT 1 FROM product_images existing
  WHERE existing.product_id = product.id
);

WITH aso_images(slug, image_url, source_url, storage_path, is_primary, sort_order) AS (
  VALUES
    ('tham-khao-aso-dau-tay-giong-nhat-ban',
     'https://dautaydalat.vn/wp-content/uploads/2020/02/dau-tay-nhat-ban-asofarm-6.jpg',
     'https://dautaydalat.vn/san-pham/dau-tay-giong-nhat-ban/',
     'external/product-images/aso-dau-tay-giong-nhat-ban-1.jpg', TRUE, 0),
    ('tham-khao-aso-dau-tay-giong-nhat-ban',
     'https://dautaydalat.vn/wp-content/uploads/2020/02/dau-tay-nhat-ban-asofarm-8.jpg',
     'https://dautaydalat.vn/san-pham/dau-tay-giong-nhat-ban/',
     'external/product-images/aso-dau-tay-giong-nhat-ban-2.jpg', FALSE, 1),
    ('tham-khao-aso-dau-tay-giong-nhat-ban',
     'https://dautaydalat.vn/wp-content/uploads/2020/02/dau-tay-nhat-ban-asofarm-3.jpg',
     'https://dautaydalat.vn/san-pham/dau-tay-giong-nhat-ban/',
     'external/product-images/aso-dau-tay-giong-nhat-ban-3.jpg', FALSE, 2),
    ('tham-khao-aso-dau-tay-giong-han-quoc',
     'https://dautaydalat.vn/wp-content/uploads/2023/08/dau-tay-da-lat-giong-han-quoc-1.jpg',
     'https://dautaydalat.vn/san-pham/dau-tay-giong-han-quoc/',
     'external/product-images/aso-dau-tay-giong-han-quoc-1.jpg', TRUE, 0),
    ('tham-khao-aso-dau-tay-giong-han-quoc',
     'https://dautaydalat.vn/wp-content/uploads/2023/08/vuon-dau-tay-da-lat-giong-han-quoc-1.jpg',
     'https://dautaydalat.vn/san-pham/dau-tay-giong-han-quoc/',
     'external/product-images/aso-dau-tay-giong-han-quoc-2.jpg', FALSE, 1),
    ('tham-khao-aso-dau-my-albion',
     'https://dautaydalat.vn/wp-content/uploads/2023/02/dau-my-albion-2.jpg',
     'https://dautaydalat.vn/san-pham/dau-my-albion/',
     'external/product-images/aso-dau-my-albion-1.jpg', TRUE, 0),
    ('tham-khao-aso-dau-my-albion',
     'https://dautaydalat.vn/wp-content/uploads/2023/02/dau-my-albion-4.jpg',
     'https://dautaydalat.vn/san-pham/dau-my-albion/',
     'external/product-images/aso-dau-my-albion-2.jpg', FALSE, 1),
    ('tham-khao-aso-dau-tay-bach-tuyet',
     'https://dautaydalat.vn/wp-content/uploads/2020/05/dau-tay-bach-tuyet-1.jpg',
     'https://dautaydalat.vn/san-pham/dau-tay-bach-tuyet/',
     'external/product-images/aso-dau-tay-bach-tuyet-1.jpg', TRUE, 0),
    ('tham-khao-aso-dau-tay-my-da',
     'https://dautaydalat.vn/wp-content/uploads/2020/03/48361489_1042997739218199_3568790263000203264_n.jpg',
     'https://dautaydalat.vn/san-pham/dau-tay-my-da/',
     'external/product-images/aso-dau-tay-my-da-1.jpg', TRUE, 0),
    ('tham-khao-aso-hop-qua-dau-tay',
     'https://dautaydalat.vn/wp-content/uploads/2020/03/hop-qua-dau-tay-4.jpg',
     'https://dautaydalat.vn/san-pham/hop-qua-dau-tay/',
     'external/product-images/aso-hop-qua-dau-tay-1.jpg', TRUE, 0),
    ('tham-khao-aso-hop-dau-tay-trai-tim',
     'https://dautaydalat.vn/wp-content/uploads/2025/02/hop-dau-tay-trai-tim-1.jpg',
     'https://dautaydalat.vn/san-pham/hop-dau-tay-trai-tim/',
     'external/product-images/aso-hop-dau-tay-trai-tim-1.jpg', TRUE, 0),
    ('tham-khao-aso-nuoc-cot-dau-tay',
     'https://dautaydalat.vn/wp-content/uploads/2019/10/nuoccot.png',
     'https://dautaydalat.vn/san-pham/nuoc-cot-day-tay/',
     'external/product-images/aso-nuoc-cot-dau-tay-1.png', TRUE, 0),
    ('tham-khao-aso-mut-dau-tay-dalavi',
     'https://dautaydalat.vn/wp-content/uploads/2019/10/mut-dau-tay-5.jpg',
     'https://dautaydalat.vn/san-pham/mut-dau-tay/',
     'external/product-images/aso-mut-dau-tay-dalavi-1.jpg', TRUE, 0),
    ('tham-khao-aso-mut-dau-tay-dalavi',
     'https://dautaydalat.vn/wp-content/uploads/2019/10/mut-dau-tay-dalavi-3.jpg',
     'https://dautaydalat.vn/san-pham/mut-dau-tay/',
     'external/product-images/aso-mut-dau-tay-dalavi-2.jpg', FALSE, 1),
    ('tham-khao-aso-keo-huong-dau-tay',
     'https://dautaydalat.vn/wp-content/uploads/2019/10/keo-dau-tay-5.jpg',
     'https://dautaydalat.vn/san-pham/keo-dau-tay/',
     'external/product-images/aso-keo-huong-dau-tay-1.jpg', TRUE, 0),
    ('tham-khao-aso-keo-huong-dau-tay',
     'https://dautaydalat.vn/wp-content/uploads/2019/10/keo-dau-tay-4.jpg',
     'https://dautaydalat.vn/san-pham/keo-dau-tay/',
     'external/product-images/aso-keo-huong-dau-tay-2.jpg', FALSE, 1),
    ('tham-khao-aso-muoi-trai-cay',
     'https://dautaydalat.vn/wp-content/uploads/2020/05/muoi-cham-trai-cay-dalavi-3.jpg',
     'https://dautaydalat.vn/san-pham/muoi-trai-cay/',
     'external/product-images/aso-muoi-trai-cay-1.jpg', TRUE, 0)
)
INSERT INTO product_images (
  product_id, storage_path, image_url, alt_text, is_primary, sort_order,
  source_url, credit, license
)
SELECT product.id, item.storage_path, item.image_url, product.name,
       item.is_primary, item.sort_order, item.source_url,
       'AsoFarm/DaLaVi', 'Được nhóm cho phép dùng cho đồ án'
FROM aso_images item
JOIN ocop_products product ON product.slug = item.slug
WHERE NOT EXISTS (
  SELECT 1
  FROM product_images existing
  WHERE existing.product_id = product.id
    AND existing.image_url = item.image_url
);

INSERT INTO product_sources (
  product_id, source_id, verification_level, evidence_role, verified_at, notes
)
SELECT product.id, source.id, 'C', 'enrichment', DATE '2026-11-12',
       'Dữ liệu tham khảo lưu bản nháp theo yêu cầu; chưa xác nhận là sản phẩm OCOP.'
FROM ocop_products product
JOIN data_sources source ON source.source_url IN (
  'https://dautaydalat.vn/',
  'https://dalathasfarm.com/c/dau-tay-hasfarm/'
)
WHERE product.slug LIKE 'tham-khao-%'
  AND (
    (product.slug LIKE 'tham-khao-aso-%' AND source.source_url = 'https://dautaydalat.vn/')
    OR
    (product.slug LIKE 'tham-khao-hasfarm-%' AND source.source_url = 'https://dalathasfarm.com/c/dau-tay-hasfarm/')
  )
  AND NOT EXISTS (
    SELECT 1
    FROM product_sources existing
    WHERE existing.product_id = product.id
      AND existing.source_id = source.id
      AND existing.evidence_role = 'enrichment'
  );

COMMIT;
