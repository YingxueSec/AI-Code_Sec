"""
Main CLI entry point for AI Code Audit System.

This module provides the main command group and coordinates all CLI commands.
"""

import click
from rich.console import Console
from rich.traceback import install
from pathlib import Path
import sys
import os

# Install rich traceback handler for better error display
install(show_locals=True)

# Initialize rich console
console = Console()

# Add the project root to Python path for development
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai_code_audit import __version__
from ai_code_audit.core.exceptions import AuditError


@click.group()
@click.version_option(version=__version__, prog_name="ai-audit")
@click.option(
    "--config", 
    "-c", 
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.option(
    "--verbose", 
    "-v", 
    is_flag=True, 
    help="Enable verbose output"
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
@click.pass_context
def main(ctx: click.Context, config: str, verbose: bool, debug: bool) -> None:
    """
    AI Code Audit System - Intelligent security analysis for your code.
    
    This tool uses advanced AI models to perform comprehensive security
    audits of your codebase, identifying vulnerabilities and providing
    actionable recommendations.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store global configuration
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    ctx.obj['console'] = console
    
    # Set up logging level based on flags
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        console.print("[yellow]Debug mode enabled[/yellow]")
    elif verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
        console.print("[blue]Verbose mode enabled[/blue]")


@main.command()
@click.argument('project_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    '--force', 
    '-f', 
    is_flag=True, 
    help='Force re-initialization of existing project'
)
@click.pass_context
def init(ctx: click.Context, project_path: str, force: bool) -> None:
    """
    Initialize a project for AI code audit.
    
    PROJECT_PATH: Path to the project directory to analyze
    """
    console = ctx.obj['console']
    
    try:
        console.print(f"[green]Initializing project audit for:[/green] {project_path}")
        
        # Convert to absolute path
        abs_path = Path(project_path).resolve()
        
        # Basic validation
        if not abs_path.exists():
            console.print(f"[red]Error:[/red] Project path does not exist: {project_path}")
            raise click.Abort()
        
        if not abs_path.is_dir():
            console.print(f"[red]Error:[/red] Project path is not a directory: {project_path}")
            raise click.Abort()
        
        # Check if project has source files
        source_files = list(abs_path.rglob("*.py")) + list(abs_path.rglob("*.js")) + list(abs_path.rglob("*.java"))
        
        if not source_files:
            console.print(f"[yellow]Warning:[/yellow] No source files found in {project_path}")
            if not click.confirm("Continue anyway?"):
                raise click.Abort()
        
        console.print(f"[green]✓[/green] Found {len(source_files)} source files")
        console.print(f"[green]✓[/green] Project initialized successfully")
        console.print(f"[blue]Next steps:[/blue]")
        console.print("  1. Run 'ai-audit scan' to analyze project structure")
        console.print("  2. Run 'ai-audit audit' to perform security analysis")
        
    except AuditError as e:
        console.print(f"[red]Audit Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        if ctx.obj.get('debug'):
            console.print_exception()
        else:
            console.print(f"[red]Unexpected error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('project_path', type=click.Path(exists=True, file_okay=False, dir_okay=True), required=False, default='.')
@click.option(
    '--output-format',
    type=click.Choice(['json', 'yaml', 'table']),
    default='table',
    help='Output format for scan results'
)
@click.option(
    '--output-file',
    '-o',
    type=click.Path(),
    help='Save results to file'
)
@click.option(
    '--save-to-db',
    is_flag=True,
    help='Save scan results to database'
)
@click.pass_context
def scan(ctx: click.Context, project_path: str, output_format: str, output_file: str, save_to_db: bool) -> None:
    """
    Scan project structure and identify modules.

    This command analyzes the project structure, identifies programming
    languages, and discovers functional modules for targeted auditing.

    PROJECT_PATH: Path to the project directory (default: current directory)
    """
    console = ctx.obj['console']

    try:
        import asyncio
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from pathlib import Path
        import json

        console.print(f"[green]Scanning project:[/green] {project_path}")

        # Initialize project analyzer
        analyzer = ProjectAnalyzer()

        # Run analysis
        async def run_analysis():
            project_info = await analyzer.analyze_project(project_path, save_to_db=save_to_db)
            return project_info

        project_info = asyncio.run(run_analysis())

        # Generate summary
        summary = analyzer.get_analysis_summary(project_info)

        # Display results based on format
        if output_format == 'table':
            console.print("\n[bold blue]📊 Project Analysis Results[/bold blue]")
            console.print(f"[bold]Project Name:[/bold] {summary['project_name']}")
            console.print(f"[bold]Project Type:[/bold] {summary['project_type']}")
            console.print(f"[bold]Total Files:[/bold] {summary['total_files']}")
            console.print(f"[bold]Total Lines:[/bold] {summary['total_lines']:,}")
            console.print(f"[bold]Languages:[/bold] {', '.join(summary['languages'])}")
            console.print(f"[bold]Dependencies:[/bold] {summary['dependencies_count']}")

            if summary['architecture_pattern']:
                console.print(f"[bold]Architecture:[/bold] {summary['architecture_pattern']}")

            if summary['entry_points']:
                console.print(f"[bold]Entry Points:[/bold] {', '.join(summary['entry_points'])}")

            # File breakdown
            console.print("\n[bold blue]📁 File Breakdown by Language[/bold blue]")
            for language, count in summary['file_breakdown'].items():
                console.print(f"  {language}: {count} files")

            console.print(f"\n[bold]Total Size:[/bold] {summary['total_size_bytes']:,} bytes")

        elif output_format == 'json':
            json_output = json.dumps(summary, indent=2, default=str)
            console.print(json_output)

        elif output_format == 'yaml':
            try:
                import yaml
                yaml_output = yaml.dump(summary, default_flow_style=False)
                console.print(yaml_output)
            except ImportError:
                console.print("[red]YAML output requires PyYAML package[/red]")
                console.print("Install with: pip install PyYAML")
                raise click.Abort()

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)

            if output_format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(summary, f, indent=2, default=str)
            elif output_format == 'yaml':
                import yaml
                with open(output_path, 'w') as f:
                    yaml.dump(summary, f, default_flow_style=False)
            else:  # table format as text
                with open(output_path, 'w') as f:
                    f.write(f"Project Analysis Results\n")
                    f.write(f"Project Name: {summary['project_name']}\n")
                    f.write(f"Project Type: {summary['project_type']}\n")
                    f.write(f"Total Files: {summary['total_files']}\n")
                    f.write(f"Total Lines: {summary['total_lines']:,}\n")
                    f.write(f"Languages: {', '.join(summary['languages'])}\n")
                    f.write(f"Dependencies: {summary['dependencies_count']}\n")

            console.print(f"[green]Results saved to:[/green] {output_path}")

        if save_to_db:
            console.print("[green]✓[/green] Results saved to database")

        console.print("\n[green]✓[/green] Project scan completed successfully")

    except Exception as e:
        if ctx.obj.get('debug'):
            console.print_exception()
        else:
            console.print(f"[red]Error during scan:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('project_path', type=click.Path(exists=True, file_okay=False, dir_okay=True), required=False, default='.')
@click.option(
    '--model',
    type=click.Choice(['qwen-coder-30b', 'kimi-k2']),
    default='qwen-coder-30b',
    help='LLM model to use for analysis'
)
@click.option(
    '--template',
    type=click.Choice(['security_audit', 'security_audit_enhanced', 'code_review', 'vulnerability_scan']),
    default='security_audit',
    help='Analysis template to use'
)
@click.option(
    '--max-files',
    type=int,
    default=5,
    help='Maximum number of files to analyze'
)
@click.option(
    '--output-file',
    '-o',
    type=click.Path(),
    help='Save results to file'
)
@click.pass_context
def audit(ctx: click.Context, project_path: str, model: str, template: str, max_files: int, output_file: str) -> None:
    """
    Perform AI-powered security audit.

    This command runs the core security analysis using AI models to
    identify vulnerabilities and security issues in your code.

    PROJECT_PATH: Path to the project directory (default: current directory)
    """
    console = ctx.obj['console']

    try:
        import asyncio
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.llm.manager import LLMManager
        from ai_code_audit.llm.prompts import PromptManager
        from ai_code_audit.llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
        from pathlib import Path
        import json

        console.print(f"[green]Starting AI security audit:[/green] {project_path}")
        console.print(f"[blue]Model:[/blue] {model} | [blue]Template:[/blue] {template}")

        async def run_audit():
            # Step 1: Analyze project
            console.print("\n[yellow]📋 Step 1:[/yellow] Analyzing project structure...")
            analyzer = ProjectAnalyzer()
            project_info = await analyzer.analyze_project(project_path, save_to_db=False)

            console.print(f"✅ Found {len(project_info.files)} files in {len(project_info.languages)} languages")

            # Step 2: Initialize LLM
            console.print("\n[yellow]🤖 Step 2:[/yellow] Initializing AI models...")
            llm_manager = LLMManager()

            if not llm_manager.providers:
                console.print("[red]❌ No LLM providers configured![/red]")
                console.print("Please set up API keys:")
                console.print("  export QWEN_API_KEY=your_qwen_key")
                console.print("  export KIMI_API_KEY=your_kimi_key")
                return

            # Validate providers
            validation_results = await llm_manager.validate_providers()
            valid_providers = [name for name, valid in validation_results.items() if valid]

            if not valid_providers:
                console.print("[red]❌ No valid LLM providers found![/red]")
                console.print("Please check your API keys")
                return

            console.print(f"✅ Valid providers: {', '.join(valid_providers)}")

            # Step 3: Prepare prompts
            console.print(f"\n[yellow]📝 Step 3:[/yellow] Preparing {template} prompts...")
            prompt_manager = PromptManager()

            # Step 4: Analyze files
            console.print(f"\n[yellow]🔍 Step 4:[/yellow] Analyzing files (max {max_files})...")

            # Filter source files
            source_files = [f for f in project_info.files if f.language][:max_files]

            if not source_files:
                console.print("[yellow]⚠️  No source files found to analyze[/yellow]")
                return

            # Map model names
            model_mapping = {
                'qwen-coder-30b': LLMModelType.QWEN_CODER_30B,
                'kimi-k2': LLMModelType.KIMI_K2,
            }

            selected_model = model_mapping.get(model, LLMModelType.QWEN_CODER_30B)
            audit_results = []

            for i, file_info in enumerate(source_files, 1):
                console.print(f"[cyan]Analyzing {i}/{len(source_files)}:[/cyan] {file_info.path}")

                try:
                    # Read file content
                    file_path = Path(file_info.absolute_path)
                    if file_path.exists() and file_path.stat().st_size < 30000:  # Skip large files
                        content = file_path.read_text(encoding='utf-8', errors='ignore')

                        # Generate prompt variables based on template
                        variables = {
                            'language': file_info.language or 'unknown',
                            'file_path': file_info.path,
                            'project_type': project_info.project_type.value,
                            'dependencies': ', '.join([d.name for d in project_info.dependencies[:5]]),
                            'code_content': content[:6000],  # Limit content size
                        }

                        # Add template-specific variables
                        if template == 'security_audit':
                            variables['additional_context'] = f"Project: {project_info.name}, Architecture: {project_info.architecture_pattern or 'Unknown'}"
                        elif template == 'code_review':
                            variables['target_element'] = f"File: {file_info.path}"
                            variables['context'] = f"Project: {project_info.name}, Type: {project_info.project_type.value}"
                        elif template == 'vulnerability_scan':
                            variables['entry_points'] = ', '.join(project_info.entry_points[:3]) if project_info.entry_points else 'Unknown'
                            variables['input_sources'] = 'User input, HTTP requests, File uploads'
                            variables['frameworks'] = ', '.join([d.name for d in project_info.dependencies[:3]])

                        prompt = prompt_manager.generate_prompt(template, variables)
                        if not prompt:
                            console.print(f"  [red]❌ Failed to generate prompt[/red]")
                            continue

                        # Create LLM request
                        request = LLMRequest(
                            messages=[
                                LLMMessage(MessageRole.SYSTEM, prompt['system']),
                                LLMMessage(MessageRole.USER, prompt['user'])
                            ],
                            model=selected_model,
                            temperature=0.1,
                            max_tokens=1500
                        )

                        # Send to LLM
                        response = await llm_manager.chat_completion(request)

                        audit_results.append({
                            'file': file_info.path,
                            'language': file_info.language,
                            'analysis': response.content,
                            'model_used': response.metadata.get('provider_used'),
                            'tokens_used': response.usage.total_tokens if response.usage else 0,
                        })

                        console.print(f"  [green]✅ Completed[/green] ({response.usage.total_tokens if response.usage else 0} tokens)")

                    else:
                        console.print(f"  [yellow]⚠️  Skipped (too large or not found)[/yellow]")

                except Exception as e:
                    console.print(f"  [red]❌ Failed: {e}[/red]")
                    continue

            # Step 5: Display results
            console.print(f"\n[green]🎉 Audit completed![/green] Analyzed {len(audit_results)} files")

            if audit_results:
                total_tokens = sum(r['tokens_used'] for r in audit_results)
                console.print(f"[blue]Total tokens used:[/blue] {total_tokens:,}")

                # Display results
                console.print("\n[bold blue]📋 Analysis Results[/bold blue]")
                for result in audit_results:
                    console.print(f"\n[bold cyan]{result['file']}[/bold cyan] ({result['language']})")
                    console.print("-" * 60)
                    # Show analysis with word wrapping
                    analysis = result['analysis']
                    if len(analysis) > 500:
                        analysis = analysis[:500] + "\n... (truncated)"
                    console.print(analysis)

                # Save results if requested
                if output_file:
                    output_path = Path(output_file)
                    with open(output_path, 'w') as f:
                        json.dump(audit_results, f, indent=2, default=str)
                    console.print(f"\n[green]Results saved to:[/green] {output_path}")

            # Clean up
            await llm_manager.close()

        # Run the audit
        asyncio.run(run_audit())

    except Exception as e:
        if ctx.obj.get('debug'):
            console.print_exception()
        else:
            console.print(f"[red]Error during audit:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('audit_id', required=False)
@click.option(
    '--format', 
    'report_format',
    type=click.Choice(['html', 'json', 'markdown', 'pdf']), 
    default='html',
    help='Report format'
)
@click.option(
    '--output', 
    '-o', 
    type=click.Path(),
    help='Output file path'
)
@click.option(
    '--latest', 
    is_flag=True, 
    help='Show latest audit report'
)
@click.pass_context
def report(ctx: click.Context, audit_id: str, report_format: str, output: str, latest: bool) -> None:
    """
    Generate and view audit reports.
    
    AUDIT_ID: Specific audit session ID (optional)
    """
    console = ctx.obj['console']
    
    try:
        if latest:
            console.print("[green]Generating latest audit report...[/green]")
        elif audit_id:
            console.print(f"[green]Generating report for audit:[/green] {audit_id}")
        else:
            console.print("[green]Generating comprehensive audit report...[/green]")
        
        console.print(f"[blue]Format:[/blue] {report_format}")
        
        if output:
            console.print(f"[blue]Output file:[/blue] {output}")
        
        # TODO: Implement actual report generation
        console.print("[yellow]Report functionality not yet implemented[/yellow]")
        console.print("This will generate:")
        console.print("  • Executive summary")
        console.print("  • Detailed findings")
        console.print("  • Risk assessment")
        console.print("  • Remediation recommendations")
        
    except Exception as e:
        if ctx.obj.get('debug'):
            console.print_exception()
        else:
            console.print(f"[red]Error generating report:[/red] {e}")
        raise click.Abort()


@main.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show version information."""
    console = ctx.obj['console']
    console.print(f"AI Code Audit System v{__version__}")


@main.command()
@click.argument('project_path', default='.')
@click.option('--template', default='security_audit',
              type=click.Choice(['security_audit', 'security_audit_enhanced', 'code_review', 'vulnerability_scan']),
              help='Analysis template to use')
@click.option('--model', default='qwen-coder-30b',
              type=click.Choice(['qwen-coder-30b', 'kimi-k2']),
              help='LLM model to use')
@click.option('--max-files', default=20, help='Maximum files to analyze')
@click.option('--output', help='Output file path for report')
@click.option('--format', 'report_format', default='json',
              type=click.Choice(['json', 'html', 'markdown', 'csv']),
              help='Report format')
@click.pass_context
def audit_v2(ctx: click.Context, project_path: str, template: str, model: str,
             max_files: int, output: str, report_format: str) -> None:
    """
    Run comprehensive AI-powered code audit using the new audit engine.

    This command uses the advanced audit engine with session management,
    orchestrated analysis, result aggregation, and report generation.
    """
    console = ctx.obj['console']

    try:
        import asyncio
        from ai_code_audit.audit.engine import AuditEngine
        from ai_code_audit.audit.report_generator import ReportFormat
        from ai_code_audit.llm.base import LLMModelType

        console.print(f"[green]🚀 Starting Advanced AI Code Audit[/green]")
        console.print(f"[blue]Project:[/blue] {project_path}")
        console.print(f"[blue]Template:[/blue] {template}")
        console.print(f"[blue]Model:[/blue] {model}")
        console.print(f"[blue]Max files:[/blue] {max_files}")

        async def run_advanced_audit():
            # Map model names
            model_mapping = {
                'qwen-coder-30b': LLMModelType.QWEN_CODER_30B,
                'kimi-k2': LLMModelType.KIMI_K2,
            }

            selected_model = model_mapping.get(model, LLMModelType.QWEN_CODER_30B)

            # Initialize audit engine
            console.print("\n[yellow]🔧 Initializing audit engine...[/yellow]")
            audit_engine = AuditEngine()
            await audit_engine.initialize()

            # Progress callback
            def progress_callback(session):
                progress = session.progress
                console.print(f"[blue]Progress:[/blue] {progress.completion_percentage:.1f}% "
                            f"({progress.analyzed_files}/{progress.total_files} files)")
                if progress.current_file:
                    console.print(f"[dim]Currently analyzing: {progress.current_file}[/dim]")

            # Start audit
            console.print(f"\n[yellow]🔍 Starting analysis with {selected_model.name}...[/yellow]")
            session_id = await audit_engine.start_audit(
                project_path=project_path,
                template=template,
                model=selected_model,
                max_files=max_files,
                progress_callback=progress_callback
            )

            console.print(f"✅ Audit session started: {session_id}")

            # Monitor progress
            with console.status("[bold green]Running comprehensive audit...") as status:
                while True:
                    await asyncio.sleep(3)

                    audit_status = await audit_engine.get_audit_status(session_id)
                    if not audit_status:
                        break

                    progress_pct = audit_status['progress']['completion_percentage']
                    status.update(f"[bold green]Audit in progress... {progress_pct:.1f}%")

                    if audit_status['status'] in ['completed', 'failed', 'cancelled']:
                        break

            # Get final results
            final_status = await audit_engine.get_audit_status(session_id)
            if not final_status:
                console.print("[red]❌ Failed to get audit status[/red]")
                return

            if final_status['status'] == 'completed':
                console.print(f"\n[green]🎉 Audit completed successfully![/green]")
                console.print(f"✅ Files analyzed: {final_status['progress']['analyzed_files']}")
                console.print(f"✅ Success rate: {final_status['statistics']['success_rate']:.1f}%")

                # Get detailed results
                audit_result = await audit_engine.get_audit_results(session_id)
                if audit_result:
                    console.print(f"\n[yellow]📊 Security Analysis Summary:[/yellow]")
                    console.print(f"✅ Total findings: {audit_result.total_findings}")
                    console.print(f"🔴 Critical: {audit_result.critical_count}")
                    console.print(f"🟠 High: {audit_result.high_count}")
                    console.print(f"📈 Risk score: {audit_result.risk_score:.1f}/10")

                    # Show top vulnerabilities
                    if audit_result.vulnerabilities:
                        console.print(f"\n[yellow]🔍 Top Security Issues:[/yellow]")
                        for i, vuln in enumerate(audit_result.vulnerabilities[:5], 1):
                            severity_color = {
                                'critical': 'red',
                                'high': 'orange',
                                'medium': 'yellow',
                                'low': 'green',
                                'info': 'blue'
                            }.get(vuln.severity.value, 'white')

                            console.print(f"[{severity_color}]{i}. {vuln.title}[/{severity_color}]")
                            console.print(f"   [dim]File: {vuln.file_path} | Severity: {vuln.severity.value.upper()}[/dim]")

                # Generate report if requested
                if output:
                    console.print(f"\n[yellow]📄 Generating {report_format.upper()} report...[/yellow]")

                    format_mapping = {
                        'json': ReportFormat.JSON,
                        'html': ReportFormat.HTML,
                        'markdown': ReportFormat.MARKDOWN,
                        'csv': ReportFormat.CSV,
                    }

                    selected_format = format_mapping.get(report_format, ReportFormat.JSON)

                    report_content = await audit_engine.generate_report(
                        session_id=session_id,
                        format=selected_format,
                        output_path=output
                    )

                    if report_content:
                        console.print(f"✅ Report saved to: {output}")
                    else:
                        console.print("[red]❌ Failed to generate report[/red]")

            elif final_status['status'] == 'failed':
                console.print(f"[red]❌ Audit failed[/red]")
                if final_status['statistics']['total_errors'] > 0:
                    console.print(f"[red]Errors: {final_status['statistics']['total_errors']}[/red]")

            else:
                console.print(f"[yellow]⚠️  Audit ended with status: {final_status['status']}[/yellow]")

            # Cleanup
            await audit_engine.shutdown()

        # Run the advanced audit
        asyncio.run(run_advanced_audit())

    except Exception as e:
        if ctx.obj.get('debug'):
            console.print_exception()
        else:
            console.print(f"[red]Error during advanced audit:[/red] {e}")
        raise click.Abort()


@main.command()
@click.option(
    '--show-keys',
    is_flag=True,
    help='Show API keys (masked for security)'
)
@click.pass_context
def config(ctx: click.Context, show_keys: bool) -> None:
    """
    Show current configuration.

    This command displays the current configuration settings including
    database, LLM providers, and audit settings.
    """
    console = ctx.obj['console']

    try:
        from ai_code_audit.core.config import get_config

        config = get_config()

        console.print("[bold blue]🔧 AI Code Audit System Configuration[/bold blue]")
        console.print("=" * 60)

        # Database configuration
        console.print("\n[bold yellow]📊 Database Configuration[/bold yellow]")
        console.print(f"Host: {config.database.host}:{config.database.port}")
        console.print(f"Database: {config.database.database}")
        console.print(f"Username: {config.database.username}")
        console.print(f"Pool Size: {config.database.pool_size}")

        # LLM configuration
        console.print("\n[bold yellow]🤖 LLM Configuration[/bold yellow]")
        console.print(f"Default Model: {config.llm.default_model}")

        if config.llm.qwen:
            console.print("\n[cyan]Qwen Provider:[/cyan]")
            console.print(f"  API Key: {'*' * 20 + config.llm.qwen.api_key[-8:] if show_keys and config.llm.qwen.api_key else '***masked***'}")
            console.print(f"  Base URL: {config.llm.qwen.base_url}")
            console.print(f"  Enabled: {config.llm.qwen.enabled}")
            console.print(f"  Priority: {config.llm.qwen.priority}")
            console.print(f"  Cost Weight: {config.llm.qwen.cost_weight}")

        if config.llm.kimi:
            console.print("\n[cyan]Kimi Provider:[/cyan]")
            console.print(f"  API Key: {'*' * 20 + config.llm.kimi.api_key[-8:] if show_keys and config.llm.kimi.api_key else '***masked***'}")
            console.print(f"  Base URL: {config.llm.kimi.base_url}")
            console.print(f"  Enabled: {config.llm.kimi.enabled}")
            console.print(f"  Priority: {config.llm.kimi.priority}")
            console.print(f"  Cost Weight: {config.llm.kimi.cost_weight}")

        # Audit configuration
        console.print("\n[bold yellow]🔍 Audit Configuration[/bold yellow]")
        console.print(f"Max Concurrent Sessions: {config.audit.max_concurrent_sessions}")
        console.print(f"Cache TTL: {config.audit.cache_ttl} seconds")
        console.print(f"Max File Size: {config.audit.max_file_size} bytes")
        console.print(f"Max Files per Audit: {config.audit.max_files_per_audit}")
        console.print(f"Supported Languages: {', '.join(config.audit.supported_languages[:5])}{'...' if len(config.audit.supported_languages) > 5 else ''}")

        # Security rules
        console.print("\n[bold yellow]🛡️  Security Rules[/bold yellow]")
        enabled_rules = []
        if config.security_rules.sql_injection:
            enabled_rules.append("SQL Injection")
        if config.security_rules.xss:
            enabled_rules.append("XSS")
        if config.security_rules.csrf:
            enabled_rules.append("CSRF")
        if config.security_rules.authentication:
            enabled_rules.append("Authentication")
        if config.security_rules.authorization:
            enabled_rules.append("Authorization")

        console.print(f"Enabled Rules: {', '.join(enabled_rules[:5])}{'...' if len(enabled_rules) > 5 else ''}")

        # Other settings
        console.print("\n[bold yellow]⚙️  Other Settings[/bold yellow]")
        console.print(f"Cache Directory: {config.cache_dir}")
        console.print(f"Log Level: {config.log_level}")
        console.print(f"Debug Mode: {config.debug}")

        console.print("\n[green]✓[/green] Configuration loaded successfully")

        if not show_keys:
            console.print("\n[dim]Use --show-keys to display API keys (last 8 characters)[/dim]")

    except Exception as e:
        if ctx.obj.get('debug'):
            console.print_exception()
        else:
            console.print(f"[red]Error loading configuration:[/red] {e}")
        raise click.Abort()


if __name__ == "__main__":
    main()
