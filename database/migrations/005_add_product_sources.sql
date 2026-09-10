BEGIN;

CREATE TABLE IF NOT EXISTS data_sources (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(500) NOT NULL,
  document_number VARCHAR(100),
  issuing_body VARCHAR(255),
  source_type VARCHAR(50) NOT NULL,
  published_at DATE,
  source_url TEXT NOT NULL UNIQUE,
  local_path VARCHAR(500),
  sha256 VARCHAR(64),
  retrieved_at DATE NOT NULL,
  CONSTRAINT data_source_sha256_format CHECK (
    sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$'
  )
);

CREATE TABLE IF NOT EXISTS product_sources (
  product_id BIGINT NOT NULL REFERENCES ocop_products(id) ON DELETE CASCADE,
  source_id BIGINT NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
  verification_level VARCHAR(2) NOT NULL
    CHECK (verification_level IN ('A', 'B1', 'B2', 'C')),
  original_address TEXT,
  evidence_role VARCHAR(30) NOT NULL
    CHECK (evidence_role IN ('recognition', 'identity', 'address', 'enrichment')),
  verified_at DATE NOT NULL,
  notes TEXT,
  PRIMARY KEY (product_id, source_id, evidence_role)
);

CREATE INDEX IF NOT EXISTS idx_product_sources_source
  ON product_sources (source_id);

COMMIT;
