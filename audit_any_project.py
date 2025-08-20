#!/usr/bin/env python3
"""
通用AI代码审计脚本
支持命令行参数指定项目路径
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit import audit_project

async def generate_markdown_report(results, project_path, output_file):
    """生成Markdown格式的审计报告"""
    
    # 生成Markdown报告
    report = f"""# 🔍 AI代码安全审计报告

## 📋 项目信息
- **项目路径**: `{project_path}`
- **审计时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **审计模板**: {results.get('template', 'owasp_top_10_2021')}
- **分析文件数**: {results.get('total_files', 0)}

## 📊 审计摘要
- **发现问题总数**: {len(results.get('findings', []))}
- **审计状态**: {results.get('summary', {}).get('completion_status', 'unknown')}

## 📁 项目结构
```
{project_path}/
└── (项目文件结构)
```

## 🔍 代码分析

本次审计分析了项目中的源代码文件，重点关注安全漏洞检测。

## 🚨 安全问题发现

"""
    
    if results.get('findings'):
        # 按文件分组显示漏洞
        files_with_issues = {}
        for finding in results['findings']:
            file_name = finding.get('file', 'Unknown')
            if file_name not in files_with_issues:
                files_with_issues[file_name] = []
            files_with_issues[file_name].append(finding)
        
        for file_name, findings in files_with_issues.items():
            report += f"""### 📄 {file_name} ({len(findings)}个问题)

"""
            for i, finding in enumerate(findings, 1):
                severity_icon = {
                    'high': '🔴',
                    'medium': '🟡', 
                    'low': '🟢'
                }.get(finding.get('severity', 'medium'), '🟡')
                
                report += f"""#### {severity_icon} 问题 {i}: {finding.get('type', '安全问题')}

**严重程度**: {finding.get('severity', 'medium').upper()}  
**行号**: {finding.get('line', 'N/A')}  
**描述**: {finding.get('description', '未知问题')}

**问题代码**:
```python
{finding.get('code_snippet', '代码片段未提供')}
```

**潜在影响**: {finding.get('impact', '未知影响')}

**修复建议**: {finding.get('recommendation', '请咨询安全专家')}

---

"""
    else:
        report += """### ✅ 未发现明显的安全问题

通过AI安全审计，当前代码库未发现明显的安全漏洞。但建议：

1. **定期更新依赖**: 确保所有第三方库都是最新版本
2. **代码审查**: 建立代码审查流程
3. **安全测试**: 进行渗透测试和安全扫描
4. **输入验证**: 加强用户输入验证
5. **日志监控**: 建立完善的日志和监控系统

"""

    report += f"""## 🔧 技术建议

### 代码质量改进
1. **添加类型注解**: 使用类型提示提高代码可读性
2. **异常处理**: 完善异常处理机制
3. **单元测试**: 增加测试覆盖率
4. **文档完善**: 添加详细的API文档

### 安全加固建议
1. **密码安全**: 使用强密码策略和安全的哈希算法
2. **SQL注入防护**: 使用参数化查询
3. **文件上传安全**: 验证文件类型和大小
4. **访问控制**: 实现细粒度的权限控制

## 📈 审计统计
- **审计开始时间**: {results.get('timestamp', 'unknown')}
- **处理文件数量**: {results.get('total_files', 0)}
- **发现问题数量**: {len(results.get('findings', []))}
- **审计完成状态**: ✅ 成功

---
*本报告由AI代码审计系统自动生成*
"""
    
    # 保存Markdown报告
    report_file = output_file.replace('.json', '_report.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Markdown报告已生成: {report_file}")
    return report_file

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI代码安全审计工具')
    parser.add_argument('project_path', help='要审计的项目路径')
    parser.add_argument('-o', '--output', default='audit_results.json', help='输出文件名 (默认: audit_results.json)')
    parser.add_argument('-t', '--template', default='owasp_top_10_2021', help='审计模板 (默认: owasp_top_10_2021)')
    parser.add_argument('-m', '--max-files', type=int, default=500, help='最大审计文件数 (默认: 500)')
    parser.add_argument('--all', action='store_true', help='审计所有文件，忽略max-files限制')
    parser.add_argument('--no-filter-stats', action='store_true', help='不显示文件过滤统计')
    
    args = parser.parse_args()
    
    # 检查项目路径是否存在
    if not Path(args.project_path).exists():
        print(f"❌ 错误: 项目路径不存在: {args.project_path}")
        sys.exit(1)
    
    # 处理--all参数
    max_files = None if args.all else args.max_files

    print(f"🔍 开始审计项目: {args.project_path}")
    print(f"📝 使用模板: {args.template}")
    if args.all:
        print(f"📊 审计模式: 所有文件 (无限制)")
    else:
        print(f"📊 最大文件数: {args.max_files}")

    try:
        results = await audit_project(
            project_path=args.project_path,
            output_file=args.output,
            template=args.template,
            max_files=max_files,
            show_filter_stats=not args.no_filter_stats
        )
        
        # 生成Markdown报告
        await generate_markdown_report(results, args.project_path, args.output)
        
        print(f"✅ 审计完成！")
        print(f"📊 结果摘要:")
        print(f"  - 分析文件数: {results['total_files']}")
        print(f"  - 发现问题数: {len(results['findings'])}")
        print(f"  - JSON结果: {args.output}")
        print(f"  - Markdown报告: {args.output.replace('.json', '_report.md')}")
        
    except Exception as e:
        print(f"❌ 审计失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
