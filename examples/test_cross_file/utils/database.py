#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import mysql.connector

def execute_raw_query(query):
    """执行原始SQL查询 - 存在SQL注入漏洞"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 直接执行用户提供的查询，存在SQL注入风险
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return str(results)
    except Exception as e:
        conn.close()
        return f"Database error: {e}"

def get_user_data(user_id):
    """获取用户数据 - 存在SQL注入漏洞"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 字符串拼接构造SQL，存在注入风险
    sql = f"SELECT * FROM users WHERE id = {user_id}"
    
    try:
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        conn.close()
        return None

def search_users(search_term):
    """搜索用户 - 存在SQL注入漏洞"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 直接拼接搜索条件
    sql = f"SELECT * FROM users WHERE name LIKE '%{search_term}%' OR email LIKE '%{search_term}%'"
    
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return []

def update_user_status(user_id, status):
    """更新用户状态 - 存在SQL注入漏洞"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 动态构造UPDATE语句
    sql = f"UPDATE users SET status = '{status}' WHERE id = {user_id}"
    
    try:
        cursor.execute(sql)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False