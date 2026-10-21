-- Apply this once to databases created before the public product API.
BEGIN;

ALTER TABLE ocop_products
  ADD COLUMN IF NOT EXISTS rating_avg NUMERIC(3, 2) NOT NULL DEFAULT 0
  CHECK (rating_avg BETWEEN 0 AND 5);

COMMIT;
