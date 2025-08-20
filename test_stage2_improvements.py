#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试第二阶段改进效果
验证上下文分析、技术栈检测和智能置信度评分的效果
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit.analysis.context_analyzer import ContextAnalyzer
from ai_code_audit.analysis.confidence_calculator import ConfidenceCalculator
from ai_code_audit.config.security_config import get_security_config

def test_context_analyzer():
    """测试上下文分析器"""
    print("🔍 测试上下文分析器...")
    
    analyzer = ContextAnalyzer()
    
    # 模拟项目文件
    test_files = [
        {
            'path': 'examples/test_oa-system/src/main/java/cn/gson/oasys/model/dao/plandao/PlanDao.java',
            'language': 'java'
        },
        {
            'path': 'examples/test_oa-system/src/main/java/cn/gson/oasys/model/dao/plandao/Planservice.java',
            'language': 'java'
        }
    ]
    
    try:
        context = analyzer.analyze_project_context(test_files)
        
        print(f"✅ 分析了 {len(test_files)} 个文件")
        print(f"✅ 检测到 {len(context['method_calls'])} 个方法调用")
        print(f"✅ 识别了 {len(context['security_boundaries'])} 个安全边界")
        
        # 显示一些示例结果
        if context['method_calls']:
            print("\n📋 方法调用示例:")
            for call in context['method_calls'][:3]:
                print(f"  - {call.caller_method} -> {call.called_method} (第{call.line_number}行)")
        
        if context['security_boundaries']:
            print("\n🛡️ 安全边界示例:")
            for path, boundary in list(context['security_boundaries'].items())[:2]:
                print(f"  - {boundary.layer}层: {Path(path).name}")
                if boundary.security_controls:
                    print(f"    安全控制: {', '.join(boundary.security_controls)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 上下文分析器测试失败: {e}")
        return False

def test_confidence_calculator():
    """测试置信度计算器"""
    print("\n🎯 测试置信度计算器...")
    
    calculator = ConfidenceCalculator()
    
    # 测试用例1: Spring Data JPA的SQL注入误报
    test_finding_1 = {
        'type': 'SQL注入',
        'severity': 'high',
        'description': 'JPA查询中的潜在SQL注入',
        'code_snippet': '@Query("from Plan p where p.label like %?1%") Page<Plan> findBybasekey(String baseKey, long userid, Pageable pa);'
    }
    
    test_context_1 = {
        'frameworks': {'spring_data_jpa': True, 'mybatis': False},
        'architecture_layer': 'dao',
        'file_path': 'PlanDao.java'
    }
    
    try:
        result_1 = calculator.calculate_confidence(test_finding_1, test_context_1)
        print(f"✅ 测试用例1 - JPA查询:")
        print(f"  置信度: {result_1.final_score:.2f}")
        print(f"  风险等级: {result_1.risk_level}")
        print(f"  主要原因: {result_1.reasoning[0] if result_1.reasoning else '无'}")
        
        # 测试用例2: MyBatis危险参数
        test_finding_2 = {
            'type': 'SQL注入',
            'severity': 'high',
            'description': 'MyBatis中的SQL注入',
            'code_snippet': 'WHERE name = \'${name}\''
        }
        
        test_context_2 = {
            'frameworks': {'mybatis': True, 'spring_data_jpa': False},
            'architecture_layer': 'dao',
            'file_path': 'UserMapper.xml'
        }
        
        result_2 = calculator.calculate_confidence(test_finding_2, test_context_2)
        print(f"\n✅ 测试用例2 - MyBatis危险参数:")
        print(f"  置信度: {result_2.final_score:.2f}")
        print(f"  风险等级: {result_2.risk_level}")
        print(f"  主要原因: {result_2.reasoning[0] if result_2.reasoning else '无'}")
        
        # 测试用例3: DAO层权限验证误报
        test_finding_3 = {
            'type': '权限验证绕过',
            'severity': 'high',
            'description': 'DAO层缺少权限验证',
            'code_snippet': 'public List<Plan> findByUser(User user) { return planDao.findByUser(user); }'
        }
        
        test_context_3 = {
            'frameworks': {'spring_data_jpa': True},
            'architecture_layer': 'dao',
            'file_path': 'PlanDao.java'
        }
        
        result_3 = calculator.calculate_confidence(test_finding_3, test_context_3)
        print(f"\n✅ 测试用例3 - DAO层权限验证:")
        print(f"  置信度: {result_3.final_score:.2f}")
        print(f"  风险等级: {result_3.risk_level}")
        print(f"  主要原因: {result_3.reasoning[0] if result_3.reasoning else '无'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 置信度计算器测试失败: {e}")
        return False

