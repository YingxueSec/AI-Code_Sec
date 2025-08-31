#!/bin/bash

# AI代码安全审计系统 Web版 发布脚本
# Version: 2.6.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本信息
VERSION="2.6.0"
TAG_NAME="web-v${VERSION}"
RELEASE_TITLE="🚀 AI代码安全审计系统 Web版 v${VERSION} - 权限管控与监控增强版"

echo -e "${BLUE}=== AI代码安全审计系统 Web版 发布脚本 ===${NC}"
echo -e "${BLUE}版本: ${VERSION}${NC}"
echo -e "${BLUE}标签: ${TAG_NAME}${NC}"
echo

# 检查是否在正确的目录
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}错误: 请在web-system目录下运行此脚本${NC}"
    exit 1
fi

# 检查Git状态
echo -e "${YELLOW}检查Git状态...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}警告: 存在未提交的更改${NC}"
    echo "未提交的文件:"
    git status --porcelain
    echo
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}发布已取消${NC}"
        exit 1
    fi
fi

# 添加所有更改
echo -e "${YELLOW}添加所有更改到Git...${NC}"
git add .

# 提交更改
echo -e "${YELLOW}提交更改...${NC}"
COMMIT_MESSAGE="🎉 发布 v${VERSION}: 权限管控与监控增强版

✨ 新特性:
- 导出权限管理系统: 细粒度的导出格式权限控制
- Token使用监控: 实时Token消耗统计和成本分析
- 权限检查优化: 动态权限验证和前端适配
- 邀请码描述: 支持为邀请码添加用途说明

🔧 技术改进:
- ExportButton组件重构: 支持动态权限加载
- 数据库结构更新: 新增权限和日志表
- API权限验证: 完善的导出权限检查机制
- 错误处理增强: 更友好的错误信息显示

🐛 问题修复:
- 修复图表权限配置错误
- 修复导出按钮硬编码问题  
- 修复API响应验证问题
- 修复CORS配置和数据库关联

📊 性能优化:
- 前端组件懒加载和缓存优化
- 后端异步处理和查询优化
- 数据库索引和关联查询改进

🚀 部署改进:
- Docker配置增强和健康检查
- 环境变量模板和配置优化
- 升级指南和迁移脚本"

git commit -m "$COMMIT_MESSAGE"

# 创建标签
echo -e "${YELLOW}创建Git标签...${NC}"
git tag -a "$TAG_NAME" -m "$RELEASE_TITLE

发布说明:
- 导出权限管理系统，支持JSON、Markdown、PDF、HTML四种格式的独立权限设置
- Token使用监控与统计，包含实时监控看板和成本分析报告
- 增强的安全特性，包括邀请码描述字段和权限检查优化
- 技术改进和性能优化，前后端全面升级
- Bug修复和用户体验优化

技术栈:
- 前端: React 18 + TypeScript + Ant Design + Zustand
- 后端: FastAPI + SQLAlchemy + MySQL + Pydantic
- 部署: Docker + Docker Compose + Nginx

兼容性: 向下兼容v2.5.0
推荐升级: 强烈推荐所有用户升级到此版本"

echo -e "${GREEN}✅ Git提交和标签创建完成${NC}"
echo

# 显示发布信息
echo -e "${BLUE}=== 发布信息 ===${NC}"
echo -e "${GREEN}版本号: ${VERSION}${NC}"
echo -e "${GREEN}标签名: ${TAG_NAME}${NC}"
echo -e "${GREEN}提交哈希: $(git rev-parse HEAD)${NC}"
echo -e "${GREEN}发布时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo

# 显示后续步骤
echo -e "${BLUE}=== 后续步骤 ===${NC}"
echo -e "${YELLOW}1. 推送到远程仓库:${NC}"
echo "   git push origin main"
echo "   git push origin $TAG_NAME"
echo
echo -e "${YELLOW}2. 在GitHub上创建Release:${NC}"
echo "   - 访问: https://github.com/YingxueSec/AI-Code_Sec/releases/new"
echo "   - 选择标签: $TAG_NAME"
echo "   - 标题: $RELEASE_TITLE"
echo "   - 上传发布文件(如果有)"
echo
echo -e "${YELLOW}3. 验证部署:${NC}"
echo "   - 测试Docker部署: docker-compose up -d"
echo "   - 验证功能正常: 权限管理、Token监控、导出功能"
echo "   - 检查数据库迁移: 新增表和字段"
echo
echo -e "${YELLOW}4. 更新文档:${NC}"
echo "   - 更新Wiki文档"
echo "   - 发布公告和更新日志"
echo "   - 通知用户升级"
echo

echo -e "${GREEN}🎉 发布准备完成！${NC}"
echo -e "${GREEN}感谢使用AI代码安全审计系统 Web版！${NC}"
