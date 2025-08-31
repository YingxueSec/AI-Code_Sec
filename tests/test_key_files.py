#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试关键文件的改进效果
专门测试之前发现误报的核心文件
"""

import sys
import asyncio
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit.llm.manager import LLMManager

async def test_key_files():
    """测试关键文件"""
    print("🎯 测试关键文件的改进效果\n")
    
    # 初始化LLM管理器 - 使用实际配置
    config = {
        'llm': {
            'kimi': {
                'api_key': 'sk-kpepqjjtmxpcdhqcvrdekuroxvmpmphkfouhzbcbudbpzzzt',
                'base_url': 'https://api.siliconflow.cn/v1',
                'model_name': 'moonshotai/Kimi-K2-Instruct',
                'enabled': True,
                'priority': 1,
                'max_requests_per_minute': 10000,
                'cost_weight': 1.0,
                'performance_weight': 1.0,
                'timeout': 60
            }
        }
    }
    
    try:
        llm_manager = LLMManager(config)
        print("✅ LLM管理器初始化成功")
    except Exception as e:
        print(f"❌ LLM管理器初始化失败: {e}")
        return False
    
    # 关键测试文件
    test_files = [
        {
            'name': 'PlanDao.java',
            'path': 'examples/test_oa-system/src/main/java/cn/gson/oasys/model/dao/plandao/PlanDao.java',
            'description': 'Spring Data JPA DAO - 之前误报SQL注入'
        },
        {
            'name': 'Planservice.java', 
            'path': 'examples/test_oa-system/src/main/java/cn/gson/oasys/model/dao/plandao/Planservice.java',
            'description': 'Service层 - 之前误报权限验证'
        },
        {
            'name': 'address-mapper.xml',
            'path': 'examples/test_oa-system/src/main/resources/mappers/address-mapper.xml',
            'description': 'MyBatis映射 - 真实SQL注入漏洞'
        }
    ]
    
    results = []
    
    for i, test_file in enumerate(test_files, 1):
        print(f"\n{'='*60}")
        print(f"🔍 测试 {i}/{len(test_files)}: {test_file['name']}")
        print(f"📝 描述: {test_file['description']}")
        print('='*60)
        
        file_path = Path(test_file['path'])
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            continue
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # 检测语言
            if file_path.suffix == '.java':
                language = 'java'
            elif file_path.suffix == '.xml':
                language = 'xml'
            else:
                language = 'unknown'
            
            print(f"📄 文件大小: {len(code)} 字符")
            print(f"🔤 检测语言: {language}")
            
            # 进行安全分析
            result = await llm_manager.analyze_code(
                code=code,
                file_path=str(file_path),
                language=language,
                template="security_audit_chinese"
            )
            
            if result.get('success'):
                findings = result.get('findings', [])
                print(f"\n📊 分析结果:")
                print(f"  发现问题数: {len(findings)}")
                
                if findings:
                    print(f"\n🔍 详细问题:")
                    for j, finding in enumerate(findings, 1):
                        print(f"  {j}. {finding.get('type', 'Unknown')}")
                        print(f"     严重程度: {finding.get('severity', 'N/A')}")
                        print(f"     置信度: {finding.get('confidence', 'N/A')}")
                        print(f"     风险等级: {finding.get('risk_level', 'N/A')}")
                        print(f"     行号: {finding.get('line', 'N/A')}")
                        print(f"     描述: {finding.get('description', 'N/A')[:100]}...")
                        
                        if 'confidence_reasoning' in finding and finding['confidence_reasoning']:
                            print(f"     置信度原因: {finding['confidence_reasoning'][0]}")
                        print()
                else:
                    print("  🎉 未发现安全问题 (可能被智能过滤)")
                
                # 保存结果
                results.append({
                    'file': test_file['name'],
                    'path': str(file_path),
                    'description': test_file['description'],
                    'findings_count': len(findings),
                    'findings': findings
                })
                
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ 分析失败: {error_msg}")
                results.append({
                    'file': test_file['name'],
                    'path': str(file_path),
                    'description': test_file['description'],
                    'error': error_msg
                })
                
        except Exception as e:
            print(f"❌ 处理文件异常: {e}")
            results.append({
                'file': test_file['name'],
                'path': str(file_path),
                'description': test_file['description'],
                'error': str(e)
            })
    
    # 生成总结报告
    print(f"\n{'='*60}")
    print("📋 测试总结报告")
    print('='*60)
    
    total_files = len(test_files)
    successful_analyses = len([r for r in results if 'error' not in r])
    total_findings = sum(r.get('findings_count', 0) for r in results if 'error' not in r)
    
    print(f"📊 统计信息:")
    print(f"  测试文件数: {total_files}")
    print(f"  成功分析数: {successful_analyses}")
    print(f"  总发现问题: {total_findings}")
    print(f"  成功率: {successful_analyses/total_files*100:.1f}%")
    
    print(f"\n🎯 关键改进效果:")
    
    for result in results:
        if 'error' not in result:
            file_name = result['file']
            findings_count = result['findings_count']
            description = result['description']
            
            if 'PlanDao.java' in file_name:
                if findings_count == 0:
                    print(f"  ✅ {file_name}: 成功过滤JPA误报 (0个问题)")
                else:
                    print(f"  ⚠️  {file_name}: 仍有{findings_count}个问题需要检查")
                    
            elif 'Planservice.java' in file_name:
                if findings_count == 0:
                    print(f"  ✅ {file_name}: 成功过滤Service层误报 (0个问题)")
                else:
                    print(f"  ⚠️  {file_name}: 仍有{findings_count}个问题需要检查")
                    
            elif 'address-mapper.xml' in file_name:
                if findings_count > 0:
                    print(f"  ✅ {file_name}: 正确识别真实漏洞 ({findings_count}个问题)")
                else:
                    print(f"  ❌ {file_name}: 可能漏掉真实漏洞 (0个问题)")
    
    # 保存详细结果
    output_file = 'key_files_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细结果已保存到: {output_file}")
    
    return successful_analyses == total_files

async def main():
    """主函数"""
    try:
        success = await test_key_files()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
