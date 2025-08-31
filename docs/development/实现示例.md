# AI代码审计系统 - 实现示例

## 核心数据模型定义

### core/models.py
```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class ProjectType(Enum):
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DESKTOP_APPLICATION = "desktop_application"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    UNKNOWN = "unknown"

class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class VulnerabilityType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    AUTHORIZATION_FAILURE = "authorization_failure"
    DATA_VALIDATION = "data_validation"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INSECURE_CRYPTO = "insecure_crypto"
    CODE_INJECTION = "code_injection"
    PATH_TRAVERSAL = "path_traversal"

@dataclass
class FileInfo:
    path: str
    absolute_path: str
    language: str
    size: int
    hash: str
    last_modified: float
    functions: List[str] = None
    classes: List[str] = None
    imports: List[str] = None

@dataclass
class DependencyInfo:
    name: str
    version: Optional[str]
    source: str  # npm, pip, cargo, etc.
    vulnerabilities: List[str] = None

@dataclass
class ProjectInfo:
    path: str
    name: str
    project_type: ProjectType
    files: List[FileInfo]
    dependencies: List[DependencyInfo]
    entry_points: List[str]
    languages: List[str]
    architecture_pattern: Optional[str] = None

@dataclass
class Module:
    name: str
    description: str
    files: List[str]
    entry_points: List[str]
    dependencies: List[str]
    business_logic: str
    risk_level: str

@dataclass
class SecurityFinding:
    id: str
    type: VulnerabilityType
    severity: SeverityLevel
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str
    confidence: float
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None

@dataclass
class AuditResult:
    module: Module
    findings: List[SecurityFinding]
    summary: Dict[str, Any]
    recommendations: List[str]
    audit_timestamp: datetime
    model_used: str
    session_id: str

@dataclass
class AuditContext:
    module: Module
    project_info: ProjectInfo
    security_rules: Dict[str, Any]
    code_index: Dict[str, Any]
    session_config: Dict[str, Any]

@dataclass
class CodeRequest:
    file_pattern: str
    reason: str
    priority: str
    context_depth: int

@dataclass
class AuditRequest:
    type: str
    context: AuditContext
    code_requests: List[CodeRequest]
    additional_params: Dict[str, Any]

@dataclass
class AuditResponse:
    findings: List[SecurityFinding]
    code_requests: List[CodeRequest]
    analysis_summary: str
    confidence_score: float
```

## 配置管理实现

### config/settings.py
```python
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LLMModelConfig:
    name: str
    api_endpoint: str
    api_key: str
    max_tokens: int
    temperature: float
    timeout: int = 30

@dataclass
class AuditConfig:
    max_concurrent_sessions: int
    cache_ttl: int
    supported_languages: List[str]
    security_rules: Dict[str, bool]
    output_formats: List[str]

@dataclass
class AppConfig:
    llm_models: Dict[str, LLMModelConfig]
    audit: AuditConfig
    cache_dir: str
    log_level: str

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 优先级：环境变量 > 用户目录 > 项目目录
        if 'AI_AUDIT_CONFIG' in os.environ:
            return os.environ['AI_AUDIT_CONFIG']
        
        user_config = Path.home() / '.ai-code-audit' / 'config.yaml'
        if user_config.exists():
            return str(user_config)
        
        return str(Path(__file__).parent / 'default.yaml')
    
    def _load_config(self) -> AppConfig:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            return self._parse_config(config_data)
        except FileNotFoundError:
            return self._create_default_config()
        except Exception as e:
            raise Exception(f"配置文件加载失败: {e}")
    
    def _parse_config(self, config_data: Dict[str, Any]) -> AppConfig:
        """解析配置数据"""
        llm_models = {}
        for name, model_config in config_data.get('llm', {}).get('models', {}).items():
            llm_models[name] = LLMModelConfig(
                name=name,
                api_endpoint=model_config['api_endpoint'],
                api_key=os.environ.get(model_config.get('api_key_env', f'{name.upper()}_API_KEY'), ''),
                max_tokens=model_config.get('max_tokens', 8192),
                temperature=model_config.get('temperature', 0.1),
                timeout=model_config.get('timeout', 30)
            )
        
        audit_config = AuditConfig(
            max_concurrent_sessions=config_data.get('audit', {}).get('max_concurrent_sessions', 3),
            cache_ttl=config_data.get('audit', {}).get('cache_ttl', 86400),
            supported_languages=config_data.get('audit', {}).get('supported_languages', []),
            security_rules=config_data.get('security_rules', {}),
            output_formats=config_data.get('audit', {}).get('output_formats', ['json', 'html'])
        )
        
        return AppConfig(
            llm_models=llm_models,
            audit=audit_config,
            cache_dir=config_data.get('cache_dir', './cache'),
            log_level=config_data.get('log_level', 'INFO')
        )
    
    def _create_default_config(self) -> AppConfig:
        """创建默认配置"""
        return AppConfig(
            llm_models={
                'qwen': LLMModelConfig(
                    name='qwen',
                    api_endpoint='https://api.siliconflow.cn/v1',
                    api_key='sk-ejzylvzgcfnlxgvctpbgnnqginfossvyoifynqhqbaurvkuo',
                    model_name='Qwen/Qwen3-Coder-30B-A3B-Instruct',
                    max_tokens=32768,
                    temperature=0.1
                ),
                'kimi': LLMModelConfig(
                    name='kimi',
                    api_endpoint='https://api.siliconflow.cn/v1',
                    api_key='sk-gzkhahnbkjsvrerhxbtzzfuctexesqkmmbgyaylhitynvdri',
                    model_name='moonshotai/Kimi-K2-Instruct',
                    max_tokens=128000,
                    temperature=0.1
                )
            },
            audit=AuditConfig(
                max_concurrent_sessions=3,
                cache_ttl=86400,
                supported_languages=['python', 'javascript', 'java', 'go'],
                security_rules={
                    'sql_injection': True,
                    'xss': True,
                    'csrf': True,
                    'authentication': True,
                    'authorization': True
                },
                output_formats=['json', 'html']
            ),
            cache_dir='./cache',
            log_level='INFO'
        )

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """加载配置的便捷函数"""
    manager = ConfigManager(config_path)
    return manager.config
```

