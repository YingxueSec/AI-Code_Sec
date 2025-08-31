# AI代码安全审计系统 - 完整参数表格

## 📋 参数分类总览

| 分类 | 参数数量 | 主要功能 |
|------|----------|----------|
| 必需参数 | 1 | 指定项目路径 |
| 输出控制 | 4 | 控制输出格式和详细程度 |
| 分析控制 | 4 | 控制分析范围和模式 |
| 功能开关 | 5 | 启用/禁用特定功能 |
| 高级选项 | 6 | 精细化控制分析过程 |
| 调试选项 | 4 | 调试和性能分析 |
| **总计** | **24** | **完整功能覆盖** |

## 🎯 必需参数

| 参数名 | 类型 | 必需 | 说明 | 示例 |
|--------|------|------|------|------|
| `project_path` | 字符串 | ✅ | 要审计的项目路径 | `/home/user/myproject` |

## 📤 输出控制参数

| 参数名 | 短参数 | 类型 | 默认值 | 必需 | 说明 | 示例 |
|--------|--------|------|--------|------|------|------|
| `--output` | `-o` | 字符串 | `audit_results.json` | ❌ | 指定输出JSON文件名 | `--output my_report.json` |
| `--no-report` | - | 布尔 | `False` | ❌ | 不生成Markdown报告文件 | `--no-report` |
| `--verbose` | `-v` | 布尔 | `False` | ❌ | 启用详细输出模式，显示时间统计 | `--verbose` |
| `--quiet` | - | 布尔 | `False` | ❌ | 静默模式，最小化输出信息 | `--quiet` |

## 🔧 分析控制参数

| 参数名 | 短参数 | 类型 | 默认值 | 可选值 | 必需 | 说明 | 示例 |
|--------|--------|------|--------|--------|------|------|------|
| `--template` | `-t` | 字符串 | `owasp_top_10_2021` | `owasp_top_10_2021`, `security_audit_chinese`, `custom` | ❌ | 选择审计模板 | `--template security_audit_chinese` |
| `--max-files` | `-m` | 整数 | `500` | 任意正整数 | ❌ | 限制最大审计文件数量 | `--max-files 100` |
| `--all` | - | 布尔 | `False` | - | ❌ | 审计所有文件，忽略max-files限制 | `--all` |
| `--quick` | - | 布尔 | `False` | - | ❌ | 启用快速扫描模式 | `--quick` |

## ⚙️ 功能开关参数

| 参数名 | 类型 | 默认值 | 必需 | 说明 | 性能影响 | 示例 |
|--------|------|--------|------|------|----------|------|
| `--no-cross-file` | 布尔 | `False` | ❌ | 禁用跨文件关联分析 | 🚀 提速20-30% | `--no-cross-file` |
| `--no-frontend-opt` | 布尔 | `False` | ❌ | 禁用前端代码优化 | 📈 增加分析量 | `--no-frontend-opt` |
| `--no-confidence-calc` | 布尔 | `False` | ❌ | 禁用置信度计算 | 🚀 提速10-15% | `--no-confidence-calc` |
| `--no-filter` | 布尔 | `False` | ❌ | 禁用智能文件过滤 | 📈 大幅增加分析量 | `--no-filter` |
| `--no-filter-stats` | 布尔 | `False` | ❌ | 不显示文件过滤统计信息 | 💡 简化输出 | `--no-filter-stats` |

## 🎛️ 高级选项参数

| 参数名 | 类型 | 默认值 | 必需 | 说明 | 示例 | 注意事项 |
|--------|------|--------|------|------|------|----------|
| `--include-extensions` | 列表 | `None` | ❌ | 只分析指定扩展名的文件 | `--include-extensions .java .py .js` | 区分大小写 |
| `--exclude-extensions` | 列表 | `None` | ❌ | 排除指定扩展名的文件 | `--exclude-extensions .txt .md .json` | 优先级高于include |
| `--include-paths` | 列表 | `None` | ❌ | 只分析匹配路径模式的文件 | `--include-paths src/ lib/ api/` | 支持通配符 |
| `--exclude-paths` | 列表 | `None` | ❌ | 排除匹配路径模式的文件 | `--exclude-paths test/ docs/ node_modules/` | 优先级高于include |
| `--min-confidence` | 浮点数 | `0.3` | ❌ | 最小置信度阈值(0.0-1.0) | `--min-confidence 0.6` | 过滤低置信度问题 |
| `--max-confidence` | 浮点数 | `1.0` | ❌ | 最大置信度阈值(0.0-1.0) | `--max-confidence 0.9` | 过滤高置信度问题 |

