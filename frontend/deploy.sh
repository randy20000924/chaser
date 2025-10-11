#!/bin/bash

# Chaser Frontend Deployment Script
# 前端部署腳本

set -e

echo "🚀 Starting Chaser Frontend Deployment..."

# 檢查是否在frontend目錄
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the frontend directory"
    exit 1
fi

# 創建前端專用的Dockerfile
echo "🐳 Creating frontend Dockerfile..."
cat > Dockerfile << 'EOF'
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry during the build.
ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
EOF

# 更新next.config.ts以支持standalone輸出
echo "⚙️ Updating Next.js config for Docker..."
cat > next.config.ts << 'EOF'
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  env: {
    MCP_SERVER_URL: process.env.MCP_SERVER_URL || 'http://localhost:8000',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.MCP_SERVER_URL || 'http://localhost:8000'}/tools/:path*`,
      },
    ];
  },
};

export default nextConfig;
EOF

# 創建前端docker-compose.yml
echo "🐳 Creating frontend docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  chaser-frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - MCP_SERVER_URL=${MCP_SERVER_URL:-http://localhost:8000}
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    image: chaser-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL:-postgresql+psycopg://ptt_user:ptt_password@db:5432/ptt_stock_crawler}
      - TARGET_AUTHORS=${TARGET_AUTHORS:-mrp}
      - CRAWL_INTERVAL=${CRAWL_INTERVAL:-300}
      - ENABLE_OLLAMA=${ENABLE_OLLAMA:-false}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5:0.5b}
      - MCP_SERVER_HOST=${MCP_SERVER_HOST:-0.0.0.0}
      - MCP_SERVER_PORT=${MCP_SERVER_PORT:-8000}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - backend_logs:/app/logs
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ptt_stock_crawler
      - POSTGRES_USER=ptt_user
      - POSTGRES_PASSWORD=ptt_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres_data:
  backend_logs:
EOF

# 創建前端部署說明
echo "📝 Creating frontend deployment guide..."
cat > DEPLOYMENT.md << 'EOF'
# Chaser Frontend Deployment Guide

## 快速部署

### 1. 環境準備
```bash
# 確保Docker和Docker Compose已安裝
docker --version
docker-compose --version

# 確保後端服務已構建
cd ../backend
docker-compose build
cd ../frontend
```

### 2. 配置環境變數
```bash
# 創建環境變數文件
cat > .env << 'ENVEOF'
MCP_SERVER_URL=http://localhost:8000
ENVEOF
```

### 3. 啟動服務
```bash
# 構建並啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

## 服務端口
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432

## 健康檢查
```bash
# 檢查前端狀態
curl http://localhost:3000/

# 檢查API狀態
curl http://localhost:8000/
```

## 開發模式
```bash
# 本地開發
npm install
npm run dev

# 構建生產版本
npm run build
npm start
```
EOF

# 創建.dockerignore
echo "📝 Creating .dockerignore..."
cat > .dockerignore << 'EOF'
node_modules
.next
.git
.gitignore
README.md
.env
.env.local
.env.production.local
.env.development.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
*.tsbuildinfo
next-env.d.ts
EOF

echo "✅ Frontend deployment files created successfully!"
echo "📁 Frontend files are in: ./frontend/"
echo "🚀 To deploy: cd frontend && docker-compose up -d"
