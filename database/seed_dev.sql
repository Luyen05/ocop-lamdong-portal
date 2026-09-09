-- Optional starter categories for local development/demo.
INSERT INTO categories (name, slug, description, icon) VALUES
  ('Thực phẩm', 'thuc-pham', 'Sản phẩm thực phẩm OCOP', 'bi-basket'),
  ('Đồ uống', 'do-uong', 'Trà, cà phê, nước ép và đồ uống', 'bi-cup-straw'),
  ('Thảo dược', 'thao-duoc', 'Sản phẩm từ dược liệu địa phương', 'bi-flower1'),
  ('Thủ công mỹ nghệ', 'thu-cong-my-nghe', 'Sản phẩm thủ công và quà tặng', 'bi-palette'),
  ('Sinh vật cảnh', 'sinh-vat-canh', 'Hoa, cây cảnh và sản phẩm trang trí', 'bi-tree'),
  ('Dịch vụ du lịch cộng đồng', 'dich-vu-du-lich-cong-dong', 'Dịch vụ gắn với nông nghiệp và cộng đồng', 'bi-geo-alt')
ON CONFLICT (slug) DO NOTHING;

-- Account only links demo content to an approved subject. It is intentionally disabled.
INSERT INTO users (
  role_id,
  email,
  hashed_password,
  full_name,
  phone,
  is_active
)
SELECT
  id,
  'demo-subject@local.invalid',
  '$argon2id$v=19$m=65536,t=3,p=4$1AXbivzI3q9g7C7t+AK3xw$tLhgXDoJ5dqNYxG+nCTIwFIoMMBaSu2+gcynwqteNVE',
  'Tài khoản dữ liệu mẫu',
  '0900000000',
  FALSE
FROM roles
WHERE name = 'subject'
ON CONFLICT (email) DO NOTHING;

-- Local demo approval attribution only; this admin cannot log in.
INSERT INTO users (role_id, email, hashed_password, full_name, is_active)
SELECT
  id,
  'demo-reviewer@local.invalid',
  '!disabled-demo-reviewer',
  'Demo reviewer (disabled)',
  FALSE
FROM roles
WHERE name = 'admin'
ON CONFLICT (email) DO NOTHING;

INSERT INTO subjects (
  user_id,
  name,
  type,
  tax_code,
  representative,
  phone,
  email,
  address,
  district,
  status,
  reviewed_by,
  reviewed_at,
  rejection_reason
)
SELECT
  id,
  'Hợp tác xã OCOP Lâm Đồng Demo',
  'cooperative',
  'DEMO-OCOP-LD',
  'Nguyễn Văn Demo',
  '0900000000',
  'demo-subject@local.invalid',
  'Thành phố Đà Lạt, tỉnh Lâm Đồng',
  'Đà Lạt',
  'approved',
  (SELECT id FROM users WHERE email = 'demo-reviewer@local.invalid'),
  CURRENT_TIMESTAMP,
  NULL
FROM users
WHERE email = 'demo-subject@local.invalid'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO ocop_products (
  subject_id,
  category_id,
  name,
  slug,
  star,
  price,
  unit,
  cert_code,
  cert_year,
  description,
  story,
  ingredients,
  usage_instructions,
  rating_avg,
  status
)
SELECT
  subjects.id,
  categories.id,
  demo.name,
  demo.slug,
  demo.star,
  demo.price,
  demo.unit,
  demo.cert_code,
  demo.cert_year,
  demo.description,
  demo.story,
  demo.ingredients,
  demo.usage_instructions,
  demo.rating_avg,
  'approved'
FROM subjects
JOIN users ON users.id = subjects.user_id
CROSS JOIN (
  VALUES
    (
      'do-uong',
      'Cà phê Arabica Cầu Đất',
      'ca-phe-arabica-cau-dat-demo',
      5,
      180000.00,
      'hộp 500g',
      'DEMO-OCOP-001',
      2025,
      'Cà phê rang xay nguyên chất từ vùng Cầu Đất.',
      'Sản phẩm được phát triển từ vùng cà phê Arabica lâu đời của Đà Lạt.',
      '100% cà phê Arabica.',
      'Dùng để pha phin hoặc pha máy.',
      4.80
    ),
    (
      'thuc-pham',
      'Mứt dâu Đà Lạt',
      'mut-dau-da-lat-demo',
      4,
      95000.00,
      'hũ 300g',
      'DEMO-OCOP-002',
      2024,
      'Mứt dâu được chế biến từ trái dâu tươi Đà Lạt.',
      'Nguồn nguyên liệu được thu mua từ các hộ trồng dâu địa phương.',
      'Dâu tây, đường phèn.',
      'Dùng trực tiếp hoặc ăn kèm bánh mì.',
      4.25
    ),
    (
      'thao-duoc',
      'Trà atiso túi lọc',
      'tra-atiso-tui-loc-demo',
      4,
      120000.00,
      'hộp 40 túi',
      'DEMO-OCOP-003',
      2025,
      'Trà atiso túi lọc tiện lợi từ nguyên liệu trồng tại Đà Lạt.',
      'Atiso được canh tác và sơ chế tại vùng cao nguyên Lâm Đồng.',
      'Thân, rễ và hoa atiso sấy khô.',
      'Hãm một túi với 200 ml nước nóng trong 3 đến 5 phút.',
      4.60
    ),
    (
      'thuc-pham',
      'Hồng treo gió Đà Lạt',
      'hong-treo-gio-da-lat-demo',
      3,
      160000.00,
      'hộp 500g',
      'DEMO-OCOP-004',
      2023,
      'Hồng chín tự nhiên được làm khô bằng phương pháp treo gió.',
      'Quy trình treo gió giúp giữ vị ngọt tự nhiên và độ dẻo của trái hồng.',
      '100% trái hồng Đà Lạt.',
      'Dùng trực tiếp và bảo quản nơi khô mát.',
      4.10
    )
) AS demo(
  category_slug,
  name,
  slug,
  star,
  price,
  unit,
  cert_code,
  cert_year,
  description,
  story,
  ingredients,
  usage_instructions,
  rating_avg
)
JOIN categories ON categories.slug = demo.category_slug
WHERE users.email = 'demo-subject@local.invalid'
ON CONFLICT (slug) DO NOTHING;

