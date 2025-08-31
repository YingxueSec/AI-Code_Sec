#!/bin/bash

# AI代码审计系统 - 生产环境部署脚本
# 用法: ./deploy.sh [init|start|stop|restart|update|logs|backup]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="ai-code-audit"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境
check_environment() {
    log_info "检查部署环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查环境变量文件
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "环境变量文件不存在，将从模板复制"
        if [ -f "docker-env-template" ]; then
            cp docker-env-template .env
            log_warning "请编辑 .env 文件并设置正确的配置"
            exit 1
        else
            log_error "未找到环境变量模板文件"
            exit 1
        fi
    fi
    
    log_success "环境检查完成"
}

# 初始化环境
init_environment() {
    log_info "初始化部署环境..."
    
    # 创建必要的目录
    mkdir -p "$BACKUP_DIR"
    mkdir -p ./logs
    mkdir -p ./ssl
    mkdir -p ./mysql/init
    
    # 设置权限
    chmod 755 deploy.sh
    
    # 创建MySQL初始化脚本
    cat > ./mysql/init/01-init.sql << 'EOF'
-- AI代码审计系统数据库初始化脚本
CREATE DATABASE IF NOT EXISTS ai_code_audit_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_code_audit_prod;

-- 设置时区
SET time_zone = '+00:00';

-- 创建索引优化
SET GLOBAL innodb_buffer_pool_size = 134217728; -- 128MB
EOF
    
    log_success "环境初始化完成"
}

# 启动服务
start_services() {
    log_info "启动AI代码审计系统..."
    
    check_environment
    
    # 构建并启动服务
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    check_services
    
    log_success "系统启动完成"
    log_info "前端访问地址: http://localhost"
    log_info "后端API地址: http://localhost:8000"
}

# 停止服务
stop_services() {
    log_info "停止AI代码审计系统..."
    
    docker-compose -f "$COMPOSE_FILE" down
    
    log_success "系统已停止"
}

# 重启服务
restart_services() {
    log_info "重启AI代码审计系统..."
    
    stop_services
    sleep 5
    start_services
}

# 更新系统
update_services() {
    log_info "更新AI代码审计系统..."
    
    # 备份数据
    backup_data
    
    # 拉取最新代码
    if [ -d ".git" ]; then
        git pull
    fi
    
    # 重新构建并启动
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    log_success "系统更新完成"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    # 检查容器状态
    docker-compose -f "$COMPOSE_FILE" ps
    
    # 检查健康状态
    services=("backend" "frontend" "mysql" "redis")
    
    for service in "${services[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "${PROJECT_NAME}_${service}.*Up"; then
            log_success "$service 服务运行正常"
        else
            log_error "$service 服务异常"
        fi
    done
}

# 查看日志
view_logs() {
    local service=${2:-""}
    
    if [ -n "$service" ]; then
        log_info "查看 $service 服务日志..."
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        log_info "查看所有服务日志..."
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# 备份数据
backup_data() {
    log_info "备份系统数据..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/backup_$timestamp.sql"
    
    # 备份MySQL数据
    docker-compose -f "$COMPOSE_FILE" exec -T mysql mysqldump \
        -u root -p"$MYSQL_ROOT_PASSWORD" \
        --all-databases \
        --single-transaction \
        --routines \
        --triggers > "$backup_file"
    
    # 压缩备份文件
    gzip "$backup_file"
    
    # 清理旧备份（保留最近7天）
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
    
    log_success "数据备份完成: ${backup_file}.gz"
}

# 恢复数据
restore_data() {
    local backup_file=$2
    
    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log_info "恢复系统数据..."
    
    # 停止后端服务
    docker-compose -f "$COMPOSE_FILE" stop backend
    
    # 恢复数据
    if [[ "$backup_file" == *.gz ]]; then
        zcat "$backup_file" | docker-compose -f "$COMPOSE_FILE" exec -T mysql mysql -u root -p"$MYSQL_ROOT_PASSWORD"
    else
        cat "$backup_file" | docker-compose -f "$COMPOSE_FILE" exec -T mysql mysql -u root -p"$MYSQL_ROOT_PASSWORD"
    fi
    
    # 重启后端服务
    docker-compose -f "$COMPOSE_FILE" start backend
    
    log_success "数据恢复完成"
}

# 显示帮助
show_help() {
    echo "AI代码审计系统部署脚本"
    echo ""
    echo "用法: $0 [命令] [参数]"
    echo ""
    echo "命令:"
    echo "  init              初始化部署环境"
    echo "  start             启动所有服务"
    echo "  stop              停止所有服务"
    echo "  restart           重启所有服务"
    echo "  update            更新系统"
    echo "  status            检查服务状态"
    echo "  logs [service]    查看日志"
    echo "  backup            备份数据"
    echo "  restore <file>    恢复数据"
    echo "  help              显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 init           # 初始化环境"
    echo "  $0 start          # 启动系统"
    echo "  $0 logs backend   # 查看后端日志"
    echo "  $0 backup         # 备份数据"
}

# 主函数
main() {
    case "${1:-help}" in
        "init")
            init_environment
            ;;
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "update")
            update_services
            ;;
        "status")
            check_services
            ;;
        "logs")
            view_logs "$@"
            ;;
        "backup")
            backup_data
            ;;
        "restore")
            restore_data "$@"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
