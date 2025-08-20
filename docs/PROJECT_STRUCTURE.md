# 📁 项目目录结构说明

## 🎯 **整理后的规范目录结构**

```
AI-CodeAudit-Aug/
├── 📄 README.md                    # 项目说明文档
├── 🚀 main.py                      # 主入口文件 - 统一命令行接口
├── ⚙️ setup.py                     # 安装配置文件
├── 📋 pyproject.toml               # 项目配置文件
├── 🧪 pytest.ini                  # 测试配置文件
├── 📝 CHANGELOG.md                 # 更新日志
│
├── 🧠 ai_code_audit/               # 核心代码包
│   ├── __init__.py                 # 包初始化，主要审计入口
│   ├── __main__.py                 # 模块入口，支持 python -m ai_code_audit
│   │
│   ├── 🔍 analysis/                # 分析模块
│   │   ├── confidence_calculator.py    # 六维度置信度计算
│   │   ├── cross_file_analyzer.py      # 跨文件关联分析
│   │   ├── context_analyzer.py         # 项目上下文分析
│   │   ├── frontend_optimizer.py       # 前端代码优化
│   │   └── frontend_backend_mapper.py  # 前后端关联映射
│   │
│   ├── 🔎 audit/                   # 审计模块
│   │   ├── project_analyzer.py         # 项目分析器
│   │   └── file_filter.py              # 智能文件过滤
│   │
│   ├── ⚙️ config/                  # 配置模块
│   │   ├── security_rules.yaml         # 安全规则配置
│   │   └── framework_rules.yaml        # 框架特定规则
│   │
│   ├── 🎯 core/                    # 核心模块
│   │   └── base.py                     # 基础类定义
│   │
│   ├── 🤖 llm/                     # LLM模块
│   │   ├── manager.py                  # LLM管理器（核心）
│   │   ├── providers/                  # LLM提供商
│   │   └── prompts/                    # 提示词模板
│   │
│   ├── 📝 templates/               # 模板模块
│   │   ├── security_audit_chinese.py   # 中文安全审计模板
│   │   └── owasp_top_10_2021.py       # OWASP Top 10模板
│   │
│   └── 🛠️ utils/                   # 工具模块
│       └── __init__.py                 # 工具函数
│
├── ⚙️ config/                      # 配置文件目录
│   ├── config.yaml                     # 主配置文件
│   ├── examples/                       # 配置示例
│   └── templates/                      # 配置模板
│
├── 📚 docs/                        # 文档目录
│   ├── guides/                         # 使用指南
│   ├── development/                    # 开发文档
│   ├── design/                         # 设计文档
│   └── reports/                        # 各种报告文档
│       ├── feature_integration_status_report.md
│       ├── frontend_optimization_implementation_report.md
│       └── cross_file_analysis_final_report.md
│
├── 🧪 tests/                       # 测试代码目录
│   ├── unit/                           # 单元测试
│   ├── integration/                    # 集成测试
│   ├── fixtures/                       # 测试数据
│   ├── reports/                        # 测试报告
│   └── test_*.py                       # 各种测试文件
│
├── 📁 examples/                    # 示例项目目录
│   ├── test_oa-system/                 # 测试用OA系统
│   ├── sample_projects/                # 示例项目
│   └── qdbcrm_full_audit.py           # 特定项目审计脚本
│
├── 🛠️ tools/                       # 工具脚本目录
│   └── performance_analyzer.py         # 性能分析工具
│
├── 📊 reports/                     # 生成的报告目录
│   ├── audit_report_*.json            # JSON格式审计报告
│   └── audit_report_*.md              # Markdown格式审计报告
│
├── 📝 logs/                        # 日志文件目录
│   ├── audit_log.txt                  # 审计日志
│   └── .gitkeep                       # 保持目录存在
│
├── 🗂️ temp/                        # 临时文件目录
│   ├── *.json                         # 临时审计结果
│   └── .gitkeep                       # 保持目录存在
│
└── 🏗️ scripts/                     # 构建和部署脚本
    ├── __init__.py
    └── init_database.py               # 数据库初始化脚本
```

## 🎯 **目录功能说明**

### **📁 核心代码目录 (ai_code_audit/)**

- **analysis/**: 各种分析算法和逻辑
  - 置信度计算、跨文件分析、前端优化等核心分析功能
  
- **audit/**: 审计相关功能
  - 项目分析器、文件过滤器等审计工具
  
- **config/**: 配置管理
  - 安全规则、框架规则等配置文件
  
- **llm/**: LLM相关功能
  - LLM管理器、提供商接口、提示词模板
  
- **templates/**: 审计模板
  - 各种审计模板和规则定义

### **📁 支持目录**

- **config/**: 外部配置文件
- **docs/**: 完整的项目文档
- **tests/**: 全面的测试代码
- **examples/**: 示例项目和脚本
- **tools/**: 辅助工具和脚本
- **reports/**: 生成的审计报告
- **logs/**: 系统日志文件
- **temp/**: 临时文件存储

## 🚀 **主要入口文件**

### **1. main.py - 主入口**
```bash
# 直接调用
python main.py /path/to/project --all

# 支持丰富的命令行参数
python main.py /path/to/project --no-cross-file --verbose
```

### **2. ai_code_audit/__main__.py - 模块入口**
```bash
# 模块调用方式
python -m ai_code_audit /path/to/project --all
```

### **3. ai_code_audit/__init__.py - 编程接口**
```python
# 编程调用方式
from ai_code_audit import audit_project
results = await audit_project("/path/to/project")
```

## 📋 **清理成果**

### **✅ 已删除的废弃文件**
- `audit_any_project.py` - 被main.py替代
- `run_audit.py` - 废弃的旧入口
- `example_usage.py` - 废弃的示例
- `complete_test.py` - 废弃的测试文件

### **✅ 已整理的文件**
- **测试文件** → `tests/` 目录
- **工具文件** → `tools/` 目录  
- **文档文件** → `docs/reports/` 目录
- **临时文件** → `temp/` 目录
- **日志文件** → `logs/` 目录
- **配置文件** → `config/` 目录

### **✅ 已规范的结构**
- 清晰的模块分离
- 统一的命名规范
- 完整的文档体系
- 规范的测试结构

## 🎯 **使用方式**

现在项目结构清晰，使用更加简单：

```bash
# 基本使用
python main.py /path/to/project

# 完整功能
python main.py /path/to/project --all --verbose

# 模块调用
python -m ai_code_audit /path/to/project --all
```

**项目现在拥有清晰、规范、易维护的目录结构！** 🎉
