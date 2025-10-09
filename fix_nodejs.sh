#!/bin/bash

# 修復 Node.js 安裝問題的腳本

set -e

echo "🔧 修復 Node.js 安裝問題..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 清理現有的 Node.js 和 npm
echo -e "${BLUE}🧹 清理現有的 Node.js 和 npm...${NC}"
apt remove --purge -y nodejs npm || true
apt autoremove -y

# 2. 清理套件快取
echo -e "${BLUE}🧹 清理套件快取...${NC}"
apt clean
apt autoclean

# 3. 更新套件列表
echo -e "${BLUE}📦 更新套件列表...${NC}"
apt update

# 4. 安裝 Node.js 18.x (使用 NodeSource 官方源)
echo -e "${BLUE}📦 安裝 Node.js 18.x...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 5. 驗證安裝
echo -e "${BLUE}✅ 驗證安裝...${NC}"
node --version
npm --version

# 6. 安裝全域 npm 套件
echo -e "${BLUE}📦 安裝全域 npm 套件...${NC}"
npm install -g pm2

echo -e "${GREEN}🎉 Node.js 修復完成！${NC}"
echo "Node.js 版本: $(node --version)"
echo "npm 版本: $(npm --version)"
