-- Chuẩn bị cho chức năng chủ thể khai báo điểm du lịch (API /subject/locations) và admin duyệt.
-- - Bản nháp được lưu dần theo từng phần của biểu mẫu, nên vị trí, xã/phường và địa chỉ có thể
--   còn trống khi đang soạn (draft) hoặc đang bổ sung (needs_revision). Các trạng thái còn lại
--   (chờ duyệt, đã duyệt, từ chối, ngừng hiển thị) bắt buộc đủ ba thông tin này.
-- - Thêm trạng thái archived: điểm đã duyệt được ngừng hiển thị khi admin duyệt yêu cầu của chủ thể.
-- Không đổi dữ liệu đang có. Chạy lặp lại an toàn.
BEGIN;

ALTER TABLE tourism_locations
  ALTER COLUMN geom DROP NOT NULL,
  ALTER COLUMN district DROP NOT NULL,
  ALTER COLUMN address DROP NOT NULL;

ALTER TABLE tourism_locations
  DROP CONSTRAINT IF EXISTS tourism_locations_status_check,
  DROP CONSTRAINT IF EXISTS tourism_locations_required_fields_check;

ALTER TABLE tourism_locations
  ADD CONSTRAINT tourism_locations_status_check CHECK (
    status IN ('draft', 'pending', 'needs_revision', 'approved', 'rejected', 'archived')
  ),
  ADD CONSTRAINT tourism_locations_required_fields_check CHECK (
    status IN ('draft', 'needs_revision')
    OR (geom IS NOT NULL AND district IS NOT NULL AND address IS NOT NULL)
  );

COMMIT;
