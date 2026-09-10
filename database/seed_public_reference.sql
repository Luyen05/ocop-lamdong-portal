-- Public-reference data for local development and UI/API testing.
-- Collected on 2026-09-10 from public OCOP and manufacturer sources.
-- This dataset is NOT an official registry and does not prove that a
-- certificate, price, address or contact remains current after collection.
-- Do not run in production.
--
-- OCOP ranking source:
-- https://lamdong.gov.vn/sites/skhcn/hd-quanly/hdql-thongtinchung/SitePages/Le-cong-bo-va-trao-chung-nhan-san-pham-OCOP-tinh-Lam-Dong-nam-2023.aspx
-- Product reference sources:
-- https://nhandan.vn/ocop/tra-atiso-thuong-hang-tui-loc-prod201.html
-- https://ngocduygroup.com/
-- https://nhandan.vn/ocop/ca-phe-pha-phin-dehavi-valley-prod545.html
-- https://dehavi.com/rowoa
-- https://dehavi.com/valley
-- https://dehavi.com/pine-forest
-- Current 2026 ranking decision (3981/QD-UBND dated 2026-08-05):
-- https://ocoplamdong.gov.vn/Media/admin/files/225%20Quye%CC%82%CC%81t%20%C4%91i%CC%A3nh%20Q%C4%90%20cu%CC%89a%20UBND%20ti%CC%89nh_signed.pdf

BEGIN;

INSERT INTO categories (name, slug, description, icon) VALUES
  ('Thực phẩm', 'thuc-pham', 'Sản phẩm thực phẩm OCOP', 'bi-basket'),
  ('Đồ uống', 'do-uong', 'Trà, cà phê, nước ép và đồ uống', 'bi-cup-straw'),
  ('Thảo dược', 'thao-duoc', 'Sản phẩm từ dược liệu địa phương', 'bi-flower1')
ON CONFLICT (slug) DO NOTHING;

-- Technical accounts only exist to satisfy ownership and audit foreign keys.
-- They use reserved .invalid addresses and cannot sign in.
INSERT INTO users (role_id, email, hashed_password, full_name, is_active)
SELECT
  roles.id,
  'public-reference-admin@local.invalid',
  '$argon2id$v=19$m=65536,t=3,p=4$1AXbivzI3q9g7C7t+AK3xw$tLhgXDoJ5dqNYxG+nCTIwFIoMMBaSu2+gcynwqteNVE',
  'Tài khoản nhập dữ liệu nguồn công khai',
  FALSE
FROM roles
WHERE roles.name = 'admin'
ON CONFLICT (email) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  full_name = EXCLUDED.full_name,
  is_active = FALSE;

WITH reference_users(email, full_name) AS (
  VALUES
    ('public-reference-ngoc-duy@local.invalid', 'Dữ liệu công khai - Trà Ngọc Duy'),
    ('public-reference-han-vinh@local.invalid', 'Dữ liệu công khai - Cà phê Hân Vinh'),
    ('public-reference-seagull@local.invalid', 'Dữ liệu công khai - Seagull'),
    ('public-reference-ceres@local.invalid', 'Dữ liệu công khai - Nông nghiệp Ceres'),
    ('public-reference-bechamp@local.invalid', 'Dữ liệu công khai - Bechamp Đắk Nông'),
    ('public-reference-hoang-an@local.invalid', 'Dữ liệu công khai - Atiso Hoàng An Đà Lạt')
)
INSERT INTO users (role_id, email, hashed_password, full_name, is_active)
SELECT
  roles.id,
  reference_users.email,
  '$argon2id$v=19$m=65536,t=3,p=4$1AXbivzI3q9g7C7t+AK3xw$tLhgXDoJ5dqNYxG+nCTIwFIoMMBaSu2+gcynwqteNVE',
  reference_users.full_name,
  FALSE
FROM reference_users
CROSS JOIN roles
WHERE roles.name = 'subject'
ON CONFLICT (email) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  full_name = EXCLUDED.full_name,
  is_active = FALSE;

