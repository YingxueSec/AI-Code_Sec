# 📁 项目目录整理方案

## 🎯 **整理目标**
- 清晰的目录结构
- 文档分类管理
- 测试文件统一
- 临时文件清理
- 专业的项目布局

## 📋 **新目录结构**

```
AI-CodeAudit-Aug/
├── 📁 ai_code_audit/           # 核心代码包
│   ├── analysis/               # 分析引擎
│   ├── audit/                  # 审计核心
│   ├── cli/                    # 命令行接口
│   ├── core/                   # 核心模型
│   ├── database/               # 数据库层
│   ├── detection/              # 检测模块
│   ├── llm/                    # LLM集成
│   ├── templates/              # 模板系统
│   └── validation/             # 验证模块
├── 📁 docs/                    # 文档目录
│   ├── design/                 # 设计文档
│   ├── development/            # 开发文档
│   ├── releases/               # 发布说明
│   ├── reports/                # 审计报告
│   └── guides/                 # 使用指南
├── 📁 tests/                   # 测试目录
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   ├── fixtures/               # 测试数据
│   └── reports/                # 测试报告
├── 📁 examples/                # 示例项目
│   ├── test_cross_file/        # 跨文件测试项目
│   └── sample_projects/        # 其他示例
├── 📁 scripts/                 # 工具脚本
│   ├── setup/                  # 安装脚本
│   ├── maintenance/            # 维护脚本
│   └── utilities/              # 工具脚本
├── 📁 assets/                  # 资源文件
│   ├── diagrams/               # 架构图
│   └── images/                 # 图片资源
├── 📁 config/                  # 配置文件
│   ├── templates/              # 配置模板
│   └── examples/               # 配置示例
├── 📄 README.md                # 主要说明
├── 📄 CHANGELOG.md             # 变更日志
├── 📄 LICENSE                  # 许可证
├── 📄 pyproject.toml           # 项目配置
├── 📄 requirements.txt         # 依赖列表
└── 📄 .gitignore               # Git忽略
```

## 🔄 **文件移动计划**

### **1. 文档整理**
```bash
# 创建docs目录结构
mkdir -p docs/{design,development,releases,reports,guides}

# 移动设计文档
mv AI-CodeAudit-System-Design.md docs/design/
mv Database-Implementation.md docs/design/
mv Feasibility-Analysis.md docs/design/

# 移动开发文档
mv Development-Guide.md docs/development/
mv Development-Implementation-Plan.md docs/development/
mv README_Development.md docs/development/

# 移动发布文档
mv RELEASE_NOTES_v2.0.0.md docs/releases/
mv BACKUP_AND_BRANCH_INFO.md docs/releases/

# 移动报告文档
mv *Audit_Report*.md docs/reports/
mv *Optimization*.md docs/reports/
mv *Comparison*.md docs/reports/

# 移动指南文档
mv CONFIGURATION_GUIDE.md docs/guides/
mv Enhanced-Audit-Strategy.md docs/guides/
```

### **2. 测试文件整理**
```bash
# 创建测试目录结构
mkdir -p tests/{integration,fixtures,reports}

# 移动测试报告
mv test_*.html tests/reports/
mv test_*.json tests/reports/
mv test_*.md tests/reports/

# 移动集成测试
mv test_*.py tests/integration/
```

### **3. 示例项目整理**
```bash
# 创建示例目录
mkdir -p examples/sample_projects

# 移动测试项目
mv test_cross_file examples/
```

### **4. 资源文件整理**
```bash
# 创建资源目录
mkdir -p assets/{diagrams,images}

# 移动图表文件
mv svg/ assets/diagrams/
mv *.xml assets/diagrams/
```

### **5. 配置文件整理**
```bash
# 创建配置目录
mkdir -p config/{templates,examples}

# 移动配置文件
mv config.yaml config/examples/
```

### **6. 临时文件清理**
```bash
# 删除临时和缓存文件
rm -rf cache/
rm -rf __pycache__/
rm -rf .pytest_cache/
rm -f *.pyc
rm -f debug_*.py
rm -f check_*.py
rm -f setup_*.py
```
