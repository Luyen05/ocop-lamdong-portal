# ERD — Cổng thông tin OCOP Lâm Đồng

```mermaid
erDiagram
  roles ||--o{ users : assigns
  users ||--o| subjects : applies
  users ||--o{ reviews : writes
  users ||--o{ news : authors
  subjects ||--o{ ocop_products : owns
  subjects ||--o{ tourism_locations : owns
  categories ||--o{ ocop_products : classifies
  ocop_products ||--o{ product_images : has
  tourism_locations ||--o{ location_images : has
  ocop_products ||--o{ location_ocop_products : appears_at
  tourism_locations ||--o{ location_ocop_products : features
  ocop_products ||--o{ reviews : receives
  tourism_locations ||--o{ reviews : receives
  news ||--o{ news_images : has
```

Các cột `geom` sử dụng `GEOMETRY(Point,4326)`. Bảng `reviews` bắt buộc đúng một trong
`product_id` hoặc `location_id`. Mỗi nhóm ảnh chỉ có tối đa một ảnh chính nhờ partial
unique index.

Hồ sơ `subjects` đồng thời là hồ sơ đăng ký chủ thể. Trường `status` biểu diễn
quy trình `pending → approved/rejected`; `moderation_note` lưu phản hồi của quản trị
viên khi xét duyệt.
