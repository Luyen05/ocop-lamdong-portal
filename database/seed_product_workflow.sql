-- Optional development data for testing the product moderation workflow.
-- DO NOT run this file in production.
-- Shared demo password: DemoOCOP@2026
-- Demo accounts:
--   admin.ocop.demo@example.com   (admin)
--   chuthe.ocop.demo@example.com  (subject)
--   ungvien.ocop.demo@example.com (user with a pending subject application)
BEGIN;

INSERT INTO users (role_id, email, hashed_password, full_name, phone, is_active)
SELECT
  roles.id,
  'admin.ocop.demo@example.com',
  '$argon2id$v=19$m=65536,t=3,p=4$omxliNzu83V7YdXSSKpF6Q$rMrCOodYH8KBvkAuekdkfyF0aMtd542DKqbDBlsdzag',
  'Quản trị viên kiểm thử',
  '0901000001',
  TRUE
FROM roles
WHERE roles.name = 'admin'
ON CONFLICT (email) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  hashed_password = EXCLUDED.hashed_password,
  full_name = EXCLUDED.full_name,
  phone = EXCLUDED.phone,
  is_active = TRUE;

INSERT INTO users (role_id, email, hashed_password, full_name, phone, is_active)
SELECT
  roles.id,
  'ungvien.ocop.demo@example.com',
  '$argon2id$v=19$m=65536,t=3,p=4$omxliNzu83V7YdXSSKpF6Q$rMrCOodYH8KBvkAuekdkfyF0aMtd542DKqbDBlsdzag',
  'Người dùng đăng ký chủ thể',
  '0901000003',
  TRUE
FROM roles
WHERE roles.name = 'user'
ON CONFLICT (email) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  hashed_password = EXCLUDED.hashed_password,
  full_name = EXCLUDED.full_name,
  phone = EXCLUDED.phone,
  is_active = TRUE;

INSERT INTO users (role_id, email, hashed_password, full_name, phone, is_active)
SELECT
  roles.id,
  'chuthe.ocop.demo@example.com',
  '$argon2id$v=19$m=65536,t=3,p=4$omxliNzu83V7YdXSSKpF6Q$rMrCOodYH8KBvkAuekdkfyF0aMtd542DKqbDBlsdzag',
  'Chủ thể OCOP kiểm thử',
  '0901000002',
  TRUE
FROM roles
WHERE roles.name = 'subject'
ON CONFLICT (email) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  hashed_password = EXCLUDED.hashed_password,
  full_name = EXCLUDED.full_name,
  phone = EXCLUDED.phone,
  is_active = TRUE;

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
  subject_user.id,
  'Hợp tác xã Nông sản Langbiang Demo',
  'cooperative',
  'DEMO-WORKFLOW-2026',
  'Nguyễn Văn Kiểm Thử',
  '0901000002',
  'chuthe.ocop.demo@example.com',
  'Phường Lang Biang - Đà Lạt, tỉnh Lâm Đồng',
  'Đà Lạt',
  'approved',
  admin_user.id,
  CURRENT_TIMESTAMP,
  NULL
FROM users AS subject_user
CROSS JOIN users AS admin_user
WHERE subject_user.email = 'chuthe.ocop.demo@example.com'
  AND admin_user.email = 'admin.ocop.demo@example.com'
ON CONFLICT (user_id) DO UPDATE SET
  name = EXCLUDED.name,
  type = EXCLUDED.type,
  tax_code = EXCLUDED.tax_code,
  representative = EXCLUDED.representative,
  phone = EXCLUDED.phone,
  email = EXCLUDED.email,
  address = EXCLUDED.address,
  district = EXCLUDED.district,
  status = 'approved',
  reviewed_by = EXCLUDED.reviewed_by,
  reviewed_at = EXCLUDED.reviewed_at,
  rejection_reason = NULL;

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
  applicant.id,
  'Cơ sở đặc sản Cao Nguyên Demo',
  'household',
  'DEMO-APPLICANT-2026',
  'Trần Minh Demo',
  '0901000003',
  'ungvien.ocop.demo@example.com',
  'Phường Xuân Hương - Đà Lạt, tỉnh Lâm Đồng',
  'Đà Lạt',
  'pending',
  NULL,
  NULL,
  NULL
