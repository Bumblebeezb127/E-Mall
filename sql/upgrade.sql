-- =============================================================
-- E-Mall 数据库升级脚本 (增量更新)
-- 在已有数据库基础上运行, 不会破坏现有数据
-- =============================================================

USE db_order;
-- ----------------------------
-- 1. 给 order 表添加 address / remark 字段
-- ----------------------------
-- 检查列是否存在再 ALTER, 兼容 MySQL 5.x/8.x
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA = 'db_order' AND TABLE_NAME = '`order`' AND COLUMN_NAME = 'address');
SET @sql = IF(@col_exists = 0,
              'ALTER TABLE `order` ADD COLUMN address VARCHAR(255) DEFAULT NULL COMMENT ''收货地址'' AFTER status',
              'SELECT ''column address already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA = 'db_order' AND TABLE_NAME = '`order`' AND COLUMN_NAME = 'remark');
SET @sql = IF(@col_exists = 0,
              'ALTER TABLE `order` ADD COLUMN remark VARCHAR(500) DEFAULT NULL COMMENT ''订单备注'' AFTER address',
              'SELECT ''column remark already exists'' AS msg');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------
-- 2. 给所有商品补充库存 (插入尚未存在的库存记录)
-- ----------------------------
USE db_inventory;
INSERT INTO inventory (product_id, stock, version, created_at, updated_at)
SELECT p.id, p.stock, 0, NOW(), NOW()
FROM db_product.product p
WHERE NOT EXISTS (SELECT 1 FROM inventory i WHERE i.product_id = p.id)
  AND p.status = 1;

SELECT 'order table upgraded, inventory rows synced' AS done;
