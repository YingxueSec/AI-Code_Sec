"""
AI Code Audit System

A comprehensive AI-powered code security audit system that provides
intelligent analysis of source code for security vulnerabilities,
code quality issues, and best practice violations.
"""

__version__ = "0.1.0"
__author__ = "AI Code Audit Team"
__email__ = "team@example.com"

from ai_code_audit.core.models import (
    ProjectInfo,
    FileInfo,
    Module,
    SecurityFinding,
    AuditResult,
    AuditContext,
)

__all__ = [
    "ProjectInfo",
    "FileInfo",
    "Module",
    "SecurityFinding",
    "AuditResult",
    "AuditContext",
    "audit_project",
]

# 简化的主入口 - 直接使用核心组件，避免复杂依赖
async def audit_project(
    project_path: str,
    output_file: str = None,
    template: str = "security_audit_chinese",
    max_files: int = 0,
    show_filter_stats: bool = True,
    filter_level: str = "strict"
):
    """
    简化的项目审计入口

    Args:
        project_path: 项目路径
        output_file: 输出文件路径
        template: 审计模板
        max_files: 最大文件数 (0=无限制)
        show_filter_stats: 显示过滤统计
        filter_level: 过滤级别 (strict/moderate/lenient)
    """
    from rich.console import Console
    from .core.config import ConfigManager
    from .core.file_filter import FileFilter
    from .analysis.project_analyzer import ProjectAnalyzer
    from .llm.manager import LLMManager
    from .templates.advanced_templates import AdvancedTemplateManager
    import json
    from datetime import datetime
    from pathlib import Path

    console = Console()

    try:
        console.print(f"🔍 开始审计项目: {project_path}")
        console.print(f"📝 使用模板: {template}")

        # 1. 加载配置
        config_manager = ConfigManager()
        config = config_manager.load_config()

        # 2. 分析项目结构
        console.print("📋 分析项目结构...")
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(project_path, save_to_db=False)
        console.print(f"✅ 发现 {len(project_info.files)} 个文件")

        # 3. 应用文件过滤
        if show_filter_stats:
            console.print("🔍 应用智能文件过滤...")
            file_filter = FileFilter(config.file_filtering, project_path)
            file_paths = [str(f.path) for f in project_info.files]
            filtered_files, filter_stats = file_filter.filter_files(file_paths)

            console.print(f"📊 文件过滤统计:")
            console.print(f"• 扫描文件总数: {len(file_paths)}")
            console.print(f"• 审计文件数: {len(filtered_files)}")
            console.print(f"• 过滤掉文件数: {len(file_paths) - len(filtered_files)}")
            console.print(f"• 过滤效率: {((len(file_paths) - len(filtered_files)) / len(file_paths) * 100):.1f}%")

            # 更新项目信息，只保留过滤后的文件
            filtered_file_objs = [f for f in project_info.files if str(f.path) in filtered_files]
            project_info.files = filtered_file_objs[:max_files] if max_files and max_files > 0 else filtered_file_objs
        else:
            # 直接限制文件数量
            if max_files and max_files > 0:
                project_info.files = project_info.files[:max_files]

        console.print(f"🎯 将审计 {len(project_info.files)} 个文件")

        # 4. 初始化LLM和模板
        console.print("🤖 初始化AI模型...")
        # 创建兼容的LLM配置（使用LLMManager期望的格式）
        llm_config_dict = {
            'llm': {},
            'performance': {
                'max_parallel_requests': 5,
                'request_timeout': 60,
                'retry_attempts': 3,
            }
        }

        # 添加qwen配置
        if config.llm.qwen and config.llm.qwen.enabled:
            llm_config_dict['llm']['qwen'] = {
                'api_key': config.llm.qwen.api_key,
                'base_url': config.llm.qwen.base_url,
                'enabled': config.llm.qwen.enabled,
                'priority': config.llm.qwen.priority,
                'max_requests_per_minute': config.llm.qwen.max_requests_per_minute,
                'cost_weight': config.llm.qwen.cost_weight,
                'performance_weight': config.llm.qwen.performance_weight,
            }

        # 添加kimi配置
        if config.llm.kimi and config.llm.kimi.enabled:
            llm_config_dict['llm']['kimi'] = {
                'api_key': config.llm.kimi.api_key,
                'base_url': config.llm.kimi.base_url,
                'enabled': config.llm.kimi.enabled,
                'priority': config.llm.kimi.priority,
                'max_requests_per_minute': config.llm.kimi.max_requests_per_minute,
                'cost_weight': config.llm.kimi.cost_weight,
                'performance_weight': config.llm.kimi.performance_weight,
            }

        llm_manager = LLMManager(llm_config_dict)
        # 设置项目路径，启用跨文件分析
        llm_manager.set_project_path(project_path)
        template_manager = AdvancedTemplateManager()

        # 5. 执行简化的审计流程
        console.print("🔍 开始安全审计...")
        results = {
            "project_path": project_path,
            "template": template,
            "total_files": len(project_info.files),
            "findings": [],
            "summary": {},
            "timestamp": str(datetime.now())
        }

        # 简单的文件分析循环
        for i, file_info in enumerate(project_info.files):
            file_name = Path(file_info.path).name if hasattr(file_info.path, 'name') else Path(str(file_info.path)).name
            console.print(f"分析 {i+1}/{len(project_info.files)}: {file_name}")

            try:
                # 读取文件内容
                file_path = str(file_info.path)
                # 如果是相对路径，相对于项目根目录
                if not Path(file_path).is_absolute():
                    full_path = Path(project_path) / file_path
                else:
                    full_path = Path(file_path)

                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # 获取模板提示词
                template_obj = template_manager.get_template(template)
                if template_obj:
                    # 构建分析请求
                    analysis_prompt = f"{template_obj.system_prompt}\n\n文件路径: {file_info.path}\n\n代码内容:\n{content}"

                    # 调用LLM分析
                    try:
                        console.print(f"  🤖 正在分析 {file_info.language} 代码...")
                        response = await llm_manager.analyze_code(
                            code=content,
                            file_path=str(file_info.path),
                            language=file_info.language,
                            template=template
                        )
                        console.print(f"  📊 LLM响应: success={response.get('success', False)}")

                        if response and response.get('success') and response.get('findings'):
                            findings_count = len(response['findings'])
                            console.print(f"  🚨 发现 {findings_count} 个安全问题")

                            for finding in response['findings']:
                                # 确保finding包含必要的字段
                                finding['file'] = str(file_info.path)
                                finding['language'] = file_info.language
                                results["findings"].append(finding)
                        elif response and not response.get('success'):
                            # LLM分析失败
                            console.print(f"  ⚠️  LLM分析失败: {response.get('error', 'Unknown error')}")
                        else:
                            # 如果没有发现问题，记录一个空结果
                            console.print(f"  ✅ 未发现安全问题")

                    except Exception as llm_error:
                        console.print(f"  ⚠️  LLM分析失败: {llm_error}")
                        # 添加错误记录
                        error_finding = {
                            "file": str(file_info.path),
                            "language": file_info.language,
                            "issues": [f"LLM分析失败: {str(llm_error)}"],
                            "severity": "info",
                            "type": "analysis_error"
                        }
                        results["findings"].append(error_finding)

            except Exception as e:
                console.print(f"⚠️  跳过文件 {file_info.path}: {e}")
                continue

        # 6. 生成摘要
        results["summary"] = {
            "total_findings": len(results["findings"]),
            "files_analyzed": len(project_info.files),
            "completion_status": "success"
        }

        # 7. 保存结果
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            console.print(f"✅ 结果已保存到: {output_file}")

        console.print("🎉 审计完成!")
        return results

    except Exception as e:
        console.print(f"❌ 审计失败: {e}")
        raise
