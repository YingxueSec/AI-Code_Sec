# 🚀 AI代码安全审计系统 - 快速参考

## 基本语法
```bash
python main.py <项目路径> [选项]
```

## 📋 核心参数速查表

### 🎯 必需参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `project_path` | 项目路径 | `/path/to/project` |

### 📤 输出控制
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-o, --output` | `audit_results.json` | 输出文件名 |
| `-v, --verbose` | - | 详细模式（显示时间统计）⭐ |
| `--quiet` | - | 静默模式 |
| `--no-report` | - | 不生成Markdown报告 |

### 🔧 分析控制
| 参数 | 默认值 | 可选值 | 说明 |
|------|--------|--------|------|
| `-t, --template` | `owasp_top_10_2021` | `security_audit_chinese`, `custom` | 审计模板⭐ |
| `-m, --max-files` | `500` | 数字 | 最大文件数 |
| `--all` | - | - | 分析所有文件 |
| `--quick` | - | - | 快速模式 |

### ⚙️ 功能开关
| 参数 | 说明 | 建议 |
|------|------|------|
| `--no-cross-file` | 禁用跨文件分析 | 提速用 |
| `--no-frontend-opt` | 禁用前端优化 | 全面分析用 |
| `--no-confidence-calc` | 禁用置信度计算 | 提速用 |
| `--no-filter` | 禁用智能过滤 | 全面分析用 |
| `--no-timing` | 禁用时间统计 | 简洁输出用 |

### 🎛️ 高级选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `--include-extensions` | 包含文件类型 | `--include-extensions .java .py` |
| `--exclude-extensions` | 排除文件类型 | `--exclude-extensions .txt .md` |
| `--include-paths` | 包含路径 | `--include-paths src/ api/` |
| `--exclude-paths` | 排除路径 | `--exclude-paths test/ docs/` |
| `--min-confidence` | 最小置信度 | `--min-confidence 0.6` |

### 🐛 调试选项
| 参数 | 说明 | 用途 |
|------|------|------|
| `--debug` | 调试模式 | 问题排查 |
| `--dry-run` | 试运行 | 测试配置 |
| `--profile` | 性能分析 | 性能优化 |

## 🌟 推荐命令组合

### 👥 客户生产环境（推荐）
```bash
python main.py /path/to/project \
  --template security_audit_chinese \
  --verbose \
  --output security_report.json
```
**特点**: 中文报告 + 时间统计 + 完整功能

### ⚡ 快速检查
```bash
python main.py /path/to/project \
  --quick \
  --max-files 50 \
  --output quick_scan.json
```
**特点**: 快速扫描 + 限制文件数

### 🔍 深度分析
```bash
python main.py /path/to/project \
  --all \
  --no-filter \
  --verbose \
  --output deep_analysis.json
```
**特点**: 分析所有文件 + 无过滤 + 详细输出

### 🤖 CI/CD集成
```bash
python main.py /path/to/project \
  --quiet \
  --min-confidence 0.6 \
  --max-files 200 \
  --output ci_report.json
```
**特点**: 静默模式 + 高置信度 + 限制文件数

### 🎯 特定文件类型
```bash
python main.py /path/to/project \
  --include-extensions .java .py .js \
  --exclude-paths test/ docs/ \
  --output targeted_scan.json
```
**特点**: 指定文件类型 + 排除测试目录

## 📊 输出文件

### 自动生成的文件
- `{output}.json` - JSON格式详细结果
- `{output}_report.md` - Markdown格式报告
- `cache/` - 缓存目录（自动创建）

### 时间统计示例（使用--verbose）
```
============================================================
📊 时间统计报告
============================================================
配置加载                :     0.01秒 (  0.0%)
项目结构分析              :     0.00秒 (  0.0%)
文件过滤                :     0.01秒 (  0.0%)
AI模型初始化             :     0.00秒 (  0.0%)
代码分析总时间             :   189.27秒 (100.0%)
LLM调用总时间            :   396.30秒 (209.3%)
摘要生成                :     0.00秒 (  0.0%)
结果保存                :     0.00秒 (  0.0%)
总执行时间               :   189.31秒 (100.0%)
平均每文件分析时间           :    99.08秒
平均LLM调用时间           :    99.08秒
LLM调用次数             :        4次
缓存命中次数              :        0次
缓存命中率               :      0.0%
------------------------------------------------------------
💾 缓存统计:
缓存文件数               :        4个
缓存大小                :     0.1MB
有效缓存                :        4个
============================================================
```

## 🎨 模板说明

| 模板名称 | 语言 | 特点 | 适用场景 |
|----------|------|------|----------|
| `owasp_top_10_2021` | 英文 | OWASP标准 | 国际项目 |
| `security_audit_chinese` | 中文 | 中文报告 | 中文用户⭐ |
| `custom` | 自定义 | 可定制 | 特殊需求 |

## ⚡ 性能优化提示

### 🚀 提升速度
- 使用 `--quick` 快速模式
- 使用 `--max-files` 限制文件数
- 使用 `--no-cross-file` 禁用跨文件分析
- 使用 `--no-timing` 禁用时间统计

### 💾 利用缓存
- 重复分析同一项目时自动使用缓存
- 缓存命中可提升性能4000+倍
- 缓存24小时自动过期

### 🎯 精确分析
- 使用 `--include-extensions` 指定文件类型
- 使用 `--exclude-paths` 排除无关目录
- 使用 `--min-confidence` 过滤低置信度问题

## ❗ 常见问题

### Q: 如何只分析Java文件？
```bash
python main.py /path/to/project --include-extensions .java
```

### Q: 如何排除测试目录？
```bash
python main.py /path/to/project --exclude-paths test/ tests/ __tests__/
```

### Q: 如何获得中文报告？
```bash
python main.py /path/to/project --template security_audit_chinese
```

### Q: 如何加快分析速度？
```bash
python main.py /path/to/project --quick --max-files 100 --no-cross-file
```

### Q: 如何进行深度分析？
```bash
python main.py /path/to/project --all --no-filter --verbose
```

---
**💡 提示**: 使用 `--verbose` 参数可以看到详细的时间统计和缓存使用情况！
