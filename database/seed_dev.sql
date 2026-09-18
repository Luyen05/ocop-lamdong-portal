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


-- Published demo news uses the existing disabled reviewer; no login account is added.
-- Images are omitted so the public API can return primary_image_url = null.
INSERT INTO news (
  author_id, title, slug, category, summary, content, views, status, published_at
)
SELECT
  users.id,
  demo.title,
  demo.slug,
  demo.category,
  demo.summary,
  demo.content,
  demo.views,
  'published',
  demo.published_at
FROM users
CROSS JOIN (
  VALUES
    (
      'Chủ thể OCOP Lâm Đồng chú trọng hoàn thiện hồ sơ sản phẩm',
      'hoan-thien-ho-so-san-pham-ocop-lam-dong-demo',
      'Chính sách',
      'Chuẩn hóa thông tin sản phẩm, nguồn nguyên liệu và câu chuyện địa phương giúp chủ thể chuẩn bị hồ sơ OCOP rõ ràng hơn.',
      E'Trong tình huống minh họa của cổng OCOP Lâm Đồng, một hợp tác xã rà soát hồ sơ cà phê, trà atiso và sản phẩm chế biến từ nông sản trước khi đăng ký đánh giá. Thông tin được tập hợp theo từng sản phẩm để thuận tiện đối chiếu.\n\nChủ thể chú trọng mô tả nguồn nguyên liệu, quy trình sản xuất, nhãn hàng hóa và tài liệu liên quan đến chất lượng. Câu chuyện sản phẩm giới thiệu người làm nghề và đặc trưng địa phương bằng thông tin có thể kiểm chứng.\n\nĐây là bài viết dữ liệu mẫu phục vụ trình diễn, không phải thông báo chính sách hoặc hướng dẫn thủ tục chính thức. Chủ thể cần tra cứu hướng dẫn hiện hành từ cơ quan phụ trách khi chuẩn bị hồ sơ thực tế.',
      128,
      TIMESTAMPTZ '2026-08-05 09:00:00+07'
    ),
    (
      'Không gian trải nghiệm giới thiệu hương vị OCOP Lâm Đồng',
      'khong-gian-trai-nghiem-huong-vi-ocop-lam-dong-demo',
      'Sự kiện',
      'Cà phê Cầu Đất, trà atiso và mứt dâu được giới thiệu trong không gian kết nối chủ thể với người tiêu dùng.',
      E'Không gian trải nghiệm trong kịch bản demo mang đến một hành trình khám phá nông sản Lâm Đồng qua các gian giới thiệu cà phê, trà và sản phẩm từ trái cây. Khách tham quan có thể tìm hiểu cách chế biến và câu chuyện của từng chủ thể.\n\nKhu vực dùng thử giúp người tiêu dùng so sánh hương vị, trao đổi về cách sử dụng và lựa chọn quà tặng phù hợp. Các gian hàng trình bày rõ thành phần, khối lượng và hướng dẫn bảo quản để khách dễ tham khảo.\n\nBài viết mô phỏng hoạt động giới thiệu sản phẩm phục vụ trình diễn cổng thông tin; không công bố lịch tổ chức hoặc địa điểm của một sự kiện thực tế.',
      246,
      TIMESTAMPTZ '2026-08-12 08:30:00+07'
    ),
    (
      'Kể câu chuyện nông sản để kết nối sản phẩm OCOP với khách hàng',
      'ket-noi-san-pham-ocop-voi-khach-hang-demo',
      'Xúc tiến thương mại',
      'Thông tin rõ ràng và câu chuyện vùng nguyên liệu giúp sản phẩm địa phương tiếp cận khách hàng qua các kênh giới thiệu trực tuyến.',
      E'Trong kịch bản xúc tiến thương mại mẫu, hợp tác xã giới thiệu bộ sản phẩm quà tặng gồm cà phê Arabica, mứt dâu và trà atiso. Mỗi sản phẩm có phần mô tả riêng về hương vị, nguồn nguyên liệu và cách sử dụng.\n\nKhi giới thiệu trực tuyến, chủ thể chuẩn bị nội dung dễ đọc, thông tin quy cách đóng gói và kênh liên hệ để khách hàng có thể trao đổi nhu cầu. Phản hồi của người mua được dùng để cải thiện cách trình bày và dịch vụ.\n\nNội dung này là dữ liệu minh họa cho chuyên mục xúc tiến thương mại, không xác nhận hợp đồng, doanh số hoặc chương trình hỗ trợ thực tế.',
      183,
      TIMESTAMPTZ '2026-08-19 10:00:00+07'
    ),
    (
      'Khám phá nông nghiệp Đà Lạt qua trải nghiệm vườn và sản phẩm địa phương',
      'trai-nghiem-vuon-va-san-pham-da-lat-demo',
      'Du lịch nông nghiệp',
      'Kết hợp tìm hiểu canh tác, thưởng thức nông sản và lựa chọn quà địa phương tạo nên hành trình trải nghiệm gần gũi với nhà vườn.',
      E'Hành trình du lịch nông nghiệp trong dữ liệu demo gợi mở trải nghiệm tìm hiểu vườn dâu và câu chuyện cà phê của vùng cao nguyên. Du khách được giới thiệu công việc chăm sóc cây trồng, thu hoạch và chế biến nông sản.\n\nHoạt động trải nghiệm cần được sắp xếp cùng nhà vườn, phù hợp điều kiện thời tiết và mùa vụ. Khách tham quan tôn trọng khu vực sản xuất, giữ vệ sinh và làm theo hướng dẫn của người phụ trách.\n\nCác sản phẩm địa phương như mứt dâu, cà phê và hồng treo gió có thể trở thành quà tặng gắn với câu chuyện chuyến đi. Bài viết phục vụ trình diễn, không đại diện cho tour đang mở bán hoặc cam kết dịch vụ của một cơ sở cụ thể.',
      312,
      TIMESTAMPTZ '2026-08-26 14:00:00+07'
    )
) AS demo(title, slug, category, summary, content, views, published_at)
WHERE users.email = 'demo-reviewer@local.invalid'
ON CONFLICT (slug) DO NOTHING;
