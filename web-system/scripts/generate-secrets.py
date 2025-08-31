#!/usr/bin/env python3
"""
AI代码审计系统 - 安全配置生成脚本
用途：生成强密码和密钥，替换默认配置
"""

import secrets
import string
import hashlib
import os
import sys
from datetime import datetime

def generate_password(length=16, include_symbols=True):
    """生成强密码"""
    characters = string.ascii_letters + string.digits
    if include_symbols:
        characters += "!@#$%^&*"
    
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_secret_key(length=64):
    """生成JWT密钥"""
    return secrets.token_urlsafe(length)

def generate_hash(password):
    """生成密码hash"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_secure_config():
    """创建安全配置"""
    print("🔐 AI代码审计系统 - 安全配置生成器")
    print("=" * 50)
    
    # 生成各种密码和密钥
    configs = {
        # 数据库配置
        'mysql_root_password': generate_password(20),
        'mysql_user_password': generate_password(16),
        'redis_password': generate_password(16),
        
        # 应用配置
        'jwt_secret_key': generate_secret_key(64),
        'admin_password': generate_password(12, include_symbols=False),
        
        # 邮件配置
        'smtp_password': generate_password(16),
        
        # API密钥（示例）
        'api_encryption_key': generate_secret_key(32),
    }
    
    # 显示生成的配置
    print("\n📋 生成的安全配置：")
    print("-" * 50)
    
    for key, value in configs.items():
        print(f"{key:20}: {value}")
    
    # 生成环境变量文件
    env_content = f"""# AI代码审计系统 - 生产环境安全配置
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ⚠️ 请妥善保管此文件，不要提交到版本控制系统

# MySQL配置
MYSQL_ROOT_PASSWORD={configs['mysql_root_password']}
MYSQL_USER=ai_audit
MYSQL_PASSWORD={configs['mysql_user_password']}
MYSQL_DATABASE=ai_code_audit_prod

# Redis配置
REDIS_PASSWORD={configs['redis_password']}

# JWT配置
SECRET_KEY={configs['jwt_secret_key']}

# 默认管理员账户
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD={configs['admin_password']}
DEFAULT_ADMIN_EMAIL=admin@yourdomain.com

# 邮件配置
SMTP_PASSWORD={configs['smtp_password']}

# API加密密钥
API_ENCRYPTION_KEY={configs['api_encryption_key']}

# 环境配置
ENVIRONMENT=production
DEBUG=false
"""
    
    # 保存到文件
    output_file = "../.env.secure"
    try:
        with open(output_file, 'w') as f:
            f.write(env_content)
        print(f"\n✅ 安全配置已保存到: {output_file}")
    except Exception as e:
        print(f"\n❌ 保存文件失败: {e}")
        return False
    
    # 生成初始化SQL脚本
    sql_content = f"""-- AI代码审计系统 - 数据库初始化脚本
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
    '$2b$12${generate_hash(configs['admin_password'])}',
    'admin',
    'vip',
    100000,
    true,
    NOW()
);

-- 更新现有admin用户密码（如果存在）
UPDATE users 
SET password_hash = '$2b$12${generate_hash(configs['admin_password'])}'
WHERE username = 'admin';
"""
    
    sql_file = "../mysql/init/02-admin-user.sql"
    try:
        os.makedirs(os.path.dirname(sql_file), exist_ok=True)
        with open(sql_file, 'w') as f:
            f.write(sql_content)
        print(f"✅ 数据库初始化脚本已保存到: {sql_file}")
    except Exception as e:
        print(f"❌ 保存SQL文件失败: {e}")
    
    # 安全提示
    print("\n🛡️  安全提示：")
    print("-" * 30)
    print("1. 请立即更改所有默认密码")
    print("2. 将 .env.secure 文件重命名为 .env")
    print("3. 确保 .env 文件不被提交到版本控制")
    print("4. 定期更换密码和密钥")
    print("5. 启用防火墙和SSL证书")
    print("6. 配置日志监控和备份策略")
    
    print("\n🚀 部署步骤：")
    print("-" * 20)
    print("1. mv .env.secure .env")
    print("2. ./deploy.sh init")
    print("3. ./deploy.sh start")
    print("4. 访问 http://your-domain.com")
    print("5. 使用生成的管理员账户登录")
    
    return True

if __name__ == "__main__":
    try:
        success = create_secure_config()
        if success:
            print("\n🎉 安全配置生成完成！")
            sys.exit(0)
        else:
            print("\n💥 配置生成失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 发生错误: {e}")
        sys.exit(1)
