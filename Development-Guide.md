# AI代码审计系统 - 开发指南

## 项目初始化

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv ai-code-audit-env
source ai-code-audit-env/bin/activate  # Linux/Mac
# ai-code-audit-env\Scripts\activate  # Windows

# 安装Poetry包管理器
pip install poetry

# 初始化项目
poetry init
```

### 2. 依赖管理
```toml
# pyproject.toml
[tool.poetry]
name = "ai-code-audit"
version = "0.1.0"
description = "AI-powered code security audit system"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.9"
click = "^8.1.0"
aiohttp = "^3.8.0"
pydantic = "^2.0.0"
pyyaml = "^6.0"
rich = "^13.0.0"
tree-sitter = "^0.20.0"
gitpython = "^3.1.0"
asyncio = "^3.4.3"
jinja2 = "^3.1.0"
aiomysql = "^0.2.0"
sqlalchemy = "^2.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
isort = "^5.12.0"
flake8 = "^6.0.0"
mypy = "^1.0.0"

[tool.poetry.scripts]
ai-audit = "ai_code_audit.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## 项目结构

```
ai-code-audit/
├── ai_code_audit/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py              # 主CLI入口
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── init.py          # 初始化命令
│   │   │   ├── scan.py          # 扫描命令
│   │   │   ├── audit.py         # 审计命令
│   │   │   └── report.py        # 报告命令
│   │   └── utils.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py            # 数据模型
│   │   ├── exceptions.py        # 异常定义
│   │   └── constants.py         # 常量定义
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py        # 数据库连接
│   │   ├── models.py            # SQLAlchemy模型
│   │   └── migrations/          # 数据库迁移
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── project_analyzer.py  # 项目分析器
│   │   ├── code_indexer.py      # 代码索引器
│   │   ├── module_identifier.py # 模块识别器
│   │   └── dependency_analyzer.py # 依赖分析器
│   ├── context/
│   │   ├── __init__.py
│   │   ├── session_manager.py   # 会话管理器
│   │   ├── cache_manager.py     # 缓存管理器
│   │   └── context_builder.py   # 上下文构建器
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base_adapter.py      # 基础适配器
│   │   ├── qwen_adapter.py      # Qwen适配器
│   │   ├── kimi_adapter.py      # Kimi适配器
│   │   ├── prompt_templates.py  # 提示模板
│   │   └── response_parser.py   # 响应解析器
│   ├── report/
│   │   ├── __init__.py
│   │   ├── generator.py         # 报告生成器
│   │   ├── templates/           # 报告模板
│   │   │   ├── html/
│   │   │   ├── json/
│   │   │   └── pdf/
│   │   └── exporters.py         # 导出器
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # 配置管理
│   │   └── default.yaml         # 默认配置
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py        # 文件工具
│       ├── crypto_utils.py      # 加密工具
│       └── logging_utils.py     # 日志工具
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
│   ├── api.md
│   ├── usage.md
│   └── examples/
├── scripts/
│   ├── setup.sh
│   └── test.sh
├── .gitignore
├── README.md
├── pyproject.toml
└── Dockerfile
```

## 核心组件开发指南

### 1. CLI框架实现

#### 主入口文件 (cli/main.py)
```python
import click
from rich.console import Console
from ai_code_audit.cli.commands import init, scan, audit, report
from ai_code_audit.config import load_config

console = Console()

@click.group()
@click.version_option()
@click.option('--config', '-c', help='配置文件路径')
@click.pass_context
def main(ctx, config):
    """AI代码审计系统"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config(config)
    ctx.obj['console'] = console

# 注册子命令
main.add_command(init.init_cmd)
main.add_command(scan.scan_cmd)
main.add_command(audit.audit_cmd)
main.add_command(report.report_cmd)

if __name__ == '__main__':
    main()
```

