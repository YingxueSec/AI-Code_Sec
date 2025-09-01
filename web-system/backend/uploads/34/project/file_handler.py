#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import shutil

def read_user_file(filename):
    """读取用户文件 - 存在路径遍历漏洞"""
    # 直接拼接文件路径，没有路径验证
    base_path = "/var/www/uploads/"
    file_path = base_path + filename
    
    try:
        # 攻击者可以使用 ../../../etc/passwd 等路径遍历
        with open(file_path, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"

def process_upload(filename, file_content):
    """处理文件上传 - 存在命令注入漏洞"""
    # 不安全的文件名处理
    safe_filename = filename.replace(' ', '_')
    upload_path = f"/tmp/uploads/{safe_filename}"
    
    try:
        # 保存文件
        with open(upload_path, 'wb') as f:
            f.write(file_content)
        
        # 命令注入漏洞：直接在shell命令中使用文件名
        # 攻击者可以上传名为 "test.txt; rm -rf /" 的文件
        cmd = f"file {upload_path} && echo 'File processed: {filename}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        return f"Upload successful: {result.stdout}"
    except Exception as e:
        return f"Upload failed: {e}"

def delete_user_file(filename, user_id):
    """删除用户文件 - 存在路径遍历和命令注入漏洞"""
    # 路径遍历漏洞
    user_dir = f"/var/www/users/{user_id}/"
    file_path = user_dir + filename
    
    # 命令注入漏洞：使用shell命令删除文件
    cmd = f"rm -f {file_path}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return "File deleted successfully"
        else:
            return f"Delete failed: {result.stderr}"
    except Exception as e:
        return f"Delete error: {e}"

def backup_user_data(user_id, backup_name):
    """备份用户数据 - 存在命令注入漏洞"""
    user_dir = f"/var/www/users/{user_id}/"
    backup_path = f"/var/backups/{backup_name}.tar.gz"
    
    # 命令注入漏洞：直接使用用户输入构造命令
    cmd = f"tar -czf {backup_path} {user_dir}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return f"Backup created: {backup_path}"
    except Exception as e:
        return f"Backup failed: {e}"

def extract_archive(archive_path, extract_to):
    """解压文件 - 存在Zip Slip漏洞"""
    import zipfile
    
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            # 直接解压，没有路径验证
            # 攻击者可以创建包含 ../../../etc/passwd 路径的恶意zip文件
            zip_ref.extractall(extract_to)
        return "Archive extracted successfully"
    except Exception as e:
        return f"Extraction failed: {e}"

def get_file_info(filename):
    """获取文件信息 - 存在命令注入漏洞"""
    # 使用file命令获取文件信息，存在命令注入风险
    cmd = f"file {filename} && ls -la {filename}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"