WITH reference_subjects(
  user_email,
  name,
  representative,
  phone,
  public_email,
  address,
  district
) AS (
  VALUES
    (
      'public-reference-ngoc-duy@local.invalid',
      'Công ty TNHH Trà Ngọc Duy',
      'Đại diện Công ty TNHH Trà Ngọc Duy',
      '02633549284',
      'ngocduy.tea@ngocduygroup.com',
      '73/17 Phan Chu Trinh, Phường 9, thành phố Đà Lạt, tỉnh Lâm Đồng',
      'Đà Lạt'
    ),
    (
      'public-reference-han-vinh@local.invalid',
      'Công ty TNHH Cà phê Hân Vinh',
      'Đại diện Công ty TNHH Cà phê Hân Vinh',
      '0973336060',
      'cafehanvinh@gmail.com',
      'Thôn Đông Anh 2, xã Nam Ban Lâm Hà, tỉnh Lâm Đồng',
      'Lâm Hà'
    ),
    (
      'public-reference-seagull@local.invalid',
      'Công ty TNHH Seagull',
      'Chưa công bố trong nguồn',
      'Chưa công bố',
      NULL,
      'Số 08 Nguyễn Trãi, phường Phan Thiết, tỉnh Lâm Đồng',
      'Phan Thiết'
    ),
    (
      'public-reference-ceres@local.invalid',
      'Chi nhánh Công ty TNHH Nông Nghiệp Ceres',
      'Chưa công bố trong nguồn',
      'Chưa công bố',
      NULL,
      'Thôn Kinh tế mới, xã Ninh Gia, tỉnh Lâm Đồng',
      'Ninh Gia'
    ),
    (
      'public-reference-bechamp@local.invalid',
      'Hợp tác xã Nông sản Hữu cơ Bechamp Đắk Nông',
      'Chưa công bố trong nguồn',
      'Chưa công bố',
      NULL,
      'Thôn 10, xã Trường Xuân, tỉnh Lâm Đồng',
      'Trường Xuân'
    ),
    (
      'public-reference-hoang-an@local.invalid',
      'Công ty TNHH Atiso Hoàng An Đà Lạt',
      'Chưa công bố trong nguồn',
      'Chưa công bố',
      NULL,
      'Thôn 2, xã Lạc Dương, tỉnh Lâm Đồng',
      'Lạc Dương'
    )
)
INSERT INTO subjects (
  user_id,
  name,
  type,
  representative,
  phone,
  email,
  address,
  district,
  status,
  reviewed_by,
  reviewed_at
)
SELECT
  subject_user.id,
  reference_subjects.name,
  'company',
  reference_subjects.representative,
  reference_subjects.phone,
  reference_subjects.public_email,
  reference_subjects.address,
  reference_subjects.district,
  'approved',
  import_admin.id,
  CURRENT_TIMESTAMP
FROM reference_subjects
JOIN users AS subject_user ON subject_user.email = reference_subjects.user_email
CROSS JOIN users AS import_admin
WHERE import_admin.email = 'public-reference-admin@local.invalid'
ON CONFLICT (user_id) DO UPDATE SET
  name = EXCLUDED.name,
  type = EXCLUDED.type,
  representative = EXCLUDED.representative,
  phone = EXCLUDED.phone,
  email = EXCLUDED.email,
  address = EXCLUDED.address,
  district = EXCLUDED.district;

