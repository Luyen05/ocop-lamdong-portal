-- Official external media only. storage_path is an external identity key,
-- consistent with ProductImage's external/product-images namespace, not a file.
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM ocop_products p JOIN subjects s ON s.id=p.subject_id
      JOIN users u ON u.id=s.user_id WHERE p.slug='tham-khao-ca-phe-dehavi-valley'
      AND u.email='public-reference-han-vinh@local.invalid')
    OR NOT EXISTS (SELECT 1 FROM tourism_locations l JOIN subjects s ON s.id=l.subject_id
      JOIN users u ON u.id=s.user_id WHERE l.slug='dehavi-showroom'
      AND u.email='public-reference-han-vinh@local.invalid') THEN
    RAISE EXCEPTION 'Dehavi media target missing or ownership conflict';
  END IF;
END $$;

INSERT INTO product_images
  (product_id,storage_path,image_url,alt_text,is_primary,sort_order,source_url,credit,license)
SELECT id,'external/product-images/dehavi/valley-500gr',
  'https://bizweb.dktcdn.net/100/513/603/products/valley-500gr-7ea7f8df-b79b-4821-9e0e-ecf3b1a1ba20.png?v=1716091443340',
  'Dehavi Valley 500gr',TRUE,0,'https://dehavi.com/valley',
  'Dehavi Coffee / Công ty TNHH Cà phê Hân Vinh',NULL
FROM ocop_products WHERE slug='tham-khao-ca-phe-dehavi-valley'
ON CONFLICT (storage_path) DO NOTHING;

INSERT INTO location_images
  (location_id,image_url,alt_text,is_primary,sort_order,source_url,credit,license)
SELECT id,'https://bizweb.dktcdn.net/100/513/603/products/5.jpg?v=1716720667660',
  'Dehavi Showroom',TRUE,0,'https://dehavi.com/cup-dehavi-showroom',
  'Dehavi Coffee / Công ty TNHH Cà phê Hân Vinh',NULL
FROM tourism_locations l WHERE slug='dehavi-showroom'
AND NOT EXISTS (SELECT 1 FROM location_images i WHERE i.location_id=l.id
  AND i.image_url='https://bizweb.dktcdn.net/100/513/603/products/5.jpg?v=1716720667660');

UPDATE tourism_locations SET opening_hours='06:30–17:30'
WHERE slug='dehavi-showroom' AND opening_hours IS DISTINCT FROM '06:30–17:30';

DO $$
BEGIN
  IF (SELECT count(*) FROM product_images i JOIN ocop_products p ON p.id=i.product_id
      WHERE p.slug='tham-khao-ca-phe-dehavi-valley' AND i.is_primary) <> 1
    OR (SELECT count(*) FROM location_images i JOIN tourism_locations l ON l.id=i.location_id
      WHERE l.slug='dehavi-showroom' AND i.is_primary) <> 1 THEN
    RAISE EXCEPTION 'Dehavi media primary image conflict';
  END IF;
END $$;
COMMIT;
