BEGIN;

CREATE INDEX IF NOT EXISTS idx_ocop_products_search
  ON ocop_products
  USING GIN (
    to_tsvector(
      'simple',
      concat_ws(
        ' ',
        name,
        description,
        story,
        ingredients,
        usage_instructions
      )
    )
  );

COMMIT;