BEGIN;

ALTER TABLE ocop_products
  ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE ocop_products AS products
SET is_demo = TRUE
WHERE products.slug LIKE 'demo-workflow-%'
   OR products.cert_code LIKE 'DEMO-OCOP-%'
   OR products.subject_id IN (
     SELECT subjects.id
     FROM subjects
     JOIN users ON users.id = subjects.user_id
     WHERE users.email IN (
       'demo-subject@local.invalid',
       'chuthe.ocop.demo@example.com'
     )
   );

CREATE INDEX IF NOT EXISTS idx_products_public_visibility
  ON ocop_products (status, is_demo, category_id, star);

COMMIT;
