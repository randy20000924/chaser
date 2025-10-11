#!/bin/bash

# PTT股票爬蟲系統 - 一鍵部署腳本
# 使用方法: ./deploy.sh [backend|frontend|all]

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
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

# 檢查參數
DEPLOY_TYPE=${1:-all}

if [[ ! "$DEPLOY_TYPE" =~ ^(backend|frontend|all)$ ]]; then
    log_error "無效的部署類型: $DEPLOY_TYPE"
    log_info "使用方法: ./deploy.sh [backend|frontend|all]"
    exit 1
fi

log_info "開始部署 PTT股票爬蟲系統..."
log_info "部署類型: $DEPLOY_TYPE"

# 檢查Docker是否安裝
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 檢查環境變數文件
if [ ! -f .env ]; then
    log_warning ".env 文件不存在，從 env.example 複製..."
    cp env.example .env
    log_warning "請編輯 .env 文件設定正確的環境變數"
fi

# 停止現有服務
log_info "停止現有服務..."
docker-compose down 2>/dev/null || true

# 清理舊的鏡像（可選）
if [ "$2" = "--clean" ]; then
    log_info "清理舊的Docker鏡像..."
    docker system prune -f
fi

# 部署後端
deploy_backend() {
    log_info "部署後端服務..."
    
    # 構建後端鏡像
    log_info "構建後端Docker鏡像..."
    docker-compose build crawler
    
    # 啟動後端服務
    log_info "啟動後端服務..."
    docker-compose up -d postgres crawler
    
    # 等待服務啟動
    log_info "等待服務啟動..."
    sleep 10
    
    # 檢查服務狀態
    if docker-compose ps | grep -q "Up"; then
        log_success "後端服務啟動成功！"
        log_info "MCP服務器: http://localhost:8000"
        log_info "PostgreSQL: localhost:5432"
    else
        log_error "後端服務啟動失敗"
        docker-compose logs crawler
        exit 1
    fi
}

# 部署前端
deploy_frontend() {
    log_info "部署前端服務..."
    
    # 檢查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安裝，請先安裝 Node.js 18+"
        exit 1
    fi
    
    # 進入前端目錄
    cd frontend
    
    # 安裝依賴
    log_info "安裝前端依賴..."
    npm install
    
    # 構建前端
    log_info "構建前端應用..."
    npm run build
    
    # 啟動前端服務
    log_info "啟動前端服務..."
    npm start &
    
    cd ..
    
    # 等待服務啟動
    sleep 5
    
    log_success "前端服務啟動成功！"
    log_info "前端應用: http://localhost:3000"
}

# 部署所有服務
deploy_all() {
    log_info "部署所有服務..."
    
    # 先部署後端
    deploy_backend
    
    # 再部署前端
    deploy_frontend
    
    log_success "所有服務部署完成！"
    log_info "前端: http://localhost:3000"
    log_info "後端API: http://localhost:8000"
    log_info "PostgreSQL: localhost:5432"
}

# 根據參數執行相應的部署
case $DEPLOY_TYPE in
    "backend")
        deploy_backend
        ;;
    "frontend")
        deploy_frontend
        ;;
    "all")
        deploy_all
        ;;
esac

# 顯示服務狀態
log_info "服務狀態:"
docker-compose ps

log_success "部署完成！"
log_info "查看日誌: docker-compose logs -f"
log_info "停止服務: docker-compose down"
