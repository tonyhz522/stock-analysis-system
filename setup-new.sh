#!/bin/bash

# Stock Analysis System Setup Script for macOS
# 股票分析系统 macOS 快速部署脚本
# 兼容新版 Docker Desktop

echo "==================================="
echo "股票分析系统部署脚本 (macOS)"
echo "==================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装！"
    echo "请先安装 Docker Desktop for Mac: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker 未运行！"
    echo "请启动 Docker Desktop"
    exit 1
fi

echo "✅ Docker 已安装并运行"

# 自动检测使用 docker-compose 还是 docker compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

echo "使用命令: $DOCKER_COMPOSE"

# 检查端口占用
check_port() {
    if lsof -i :$1 &> /dev/null; then
        echo "⚠️  端口 $1 已被占用"
        return 1
    fi
    return 0
}

echo ""
echo "检查端口占用情况..."
PORT_OK=true

if ! check_port 3306; then
    PORT_OK=false
    echo "   建议：修改 docker-compose.yml 中 MySQL 端口映射"
fi

if ! check_port 8501; then
    PORT_OK=false
    echo "   建议：修改 docker-compose.yml 中 Streamlit 端口映射"
fi

if [ "$PORT_OK" = true ]; then
    echo "✅ 端口检查通过"
fi

# 创建必要目录
echo ""
echo "创建项目目录..."
mkdir -p app
mkdir -p mysql_data

# 设置权限
chmod 755 mysql_data
chmod 755 app

echo "✅ 目录创建完成"

# 检查必要文件
echo ""
echo "检查必要文件..."
MISSING_FILES=()

[ ! -f "docker-compose.yml" ] && MISSING_FILES+=("docker-compose.yml")
[ ! -f "Dockerfile" ] && MISSING_FILES+=("Dockerfile")
[ ! -f "requirements.txt" ] && MISSING_FILES+=("requirements.txt")
[ ! -f "init.sql" ] && MISSING_FILES+=("init.sql")
[ ! -f "app/app.py" ] && MISSING_FILES+=("app/app.py")

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo "❌ 缺少以下文件："
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "请确保所有文件都已创建在正确位置"
    exit 1
fi

echo "✅ 所有文件检查通过"

# 启动服务
echo ""
echo "==================================="
echo "开始启动服务..."
echo "==================================="

# 停止可能存在的旧容器
$DOCKER_COMPOSE down 2>/dev/null

# 启动新容器
$DOCKER_COMPOSE up -d

echo ""
echo "等待服务启动..."
echo "(首次启动需要下载镜像和初始化数据，可能需要 3-5 分钟)"

# 等待 MySQL 健康检查通过
MAX_WAIT=120
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if $DOCKER_COMPOSE exec mysql mysqladmin ping -h localhost &> /dev/null; then
        echo ""
        echo "✅ MySQL 已启动"
        break
    fi
    echo -n "."
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo ""
    echo "❌ MySQL 启动超时"
    echo "请运行 '$DOCKER_COMPOSE logs mysql' 查看错误信息"
    exit 1
fi

# 检查 Streamlit
sleep 5
if $DOCKER_COMPOSE ps | grep -q "streamlit.*Up"; then
    echo "✅ Streamlit 已启动"
else
    echo "❌ Streamlit 启动失败"
    echo "请运行 '$DOCKER_COMPOSE logs streamlit' 查看错误信息"
    exit 1
fi

echo ""
echo "==================================="
echo "🎉 部署成功！"
echo "==================================="
echo ""
echo "访问地址: http://localhost:8501"
echo ""
echo "登录账号:"
echo "  用户名: admin / user1 / user2"
echo "  密码: password123"
echo ""
echo "==================================="
echo ""
echo "常用命令:"
echo "  查看日志: $DOCKER_COMPOSE logs -f"
echo "  停止服务: $DOCKER_COMPOSE stop"
echo "  启动服务: $DOCKER_COMPOSE start"
echo "  重启服务: $DOCKER_COMPOSE restart"
echo "  删除服务: $DOCKER_COMPOSE down"
echo ""
echo "==================================="