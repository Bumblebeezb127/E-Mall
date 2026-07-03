"""Run database upgrade to add address/remark and sync inventory."""
import pymysql

CONN_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'emall_app',
    'password': 'Emall@2024',
    'charset': 'utf8mb4',
    'autocommit': False,
}

def main():
    # 1. db_order: add address/remark columns
    print("=== Step 1: upgrade db_order ===")
    conn = pymysql.connect(database='db_order', **CONN_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'db_order' AND TABLE_NAME = 'order' AND COLUMN_NAME = 'address'
    """)
    if cur.fetchone()[0] == 0:
        cur.execute("ALTER TABLE `order` ADD COLUMN address VARCHAR(255) DEFAULT NULL COMMENT '收货地址' AFTER status")
        print("  + added column: order.address")
    else:
        print("  - column order.address already exists")

    cur.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'db_order' AND TABLE_NAME = 'order' AND COLUMN_NAME = 'remark'
    """)
    if cur.fetchone()[0] == 0:
        cur.execute("ALTER TABLE `order` ADD COLUMN remark VARCHAR(500) DEFAULT NULL COMMENT '订单备注' AFTER address")
        print("  + added column: order.remark")
    else:
        print("  - column order.remark already exists")
    conn.commit()
    conn.close()

    # 2. db_inventory: sync inventory for all products
    print("\n=== Step 2: sync inventory for all products ===")
    conn = pymysql.connect(database='db_product', **CONN_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id, name, stock FROM product WHERE status = 1 ORDER BY id")
    products = cur.fetchall()
    print(f"  Found {len(products)} active products")
    conn.close()

    conn = pymysql.connect(database='db_inventory', **CONN_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT product_id FROM inventory")
    existing = {row[0] for row in cur.fetchall()}
    print(f"  Existing inventory rows: {len(existing)}")

    added = 0
    for pid, name, stock in products:
        if pid in existing:
            continue
        cur.execute(
            "INSERT INTO inventory (product_id, stock, version, created_at, updated_at) VALUES (%s, %s, 0, NOW(), NOW())",
            (pid, stock or 0)
        )
        added += 1
    conn.commit()
    print(f"  + inserted {added} new inventory rows")
    conn.close()

    print("\nDone.")

if __name__ == "__main__":
    main()