## 🐛 调试选项参数

| 参数名 | 类型 | 默认值 | 必需 | 说明 | 影响 | 示例 |
|--------|------|--------|------|------|------|------|
| `--debug` | 布尔 | `False` | ❌ | 启用调试模式 | 🐌 强制串行分析，详细日志 | `--debug` |
| `--dry-run` | 布尔 | `False` | ❌ | 试运行模式，不执行实际分析 | 🚀 快速验证配置 | `--dry-run` |
| `--profile` | 布尔 | `False` | ❌ | 启用性能分析 | 📊 生成性能报告 | `--profile` |
| `--no-timing` | 布尔 | `False` | ❌ | 禁用时间统计显示 | 💡 简化输出 | `--no-timing` |

## 📊 参数优先级和冲突处理

### 优先级规则
| 高优先级 | 低优先级 | 处理方式 |
|----------|----------|----------|
| `--exclude-extensions` | `--include-extensions` | 排除优先 |
| `--exclude-paths` | `--include-paths` | 排除优先 |
| `--all` | `--max-files` | 忽略max-files |
| `--quiet` | `--verbose` | 静默优先 |
| `--debug` | 并行模式 | 强制串行 |

### 冲突组合
| 参数组合 | 结果 | 建议 |
|----------|------|------|
| `--verbose` + `--quiet` | 使用`--quiet` | 避免同时使用 |
| `--all` + `--max-files` | 忽略`--max-files` | 使用其中一个 |
| `--no-filter` + `--include-extensions` | 两者都生效 | 可以组合使用 |

## 🎨 模板详细说明

| 模板名称 | 语言 | 特点 | 检测重点 | 适用场景 | 性能 |
|----------|------|------|----------|----------|------|
| `owasp_top_10_2021` | 英文 | OWASP标准，国际通用 | OWASP Top 10漏洞 | 国际项目，英文团队 | 标准 |
| `security_audit_chinese` | 中文 | 中文报告，本土化 | 全面安全检查 | 中文用户，国内项目 | 标准 |
| `custom` | 自定义 | 可定制规则 | 用户定义 | 特殊需求，定制化 | 可变 |

## 📈 性能影响参数对比

| 参数 | 速度影响 | 准确性影响 | 资源消耗 | 推荐场景 |
|------|----------|------------|----------|----------|
| `--quick` | 🚀🚀🚀 提速50%+ | 📉 略降 | 💚 低 | 快速检查 |
| `--no-cross-file` | 🚀🚀 提速20-30% | 📉 降低 | 💚 低 | 单文件分析 |
| `--no-confidence-calc` | 🚀 提速10-15% | 📊 无影响 | 💚 低 | 简化输出 |
| `--max-files 100` | 🚀🚀 线性提速 | 📉 覆盖率降低 | 💚 低 | 大项目采样 |
| `--all` | 🐌🐌 可能很慢 | 📈 最全面 | 🔴 高 | 全面审计 |
| `--no-filter` | 🐌 增加分析量 | 📈 更全面 | 🔴 高 | 深度分析 |

## 💡 最佳实践组合

### 🏢 企业生产环境
```bash
python main.py /path/to/project \
  --template security_audit_chinese \
  --verbose \
  --output enterprise_audit.json \
  --max-files 500 \
  --min-confidence 0.5
```

### ⚡ CI/CD快速检查
```bash
python main.py /path/to/project \
  --quick \
  --quiet \
  --max-files 200 \
  --min-confidence 0.7 \
  --output ci_quick_scan.json
```

### 🔍 安全专家深度分析
```bash
python main.py /path/to/project \
  --all \
  --no-filter \
  --verbose \
  --template security_audit_chinese \
  --min-confidence 0.3 \
  --output security_expert_analysis.json
```

### 🎯 特定技术栈分析
```bash
python main.py /path/to/project \
  --include-extensions .java .jsp .xml \
  --include-paths src/ webapp/ \
  --exclude-paths test/ \
  --template owasp_top_10_2021 \
  --output java_web_audit.json
```

## ⚠️ 重要提醒

1. **路径格式**: 支持相对路径和绝对路径，Windows用户注意路径分隔符
2. **权限要求**: 需要对项目目录的读取权限和输出目录的写入权限
3. **网络依赖**: 需要稳定网络连接访问LLM API
4. **缓存机制**: 系统自动创建`cache/`目录，24小时TTL
5. **内存使用**: 大项目建议使用`--max-files`限制文件数量
6. **并发控制**: 默认最多3个文件并行分析，避免API限制