WITH reference_products(
  subject_user_email,
  category_slug,
  name,
  slug,
  star,
  price,
  unit,
  cert_year,
  cert_issued_at,
  description,
  story,
  ingredients,
  usage_instructions,
  source_url,
  image_file
) AS (
  VALUES
    (
      'public-reference-ngoc-duy@local.invalid',
      'do-uong',
      'Trà Atiso thượng hạng túi lọc',
      'tham-khao-tra-atiso-thuong-hang-ngoc-duy',
      4,
      150000.00,
      'gói 100 túi',
      2023,
      NULL::DATE,
      'Trà túi lọc có thành phần chính từ atiso Đà Lạt. Giá trong dữ liệu là giá tham khảo tại ngày thu thập và có thể thay đổi.',
      'Sản phẩm của Công ty TNHH Trà Ngọc Duy; nguồn OCOP công khai ghi nhận hạng 4 sao. Quy cách và giá tham khảo lấy từ website nhà sản xuất ngày 10/09/2026.',
      'Bông atiso, thân atiso và rễ atiso.',
      'Pha với nước nóng theo hướng dẫn trên bao bì của nhà sản xuất.',
      'https://ngocduygroup.com/',
      'artichoke-tea.svg'
    ),
    (
      'public-reference-ngoc-duy@local.invalid',
      'do-uong',
      'Cao nước Atiso Ngọc Duy',
      'tham-khao-cao-nuoc-atiso-ngoc-duy',
      4,
      47000.00,
      'hộp',
      2023,
      NULL::DATE,
      'Sản phẩm cao nước atiso của Trà Ngọc Duy. Giá trong dữ liệu là giá tham khảo tại ngày thu thập và có thể thay đổi.',
      'Nguồn OCOP công khai ghi nhận sản phẩm Cao nước Atiso của Công ty TNHH Trà Ngọc Duy đạt hạng 4 sao; giá tham khảo lấy từ website nhà sản xuất ngày 10/09/2026.',
      NULL,
      'Sử dụng theo hướng dẫn trên bao bì của nhà sản xuất.',
      'https://ngocduygroup.com/',
      'artichoke-tea.svg'
    ),
    (
      'public-reference-ngoc-duy@local.invalid',
      'do-uong',
      'Cao nước Atiso cỏ ngọt',
      'tham-khao-cao-nuoc-atiso-co-ngot-ngoc-duy',
      4,
      71000.00,
      'hộp',
      2023,
      NULL::DATE,
      'Sản phẩm kết hợp atiso và cỏ ngọt của Trà Ngọc Duy. Giá trong dữ liệu là giá tham khảo tại ngày thu thập và có thể thay đổi.',
      'Nguồn OCOP công khai ghi nhận sản phẩm Cao nước Atiso cỏ ngọt của Công ty TNHH Trà Ngọc Duy đạt hạng 4 sao; giá tham khảo lấy từ website nhà sản xuất ngày 10/09/2026.',
      'Atiso và cỏ ngọt.',
      'Sử dụng theo hướng dẫn trên bao bì của nhà sản xuất.',
      'https://ngocduygroup.com/',
      'artichoke-tea.svg'
    ),
    (
      'public-reference-ngoc-duy@local.invalid',
      'do-uong',
      'Cao nước Atiso sâm',
      'tham-khao-cao-nuoc-atiso-sam-ngoc-duy',
      4,
      91000.00,
      'hộp',
      2023,
      NULL::DATE,
      'Sản phẩm cao nước atiso sâm của Trà Ngọc Duy. Giá trong dữ liệu là giá tham khảo tại ngày thu thập và có thể thay đổi.',
      'Nguồn OCOP công khai ghi nhận sản phẩm Cao nước Atiso sâm của Công ty TNHH Trà Ngọc Duy đạt hạng 4 sao; giá tham khảo lấy từ website nhà sản xuất ngày 10/09/2026.',
      NULL,
      'Sử dụng theo hướng dẫn trên bao bì của nhà sản xuất.',
      'https://ngocduygroup.com/',
      'artichoke-tea.svg'
    ),
    (
      'public-reference-han-vinh@local.invalid',
      'do-uong',
      'Cà phê pha phin Dehavi Rowoa',
      'tham-khao-ca-phe-dehavi-rowoa',
      4,
      80000.00,
      'gói 250g',
      2024,
      DATE '2024-01-10',
      'Dòng cà phê pha phin đậm vị của Dehavi. Giá trong dữ liệu là giá tham khảo tại ngày thu thập và có thể thay đổi.',
      'Rowoa là sản phẩm của Công ty TNHH Cà phê Hân Vinh, sử dụng Robusta Nam Ban và Arabica Cầu Đất. Giá tham khảo lấy từ website nhà sản xuất ngày 10/09/2026.',
      '90% Robusta Nam Ban và 10% Arabica Cầu Đất.',
      'Phù hợp pha phin; thực hiện theo hướng dẫn trên bao bì của nhà sản xuất.',
      'https://dehavi.com/rowoa',
      'coffee.svg'
    ),
    (
      'public-reference-han-vinh@local.invalid',
      'do-uong',
      'Cà phê pha phin Dehavi Valley',
      'tham-khao-ca-phe-dehavi-valley',
      4,
      85000.00,
      'gói 250g',
      2024,
      DATE '2024-01-10',
      'Dòng cà phê pha phin cân bằng của Dehavi. Giá trong dữ liệu là giá tham khảo tại ngày thu thập và có thể thay đổi.',
      'Valley là sản phẩm của Công ty TNHH Cà phê Hân Vinh, kết hợp Robusta Nam Ban và Arabica Cầu Đất. Sản phẩm được nguồn OCOP công khai ghi nhận hạng 4 sao.',
      '70% Robusta Nam Ban và 30% Arabica Cầu Đất.',
      'Phù hợp pha phin và cà phê sữa; thực hiện theo hướng dẫn trên bao bì của nhà sản xuất.',
      'https://dehavi.com/valley',
      'coffee.svg'
    ),
    (
      'public-reference-han-vinh@local.invalid',
      'do-uong',
      'Cà phê pha phin Dehavi Pine Forest',
      'tham-khao-ca-phe-dehavi-pine-forest',
      4,
      100000.00,
      'gói 250g',
      2024,
      DATE '2024-01-10',
      'Dòng cà phê pha phin có tỷ lệ Arabica cao hơn trong bộ ba Dehavi. Giá trong dữ liệu là giá tham khảo tại ngày thu thập và có thể thay đổi.',
      'Pine Forest là sản phẩm của Công ty TNHH Cà phê Hân Vinh, kết hợp Robusta Nam Ban và Arabica Cầu Đất. Giá tham khảo lấy từ website nhà sản xuất ngày 10/09/2026.',
      '50% Robusta Nam Ban và 50% Arabica Cầu Đất.',
      'Phù hợp pha phin; thực hiện theo hướng dẫn trên bao bì của nhà sản xuất.',
      'https://dehavi.com/pine-forest',
      'coffee.svg'
    )
)
INSERT INTO ocop_products (
  subject_id,
  category_id,
  name,
  slug,
  star,
  price,
  unit,
  cert_year,
  cert_issued_at,
  issuing_authority,
  description,
  story,
  ingredients,
  usage_instructions,
  rating_avg,
  status,
  reviewed_by,
  reviewed_at,
  review_note,
  version
)
SELECT
  subjects.id,
  categories.id,
  reference_products.name,
  reference_products.slug,
  reference_products.star,
  reference_products.price,
  reference_products.unit,
  reference_products.cert_year,
  reference_products.cert_issued_at,
  'Ủy ban nhân dân tỉnh Lâm Đồng',
  reference_products.description,
  reference_products.story || ' Nguồn sản phẩm: ' || reference_products.source_url,
  reference_products.ingredients,
  reference_products.usage_instructions,
  0,
  'approved',
  import_admin.id,
  CURRENT_TIMESTAMP,
  'Nhập từ nguồn công khai để kiểm thử; không thay thế hồ sơ pháp lý hoặc xác nhận hiệu lực chứng nhận.',
  1
