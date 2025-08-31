from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"
    
    @property
    def action_display(self) -> str:
        """获取操作的中文显示"""
        action_map = {
            'login': '用户登录',
            'logout': '用户退出',
            'register': '用户注册',
            'audit_start': '开始代码审计',
            'audit_complete': '完成代码审计',
            'audit_cancel': '取消代码审计',
            'audit_delete': '删除审计任务',
            'file_upload': '文件上传',
            'report_export': '导出报告',
            'user_create': '创建用户',
            'user_update': '更新用户',
            'user_delete': '删除用户',
            'invitation_create': '创建邀请码',
            'invitation_use': '使用邀请码',
            'invitation_update': '更新邀请码',
            'invitation_delete': '删除邀请码',
            'profile_update': '更新个人资料',
            'password_change': '修改密码',
            'admin_access': '管理员访问',
            'system_config': '系统配置',
        }
        return action_map.get(self.action, self.action)