#### 初始化命令 (cli/commands/init.py)
```python
import click
from pathlib import Path
from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
from ai_code_audit.config.settings import create_project_config

@click.command('init')
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--force', '-f', is_flag=True, help='强制重新初始化')
@click.pass_context
def init_cmd(ctx, project_path, force):
    """初始化项目审计"""
    console = ctx.obj['console']
    
    with console.status("[bold green]正在初始化项目..."):
        try:
            analyzer = ProjectAnalyzer()
            project_info = analyzer.analyze_project(project_path)
            
            # 创建项目配置
            config_path = create_project_config(project_path, project_info, force)
            
            console.print(f"[green]✓[/green] 项目初始化完成: {config_path}")
            console.print(f"[blue]项目类型:[/blue] {project_info.project_type}")
            console.print(f"[blue]文件数量:[/blue] {len(project_info.files)}")
            console.print(f"[blue]支持语言:[/blue] {', '.join(project_info.languages)}")
            
        except Exception as e:
            console.print(f"[red]✗[/red] 初始化失败: {e}")
            raise click.Abort()
```

### 2. 项目分析器实现

#### 核心分析器 (analysis/project_analyzer.py)
```python
from pathlib import Path
from typing import List, Dict, Set
from ai_code_audit.core.models import ProjectInfo, FileInfo, DependencyInfo
from ai_code_audit.utils.file_utils import get_file_hash, detect_language

class ProjectAnalyzer:
    def __init__(self):
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c'
        }
    
    def analyze_project(self, project_path: str) -> ProjectInfo:
        """分析项目结构和基本信息"""
        project_path = Path(project_path)
        
        # 扫描所有文件
        files = self._scan_files(project_path)
        
        # 检测项目类型
        project_type = self._detect_project_type(project_path, files)
        
        # 分析依赖关系
        dependencies = self._analyze_dependencies(project_path, files)
        
        # 识别入口点
        entry_points = self._identify_entry_points(files)
        
        return ProjectInfo(
            path=str(project_path),
            name=project_path.name,
            project_type=project_type,
            files=files,
            dependencies=dependencies,
            entry_points=entry_points,
            languages=list(set(f.language for f in files if f.language))
        )
    
    def _scan_files(self, project_path: Path) -> List[FileInfo]:
        """扫描项目中的所有源代码文件"""
        files = []
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                language = detect_language(file_path)
                if language:
                    file_info = FileInfo(
                        path=str(file_path.relative_to(project_path)),
                        absolute_path=str(file_path),
                        language=language,
                        size=file_path.stat().st_size,
                        hash=get_file_hash(file_path),
                        last_modified=file_path.stat().st_mtime
                    )
                    files.append(file_info)
        
        return files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """判断是否应该忽略文件"""
        ignore_patterns = [
            '.git', '__pycache__', 'node_modules', 'target',
            '.pytest_cache', '.mypy_cache', 'dist', 'build'
        ]
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
```

### 3. LLM集成实现

#### 基础适配器 (llm/base_adapter.py)
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ai_code_audit.core.models import AuditRequest, AuditResponse

class LLMAdapter(ABC):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
    
    @abstractmethod
    async def create_session(self, system_prompt: str, **kwargs) -> str:
        """创建新的对话会话"""
        pass
    
    @abstractmethod
    async def send_message(self, session_id: str, message: str, **kwargs) -> str:
        """发送消息并获取响应"""
        pass
    
    @abstractmethod
    async def analyze_code(self, code: str, analysis_type: str, **kwargs) -> AuditResponse:
        """分析代码并返回审计结果"""
        pass
    
    def build_audit_prompt(self, context: Dict[str, Any]) -> str:
        """构建审计提示"""
        from ai_code_audit.llm.prompt_templates import AuditPromptTemplates
        
        templates = AuditPromptTemplates()
        return templates.build_system_prompt(context)
```

#### Qwen适配器 (llm/qwen_adapter.py)
```python
import aiohttp
import json
from typing import Dict, Any
from ai_code_audit.llm.base_adapter import LLMAdapter
from ai_code_audit.core.models import AuditResponse

