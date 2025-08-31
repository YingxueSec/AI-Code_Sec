-- 导出权限管理功能数据库表结构
-- 运行前请确保已连接到正确的数据库

-- 创建导出权限配置表
CREATE TABLE IF NOT EXISTS export_permission_configs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_level VARCHAR(50) NOT NULL COMMENT '用户等级',
    allowed_formats JSON NOT NULL COMMENT '允许的导出格式列表',
    max_exports_per_day BIGINT NOT NULL DEFAULT 10 COMMENT '每日最大导出次数',
    max_file_size_mb BIGINT NOT NULL DEFAULT 50 COMMENT '最大文件大小(MB)',
    description TEXT COMMENT '配置描述',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_level (user_level),
    INDEX idx_is_active (is_active),
    UNIQUE KEY uk_user_level (user_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='导出权限配置表';

-- 创建用户导出记录表
CREATE TABLE IF NOT EXISTS user_export_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    task_id BIGINT NOT NULL COMMENT '任务ID',
    export_format VARCHAR(20) NOT NULL COMMENT '导出格式',
    file_size_mb BIGINT NOT NULL DEFAULT 0 COMMENT '文件大小(MB)',
    export_status VARCHAR(20) NOT NULL DEFAULT 'success' COMMENT '导出状态(success, failed, blocked)',
    blocked_reason VARCHAR(255) COMMENT '被阻止的原因',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_task_id (task_id),
    INDEX idx_export_format (export_format),
    INDEX idx_export_status (export_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户导出记录表';

-- 插入默认的导出权限配置
INSERT INTO export_permission_configs (user_level, allowed_formats, max_exports_per_day, max_file_size_mb, description, is_active) 
VALUES 
    ('free', '["json"]', 3, 10, '免费用户：仅支持JSON格式，每日3次，最大10MB', TRUE),
    ('standard', '["json", "markdown"]', 10, 50, '标准用户：支持JSON和Markdown格式，每日10次，最大50MB', TRUE),
    ('premium', '["json", "markdown", "pdf", "html"]', 50, 200, '高级用户：支持多种格式，每日50次，最大200MB', TRUE)
ON DUPLICATE KEY UPDATE 
    allowed_formats = VALUES(allowed_formats),
    max_exports_per_day = VALUES(max_exports_per_day),
    max_file_size_mb = VALUES(max_file_size_mb),
    description = VALUES(description),
    is_active = VALUES(is_active);

-- 验证表结构
SELECT 'export_permission_configs表创建成功' as status;
DESCRIBE export_permission_configs;

SELECT 'user_export_logs表创建成功' as status;
DESCRIBE user_export_logs;

-- 验证默认数据
SELECT 'default configurations:' as status;
SELECT * FROM export_permission_configs;
