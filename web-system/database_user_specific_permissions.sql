-- 用户专属导出权限配置表
CREATE TABLE IF NOT EXISTS `user_specific_export_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL UNIQUE,
  `allowed_formats` JSON NOT NULL COMMENT '允许的导出格式列表',
  `max_exports_per_day` BIGINT NOT NULL DEFAULT 0 COMMENT '每日最大导出次数',
  `max_file_size_mb` BIGINT NOT NULL DEFAULT 0 COMMENT '最大文件大小(MB)',
  `description` TEXT NULL COMMENT '配置描述',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户专属导出权限配置表';

-- 插入示例数据（可选）
-- INSERT INTO `user_specific_export_permissions` 
-- (`user_id`, `allowed_formats`, `max_exports_per_day`, `max_file_size_mb`, `description`) 
-- VALUES 
-- (2, '["json", "markdown", "pdf"]', 100, 500, '特殊用户：支持多格式，高限额');
