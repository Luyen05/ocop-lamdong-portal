BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE roles (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(255)
);

CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
  email VARCHAR(150) NOT NULL UNIQUE,
  hashed_password VARCHAR(255) NOT NULL,
  full_name VARCHAR(150) NOT NULL,
  phone VARCHAR(20),
  avatar_url VARCHAR(500),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subjects (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  tax_code VARCHAR(50) UNIQUE,
  representative VARCHAR(150) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  email VARCHAR(150),
  address TEXT NOT NULL,
  district VARCHAR(100) NOT NULL,
  geom GEOMETRY(Point, 4326),
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  moderation_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(150) NOT NULL UNIQUE,
  slug VARCHAR(150) NOT NULL UNIQUE,
  description TEXT,
  icon VARCHAR(100)
);

CREATE TABLE ocop_products (
  id BIGSERIAL PRIMARY KEY,
  subject_id BIGINT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  star SMALLINT NOT NULL CHECK (star BETWEEN 3 AND 5),
  price NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (price >= 0),
  unit VARCHAR(50) NOT NULL,
  cert_code VARCHAR(100) UNIQUE,
  cert_year SMALLINT CHECK (cert_year BETWEEN 2000 AND 2100),
  vietgap_code VARCHAR(100),
  description TEXT NOT NULL,
  story TEXT,
  ingredients TEXT,
  usage_instructions TEXT,
  rating_avg NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (rating_avg BETWEEN 0 AND 5),
  views INTEGER NOT NULL DEFAULT 0 CHECK (views >= 0),
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_images (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES ocop_products(id) ON DELETE CASCADE,
  image_url VARCHAR(500) NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  sort_order INTEGER NOT NULL DEFAULT 0 CHECK (sort_order >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tourism_locations (
  id BIGSERIAL PRIMARY KEY,
  subject_id BIGINT REFERENCES subjects(id) ON DELETE SET NULL,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  type VARCHAR(100) NOT NULL,
  district VARCHAR(100) NOT NULL,
  address TEXT NOT NULL,
  geom GEOMETRY(Point, 4326) NOT NULL,
  contact_phone VARCHAR(20),
  opening_hours VARCHAR(100),
  ticket_price NUMERIC(12,2) CHECK (ticket_price >= 0),
  services TEXT[] NOT NULL DEFAULT '{}',
  description TEXT,
  rating_avg NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (rating_avg BETWEEN 0 AND 5),
  views INTEGER NOT NULL DEFAULT 0 CHECK (views >= 0),
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE location_images (
  id BIGSERIAL PRIMARY KEY,
  location_id BIGINT NOT NULL REFERENCES tourism_locations(id) ON DELETE CASCADE,
  image_url VARCHAR(500) NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  sort_order INTEGER NOT NULL DEFAULT 0 CHECK (sort_order >= 0)
);

CREATE TABLE location_ocop_products (
  location_id BIGINT NOT NULL REFERENCES tourism_locations(id) ON DELETE CASCADE,
  product_id BIGINT NOT NULL REFERENCES ocop_products(id) ON DELETE CASCADE,
  PRIMARY KEY (location_id, product_id)
);

CREATE TABLE reviews (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id BIGINT REFERENCES ocop_products(id) ON DELETE CASCADE,
  location_id BIGINT REFERENCES tourism_locations(id) ON DELETE CASCADE,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT review_exactly_one_target CHECK (
    (product_id IS NOT NULL AND location_id IS NULL) OR
    (product_id IS NULL AND location_id IS NOT NULL)
  )
);

CREATE TABLE news (
  id BIGSERIAL PRIMARY KEY,
  author_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  category VARCHAR(100) NOT NULL,
  summary TEXT NOT NULL,
  content TEXT NOT NULL,
  views INTEGER NOT NULL DEFAULT 0 CHECK (views >= 0),
  status VARCHAR(20) NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'published', 'archived')),
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT published_news_has_date CHECK (status <> 'published' OR published_at IS NOT NULL)
);

CREATE TABLE news_images (
  id BIGSERIAL PRIMARY KEY,
  news_id BIGINT NOT NULL REFERENCES news(id) ON DELETE CASCADE,
  image_url VARCHAR(500) NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  sort_order INTEGER NOT NULL DEFAULT 0 CHECK (sort_order >= 0)
);

CREATE INDEX idx_subjects_geom ON subjects USING GIST (geom);
CREATE INDEX idx_tourism_locations_geom ON tourism_locations USING GIST (geom);
CREATE INDEX idx_products_public_filters ON ocop_products (status, category_id, star);
CREATE INDEX idx_locations_public_filters ON tourism_locations (status, district, type);
CREATE INDEX idx_reviews_product_status ON reviews (product_id, status);
CREATE INDEX idx_reviews_location_status ON reviews (location_id, status);
CREATE UNIQUE INDEX uq_product_primary_image ON product_images (product_id) WHERE is_primary;
CREATE UNIQUE INDEX uq_location_primary_image ON location_images (location_id) WHERE is_primary;
CREATE UNIQUE INDEX uq_news_primary_image ON news_images (news_id) WHERE is_primary;
CREATE UNIQUE INDEX uq_review_user_product ON reviews (user_id, product_id) WHERE product_id IS NOT NULL;
CREATE UNIQUE INDEX uq_review_user_location ON reviews (user_id, location_id) WHERE location_id IS NOT NULL;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_subjects_updated_at BEFORE UPDATE ON subjects
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_products_updated_at BEFORE UPDATE ON ocop_products
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_locations_updated_at BEFORE UPDATE ON tourism_locations
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_reviews_updated_at BEFORE UPDATE ON reviews
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_news_updated_at BEFORE UPDATE ON news
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

INSERT INTO roles (name, description) VALUES
  ('admin', 'Quản trị hệ thống'),
  ('subject', 'Chủ thể OCOP hoặc nhà vườn'),
  ('user', 'Du khách/người dùng')
ON CONFLICT (name) DO NOTHING;

COMMIT;
