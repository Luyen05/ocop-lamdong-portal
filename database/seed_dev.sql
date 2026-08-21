-- Optional starter categories for local development/demo.
INSERT INTO categories (name, slug, description, icon) VALUES
  ('Thực phẩm', 'thuc-pham', 'Sản phẩm thực phẩm OCOP', 'bi-basket'),
  ('Đồ uống', 'do-uong', 'Trà, cà phê, nước ép và đồ uống', 'bi-cup-straw'),
  ('Thảo dược', 'thao-duoc', 'Sản phẩm từ dược liệu địa phương', 'bi-flower1'),
  ('Thủ công mỹ nghệ', 'thu-cong-my-nghe', 'Sản phẩm thủ công và quà tặng', 'bi-palette'),
  ('Sinh vật cảnh', 'sinh-vat-canh', 'Hoa, cây cảnh và sản phẩm trang trí', 'bi-tree'),
  ('Dịch vụ du lịch cộng đồng', 'dich-vu-du-lich-cong-dong', 'Dịch vụ gắn với nông nghiệp và cộng đồng', 'bi-geo-alt')
ON CONFLICT (slug) DO NOTHING;

