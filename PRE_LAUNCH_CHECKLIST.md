# 🚀 云端内测上线前检查清单

## ⚠️ **必须完成项目 (上线阻塞)**

### 🔐 **1. 安全加固 (P0 - 上线阻塞)**

#### 1.1 敏感信息安全
- [ ] **移除硬编码密钥**
  ```bash
  # 当前问题: config/config.yaml 中暴露API密钥
  kimi:
    api_key: "sk-kpepqjjtmxpcdhqcvrdekuroxvmpmphkfouhzbcbudbpzzzt"  # ❌ 暴露
  ```
  - [ ] 使用环境变量管理所有敏感信息
  - [ ] 实现配置文件加密
  - [ ] 清理Git历史中的敏感信息

#### 1.2 数据库安全
- [ ] **修改默认密码**
  ```sql
  -- 当前使用默认密码 "jackhou."
  ALTER USER 'root'@'localhost' IDENTIFIED BY '强密码';
  CREATE USER 'ai_audit'@'%' IDENTIFIED BY '复杂密码';
  ```
  - [ ] 创建专用数据库用户
  - [ ] 限制数据库访问权限
  - [ ] 启用SSL连接

#### 1.3 API安全
- [ ] **实现API限流**
  ```python
  # 必须添加限流保护
  @limiter.limit("100/minute")
  async def sensitive_endpoint():
      pass
  ```
  - [ ] 添加请求签名验证
  - [ ] 实现IP白名单
  - [ ] 启用HTTPS强制重定向

### 🛡️ **2. 生产环境配置 (P0)**

#### 2.1 环境变量配置
- [ ] **创建生产环境配置**
  ```bash
  # .env.production
  DATABASE_URL=mysql+asyncio://user:${STRONG_PASSWORD}@db:3306/ai_audit_prod
  JWT_SECRET_KEY=${RANDOM_32_CHAR_KEY}
  DEBUG=false
  LOG_LEVEL=INFO
  ```

#### 2.2 数据库配置
- [ ] **生产数据库设置**
  - [ ] 创建生产数据库实例
  - [ ] 配置备份策略
  - [ ] 设置连接池参数
  - [ ] 添加必要索引

#### 2.3 服务器配置
- [ ] **部署环境准备**
  - [ ] 配置防火墙规则
  - [ ] 设置SSL证书
  - [ ] 配置域名解析
  - [ ] 准备监控告警

### 📊 **3. 性能优化 (P0)**

#### 3.1 数据库优化
- [ ] **添加关键索引**
  ```sql
  CREATE INDEX idx_users_username ON users(username);
  CREATE INDEX idx_audit_tasks_user_status ON audit_tasks(user_id, status);
  CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
  ```

#### 3.2 前端优化
- [ ] **生产构建优化**
  ```bash
  # 确保生产构建正常
  cd web-system/frontend
  npm run build
  # 检查打包文件大小
  ```
  - [ ] 启用代码分割
  - [ ] 压缩静态资源
  - [ ] 配置CDN加速

### 🔧 **4. 系统稳定性 (P0)**

#### 4.1 错误处理
- [ ] **统一错误处理**
  ```python
  # 避免敏感信息泄露
  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      return JSONResponse(
          status_code=500,
          content={"detail": "内部服务器错误"}  # 不暴露详细错误
      )
  ```

#### 4.2 日志系统
- [ ] **配置生产日志**
  - [ ] 设置日志轮转
  - [ ] 过滤敏感信息
  - [ ] 配置日志聚合

#### 4.3 健康检查
- [ ] **实现健康检查端点**
  ```python
  @router.get("/health")
  async def health_check():
      # 检查数据库、Redis、AI服务连接状态
      return {"status": "healthy"}
  ```

### 🚀 **5. 部署配置 (P0)**

#### 5.1 Docker配置
- [ ] **优化Docker镜像**
  ```dockerfile
  # 多阶段构建，减少镜像大小
  FROM python:3.11-slim as builder
  # ... 构建阶段
  FROM python:3.11-slim as runtime
  # ... 运行阶段
  ```

#### 5.2 反向代理
- [ ] **配置Nginx**
  ```nginx
  # 生产Nginx配置
  server {
      listen 443 ssl http2;
      server_name your-domain.com;
      
      ssl_certificate /path/to/cert.pem;
      ssl_certificate_key /path/to/key.pem;
      
      location /api/ {
          proxy_pass http://backend:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }
  ```

## ⚡ **重要但非阻塞项目 (P1)**

