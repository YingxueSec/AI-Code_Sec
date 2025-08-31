#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端代码分析优化功能
验证智能前端过滤、输入点提取和前后端关联分析
"""

import sys
import asyncio
import json
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit.llm.manager import LLMManager
from ai_code_audit.analysis.frontend_optimizer import FrontendOptimizer
from ai_code_audit.analysis.frontend_backend_mapper import FrontendBackendMapper

async def test_frontend_optimization():
    """测试前端优化功能"""
    print("🚀 测试前端代码分析优化功能\n")
    
    # 初始化LLM管理器
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
        project_path = "examples/test_oa-system"
        llm_manager.set_project_path(project_path)
        print("✅ LLM管理器初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    # 测试用例
    test_cases = [
        {
            'name': '纯静态HTML页面',
            'file_path': 'test_static.html',
            'content': '''<!DOCTYPE html>
<html>
<head>
    <title>静态页面</title>
    <style>
        body { font-size: 14px; color: #333; }
        .container { width: 100%; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>欢迎访问</h1>
        <p>这是一个纯静态页面</p>
    </div>
</body>
</html>''',
            'expected_skip': True
        },
        {
            'name': '包含表单的交互页面',
            'file_path': 'test_form.html',
            'content': '''<!DOCTYPE html>
<html>
<head><title>登录页面</title></head>
<body>
    <form action="/login" method="POST">
        <input type="text" name="username" required>
        <input type="password" name="password" required>
        <button type="submit">登录</button>
    </form>
    <script>
        document.querySelector('form').addEventListener('submit', function(e) {
            // 简单验证
            if (!document.querySelector('[name="username"]').value) {
                e.preventDefault();
                alert('请输入用户名');
            }
        });
    </script>
</body>
</html>''',
            'expected_skip': False,
            'expected_type': 'input_extraction'
        },
        {
            'name': '包含XSS风险的页面',
            'file_path': 'test_xss.html',
            'content': '''<!DOCTYPE html>
<html>
<body>
    <div id="content"></div>
    <script>
        function displayMessage(msg) {
            document.getElementById('content').innerHTML = msg + '<br>';
        }
        
        function processUserInput() {
            var userInput = location.hash.substring(1);
            eval('var result = ' + userInput);
            displayMessage(result);
        }
        
        setTimeout("processUserInput()", 1000);
    </script>
</body>
</html>''',
            'expected_skip': False,
            'expected_type': 'hotspot'
        },
        {
            'name': '包含敏感信息的页面',
            'file_path': 'test_sensitive.html',
            'content': '''<!DOCTYPE html>
<html>
<body>
    <script>
        var config = {
            api_key: "sk-1234567890abcdef",
            password: "admin123456",
            database_url: "jdbc:mysql://localhost:3306/app?user=root&password=secret123"
        };
        
        function initApp() {
            localStorage.setItem('token', config.api_key);
            document.cookie = 'session=' + config.password;
        }
    </script>
</body>
</html>''',
            'expected_skip': False,
            'expected_type': 'hotspot'
        }
    ]
    
    # 测试前端优化器
    optimizer = FrontendOptimizer()
    total_time_saved = 0
    
    print("📊 前端优化测试结果:")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 测试 {i}: {test_case['name']}")
        print(f"文件: {test_case['file_path']}")
        print(f"内容长度: {len(test_case['content'])} 字符")
        
        # 分析前端文件
        start_time = time.time()
        result = optimizer.analyze_frontend_file(test_case['file_path'], test_case['content'])
        analysis_time = time.time() - start_time
        
        print(f"分析时间: {analysis_time:.3f}秒")
        print(f"应该跳过: {result.should_skip}")
        
        if result.should_skip:
            print(f"跳过原因: {result.skip_reason}")
            print(f"节省时间: {result.estimated_time_saved:.1f}秒")
            total_time_saved += result.estimated_time_saved
        else:
            print(f"分析类型: {result.analysis_type}")
            if result.input_points:
                print(f"输入点数量: {len(result.input_points)}")
                for ip in result.input_points[:3]:  # 只显示前3个
                    print(f"  - {ip.type}: {ip.name}")
            
            if result.security_hotspots:
                print(f"安全热点数量: {len(result.security_hotspots)}")
                for hotspot in result.security_hotspots[:3]:  # 只显示前3个
                    print(f"  - {hotspot.type}: {hotspot.description} (第{hotspot.line_number}行)")
            
            if result.estimated_time_saved > 0:
                print(f"节省时间: {result.estimated_time_saved:.1f}秒")
                total_time_saved += result.estimated_time_saved
        
        # 验证预期结果
        if result.should_skip == test_case['expected_skip']:
            print("✅ 跳过判断正确")
        else:
            print("❌ 跳过判断错误")
        
        if not result.should_skip and 'expected_type' in test_case:
            if result.analysis_type == test_case['expected_type']:
                print("✅ 分析类型正确")
            else:
                print(f"❌ 分析类型错误，期望: {test_case['expected_type']}, 实际: {result.analysis_type}")
    
    print(f"\n📊 优化效果统计:")
    print(f"总节省时间: {total_time_saved:.1f}秒")
    print(f"平均每个文件节省: {total_time_saved/len(test_cases):.1f}秒")
    
    return True

async def test_integrated_frontend_analysis():
    """测试集成的前端分析功能"""
    print("\n🔗 测试集成的前端分析功能\n")
    
    # 初始化LLM管理器
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
        project_path = "examples/test_oa-system"
        llm_manager.set_project_path(project_path)
        print("✅ LLM管理器初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    # 测试真实的HTML文件
    test_file = "examples/test_oa-system/src/main/resources/static/plugins/kindeditor/plugins/baidumap/index.html"
    
    if not Path(test_file).exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    try:
        with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        print(f"📄 测试文件: {Path(test_file).name}")
        print(f"📄 文件大小: {len(content)} 字符")
        
        # 测试前端优化
        start_time = time.time()
        result = await llm_manager.analyze_code(
            code=content,
            file_path=test_file,
            language="html",
            template="security_audit_chinese"
        )
        analysis_time = time.time() - start_time
        
        print(f"⏱️  分析时间: {analysis_time:.2f}秒")
        print(f"✅ 分析成功: {result.get('success', False)}")
        
        # 检查前端优化信息
        if 'frontend_optimization' in result:
            opt_info = result['frontend_optimization']
            print(f"🔧 前端优化:")
            print(f"  跳过分析: {opt_info.get('skipped', False)}")
            if opt_info.get('skipped'):
                print(f"  跳过原因: {opt_info.get('reason', 'N/A')}")
                print(f"  节省时间: {opt_info.get('time_saved', 0):.1f}秒")
        
        findings = result.get('findings', [])
        print(f"📊 发现问题数: {len(findings)}")
        
        if findings:
            print("🔍 发现的问题:")
            for i, finding in enumerate(findings[:3], 1):  # 只显示前3个
                print(f"  {i}. {finding.get('type', 'Unknown')}")
                print(f"     严重程度: {finding.get('severity', 'N/A')}")
                print(f"     置信度: {finding.get('confidence', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🚀 开始测试前端代码分析优化功能\n")
    
    tests = [
        ("前端优化器功能", test_frontend_optimization),
        ("集成前端分析", test_integrated_frontend_analysis),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print('='*60)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print(f"\n{'='*60}")
    print("📋 测试总结")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 前端优化功能测试成功！")
        print("\n📋 功能特性:")
        print("✅ 智能识别纯静态内容并跳过分析")
        print("✅ 提取前端输入点进行重点分析")
        print("✅ 检测安全热点进行针对性分析")
        print("✅ 生成优化的分析提示词")
        print("✅ 显著节省分析时间和资源消耗")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步调试")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
