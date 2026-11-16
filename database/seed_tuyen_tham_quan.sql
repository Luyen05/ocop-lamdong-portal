-- Tuyến tham quan MINH HỌA ghép từ các điểm có sẵn (điểm du lịch, cửa hàng, cơ sở sản xuất).
--
-- CHÚ Ý: đây là gợi ý hành trình do nhóm tạo để trình diễn, chưa kiểm chứng thực địa
-- (thời lượng, thứ tự và ghi chú chặng đều là gợi ý). Tên tuyến ghi rõ "(minh họa)".
-- Chạy lặp lại an toàn. Chạy sau seed_tourism_locations.sql, seed_dalavi_reference.sql, seed_cua_hang_ban_do.sql.
BEGIN;

INSERT INTO tourism_routes (slug, name, description, duration_text, status)
VALUES
  ('hanh-trinh-dau-tay-da-lat', 'Hành trình dâu tây Đà Lạt (minh họa)',
   'Đi từ vườn dâu đến nơi sản xuất và cửa hàng mua dâu tây sấy dẻo OCOP của DaLaVi. Gợi ý của nhóm, chưa kiểm chứng thực địa.',
   'Nửa ngày', 'published'),
  ('hanh-trinh-tra-ca-phe-cau-dat', 'Hành trình trà và cà phê Cầu Đất (minh họa)',
   'Tham quan các đồi chè, vườn cà phê rồi ghé điểm giới thiệu sản phẩm OCOP để mua quà. Gợi ý của nhóm, chưa kiểm chứng thực địa.',
   '1 ngày', 'published')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO tourism_route_stops (route_id, location_id, position, note)
SELECT r.id, l.id, stop.position, stop.note
FROM (VALUES
  ('hanh-trinh-dau-tay-da-lat', 'vuon-dau-tay-co-lien', 1, 'Tham quan vườn dâu, tự tay hái dâu.'),
  ('hanh-trinh-dau-tay-da-lat', 'dalavi-co-so-pang-tieng', 2, 'Nơi sản xuất dâu tây sấy dẻo (liên hệ trước khi đến).'),
  ('hanh-trinh-dau-tay-da-lat', 'dalavi-cua-hang-yersin', 3, 'Mua dâu tây sấy dẻo DaLaVi làm quà.')
) AS stop(route_slug, location_slug, position, note)
JOIN tourism_routes r ON r.slug = stop.route_slug
JOIN tourism_locations l ON l.slug = stop.location_slug
ON CONFLICT DO NOTHING;

INSERT INTO tourism_route_stops (route_id, location_id, position, note)
SELECT r.id, l.id, stop.position, stop.note
FROM (VALUES
  ('hanh-trinh-tra-ca-phe-cau-dat', 'cau-dat-farm', 1, 'Dạo đồi chè Cầu Đất, tìm hiểu cách chế biến trà.'),
  ('hanh-trinh-tra-ca-phe-cau-dat', 'me-linh-coffee-garden', 2, 'Thưởng thức cà phê tại vườn.'),
  ('hanh-trinh-tra-ca-phe-cau-dat', 'diem-ocop-minh-hoa-da-lat', 3, 'Mua sản phẩm OCOP làm quà (điểm minh họa).')
) AS stop(route_slug, location_slug, position, note)
JOIN tourism_routes r ON r.slug = stop.route_slug
JOIN tourism_locations l ON l.slug = stop.location_slug
ON CONFLICT DO NOTHING;

COMMIT;
