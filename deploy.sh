#!/bin/bash
# 一键部署脚本
# 用法： ./deploy.sh [start|stop|restart|logs]

set -e

case "$1" in
  start)
    echo "启动所有服务..."
    docker compose up -d
    ;;
  stop)
    echo "停止所有服务..."
    docker compose down
    ;;
  restart)
    echo "重启所有服务..."
    docker compose restart
    ;;
  logs)
    echo "查看所有服务日志..."
    docker compose logs -f
    ;;
  *)
    echo "用法: $0 {start|stop|restart|logs}"
    exit 1
    ;;
esac
