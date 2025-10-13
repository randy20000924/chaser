module.exports = {
  apps: [
    {
      name: 'chaser-backend',
      script: 'python3',
      args: 'main.py --mode mcp',
      cwd: '/var/www/chaser',
      user: 'www-data',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      restart_delay: 4000,  // 重啟延遲 4 秒
      max_restarts: 10,     // 最大重啟次數
      min_uptime: '10s',    // 最小運行時間
      kill_timeout: 5000,   // 強制關閉超時
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/var/log/chaser/backend-error.log',
      out_file: '/var/log/chaser/backend-out.log',
      log_file: '/var/log/chaser/backend-combined.log',
      time: true
    },
    {
      name: 'chaser-frontend',
      script: 'npm',
      args: 'start',
      cwd: '/var/www/chaser/frontend',
      user: 'www-data',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      restart_delay: 4000,  // 重啟延遲 4 秒
      max_restarts: 10,     // 最大重啟次數
      min_uptime: '10s',    // 最小運行時間
      kill_timeout: 5000,   // 強制關閉超時
      env: {
        NODE_ENV: 'production',
        NEXT_PUBLIC_MCP_SERVER_URL: 'http://localhost:8000'
      },
      error_file: '/var/log/chaser/frontend-error.log',
      out_file: '/var/log/chaser/frontend-out.log',
      log_file: '/var/log/chaser/frontend-combined.log',
      time: true
    },
    {
      name: 'chaser-scheduler',
      script: 'python3',
      args: 'auto_crawler.py',
      cwd: '/var/www/chaser',
      user: 'www-data',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      restart_delay: 10000, // 排程器重啟延遲 10 秒
      max_restarts: 5,      // 排程器最大重啟次數較少
      min_uptime: '30s',    // 排程器最小運行時間較長
      kill_timeout: 5000,   // 強制關閉超時
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/var/log/chaser/scheduler-error.log',
      out_file: '/var/log/chaser/scheduler-out.log',
      log_file: '/var/log/chaser/scheduler-combined.log',
      time: true
    }
  ]
};