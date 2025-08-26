#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试编码修复效果
"""

import sys
import os

# 复制main.py中的编码设置
def setup_encoding():
    """设置编码确保支持Unicode字符"""
    try:
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 重新配置标准输出和错误输出的编码
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            
        # 在Windows上设置控制台编码
        if sys.platform == 'win32':
            try:
                import ctypes
                # 设置控制台输出为UTF-8
                ctypes.windll.kernel32.SetConsoleOutputCP(65001)
                ctypes.windll.kernel32.SetConsoleCP(65001)
            except:
                pass
                
    except Exception:
        # 忽略编码设置错误
        pass

def safe_print(text, **kwargs):
    """安全输出函数，处理编码问题"""
    try:
        # 先尝试直接输出
        print(text, **kwargs)
        sys.stdout.flush()
    except UnicodeEncodeError:
        try:
            # 尝试使用gbk编码（Windows默认）
            encoded_text = text.encode('gbk', errors='replace').decode('gbk')
            print(encoded_text, **kwargs)
            sys.stdout.flush()
        except:
            try:
                # 最后备选：使用ascii安全编码
                safe_text = text.encode('ascii', errors='replace').decode('ascii')
                print(safe_text, **kwargs)
                sys.stdout.flush()
            except:
                # 最终备选：只输出ASCII字符
                import re
                ascii_only = re.sub(r'[^\x00-\x7F]', '?', text)
                print(ascii_only, **kwargs)
                sys.stdout.flush()

def test_encoding():
    """测试编码处理"""
    setup_encoding()
    
    print("=" * 60)
    print("编码测试开始...")
    print("=" * 60)
    
    # 测试中文输出
    safe_print("1. 中文测试: 这是一个测试")
    safe_print("2. English test: This is a test")
    
    # 测试程序输出格式
    safe_print("[配置] 审计配置:")
    safe_print("  项目路径: examples/test_oa-system")
    safe_print("  审计模板: owasp_top_10_2021")
    safe_print("")
    safe_print("[INFO] 开始审计项目: examples/test_oa-system")
    safe_print("[SUCCESS] 发现 425 个文件")
    safe_print("[WARNING] 审计失败: 测试错误")
    safe_print("[PASS] 未发现安全问题")
    
    print("=" * 60)
    print("编码测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_encoding()