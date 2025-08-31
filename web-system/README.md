# 🚀 AI代码安全审计系统 Web版 v2.6.0

基于AI大语言模型的智能代码安全审计系统的现代化Web界面，提供企业级的代码安全审计解决方案。

## ✨ 核心特性

### 🎯 智能审计引擎
- **AI驱动检测** - 基于先进的大语言模型进行深度代码分析
- **多层次扫描** - 语法检查、安全漏洞检测、业务逻辑分析
- **实时进度** - 可视化审计进度和状态监控
- **智能缓存** - 文件哈希缓存，避免重复分析

### 🔐 安全管理系统
- **用户权限管理** - 基于角色的访问控制(RBAC)
- **邀请码系统** - 可控的用户注册机制
- **导出权限控制** - 细粒度的报告导出权限管理
- **安全认证** - JWT令牌认证，密码强度验证

### 📊 数据分析看板
- **实时统计** - 用户活跃度、安全问题趋势分析
- **Token使用监控** - AI服务调用统计和成本分析
- **系统性能** - 审计任务完成率、系统负载监控
- **可视化图表** - 基于Ant Design Charts的数据可视化

### 🛠 企业级功能
- **多格式导出** - JSON、Markdown、PDF、HTML格式支持
- **任务管理** - 审计任务的创建、监控、取消、删除
- **历史记录** - 完整的审计历史和结果追溯
- **系统日志** - 详细的操作日志和审计轨迹

## 🏗 技术架构

### 前端技术栈
- **React 18** - 现代化前端框架
- **TypeScript** - 类型安全的JavaScript
- **Ant Design** - 企业级UI组件库
- **Zustand** - 轻量级状态管理
- **Ant Design Charts** - 专业数据可视化

### 后端技术栈
- **FastAPI** - 高性能Python Web框架
- **SQLAlchemy** - 异步ORM数据库操作
- **MySQL** - 企业级关系数据库
- **Pydantic** - 数据验证和序列化
- **JWT** - 安全的用户认证机制

### 部署技术
- **Docker** - 容器化部署
- **Docker Compose** - 多服务编排
- **Nginx** - 反向代理和静态资源服务
- **环境隔离** - 开发/生产环境配置分离

## 🚀 快速开始

### 开发环境启动

```bash
# 1. 克隆项目
git clone https://github.com/YingxueSec/AI-Code_Sec.git
cd AI-Code_Sec/web-system

# 2. 启动后端服务
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run_server.py

# 3. 启动前端服务
cd ../frontend
npm install
npm start

# 4. 访问系统
# 前端: http://localhost:3000
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### Docker部署

```bash
# 1. 配置环境变量
cp docker-env-template .env
# 编辑 .env 文件，设置数据库密码等

# 2. 启动服务
docker-compose up -d

# 3. 访问系统
# 系统地址: http://localhost
```

## 👥 默认账户

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 系统管理、用户管理、数据分析 |
| 普通用户 | user | user123 | 代码审计、查看报告 |

## 📖 使用指南

### 1. 代码审计流程

1. **上传代码** - 支持ZIP文件上传
2. **配置审计** - 选择审计模板和参数
3. **开始分析** - AI引擎进行深度代码分析
4. **查看结果** - 详细的安全问题报告
5. **导出报告** - 多格式报告导出

### 2. 系统管理

#### 用户管理
- 查看用户列表和状态
- 管理用户权限和等级
- 监控用户活跃度

#### 邀请码管理
- 创建带有权限控制的邀请码
- 设置邀请码有效期和使用次数
- 跟踪邀请码使用情况

#### 导出权限管理
- 为不同用户设置导出格式权限
- JSON、Markdown、PDF、HTML格式控制
- 导出日志和统计

### 3. 数据分析

#### 安全趋势分析
- 高中低危漏洞分布统计
- 时间维度的安全问题趋势
- 用户审计活跃度分析

#### Token使用监控
- AI服务调用统计
- 成本分析和预算控制
- 用户级别的使用量监控

## 🔧 配置说明

### 环境变量配置

```bash
# 数据库配置
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/ai_code_audit_web

# JWT配置
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI模型配置
OPENAI_API_KEY=your-openai-key
QWEN_API_KEY=your-qwen-key

# CORS配置
CORS_ORIGINS=["http://localhost:3000"]
```

### 数据库初始化

```sql
-- 创建数据库
CREATE DATABASE ai_code_audit_web CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 导入表结构
mysql -u root -p ai_code_audit_web < backend/create_export_permission_tables.sql
```

## 📊 系统架构图

```mermaid
graph TB
    A[用户浏览器] --> B[Nginx反向代理]
    B --> C[React前端应用]
    B --> D[FastAPI后端API]
    D --> E[MySQL数据库]
    D --> F[AI审计引擎]
    F --> G[文件存储系统]
    D --> H[Redis缓存]
    
    C --> |API调用| D
    D --> |数据持久化| E
    D --> |缓存操作| H
    F --> |文件分析| G
```

## 🛡 安全特性

### 认证与授权
- JWT令牌认证机制
- 基于角色的访问控制
- 会话管理和超时控制
- 密码强度验证

### 数据安全
- 数据库连接加密
- 敏感信息脱敏
- 审计日志记录
- 文件上传安全检查

### API安全
- CORS跨域保护
- 请求频率限制
- 输入数据验证
- SQL注入防护

## 📈 性能优化

### 前端优化
- 代码分割和懒加载
- 组件级别缓存
- 图片和资源压缩
- CDN静态资源加速

### 后端优化
- 异步I/O操作
- 数据库连接池
- Redis缓存策略
- 文件哈希去重

### 部署优化
- Docker多阶段构建
- Nginx静态资源缓存
- 数据库索引优化
- 监控和日志聚合

## 🤝 贡献指南

### 开发规范
- 遵循PEP 8 Python代码风格
- 使用ESLint和Prettier格式化前端代码
- 编写单元测试和集成测试
- 提供详细的代码注释

### 提交流程
1. Fork项目仓库
2. 创建功能分支
3. 提交代码更改
4. 编写测试用例
5. 发起Pull Request

### 问题反馈
- GitHub Issues: 报告Bug和功能建议
- GitHub Discussions: 技术讨论和经验分享
- Wiki文档: 详细的技术文档和教程

## 📝 更新日志

### v2.6.0 (2025-01-01)
- ✨ 新增导出权限管理系统
- ✨ 实现Token使用监控和统计
- ✨ 优化用户界面和交互体验
- 🐛 修复审计任务状态同步问题
- 🔧 改进Docker部署配置

### v2.5.0 (2024-12-15)
- ✨ 新增邀请码管理功能
- ✨ 实现数据分析看板
- ✨ 添加系统管理界面
- 🔧 优化数据库结构设计

### v2.0.0 (2024-12-01)
- 🚀 Web界面完全重构
- ✨ 基于React+FastAPI的现代化架构
- ✨ 用户认证和权限管理系统
- ✨ 可视化审计进度和结果展示

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- **项目主页**: https://github.com/YingxueSec/AI-Code_Sec
- **在线文档**: https://github.com/YingxueSec/AI-Code_Sec/wiki
- **问题反馈**: https://github.com/YingxueSec/AI-Code_Sec/issues
- **讨论社区**: https://github.com/YingxueSec/AI-Code_Sec/discussions

---

## 📞 联系方式

如有任何问题或建议，欢迎通过以下方式联系我们：

- **GitHub Issues**: 技术问题和Bug报告
- **Email**: support@yingxuesec.com
- **微信群**: 扫描二维码加入技术交流群

---

**🎉 感谢使用AI代码安全审计系统，让代码更安全！**
