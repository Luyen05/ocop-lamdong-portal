-- Allow subjects to save incomplete product drafts and attach a private certificate file.
BEGIN;

ALTER TABLE ocop_products
  ALTER COLUMN star DROP NOT NULL,
  ALTER COLUMN price DROP NOT NULL,
  ALTER COLUMN unit DROP NOT NULL,
  ALTER COLUMN description DROP NOT NULL,
  ADD COLUMN IF NOT EXISTS certificate_storage_path VARCHAR(500);

CREATE UNIQUE INDEX IF NOT EXISTS uq_products_certificate_storage_path
  ON ocop_products (certificate_storage_path)
  WHERE certificate_storage_path IS NOT NULL;

COMMIT;
