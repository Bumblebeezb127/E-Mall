-- =============================================================
--  E-Mall 电商微服务数据库初始化脚本
--  用途:
--    1. 创建专用数据库用户 emall_app (替代 root, 最小权限)
--    2. 创建 4 个微服务数据库 (db_user, db_product, db_order, db_inventory)
--    3. 创建业务表
--    4. 灌入 120+ 条初始数据 (50 商品 / 30 用户 / 20 库存 / 20 订单)
--  使用方法 (以 root 身份):
--    mysql -u root -p < init.sql
-- =============================================================

-- 强制客户端使用 utf8mb4 字符集, 避免 Windows cmd / PowerShell GBK 默认编码导致中文乱码
SET NAMES utf8mb4;
SET CHARACTER_SET_CLIENT = utf8mb4;
SET CHARACTER_SET_RESULTS = utf8mb4;
SET CHARACTER_SET_CONNECTION = utf8mb4;

-- -------------------------------------------------------------
-- 1. 创建专用应用用户 (无 DROP/GRANT 权限, 仅有 DML + 部分 DDL)
-- -------------------------------------------------------------
-- 1.1 删除已存在的同名用户, 避免重复运行报错
DROP USER IF EXISTS 'emall_app'@'localhost';
DROP USER IF EXISTS 'emall_app'@'%';

-- 1.2 创建新用户 (允许本地 + 远程, 密码 Emall@2024)
CREATE USER 'emall_app'@'localhost' IDENTIFIED BY 'Emall@2024';
CREATE USER 'emall_app'@'%'         IDENTIFIED BY 'Emall@2024';

-- 1.3 授权 (4 个数据库上的完整 DML + 部分 DDL)
GRANT SELECT, INSERT, UPDATE, DELETE,
      CREATE, DROP, ALTER, INDEX, REFERENCES,
      CREATE VIEW, SHOW VIEW,
      EXECUTE, ALTER ROUTINE, CREATE ROUTINE,
      CREATE TEMPORARY TABLES
      ON db_user.*     TO 'emall_app'@'localhost', 'emall_app'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE,
      CREATE, DROP, ALTER, INDEX, REFERENCES,
      CREATE VIEW, SHOW VIEW,
      EXECUTE, ALTER ROUTINE, CREATE ROUTINE,
      CREATE TEMPORARY TABLES
      ON db_product.*  TO 'emall_app'@'localhost', 'emall_app'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE,
      CREATE, DROP, ALTER, INDEX, REFERENCES,
      CREATE VIEW, SHOW VIEW,
      EXECUTE, ALTER ROUTINE, CREATE ROUTINE,
      CREATE TEMPORARY TABLES
      ON db_order.*    TO 'emall_app'@'localhost', 'emall_app'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE,
      CREATE, DROP, ALTER, INDEX, REFERENCES,
      CREATE VIEW, SHOW VIEW,
      EXECUTE, ALTER ROUTINE, CREATE ROUTINE,
      CREATE TEMPORARY TABLES
      ON db_inventory.* TO 'emall_app'@'localhost', 'emall_app'@'%';

FLUSH PRIVILEGES;

-- -------------------------------------------------------------
-- 2. 删除并重建数据库 (干净初始化)
-- -------------------------------------------------------------
DROP DATABASE IF EXISTS db_user;
DROP DATABASE IF EXISTS db_product;
DROP DATABASE IF EXISTS db_order;
DROP DATABASE IF EXISTS db_inventory;

CREATE DATABASE db_user     DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE db_product  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE db_order    DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE db_inventory DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- =============================================================
-- 3. 创建表结构
-- =============================================================

-- ---------- 3.1 用户表 ----------
USE db_user;

DROP TABLE IF EXISTS `user`;

