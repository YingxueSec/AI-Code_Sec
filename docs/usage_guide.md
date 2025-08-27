# AI代码安全审计系统 - 使用指南

## 🚀 快速开始

### 基本命令
```bash
# 最简单的使用方式
python main.py /path/to/project

# 指定输出文件
python main.py /path/to/project --output my_audit_results.json

# 详细输出模式（推荐）
python main.py /path/to/project --verbose --output results.json
```

## 📋 完整参数表格

### 必需参数
| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `project_path` | 路径 | 要审计的项目路径 | `/path/to/project` |

### 输出控制参数
| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--output` | `-o` | 字符串 | `audit_results.json` | 输出文件名 |
| `--no-report` | - | 开关 | `False` | 不生成Markdown报告 |
| `--verbose` | `-v` | 开关 | `False` | 详细输出模式（显示时间统计） |
| `--quiet` | - | 开关 | `False` | 静默模式，只输出结果 |

### 分析控制参数
| 参数 | 短参数 | 类型 | 默认值 | 可选值 | 说明 |
|------|--------|------|--------|--------|------|
| `--template` | `-t` | 字符串 | `owasp_top_10_2021` | `owasp_top_10_2021`, `security_audit_chinese`, `custom` | 审计模板 |
| `--max-files` | `-m` | 整数 | `500` | 任意正整数 | 最大审计文件数 |
| `--all` | - | 开关 | `False` | - | 审计所有文件，忽略max-files限制 |
| `--quick` | - | 开关 | `False` | - | 快速扫描模式 |

### 功能开关参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--no-cross-file` | 开关 | `False` | 禁用跨文件关联分析 |
| `--no-frontend-opt` | 开关 | `False` | 禁用前端代码优化 |
| `--no-confidence-calc` | 开关 | `False` | 禁用置信度计算 |
| `--no-filter` | 开关 | `False` | 禁用智能文件过滤 |
| `--no-filter-stats` | 开关 | `False` | 不显示文件过滤统计 |

### 高级选项参数
| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `--include-extensions` | 列表 | - | 包含的文件扩展名 | `--include-extensions .java .py .js` |
| `--exclude-extensions` | 列表 | - | 排除的文件扩展名 | `--exclude-extensions .txt .md` |
| `--include-paths` | 列表 | - | 包含的路径模式 | `--include-paths src/ lib/` |
| `--exclude-paths` | 列表 | - | 排除的路径模式 | `--exclude-paths test/ docs/` |
| `--min-confidence` | 浮点数 | `0.3` | 最小置信度阈值 | `--min-confidence 0.5` |
| `--max-confidence` | 浮点数 | `1.0` | 最大置信度阈值 | `--max-confidence 0.9` |

### 调试选项参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--debug` | 开关 | `False` | 启用调试模式（强制串行分析） |
| `--dry-run` | 开关 | `False` | 试运行模式，不执行实际分析 |
| `--profile` | 开关 | `False` | 启用性能分析 |
| `--no-timing` | 开关 | `False` | 禁用时间统计显示 |

## 💡 常用命令示例

### 基础使用
```bash
# 基本审计
python main.py /path/to/project

# 指定输出文件
python main.py /path/to/project --output security_report.json

# 详细模式（推荐客户使用）
python main.py /path/to/project --verbose --output detailed_report.json
```

### 模板选择
```bash
# 使用中文模板（推荐中文用户）
python main.py /path/to/project --template security_audit_chinese

# 使用OWASP Top 10模板（默认）
python main.py /path/to/project --template owasp_top_10_2021

# 使用自定义模板
python main.py /path/to/project --template custom
```

### 文件控制
```bash
# 限制分析文件数量
python main.py /path/to/project --max-files 100

# 分析所有文件
python main.py /path/to/project --all

# 只分析特定类型文件
python main.py /path/to/project --include-extensions .java .py .js

# 排除特定类型文件
python main.py /path/to/project --exclude-extensions .txt .md .json
```

### 路径过滤
```bash
# 只分析特定目录
python main.py /path/to/project --include-paths src/ lib/ api/

# 排除特定目录
python main.py /path/to/project --exclude-paths test/ docs/ node_modules/

# 组合使用
python main.py /path/to/project \
  --include-paths src/ \
  --exclude-paths src/test/ \
  --include-extensions .java .py
```

### 功能控制
```bash
# 禁用跨文件分析（提高速度）
python main.py /path/to/project --no-cross-file

# 禁用前端优化（分析所有前端代码）
python main.py /path/to/project --no-frontend-opt

# 禁用智能过滤（分析所有文件）
python main.py /path/to/project --no-filter

# 组合禁用多个功能
python main.py /path/to/project \
  --no-cross-file \
  --no-frontend-opt \
  --no-confidence-calc
```

### 置信度控制
```bash
# 只显示高置信度问题
python main.py /path/to/project --min-confidence 0.7

# 过滤置信度范围
python main.py /path/to/project \
  --min-confidence 0.5 \
  --max-confidence 0.9
```

### 性能优化
```bash
# 快速扫描模式
python main.py /path/to/project --quick

# 禁用时间统计（提高性能）
python main.py /path/to/project --no-timing

# 静默模式（最快）
python main.py /path/to/project --quiet --no-timing
```

### 调试和测试
```bash
# 调试模式（串行分析，详细日志）
python main.py /path/to/project --debug --verbose

# 试运行（不实际分析）
python main.py /path/to/project --dry-run

# 性能分析
python main.py /path/to/project --profile --verbose
```

## 🎯 推荐配置

### 客户生产环境（推荐）
```bash
python main.py /path/to/project \
  --template security_audit_chinese \
  --verbose \
  --output security_audit_report.json \
  --max-files 500
```

### CI/CD集成
```bash
python main.py /path/to/project \
  --template owasp_top_10_2021 \
  --quiet \
  --output ci_security_report.json \
  --max-files 200 \
  --min-confidence 0.6
```

### 快速检查
```bash
python main.py /path/to/project \
  --quick \
  --no-timing \
  --max-files 50 \
  --output quick_scan.json
```

### 深度分析
```bash
python main.py /path/to/project \
  --all \
  --verbose \
  --template security_audit_chinese \
  --min-confidence 0.3 \
  --output comprehensive_audit.json
```

## 📊 输出文件说明

### JSON结果文件
- **文件名**: 通过`--output`参数指定
- **格式**: JSON格式，包含详细的漏洞信息
- **内容**: 项目信息、发现的问题、置信度评分、时间统计等

### Markdown报告文件
- **文件名**: 自动生成，在JSON文件名基础上添加`_report.md`
- **格式**: Markdown格式，适合阅读和分享
- **内容**: 格式化的审计报告，包含摘要、详细问题列表、修复建议等

### 时间统计信息
当使用`--verbose`参数时，会显示详细的时间统计：
- 各步骤耗时
- 缓存命中情况
- 性能优化效果
- LLM调用统计

## ⚠️ 注意事项

1. **路径格式**: 支持相对路径和绝对路径
2. **文件权限**: 确保对项目目录有读取权限
3. **输出目录**: 确保对输出目录有写入权限
4. **网络连接**: 需要稳定的网络连接访问LLM API
5. **缓存目录**: 系统会在当前目录创建`cache/`目录存储缓存文件
