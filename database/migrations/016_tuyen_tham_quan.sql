-- Tuyến tham quan: chuỗi các điểm (điểm du lịch, cửa hàng) theo thứ tự, có ghi chú từng chặng.
--
-- - tourism_routes: tuyến (slug, tên, mô tả, thời lượng gợi ý). Chỉ tuyến 'published' hiện công khai.
-- - tourism_route_stops: các chặng theo thứ tự (position bắt đầu từ 1). Xóa điểm thì chặng tự mất.
-- Chạy trong một transaction, chạy lặp lại an toàn. Database tạo mới từ schema.sql không cần chạy file này.
-- Sau khi chạy, mở tools/kiem-tra-database.sql trong pgAdmin: kết quả rỗng là khớp repo.
BEGIN;

CREATE TABLE IF NOT EXISTS tourism_routes (
  id BIGSERIAL PRIMARY KEY,
  slug VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  duration_text VARCHAR(100),
  status VARCHAR(20) NOT NULL DEFAULT 'draft'
    CONSTRAINT tourism_routes_status_check CHECK (status IN ('draft', 'published', 'archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tourism_route_stops (
  route_id BIGINT NOT NULL REFERENCES tourism_routes(id) ON DELETE CASCADE,
  location_id BIGINT NOT NULL REFERENCES tourism_locations(id) ON DELETE CASCADE,
  position SMALLINT NOT NULL CONSTRAINT tourism_route_stops_position_check CHECK (position >= 1),
  note TEXT,
  PRIMARY KEY (route_id, location_id),
  CONSTRAINT uq_tourism_route_stops_position UNIQUE (route_id, position)
);

CREATE INDEX IF NOT EXISTS idx_tourism_route_stops_location
  ON tourism_route_stops (location_id);

COMMIT;
