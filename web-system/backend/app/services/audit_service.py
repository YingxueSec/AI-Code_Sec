"""
审计服务 - 集成现有的AI代码审计引擎
"""

import asyncio
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import sys
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, UploadFile

from app.models.audit import AuditTask, AuditResult, AuditFile, TaskStatus, FileStatus
from app.models.user import User
from app.core.config import settings

# 添加AI审计引擎到Python路径
audit_engine_path = str(Path(__file__).parent.parent.parent.parent.parent)
if audit_engine_path not in sys.path:
    sys.path.insert(0, audit_engine_path)


class AuditService:
    
    @staticmethod
    async def create_audit_task(
        db: AsyncSession,
        user: User,
        project_name: str,
        description: Optional[str] = None,
        config_params: Optional[Dict[str, Any]] = None
    ) -> AuditTask:
        """创建审计任务"""
        
        # 创建审计任务记录
        task = AuditTask(
            user_id=user.id,
            project_name=project_name,
            description=description or f"{project_name} 的安全审计",
            status=TaskStatus.pending,
            config_params=config_params or {},
            total_files=0,
            analyzed_files=0,
            progress_percent=0.0
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        return task
    
    @staticmethod
    async def upload_project_files(
        task_id: int,
        files: List[UploadFile],
        db: AsyncSession
    ) -> str:
        """上传项目文件并解压到临时目录"""
        
        try:
            # 创建任务专用目录
            task_dir = Path(settings.UPLOAD_PATH) / str(task_id)
            task_dir.mkdir(parents=True, exist_ok=True)
            
            project_dir = task_dir / "project"
            project_dir.mkdir(exist_ok=True)
            
            total_files = 0
            
            for file in files:
                file_path = task_dir / file.filename
                
                # 保存上传的文件
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                # 如果是压缩文件，解压到project目录
                if file.filename.endswith(('.zip', '.tar.gz', '.rar')):
                    try:
                        if file.filename.endswith('.zip'):
                            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                                zip_ref.extractall(project_dir)
                                total_files += len(zip_ref.namelist())
                        # TODO: 添加其他压缩格式的支持
                        
                        # 删除压缩文件
                        file_path.unlink()
                        
                    except Exception as e:
                        raise HTTPException(status_code=400, detail=f"解压文件失败: {str(e)}")
                else:
                    # 直接文件，移动到project目录
                    shutil.move(str(file_path), str(project_dir / file.filename))
                    total_files += 1
        
            # 更新任务的文件总数
            await db.execute(
                update(AuditTask)
                .where(AuditTask.id == task_id)
                .values(total_files=total_files)
            )
            await db.commit()
            
            # 验证项目目录确实包含文件
            if total_files == 0:
                raise HTTPException(status_code=400, detail="未找到有效的项目文件")
            
            return str(project_dir)
            
        except Exception as e:
            # 清理部分上传的文件
            task_dir = Path(settings.UPLOAD_PATH) / str(task_id)
            if task_dir.exists():
                shutil.rmtree(task_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=f"文件上传失败: {str(e)}")
    
    @staticmethod
    async def start_audit_analysis(
        task_id: int,
        project_path: str,
        user: User,
        db: AsyncSession
    ) -> bool:
        """开始异步审计分析"""
        
        try:
            # 更新任务状态为运行中
            await db.execute(
                update(AuditTask)
                .where(AuditTask.id == task_id)
                .values(
                    status=TaskStatus.running,
                    started_at=datetime.utcnow(),
                    progress_percent=5.0
                )
            )
            await db.commit()
            
            # 在后台启动审计任务
            asyncio.create_task(
                AuditService._run_audit_analysis(task_id, project_path, user, db)
            )
            
            return True
            
        except Exception as e:
            # 更新任务状态为失败
            await db.execute(
                update(AuditTask)
                .where(AuditTask.id == task_id)
                .values(
                    status=TaskStatus.failed,
                    error_message=str(e),
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            raise HTTPException(status_code=500, detail=f"启动审计失败: {str(e)}")
    
    @staticmethod
    async def _run_audit_analysis(
        task_id: int,
        project_path: str,
        user: User,
        db: AsyncSession
    ):
        """运行实际的审计分析（后台任务）"""
        
        try:
            # 导入AI审计引擎
            from ai_code_audit import audit_project
            
            # 更新进度：开始分析
            await AuditService._update_progress(db, task_id, 10.0, "正在分析项目结构...")
            
            # 切换到正确的工作目录，确保能找到配置文件
            original_cwd = os.getcwd()
            ai_engine_root = str(Path(__file__).parent.parent.parent.parent.parent)
            os.chdir(ai_engine_root)
            
            # 配置审计参数
            output_file = Path(settings.REPORTS_PATH) / f"task_{task_id}_results.json"
            
            # 转换项目路径为绝对路径
            absolute_project_path = str(Path(original_cwd) / project_path)
            absolute_output_file = str(Path(original_cwd) / output_file)
            
            audit_params = {
                'project_path': absolute_project_path,
                'output_file': absolute_output_file,
                'template': 'owasp_top_10_2021',
                'max_files': 100,  # 限制文件数量避免超时
                'show_filter_stats': True,
                'enable_cross_file': True,
                'enable_frontend_opt': True,
                'enable_confidence_calc': True,
                'enable_filter': True,
                'min_confidence': 0.3,
                'max_confidence': 1.0,
                'quick_mode': False,
                'verbose': False,
                'debug': False,
                'show_timing': True
            }
            
            # 更新进度：开始AI分析
            await AuditService._update_progress(db, task_id, 30.0, "正在进行AI安全分析...")
            
            # 调用AI审计引擎
            results = await audit_project(**audit_params)
            
            # 更新进度：处理结果
            await AuditService._update_progress(db, task_id, 80.0, "正在处理分析结果...")
            
            # 保存分析结果到数据库
            await AuditService._save_audit_results(db, task_id, results, project_path)
            
            # 记录Token使用（如果有的话）
            await AuditService._record_token_usage(db, task_id, user, results)
            
            # 更新任务状态为完成
            await db.execute(
                update(AuditTask)
                .where(AuditTask.id == task_id)
                .values(
                    status=TaskStatus.completed,
                    progress_percent=100.0,
                    completed_at=datetime.utcnow(),
                    analyzed_files=results.get('total_files', 0)
                )
            )
            await db.commit()
            
            # 恢复原始工作目录
            os.chdir(original_cwd)
            
        except Exception as e:
            # 恢复原始工作目录
            try:
                os.chdir(original_cwd)
            except:
                pass
                
            # 记录错误并更新任务状态
            error_message = f"审计分析失败: {str(e)}"
            
            await db.execute(
                update(AuditTask)
                .where(AuditTask.id == task_id)
                .values(
                    status=TaskStatus.failed,
                    error_message=error_message,
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            print(f"审计任务 {task_id} 失败: {e}")
    
    @staticmethod
    async def _update_progress(
        db: AsyncSession,
        task_id: int,
        progress: float,
        message: str = None
    ):
        """更新任务进度"""
        update_data = {"progress_percent": progress}
        if message:
            # 可以在这里添加进度消息字段
            pass
            
        await db.execute(
            update(AuditTask)
            .where(AuditTask.id == task_id)
            .values(**update_data)
        )
        await db.commit()
    
    @staticmethod
    async def _save_audit_results(
        db: AsyncSession,
        task_id: int,
        results: Dict[str, Any],
        project_path: str
    ):
        """保存审计结果到数据库"""
        
        # 统计安全问题
        findings = results.get('findings', [])
        high_issues = len([f for f in findings if f.get('severity') == 'high'])
        medium_issues = len([f for f in findings if f.get('severity') == 'medium'])
        low_issues = len([f for f in findings if f.get('severity') == 'low'])
        
        # 计算平均置信度
        confidences = [f.get('confidence', 0) for f in findings if f.get('confidence')]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 生成摘要
        summary = f"分析了 {results.get('total_files', 0)} 个文件，发现 {len(findings)} 个潜在安全问题。"
        
        # 保存审计结果
        audit_result = AuditResult(
            task_id=task_id,
            findings=findings,
            statistics=results.get('timing_stats', {}),
            summary=summary,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            total_confidence=avg_confidence
        )
        
        db.add(audit_result)
        
        # 保存文件分析记录
        file_findings = {}
        for finding in findings:
            file_path = finding.get('file', '')
            if file_path not in file_findings:
                file_findings[file_path] = []
            file_findings[file_path].append(finding)
        
        # 为每个分析的文件创建记录
        for file_path, file_results in file_findings.items():
            # 计算文件的置信度
            file_confidences = [f.get('confidence', 0) for f in file_results if f.get('confidence')]
            file_confidence = sum(file_confidences) / len(file_confidences) if file_confidences else 0.0
            
            audit_file = AuditFile(
                task_id=task_id,
                file_path=file_path,
                file_type=AuditService._detect_file_type(file_path),
                file_size=AuditService._get_file_size(project_path, file_path),
                analysis_result=file_results,
                confidence_score=file_confidence,
                status=FileStatus.analyzed
            )
            db.add(audit_file)
        
        await db.commit()
    
    @staticmethod
    def _detect_file_type(file_path: str) -> str:
        """检测文件类型"""
        suffix = Path(file_path).suffix.lower()
        type_mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.php': 'php',
            '.go': 'go',
            '.rs': 'rust',
            '.cs': 'csharp',
            '.rb': 'ruby'
        }
        return type_mapping.get(suffix, 'unknown')
    
    @staticmethod
    def _get_file_size(project_path: str, file_path: str) -> int:
        """获取文件大小"""
        try:
            full_path = Path(project_path) / file_path
            if full_path.exists():
                return full_path.stat().st_size
        except:
            pass
        return 0
    
    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: int, user_id: int) -> Optional[AuditTask]:
        """获取用户的审计任务"""
        result = await db.execute(
            select(AuditTask)
            .where(AuditTask.id == task_id)
            .where(AuditTask.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_tasks(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[AuditTask]:
        """获取用户的审计任务列表"""
        result = await db.execute(
            select(AuditTask)
            .where(AuditTask.user_id == user_id)
            .order_by(AuditTask.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_task_results(db: AsyncSession, task_id: int, user_id: int) -> Optional[AuditResult]:
        """获取审计结果"""
        # 首先验证任务属于当前用户
        task = await AuditService.get_task_by_id(db, task_id, user_id)
        if not task:
            return None
        
        result = await db.execute(
            select(AuditResult)
            .where(AuditResult.task_id == task_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def cancel_task(db: AsyncSession, task_id: int, user_id: int) -> bool:
        """取消审计任务"""
        task = await AuditService.get_task_by_id(db, task_id, user_id)
        if not task:
            return False
        
        if task.status not in [TaskStatus.pending, TaskStatus.running]:
            return False
        
        await db.execute(
            update(AuditTask)
            .where(AuditTask.id == task_id)
            .values(
                status=TaskStatus.cancelled,
                completed_at=datetime.utcnow()
            )
        )
        await db.commit()
        return True
    
    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int, user_id: int) -> bool:
        """删除审计任务和相关文件"""
        task = await AuditService.get_task_by_id(db, task_id, user_id)
        if not task:
            return False
        
        try:
            # 删除任务文件
            task_dir = Path(settings.UPLOAD_PATH) / str(task_id)
            if task_dir.exists():
                shutil.rmtree(task_dir)
            
            # 删除报告文件
            report_file = Path(settings.REPORTS_PATH) / f"task_{task_id}_results.json"
            if report_file.exists():
                report_file.unlink()
                
            # 删除数据库记录（级联删除会自动删除相关记录）
            await db.delete(task)
            await db.commit()
            
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"删除任务失败: {e}")
            return False
    
    @staticmethod
    async def _record_token_usage(
        db: AsyncSession,
        task_id: int,
        user: User,
        results: Dict[str, Any]
    ):
        """记录Token使用情况"""
        try:
            from app.services.token_usage_service import TokenUsageService
            
            # 从结果中提取Token使用信息
            # 注意：这里需要根据AI审计引擎的实际返回结构来调整
            token_info = results.get('token_usage', {})
            
            if token_info:
                tokens_consumed = token_info.get('total_tokens', 0)
                provider = token_info.get('provider', 'unknown')
                model_name = token_info.get('model', None)
                cost = token_info.get('cost', 0)
                
                if tokens_consumed > 0:
                    await TokenUsageService.record_token_usage(
                        db=db,
                        user_id=user.id,
                        tokens_consumed=tokens_consumed,
                        provider=provider,
                        model_name=model_name,
                        task_id=task_id,
                        cost=cost
                    )
            else:
                # 如果没有具体的Token信息，使用估算值
                # 基于分析的文件数量和复杂度估算Token使用
                total_files = results.get('total_files', 0)
                total_findings = len(results.get('findings', []))
                
                # 简单估算：每个文件平均100 tokens，每个发现额外20 tokens
                estimated_tokens = (total_files * 100) + (total_findings * 20)
                
                if estimated_tokens > 0:
                    await TokenUsageService.record_token_usage(
                        db=db,
                        user_id=user.id,
                        tokens_consumed=estimated_tokens,
                        provider='ai_audit_engine',
                        model_name='code_analysis',
                        task_id=task_id,
                        cost=0
                    )
                    
        except Exception as e:
            print(f"记录Token使用失败: {e}")
            # 不影响主要流程，继续执行
