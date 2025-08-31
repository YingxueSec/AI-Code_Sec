-- AI代码审计系统数据库初始化脚本
-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_code_audit_web DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_code_audit_web;

-- 用户表
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    user_level ENUM('free', 'standard', 'premium') NOT NULL DEFAULT 'free',
    daily_token_limit INT NOT NULL DEFAULT 1000,
    used_tokens_today INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_user_level (user_level),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 邀请码表
CREATE TABLE invitation_codes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    user_level ENUM('free', 'standard', 'premium') NOT NULL DEFAULT 'free',
    token_limit INT NOT NULL DEFAULT 1000,
    max_uses INT NOT NULL DEFAULT 1,
    used_count INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_code (code),
    INDEX idx_created_by (created_by),
    INDEX idx_expires_at (expires_at),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 审计任务表
CREATE TABLE audit_tasks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'pending',
    config_params JSON,
    error_message TEXT,
    total_files INT DEFAULT 0,
    analyzed_files INT DEFAULT 0,
    progress_percent DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_project_name (project_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 审计结果表
CREATE TABLE audit_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL UNIQUE,
    findings JSON,
    statistics JSON,
    summary TEXT,
    high_issues INT DEFAULT 0,
    medium_issues INT DEFAULT 0,
    low_issues INT DEFAULT 0,
    total_confidence DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES audit_tasks(id) ON DELETE CASCADE,
    INDEX idx_task_id (task_id),
    INDEX idx_high_issues (high_issues),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 审计文件表
CREATE TABLE audit_files (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT DEFAULT 0,
    analysis_result JSON,
    confidence_score DECIMAL(5,2) DEFAULT 0.00,
    status ENUM('pending', 'analyzed', 'skipped', 'error') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES audit_tasks(id) ON DELETE CASCADE,
    INDEX idx_task_id (task_id),
    INDEX idx_file_type (file_type),
    INDEX idx_status (status),
    INDEX idx_confidence_score (confidence_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 报告表
CREATE TABLE reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    report_name VARCHAR(255) NOT NULL,
    format ENUM('json', 'pdf', 'html', 'markdown') NOT NULL DEFAULT 'json',
    file_path TEXT,
    file_size BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES audit_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_task_id (task_id),
    INDEX idx_user_id (user_id),
    INDEX idx_format (format),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Token使用记录表
CREATE TABLE token_usage (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id BIGINT,
    tokens_consumed INT NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100),
    cost DECIMAL(10,4) DEFAULT 0.0000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES audit_tasks(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_task_id (task_id),
    INDEX idx_provider (provider),
    INDEX idx_created_at (created_at),
    INDEX idx_user_date (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 系统日志表
CREATE TABLE system_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at),
    INDEX idx_ip_address (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员用户（密码：admin123）
INSERT INTO users (username, email, password_hash, role, user_level, daily_token_limit) VALUES 
('admin', 'admin@ai-audit.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeH5ENbPlB4dT3sV2', 'admin', 'premium', 100000);

-- 创建第一个邀请码
INSERT INTO invitation_codes (code, user_level, token_limit, max_uses, created_by) VALUES 
('WELCOME2024', 'standard', 5000, 100, 1);

-- 创建Token使用统计视图
CREATE VIEW daily_token_stats AS
SELECT 
    user_id,
    DATE(created_at) as usage_date,
    SUM(tokens_consumed) as total_tokens,
    COUNT(*) as request_count,
    AVG(tokens_consumed) as avg_tokens_per_request
FROM token_usage 
GROUP BY user_id, DATE(created_at);

-- 创建用户统计视图
CREATE VIEW user_statistics AS
SELECT 
    u.id,
    u.username,
    u.user_level,
    u.daily_token_limit,
    u.used_tokens_today,
    COUNT(DISTINCT at.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN at.status = 'completed' THEN at.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN at.status = 'failed' THEN at.id END) as failed_tasks,
    COALESCE(SUM(ar.high_issues), 0) as total_high_issues,
    COALESCE(SUM(ar.medium_issues), 0) as total_medium_issues,
    COALESCE(SUM(ar.low_issues), 0) as total_low_issues
FROM users u
LEFT JOIN audit_tasks at ON u.id = at.user_id
LEFT JOIN audit_results ar ON at.id = ar.task_id
GROUP BY u.id;

-- 创建系统统计视图
CREATE VIEW system_dashboard AS
SELECT 
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as active_users,
    (SELECT COUNT(*) FROM users WHERE role = 'admin') as admin_users,
    (SELECT COUNT(*) FROM audit_tasks WHERE DATE(created_at) = CURDATE()) as today_tasks,
    (SELECT COUNT(*) FROM audit_tasks WHERE status = 'running') as running_tasks,
    (SELECT COUNT(*) FROM audit_tasks WHERE status = 'completed') as completed_tasks,
    (SELECT SUM(tokens_consumed) FROM token_usage WHERE DATE(created_at) = CURDATE()) as today_tokens,
    (SELECT COUNT(*) FROM invitation_codes WHERE is_active = TRUE) as active_invitations;
