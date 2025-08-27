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
    filter_level: str = "strict",
    enable_cross_file: bool = True,
    enable_frontend_opt: bool = True,
    enable_confidence_calc: bool = True,
    enable_filter: bool = True,
    min_confidence: float = 0.3,
    max_confidence: float = 1.0,
    quick_mode: bool = False,
    verbose: bool = False,
    debug: bool = False,
    include_extensions: list = None,
    exclude_extensions: list = None,
    include_paths: list = None,
    exclude_paths: list = None,
    show_timing: bool = True
):
    """
    完整的项目审计入口，支持所有功能参数控制

    Args:
        project_path: 项目路径
        output_file: 输出文件路径
        template: 审计模板
        max_files: 最大文件数 (0=无限制)
        show_filter_stats: 显示过滤统计
        filter_level: 过滤级别 (strict/moderate/lenient)
        enable_cross_file: 启用跨文件关联分析
        enable_frontend_opt: 启用前端代码优化
        enable_confidence_calc: 启用置信度计算
        enable_filter: 启用智能文件过滤
        min_confidence: 最小置信度阈值
        max_confidence: 最大置信度阈值
        quick_mode: 快速扫描模式
        verbose: 详细输出模式
        debug: 调试模式
        include_extensions: 包含的文件扩展名
        exclude_extensions: 排除的文件扩展名
        include_paths: 包含的路径模式
        exclude_paths: 排除的路径模式
        show_timing: 显示时间统计
    """
    from rich.console import Console
    from .core.config import ConfigManager
    from .core.file_filter import FileFilter
    from .analysis.project_analyzer import ProjectAnalyzer
    from .llm.manager import LLMManager
    from .templates.advanced_templates import AdvancedTemplateManager
    from .utils.cache import get_cache
    import json
    import time
    from datetime import datetime
    from pathlib import Path

    console = Console()
    llm_manager = None

    # 时间统计
    timing_stats = {}
    total_start_time = time.time()

    def log_timing(step_name: str, duration: float):
        """记录时间统计"""
        timing_stats[step_name] = duration
        if show_timing:
            console.print(f"⏱️  {step_name}: {duration:.2f}秒")

    try:
        console.print(f"[INFO] 开始审计项目: {project_path}")
        console.print(f"[INFO] 使用模板: {template}")

        # 1. 加载配置
        step_start = time.time()
        config_manager = ConfigManager()
        config = config_manager.load_config()
        log_timing("配置加载", time.time() - step_start)

        # 2. 分析项目结构
        console.print("[INFO] 分析项目结构...")
        step_start = time.time()
        analyzer = ProjectAnalyzer()
        # 传递扩展名过滤参数给项目分析器
        project_info = await analyzer.analyze_project(
            project_path,
            save_to_db=False,
            include_extensions=include_extensions,
            exclude_extensions=exclude_extensions,
            include_paths=include_paths,
            exclude_paths=exclude_paths
        )
        log_timing("项目结构分析", time.time() - step_start)
        console.print(f"[SUCCESS] 发现 {len(project_info.files)} 个文件")

        # 3. 应用文件过滤
        step_start = time.time()
        if show_filter_stats:
            console.print("[INFO] 应用智能文件过滤...")
            # 创建文件过滤器并传递命令行参数
            file_filter = FileFilter(
                config.file_filtering,
                project_path,
                include_extensions=include_extensions,
                exclude_extensions=exclude_extensions,
                include_paths=include_paths,
                exclude_paths=exclude_paths
            )
            file_paths = [str(f.path) for f in project_info.files]
            filtered_files, filter_stats = file_filter.filter_files(file_paths)

            console.print(f"[INFO] 文件过滤统计:")
            console.print(f"* 扫描文件总数: {len(file_paths)}")
            console.print(f"* 审计文件数: {len(filtered_files)}")
            console.print(f"* 过滤掉文件数: {len(file_paths) - len(filtered_files)}")
            console.print(f"* 过滤效率: {((len(file_paths) - len(filtered_files)) / len(file_paths) * 100):.1f}%")

            # 更新项目信息，只保留过滤后的文件
            filtered_file_objs = [f for f in project_info.files if str(f.path) in filtered_files]
            project_info.files = filtered_file_objs[:max_files] if max_files and max_files > 0 else filtered_file_objs
        else:
            # 直接限制文件数量
            if max_files and max_files > 0:
                project_info.files = project_info.files[:max_files]

        log_timing("文件过滤", time.time() - step_start)
        console.print(f"[INFO] 将审计 {len(project_info.files)} 个文件")

        # 4. 初始化LLM和模板
        console.print("[INFO] 初始化AI模型...")
        step_start = time.time()
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
        log_timing("AI模型初始化", time.time() - step_start)

        # 5. 执行简化的审计流程
        console.print("[INFO] 开始安全审计...")
        analysis_start_time = time.time()

        results = {
            "project_path": project_path,
            "template": template,
            "total_files": len(project_info.files),
            "findings": [],
            "summary": {},
            "timestamp": str(datetime.now()),
            "timing_stats": {}
        }

        # 文件分析时间统计
        file_analysis_times = []
        llm_call_times = []

        # 检查是否启用并行处理
        enable_parallel = len(project_info.files) > 1 and not debug
        max_concurrent = min(3, len(project_info.files))  # 最多3个并发，避免API限制

        if enable_parallel:
            console.print(f"[INFO] 启用并行分析，最大并发数: {max_concurrent}")
            # 并行文件分析
            import asyncio
            semaphore = asyncio.Semaphore(max_concurrent)

            async def analyze_single_file(file_info, index):
                async with semaphore:
                    return await _analyze_file_async(file_info, index, len(project_info.files),
                                                   template_manager, template, llm_manager,
                                                   show_timing, console, project_path)

            # 创建并发任务
            tasks = [analyze_single_file(file_info, i) for i, file_info in enumerate(project_info.files)]
            analysis_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for result in analysis_results:
                if isinstance(result, Exception):
                    console.print(f"[WARNING] 文件分析失败: {result}")
                    continue
                if result:
                    file_time, llm_time, findings = result
                    file_analysis_times.append(file_time)
                    llm_call_times.append(llm_time)
                    results["findings"].extend(findings)
        else:
            # 串行文件分析循环（调试模式或单文件）
            for i, file_info in enumerate(project_info.files):
                file_start_time = time.time()
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
                            console.print(f"  [AI] 正在分析 {file_info.language} 代码...")
                            llm_start_time = time.time()
                            response = await llm_manager.analyze_code(
                                code=content,
                                file_path=str(file_info.path),
                                language=file_info.language,
                                template=template
                            )
                            llm_duration = time.time() - llm_start_time
                            llm_call_times.append(llm_duration)

                            if show_timing:
                                console.print(f"  ⏱️  LLM分析耗时: {llm_duration:.2f}秒")
                            console.print(f"  [INFO] LLM响应: success={response.get('success', False)}")

                            if response and response.get('success') and response.get('findings'):
                                findings_count = len(response['findings'])
                                console.print(f"  [ALERT] 发现 {findings_count} 个安全问题")

                                for finding in response['findings']:
                                    # 确保finding包含必要的字段
                                    finding['file'] = str(file_info.path)
                                    finding['language'] = file_info.language
                                    results["findings"].append(finding)
                            elif response and not response.get('success'):
                                # LLM分析失败
                                console.print(f"  [WARNING] LLM分析失败: {response.get('error', 'Unknown error')}")
                            else:
                                # 如果没有发现问题，记录一个空结果
                                console.print(f"  [SUCCESS] 未发现安全问题")

                        except Exception as llm_error:
                            console.print(f"  [WARNING] LLM分析失败: {llm_error}")
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
                    console.print(f"[WARNING] 跳过文件 {file_info.path}: {e}")
                    continue

                # 记录单个文件分析时间
                file_duration = time.time() - file_start_time
                file_analysis_times.append(file_duration)
                if show_timing:
                    console.print(f"  ⏱️  文件分析总耗时: {file_duration:.2f}秒")

        # 记录总分析时间
        total_analysis_time = time.time() - analysis_start_time
        log_timing("代码分析总时间", total_analysis_time)

        # 获取缓存统计
        cache = get_cache()
        cache_stats = cache.get_stats()
        cache_hits = sum(1 for t in llm_call_times if t < 1.0)  # 假设缓存命中时间 < 1秒
        cache_hit_rate = (cache_hits / len(llm_call_times) * 100) if llm_call_times else 0

        # 6. 生成摘要和时间统计
        step_start = time.time()

        # 计算时间统计
        avg_file_time = sum(file_analysis_times) / len(file_analysis_times) if file_analysis_times else 0
        avg_llm_time = sum(llm_call_times) / len(llm_call_times) if llm_call_times else 0
        total_llm_time = sum(llm_call_times)

        timing_stats.update({
            "代码分析总时间": total_analysis_time,
            "LLM调用总时间": total_llm_time,
            "平均每文件分析时间": avg_file_time,
            "平均LLM调用时间": avg_llm_time,
            "LLM调用次数": len(llm_call_times),
            "缓存命中次数": cache_hits,
            "缓存命中率": cache_hit_rate
        })

        results["summary"] = {
            "total_findings": len(results["findings"]),
            "files_analyzed": len(project_info.files),
            "completion_status": "success"
        }
        results["timing_stats"] = timing_stats
        log_timing("摘要生成", time.time() - step_start)

        # 7. 保存结果
        step_start = time.time()
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            console.print(f"[SUCCESS] 结果已保存到: {output_file}")

            # 生成markdown报告
            try:
                markdown_file = output_file.replace('.json', '_report.md')
                generate_markdown_report(results, markdown_file)
                console.print(f"[INFO] Markdown报告已保存到: {markdown_file}")
            except Exception as report_error:
                console.print(f"[WARNING] 生成Markdown报告失败: {report_error}")
        log_timing("结果保存", time.time() - step_start)

        # 8. 显示完整时间统计报告
        total_time = time.time() - total_start_time
        timing_stats["总执行时间"] = total_time

        if show_timing:
            console.print("\n" + "="*60)
            console.print("📊 时间统计报告")
            console.print("="*60)

            # 分类显示时间统计
            time_items = []
            count_items = []
            avg_items = []

            for step, value in timing_stats.items():
                if "次数" in step:
                    count_items.append((step, value))
                elif "平均" in step:
                    avg_items.append((step, value))
                else:
                    time_items.append((step, value))

            # 显示时间类统计（带百分比）
            for step, duration in time_items:
                if isinstance(duration, (int, float)):
                    percentage = (duration / total_time * 100) if total_time > 0 else 0
                    console.print(f"{step:<20}: {duration:>8.2f}秒 ({percentage:>5.1f}%)")

            # 显示平均时间类统计（不带百分比）
            for step, duration in avg_items:
                if isinstance(duration, (int, float)):
                    console.print(f"{step:<20}: {duration:>8.2f}秒")

            # 显示计数类统计（不带秒和百分比）
            for step, count in count_items:
                if "率" in step:
                    console.print(f"{step:<20}: {count:>7.1f}%")
                else:
                    console.print(f"{step:<20}: {count:>8}次")

            # 显示缓存统计
            if cache_stats['total_files'] > 0:
                console.print("-" * 60)
                console.print("💾 缓存统计:")
                console.print(f"{'缓存文件数':<20}: {cache_stats['total_files']:>8}个")
                console.print(f"{'缓存大小':<20}: {cache_stats['total_size_mb']:>7.1f}MB")
                console.print(f"{'有效缓存':<20}: {cache_stats['valid_files']:>8}个")

            console.print("="*60)

        console.print("[SUCCESS] 审计完成!")
        return results

    except Exception as e:
        console.print(f"[ERROR] 审计失败: {e}")
        raise
    finally:
        if llm_manager:
            await llm_manager.close()