## 提示工程模板

### llm/prompt_templates.py
```python
from typing import Dict, Any, List
from ai_code_audit.core.models import Module, ProjectInfo, VulnerabilityType

class AuditPromptTemplates:
    
    SYSTEM_PROMPT_TEMPLATE = """
你是一个专业的代码安全审计专家，具有以下专业能力：

🔍 **核心能力**
1. 深度理解各种编程语言的安全特性和常见漏洞模式
2. 识别OWASP Top 10和CWE常见安全风险
3. 分析代码架构和业务逻辑中的安全缺陷
4. 主动请求相关代码文件进行全面分析
5. 提供具体可行的修复建议和安全最佳实践

🎯 **当前审计任务**
- 项目名称: {project_name}
- 项目类型: {project_type}
- 审计模块: {module_name}
- 主要语言: {primary_language}
- 架构模式: {architecture_pattern}

📋 **审计重点**
{security_focus_areas}

🔧 **审计流程**
1. 分析模块的核心功能和业务逻辑
2. 识别关键的数据流和控制流
3. 主动请求需要审查的相关代码文件
4. 深度分析安全风险点和漏洞模式
5. 评估风险等级和影响范围
6. 生成详细的审计报告和修复建议

请严格按照专业的安全审计标准进行分析，确保不遗漏任何潜在的安全风险。
"""

    CODE_REQUEST_TEMPLATE = """
基于当前的审计上下文，我需要分析 **{audit_target}** 的安全风险。

**当前上下文信息：**
- 审计模块: {module_name}
- 已知入口点: {entry_points}
- 相关文件: {related_files}

请分析并告诉我需要查看哪些代码文件来完成这个审计任务。

**请以JSON格式返回你的代码请求：**
```json
{{
    "requests": [
        {{
            "file_pattern": "具体文件路径或匹配模式",
            "reason": "请求这个文件的具体原因",
            "priority": "high|medium|low",
            "context_depth": 1-5,
            "analysis_focus": "重点分析的方面"
        }}
    ],
    "analysis_strategy": "整体分析策略说明"
}}
```
"""

    VULNERABILITY_ANALYSIS_TEMPLATE = """
请对以下代码进行深度安全分析：

**文件信息：**
- 文件路径: {file_path}
- 编程语言: {language}
- 文件大小: {file_size} bytes
- 业务功能: {business_function}

**代码内容：**
```{language}
{code_content}
```

**分析要求：**
请重点关注以下安全风险类型：
{vulnerability_types}

**输出格式：**
对于每个发现的安全问题，请提供：

1. **漏洞类型**: 具体的漏洞分类
2. **风险等级**: Critical/High/Medium/Low
3. **影响范围**: 描述可能的影响
4. **具体位置**: 精确的行号和代码片段
5. **攻击场景**: 详细的攻击利用方式
6. **修复建议**: 具体的代码修复方案
7. **安全最佳实践**: 相关的安全编码建议

请确保分析的准确性和完整性，不要遗漏任何潜在的安全风险。
"""

    BUSINESS_LOGIC_ANALYSIS_TEMPLATE = """
请分析以下业务逻辑代码的安全性：

**业务模块**: {module_name}
**核心功能**: {core_functionality}
**数据流向**: {data_flow}

**相关代码文件：**
{code_files}

**分析重点：**
1. 业务逻辑绕过风险
2. 权限控制缺陷
3. 数据验证不足
4. 状态管理问题
5. 并发安全问题
6. 业务流程完整性

请提供详细的业务逻辑安全分析报告。
"""

    def build_system_prompt(self, context: Dict[str, Any]) -> str:
        """构建系统提示"""
        security_areas = self._format_security_areas(context.get('security_rules', {}))
        
        return self.SYSTEM_PROMPT_TEMPLATE.format(
            project_name=context.get('project_name', 'Unknown'),
            project_type=context.get('project_type', 'Unknown'),
            module_name=context.get('module_name', 'Unknown'),
            primary_language=context.get('primary_language', 'Unknown'),
            architecture_pattern=context.get('architecture_pattern', 'Unknown'),
            security_focus_areas=security_areas
        )
    
    def build_code_request_prompt(self, audit_target: str, context: Dict[str, Any]) -> str:
        """构建代码请求提示"""
        return self.CODE_REQUEST_TEMPLATE.format(
            audit_target=audit_target,
            module_name=context.get('module_name', ''),
            entry_points=', '.join(context.get('entry_points', [])),
            related_files=', '.join(context.get('related_files', []))
        )
    
    def build_vulnerability_analysis_prompt(self, file_info: Dict[str, Any], code_content: str) -> str:
        """构建漏洞分析提示"""
        vuln_types = self._format_vulnerability_types()
        
        return self.VULNERABILITY_ANALYSIS_TEMPLATE.format(
            file_path=file_info.get('path', ''),
            language=file_info.get('language', ''),
            file_size=file_info.get('size', 0),
            business_function=file_info.get('business_function', '未知'),
            code_content=code_content,
            vulnerability_types=vuln_types
        )
    
    def _format_security_areas(self, security_rules: Dict[str, bool]) -> str:
        """格式化安全关注领域"""
        enabled_rules = [rule for rule, enabled in security_rules.items() if enabled]
        
        area_mapping = {
            'sql_injection': '• SQL注入攻击检测',
            'xss': '• 跨站脚本攻击(XSS)检测',
            'csrf': '• 跨站请求伪造(CSRF)检测',
            'authentication': '• 身份认证机制分析',
            'authorization': '• 权限控制检查',
            'data_validation': '• 数据验证完整性',
            'sensitive_data': '• 敏感数据保护',
            'crypto': '• 加密算法安全性'
        }
        
        return '\n'.join([area_mapping.get(rule, f'• {rule}') for rule in enabled_rules])
    
    def _format_vulnerability_types(self) -> str:
        """格式化漏洞类型列表"""
        return """
• SQL注入 (CWE-89)
• 跨站脚本攻击 (CWE-79)
• 跨站请求伪造 (CWE-352)
• 命令注入 (CWE-78)
• 路径遍历 (CWE-22)
• 不安全的反序列化 (CWE-502)
• 身份认证绕过 (CWE-287)
• 权限控制缺陷 (CWE-285)
• 敏感信息泄露 (CWE-200)
• 不安全的加密实现 (CWE-327)
"""
```

