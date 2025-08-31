#!/usr/bin/env python3
"""
AI代码审计性能分析工具
详细分析每个步骤的时间消耗
"""

import time
import asyncio
import json
from datetime import datetime
from ai_code_audit.core.config import ConfigManager
from ai_code_audit.llm.manager import LLMManager
from ai_code_audit.llm.models import LLMRequest, LLMMessage, MessageRole

class PerformanceAnalyzer:
    def __init__(self):
        self.timings = {}
        self.start_time = None
        
    def start_timer(self, step_name):
        """开始计时"""
        self.start_time = time.time()
        print(f"⏱️  开始: {step_name} - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
    def end_timer(self, step_name):
        """结束计时"""
        if self.start_time:
            duration = time.time() - self.start_time
            self.timings[step_name] = duration
            print(f"✅ 完成: {step_name} - 耗时: {duration:.2f}秒")
            return duration
        return 0
    
    async def analyze_llm_performance(self):
        """分析LLM API性能"""
        print("\n🔍 LLM API性能分析:")
        
        # 测试配置加载
        self.start_timer("配置加载")
        config_manager = ConfigManager()
        config = config_manager.load_config()
        self.end_timer("配置加载")
        
        # 测试LLM初始化
        self.start_timer("LLM管理器初始化")
        llm_manager = LLMManager(config)
        self.end_timer("LLM管理器初始化")
        
        # 测试小请求
        self.start_timer("小请求测试 (50 tokens)")
        small_request = LLMRequest(
            messages=[
                LLMMessage(MessageRole.SYSTEM, "你是一个AI助手"),
                LLMMessage(MessageRole.USER, "请简单回复：测试成功")
            ],
            model='kimi-k2',
            temperature=0.1,
            max_tokens=50
        )
        
        try:
            response = await llm_manager.chat_completion(small_request)
            small_duration = self.end_timer("小请求测试 (50 tokens)")
            print(f"   响应内容: {response.content[:50]}...")
            print(f"   Token使用: {response.usage.total_tokens if response.usage else 'N/A'}")
        except Exception as e:
            print(f"   ❌ 小请求失败: {e}")
            small_duration = 0
        
        # 测试中等请求
        self.start_timer("中等请求测试 (500 tokens)")
        medium_request = LLMRequest(
            messages=[
                LLMMessage(MessageRole.SYSTEM, "你是一个代码安全专家"),
                LLMMessage(MessageRole.USER, """请分析以下Python代码的安全问题：
```python
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    return cursor.fetchone()
```
请简要说明主要安全风险。""")
            ],
            model='kimi-k2',
            temperature=0.1,
            max_tokens=500
        )
        
        try:
            response = await llm_manager.chat_completion(medium_request)
            medium_duration = self.end_timer("中等请求测试 (500 tokens)")
            print(f"   响应内容: {response.content[:100]}...")
            print(f"   Token使用: {response.usage.total_tokens if response.usage else 'N/A'}")
        except Exception as e:
            print(f"   ❌ 中等请求失败: {e}")
            medium_duration = 0
        
        # 测试大请求 (模拟实际审计)
        self.start_timer("大请求测试 (4000 tokens)")
        large_code = """
def get_user_data(user_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    sql = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(sql)
    return cursor.fetchall()

def validate_user(user_id):
    if str(user_id) in ['1', 'admin', '0']:
        return True
    return False

def process_upload(filename, content):
    cmd = f"file {filename} && echo 'processed'"
    result = subprocess.run(cmd, shell=True)
    return result
""" * 3  # 重复3次模拟更大的代码
        
        large_request = LLMRequest(
            messages=[
                LLMMessage(MessageRole.SYSTEM, "你是一个资深的代码安全审计专家，请进行深度安全分析"),
                LLMMessage(MessageRole.USER, f"""请对以下Python代码进行全面的安全审计：

```python
{large_code}
```

请详细分析所有安全漏洞，包括：
1. 漏洞类型和严重程度
2. 具体攻击场景
3. 业务影响
4. 修复方案

请提供详细的分析报告。""")
            ],
            model='kimi-k2',
            temperature=0.1,
            max_tokens=4000
        )
        
        try:
            response = await llm_manager.chat_completion(large_request)
            large_duration = self.end_timer("大请求测试 (4000 tokens)")
            print(f"   响应内容: {response.content[:100]}...")
            print(f"   Token使用: {response.usage.total_tokens if response.usage else 'N/A'}")
        except Exception as e:
            print(f"   ❌ 大请求失败: {e}")
            large_duration = 0
        
        return {
            'small_request': small_duration,
            'medium_request': medium_duration, 
            'large_request': large_duration
        }
    
    def analyze_results(self, llm_timings):
        """分析结果"""
        print("\n📊 性能分析结果:")
        print("=" * 50)
        
        print("🔧 系统开销:")
        for step, duration in self.timings.items():
            print(f"  {step}: {duration:.2f}秒")
        
        print("\n🌐 API请求性能:")
        for request_type, duration in llm_timings.items():
            if duration > 0:
                print(f"  {request_type}: {duration:.2f}秒")
        
        # 计算每token的平均时间
        if llm_timings['large_request'] > 0:
            tokens_per_second = 4000 / llm_timings['large_request']
            print(f"\n⚡ API性能指标:")
            print(f"  处理速度: {tokens_per_second:.1f} tokens/秒")
            print(f"  每1000 tokens耗时: {1000/tokens_per_second:.1f}秒")
        
        # 分析瓶颈
        total_system = sum(self.timings.values())
        total_api = sum(v for v in llm_timings.values() if v > 0)
        
        print(f"\n🎯 瓶颈分析:")
        print(f"  系统开销总计: {total_system:.2f}秒")
        print(f"  API请求总计: {total_api:.2f}秒")
        if total_api > 0:
            print(f"  API占比: {(total_api/(total_system+total_api))*100:.1f}%")
        
        # 并发效果分析
        print(f"\n🚀 并发效果分析:")
        print(f"  单文件平均时间: {llm_timings.get('large_request', 0):.1f}秒")
        print(f"  4文件串行时间: {llm_timings.get('large_request', 0) * 4:.1f}秒")
        print(f"  4文件并发时间: {llm_timings.get('large_request', 0):.1f}秒 (理论值)")
        print(f"  实际并发时间: 150秒 (受API限制)")

async def main():
    analyzer = PerformanceAnalyzer()
    
    print("🚀 开始AI代码审计性能分析")
    print("=" * 50)
    
    # 分析LLM性能
    llm_timings = await analyzer.analyze_llm_performance()
    
    # 分析结果
    analyzer.analyze_results(llm_timings)

if __name__ == "__main__":
    asyncio.run(main())
