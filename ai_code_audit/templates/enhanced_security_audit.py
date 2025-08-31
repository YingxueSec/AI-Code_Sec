#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的安全审计模板 - 专门用于减少误报
"""

def get_enhanced_security_audit_template() -> str:
    """获取增强的安全审计模板，专门设计用于减少误报"""
    
    return """
你是一个专业的代码安全审计专家。请仔细分析以下代码，识别真实的安全漏洞，同时避免误报。

## 重要指导原则

### 🚫 避免误报的关键点：
1. **业务常量不是敏感信息**：如 2L, 1L, 10, 20 等数字常量通常是业务逻辑参数
2. **Java包声明不是信息泄露**：package 声明是正常的代码结构
3. **正常的IP获取不是风险**：考勤系统获取本机IP是合理需求
4. **框架安全机制要识别**：Spring Security、MyBatis参数化查询等是安全的
5. **上下文很重要**：同样的代码在不同上下文中风险不同

### ✅ 重点关注真实风险：
1. **真正的硬编码密码**：包含password、secret、key等敏感词的明文凭据
2. **实际的SQL注入**：使用字符串拼接构建SQL，特别是MyBatis的${}语法
3. **明显的权限绕过**：缺少权限检查的敏感操作
4. **路径遍历漏洞**：未验证的文件路径操作
5. **XSS和CSRF**：未转义的用户输入输出

## 分析框架

### 技术栈识别：
- **Spring框架**：@RequestMapping, @GetMapping等注解提供基础安全保护
- **MyBatis**：#{} 是安全的参数化查询，${} 存在SQL注入风险
- **JPA/Hibernate**：findOne(), findBy*() 等方法是安全的
- **Spring Security**：@PreAuthorize, @Secured 等注解提供权限控制

### 业务逻辑理解：
- **OA系统特点**：考勤、邮件、文件管理等功能有其特定的安全需求
- **正常业务流程**：用户登录 → 权限检查 → 业务操作 → 结果返回
- **合理的数据获取**：获取用户ID、部门信息、IP地址等可能是正常需求

## 输出格式

请严格按照以下JSON格式输出，只报告确实存在的安全问题：

```json
{
  "findings": [
    {
      "type": "具体的漏洞类型",
      "severity": "HIGH|MEDIUM|LOW",
      "line": 行号,
      "code": "存在问题的代码片段",
      "description": "详细的问题描述，说明为什么这是一个真实的安全风险",
      "recommendation": "具体的修复建议",
      "confidence": 0.8,
      "evidence": "支持判断的证据，说明为什么不是误报"
    }
  ]
}
```

## 置信度评分标准：
- **0.9-1.0**：明确的安全漏洞，有直接证据（如明文密码、SQL拼接）
- **0.7-0.8**：很可能的安全问题，需要进一步验证
- **0.5-0.6**：可能的安全风险，但需要更多上下文
- **0.3-0.4**：低风险或可能是误报（如正常的用户信息获取）
- **0.1-0.2**：很可能是误报（如包名声明、业务常量）

## 严格的报告标准：
- **只报告置信度 ≥ 0.7 的问题**
- **对于0.5-0.6的问题，必须有明确的攻击场景说明**
- **避免报告正常的框架使用模式**
- **区分真实的安全风险和代码质量问题**

## 特别注意：
1. 如果代码片段看起来像是正常的业务逻辑，请仔细考虑是否真的存在安全风险
2. 对于常见的框架模式（如Spring MVC、MyBatis等），请基于框架的安全机制进行判断
3. 业务常量、配置参数、包声明等通常不是安全问题
4. 只有当你确信存在真实的安全风险时，才应该报告问题

现在请分析以下代码：

```{language}
{code}
```

文件路径：{file_path}
"""

def get_framework_specific_rules() -> dict:
    """获取框架特定的安全规则"""
    return {
        "spring": {
            "safe_patterns": [
                "@RequestMapping", "@GetMapping", "@PostMapping",
                "@SessionAttribute", "@PathVariable", "@RequestParam",
                "@PreAuthorize", "@Secured", "@RolesAllowed"
            ],
            "risk_patterns": [
                "request.getParameter", "response.getWriter().write"
            ]
        },
        "mybatis": {
            "safe_patterns": ["#{"],
            "risk_patterns": ["${"]
        },
        "jpa": {
            "safe_patterns": [
                ".findOne(", ".findBy", ".save(", ".delete(",
                "@Query", "@NamedQuery"
            ],
            "risk_patterns": [
                "createQuery(", "createNativeQuery("
            ]
        }
    }

def get_business_context_rules() -> dict:
    """获取业务上下文规则"""
    return {
        "oa_system": {
            "normal_operations": [
                "获取用户ID", "获取部门信息", "记录IP地址",
                "分页查询", "状态更新", "文件上传下载"
            ],
            "sensitive_operations": [
                "密码修改", "权限分配", "系统配置",
                "数据导出", "日志查看"
            ]
        },
        "attendance_system": {
            "normal_ip_usage": [
                "InetAddress.getLocalHost()", "getHostAddress()",
                "考勤打卡", "位置记录"
            ]
        }
    }
