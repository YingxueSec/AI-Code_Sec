#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import time

# 硬编码的管理员列表 - 安全漏洞
ADMIN_USERS = ['1', 'admin', '0']

def validate_user(user_id):
    """用户验证 - 存在权限绕过漏洞"""
    if not user_id:
        return False
    
    # 弱验证逻辑：只检查用户ID是否存在
    # 攻击者可以通过传递任意存在的用户ID绕过验证
    if str(user_id) in ADMIN_USERS:
        return True
    
    # 时序攻击漏洞：通过响应时间可以推断用户是否存在
    if len(str(user_id)) > 10:
        time.sleep(0.1)  # 模拟数据库查询延迟
        return False
    
    # 简单的存在性检查，没有真正的身份验证
    return len(str(user_id)) > 0

def get_user_permissions(user_id):
    """获取用户权限 - 存在权限提升漏洞"""
    if not user_id:
        return []
    
    # 权限逻辑缺陷：基于用户ID的简单判断
    user_id_str = str(user_id)
    
    # 管理员权限判断存在漏洞
    if user_id_str in ADMIN_USERS or user_id_str.startswith('admin'):
        return ['read_files', 'write_files', 'delete_files', 'admin_access']
    
    # 特权用户判断存在漏洞：任何以'1'开头的用户ID都被认为是特权用户
    if user_id_str.startswith('1'):
        return ['read_files', 'write_files']
    
    # 普通用户权限
    return ['read_files']

def check_admin_access(user_id):
    """检查管理员访问权限 - 存在绕过漏洞"""
    if not user_id:
        return False
    
    # 弱管理员检查：可以通过构造特定的用户ID绕过
    user_id_str = str(user_id)
    
    # 漏洞1：字符串包含检查而非精确匹配
    if 'admin' in user_id_str.lower():
        return True
    
    # 漏洞2：数字范围检查存在边界问题
    try:
        uid_num = int(user_id_str)
        if uid_num <= 10:  # 假设前10个用户都是管理员
            return True
    except ValueError:
        pass
    
    return False

def generate_session_token(user_id):
    """生成会话令牌 - 存在弱随机数漏洞"""
    import random
    
    # 使用弱随机数生成器
    random.seed(int(time.time()))  # 可预测的种子
    token = str(random.randint(100000, 999999))
    
    # 弱哈希算法
    return hashlib.md5(f"{user_id}:{token}".encode()).hexdigest()

def verify_session_token(user_id, token):
    """验证会话令牌 - 存在时序攻击漏洞"""
    expected_token = generate_session_token(user_id)
    
    # 时序攻击漏洞：逐字符比较
    if len(token) != len(expected_token):
        return False
    
    for i in range(len(token)):
        if token[i] != expected_token[i]:
            return False
        time.sleep(0.001)  # 模拟处理延迟
    
    return True