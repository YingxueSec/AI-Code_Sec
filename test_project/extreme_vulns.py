#!/usr/bin/env python3
"""
极端明显的安全漏洞代码 - 测试AI检测能力
包含15种常见高危安全漏洞
"""

import os
import pickle
import subprocess
import sqlite3
import hashlib

# 1. 硬编码密码和密钥 - 高危
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"
SECRET_KEY = "super_secret_key"

# 2. SQL注入漏洞 - 高危
def get_user_by_id(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # 直接字符串拼接，明显的SQL注入
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    return cursor.fetchone()

# 3. 命令注入漏洞 - 高危
def run_command(filename):
    # 直接执行用户输入，极度危险
    command = f"cat {filename} && ls -la"
    os.system(command)

# 4. 路径遍历漏洞 - 高危
def read_file(filename):
    # 没有任何路径验证
    with open(f"/var/data/{filename}", 'r') as f:
        return f.read()

# 5. 不安全的反序列化 - 高危
def load_user_data(serialized_data):
    # pickle.loads是极度危险的
    return pickle.loads(serialized_data)

# 6. 弱密码哈希 - 中危
def hash_password(password):
    # MD5已被认为不安全
    return hashlib.md5(password.encode()).hexdigest()

# 7. 明文密码存储 - 高危
def save_user(username, password):
    with open('users.txt', 'a') as f:
        f.write(f"{username}:{password}\n")

# 8. 没有身份验证的敏感操作 - 高危
def delete_all_users():
    # 没有任何权限检查
    os.system("rm -rf /var/users/*")

# 9. 信息泄露 - 中危
def debug_error():
    try:
        1/0
    except Exception as e:
        # 泄露内部错误信息
        return f"Internal error: {e.__class__.__name__} in {__file__} line {e.__traceback__.tb_lineno}"

# 10. 不安全的随机数 - 低危
import random
def generate_token():
    # 使用不安全的随机数生成器
    return str(random.randint(1000, 9999))

# 11. 不安全的文件权限 - 中危
def create_config_file():
    with open('/tmp/config.conf', 'w') as f:
        f.write(f"api_key={API_KEY}\n")
    # 设置过于宽松的权限
    os.chmod('/tmp/config.conf', 0o777)

# 12. 时序攻击漏洞 - 中危
def check_password(input_password, real_password):
    # 字符逐一比较会泄露密码长度信息
    if len(input_password) != len(real_password):
        return False
    for i in range(len(input_password)):
        if input_password[i] != real_password[i]:
            return False
    return True

# 13. XXE攻击漏洞 - 高危
import xml.etree.ElementTree as ET
def parse_xml(xml_data):
    # 没有禁用外部实体，容易受到XXE攻击
    root = ET.fromstring(xml_data)
    return root

# 14. 不安全的重定向 - 中危
def redirect_user(url):
    # 没有验证URL，可能导致钓鱼攻击
    return f"<script>window.location.href='{url}'</script>"

# 15. 缓冲区溢出风险（Python中较少见，但模拟C风格）
def unsafe_copy(data):
    buffer = [0] * 10
    # 没有边界检查
    for i in range(len(data)):
        if i < len(buffer):
            buffer[i] = data[i]
        else:
            # 这会在C中造成溢出，Python中会出错
            pass

if __name__ == "__main__":
    print("这个文件包含15种明显的安全漏洞")
    
    # 危险的示例调用
    get_user_by_id("1' OR '1'='1")  # SQL注入
    run_command("test.txt; rm -rf /")  # 命令注入
    read_file("../../../etc/passwd")  # 路径遍历
    
    print("如果AI系统正常工作，应该检测出多个高危漏洞")
