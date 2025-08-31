#!/usr/bin/env python3
"""
包含多种常见安全漏洞的测试代码
用于测试AI审计引擎的检测能力
"""

import os
import sqlite3
import subprocess
import pickle
import hashlib

# 1. SQL注入漏洞
def get_user_data(user_id):
    """SQL注入漏洞示例"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 危险：直接拼接SQL语句
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    return cursor.fetchall()

# 2. 命令注入漏洞
def run_system_command(filename):
    """命令注入漏洞示例"""
    # 危险：直接执行用户输入
    command = f"cat {filename}"
    result = os.system(command)
    return result

# 3. 路径遍历漏洞
def read_file(filename):
    """路径遍历漏洞示例"""
    # 危险：没有验证文件路径
    with open(f"/var/www/uploads/{filename}", 'r') as f:
        return f.read()

# 4. 不安全的反序列化
def load_user_session(session_data):
    """不安全反序列化漏洞示例"""
    # 危险：直接反序列化用户数据
    return pickle.loads(session_data)

# 5. 硬编码密码
def connect_to_database():
    """硬编码密码漏洞示例"""
    # 危险：硬编码敏感信息
    username = "admin"
    password = "password123"
    host = "192.168.1.100"
    
    return f"mysql://{username}:{password}@{host}/database"

# 6. 弱加密算法
def hash_password(password):
    """弱加密算法漏洞示例"""
    # 危险：使用不安全的哈希算法
    return hashlib.md5(password.encode()).hexdigest()

# 7. 未验证的重定向
def redirect_user(url):
    """开放重定向漏洞示例"""
    # 危险：未验证重定向URL
    return f"<script>window.location.href='{url}'</script>"

# 8. 竞态条件
import threading
import time

shared_counter = 0

def increment_counter():
    """竞态条件漏洞示例"""
    global shared_counter
    # 危险：没有同步机制
    temp = shared_counter
    time.sleep(0.001)  # 模拟处理时间
    shared_counter = temp + 1

# 9. 信息泄露
def debug_info():
    """信息泄露漏洞示例"""
    # 危险：泄露敏感调试信息
    import traceback
    try:
        1/0
    except Exception as e:
        return traceback.format_exc()

# 10. CSRF漏洞相关代码
def process_payment(amount, account):
    """CSRF漏洞示例"""
    # 危险：没有CSRF token验证
    if amount > 0:
        return f"Transferring ${amount} to {account}"

# 11. XSS漏洞
def display_user_comment(comment):
    """XSS漏洞示例"""
    # 危险：直接输出用户内容
    return f"<div>{comment}</div>"

# 12. 不安全的随机数生成
import random

def generate_session_token():
    """弱随机数生成漏洞示例"""
    # 危险：使用不安全的随机数生成器
    return str(random.randint(1000000, 9999999))

# 13. 缓冲区溢出相关（Python中较少见，但模拟C风格代码）
def unsafe_copy(source):
    """模拟缓冲区相关问题"""
    # 危险：没有长度检查
    buffer = [0] * 10
    for i, char in enumerate(source):
        buffer[i] = char  # 可能越界

# 14. 不安全的文件权限
def create_temp_file():
    """不安全文件权限示例"""
    # 危险：创建的文件权限过于宽松
    filename = "/tmp/sensitive_data.txt"
    with open(filename, 'w') as f:
        f.write("sensitive information")
    os.chmod(filename, 0o777)

# 15. 密码验证绕过
def authenticate_user(username, password):
    """密码验证绕过漏洞示例"""
    # 危险：逻辑错误
    if username == "admin":
        if password:  # 只检查密码是否存在，不验证内容
            return True
    return False

if __name__ == "__main__":
    print("这是一个包含多种安全漏洞的测试文件")
    print("用于测试AI安全审计系统的检测能力")
    
    # 示例调用
    get_user_data("1 OR 1=1")  # SQL注入
    run_system_command("file.txt; rm -rf /")  # 命令注入
    read_file("../../../etc/passwd")  # 路径遍历
