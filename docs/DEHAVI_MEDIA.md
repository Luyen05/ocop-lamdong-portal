# Dehavi official media

Applied locally on 2026-10-07 using only `database/seed_dehavi_media.sql`.
External keys in `product_images.storage_path` identify external records;
they do not refer to an uploaded file or Cloudinary asset.

## Official candidates

Valley source: https://dehavi.com/valley
All seven full-size gallery images have HTML width/height 540/540 and alt `VALLEY`.
The 112/112 thumbnails, logos, icons, related-product and blog images are excluded.

- https://bizweb.dktcdn.net/100/513/603/products/valley-500gr-7ea7f8df-b79b-4821-9e0e-ecf3b1a1ba20.png?v=1716091443340
- https://bizweb.dktcdn.net/100/513/603/products/54-c9a9275b-ef98-4ae2-95d5-fafe60e26f1a.png?v=1716091443340
- https://bizweb.dktcdn.net/100/513/603/products/sa-n-pha-m-bbef67a4-2776-4b74-8d9b-8e1d6da21ab6-3ad660a0-c9d2-4eb1-a2d2-e8264c48bebe.png?v=1716091443340
- https://bizweb.dktcdn.net/100/513/603/products/4-a0118223-6170-476f-8587-8e54a5c2aa8d-5b1c6f16-f961-491d-9f0f-d1cbeb1606b4.png?v=1716091443340
- https://bizweb.dktcdn.net/100/513/603/products/61-f010b99e-4bb0-441a-8e8a-6aeb372e36a9-e041b2a1-4228-4b1c-aa08-5edf9b0d9e6c.png?v=1716091443340
- https://bizweb.dktcdn.net/100/513/603/products/3-4c284c82-1399-43d4-af52-029f0ccc6800.png?v=1753331615603
- https://bizweb.dktcdn.net/100/513/603/products/mu-c-rang-8c3c4335-16fc-4618-b082-591d70598938.png?v=1753331616503

Showroom source: https://dehavi.com/cup-dehavi-showroom
One full-size gallery image, HTML width/height 540/540, alt `Dehavi Showroom`:

- https://bizweb.dktcdn.net/100/513/603/products/5.jpg?v=1716720667660

## Selection and verification

Selected the first Valley image (500gr product packaging) and the identified
Showroom image. Each is primary with sort_order 0; no additional candidate is seeded.
GET checks: Valley HTTP 200, image/png, 711286 bytes; Showroom HTTP 200,
image/jpeg, 270142 bytes. Dimensions above are HTML attributes, not decoded pixel sizes.
Both use their official source page and credit
`Dehavi Coffee / Công ty TNHH Cà phê Hân Vinh`; unknown license remains NULL.
Showroom opening_hours uses the schema's free-text convention: `06:30–17:30`.

## Local runtime evidence

Before: no images for either target. After: one primary each, product image id 61,
location image id 1. Snapshot comparison of every public business table outside
target media and showroom row passed. Product and Location detail APIs returned
the external URLs, sources, credit and NULL license.

Fresh custom-format backup:
`D:\DaiHocDL\DoAnChuyenNganh\db-backups\dehavi-media-before-20261007-145459.dump`.
`pg_restore --list` passed before export and after copying back under another name.

The disposable PostGIS test runs the real schema, base Dehavi seed and media seed,
then reruns media seed and checks API serialization and unrelated rows.
Use the isolated test mechanism documented in DEHAVI_DEMO_DATA.md and pass
`tests/test_dehavi_media_seed.py`; all Docker commands must use the explicit
DockerDesktop executable through `& $docker` in PowerShell.

ProductDetailView, ProductExperienceView and LocationDetailView pass detail images
to PresentationGallery, which renders external URLs and attribution. Browser
runtime reported no browser available (empty discovery list):
`[NEEDS_MANUAL_SCREENSHOT_CHECK]`.