def test_security_config():
    """测试安全配置系统"""
    print("\n⚙️ 测试安全配置系统...")
    
    try:
        config = get_security_config()
        
        # 测试框架检测
        java_code = """
        @Query("from User u where u.name = ?1")
        public User findByName(String name);
        """
        
        detected = config.detect_frameworks(java_code, "UserDao.java")
        detected_frameworks = [name for name, found in detected.items() if found]
        
        print(f"✅ 框架检测: {detected_frameworks}")
        
        # 测试安全模式检查
        if detected.get('spring_data_jpa'):
            is_safe = config.is_safe_pattern("@Query(\"from User u where u.name = ?1\")", 'spring_data_jpa')
            print(f"✅ 安全模式检查: {'安全' if is_safe else '危险'}")
        
        # 测试DAO层权限问题检查
        is_dao_issue = config.is_dao_layer_permission_issue("dao/UserDao.java", "findByUser")
        print(f"✅ DAO层权限问题检查: {'是误报' if is_dao_issue else '不是误报'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 安全配置系统测试失败: {e}")
        return False

def test_integration():
    """测试集成效果"""
    print("\n🔗 测试集成效果...")
    
    try:
        # 模拟一个完整的分析流程
        config = get_security_config()
        calculator = ConfidenceCalculator()
        
        # 模拟LLM返回的原始发现
        raw_findings = [
            {
                'type': 'SQL注入',
                'severity': 'high',
                'description': 'JPA查询中的潜在SQL注入风险',
                'code_snippet': '@Query("from Plan p where p.label like %?1%") Page<Plan> findBybasekey(String baseKey, long userid, Pageable pa);',
                'line': 49
            },
            {
                'type': '权限验证绕过',
                'severity': 'high', 
                'description': 'DAO层缺少权限验证',
                'code_snippet': 'return planDao.findBybasekey(baseKey, userid, pa);',
                'line': 36
            }
        ]
        
        file_path = "examples/test_oa-system/src/main/java/cn/gson/oasys/model/dao/plandao/PlanDao.java"
        code = """
        @Query("from Plan p where (p.label like %?1% or p.title like %?1%) and p.user.userId=?2")
        Page<Plan> findBybasekey (String baseKey, long userid,Pageable pa);
        """
        
        # 1. 框架检测
        frameworks = config.detect_frameworks(code, file_path)
        print(f"✅ 检测到框架: {[name for name, found in frameworks.items() if found]}")
        
        # 2. 误报过滤
        filtered_findings = []
        for finding in raw_findings:
            # 检查SQL注入误报
            if finding['type'] == 'SQL注入' and config.is_safe_sql_pattern(finding['code_snippet']):
                print(f"✅ 过滤SQL注入误报: {finding['description']}")
                continue
            
            # 检查权限验证误报
            if '权限' in finding['type'] and config.is_dao_layer_permission_issue(file_path, finding['code_snippet']):
                print(f"✅ 过滤权限验证误报: {finding['description']}")
                continue
            
            filtered_findings.append(finding)
        
        # 3. 置信度评估
        enhanced_findings = []
        for finding in filtered_findings:
            context = {
                'frameworks': frameworks,
                'architecture_layer': 'dao',
                'file_path': file_path
            }
            
            confidence_result = calculator.calculate_confidence(finding, context)
            finding['confidence'] = confidence_result.final_score
            finding['risk_level'] = confidence_result.risk_level
            finding['reasoning'] = confidence_result.reasoning
            
            enhanced_findings.append(finding)
        
        print(f"\n📊 处理结果:")
        print(f"  原始发现: {len(raw_findings)} 个")
        print(f"  过滤后: {len(filtered_findings)} 个")
        print(f"  最终结果: {len(enhanced_findings)} 个")
        
        if enhanced_findings:
            print(f"\n🎯 剩余问题:")
            for finding in enhanced_findings:
                print(f"  - {finding['type']}: 置信度 {finding['confidence']:.2f}, 风险 {finding['risk_level']}")
        else:
            print(f"\n🎉 所有误报都被成功过滤!")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始第二阶段改进效果测试\n")
    
    tests = [
        ("上下文分析器", test_context_analyzer),
        ("置信度计算器", test_confidence_calculator),
        ("安全配置系统", test_security_config),
        ("集成效果", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print(f"\n{'='*50}")
    print("📋 测试总结")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！第二阶段改进成功！")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步调试")
        return 1

if __name__ == "__main__":
    exit(main())
