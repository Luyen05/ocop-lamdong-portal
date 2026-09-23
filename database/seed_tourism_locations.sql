-- Dữ liệu tham khảo điểm du lịch nông nghiệp tỉnh Lâm Đồng.
-- Sinh tự động bằng tools/build_tourism_seed.py từ
-- data/tourism/diem_du_lich_nong_nghiep_2026.csv ngày 2026-09-23.
-- Tọa độ, địa chỉ và giờ mở cửa lấy từ trang địa điểm công khai ghi ở cột
-- source_url; đây KHÔNG phải dữ liệu hành chính chính thức và có thể đã thay đổi.
-- Chạy lặp lại an toàn: cập nhật thông tin theo slug nhưng giữ nguyên trạng thái
-- kiểm duyệt, điểm đánh giá và lượt xem đang có trong cơ sở dữ liệu.
-- Yêu cầu schema có cột website/source_url (database/migrations/008).

BEGIN;

INSERT INTO tourism_locations (
  name, slug, type, district, address, geom, contact_phone, opening_hours,
  ticket_price, services, description, website, source_url, status
)
VALUES
  (
    'Cầu Đất Farm - Đồi chè Cầu Đất',
    'cau-dat-farm',
    'tea_coffee_farm',
    'Đà Lạt',
    'Thôn Xuân Trường, khu vực Cầu Đất, Đà Lạt, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(108.5473980, 11.8795830), 4326),
    NULL,
    '07:00 - 19:00',
    30000,
    ARRAY['Tham quan đồi chè', 'Tìm hiểu chế biến trà', 'Cà phê và ẩm thực', 'Chụp ảnh']::TEXT[],
    'Đồi chè và vườn cà phê lâu năm ở vùng Cầu Đất, phía đông nam trung tâm Đà Lạt. Du khách có thể dạo đồi chè, tìm hiểu quy trình chế biến trà và ngắm cảnh cao nguyên.',
    NULL,
    'https://www.foody.vn/lam-dong/doi-che-cau-dat',
    'approved'
  ),
  (
    'Mê Linh Coffee Garden',
    'me-linh-coffee-garden',
    'tea_coffee_farm',
    'Đà Lạt',
    'Tỉnh lộ 725, khu vực Tà Nung, Đà Lạt, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(108.3479746, 11.8996136), 4326),
    NULL,
    '07:00 - 22:00',
    NULL,
    ARRAY['Tham quan vườn cà phê', 'Thưởng thức cà phê tại vườn', 'Chụp ảnh']::TEXT[],
    'Vườn cà phê trên sườn đồi khu vực Tà Nung, có tầm nhìn ra thung lũng. Du khách có thể tìm hiểu cây cà phê và thưởng thức cà phê ngay tại vườn.',
    NULL,
    'https://www.foody.vn/lam-dong/me-linh-cafe',
    'approved'
  ),
  (
    'Nông trại Dalat Milk',
    'nong-trai-dalat-milk',
    'dairy_farm',
    'Đơn Dương',
    'Xã Tu Tra, Đơn Dương, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(108.4377250, 11.7397710), 4326),
    NULL,
    'Cả ngày',
    0,
    ARRAY['Tham quan đồng cỏ', 'Chụp ảnh', 'Mua sản phẩm từ sữa']::TEXT[],
    'Nông trại chăn nuôi bò sữa với đồng cỏ và cảnh quan rộng. Khách có thể tham quan, chụp ảnh và mua các sản phẩm từ sữa tại chỗ.',
    NULL,
    'https://www.foody.vn/lam-dong/nong-trai-dalat-milk',
    'approved'
  ),
  (
    'Đồi chè Tâm Châu',
    'doi-che-tam-chau',
    'tea_coffee_farm',
    'Bảo Lâm',
    'Xã Lộc Tân, Bảo Lâm, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(107.7427220, 11.5952860), 4326),
    NULL,
    'Cả ngày',
    NULL,
    ARRAY['Tham quan đồi chè', 'Chụp ảnh', 'Mua trà đặc sản']::TEXT[],
    'Đồi chè rộng thuộc vùng chè Bảo Lâm - Bảo Lộc, một trong những vùng trồng chè lớn của Lâm Đồng. Điểm dừng chân tham quan, chụp ảnh và tìm hiểu cây chè.',
    NULL,
    'https://www.foody.vn/lam-dong/doi-che-tam-chau',
    'approved'
  ),
  (
    'Vườn dâu Chào Đà Lạt',
    'vuon-dau-chao-da-lat',
    'fruit_garden',
    'Lạc Dương',
    'Tỉnh lộ 723, Lạc Dương, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(108.5861740, 12.1120130), 4326),
    NULL,
    '09:00 - 21:00',
    NULL,
    ARRAY['Tham quan vườn dâu', 'Tự tay hái dâu', 'Chụp ảnh']::TEXT[],
    'Vườn dâu tây phục vụ khách tham quan và tự tay hái dâu, nằm trên tuyến tỉnh lộ 723 thuộc khu vực Lạc Dương.',
    NULL,
    'https://www.foody.vn/lam-dong/vuon-dau-chao-da-lat',
    'approved'
  ),
  (
    'Vườn dâu tây Cô Liên',
    'vuon-dau-tay-co-lien',
    'fruit_garden',
    'Đà Lạt',
    '87 Tô Vĩnh Diện, Phường 7, Đà Lạt, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(108.4234086, 11.9588343), 4326),
    NULL,
    '06:00 - 17:00',
    NULL,
    ARRAY['Tham quan vườn dâu', 'Tự tay hái dâu', 'Mua dâu tươi']::TEXT[],
    'Vườn dâu tây trong khu dân cư phía bắc Đà Lạt, khách có thể tham quan và hái dâu tại vườn.',
    NULL,
    'https://www.foody.vn/lam-dong/vuon-dau-tay-co-lien',
    'approved'
  ),
  (
    'Vườn hồng Nhà Tom',
    'vuon-hong-nha-tom',
    'fruit_garden',
    'Đà Lạt',
    '86 Khe Sanh, Phường 10, Đà Lạt, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(108.4589400, 11.9321060), 4326),
    '0943268138',
    '08:00 - 17:00',
    NULL,
    ARRAY['Tham quan vườn hồng', 'Chụp ảnh', 'Mua hồng treo gió']::TEXT[],
    'Vườn hồng gắn với mùa hồng và đặc sản hồng treo gió của Đà Lạt, phục vụ khách tham quan và chụp ảnh.',
    NULL,
    'https://www.foody.vn/lam-dong/vuon-hong-nha-tom',
    'approved'
  ),
  (
    'Vườn hoa Cẩm Tú Cầu',
    'cam-tu-cau-garden',
    'flower_garden',
    'Đà Lạt',
    'Tổ 1, thôn Lộc Quý, xã Xuân Thọ, Đà Lạt, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(108.5113170, 11.9454810), 4326),
    NULL,
    '07:00 - 17:00',
    NULL,
    ARRAY['Tham quan vườn hoa', 'Chụp ảnh']::TEXT[],
    'Vườn hoa cẩm tú cầu ở khu vực Xuân Thọ, phía đông Đà Lạt, thu hút khách tham quan và chụp ảnh.',
    NULL,
    'https://www.foody.vn/lam-dong/cam-tu-cau-garden',
    'approved'
  ),
  (
    'Cánh đồng Lavender hồ Tuyền Lâm',
    'canh-dong-lavender-ho-tuyen-lam',
    'flower_garden',
    'Đà Lạt',
    'Khu du lịch hồ Tuyền Lâm, Đà Lạt, Lâm Đồng',
    ST_SetSRID(ST_MakePoint(108.4196380, 11.8958760), 4326),
    NULL,
    '07:00 - 17:00',
    40000,
    ARRAY['Ngắm hoa oải hương', 'Chụp ảnh', 'Đồ uống']::TEXT[],
    'Cánh đồng hoa oải hương ven khu vực hồ Tuyền Lâm, có không gian ngắm hoa và phục vụ đồ uống.',
    NULL,
    'https://www.foody.vn/lam-dong/canh-dong-lavender-ho-tuyen-lam',
    'approved'
  )
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  type = EXCLUDED.type,
  district = EXCLUDED.district,
  address = EXCLUDED.address,
  geom = EXCLUDED.geom,
  contact_phone = EXCLUDED.contact_phone,
  opening_hours = EXCLUDED.opening_hours,
  ticket_price = EXCLUDED.ticket_price,
  services = EXCLUDED.services,
  description = EXCLUDED.description,
  website = EXCLUDED.website,
  source_url = EXCLUDED.source_url;

COMMIT;
