#!/bin/bash

# 後端專用部署腳本
# 使用方法: ./deploy.sh [dev|prod]

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
MODE=${1:-dev}

if [[ ! "$MODE" =~ ^(dev|prod)$ ]]; then
    log_error "無效的模式: $MODE"
    log_info "使用方法: ./deploy.sh [dev|prod]"
    exit 1
fi

log_info "開始部署後端服務..."
log_info "模式: $MODE"

# 檢查Python
if ! command -v python3 &> /dev/null; then
    log_error "Python3 未安裝，請先安裝 Python 3.8+"
    exit 1
fi

# 檢查pip
if ! command -v pip3 &> /dev/null; then
    log_error "pip3 未安裝，請先安裝 pip3"
    exit 1
fi

# 檢查Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安裝，請先安裝 Docker"
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
pkill -f "python.*main.py" 2>/dev/null || true

# 創建虛擬環境（如果不存在）
if [ ! -d "venv" ]; then
    log_info "創建Python虛擬環境..."
    python3 -m venv venv
fi

# 激活虛擬環境
log_info "激活虛擬環境..."
source venv/bin/activate

# 安裝依賴
log_info "安裝Python依賴..."
pip install -r requirements.txt

# 啟動PostgreSQL
log_info "啟動PostgreSQL資料庫..."
docker-compose up -d postgres

# 等待資料庫啟動
log_info "等待資料庫啟動..."
sleep 10

# 初始化資料庫
log_info "初始化資料庫..."
python -c "from database import db_manager; db_manager.create_tables()"

# 啟動服務
if [ "$MODE" = "prod" ]; then
    log_info "啟動生產環境服務..."
    # 使用Docker Compose啟動所有服務
    docker-compose up -d crawler
    
    # 等待服務啟動
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
else
    log_info "啟動開發環境服務..."
    # 直接運行Python應用
    python main.py --mode both &
    
    # 等待服務啟動
    sleep 5
    
    # 檢查服務狀態
    if curl -s http://localhost:8000 > /dev/null; then
        log_success "後端服務啟動成功！"
        log_info "MCP服務器: http://localhost:8000"
        log_info "PostgreSQL: localhost:5432"
    else
        log_error "後端服務啟動失敗"
        exit 1
    fi
fi

log_success "後端部署完成！"
log_info "查看日誌: docker-compose logs -f (生產模式) 或查看終端輸出 (開發模式)"
