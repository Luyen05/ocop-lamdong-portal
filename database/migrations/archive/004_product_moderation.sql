-- Add the product publication workflow to an existing database.
BEGIN;

ALTER TABLE ocop_products
  ADD COLUMN IF NOT EXISTS cert_issued_at DATE,
  ADD COLUMN IF NOT EXISTS cert_expires_at DATE,
  ADD COLUMN IF NOT EXISTS issuing_authority VARCHAR(255),
  ADD COLUMN IF NOT EXISTS certificate_url VARCHAR(500),
  ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS reviewed_by BIGINT REFERENCES users(id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS review_note TEXT,
  ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

ALTER TABLE ocop_products
  ALTER COLUMN status SET DEFAULT 'draft',
  DROP CONSTRAINT IF EXISTS ocop_products_status_check,
  DROP CONSTRAINT IF EXISTS ck_product_status,
  DROP CONSTRAINT IF EXISTS ck_ocop_products_status,
  DROP CONSTRAINT IF EXISTS ck_ocop_products_review_state,
  DROP CONSTRAINT IF EXISTS product_certificate_dates;

ALTER TABLE ocop_products
  ADD CONSTRAINT ocop_products_status_check CHECK (
    status IN (
      'draft',
      'pending',
      'needs_revision',
      'approved',
      'rejected',
      'suspended',
      'archived'
    )
  ),
  ADD CONSTRAINT product_certificate_dates CHECK (
    cert_issued_at IS NULL OR cert_expires_at IS NULL OR cert_expires_at > cert_issued_at
  );

ALTER TABLE product_images
  ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500),
  ADD COLUMN IF NOT EXISTS alt_text VARCHAR(255);

UPDATE product_images
SET storage_path = 'legacy/product-images/' || id
WHERE storage_path IS NULL OR BTRIM(storage_path) = '';

ALTER TABLE product_images
  ALTER COLUMN storage_path SET NOT NULL,
  ALTER COLUMN image_url TYPE VARCHAR(1000);

CREATE UNIQUE INDEX IF NOT EXISTS uq_product_images_storage_path
  ON product_images (storage_path);

CREATE TABLE IF NOT EXISTS product_change_requests (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES ocop_products(id) ON DELETE CASCADE,
  subject_id BIGINT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('update', 'delete')),
  proposed_data JSONB,
  reason TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'needs_revision', 'approved', 'rejected', 'cancelled')),
  base_version INTEGER NOT NULL CHECK (base_version >= 1),
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_by BIGINT REFERENCES users(id) ON DELETE RESTRICT,
  reviewed_at TIMESTAMPTZ,
  review_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT product_change_payload CHECK (
    (request_type = 'update' AND proposed_data IS NOT NULL)
    OR (request_type = 'delete' AND proposed_data IS NULL)
  )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_product_active_change_request
  ON product_change_requests (product_id)
  WHERE status IN ('pending', 'needs_revision');

DROP TRIGGER IF EXISTS trg_product_change_requests_updated_at ON product_change_requests;
CREATE TRIGGER trg_product_change_requests_updated_at
BEFORE UPDATE ON product_change_requests
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
