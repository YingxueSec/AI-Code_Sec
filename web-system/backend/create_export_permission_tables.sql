-- 创建用户导出权限表
CREATE TABLE IF NOT EXISTS user_export_permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    allowed_formats JSON NOT NULL DEFAULT ('["json"]'),
    updated_by BIGINT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_user_export_permissions_user_id (user_id),
    INDEX idx_user_export_permissions_updated_by (updated_by)
);

-- 创建导出操作日志表
CREATE TABLE IF NOT EXISTS export_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    export_format VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NULL,
    success VARCHAR(10) NOT NULL DEFAULT 'success',
    error_message VARCHAR(500) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES audit_tasks(id) ON DELETE CASCADE,
    
    INDEX idx_export_logs_user_id (user_id),
    INDEX idx_export_logs_task_id (task_id),
    INDEX idx_export_logs_exported_at (exported_at),
    INDEX idx_export_logs_export_format (export_format),
    INDEX idx_export_logs_success (success)
);

-- 插入一些示例数据（可选）
-- 为现有用户设置默认权限（可根据需要调整）
-- INSERT INTO user_export_permissions (user_id, allowed_formats, updated_by) 
-- SELECT id, '["json"]', 1 FROM users WHERE role = 'user' AND user_level = 'free';

-- INSERT INTO user_export_permissions (user_id, allowed_formats, updated_by) 
-- SELECT id, '["json", "markdown"]', 1 FROM users WHERE role = 'user' AND user_level = 'standard';

-- INSERT INTO user_export_permissions (user_id, allowed_formats, updated_by) 
-- SELECT id, '["json", "markdown", "pdf"]', 1 FROM users WHERE role = 'user' AND user_level = 'premium';

-- 注释：管理员用户默认拥有所有格式权限，无需插入记录
