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
      max_memory_restart: '512M',  // 降低記憶體限制
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
      max_memory_restart: '512M',  // 降低記憶體限制
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
      max_memory_restart: '256M',  // 降低記憶體限制
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
