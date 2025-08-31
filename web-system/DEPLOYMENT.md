# AI代码审计系统 - 生产环境部署指南

## 🚀 快速部署

### 1. 系统要求

**最低配置：**
- CPU: 2核心
- 内存: 4GB RAM
- 存储: 20GB SSD
- 系统: Ubuntu 20.04+ / CentOS 8+ / Debian 11+

**推荐配置：**
- CPU: 4核心
- 内存: 8GB RAM
- 存储: 50GB SSD
- 系统: Ubuntu 22.04 LTS

### 2. 环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以应用docker组权限
newgrp docker
```

### 3. 项目部署

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd web-system

# 2. 生成安全配置
cd scripts
python3 generate-secrets.py
cd ..

# 3. 配置环境变量
mv .env.secure .env
# 编辑 .env 文件，修改域名和API密钥等配置

# 4. 初始化环境
./deploy.sh init

# 5. 启动服务
./deploy.sh start

# 6. 检查服务状态
./deploy.sh status
```

### 4. 访问系统

- **前端地址**: http://your-domain.com
- **API文档**: http://your-domain.com:8000/docs
- **管理员账户**: 见生成的 `.env` 文件中的配置

## 🔧 详细配置

### 环境变量配置

主要配置文件：`.env`

```bash
# 数据库配置
MYSQL_ROOT_PASSWORD=<生成的强密码>
MYSQL_USER=ai_audit
MYSQL_PASSWORD=<生成的强密码>
MYSQL_DATABASE=ai_code_audit_prod

# Redis配置
REDIS_PASSWORD=<生成的强密码>

# JWT配置
SECRET_KEY=<生成的JWT密钥>

# AI API配置（必需）
AI_API_KEY=<你的AI API密钥>

# 域名配置
DOMAIN_NAME=yourdomain.com
SSL_EMAIL=admin@yourdomain.com
```

### SSL证书配置

#### 1. 使用Let's Encrypt（推荐）

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 2. 使用自签名证书（仅测试）

```bash
# 创建SSL目录
mkdir -p ./ssl

# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/private.key \
  -out ./ssl/certificate.crt \
  -subj "/C=CN/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

### 反向代理配置

创建 `nginx/conf.d/default.conf`：

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL配置
    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 前端代理
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## 🛡️ 安全配置

### 1. 防火墙设置

```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw deny 3306   # 禁止外部访问MySQL
sudo ufw deny 6379   # 禁止外部访问Redis

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. 系统安全

```bash
# 禁用root登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 安装fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 自动安全更新
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. 数据库安全

```bash
# 在容器中运行MySQL安全脚本
docker-compose exec mysql mysql_secure_installation
```

## 📊 监控和日志

### 1. 系统监控

```bash
# 安装监控工具
sudo apt install htop iotop nethogs

# 检查系统资源
htop
df -h
free -h
```

### 2. 容器监控

```bash
# 查看容器状态
docker-compose ps

# 查看容器资源使用
docker stats

# 查看日志
./deploy.sh logs
./deploy.sh logs backend
./deploy.sh logs frontend
```

### 3. 日志管理

```bash
# 配置日志轮转
sudo tee /etc/logrotate.d/ai-audit << EOF
/var/log/ai_audit/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 app app
}
EOF
```

## 💾 备份和恢复

### 1. 自动备份

```bash
# 创建备份脚本
sudo tee /etc/cron.daily/ai-audit-backup << 'EOF'
#!/bin/bash
cd /path/to/web-system
./deploy.sh backup
EOF

sudo chmod +x /etc/cron.daily/ai-audit-backup
```

### 2. 手动备份

```bash
# 备份数据
./deploy.sh backup

# 备份配置文件
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml nginx/
```

### 3. 数据恢复

```bash
# 恢复数据库
./deploy.sh restore backups/backup_20231201_120000.sql.gz

# 恢复配置
tar -xzf config-backup-20231201.tar.gz
```

## 🔄 更新和维护

### 1. 系统更新

```bash
# 更新应用
git pull
./deploy.sh update

# 更新Docker镜像
docker-compose pull
./deploy.sh restart
```

### 2. 数据库维护

```bash
# 优化数据库
docker-compose exec mysql mysqlcheck -u root -p --optimize --all-databases

# 查看数据库状态
docker-compose exec mysql mysql -u root -p -e "SHOW PROCESSLIST;"
```

### 3. 清理维护

```bash
# 清理Docker
docker system prune -a

# 清理日志
sudo journalctl --vacuum-time=7d

# 清理旧备份
find ./backups -name "backup_*.sql.gz" -mtime +30 -delete
```

## 🚨 故障排除

### 1. 常见问题

**问题：服务无法启动**
```bash
# 检查端口占用
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# 检查Docker状态
sudo systemctl status docker
docker-compose logs
```

**问题：数据库连接失败**
```bash
# 检查MySQL状态
docker-compose exec mysql mysql -u root -p -e "SELECT 1;"

# 检查网络连接
docker network ls
docker-compose exec backend ping mysql
```

**问题：前端无法访问**
```bash
# 检查Nginx配置
docker-compose exec frontend nginx -t

# 检查代理配置
curl -I http://localhost/api/health
```

### 2. 性能优化

```bash
# 优化MySQL配置
# 编辑 mysql/my.cnf
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
query_cache_size = 128M

# 优化Redis配置
# 编辑 redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

## 📞 技术支持

- **文档**: 查看项目README.md
- **问题**: 提交GitHub Issues
- **社区**: 加入技术交流群

---

**⚠️ 重要提醒**：
1. 生产环境部署前请仔细测试
2. 定期备份重要数据
3. 及时更新系统和依赖
4. 监控系统运行状态
5. 遵循安全最佳实践
