#!/bin/bash

# Ollama 安裝腳本
# 適用於 Ubuntu/Debian 系統

set -e

echo "🤖 開始安裝 Ollama..."

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 檢查是否為 root 用戶
if [ "$EUID" -ne 0 ]; then
    echo "請使用 sudo 執行此腳本"
    exit 1
fi

# 安裝 Ollama
echo -e "${YELLOW}📦 安裝 Ollama...${NC}"
curl -fsSL https://ollama.ai/install.sh | sh

# 啟動 Ollama 服務
echo -e "${YELLOW}🚀 啟動 Ollama 服務...${NC}"
systemctl start ollama
systemctl enable ollama

# 等待服務啟動
sleep 5

# 下載 Qwen2.5:0.5b 模型
echo -e "${YELLOW}📥 下載 Qwen2.5:0.5b 模型...${NC}"
sudo -u www-data ollama pull qwen2.5:0.5b

# 驗證安裝
echo -e "${YELLOW}✅ 驗證安裝...${NC}"
ollama list

echo -e "${GREEN}✅ Ollama 安裝完成！${NC}"
echo ""
echo -e "${BLUE}📋 管理命令:${NC}"
echo "  查看模型: ollama list"
echo "  運行模型: ollama run qwen2.5:0.5b"
echo "  停止服務: systemctl stop ollama"
echo "  重啟服務: systemctl restart ollama"
echo ""
echo -e "${BLUE}📊 模型信息:${NC}"
echo "  模型名稱: qwen2.5:0.5b"
echo "  模型大小: 約 3.4GB"
echo "  記憶體需求: 約 4GB RAM"
