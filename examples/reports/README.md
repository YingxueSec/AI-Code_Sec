# 📊 报告生成功能说明

## 🎯 功能概述

AI代码审计系统现在支持自动生成中文安全审计报告，包含JSON和Markdown两种格式。

## 📋 报告特性

### ✨ 中文化报告
- 完全中文的漏洞分析和描述
- 中文日期格式 (2025年08月18日)
- 中文严重程度分布统计
- 专业的中文安全术语

### 📊 双格式输出
- **JSON格式**: 结构化数据，便于程序处理
- **Markdown格式**: 人类友好，便于阅读和分享

### 🔧 自动生成
- 默认自动生成报告到 `./reports` 目录
- 智能文件命名: `audit_report_{timestamp}_{project_name}`
- 支持自定义输出目录和格式

## 📁 报告结构

### Markdown报告包含:
```markdown
# 安全审计报告

## 项目信息
- 项目路径、生成时间、分析文件数

## 摘要  
- 发现漏洞总数
- 严重程度分布统计

## 详细分析
- 逐文件漏洞分析
- OWASP分类和CWE编号
- 攻击场景和业务影响
- 具体修复方案

## 报告元数据
- 使用模型、消耗Token
- 免责声明和使用建议
```

### JSON报告包含:
```json
[
  {
    "file": "filename.py",
    "language": "python", 
    "analysis": "详细的中文漏洞分析...",
    "model_used": "qwen",
    "tokens_used": 2677
  }
]
```

## 🚀 使用方式

### 自动生成报告
```bash
# 使用默认中文模板，自动生成报告
python -m ai_code_audit.cli.main audit /path/to/project

# 显式指定中文模板
python -m ai_code_audit.cli.main audit /path/to/project --template security_audit_chinese
```

### 手动指定输出
```bash
# 仍支持手动指定输出文件
python -m ai_code_audit.cli.main audit /path/to/project -o custom_report.json
```

## ⚙️ 配置选项

在 `config.yaml` 中可配置:

```yaml
advanced:
  reports:
    # 自动生成设置
    auto_generate_reports: true
    default_formats: ["json", "markdown"]
    default_output_dir: "./reports"
    filename_template: "audit_report_{timestamp}_{project_name}"
    
    # 报告内容设置
    include_code_snippets: true
    max_snippet_length: 500
    include_fix_suggestions: true
    severity_threshold: "medium"
```

## 📈 示例输出

生成的报告文件:
```
reports/
├── audit_report_20250818_152825_.json    # JSON格式
└── audit_report_20250818_152825_.md      # Markdown格式
```

## 🎯 技术特点

- **完整性**: 修复了max_tokens限制，确保报告完整
- **专业性**: 包含OWASP分类、CWE编号、攻击场景
- **实用性**: 提供具体的修复代码示例
- **本地化**: 完全中文化的专业安全报告

## 📝 注意事项

- 报告目录 `./reports` 默认被 `.gitignore` 忽略
- 大项目建议使用Kimi模型以获得更高的TPM限制
- 可通过配置调整报告格式和内容详细程度
