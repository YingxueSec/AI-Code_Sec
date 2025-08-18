#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request
from utils.database import execute_raw_query, get_user_data
from utils.auth import validate_user, get_user_permissions
from utils.file_handler import read_user_file, process_upload

app = Flask(__name__)

@app.route('/user/<user_id>')
def get_user(user_id):
    """获取用户信息 - 存在跨文件SQL注入风险"""
    # 直接传递用户输入到数据库查询函数
    # 这里看起来安全，但实际上execute_raw_query函数存在SQL注入
    user_data = get_user_data(user_id)
    return user_data

@app.route('/admin/query')
def admin_query():
    """管理员查询 - 跨文件权限绕过风险"""
    query = request.args.get('q')
    user_id = request.args.get('user_id')
    
    # 调用权限验证，但验证函数本身存在缺陷
    if validate_user(user_id):
        # 直接执行原始SQL查询
        result = execute_raw_query(query)
        return result
    else:
        return "Access denied"

@app.route('/file/<filename>')
def get_file(filename):
    """文件读取 - 跨文件路径遍历风险"""
    user_id = request.args.get('user_id')
    
    # 权限检查看起来正常
    permissions = get_user_permissions(user_id)
    if 'read_files' in permissions:
        # 但文件读取函数存在路径遍历漏洞
        content = read_user_file(filename)
        return content
    return "Permission denied"

@app.route('/upload', methods=['POST'])
def upload_file():
    """文件上传 - 跨文件命令注入风险"""
    if 'file' not in request.files:
        return "No file"
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    # 权限验证
    if validate_user(user_id):
        # 文件处理函数存在命令注入漏洞
        result = process_upload(file.filename, file.read())
        return result
    return "Access denied"

if __name__ == '__main__':
    app.run(debug=True)