#!/usr/bin/env python3
"""
AI Code Audit - 简化使用示例

移除CLI后的直接调用方式
"""

import asyncio
from ai_code_audit import audit_project

async def main():
    """主函数示例"""
    
    # 基本用法
    print("🔍 基本审计示例:")
    try:
        results = await audit_project(
            project_path="/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2",
            output_file="audit_results.json",
            template="security_audit_chinese",
            max_files=50,
            show_filter_stats=True,
            filter_level="strict"
        )
        print(f"✅ 审计完成，发现 {len(results.get('findings', []))} 个问题")
        
    except Exception as e:
        print(f"❌ 审计失败: {e}")

    # 快速审计（只审计前10个文件）
    print("\n🚀 快速审计示例:")
    try:
        results = await audit_project(
            project_path="/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2",
            max_files=10,
            show_filter_stats=False
        )
        print(f"✅ 快速审计完成")
        
    except Exception as e:
        print(f"❌ 快速审计失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
