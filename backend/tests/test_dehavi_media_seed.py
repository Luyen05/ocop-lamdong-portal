"""Media integration checks using the existing disposable PostGIS fixture."""
import os
from pathlib import Path

from test_dehavi_seed import seeded_dehavi, PRODUCT, LOCATION


def test_official_media_seed_and_api(seeded_dehavi):
    client, db, _ = seeded_dehavi
    sql_dir = Path(os.environ.get('DEHAVI_SEED_SQL_DIR', Path(__file__).resolve().parents[2] / 'database'))
    seed = (sql_dir / 'seed_dehavi_media.sql').read_text(encoding='utf-8')
    tables = ('users', 'subjects', 'categories', 'ocop_products', 'tourism_locations',
              'data_sources', 'product_sources', 'location_ocop_products',
              'product_images', 'location_images')
    before = {t: dict(db.execute(f'SELECT id,row_to_json(t)::text FROM {t} t').fetchall())
              for t in tables if t not in ('product_sources', 'location_ocop_products')}
    links = {t: db.execute(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY 1').fetchall()
             for t in ('product_sources', 'location_ocop_products')}
    target = db.execute('SELECT id FROM tourism_locations WHERE slug=%s', (LOCATION,)).fetchone()[0]
    for attempt in range(2):
        db.execute(seed, prepare=False)
        for table, rows in before.items():
            current = dict(db.execute(f'SELECT id,row_to_json(t)::text FROM {table} t').fetchall())
            for key, value in rows.items():
                if table == 'tourism_locations' and key == target:
                    continue
                assert current[key] == value, table
        for table, rows in links.items():
            assert db.execute(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY 1').fetchall() == rows
        for endpoint, slug, page in [('products', PRODUCT, 'valley'), ('locations', LOCATION, 'cup-dehavi-showroom')]:
            response = client.get(f'/api/v1/{endpoint}/{slug}')
            assert response.status_code == 200
            images = response.json()['images']
            assert len(images) == 1
            assert sum(i['is_primary'] for i in images) == 1
            assert images[0]['image_url'].startswith('https://bizweb.dktcdn.net/')
            assert images[0]['source_url'] == f'https://dehavi.com/{page}'
            assert images[0]['credit'] == 'Dehavi Coffee / Công ty TNHH Cà phê Hân Vinh'
            assert images[0]['license'] is None
        assert client.get(f'/api/v1/locations/{LOCATION}').json()['opening_hours'] == '06:30–17:30'
        counts = [db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ('product_images', 'location_images')]
        if attempt == 0:
            initial_counts = counts
        else:
            assert counts == initial_counts