### 📈 **监控告警**
- [ ] 实现基础监控 (CPU、内存、磁盘)
- [ ] 配置服务可用性监控
- [ ] 设置关键指标告警

### 🔍 **测试验证**
- [ ] 端到端功能测试
- [ ] 性能压力测试
- [ ] 安全渗透测试

### 📋 **用户体验**
- [ ] 优化加载速度
- [ ] 完善错误提示
- [ ] 添加用户指南

## 🛠️ **具体实施步骤**

### **第1天: 安全加固**
```bash
# 1. 清理敏感信息
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config/config.yaml' \
  --prune-empty --tag-name-filter cat -- --all

# 2. 创建安全配置
cp web-system/backend/env.example .env.production
# 编辑 .env.production，使用强密码和随机密钥

# 3. 更新代码读取环境变量
```

### **第2天: 数据库配置**
```sql
-- 1. 创建生产数据库
CREATE DATABASE ai_code_audit_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 创建专用用户
CREATE USER 'ai_audit_prod'@'%' IDENTIFIED BY 'STRONG_RANDOM_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_code_audit_prod.* TO 'ai_audit_prod'@'%';

-- 3. 执行数据库脚本
mysql -u ai_audit_prod -p ai_code_audit_prod < web-system/database_setup.sql
mysql -u ai_audit_prod -p ai_code_audit_prod < web-system/database_export_permissions.sql
mysql -u ai_audit_prod -p ai_code_audit_prod < web-system/database_user_specific_permissions.sql

-- 4. 添加生产索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_audit_tasks_user_status ON audit_tasks(user_id, status);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
```

### **第3天: 部署配置**
```bash
# 1. 构建生产镜像
cd web-system
docker build -t ai-audit-backend:prod ./backend
docker build -t ai-audit-frontend:prod ./frontend

# 2. 配置生产docker-compose
cp docker-compose.yml docker-compose.prod.yml
# 编辑生产配置

# 3. 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

### **第4天: 测试验证**
```bash
# 1. 功能测试
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin","password":"admin123"}'

# 2. 性能测试
ab -n 1000 -c 10 https://your-domain.com/api/v1/health

# 3. 安全检查
nmap -sV your-domain.com
```

## ✅ **上线检查清单**

### **技术检查**
- [ ] 所有API端点正常响应
- [ ] 数据库连接正常
- [ ] 文件上传功能正常
- [ ] 用户注册登录正常
- [ ] 审计功能正常运行
- [ ] 导出功能正常
- [ ] 权限控制正确

### **安全检查**
- [ ] 无硬编码敏感信息
- [ ] HTTPS强制启用
- [ ] API限流生效
- [ ] 权限控制正确
- [ ] 错误信息不泄露
- [ ] 日志记录正常

### **性能检查**
- [ ] 页面加载时间<3秒
- [ ] API响应时间<1秒
- [ ] 数据库查询优化
- [ ] 静态资源压缩
- [ ] CDN配置正确

### **监控检查**
- [ ] 健康检查端点正常
- [ ] 基础监控正常
- [ ] 告警配置正确
- [ ] 日志聚合正常

## 🚨 **风险评估**

### **高风险项 (必须解决)**
1. **硬编码API密钥** - 可能导致服务被滥用
2. **默认数据库密码** - 严重安全风险
3. **缺少API限流** - 可能导致服务被攻击
4. **错误信息泄露** - 可能暴露系统信息

### **中风险项 (建议解决)**
1. **缺少监控告警** - 故障发现延迟
2. **性能未优化** - 用户体验差
3. **备份策略缺失** - 数据丢失风险

### **低风险项 (可延后)**
1. **日志系统不完善** - 问题排查困难
2. **用户体验待优化** - 影响用户满意度

## 📅 **上线时间估算**

- **最快上线时间**: 3-4天 (仅完成P0项目)
- **推荐上线时间**: 1-2周 (完成P0+P1项目)
- **完整优化时间**: 3-4周 (包含所有优化)

## 🎯 **内测用户建议**

### **用户规模**
- **第一批**: 5-10个技术用户
- **第二批**: 20-30个业务用户
- **第三批**: 50-100个普通用户

### **功能限制**
- **文件大小**: 限制为10MB
- **并发审计**: 限制为3个任务
- **导出次数**: 每日限制10次
- **用户注册**: 仅通过邀请码

---

**⚠️ 重要提醒: 上述P0项目是上线的必要条件，任何一项未完成都不建议开放给用户使用！**