FROM reference_products
JOIN users AS subject_user ON subject_user.email = reference_products.subject_user_email
JOIN subjects ON subjects.user_id = subject_user.id
JOIN categories ON categories.slug = reference_products.category_slug
CROSS JOIN users AS import_admin
WHERE import_admin.email = 'public-reference-admin@local.invalid'
ON CONFLICT (slug) DO UPDATE SET
  subject_id = EXCLUDED.subject_id,
  category_id = EXCLUDED.category_id,
  name = EXCLUDED.name,
  star = EXCLUDED.star,
  price = EXCLUDED.price,
  unit = EXCLUDED.unit,
  cert_year = EXCLUDED.cert_year,
  cert_issued_at = EXCLUDED.cert_issued_at,
  issuing_authority = EXCLUDED.issuing_authority,
  description = EXCLUDED.description,
  story = EXCLUDED.story,
  ingredients = EXCLUDED.ingredients,
  usage_instructions = EXCLUDED.usage_instructions,
  review_note = EXCLUDED.review_note;

WITH reference_products_2026(
  subject_user_email,
  category_slug,
  name,
  slug,
  score
) AS (
  VALUES
    ('public-reference-seagull@local.invalid', 'thuc-pham', 'Mắm nêm Seagull', 'tham-khao-2026-mam-nem-seagull', 69.25),
    ('public-reference-ceres@local.invalid', 'thao-duoc', 'Nấm Fresh Cordyceps Vietnam (Nấm tươi)', 'tham-khao-2026-nam-fresh-cordyceps-vietnam', 66.75),
    ('public-reference-ceres@local.invalid', 'thao-duoc', 'Nấm Cordyceps Vietnam (Nấm khô sấy thăng hoa)', 'tham-khao-2026-nam-cordyceps-vietnam-say-thang-hoa', 67.13),
    ('public-reference-bechamp@local.invalid', 'do-uong', 'beCHAMP Coffee Natural Nắng Vàng', 'tham-khao-2026-bechamp-coffee-natural-nang-vang', 69.29),
    ('public-reference-bechamp@local.invalid', 'do-uong', 'beCHAMP Coffee Gu Mạnh', 'tham-khao-2026-bechamp-coffee-gu-manh', 69.71),
    ('public-reference-bechamp@local.invalid', 'do-uong', 'Bechamp Coffee Hòa Tan Nấm Linh Chi', 'tham-khao-2026-bechamp-coffee-hoa-tan-nam-linh-chi', 69.68),
    ('public-reference-bechamp@local.invalid', 'thuc-pham', 'MACCA BECHAMP', 'tham-khao-2026-macca-bechamp', 69.00),
    ('public-reference-bechamp@local.invalid', 'do-uong', 'beCHAMP Coffee Honey Nắng Vàng', 'tham-khao-2026-bechamp-coffee-honey-nang-vang', 67.78),
    ('public-reference-hoang-an@local.invalid', 'thao-duoc', 'Cao Atiso Hoàng An', 'tham-khao-2026-cao-atiso-hoang-an', 61.75)
)
INSERT INTO ocop_products (
  subject_id,
  category_id,
  name,
  slug,
  star,
  price,
  unit,
  cert_year,
  cert_issued_at,
  cert_expires_at,
  issuing_authority,
  description,
  story,
  rating_avg,
  status,
  reviewed_by,
  reviewed_at,
  review_note,
  version
)
SELECT
  subjects.id,
  categories.id,
  reference_products_2026.name,
  reference_products_2026.slug,
  3,
  0,
  'liên hệ chủ thể',
  2026,
  DATE '2026-08-05',
  DATE '2029-08-05',
  'Ủy ban nhân dân tỉnh Lâm Đồng',
  reference_products_2026.name || ' được công nhận OCOP 3 sao đợt 1 năm 2026. Nguồn quyết định không công bố giá bán hoặc quy cách đóng gói.',
  'Sản phẩm đạt ' || REPLACE(reference_products_2026.score::TEXT, '.', ',') || ' điểm trong danh sách kèm Quyết định 3981/QĐ-UBND ngày 05/08/2026. Nguồn: https://ocoplamdong.gov.vn/Media/admin/files/225%20Quye%CC%82%CC%81t%20%C4%91i%CC%A3nh%20Q%C4%90%20cu%CC%89a%20UBND%20ti%CC%89nh_signed.pdf',
  0,
  'approved',
  import_admin.id,
  CURRENT_TIMESTAMP,
  'Nhập từ Quyết định 3981/QĐ-UBND để kiểm thử; không thay thế hồ sơ pháp lý. Giá và quy cách chưa được nguồn công bố.',
  1
