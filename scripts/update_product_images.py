"""
Update product image URLs using picsum.photos (random but stable) and unsplash.
These are real, working image CDN services.
"""
import pymysql

# 关键字到 unsplash 搜索词的映射 (得到主题相关的真实图片)
CATEGORY_THEMES = {
    'phone': 'smartphone',
    'iphone': 'iphone',
    'macbook': 'macbook',
    'laptop': 'laptop',
    'watch': 'smartwatch',
    'headphone': 'headphones',
    'speaker': 'speaker',
    'tablet': 'tablet',
    'tv': 'television',
    'camera': 'camera',
    'router': 'router',
    'monitor': 'monitor',
    'keyboard': 'keyboard',
    'mouse': 'mouse',
    'hub': 'usb-hub',
    'cable': 'cable',
    'case': 'phone-case',
    'game': 'gaming',
    'ssd': 'ssd',
    'charge': 'charger',
    'power': 'powerbank',
    'mouse': 'mouse',
    'pen': 'stylus',
}

def get_image_url(name, product_id):
    """根据商品名称生成 picsum 图片URL, 用 product_id 作为 seed 保证稳定"""
    name_lower = name.lower()
    # 先尝试用 unsplash source (更精准)
    for key, theme in CATEGORY_THEMES.items():
        if key in name_lower:
            # 备用: picsum 随机图
            seed = f"{key}-{product_id}"
            return f"https://picsum.photos/seed/{seed}/400/400"

    # 默认: picsum 用 ID 作 seed, 保证每个商品图固定
    return f"https://picsum.photos/seed/product{product_id}/400/400"


conn = pymysql.connect(host='localhost', port=3306, user='emall_app',
                       password='Emall@2024', database='db_product')
cur = conn.cursor()
cur.execute("SELECT id, name FROM product")
rows = cur.fetchall()
print(f"Updating {len(rows)} products with picsum.photos URLs...")

updated = 0
for pid, name in rows:
    new_url = get_image_url(name, pid)
    cur.execute("UPDATE product SET image_url = %s WHERE id = %s", (new_url, pid))
    updated += 1

conn.commit()
print(f"[OK] Updated {updated} product image URLs to picsum.photos")

# verify
cur.execute("SELECT id, name, image_url FROM product ORDER BY id LIMIT 5")
for r in cur.fetchall():
    print(f"  id={r[0]:3}  {r[1][:25]:25}  -> {r[2]}")
conn.close()
