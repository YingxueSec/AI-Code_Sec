# AI代码审计系统 - 全新版本

## 项目概述

这是一个基于大语言模型(LLM)的智能代码安全审计系统，采用分段式审计策略和智能上下文管理，支持深度的代码安全分析。

### 核心特性

- 🧠 **智能分段审计**: AI理解项目架构后，按功能模块进行独立深度审计
- 🔍 **主动代码检索**: AI根据审计需求主动请求相关代码文件
- 🚀 **多模型支持**: 集成硅基流动Qwen和MoonshotAI Kimi模型
- 📊 **智能报告生成**: 生成详细的安全审计报告和修复建议
- ⚡ **高性能处理**: 支持并行审计和智能缓存机制
- 🛠️ **CLI友好**: 完整的命令行界面，便于集成和自动化

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                      │
├─────────────────────────────────────────────────────────────┤
│                  Command Processing Layer                   │
├─────────────────────────────────────────────────────────────┤
│                   Project Analysis Layer                    │
├─────────────────────────────────────────────────────────────┤
│                    Context Management                       │
├─────────────────────────────────────────────────────────────┤
│                      LLM Integration                        │
├─────────────────────────────────────────────────────────────┤
│                    Report Generation                        │
└─────────────────────────────────────────────────────────────┘
```

## 核心设计理念

### 分段式审计策略
1. **项目全局理解**: AI首先分析整个项目的架构和结构
2. **功能模块分离**: 将项目按功能模块划分，每个模块独立审计
3. **上下文隔离**: 每个功能模块使用独立的对话上下文
4. **主动代码检索**: AI根据审计需求主动请求相关代码文件

### 智能上下文管理
- **项目缓存机制**: 缓存项目基础信息，便于跨会话复用
- **动态代码加载**: 根据审计需求动态加载相关代码片段
- **关联性分析**: 自动识别代码间的依赖关系和调用链

## 快速开始

### 环境要求
- Python 3.9+
- Poetry (包管理器)
- MySQL 8.0+
- Git

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd ai-code-audit

# 2. 安装依赖
poetry install

# 3. 配置数据库和API密钥
# 创建MySQL数据库
mysql -u root -p"jackhou." -e "CREATE DATABASE ai_code_audit_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# API密钥已内置在配置中（硅基流动提供）
# Qwen: sk-ejzylvzgcfnlxgvctpbgnnqginfossvyoifynqhqbaurvkuo
# Kimi: sk-gzkhahnbkjsvrerhxbtzzfuctexesqkmmbgyaylhitynvdri

# 4. 初始化配置
ai-audit config init
```

### 基本使用

```bash
# 初始化项目审计
ai-audit init /path/to/your/project

# 扫描项目结构
ai-audit scan --output-format json

# 查看识别的功能模块
ai-audit modules list

# 审计特定模块
ai-audit audit module authentication --model qwen

# 审计所有模块
ai-audit audit all --parallel --model qwen

# 查看审计报告
ai-audit report show latest --format html

# 导出审计报告
ai-audit report export latest --format pdf
```

## 支持的编程语言

- Python
- JavaScript/TypeScript
- Java
- Go
- Rust
- C/C++

## 支持的LLM模型

### 硅基流动 - Qwen/Qwen3-Coder-30B-A3B-Instruct
- **特点**: 专业代码理解能力强，适合代码结构分析和漏洞识别
- **上下文长度**: 32K tokens
- **适用场景**: 代码漏洞检测、安全模式识别
- **API提供商**: 硅基流动

### 硅基流动 - moonshotai/Kimi-K2-Instruct
- **特点**: 长上下文处理能力，适合大型项目整体分析
- **上下文长度**: 128K tokens
- **适用场景**: 项目架构分析、复杂业务逻辑审计
- **API提供商**: 硅基流动

## 审计流程

### 阶段一: 项目全局分析
1. **项目结构扫描** - 扫描所有源代码文件，识别文件类型和依赖关系
2. **架构理解** - 分析项目的整体架构模式和关键组件
3. **功能模块划分** - 基于业务逻辑自动划分功能模块
4. **审计计划生成** - 生成针对性的审计计划和优先级