## 使用示例

### 基本使用流程
```bash
# 1. 初始化项目
ai-audit init /path/to/your/project

# 2. 扫描项目结构
ai-audit scan --output-format json

# 3. 查看识别的模块
ai-audit modules list

# 4. 审计特定模块
ai-audit audit module authentication --model qwen

# 5. 查看审计报告
ai-audit report show latest --format html

# 6. 导出报告
ai-audit report export latest --format pdf --output ./audit-report.pdf
```

### 配置文件示例 (config/default.yaml)
```yaml
llm:
  default_model: "qwen"
  models:
    qwen:
      api_endpoint: "https://api.siliconflow.cn/v1"
      api_key: "sk-ejzylvzgcfnlxgvctpbgnnqginfossvyoifynqhqbaurvkuo"
      model_name: "Qwen/Qwen3-Coder-30B-A3B-Instruct"
      max_tokens: 32768
      temperature: 0.1
      timeout: 30
    kimi:
      api_endpoint: "https://api.siliconflow.cn/v1"
      api_key: "sk-gzkhahnbkjsvrerhxbtzzfuctexesqkmmbgyaylhitynvdri"
      model_name: "moonshotai/Kimi-K2-Instruct"
      max_tokens: 128000
      temperature: 0.1
      timeout: 60

database:
  type: "mysql"
  host: "localhost"
  port: 3306
  username: "root"
  password: "jackhou."
  database: "ai_code_audit_system"
  charset: "utf8mb4"
  pool_size: 10
  max_overflow: 20

audit:
  max_concurrent_sessions: 3
  cache_ttl: 86400
  supported_languages:
    - "python"
    - "javascript"
    - "typescript"
    - "java"
    - "go"
    - "rust"
  output_formats:
    - "json"
    - "html"
    - "pdf"

security_rules:
  sql_injection: true
  xss: true
  csrf: true
  authentication: true
  authorization: true
  data_validation: true
  sensitive_data_exposure: true
  insecure_crypto: true
  code_injection: true
  path_traversal: true

cache_dir: "./cache"
log_level: "INFO"
```

这些实现示例提供了系统的核心组件结构，可以作为开发的起点。接下来可以根据这些模板逐步实现完整的功能。
