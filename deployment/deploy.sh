#!/bin/bash

# 项目管理系统 Docker 部署脚本
# 使用方法: ./deploy.sh [start|stop|restart|logs|build|clean]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 函数：打印彩色消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 函数：检查 Docker 和 Docker Compose
check_requirements() {
    print_message "检查系统要求..." "$YELLOW"
    
    if ! command -v docker &> /dev/null; then
        print_message "错误: Docker 未安装，请先安装 Docker" "$RED"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_message "错误: Docker Compose 未安装，请先安装 Docker Compose" "$RED"
        exit 1
    fi
    
    print_message "✓ Docker 和 Docker Compose 已安装" "$GREEN"
}

# 函数：检查环境配置文件
check_env_file() {
    if [ ! -f "$SCRIPT_DIR/.env.production" ]; then
        print_message "警告: .env.production 文件不存在，使用默认配置" "$YELLOW"
        print_message "建议: 复制 .env.production 并修改配置" "$YELLOW"
    else
        cp "$SCRIPT_DIR/.env.production" "$SCRIPT_DIR/.env"
        print_message "✓ 环境配置已加载" "$GREEN"
    fi
}

# 函数：构建镜像
build_images() {
    print_message "开始构建 Docker 镜像..." "$YELLOW"
    cd "$SCRIPT_DIR"
    
    # 使用国内镜像加速
    export DOCKER_BUILDKIT=1
    
    docker-compose build
    
    print_message "✓ Docker 镜像构建完成" "$GREEN"
}

# 函数：启动服务
start_services() {
    print_message "启动服务..." "$YELLOW"
    cd "$SCRIPT_DIR"
    
    # 创建必要的目录
    mkdir -p data/uploads data/logs
    
    docker-compose up -d
    
    print_message "✓ 服务启动成功" "$GREEN"
    print_message "\n服务访问地址:" "$GREEN"
    print_message "  - 前端: http://localhost:6004" "$GREEN"
    print_message "  - 后端 API: http://localhost:6002" "$GREEN"
    print_message "  - API 文档: http://localhost:6002/docs" "$GREEN"
    print_message "  - MongoDB: External (External Database Specified)" "$GREEN"
}

# 函数：停止服务
stop_services() {
    print_message "停止服务..." "$YELLOW"
    cd "$SCRIPT_DIR"
    
    docker-compose down
    
    print_message "✓ 服务已停止" "$GREEN"
}

# 函数：重启服务
restart_services() {
    print_message "重启服务..." "$YELLOW"
    stop_services
    start_services
}

# 函数：查看日志
view_logs() {
    cd "$SCRIPT_DIR"
    
    if [ -n "$2" ]; then
        # 查看特定服务的日志
        docker-compose logs -f "$2"
    else
        # 查看所有服务的日志
        docker-compose logs -f
    fi
}

# 函数：清理资源
clean_resources() {
    print_message "清理 Docker 资源..." "$YELLOW"
    cd "$SCRIPT_DIR"
    
    read -p "这将删除所有容器、镜像和卷，确定要继续吗？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --rmi all
        print_message "✓ 资源清理完成" "$GREEN"
    else
        print_message "取消清理操作" "$YELLOW"
    fi
}

# 函数：显示服务状态
show_status() {
    print_message "服务状态:" "$YELLOW"
    cd "$SCRIPT_DIR"
    docker-compose ps
}

# 函数：备份数据
backup_data() {
    print_message "备份数据库..." "$YELLOW"
    
    BACKUP_DIR="$PROJECT_ROOT/backups"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/mongodb_backup_$TIMESTAMP.archive"
    
    print_message "警告: 外部 MongoDB 模式下，此脚本不支持自动备份。请手动备份您的本地数据库。" "$YELLOW"
}

# 函数：恢复数据
restore_data() {
    if [ -z "$2" ]; then
        print_message "错误: 请指定备份文件路径" "$RED"
        print_message "用法: $0 restore <backup_file>" "$YELLOW"
        exit 1
    fi
    
    if [ ! -f "$2" ]; then
        print_message "错误: 备份文件不存在: $2" "$RED"
        exit 1
    fi
    
    print_message "恢复数据库..." "$YELLOW"
    
    print_message "警告: 外部 MongoDB 模式下，此脚本不支持自动恢复。请手动恢复您的本地数据库。" "$YELLOW"
}

# 函数：显示帮助信息
show_help() {
    cat << EOF
项目管理系统 Docker 部署脚本

用法: $0 [命令] [选项]

命令:
  build       构建 Docker 镜像
  start       启动所有服务
  stop        停止所有服务
  restart     重启所有服务
  status      显示服务状态
  logs        查看日志 (可选: logs <service_name>)
  backup      备份数据库
  restore     恢复数据库 (需要: restore <backup_file>)
  clean       清理所有 Docker 资源（容器、镜像、卷）
  help        显示此帮助信息

示例:
  $0 build              # 构建镜像
  $0 start              # 启动服务
  $0 logs backend       # 查看后端日志
  $0 backup             # 备份数据库
  $0 restore backup.archive  # 恢复数据库

EOF
}

# 主程序
main() {
    case "${1:-help}" in
        build)
            check_requirements
            check_env_file
            build_images
            ;;
        start)
            check_requirements
            check_env_file
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            view_logs "$@"
            ;;
        backup)
            backup_data
            ;;
        restore)
            restore_data "$@"
            ;;
        clean)
            clean_resources
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_message "错误: 未知命令 '$1'" "$RED"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主程序
main "$@"
