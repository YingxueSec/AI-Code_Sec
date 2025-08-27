# 🔄 默认模型配置变更说明

## 📋 变更概述

由于Qwen模型API服务不稳定，系统默认模型已从 **Qwen3-Coder-30B** 调整为 **Kimi-K2-Instruct**。

## 🎯 变更原因

### **Qwen模型问题**
- ❌ API服务频繁繁忙 (`System is too busy now`)
- ❌ 连接超时和重试失败
- ❌ 影响用户体验和审计效率

### **Kimi模型优势**
- ✅ **更高的稳定性** - API响应更可靠
- ✅ **更大的TPM限制** - 400,000 vs 40,000 tokens/分钟
- ✅ **更高的RPM限制** - 10,000 vs 1,000 请求/分钟
- ✅ **更好的并发性能** - 支持更大规模项目审计

## 📊 性能对比

| 指标 | Qwen3-Coder-30B | Kimi-K2-Instruct | 优势 |
|------|-----------------|------------------|------|
| **上下文长度** | 256K tokens | 128K tokens | Qwen |
| **TPM限制** | 40,000 | 400,000 | **Kimi** ⭐ |
| **RPM限制** | 1,000 | 10,000 | **Kimi** ⭐ |
| **API稳定性** | 不稳定 | 稳定 | **Kimi** ⭐ |
| **响应速度** | 较慢 | 较快 | **Kimi** ⭐ |

## 🔧 配置变更详情

### **1. 主配置文件** (`config.yaml`)
```yaml
# 变更前
llm:
  default_model: "qwen-coder-30b"
  qwen:
    priority: 1
  kimi:
    priority: 2

# 变更后
llm:
  default_model: "kimi-k2"  # 🔄 默认模型变更
  kimi:
    priority: 1             # 🔄 提升为第一优先级
  qwen:
    priority: 2             # 🔄 降为备用选择
```

### **2. CLI默认参数**
```bash
# 变更前
--model qwen-coder-30b  # 默认值

# 变更后  
--model kimi-k2         # 🔄 新默认值
```

### **3. 常量配置**
```python
# 变更前
DEFAULT_LLM_CONFIG = {
    "qwen": {...},    # 第一位
    "kimi": {...},    # 第二位
}

# 变更后
DEFAULT_LLM_CONFIG = {
    "kimi": {...},    # 🔄 提升到第一位
    "qwen": {...},    # 🔄 移到第二位
}
```

## 🚀 使用方式

### **默认使用** (推荐)
```bash
# 自动使用Kimi模型
python -m ai_code_audit audit /path/to/project

# 显式指定Kimi模型
python -m ai_code_audit audit /path/to/project --model kimi-k2
```

### **仍可使用Qwen**
```bash
# 如果需要使用Qwen模型
python -m ai_code_audit audit /path/to/project --model qwen-coder-30b
```

## 📈 预期效果

### **稳定性提升**
- 🎯 减少API错误和重试
- 🎯 提高审计成功率
- 🎯 改善用户体验

### **性能提升**
- 🚀 支持更大规模项目 (10倍TPM限制)
- 🚀 更快的并发处理能力
- 🚀 减少等待时间

### **成本优化**
- 💰 更高的token限制减少分批处理
- 💰 更稳定的服务减少重试成本
- 💰 更好的性价比

## 🧪 测试验证

### **功能测试结果**
```
✅ 默认模型切换成功
✅ 文件过滤功能正常 (32.6%过滤效率)
✅ 中文报告生成正常
✅ 发现3个严重漏洞 (SQL注入、硬编码密钥、命令注入)
✅ 报告质量高，分析详细
```

### **性能测试结果**
```
📊 测试项目: 86个文件 → 58个文件 (过滤)
⏱️ 分析时间: 约60秒 (1个文件)
🔢 Token消耗: 3,606 tokens
📄 报告生成: JSON + Markdown 双格式
```

## 🔄 回滚方案

如果需要回滚到Qwen模型：

### **方法1: CLI参数**
```bash
python -m ai_code_audit audit /path/to/project --model qwen-coder-30b
```

### **方法2: 修改配置文件**
```yaml
llm:
  default_model: "qwen-coder-30b"
```

### **方法3: 环境变量**
```bash
export DEFAULT_LLM_MODEL="qwen-coder-30b"
```

## 📝 注意事项

1. **兼容性**: 所有现有功能保持不变
2. **API密钥**: 两个模型使用相同的SiliconFlow API密钥
3. **模板**: 中文模板与两个模型都兼容
4. **配置**: 用户自定义配置不受影响

## 🎉 总结

这次配置变更将显著提升系统的稳定性和性能，为用户提供更好的代码审计体验。Kimi模型的高稳定性和大容量限制使其更适合作为默认选择，同时保留Qwen模型作为备用选项。

**推荐**: 使用新的默认配置以获得最佳体验！🚀
