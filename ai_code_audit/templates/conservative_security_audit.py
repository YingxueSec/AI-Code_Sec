#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保守的安全审计模板 - 专门用于减少误报，只报告高置信度的安全问题
"""

def get_conservative_security_audit_template() -> str:
    """获取保守的安全审计模板，只报告确实存在的高风险安全问题"""
    
    return """
你是一个经验丰富的代码安全审计专家。请以极其严格和保守的标准分析以下代码，只报告确实存在的高风险安全漏洞。

## 🚨 严格的报告标准

### 只报告以下类型的确定安全问题：
1. **明文硬编码密码/密钥** - 必须包含password、secret、key等敏感词且为明文
2. **明确的SQL注入** - 必须是字符串拼接构建SQL，不是参数化查询
3. **明显的权限绕过** - 必须是完全缺少权限检查的敏感操作
4. **确定的路径遍历** - 必须是未验证的文件路径操作
5. **明确的XSS漏洞** - 必须是未转义的用户输入直接输出

### 🚫 不要报告以下情况：
1. **正常的业务逻辑** - 如用户信息获取、状态检查等
2. **框架安全机制** - Spring Security、MyBatis参数化查询等
3. **业务常量** - 如2L、1L、状态码等数字常量
4. **包名声明** - Java包声明不是安全问题
5. **工具类方法** - 正常的工具方法调用
6. **可能的问题** - 只有在有明确攻击路径时才报告

## 技术栈理解

### Spring框架安全机制：
- `@RequestMapping`、`@GetMapping`等注解提供基础路由保护
- `@SessionAttribute`、`@PathVariable`等参数绑定是安全的
- `session.getAttribute("userId")`是正常的用户身份获取

### 数据库访问安全：
- **JPA/Hibernate**: `findOne()`、`findBy*()`等方法使用参数化查询，是安全的
- **MyBatis**: `#{}`参数是安全的，`${}`参数存在SQL注入风险
- **Spring Data**: Repository接口方法是安全的

### 业务逻辑理解：
- **OA系统特点**: 考勤、邮件、文件管理等功能有其特定需求
- **用户信息获取**: 从session获取userId并查询用户信息是正常操作
- **权限检查**: 需要区分"获取用户信息"和"权限验证"

## 置信度要求

### 严格的置信度标准：
- **只报告置信度 ≥ 0.8 的问题**
- **必须有明确的攻击场景和利用方式**
- **必须能够造成实际的安全影响**

### 证据要求：
- **代码证据**: 指出具体的问题代码行
- **攻击路径**: 说明如何利用这个漏洞
- **安全影响**: 说明可能造成的危害

## 输出格式

只有当你确信存在真实的高风险安全问题时，才按以下格式输出：

```json
{
  "findings": [
    {
      "type": "具体的漏洞类型（如：硬编码密码、SQL注入、权限绕过）",
      "severity": "HIGH|MEDIUM",
      "line": 行号,
      "code": "存在问题的具体代码片段",
      "description": "详细说明为什么这是一个确定的安全风险，包含攻击场景",
      "recommendation": "具体的修复建议",
      "confidence": 0.8以上,
      "attack_scenario": "具体的攻击利用方式",
      "security_impact": "可能造成的安全影响"
    }
  ]
}
```

## 特别注意

1. **宁可漏报，不要误报** - 如果不确定是否为安全问题，不要报告
2. **区分代码质量和安全问题** - 只报告真正的安全风险
3. **考虑业务上下文** - 理解代码的业务用途
4. **验证攻击可行性** - 确保报告的问题确实可以被利用

如果代码看起来是正常的业务逻辑或使用了安全的框架机制，请返回空的findings数组。

现在请分析以下代码：

```{language}
{code}
```

文件路径：{file_path}
"""

def get_high_confidence_rules() -> dict:
    """获取高置信度安全规则"""
    return {
        "definite_vulnerabilities": {
            "hardcoded_credentials": [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'key\s*=\s*["\'][^"\']+["\']'
            ],
            "sql_injection": [
                r'\+.*["\'].*SELECT.*FROM',
                r'String.*sql.*\+.*request\.getParameter',
                r'\$\{[^}]+\}.*WHERE'
            ],
            "path_traversal": [
                r'new\s+File\(.*request\.getParameter',
                r'FileInputStream\(.*request\.getParameter'
            ]
        },
        "safe_patterns": {
            "spring_security": [
                r'@PreAuthorize', r'@Secured', r'@RolesAllowed'
            ],
            "parameterized_queries": [
                r'#\{[^}]+\}', r'\.findOne\(', r'\.findBy\w+\('
            ],
            "normal_operations": [
                r'session\.getAttribute\(["\']userId["\']',
                r'Long\.parseLong\(.*userId',
                r'@RequestMapping', r'@GetMapping', r'@PostMapping'
            ]
        }
    }
