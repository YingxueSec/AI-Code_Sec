# 🎉 发布说明 - AI代码安全审计系统 Web版

## 📦 v2.6.0 "权限管控与监控增强版" (2025-01-01)

### 🎯 重大特性

#### ✨ 导出权限管理系统
- **细粒度权限控制**: 支持JSON、Markdown、PDF、HTML四种格式的独立权限设置
- **管理员权限面板**: 可视化的用户导出权限管理界面
- **动态权限检查**: 前端实时获取用户权限，动态显示可用导出选项
- **权限继承机制**: 基于用户等级的默认权限分配
- **操作日志记录**: 完整的导出操作审计轨迹

#### 📊 Token使用监控与统计
- **实时监控看板**: 每日Token消耗量趋势图表
- **用户级别统计**: 个人Token使用历史和排行
- **成本分析报告**: AI服务调用成本预估和预算控制
- **使用量预警**: Token使用量异常检测和通知
- **数据导出功能**: Token使用数据的多格式导出

#### 🔐 增强的安全特性
- **邀请码描述字段**: 支持为邀请码添加用途说明
- **权限检查优化**: 后端API权限验证机制增强
- **数据验证加强**: Pydantic模型验证规则完善
- **错误处理改进**: 更友好的错误信息和异常处理

### 🔧 技术改进

#### 后端优化
```python
# 新增导出权限服务
class ExportPermissionService:
    @staticmethod
    async def get_user_allowed_formats(db: AsyncSession, user_id: int) -> List[str]
    @staticmethod
    async def set_user_export_permission(db: AsyncSession, user_id: int, allowed_formats: List[str], admin_id: int) -> bool
    @staticmethod
    async def check_export_permission(db: AsyncSession, user_id: int, format: str) -> bool
```

#### 前端组件增强
```typescript
// ExportButton组件动态权限加载
const ExportButton: React.FC<ExportButtonProps> = ({ taskId }) => {
  const [allowedFormats, setAllowedFormats] = useState<ExportFormat[]>([]);
  
  useEffect(() => {
    loadAllowedFormats();
  }, []);
  
  // 根据权限动态显示导出选项
  if (allowedFormats.length === 1) {
    return <Button>{/* 单一格式直接按钮 */}</Button>;
  }
  
  return <Dropdown>{/* 多格式下拉菜单 */}</Dropdown>;
};
```

#### 数据库结构更新
```sql
-- 新增用户导出权限表
CREATE TABLE user_export_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    allowed_formats JSON NOT NULL,
    updated_by BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 新增导出操作日志表
CREATE TABLE export_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    export_format VARCHAR(20) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    ip_address VARCHAR(45),
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 🐛 问题修复

#### 关键Bug修复
- **修复图表权限错误**: 解决用户活跃度图表的`position: middle`配置问题
- **修复导出按钮显示**: 替换硬编码导出按钮为动态权限控制组件
- **修复API响应验证**: 解决邀请码API的datetime验证错误
- **修复CORS配置**: 优化跨域请求处理和错误响应
- **修复数据库关联**: 解决用户导出权限的关联查询问题

#### 界面体验优化
- **统一错误提示**: 标准化的错误信息展示机制
- **加载状态优化**: 改进数据加载的用户体验
- **权限提示完善**: 当用户无权限时的友好提示信息
- **表格性能优化**: 大数据量表格的分页和虚拟滚动

### 📊 性能提升

#### 前端性能
- **组件懒加载**: 图表组件按需加载，减少初始包大小
- **状态管理优化**: Zustand store结构优化，减少不必要的重渲染
- **API请求缓存**: 用户权限等静态数据的客户端缓存
- **图表渲染优化**: Ant Design Charts配置简化，提升渲染性能

#### 后端性能
- **数据库查询优化**: 添加复合索引，优化关联查询性能
- **异步处理增强**: 更多I/O操作改为异步处理
- **缓存策略改进**: Redis缓存在权限检查中的应用
- **SQL注入防护**: 参数化查询和ORM使用规范

### 🔄 API变更

#### 新增API端点
```http
# 导出权限管理
GET    /api/v1/admin/export/permissions      # 获取所有用户导出权限
POST   /api/v1/admin/export/permissions/{user_id}  # 设置用户导出权限
DELETE /api/v1/admin/export/permissions/{user_id}  # 重置用户导出权限
POST   /api/v1/admin/export/permissions/batch      # 批量设置导出权限