def generate_markdown_report(results, output_file):
    """生成Markdown格式的审计报告"""
    from datetime import datetime

    # 统计数据
    total_findings = len(results.get("findings", []))
    files_analyzed = results.get("total_files", 0)

    # 按严重程度分类
    severity_counts = {}
    file_findings = {}

    for finding in results.get("findings", []):
        severity = finding.get("severity", "unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        file_path = finding.get("file", "unknown")
        if file_path not in file_findings:
            file_findings[file_path] = []
        file_findings[file_path].append(finding)

    # 生成报告内容
    report_content = f"""# AI代码安全审计报告

## 审计概览

- **项目路径**: {results.get('project_path', 'N/A')}
- **审计时间**: {results.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
- **分析文件数**: {files_analyzed}
- **发现问题数**: {total_findings}

## 问题统计

"""

    if severity_counts:
        for severity, count in sorted(severity_counts.items()):
            report_content += f"- **{severity.upper()}**: {count} 个问题\n"
    else:
        report_content += "- 未发现安全问题\n"

    report_content += "\n## 详细发现\n\n"

    if file_findings:
        for file_path, findings in file_findings.items():
            report_content += f"### 文件: {file_path}\n\n"

            for i, finding in enumerate(findings, 1):
                severity = finding.get("severity", "unknown").upper()
                line_number = finding.get("line", "N/A")

                report_content += f"#### {i}. {finding.get('type', '未知问题')} [{severity}]\n\n"
                report_content += f"- **位置**: 第 {line_number} 行\n"

                if finding.get("description"):
                    report_content += f"- **描述**: {finding['description']}\n"

                if finding.get("code_snippet") and finding['code_snippet'].strip():
                    report_content += f"\n**代码片段:**\n```{finding.get('language', '')}\n{finding['code_snippet']}\n```\n"

                if finding.get("recommendation"):
                    report_content += f"\n**建议**: {finding['recommendation']}\n"

                report_content += "\n---\n\n"
    else:
        report_content += "恭喜！未发现任何安全问题。\n\n"

    report_content += f"""## 审计总结

本次审计共分析了 **{files_analyzed}** 个文件，发现了 **{total_findings}** 个潜在问题。

### 建议

1. 优先处理高严重程度的安全问题
2. 定期进行代码安全审计
3. 建立安全编码规范
4. 加强开发团队的安全意识培训

---

*报告由AI代码安全审计系统自动生成*
"""

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)


