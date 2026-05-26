#!/bin/bash

# 快速部署脚本 - 一键部署整个项目
# 作者: Project Management System
# 用法: curl -fsSL https://your-domain.com/quick-deploy.sh | bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印带颜色的消息
print_msg() {
    echo -e "${2}${1}${NC}"
}

# 打印标题
print_title() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_title "项目管理系统 - 快速部署脚本"

# 1. 检查系统
print_msg "步骤 1/6: 检查系统环境..." "$YELLOW"

if ! command_exists docker; then
    print_msg "❌ Docker 未安装" "$RED"
    print_msg "正在安装 Docker..." "$YELLOW"
    
    # 检测操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        print_msg "❌ 无法检测操作系统" "$RED"
        exit 1
    fi
    
    # 安装 Docker
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl gnupg lsb-release
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    else
        print_msg "❌ 不支持的操作系统: $OS" "$RED"
        exit 1
    fi
    
    sudo systemctl start docker
    sudo systemctl enable docker
    print_msg "✓ Docker 安装完成" "$GREEN"
else
    print_msg "✓ Docker 已安装" "$GREEN"
fi

# 2. 设置项目目录
print_msg "步骤 2/6: 创建项目目录..." "$YELLOW"

PROJECT_DIR="/opt/project-management"

if [ -d "$PROJECT_DIR" ]; then
    print_msg "⚠️  项目目录已存在: $PROJECT_DIR" "$YELLOW"
    read -p "是否覆盖? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_msg "部署已取消" "$RED"
        exit 1
    fi
    sudo rm -rf "$PROJECT_DIR"
fi

sudo mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

print_msg "✓ 项目目录创建完成" "$GREEN"

# 3. 获取项目文件
print_msg "步骤 3/6: 获取项目文件..." "$YELLOW"

# 这里假设项目文件已经通过 SCP 或其他方式上传到服务器
# 如果有 Git 仓库，可以使用 git clone
# git clone https://github.com/your-repo/project-management.git .

print_msg "✓ 项目文件准备完成（请确保已上传项目文件到 $PROJECT_DIR）" "$GREEN"

# 4. 配置环境变量
print_msg "步骤 4/6: 配置环境变量..." "$YELLOW"

if [ ! -f "$PROJECT_DIR/deployment/.env.production" ]; then
    print_msg "❌ 未找到 .env.production 文件" "$RED"
    print_msg "请确保 deployment 目录包含所有必要文件" "$RED"
    exit 1
fi

cd "$PROJECT_DIR/deployment"

# 复制环境变量文件
cp .env.production .env

# 生成随机密钥
if command_exists openssl; then
    RANDOM_SECRET=$(openssl rand -hex 32)
    sed -i "s/change_this_to_a_random_secret_key_at_least_32_characters_long/$RANDOM_SECRET/" .env
    print_msg "✓ 已自动生成 JWT 密钥" "$GREEN"
else
    print_msg "⚠️  请手动修改 .env 文件中的 SECRET_KEY" "$YELLOW"
fi

print_msg "✓ 环境变量配置完成" "$GREEN"

# 5. 构建和启动服务
print_msg "步骤 5/6: 构建 Docker 镜像并启动服务..." "$YELLOW"
print_msg "这可能需要 10-30 分钟，请耐心等待..." "$YELLOW"

# 授予脚本执行权限
chmod +x deploy.sh

# 构建镜像
./deploy.sh build

# 启动服务
./deploy.sh start

print_msg "✓ 服务启动完成" "$GREEN"

# 6. 验证部署
print_msg "步骤 6/6: 验证部署..." "$YELLOW"

sleep 10  # 等待服务完全启动

# 检查容器状态
if docker ps | grep -q "pm_backend"; then
    print_msg "✓ 后端服务运行正常" "$GREEN"
else
    print_msg "❌ 后端服务启动失败" "$RED"
fi

if docker ps | grep -q "pm_frontend"; then
    print_msg "✓ 前端服务运行正常" "$GREEN"
else
    print_msg "❌ 前端服务启动失败" "$RED"
fi

if docker ps | grep -q "pm_mongodb"; then
    print_msg "✓ 数据库服务运行正常" "$GREEN"
else
    print_msg "❌ 数据库服务启动失败" "$RED"
fi

# 完成
print_title "部署完成！"

# 获取服务器 IP
SERVER_IP=$(hostname -I | awk '{print $1}')

cat << EOF
${GREEN}✓ 项目管理系统部署成功！${NC}

${BLUE}访问地址:${NC}
  - 前端界面: http://$SERVER_IP
  - 后端 API: http://$SERVER_IP:8000
  - API 文档: http://$SERVER_IP:8000/docs

${BLUE}管理命令:${NC}
  - 查看服务状态: cd $PROJECT_DIR/deployment && ./deploy.sh status
  - 查看日志: cd $PROJECT_DIR/deployment && ./deploy.sh logs
  - 停止服务: cd $PROJECT_DIR/deployment && ./deploy.sh stop
  - 重启服务: cd $PROJECT_DIR/deployment && ./deploy.sh restart
  - 备份数据: cd $PROJECT_DIR/deployment && ./deploy.sh backup

${YELLOW}重要提示:${NC}
  1. 请修改 $PROJECT_DIR/deployment/.env 中的数据库密码
  2. 生产环境建议启用 HTTPS
  3. 定期备份数据库
  4. 查看完整文档: $PROJECT_DIR/deployment/README.md

${GREEN}祝使用愉快！${NC}
EOF
