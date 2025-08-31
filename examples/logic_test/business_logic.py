#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复杂逻辑漏洞测试用例
测试AI是否能检测到更深层的业务逻辑问题
"""

import time
import hashlib
from decimal import Decimal

class BankAccount:
    def __init__(self, account_id, balance=0):
        self.account_id = account_id
        self.balance = Decimal(str(balance))
        self.is_locked = False
        self.failed_attempts = 0
        
    def transfer_money(self, to_account, amount):
        """转账功能 - 存在竞态条件漏洞"""
        # 逻辑漏洞1: 检查余额和扣款之间存在时间窗口
        if self.balance >= amount:
            # 模拟网络延迟或数据库操作
            time.sleep(0.1)  
            # 在这个时间窗口内，余额可能被其他操作修改
            self.balance -= amount
            to_account.balance += amount
            return True
        return False
    
    def withdraw(self, amount, pin):
        """取款功能 - 存在逻辑绕过漏洞"""
        # 逻辑漏洞2: 锁定检查在PIN验证之后
        if self._verify_pin(pin):
            if self.is_locked:  # 应该在PIN验证之前检查
                return False, "Account locked"
            
            if self.balance >= amount:
                self.balance -= amount
                return True, "Withdrawal successful"
            return False, "Insufficient funds"
        return False, "Invalid PIN"
    
    def _verify_pin(self, pin):
        """PIN验证 - 存在时序攻击漏洞"""
        correct_pin = "1234"
        # 逻辑漏洞3: 逐字符比较导致时序攻击
        for i, (a, b) in enumerate(zip(pin, correct_pin)):
            if a != b:
                self.failed_attempts += 1
                if self.failed_attempts >= 3:
                    self.is_locked = True
                return False
            time.sleep(0.01)  # 每个正确字符增加延迟
        return len(pin) == len(correct_pin)

class ShoppingCart:
    def __init__(self):
        self.items = []
        self.discount_applied = False
        
    def add_item(self, item_id, price, quantity=1):
        """添加商品 - 存在整数溢出漏洞"""
        # 逻辑漏洞4: 没有检查数量的合理范围
        if quantity < 0:
            # 负数数量可能导致退款而不是付款
            pass
        
        total_price = price * quantity  # 可能发生整数溢出
        self.items.append({
            'id': item_id,
            'price': price,
            'quantity': quantity,
            'total': total_price
        })
    
    def apply_discount(self, discount_code):
        """应用折扣 - 存在重复应用漏洞"""
        # 逻辑漏洞5: 可以重复应用折扣
        if discount_code == "SAVE20":
            if not self.discount_applied:  # 检查不够严格
                for item in self.items:
                    item['total'] *= 0.8  # 20% 折扣
                self.discount_applied = True
            return True
        return False
    
    def calculate_total(self):
        """计算总价 - 存在精度问题"""
        # 逻辑漏洞6: 浮点数精度问题
        total = 0.0  # 应该使用Decimal
        for item in self.items:
            total += item['total']
        return total

class UserSession:
    def __init__(self):
        self.sessions = {}
        
    def create_session(self, user_id, role="user"):
        """创建会话 - 存在会话固定漏洞"""
        # 逻辑漏洞7: 会话ID可预测
        session_id = hashlib.md5(f"{user_id}_{int(time.time())}".encode()).hexdigest()
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'role': role,
            'created_at': time.time(),
            'last_activity': time.time()
        }
        return session_id
    
    def elevate_privileges(self, session_id, admin_code):
        """权限提升 - 存在逻辑绕过漏洞"""
        if session_id not in self.sessions:
            return False
            
        session = self.sessions[session_id]
        
        # 逻辑漏洞8: 权限检查逻辑错误
        if admin_code == "admin123" or session['role'] == "admin":
            # 如果已经是admin，不需要验证admin_code
            session['role'] = "admin"
            return True
        
        # 逻辑漏洞9: 时间窗口攻击
        if time.time() - session['created_at'] < 300:  # 5分钟内
            # 新会话有特殊权限？这是错误的逻辑
            session['role'] = "privileged"
            return True
            
        return False

class PaymentProcessor:
    def __init__(self):
        self.processed_payments = set()
        
    def process_payment(self, payment_id, amount, card_number):
        """处理支付 - 存在重放攻击漏洞"""
        # 逻辑漏洞10: 重放攻击防护不足
        if payment_id in self.processed_payments:
            return False, "Payment already processed"
        
        # 逻辑漏洞11: 金额验证不足
        if amount <= 0:
            return False, "Invalid amount"
        
        # 模拟支付处理
        if self._validate_card(card_number):
            # 逻辑漏洞12: 在验证成功后才记录，存在竞态条件
            self.processed_payments.add(payment_id)
            return True, "Payment successful"
        
        return False, "Invalid card"
    
    def _validate_card(self, card_number):
        """信用卡验证 - 存在侧信道攻击"""
        # 逻辑漏洞13: 通过响应时间可以推断卡号有效性
        valid_prefixes = ["4", "5", "3"]  # Visa, MasterCard, Amex
        
        for prefix in valid_prefixes:
            if card_number.startswith(prefix):
                time.sleep(0.1)  # 有效前缀需要更多处理时间
                return len(card_number) >= 13
        
        return False

def vulnerable_password_reset(email, security_question, answer):
    """密码重置 - 存在逻辑绕过漏洞"""
    # 逻辑漏洞14: 安全问题验证可以绕过
    if not email:
        return False, "Email required"
    
    # 逻辑漏洞15: 空答案被接受
    if security_question and not answer:
        # 如果提供了安全问题但没有答案，应该拒绝
        pass  # 但这里没有返回False
    
    # 逻辑漏洞16: 邮箱验证不充分
    if "@" in email:  # 过于简单的邮箱验证
        return True, "Reset link sent"
    
    return False, "Invalid email"

def race_condition_vote(user_id, candidate_id):
    """投票功能 - 存在竞态条件漏洞"""
    # 逻辑漏洞17: 检查和记录之间的竞态条件
    votes_file = f"votes_{candidate_id}.txt"
    
    # 检查用户是否已投票
    try:
        with open(votes_file, 'r') as f:
            voted_users = f.read().splitlines()
            if str(user_id) in voted_users:
                return False, "Already voted"
    except FileNotFoundError:
        voted_users = []
    
    # 时间窗口：在这里可能发生竞态条件
    time.sleep(0.01)
    
    # 记录投票
    with open(votes_file, 'a') as f:
        f.write(f"{user_id}\n")
    
    return True, "Vote recorded"