# 导出操作日志
GET    /api/v1/admin/export/logs           # 获取导出操作日志
GET    /api/v1/admin/export/stats          # 获取导出统计信息

# 用户导出权限查询
GET    /api/v1/audit/export/formats        # 获取当前用户允许的导出格式

# Token使用统计
GET    /api/v1/token-usage/user-stats      # 获取用户Token使用统计
GET    /api/v1/token-usage/admin-stats     # 获取管理员Token统计概览
```

#### API响应格式更新
```json
// 导出格式权限响应
{
  "allowed_formats": [
    {
      "format": "json",
      "name": "JSON",
      "description": "结构化数据格式",
      "icon": "file-text"
    }
  ],
  "user_level": "free",
  "user_role": "user"
}

// Token使用统计响应
{
  "daily_breakdown": [
    {
      "date": "2025-01-01",
      "total_tokens": 1500,
      "api_calls": 25,
      "average_tokens_per_call": 60
    }
  ],
  "summary": {
    "total_tokens": 45000,
    "total_calls": 750,
    "period_days": 30
  }
}
```

### 🚀 部署改进

#### Docker配置优化
```yaml
# docker-compose.yml 增强
version: '3.8'
services:
  web-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### 环境配置模板
```bash
# .env.production 模板
DATABASE_URL=mysql+aiomysql://user:password@db:3306/ai_code_audit_web
SECRET_KEY=your-256-bit-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI模型配置
OPENAI_API_KEY=sk-your-openai-key
QWEN_API_KEY=your-qwen-key

# Redis配置
REDIS_URL=redis://redis:6379/0

# CORS配置
CORS_ORIGINS=["http://localhost","https://yourdomain.com"]
```

### 📋 升级指南

#### 从v2.5.0升级到v2.6.0

1. **数据库迁移**:
```sql
-- 执行新表创建脚本
mysql -u root -p ai_code_audit_web < create_export_permission_tables.sql

-- 为邀请码表添加描述字段
ALTER TABLE invitation_codes ADD COLUMN description VARCHAR(255) DEFAULT '';
```

2. **环境变量更新**:
```bash
# 添加新的环境变量
echo "REDIS_URL=redis://localhost:6379/0" >> .env
echo "MAX_EXPORT_SIZE=50MB" >> .env
```

3. **前端依赖更新**:
```bash
cd frontend
npm install  # 安装新的依赖包
npm run build  # 重新构建生产版本
```

4. **配置文件更新**:
- 更新Docker配置文件
- 检查Nginx配置
- 验证CORS设置

### ⚠️ 破坏性变更

#### API变更
- **导出API权限检查**: 所有导出相关API现在需要权限验证
- **邀请码模型更新**: 新增`description`字段，可能影响现有的邀请码创建逻辑

#### 前端组件变更
- **ExportButton组件**: 接口变更，需要传入`taskId`参数
- **权限检查机制**: 组件渲染前需要获取用户权限信息

### 🔮 下一版本预告 (v2.7.0)

#### 计划特性
- **多语言支持**: 国际化(i18n)支持，英文界面
- **主题定制**: 支持暗色主题和企业品牌定制
- **实时通知**: WebSocket实时通知系统
- **API限流**: 更完善的API访问频率控制
- **数据备份**: 自动化数据备份和恢复机制

#### 性能优化计划
- **前端**: 实现更激进的代码分割和缓存策略
- **后端**: 引入消息队列处理异步任务
- **数据库**: 分库分表支持和读写分离

---

### 🙏 致谢

感谢所有贡献者和用户的反馈，让这个版本能够更好地服务于代码安全审计的需求。

### 📞 技术支持

如遇到升级问题，请：
1. 查阅 [升级文档](DEPLOYMENT.md)
2. 提交 [GitHub Issue](https://github.com/YingxueSec/AI-Code_Sec/issues)
3. 加入技术交流群获取支持

---

**发布时间**: 2025年1月1日  
**发布状态**: 稳定版 (Stable)  
**兼容性**: 向下兼容v2.5.0  
**推荐升级**: ✅ 强烈推荐