### 阶段二: 分模块深度审计
1. **上下文初始化** - 为每个模块创建独立的审计上下文
2. **AI主动检索** - AI分析需求并主动请求相关代码文件
3. **深度安全分析** - 进行漏洞识别、风险评估和代码质量分析
4. **结果整合输出** - 生成结构化的审计报告和修复建议

## 安全检测能力

### 支持的漏洞类型
- SQL注入 (CWE-89)
- 跨站脚本攻击 (CWE-79)
- 跨站请求伪造 (CWE-352)
- 命令注入 (CWE-78)
- 路径遍历 (CWE-22)
- 不安全的反序列化 (CWE-502)
- 身份认证绕过 (CWE-287)
- 权限控制缺陷 (CWE-285)
- 敏感信息泄露 (CWE-200)
- 不安全的加密实现 (CWE-327)

### 分析维度
- **代码层面**: 语法分析、模式匹配、数据流分析
- **架构层面**: 组件交互、权限模型、数据流向
- **业务层面**: 业务逻辑漏洞、流程完整性、状态管理

## 报告格式

### 支持的输出格式
- **JSON**: 结构化数据，便于程序处理
- **HTML**: 交互式网页报告，包含图表和导航
- **PDF**: 专业的审计报告文档
- **Markdown**: 轻量级文档格式

### 报告内容
- **执行摘要**: 高层次的风险概述和关键发现
- **详细发现**: 每个安全问题的详细描述和位置
- **风险评估**: 基于CVSS的风险等级评估
- **修复建议**: 具体的代码修复方案和最佳实践
- **合规检查**: 对照OWASP、CWE等标准的合规性分析

## 配置管理

### 配置文件结构
```yaml
llm:
  default_model: "qwen"
  models:
    qwen:
      api_endpoint: "https://api.siliconflow.cn/v1"
      api_key: "sk-ejzylvzgcfnlxgvctpbgnnqginfossvyoifynqhqbaurvkuo"
      model_name: "Qwen/Qwen3-Coder-30B-A3B-Instruct"
      max_tokens: 32768
    kimi:
      api_endpoint: "https://api.siliconflow.cn/v1"
      api_key: "sk-gzkhahnbkjsvrerhxbtzzfuctexesqkmmbgyaylhitynvdri"
      model_name: "moonshotai/Kimi-K2-Instruct"
      max_tokens: 128000

database:
  type: "mysql"
  host: "localhost"
  port: 3306
  username: "root"
  password: "jackhou."
  database: "ai_code_audit_system"
  charset: "utf8mb4"

audit:
  max_concurrent_sessions: 3
  cache_ttl: 86400
  supported_languages: ["python", "javascript", "java", "go"]

security_rules:
  sql_injection: true
  xss: true
  csrf: true
  authentication: true
  authorization: true
```

## 开发计划

### Phase 1: 基础框架 (2-3周)
- [x] 项目设计和架构规划
- [ ] CLI框架搭建
- [ ] 项目扫描器实现
- [ ] 配置管理系统
- [ ] LLM集成接口

### Phase 2: 核心功能 (3-4周)
- [ ] 架构分析器
- [ ] 功能模块识别
- [ ] 上下文管理器
- [ ] 审计流程引擎

### Phase 3: 高级特性 (2-3周)
- [ ] 智能代码检索
- [ ] 多模型支持
- [ ] 报告生成系统
- [ ] 缓存优化

### Phase 4: 测试优化 (1-2周)
- [ ] 单元测试覆盖
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档完善

## 技术栈

- **后端**: Python 3.9+, AsyncIO
- **CLI框架**: Click
- **代码解析**: Tree-sitter
- **HTTP客户端**: aiohttp
- **配置管理**: YAML, Pydantic
- **数据库**: MySQL 8.0+, SQLAlchemy, aiomysql
- **测试**: pytest, pytest-asyncio
- **代码质量**: Black, isort, flake8, mypy

## 文档结构

- `AI-CodeAudit-System-Design.md` - 详细的系统设计文档
- `Development-Guide.md` - 开发指南和项目结构
- `Implementation-Examples.md` - 核心组件实现示例
- `README.md` - 项目概述和使用说明

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 参与讨论

---

**注意**: 这是一个全新设计的AI代码审计系统，重点关注分段式审计和智能上下文管理。系统设计充分考虑了实际使用场景和性能要求，为代码安全审计提供了强大而灵活的解决方案。