FROM reference_products_2026
JOIN users AS subject_user ON subject_user.email = reference_products_2026.subject_user_email
JOIN subjects ON subjects.user_id = subject_user.id
JOIN categories ON categories.slug = reference_products_2026.category_slug
CROSS JOIN users AS import_admin
WHERE import_admin.email = 'public-reference-admin@local.invalid'
ON CONFLICT (slug) DO UPDATE SET
  subject_id = EXCLUDED.subject_id,
  category_id = EXCLUDED.category_id,
  name = EXCLUDED.name,
  star = EXCLUDED.star,
  price = EXCLUDED.price,
  unit = EXCLUDED.unit,
  cert_year = EXCLUDED.cert_year,
  cert_issued_at = EXCLUDED.cert_issued_at,
  cert_expires_at = EXCLUDED.cert_expires_at,
  issuing_authority = EXCLUDED.issuing_authority,
  description = EXCLUDED.description,
  story = EXCLUDED.story,
  review_note = EXCLUDED.review_note;

WITH reference_images(product_slug, image_file) AS (
  VALUES
    ('tham-khao-tra-atiso-thuong-hang-ngoc-duy', 'artichoke-tea.svg'),
    ('tham-khao-cao-nuoc-atiso-ngoc-duy', 'artichoke-tea.svg'),
    ('tham-khao-cao-nuoc-atiso-co-ngot-ngoc-duy', 'artichoke-tea.svg'),
    ('tham-khao-cao-nuoc-atiso-sam-ngoc-duy', 'artichoke-tea.svg'),
    ('tham-khao-ca-phe-dehavi-rowoa', 'coffee.svg'),
    ('tham-khao-ca-phe-dehavi-valley', 'coffee.svg'),
    ('tham-khao-ca-phe-dehavi-pine-forest', 'coffee.svg'),
    ('tham-khao-2026-mam-nem-seagull', 'public-reference.svg'),
    ('tham-khao-2026-nam-fresh-cordyceps-vietnam', 'public-reference.svg'),
    ('tham-khao-2026-nam-cordyceps-vietnam-say-thang-hoa', 'public-reference.svg'),
    ('tham-khao-2026-bechamp-coffee-natural-nang-vang', 'coffee.svg'),
    ('tham-khao-2026-bechamp-coffee-gu-manh', 'coffee.svg'),
    ('tham-khao-2026-bechamp-coffee-hoa-tan-nam-linh-chi', 'coffee.svg'),
    ('tham-khao-2026-macca-bechamp', 'public-reference.svg'),
    ('tham-khao-2026-bechamp-coffee-honey-nang-vang', 'coffee.svg'),
    ('tham-khao-2026-cao-atiso-hoang-an', 'artichoke-tea.svg')
)
INSERT INTO product_images (
  product_id,
  storage_path,
  image_url,
  alt_text,
  is_primary,
  sort_order
)
SELECT
  products.id,
  'public-reference/product-images/' || products.slug || '/' || reference_images.image_file,
  'http://localhost:5173/assets/demo/products/' || reference_images.image_file,
  'Ảnh minh họa cho ' || products.name || ', không phải ảnh bao bì thực tế',
  TRUE,
  0
FROM reference_images
JOIN ocop_products AS products ON products.slug = reference_images.product_slug
WHERE NOT EXISTS (
  SELECT 1
  FROM product_images
  WHERE product_images.product_id = products.id
    AND product_images.is_primary = TRUE
);

COMMIT;
