#!/usr/bin/env python3
"""
AI代码安全审计系统 - 自动化测试脚本
用于验证所有API接口和核心功能
"""

import requests
import json
import time
import os
from typing import Dict, Any

class SystemTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.token = None
        self.admin_token = None
        
    def log(self, message: str, level: str = "INFO"):
        """打印日志"""
        print(f"[{level}] {message}")
        
    def test_health_check(self) -> bool:
        """测试服务器健康状态"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            if response.status_code == 200:
                self.log("✅ 后端服务器运行正常")
                return True
            else:
                self.log("❌ 后端服务器响应异常", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ 无法连接到后端服务器: {e}", "ERROR")
            return False
    
    def test_user_auth(self) -> bool:
        """测试用户认证功能"""
        try:
            # 测试登录
            login_data = {
                "username_or_email": "newuser",
                "password": "password123"
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.admin_token = data["access_token"]  # newuser是管理员
                self.log("✅ 用户登录成功")
                
                # 测试获取用户信息
                headers = {"Authorization": f"Bearer {self.token}"}
                profile_response = requests.get(
                    f"{self.api_url}/auth/profile",
                    headers=headers
                )
                
                if profile_response.status_code == 200:
                    user_data = profile_response.json()
                    self.log(f"✅ 获取用户信息成功: {user_data['username']} ({user_data['role']})")
                    return True
                else:
                    self.log("❌ 获取用户信息失败", "ERROR")
                    return False
            else:
                self.log(f"❌ 用户登录失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 用户认证测试失败: {e}", "ERROR")
            return False
    
    def test_audit_templates(self) -> bool:
        """测试审计模板接口"""
        try:
            response = requests.get(f"{self.api_url}/audit/templates")
            
            if response.status_code == 200:
                templates = response.json()["templates"]
                self.log(f"✅ 获取审计模板成功，共 {len(templates)} 个模板")
                for template in templates:
                    self.log(f"   - {template['display_name']}: {template['description']}")
                return True
            else:
                self.log(f"❌ 获取审计模板失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 审计模板测试失败: {e}", "ERROR")
            return False
    
    def test_file_upload_and_audit(self) -> bool:
        """测试文件上传和审计功能"""
        if not self.token:
            self.log("❌ 需要先登录", "ERROR")
            return False
            
        try:
            # 准备测试文件
            test_file_path = "/Users/admin/AnyProjects/AttackSec/A-AI/Last/AI-Code_Sec-2.6.0-cursor/web-system/test_vulnerable_code.py"
            
            if not os.path.exists(test_file_path):
                self.log("❌ 测试文件不存在", "ERROR")
                return False
            
            # 上传文件
            headers = {"Authorization": f"Bearer {self.token}"}
            files = {"files": open(test_file_path, "rb")}
            data = {
                "project_name": "Security Test Project",
                "description": "自动化测试 - 包含多种安全漏洞的代码",
                "config_params": json.dumps({
                    "template": "security_audit_chinese",
                    "scan_depth": "deep",
                    "enable_ai_analysis": True
                })
            }
            
            response = requests.post(
                f"{self.api_url}/audit/upload",
                headers=headers,
                files=files,
                data=data
            )
            files["files"].close()
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data["id"]
                self.log(f"✅ 文件上传成功，任务ID: {task_id}")
                
                # 启动审计
                start_response = requests.post(
                    f"{self.api_url}/audit/start/{task_id}",
                    headers=headers
                )
                
                if start_response.status_code == 200:
                    self.log("✅ 审计任务启动成功")
                    
                    # 监控任务进度
                    return self.monitor_audit_progress(task_id)
                else:
                    self.log(f"❌ 启动审计失败: {start_response.text}", "ERROR")
                    return False
            else:
                self.log(f"❌ 文件上传失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 文件上传和审计测试失败: {e}", "ERROR")
            return False
    
    def monitor_audit_progress(self, task_id: int, max_wait: int = 60) -> bool:
        """监控审计进度"""
        headers = {"Authorization": f"Bearer {self.token}"}
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # 获取任务进度
                progress_response = requests.get(
                    f"{self.api_url}/audit/tasks/{task_id}/progress",
                    headers=headers
                )
                
                if progress_response.status_code == 200:
                    progress = progress_response.json()
                    status = progress["status"]
                    percent = progress["progress_percent"]
                    
                    self.log(f"📊 任务进度: {status} - {percent:.1f}%")
                    
                    if status == "completed":
                        self.log("✅ 审计任务完成")
                        return self.check_audit_results(task_id)
                    elif status == "failed":
                        error_msg = progress.get("error_message", "未知错误")
                        self.log(f"❌ 审计任务失败: {error_msg}", "ERROR")
                        return False
                    
                time.sleep(2)
                
            except Exception as e:
                self.log(f"❌ 获取任务进度失败: {e}", "ERROR")
                return False
        
        self.log("⚠️ 审计任务超时", "WARNING")
        return False
    
    def check_audit_results(self, task_id: int) -> bool:
        """检查审计结果"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{self.api_url}/audit/results/{task_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                results = response.json()
                
                self.log("📋 审计结果:")
                self.log(f"   高危问题: {results['high_issues']}")
                self.log(f"   中危问题: {results['medium_issues']}")
                self.log(f"   低危问题: {results['low_issues']}")
                self.log(f"   总体置信度: {results['total_confidence']:.1f}%")
                
                findings = results.get("findings", [])
                if findings:
                    self.log(f"   发现 {len(findings)} 个具体问题:")
                    for finding in findings[:5]:  # 只显示前5个
                        severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🔵"}
                        emoji = severity_emoji.get(finding["severity"], "⚪")
                        self.log(f"     {emoji} {finding['type']}: {finding['description']}")
                
                if results.get("summary"):
                    self.log(f"   AI分析摘要: {results['summary']}")
                
                self.log("✅ 审计结果获取成功")
                return True
            else:
                self.log(f"❌ 获取审计结果失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 检查审计结果失败: {e}", "ERROR")
            return False
    
    def test_admin_features(self) -> bool:
        """测试管理员功能"""
        if not self.admin_token:
            self.log("❌ 需要管理员权限", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # 测试系统统计
            stats_response = requests.get(
                f"{self.api_url}/admin/stats",
                headers=headers
            )
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                self.log("📊 系统统计:")
                self.log(f"   总用户数: {stats['total_users']}")
                self.log(f"   活跃用户: {stats['active_users']}")
                self.log(f"   总任务数: {stats['total_tasks']}")
                self.log(f"   已完成任务: {stats['completed_tasks']}")
                self.log("✅ 管理员统计功能正常")
            else:
                self.log(f"❌ 获取系统统计失败: {stats_response.text}", "ERROR")
                return False
            
            # 测试用户列表
            users_response = requests.get(
                f"{self.api_url}/admin/users",
                headers=headers
            )
            
            if users_response.status_code == 200:
                users = users_response.json()
                self.log(f"👥 用户列表 (共 {len(users)} 个用户):")
                for user in users:
                    role_emoji = "👑" if user["role"] == "admin" else "👤"
                    self.log(f"   {role_emoji} {user['username']} ({user['email']}) - {user['role']}")
                self.log("✅ 管理员用户管理功能正常")
                return True
            else:
                self.log(f"❌ 获取用户列表失败: {users_response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 管理员功能测试失败: {e}", "ERROR")
            return False
    
    def test_task_management(self) -> bool:
        """测试任务管理功能"""
        if not self.token:
            self.log("❌ 需要先登录", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{self.api_url}/audit/tasks",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                tasks = data["tasks"]
                self.log(f"📝 任务列表 (共 {data['total']} 个任务):")
                
                for task in tasks[:5]:  # 只显示前5个
                    status_emoji = {
                        "pending": "⏳",
                        "running": "🔄", 
                        "completed": "✅",
                        "failed": "❌",
                        "cancelled": "⏹️"
                    }
                    emoji = status_emoji.get(task["status"], "❓")
                    self.log(f"   {emoji} {task['project_name']} - {task['status']} ({task['progress_percent']:.1f}%)")
                
                self.log("✅ 任务管理功能正常")
                return True
            else:
                self.log(f"❌ 获取任务列表失败: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 任务管理测试失败: {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        self.log("🚀 开始系统全面测试...")
        
        results = {}
        
        # 1. 健康检查
        self.log("\n" + "="*50)
        self.log("1. 服务器健康检查")
        self.log("="*50)
        results["health_check"] = self.test_health_check()
        
        if not results["health_check"]:
            self.log("❌ 服务器不可用，停止测试", "ERROR")
            return results
        
        # 2. 用户认证
        self.log("\n" + "="*50)
        self.log("2. 用户认证功能测试")
        self.log("="*50)
        results["user_auth"] = self.test_user_auth()
        
        # 3. 审计模板
        self.log("\n" + "="*50)
        self.log("3. 审计模板功能测试")
        self.log("="*50)
        results["audit_templates"] = self.test_audit_templates()
        
        # 4. 任务管理
        self.log("\n" + "="*50)
        self.log("4. 任务管理功能测试")
        self.log("="*50)
        results["task_management"] = self.test_task_management()
        
        # 5. 文件上传和审计
        self.log("\n" + "="*50)
        self.log("5. 文件上传和AI审计功能测试")
        self.log("="*50)
        results["file_upload_audit"] = self.test_file_upload_and_audit()
        
        # 6. 管理员功能
        self.log("\n" + "="*50)
        self.log("6. 管理员功能测试")
        self.log("="*50)
        results["admin_features"] = self.test_admin_features()
        
        # 总结
        self.log("\n" + "="*50)
        self.log("🎯 测试结果总结")
        self.log("="*50)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log(f"\n总体结果: {passed_tests}/{total_tests} 测试通过")
        
        if passed_tests == total_tests:
            self.log("🎉 所有测试通过！系统运行正常")
        else:
            self.log("⚠️ 部分测试失败，需要检查相关功能")
        
        return results

if __name__ == "__main__":
    print("AI代码安全审计系统 - 自动化测试")
    print("=" * 60)
    
    tester = SystemTester()
    results = tester.run_all_tests()
    
    # 退出码
    exit_code = 0 if all(results.values()) else 1
    exit(exit_code)
