-- AI代码审计系统 - 数据库初始化脚本
-- 创建默认管理员用户

USE ai_code_audit_prod;

-- 插入默认管理员用户（如果不存在）
INSERT IGNORE INTO users (
    username, 
    email, 
    password_hash, 
    role, 
    user_level,
    daily_token_limit,
    is_active,
    created_at
) VALUES (
    'admin',
    'admin@yourdomain.com',
    '$2b$12$39b28442d730065f9eaa67d5df2b99c610d4a70911a035d85bdf8ff451313926',
    'admin',
    'vip',
    100000,
    true,
    NOW()
);

-- 更新现有admin用户密码（如果存在）
UPDATE users 
SET password_hash = '$2b$12$39b28442d730065f9eaa67d5df2b99c610d4a70911a035d85bdf8ff451313926'
WHERE username = 'admin';
