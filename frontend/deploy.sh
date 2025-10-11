#!/bin/bash

# 前端專用部署腳本
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

log_info "開始部署前端應用..."
log_info "模式: $MODE"

# 檢查Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安裝，請先安裝 Node.js 18+"
    exit 1
fi

# 檢查npm
if ! command -v npm &> /dev/null; then
    log_error "npm 未安裝，請先安裝 npm"
    exit 1
fi

# 檢查環境變數
if [ ! -f .env.local ]; then
    log_warning ".env.local 文件不存在，創建默認配置..."
    cat > .env.local << EOF
# 前端環境變數
NEXT_PUBLIC_MCP_SERVER_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=PTT股票爬蟲分析
EOF
    log_warning "請編輯 .env.local 文件設定正確的環境變數"
fi

# 停止現有服務
log_info "停止現有服務..."
pkill -f "next start" 2>/dev/null || true

# 清理舊的構建文件
log_info "清理舊的構建文件..."
rm -rf .next
rm -rf out

# 安裝依賴
log_info "安裝依賴..."
npm install

# 檢查代碼
log_info "檢查代碼..."
npm run lint 2>/dev/null || log_warning "Lint檢查失敗，繼續部署..."

# 構建應用
log_info "構建應用..."
if [ "$MODE" = "prod" ]; then
    npm run build
    log_success "生產環境構建完成！"
    log_info "啟動生產服務器..."
    npm start &
else
    log_info "啟動開發服務器..."
    npm run dev &
fi

# 等待服務啟動
sleep 5

# 檢查服務狀態
if curl -s http://localhost:3000 > /dev/null; then
    log_success "前端服務啟動成功！"
    log_info "前端應用: http://localhost:3000"
    log_info "後端API: http://localhost:8000"
else
    log_error "前端服務啟動失敗"
    exit 1
fi

log_success "前端部署完成！"
log_info "查看日誌: npm run dev (開發模式) 或 npm start (生產模式)"