FROM users AS applicant
WHERE applicant.email = 'ungvien.ocop.demo@example.com'
ON CONFLICT (user_id) DO UPDATE SET
  name = EXCLUDED.name,
  type = EXCLUDED.type,
  tax_code = EXCLUDED.tax_code,
  representative = EXCLUDED.representative,
  phone = EXCLUDED.phone,
  email = EXCLUDED.email,
  address = EXCLUDED.address,
  district = EXCLUDED.district,
  status = 'pending',
  reviewed_by = NULL,
  reviewed_at = NULL,
  rejection_reason = NULL;

WITH demo_products (
  category_slug,
  name,
  slug,
  star,
  price,
  unit,
  cert_code,
  description,
  story,
  ingredients,
  usage_instructions,
  status,
  submitted_at,
  review_note,
  image_file
) AS (
  VALUES
    (
      'thao-duoc',
      'Trà atiso túi lọc - Bản nháp kiểm thử',
      'demo-workflow-tra-atiso-draft',
      4,
      125000.00,
      'hộp 40 túi',
      'DEMO-OCOP-DRAFT-001',
      'Trà atiso túi lọc từ vùng nguyên liệu tại Đà Lạt.',
      'Sản phẩm minh họa đang được chủ thể hoàn thiện trước khi gửi duyệt.',
      'Thân, rễ và hoa atiso sấy khô.',
      'Hãm một túi với 200 ml nước nóng trong 3 đến 5 phút.',
      'draft',
      NULL::TIMESTAMPTZ,
      NULL,
      'artichoke-tea.svg'
    ),
    (
      'thuc-pham',
      'Mứt dâu Đà Lạt - Chờ duyệt',
      'demo-workflow-mut-dau-pending',
      3,
      95000.00,
      'hũ 300g',
      'DEMO-OCOP-PENDING-002',
      'Mứt dâu được chế biến từ dâu tươi trồng tại Đà Lạt.',
      'Sản phẩm minh họa đã được chủ thể gửi và đang chờ quản trị viên kiểm tra.',
      'Dâu tây, đường phèn.',
      'Dùng trực tiếp hoặc ăn kèm bánh mì.',
      'pending',
      CURRENT_TIMESTAMP - INTERVAL '1 day',
      NULL,
      'strawberry-jam.svg'
    ),
    (
      'do-uong',
      'Cà phê Arabica - Cần bổ sung',
      'demo-workflow-ca-phe-revision',
      4,
      185000.00,
      'hộp 500g',
      'DEMO-OCOP-REVISION-003',
      'Cà phê Arabica rang xay từ vùng Cầu Đất.',
      'Hồ sơ minh họa cần chủ thể thay đường dẫn ảnh chứng nhận rõ hơn.',
      '100% cà phê Arabica.',
      'Pha phin hoặc pha máy.',
      'needs_revision',
      CURRENT_TIMESTAMP - INTERVAL '3 days',
      'Ảnh giấy chứng nhận chưa rõ số quyết định. Vui lòng tải lại minh chứng.',
      'coffee.svg'
    ),
    (
      'thuc-pham',
      'Hồng treo gió Đà Lạt - Đã duyệt',
      'demo-workflow-hong-treo-gio-approved',
      3,
      165000.00,
      'hộp 500g',
      'DEMO-OCOP-APPROVED-004',
      'Hồng chín tự nhiên được làm khô bằng phương pháp treo gió.',
      'Sản phẩm minh họa đã được đối chiếu chứng nhận và công khai.',
      'Hồng tươi Đà Lạt.',
      'Dùng trực tiếp, bảo quản nơi khô mát.',
      'approved',
      CURRENT_TIMESTAMP - INTERVAL '5 days',
      'Đã đối chiếu thông tin trên giấy chứng nhận minh họa.',
      'persimmon.svg'
    ),
    (
      'thuc-pham',
      'Mật ong hoa cà phê - Chờ ngừng hiển thị',
      'demo-workflow-mat-ong-approved',
      4,
      210000.00,
      'chai 500ml',
      'DEMO-OCOP-DELETE-005',
      'Mật ong thu hoạch trong mùa hoa cà phê tại Lâm Đồng.',
      'Sản phẩm công khai dùng để kiểm tra yêu cầu ngừng hiển thị.',
      '100% mật ong nguyên chất.',
      'Dùng trực tiếp hoặc pha cùng nước ấm.',
      'approved',
      CURRENT_TIMESTAMP - INTERVAL '6 days',
      'Đã duyệt hiển thị cho mục đích kiểm thử.',
      'honey.svg'
    ),
    (
      'thao-duoc',
      'Bột rau má sấy lạnh - Bị từ chối',
      'demo-workflow-rau-ma-rejected',
      3,
      110000.00,
      'hộp 20 gói',
      'DEMO-OCOP-REJECTED-006',
      'Bột rau má hòa tan được chế biến bằng phương pháp sấy lạnh.',
      'Hồ sơ minh họa bị từ chối vì mã chứng nhận không khớp.',
      'Bột rau má.',
      'Pha một gói với 200 ml nước.',
      'rejected',
      CURRENT_TIMESTAMP - INTERVAL '4 days',
      'Mã chứng nhận khai báo không khớp tài liệu minh chứng.',
      'artichoke-tea.svg'
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
  cert_code,
  cert_year,
  cert_issued_at,
  cert_expires_at,
  issuing_authority,
  certificate_url,
  description,
  story,
  ingredients,
  usage_instructions,
  status,
  submitted_at,
  reviewed_by,
  reviewed_at,
  review_note,
  is_demo,
  version
)
SELECT
  subjects.id,
  categories.id,
  demo_products.name,
  demo_products.slug,
  demo_products.star,
  demo_products.price,
  demo_products.unit,
  demo_products.cert_code,
  2026,
  DATE '2026-01-15',
  DATE '2029-01-15',
  'Cơ quan có thẩm quyền tỉnh Lâm Đồng (dữ liệu minh họa)',
  'http://localhost:5173/assets/demo/certificates/ocop-demo.svg',
  demo_products.description,
  demo_products.story,
  demo_products.ingredients,
  demo_products.usage_instructions,
  demo_products.status,
  demo_products.submitted_at,
  CASE
    WHEN demo_products.status IN ('approved', 'needs_revision', 'rejected') THEN admin_user.id
    ELSE NULL
  END,
  CASE
    WHEN demo_products.status IN ('approved', 'needs_revision', 'rejected') THEN CURRENT_TIMESTAMP - INTERVAL '1 day'
    ELSE NULL
  END,
  demo_products.review_note,
  TRUE,
  1
FROM demo_products
JOIN categories ON categories.slug = demo_products.category_slug
CROSS JOIN subjects
JOIN users AS subject_user ON subject_user.id = subjects.user_id
CROSS JOIN users AS admin_user
WHERE subject_user.email = 'chuthe.ocop.demo@example.com'
  AND admin_user.email = 'admin.ocop.demo@example.com'
ON CONFLICT (slug) DO UPDATE SET
  subject_id = EXCLUDED.subject_id,
  category_id = EXCLUDED.category_id,
  name = EXCLUDED.name,
  star = EXCLUDED.star,
  price = EXCLUDED.price,
  unit = EXCLUDED.unit,
  cert_code = EXCLUDED.cert_code,
  cert_year = EXCLUDED.cert_year,
  cert_issued_at = EXCLUDED.cert_issued_at,
  cert_expires_at = EXCLUDED.cert_expires_at,
  issuing_authority = EXCLUDED.issuing_authority,
  certificate_url = EXCLUDED.certificate_url,
  description = EXCLUDED.description,
  story = EXCLUDED.story,
  ingredients = EXCLUDED.ingredients,
  usage_instructions = EXCLUDED.usage_instructions,
  status = EXCLUDED.status,
  submitted_at = EXCLUDED.submitted_at,
  reviewed_by = EXCLUDED.reviewed_by,
  reviewed_at = EXCLUDED.reviewed_at,
  review_note = EXCLUDED.review_note,
  is_demo = TRUE,
  version = EXCLUDED.version;

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
  'demo/product-images/' || image_data.product_slug || '/' || image_data.image_file,
  'http://localhost:5173/assets/demo/products/' || image_data.image_file,
  products.name,
  TRUE,
  0
FROM (
  VALUES
    ('demo-workflow-tra-atiso-draft', 'artichoke-tea.svg'),
    ('demo-workflow-mut-dau-pending', 'strawberry-jam.svg'),
    ('demo-workflow-ca-phe-revision', 'coffee.svg'),
    ('demo-workflow-hong-treo-gio-approved', 'persimmon.svg'),
    ('demo-workflow-mat-ong-approved', 'honey.svg'),
    ('demo-workflow-rau-ma-rejected', 'artichoke-tea.svg')
) AS image_data(product_slug, image_file)
JOIN ocop_products AS products ON products.slug = image_data.product_slug
WHERE NOT EXISTS (
  SELECT 1
  FROM product_images
  WHERE product_images.product_id = products.id
    AND product_images.is_primary
);

INSERT INTO product_change_requests (
  product_id,
  subject_id,
  request_type,
  proposed_data,
  reason,
  status,
  base_version
)
SELECT
  products.id,
  products.subject_id,
  'update',
  jsonb_build_object(
    'category_id', products.category_id,
    'name', 'Hồng treo gió hộp quà - Đề nghị cập nhật',
    'star', 3,
    'price', '175000',
    'unit', 'hộp 500g',
    'cert_code', products.cert_code,
    'cert_issued_at', '2026-01-15',
    'cert_expires_at', '2029-01-15',
    'issuing_authority', products.issuing_authority,
    'certificate_url', products.certificate_url,
    'vietgap_code', NULL,
    'description', 'Hồng treo gió đóng hộp quà với bao bì mới.',
    'story', products.story,
    'ingredients', products.ingredients,
    'usage_instructions', products.usage_instructions,
    'images', jsonb_build_array(
      jsonb_build_object(
        'image_url', 'http://localhost:5173/assets/demo/products/persimmon.svg',
        'is_primary', TRUE,
        'sort_order', 0
      )
    )
  ),
  '[DEMO] Cập nhật bao bì và giá bán mới.',
  'pending',
  products.version
FROM ocop_products AS products
WHERE products.slug = 'demo-workflow-hong-treo-gio-approved'
  AND NOT EXISTS (
    SELECT 1 FROM product_change_requests
    WHERE product_change_requests.product_id = products.id
      AND product_change_requests.reason = '[DEMO] Cập nhật bao bì và giá bán mới.'
  );

INSERT INTO product_change_requests (
  product_id,
  subject_id,
  request_type,
  proposed_data,
  reason,
  status,
  base_version
)
SELECT
  products.id,
  products.subject_id,
  'delete',
  NULL,
  '[DEMO] Chủ thể đã ngừng kinh doanh sản phẩm.',
  'pending',
  products.version
FROM ocop_products AS products
WHERE products.slug = 'demo-workflow-mat-ong-approved'
  AND NOT EXISTS (
    SELECT 1 FROM product_change_requests
    WHERE product_change_requests.product_id = products.id
      AND product_change_requests.reason = '[DEMO] Chủ thể đã ngừng kinh doanh sản phẩm.'
  );

COMMIT;