CREATE TABLE `user` (
    `id`         bigint       NOT NULL AUTO_INCREMENT  COMMENT '用户ID',
    `username`   varchar(50)  NOT NULL                  COMMENT '用户名',
    `password`   varchar(100) NOT NULL                  COMMENT '密码(BCrypt)',
    `nickname`   varchar(50)  DEFAULT NULL              COMMENT '昵称',
    `email`      varchar(100) DEFAULT NULL              COMMENT '邮箱',
    `phone`      varchar(20)  DEFAULT NULL              COMMENT '手机号',
    `avatar`     varchar(255) DEFAULT NULL              COMMENT '头像URL',
    `role`       varchar(20)  NOT NULL DEFAULT 'USER'   COMMENT '角色: ADMIN/MERCHANT/USER',
    `status`     tinyint      NOT NULL DEFAULT 1        COMMENT '状态: 1-正常 0-禁用',
    `created_at` datetime     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` datetime     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `idx_role`   (`role`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ---------- 3.2 商品表 ----------
USE db_product;

DROP TABLE IF EXISTS `product`;

CREATE TABLE `product` (
    `id`          bigint        NOT NULL AUTO_INCREMENT  COMMENT '商品ID',
    `name`        varchar(100)  NOT NULL                 COMMENT '商品名称',
    `price`       decimal(10,2) NOT NULL                 COMMENT '商品价格',
    `stock`       int           DEFAULT 0                COMMENT '库存数量',
    `description` text                                   COMMENT '商品描述',
    `image_url`   varchar(255)  DEFAULT NULL             COMMENT '商品图片URL',
    `category`    varchar(50)   DEFAULT NULL             COMMENT '商品分类',
    `status`      tinyint       DEFAULT 1                COMMENT '状态: 1-上架 0-下架',
    `created_at`  datetime      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  datetime      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_status`   (`status`),
    KEY `idx_name`     (`name`),
    KEY `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品表';

-- ---------- 3.3 订单表 + 订单项表 ----------
USE db_order;

DROP TABLE IF EXISTS `order_item`;
DROP TABLE IF EXISTS `order`;

CREATE TABLE `order` (
    `id`            bigint        NOT NULL AUTO_INCREMENT  COMMENT '订单ID',
    `order_no`      varchar(32)   NOT NULL                 COMMENT '订单编号',
    `user_id`       bigint        NOT NULL                 COMMENT '用户ID',
    `total_amount`  decimal(10,2) DEFAULT NULL             COMMENT '订单总金额',
    `status`        tinyint       DEFAULT 0                COMMENT '状态: 0-待支付 1-已支付 2-已发货 3-已完成 4-已取消',
    `receiver_name` varchar(50)   DEFAULT NULL             COMMENT '收货人姓名',
    `receiver_phone` varchar(20)  DEFAULT NULL             COMMENT '收货人电话',
    `address`       varchar(255)  DEFAULT NULL             COMMENT '收货地址',
    `remark`        varchar(255)  DEFAULT NULL             COMMENT '备注',
    `created_at`    datetime      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`    datetime      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_status`  (`status`),
    KEY `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

CREATE TABLE `order_item` (
    `id`           bigint        NOT NULL AUTO_INCREMENT COMMENT '订单项ID',
    `order_id`     bigint        NOT NULL                COMMENT '订单ID',
    `product_id`   bigint        NOT NULL                COMMENT '商品ID',
    `product_name` varchar(100)  NOT NULL                COMMENT '商品名(快照)',
    `price`        decimal(10,2) NOT NULL                COMMENT '购买时单价',
    `quantity`     int           NOT NULL                COMMENT '购买数量',
    `subtotal`     decimal(10,2) NOT NULL                COMMENT '小计金额',
    `created_at`   datetime      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_order_id`   (`order_id`),
    KEY `idx_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单项表';

-- ---------- 3.4 库存表 ----------
USE db_inventory;

DROP TABLE IF EXISTS `inventory`;

CREATE TABLE `inventory` (
    `id`         bigint   NOT NULL AUTO_INCREMENT  COMMENT '库存ID',
    `product_id` bigint   NOT NULL                 COMMENT '商品ID',
    `warehouse`  varchar(50) DEFAULT 'MAIN'        COMMENT '仓库名称',
    `stock`      int      NOT NULL DEFAULT 0       COMMENT '库存数量',
    `locked`     int      NOT NULL DEFAULT 0       COMMENT '锁定数量(预占)',
    `version`    int      DEFAULT 0                COMMENT '乐观锁版本号',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_product_warehouse` (`product_id`, `warehouse`),
    KEY `idx_stock`     (`stock`),
    KEY `idx_warehouse` (`warehouse`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库存表';

-- =============================================================
-- 4. 灌入初始数据 (共 120 条)
-- =============================================================

-- ---------- 4.1 商品数据 (50 条) ----------
USE db_product;

TRUNCATE TABLE `product`;

INSERT INTO `product` (`id`, `name`, `price`, `stock`, `description`, `image_url`, `category`, `status`) VALUES
-- 手机类 (10 个)
(1,  '华为Mate 60 Pro',       6999.00, 100, '华为旗舰, 麒麟9000S, 卫星通话',           'https://example.com/images/huawei-mate60.jpg',     '手机',   1),
(2,  'iPhone 15 Pro Max',     9999.00,  80, '苹果A17 Pro 芯片, 钛金属边框',             'https://example.com/images/iphone15pm.jpg',        '手机',   1),
(3,  '小米14 Ultra',          6499.00,  60, '徕卡光学, 骁龙8 Gen3',                      'https://example.com/images/mi14u.jpg',             '手机',   1),
(4,  'OPPO Find X7',          4999.00,  90, '天玑9300, 哈苏联名',                        'https://example.com/images/findx7.jpg',            '手机',   1),
(5,  'vivo X100 Pro',         5499.00,  70, '蔡司影像, 蓝晶芯片',                        'https://example.com/images/vivox100.jpg',         '手机',   1),
(6,  '三星Galaxy S24 Ultra',  9699.00,  50, '骁龙8 Gen3 for Galaxy, S Pen',             'https://example.com/images/s24u.jpg',              '手机',   1),
(7,  '荣耀Magic6 Pro',        5699.00,  85, '鹰眼相机, 骁龙8 Gen3',                     'https://example.com/images/magic6.jpg',            '手机',   1),
(8,  '一加12',                4299.00, 110, '哈苏调色, 24GB+1TB',                       'https://example.com/images/oneplus12.jpg',         '手机',   1),
(9,  'Redmi K70 Pro',         3299.00, 150, '性价比旗舰, 骁龙8 Gen3',                   'https://example.com/images/k70pro.jpg',            '手机',   1),
(10, 'realme GT5 Pro',        3299.00, 120, '旗舰焊门员, 长续航',                        'https://example.com/images/gt5pro.jpg',            '手机',   1),

-- 电脑类 (10 个)
(11, 'MacBook Pro 14 M3',     14999.00, 30, 'M3 Pro 芯片, Liquid 视网膜 XDR',           'https://example.com/images/mbp14.jpg',             '电脑',   1),
(12, 'MacBook Air 13 M2',      8999.00, 50, 'M2 芯片, 轻薄长续航',                      'https://example.com/images/mba13.jpg',             '电脑',   1),
(13, 'ThinkPad X1 Carbon',     9999.00, 40, '商务旗舰, 14寸 2.8K',                       'https://example.com/images/x1carbon.jpg',          '电脑',   1),
(14, '戴尔XPS 15',            13999.00, 25, 'OLED 4K屏, 设计师首选',                    'https://example.com/images/xps15.jpg',             '电脑',   1),
(15, '华为MateBook X Pro',     9999.00, 35, '3.1K 全面屏, 鸿蒙生态',                    'https://example.com/images/matebookx.jpg',         '电脑',   1),
(16, '联想小新Pro 16',         5999.00, 80, '16寸 2.5K 120Hz, R7-7840HS',               'https://example.com/images/xiaoxinpro16.jpg',      '电脑',   1),
(17, 'ROG 幻16',              12999.00, 20, 'i9-13900H + RTX4070, 游戏本',              'https://example.com/images/rog16.jpg',             '电脑',   1),
(18, '雷神911黑武士',          7999.00, 45, 'i7-13700H + RTX4060',                       'https://example.com/images/911.jpg',               '电脑',   1),
(19, '微软Surface Pro 9',     9999.00, 30, '二合一平板, 13寸触控屏',                   'https://example.com/images/surface9.jpg',          '电脑',   1),
(20, '机械革命无界14X',        4299.00, 60, '高性价比轻薄本',                           'https://example.com/images/wujie14x.jpg',          '电脑',   1),

-- 平板类 (8 个)
(21, 'iPad Pro 12.9 M2',       9999.00, 40, 'M2 芯片, mini-LED 屏幕',                   'https://example.com/images/ipp12.jpg',             '平板',   1),
(22, 'iPad Air 5',             4799.00, 60, 'M1 芯片, 10.9寸全面屏',                    'https://example.com/images/ipadair5.jpg',          '平板',   1),
(23, '华为MatePad Pro 13.2',   5199.00, 50, '13.2寸柔性OLED, 鸿蒙生态',                 'https://example.com/images/matepad13.jpg',         '平板',   1),
(24, '小米平板6 Pro',          3299.00, 80, '骁龙8+ Gen1, 11寸 2.8K',                   'https://example.com/images/mipad6p.jpg',           '平板',   1),
(25, '三星Galaxy Tab S9',     6499.00, 35, '11寸 Dynamic AMOLED 2X',                    'https://example.com/images/tabs9.jpg',             '平板',   1),
(26, '荣耀MagicPad 13',        3299.00, 70, '13寸大屏, 骁龙888',                        'https://example.com/images/magicpad.jpg',          '平板',   1),
(27, 'OPPO Pad 2',             2999.00, 90, '11.6寸 2.8K 144Hz',                        'https://example.com/images/oppopad2.jpg',          '平板',   1),
(28, 'vivo Pad Air',           1899.00,100, '11.5寸 2.8K 144Hz',                        'https://example.com/images/vivopadair.jpg',        '平板',   1),

-- 家电类 (10 个)
(29, '海尔变频空调',           3499.00, 60, '1.5匹一级能效, 智能控温',                  'https://example.com/images/haier-ac.jpg',          '家电',   1),
(30, '美的对开门冰箱',         4999.00, 40, '606升变频风冷无霜',                        'https://example.com/images/midea-fridge.jpg',      '家电',   1),
(31, '西门子10kg洗衣机',       4299.00, 50, 'BLDC变频, 10公斤大容量',                   'https://example.com/images/siemens-wm.jpg',        '家电',   1),
(32, '小米电视6 OLED 65',      6999.00, 30, '65寸 4K OLED, MEMC运动补偿',               'https://example.com/images/mi-tv6.jpg',            '家电',   1),
(33, '华为智慧屏V75',          9999.00, 20, '75寸 SuperMiniLED, 鸿蒙生态',              'https://example.com/images/vision-v75.jpg',        '家电',   1),
(34, '戴森V15 Detect吸尘器',   5290.00, 40, '激光显尘, 强劲吸力',                       'https://example.com/images/dyson-v15.jpg',         '家电',   1),
(35, '飞利浦空气净化器',       2999.00, 70, '甲醛CADR 400, APP远程',                    'https://example.com/images/philips-air.jpg',       '家电',   1),
(36, '格力电暖气',             1299.00,100, '踢脚线取暖器, 智能恒温',                   'https://example.com/images/gree-heater.jpg',       '家电',   1),
(37, '九阳破壁机',              699.00,150, '低音破壁, 多功能料理',                     'https://example.com/images/joyoung.jpg',           '家电',   1),
(38, '苏泊尔电饭煲',            399.00,200, 'IH电磁加热, 智能预约',                     'https://example.com/images/supor.jpg',             '家电',   1),

-- 穿戴类 (6 个)
(39, 'Apple Watch Ultra 2',   6499.00, 50, '钛金属表壳, 36小时续航',                   'https://example.com/images/awu2.jpg',              '穿戴',   1),
(40, '华为Watch GT4',          1488.00,100, '46mm 运动健康, 14天续航',                  'https://example.com/images/gt4.jpg',               '穿戴',   1),
(41, '小米手环8',               239.00,200, 'AMOLED屏, 16天续航',                       'https://example.com/images/miband8.jpg',           '穿戴',   1),
(42, 'AirPods Pro 2',         1899.00, 80, '主动降噪, 空间音频',                       'https://example.com/images/airpodspro2.jpg',       '穿戴',   1),
(43, '索尼WH-1000XM5',        2899.00, 60, '无线降噪耳机, 30小时续航',                'https://example.com/images/wh1000xm5.jpg',         '穿戴',   1),
(44, 'Bose QC Ultra',          3499.00, 40, '沉浸式音频, 旗舰降噪',                     'https://example.com/images/qc-ultra.jpg',          '穿戴',   1),

-- 配件类 (6 个)
(45, '罗技MX Master 3S',      1099.00, 80, '无线静音, 多设备切换',                     'https://example.com/images/mxmaster3s.jpg',        '配件',   1),
(46, '雷蛇BlackWidow V4',     1499.00, 50, '机械键盘, RGB背光',                        'https://example.com/images/razer-bw.jpg',          '配件',   1),
(47, '小米10000mAh充电宝',     129.00,300, '22.5W双向快充',                            'https://example.com/images/mi-powerbank.jpg',      '配件',   1),
(48, 'Anker 65W氮化镓',         199.00,200, '三口快充, 折叠插脚',                       'https://example.com/images/anker-65w.jpg',         '配件',   1),
(49, '三星980 Pro 2TB SSD',   1099.00, 60, 'NVMe PCIe 4.0, 7000MB/s',                  'https://example.com/images/980pro.jpg',            '配件',   1),
(50, '绿联USB-C扩展坞',        399.00,150, '10合1, 4K HDMI',                            'https://example.com/images/ugreen-dock.jpg',       '配件',   1);

-- ---------- 4.2 用户数据 (30 条) ----------
USE db_user;

TRUNCATE TABLE `user`;

-- 密码统一为 123456 的 BCrypt 哈希: $2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
-- 管理员密码 admin123 的 BCrypt 哈希:  $2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2
INSERT INTO `user` (`id`, `username`, `password`, `nickname`, `email`, `phone`, `role`, `status`) VALUES
(1,  'admin',    '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2', '超级管理员', 'admin@emall.com',  '13800000000', 'ADMIN',    1),
(2,  'merchant1','$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '华为旗舰店',  'merchant1@emall.com','13800000001', 'MERCHANT', 1),
(3,  'merchant2','$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '苹果旗舰店',  'merchant2@emall.com','13800000002', 'MERCHANT', 1),
(4,  'merchant3','$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '小米官方',    'merchant3@emall.com','13800000003', 'MERCHANT', 1),
(5,  'user001',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '张三',        'user001@emall.com',  '13900000001', 'USER',     1),
(6,  'user002',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '李四',        'user002@emall.com',  '13900000002', 'USER',     1),
(7,  'user003',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '王五',        'user003@emall.com',  '13900000003', 'USER',     1),
(8,  'user004',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '赵六',        'user004@emall.com',  '13900000004', 'USER',     1),
(9,  'user005',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '钱七',        'user005@emall.com',  '13900000005', 'USER',     1),
(10, 'user006',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '孙八',        'user006@emall.com',  '13900000006', 'USER',     1),
(11, 'user007',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '周九',        'user007@emall.com',  '13900000007', 'USER',     1),
(12, 'user008',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '吴十',        'user008@emall.com',  '13900000008', 'USER',     1),
(13, 'user009',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '郑十一',      'user009@emall.com',  '13900000009', 'USER',     1),
(14, 'user010',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '王十二',      'user010@emall.com',  '13900000010', 'USER',     1),
(15, 'user011',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '李十三',      'user011@emall.com',  '13900000011', 'USER',     1),
(16, 'user012',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '张十四',      'user012@emall.com',  '13900000012', 'USER',     1),
(17, 'user013',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '刘十五',      'user013@emall.com',  '13900000013', 'USER',     1),
(18, 'user014',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '陈十六',      'user014@emall.com',  '13900000014', 'USER',     1),
(19, 'user015',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '杨十七',      'user015@emall.com',  '13900000015', 'USER',     1),
(20, 'user016',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '黄十八',      'user016@emall.com',  '13900000016', 'USER',     1),
(21, 'user017',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '周十九',      'user017@emall.com',  '13900000017', 'USER',     1),
(22, 'user018',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '吴二十',      'user018@emall.com',  '13900000018', 'USER',     1),
(23, 'user019',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '徐二十一',    'user019@emall.com',  '13900000019', 'USER',     1),
(24, 'user020',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '孙二十二',    'user020@emall.com',  '13900000020', 'USER',     1),
(25, 'user021',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '马二十三',    'user021@emall.com',  '13900000021', 'USER',     1),
(26, 'user022',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '朱二十四',    'user022@emall.com',  '13900000022', 'USER',     1),
(27, 'user023',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '胡二十五',    'user023@emall.com',  '13900000023', 'USER',     1),
(28, 'user024',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '林二十六',    'user024@emall.com',  '13900000024', 'USER',     1),
(29, 'user025',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '何二十七',    'user025@emall.com',  '13900000025', 'USER',     1),
(30, 'user026',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '高二十八',    'user026@emall.com',  '13900000026', 'USER',     0),
(31, 'user027',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '罗二十九',    'user027@emall.com',  '13900000027', 'USER',     1),
(32, 'user028',  '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '梁三十',      'user028@emall.com',  '13900000028', 'USER',     1);

-- ---------- 4.3 库存数据 (20 条) ----------
USE db_inventory;

TRUNCATE TABLE `inventory`;

INSERT INTO `inventory` (`product_id`, `warehouse`, `stock`, `locked`, `version`) VALUES
(1,  'MAIN',      95, 2, 0),
(2,  'MAIN',      78, 1, 0),
(3,  'MAIN',      55, 0, 0),
(4,  'MAIN',      85, 0, 0),
(5,  'MAIN',      65, 1, 0),
(6,  'MAIN',      48, 0, 0),
(7,  'MAIN',      80, 0, 0),
(8,  'MAIN',     105, 0, 0),
(9,  'MAIN',     145, 0, 0),
(10, 'MAIN',     115, 0, 0),
(11, 'BEIJING',   28, 1, 0),
(12, 'BEIJING',   48, 0, 0),
(13, 'SHANGHAI',  38, 0, 0),
(14, 'SHANGHAI',  23, 0, 0),
(15, 'GUANGZHOU', 33, 0, 0),
(16, 'GUANGZHOU', 75, 0, 0),
(17, 'MAIN',      18, 0, 0),
(18, 'MAIN',      42, 0, 0),
(19, 'SHENZHEN',  28, 0, 0),
(20, 'SHENZHEN',  55, 0, 0);

-- ---------- 4.4 订单数据 (20 条) + 订单项 (约 20-30 条) ----------
USE db_order;

TRUNCATE TABLE `order_item`;
TRUNCATE TABLE `order`;

INSERT INTO `order` (`id`, `order_no`, `user_id`, `total_amount`, `status`, `receiver_name`, `receiver_phone`, `address`, `created_at`) VALUES
(1,  'ORD20250601001', 5,  6999.00, 3, '张三', '13900000001', '北京市朝阳区建国路1号',           '2026-05-01 10:15:00'),
(2,  'ORD20250601002', 6,  9999.00, 2, '李四', '13900000002', '上海市浦东新区世纪大道100号',     '2026-05-01 14:20:00'),
(3,  'ORD20250602003', 7, 10398.00, 1, '王五', '13900000003', '广州市天河区珠江新城88号',         '2026-05-02 09:30:00'),
(4,  'ORD20250602004', 8, 14999.00, 1, '赵六', '13900000004', '深圳市南山区科技园路1号',         '2026-05-02 16:45:00'),
(5,  'ORD20250603005', 9,   538.00, 3, '钱七', '13900000005', '杭州市西湖区文三路100号',         '2026-05-03 11:00:00'),
(6,  'ORD20250603006', 10,  368.00, 0, '孙八', '13900000006', '成都市武侯区天府大道500号',       '2026-05-03 20:30:00'),
(7,  'ORD20250604007', 11, 5499.00, 2, '周九', '13900000007', '武汉市江汉区解放大道700号',       '2026-05-04 08:15:00'),
(8,  'ORD20250604008', 12,  199.00, 4, '吴十', '13900000008', '南京市鼓楼区中山路200号',         '2026-05-04 13:40:00'),
(9,  'ORD20250605009', 13, 4299.00, 1, '郑十一', '13900000009', '西安市雁塔区高新路50号',         '2026-05-05 15:20:00'),
(10, 'ORD20250605010', 14, 5198.00, 3, '王十二', '13900000010', '重庆市渝中区解放碑步行街',         '2026-05-05 17:30:00'),
(11, 'ORD20250606011', 15,  699.00, 1, '李十三', '13900000011', '苏州市工业园区现代大道',         '2026-05-06 09:50:00'),
(12, 'ORD20250606012', 16, 6698.00, 0, '张十四', '13900000012', '天津市和平区南京路200号',         '2026-05-06 14:10:00'),
(13, 'ORD20250607013', 17, 7198.00, 2, '刘十五', '13900000013', '青岛市市南区香港中路100号',       '2026-05-07 11:25:00'),
(14, 'ORD20250607014', 18, 1899.00, 1, '陈十六', '13900000014', '大连市中山区人民路50号',         '2026-05-07 18:00:00'),
(15, 'ORD20250608015', 19, 1099.00, 3, '杨十七', '13900000015', '沈阳市和平区南京北街100号',       '2026-05-08 10:35:00'),
(16, 'ORD20250608016', 20, 1099.00, 1, '黄十八', '13900000016', '长沙市岳麓区金星中路',           '2026-05-08 13:55:00'),
(17, 'ORD20250609017', 21, 3198.00, 2, '周十九', '13900000017', '郑州市金水区花园路',             '2026-05-09 16:20:00'),
(18, 'ORD20250609018', 22, 5699.00, 0, '吴二十', '13900000018', '济南市历下区泉城路',             '2026-05-09 19:45:00'),
(19, 'ORD20250610019', 23, 1499.00, 3, '徐二十一', '13900000019', '合肥市蜀山区政务区',            '2026-05-10 08:30:00'),
(20, 'ORD20250610020', 24, 4999.00, 1, '孙二十二', '13900000020', '福州市鼓楼区五一北路',           '2026-05-10 12:15:00');

-- 订单项数据
INSERT INTO `order_item` (`order_id`, `product_id`, `product_name`, `price`, `quantity`, `subtotal`) VALUES
-- 订单1: 华为Mate60
(1, 1, '华为Mate 60 Pro',       6999.00, 1,  6999.00),
-- 订单2: iPhone 15 Pro Max
(2, 2, 'iPhone 15 Pro Max',     9999.00, 1,  9999.00),
-- 订单3: 1 平板 + 1 平板壳
(3, 21, 'iPad Pro 12.9 M2',      9999.00, 1,  9999.00),
(3, 50, '绿联USB-C扩展坞',        399.00, 1,   399.00),
-- 订单4: MacBook Pro 14
(4, 11, 'MacBook Pro 14 M3',    14999.00, 1, 14999.00),
-- 订单5: 1 穿戴 + 1 家电
(5, 41, '小米手环8',              239.00, 1,   239.00),
(5, 38, '苏泊尔电饭煲',            299.00, 1,   299.00),
-- 订单6: 小米手环
(6, 41, '小米手环8',              239.00, 1,   239.00),
(6, 47, '小米10000mAh充电宝',     129.00, 1,   129.00),
-- 订单7: vivo X100
(7, 5, 'vivo X100 Pro',         5499.00, 1,  5499.00),
-- 订单8: Anker 充电头 (已取消)
(8, 48, 'Anker 65W氮化镓',         199.00, 1,   199.00),
-- 订单9: 1 电脑 + 1 鼠标
(9, 20, '机械革命无界14X',        4299.00, 1,  4299.00),
-- 订单10: 1 手机 + 1 平板
(10, 9, 'Redmi K70 Pro',        3299.00, 1,  3299.00),
(10, 28, 'vivo Pad Air',         1899.00, 1,  1899.00),
-- 订单11: 九阳破壁机
(11, 37, '九阳破壁机',              699.00, 1,   699.00),
-- 订单12: 1 平板 + 1 键盘
(12, 23, '华为MatePad Pro 13.2',  5199.00, 1,  5199.00),
(12, 46, '雷蛇BlackWidow V4',    1499.00, 1,  1499.00),
-- 订单13: 1 穿戴 + 1 家电
(13, 39, 'Apple Watch Ultra 2',  6499.00, 1,  6499.00),
(13, 37, '九阳破壁机',              699.00, 1,   699.00),
-- 订单14: AirPods
(14, 42, 'AirPods Pro 2',        1899.00, 1,  1899.00),
-- 订单15: 罗技鼠标
(15, 45, '罗技MX Master 3S',     1099.00, 1,  1099.00),
-- 订单16: 三星SSD
(16, 49, '三星980 Pro 2TB SSD',  1099.00, 1,  1099.00),
-- 订单17: 1 穿戴 + 1 家电
(17, 43, '索尼WH-1000XM5',       2899.00, 1,  2899.00),
(17, 38, '苏泊尔电饭煲',            299.00, 1,   299.00),
-- 订单18: 荣耀Magic6
(18, 7, '荣耀Magic6 Pro',        5699.00, 1,  5699.00),
-- 订单19: 雷蛇键盘
(19, 46, '雷蛇BlackWidow V4',    1499.00, 1,  1499.00),
-- 订单20: OPPO Find X7
(20, 4, 'OPPO Find X7',         4999.00, 1,  4999.00);

-- =============================================================
-- 5. 完成提示
-- =============================================================
SELECT '✅ 初始化完成! 用户: emall_app / Emall@2024' AS message;
SELECT '商品总数: ' AS info, COUNT(*) AS cnt FROM db_product.product
UNION ALL
SELECT '用户总数: ',                  COUNT(*) FROM db_user.user
UNION ALL
SELECT '订单总数: ',                  COUNT(*) FROM db_order.`order`
UNION ALL
SELECT '订单项总数: ',                COUNT(*) FROM db_order.order_item
UNION ALL
SELECT '库存总数: ',                  COUNT(*) FROM db_inventory.inventory;