async def _analyze_file_async(file_info, index, total_files, template_manager, template, llm_manager, show_timing, console, project_path):
    """异步分析单个文件"""
    import time
    from pathlib import Path
    from .utils.cache import get_cache

    file_start_time = time.time()
    file_name = Path(file_info.path).name if hasattr(file_info.path, 'name') else Path(str(file_info.path)).name
    console.print(f"分析 {index+1}/{total_files}: {file_name}")

    try:
        # 读取文件内容
        file_path = str(file_info.path)
        if not Path(file_path).is_absolute():
            full_path = Path(project_path) / file_path
        else:
            full_path = Path(file_path)

        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 获取模板提示词
        template_obj = template_manager.get_template(template)
        if template_obj:
            # 检查缓存
            cache = get_cache()
            cached_response = cache.get(content, template, file_info.language)

            if cached_response:
                console.print(f"  [CACHE] 使用缓存结果")
                response = cached_response.get('response', {})
                llm_duration = 0.1  # 缓存访问时间很短
            else:
                # 调用LLM分析
                console.print(f"  [AI] 正在分析 {file_info.language} 代码...")
                llm_start_time = time.time()
                response = await llm_manager.analyze_code(
                    code=content,
                    file_path=str(file_info.path),
                    language=file_info.language,
                    template=template
                )
                llm_duration = time.time() - llm_start_time

                # 保存到缓存
                if response and response.get('success'):
                    cache.set(content, template, file_info.language, response)

            if show_timing:
                console.print(f"  ⏱️  LLM分析耗时: {llm_duration:.2f}秒")
            console.print(f"  [INFO] LLM响应: success={response.get('success', False)}")

            findings = []
            if response and response.get('success') and response.get('findings'):
                findings_count = len(response['findings'])
                console.print(f"  [ALERT] 发现 {findings_count} 个安全问题")

                for finding in response['findings']:
                    finding['file'] = str(file_info.path)
                    finding['language'] = file_info.language
                    findings.append(finding)
            elif response and not response.get('success'):
                console.print(f"  [WARNING] LLM分析失败: {response.get('error', 'Unknown error')}")
            else:
                console.print(f"  [SUCCESS] 未发现安全问题")

            file_duration = time.time() - file_start_time
            if show_timing:
                console.print(f"  ⏱️  文件分析总耗时: {file_duration:.2f}秒")

            return file_duration, llm_duration, findings

    except Exception as e:
        console.print(f"[WARNING] 跳过文件 {file_info.path}: {e}")
        return 0, 0, []
