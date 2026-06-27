#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# YOLO Trainer — 生产环境部署脚本
# 用法: ./scripts/deploy.sh [build|up|down|restart|logs|init-db]
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_DIR="$PROJECT_DIR/docker"
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.yml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── 检查前置条件 ──────────────────────────────────────────────────────
check_prereqs() {
    for cmd in docker docker-compose; do
        if ! command -v "$cmd" &>/dev/null; then
            err "$cmd 未安装，请先安装。"
            exit 1
        fi
    done
}

# ── 构建镜像 ──────────────────────────────────────────────────────────
build() {
    log "构建 Docker 镜像..."
    docker-compose -f "$COMPOSE_FILE" build --parallel
    log "镜像构建完成 ✅"
}

# ── 启动服务 ──────────────────────────────────────────────────────────
up() {
    log "启动所有服务..."
    docker-compose -f "$COMPOSE_FILE" up -d
    log "等待服务就绪..."
    sleep 10
    # 健康检查
    local retries=30
    while [ $retries -gt 0 ]; do
        if curl -sf http://localhost:10003/health > /dev/null 2>&1; then
            log "后端服务已就绪 ✅"
            break
        fi
        retries=$((retries - 1))
        sleep 2
    done
    if [ $retries -eq 0 ]; then
        warn "后端健康检查超时，请查看日志: docker-compose logs backend"
    fi
    log "服务启动完成 🚀"
    echo ""
    echo "  前端:     http://localhost:5173"
    echo "  API 文档: http://localhost:10003/docs"
    echo "  Flower:   http://localhost:5555"
    echo "  MinIO:    http://localhost:9001"
    echo ""
}

# ── 停止服务 ──────────────────────────────────────────────────────────
down() {
    log "停止所有服务..."
    docker-compose -f "$COMPOSE_FILE" down
    log "服务已停止 ✅"
}

# ── 重启服务 ──────────────────────────────────────────────────────────
restart() {
    down
    up
}

# ── 查看日志 ──────────────────────────────────────────────────────────
logs() {
    docker-compose -f "$COMPOSE_FILE" logs -f --tail=100 "${@:2}"
}

# ── 初始化数据库 ──────────────────────────────────────────────────────
init_db() {
    log "初始化数据库..."
    # 等待 postgres 就绪
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            break
        fi
        retries=$((retries - 1))
        sleep 2
    done
    # 创建 MinIO bucket
    log "创建 MinIO 默认 bucket..."
    docker-compose -f "$COMPOSE_FILE" exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
    docker-compose -f "$COMPOSE_FILE" exec -T minio mc mb local/yolo-trainer 2>/dev/null || true
    docker-compose -f "$COMPOSE_FILE" exec -T minio mc anonymous set download local/yolo-trainer 2>/dev/null || true
    log "数据库初始化完成 ✅"
}

# ── 主入口 ────────────────────────────────────────────────────────────
main() {
    check_prereqs
    local cmd="${1:-up}"
    case "$cmd" in
        build)    build ;;
        up)       build; up; init_db ;;
        down)     down ;;
        restart)  restart ;;
        logs)     logs "$@" ;;
        init-db)  init_db ;;
        *)
            echo "用法: $0 {build|up|down|restart|logs|init-db}"
            exit 1
            ;;
    esac
}

main "$@"