class QwenAdapter(LLMAdapter):
    def __init__(self, api_key: str):
        super().__init__(api_key, "Qwen/Qwen3-Coder-30B-A3B-Instruct")
        self.api_endpoint = "https://api.siliconflow.cn/v1"
        self.sessions = {}
    
    async def create_session(self, system_prompt: str, **kwargs) -> str:
        """创建新的对话会话"""
        import uuid
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'messages': [
                {"role": "system", "content": system_prompt}
            ],
            'config': kwargs
        }
        
        return session_id
    
    async def send_message(self, session_id: str, message: str, **kwargs) -> str:
        """发送消息并获取响应"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        session['messages'].append({"role": "user", "content": message})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": session['messages'],
            "temperature": kwargs.get('temperature', 0.1),
            "max_tokens": kwargs.get('max_tokens', 8192),
            "stream": False
        }
        
        async with aiohttp.ClientSession() as client:
            async with client.post(
                f"{self.api_endpoint}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    assistant_message = result['choices'][0]['message']['content']
                    session['messages'].append({"role": "assistant", "content": assistant_message})
                    return assistant_message
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
    
    async def analyze_code(self, code: str, analysis_type: str, **kwargs) -> AuditResponse:
        """分析代码并返回审计结果"""
        from ai_code_audit.llm.prompt_templates import AuditPromptTemplates
        
        templates = AuditPromptTemplates()
        prompt = templates.get_vulnerability_analysis_prompt(code, analysis_type)
        
        # 创建临时会话进行分析
        session_id = await self.create_session(templates.SYSTEM_PROMPT)
        response_text = await self.send_message(session_id, prompt)
        
        # 解析响应
        from ai_code_audit.llm.response_parser import ResponseParser
        parser = ResponseParser()
        return parser.parse_audit_response(response_text)

class KimiAdapter(LLMAdapter):
    def __init__(self, api_key: str):
        super().__init__(api_key, "moonshotai/Kimi-K2-Instruct")
        self.api_endpoint = "https://api.siliconflow.cn/v1"
        self.sessions = {}

    async def create_session(self, system_prompt: str, **kwargs) -> str:
        """创建新的对话会话"""
        import uuid
        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            'messages': [
                {"role": "system", "content": system_prompt}
            ],
            'config': kwargs
        }

        return session_id

    async def send_message(self, session_id: str, message: str, **kwargs) -> str:
        """发送消息并获取响应 - 支持长上下文"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        session['messages'].append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": session['messages'],
            "temperature": kwargs.get('temperature', 0.1),
            "max_tokens": kwargs.get('max_tokens', 128000),  # 支持更长的输出
            "stream": False
        }

        async with aiohttp.ClientSession() as client:
            async with client.post(
                f"{self.api_endpoint}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    assistant_message = result['choices'][0]['message']['content']
                    session['messages'].append({"role": "assistant", "content": assistant_message})
                    return assistant_message
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")

    async def analyze_code(self, code: str, analysis_type: str, **kwargs) -> AuditResponse:
        """分析代码并返回审计结果 - 适合大型项目分析"""
        from ai_code_audit.llm.prompt_templates import AuditPromptTemplates

        templates = AuditPromptTemplates()
        prompt = templates.get_vulnerability_analysis_prompt(code, analysis_type)

        # 创建临时会话进行分析
        session_id = await self.create_session(templates.SYSTEM_PROMPT)
        response_text = await self.send_message(session_id, prompt)

        # 解析响应
        from ai_code_audit.llm.response_parser import ResponseParser
        parser = ResponseParser()
        return parser.parse_audit_response(response_text)
```

## 配置更新说明

### API配置变更
- **统一API提供商**: 所有模型都通过硅基流动提供
- **Qwen模型**: sk-ejzylvzgcfnlxgvctpbgnnqginfossvyoifynqhqbaurvkuo
- **Kimi模型**: sk-gzkhahnbkjsvrerhxbtzzfuctexesqkmmbgyaylhitynvdri
- **API端点**: https://api.siliconflow.cn/v1

### 数据库配置
- **数据库类型**: MySQL 8.0+
- **连接信息**: localhost:3306
- **用户凭据**: root / jackhou.
- **数据库名**: ai_code_audit

这个开发指南提供了详细的项目结构和核心组件的实现方案，包括更新后的LLM适配器和数据库配置。接下来我们可以开始具体的开发工作，从基础框架开始逐步实现各个功能模块。
