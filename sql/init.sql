-- E-Mall Microservice Database Initialization Script
-- Create databases
CREATE DATABASE IF NOT EXISTS db_user DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS db_product DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS db_order DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS db_inventory DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE db_user;

CREATE TABLE IF NOT EXISTS `user` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'User ID',
    `username` varchar(50) NOT NULL COMMENT 'Username',
    `password` varchar(100) NOT NULL COMMENT 'Password',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='User Table';

USE db_product;

CREATE TABLE IF NOT EXISTS `product` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'Product ID',
    `name` varchar(100) NOT NULL COMMENT 'Product Name',
    `price` decimal(10,2) NOT NULL COMMENT 'Product Price',
    `stock` int DEFAULT 0 COMMENT 'Stock Quantity',
    `description` text COMMENT 'Product Description',
    `image_url` varchar(255) DEFAULT NULL COMMENT 'Product Image URL',
    `status` tinyint DEFAULT 1 COMMENT 'Product Status: 1-Active, 0-Inactive',
    PRIMARY KEY (`id`),
    KEY `idx_status` (`status`),
    KEY `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Product Table';

USE db_order;

CREATE TABLE IF NOT EXISTS `order` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'Order ID',
    `order_no` varchar(32) NOT NULL COMMENT 'Order Number',
    `user_id` bigint NOT NULL COMMENT 'User ID',
    `total_amount` decimal(10,2) DEFAULT NULL COMMENT 'Total Amount',
    `status` tinyint DEFAULT 0 COMMENT 'Order Status: 0-Pending, 1-Paid, 2-Shipped, 3-Completed, 4-Cancelled',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Order Table';

CREATE TABLE IF NOT EXISTS `order_item` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'Order Item ID',
    `order_id` bigint NOT NULL COMMENT 'Order ID',
    `product_id` bigint NOT NULL COMMENT 'Product ID',
    `product_name` varchar(100) NOT NULL COMMENT 'Product Name (Snapshot)',
    `price` decimal(10,2) NOT NULL COMMENT 'Price at Purchase',
    `quantity` int NOT NULL COMMENT 'Quantity',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
    PRIMARY KEY (`id`),
    KEY `idx_order_id` (`order_id`),
    KEY `idx_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Order Item Table';

ALTER TABLE `order_item` ADD CONSTRAINT `fk_order_item_order` FOREIGN KEY (`order_id`) REFERENCES `order` (`id`) ON DELETE CASCADE;

USE db_inventory;

CREATE TABLE IF NOT EXISTS `inventory` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'Inventory ID',
    `product_id` bigint NOT NULL COMMENT 'Product ID',
    `stock` int NOT NULL DEFAULT 0 COMMENT 'Stock Quantity',
    `version` int DEFAULT 0 COMMENT 'Optimistic Lock Version',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_product_id` (`product_id`),
    KEY `idx_stock` (`stock`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Inventory Table';

USE db_product;

INSERT INTO `product` (`name`, `price`, `stock`, `description`, `image_url`, `status`) VALUES
('华为手机', 3999.00, 100, '华为旗舰手机，麒麟芯片，拍照神器', 'https://example.com/images/huawei-phone.jpg', 1),
('小米手环', 299.00, 50, '小米智能手环，支持心率监测、计步', 'https://example.com/images/xiaomi-band.jpg', 1);

USE db_inventory;

INSERT INTO `inventory` (`product_id`, `stock`, `version`) VALUES
(1, 100, 0),
(2, 50, 0);
