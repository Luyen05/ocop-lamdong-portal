-- Apply this once in pgAdmin to an existing database created before schema.sql
-- was committed. The transaction rolls back if duplicate reviews or multiple
-- primary images violate the new unique indexes; clean those rows, then retry.
BEGIN;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'review_exactly_one_target') THEN
    ALTER TABLE reviews ADD CONSTRAINT review_exactly_one_target CHECK (
      (product_id IS NOT NULL AND location_id IS NULL) OR
      (product_id IS NULL AND location_id IS NOT NULL)
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_subject_status') THEN
    ALTER TABLE subjects ADD CONSTRAINT ck_subject_status CHECK (status IN ('pending','approved','rejected'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_product_status') THEN
    ALTER TABLE ocop_products ADD CONSTRAINT ck_product_status CHECK (status IN ('pending','approved','rejected'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_location_status') THEN
    ALTER TABLE tourism_locations ADD CONSTRAINT ck_location_status CHECK (status IN ('pending','approved','rejected'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_review_status') THEN
    ALTER TABLE reviews ADD CONSTRAINT ck_review_status CHECK (status IN ('pending','approved','rejected'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_news_status') THEN
    ALTER TABLE news ADD CONSTRAINT ck_news_status CHECK (status IN ('draft','published','archived'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_subjects_geom ON subjects USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_tourism_locations_geom ON tourism_locations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_products_public_filters ON ocop_products (status, category_id, star);
CREATE INDEX IF NOT EXISTS idx_locations_public_filters ON tourism_locations (status, district, type);
CREATE INDEX IF NOT EXISTS idx_reviews_product_status ON reviews (product_id, status);
CREATE INDEX IF NOT EXISTS idx_reviews_location_status ON reviews (location_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS uq_product_primary_image ON product_images (product_id) WHERE is_primary;
CREATE UNIQUE INDEX IF NOT EXISTS uq_location_primary_image ON location_images (location_id) WHERE is_primary;
CREATE UNIQUE INDEX IF NOT EXISTS uq_news_primary_image ON news_images (news_id) WHERE is_primary;
CREATE UNIQUE INDEX IF NOT EXISTS uq_review_user_product ON reviews (user_id, product_id) WHERE product_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_review_user_location ON reviews (user_id, location_id) WHERE location_id IS NOT NULL;

CREATE OR REPLACE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_subjects_updated_at BEFORE UPDATE ON subjects
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_products_updated_at BEFORE UPDATE ON ocop_products
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_locations_updated_at BEFORE UPDATE ON tourism_locations
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_reviews_updated_at BEFORE UPDATE ON reviews
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE TRIGGER trg_news_updated_at BEFORE UPDATE ON news
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;

