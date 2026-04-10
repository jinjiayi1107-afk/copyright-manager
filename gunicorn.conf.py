# -*- coding: utf-8 -*-
# ============================================================
# Gunicorn 配置文件
# 说明：生产环境运行Flask应用，支持多worker并发处理
# 用法：gunicorn -c gunicorn.conf.py app:app
# ============================================================

import multiprocessing
import os

# ==================== 服务器配置 ====================
# 监听地址和端口
bind = "0.0.0.0:5000"

# Worker进程数
# 建议：CPU核心数 * 2 + 1，小系统2-4个够用
workers = multiprocessing.cpu_count() * 2 + 1
# 如果不想自动计算，可以固定数量：
# workers = 4

# 每个worker的线程数（gunicorn默认使用sync worker，线程数为1）
threads = 1

# Worker连接数上限
worker_connections = 1000

# ==================== 超时配置 ====================
# Worker超时时间（秒），超过此时间会被重启
timeout = 30

# 优雅关闭超时时间
graceful_timeout = 10

# Keep-alive时间
keepalive = 2

# ==================== 进程管理 ====================
# 最大请求数，超过后重启worker（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50  # 随机抖动，避免所有worker同时重启

# 预加载应用（在fork worker之前加载应用代码）
# 好处：减少内存占用，加快启动
# 坏处：如果应用有延迟加载的资源，可能出问题
preload_app = True

# ==================== 日志配置 ====================
# 日志级别：debug, info, warning, error, critical
loglevel = "info"

# 访问日志格式
accesslog = "-"  # 输出到stdout
errorlog = "-"   # 输出到stderr

# 日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ==================== 安全配置 ====================
# 限制请求体大小（字节），10MB
limit_request_line = 0  # 不限制请求行大小
limit_request_fields = 100  # 限制请求头字段数量
limit_request_field_size = 8190  # 限制请求头字段大小

# ==================== 其他配置 ====================
# 守护进程模式（True=后台运行，False=前台运行）
# systemd管理时建议False
daemon = False

# PID文件位置
pidfile = "/tmp/gunicorn_copyright.pid"

# 工作目录（可选，默认为启动目录）
# cwd = "/path/to/copyright-manager"

# 进程名前缀
proc_name = "copyright-manager"

# ==================== 钩子函数（可选） ====================
def on_starting(server):
    """服务器启动时执行"""
    print(f"[Gunicorn] 服务器启动中，workers={workers}")

def on_exit(server):
    """服务器退出时执行"""
    print("[Gunicorn] 服务器已关闭")

def worker_exit(server, worker):
    """Worker退出时执行"""
    print(f"[Gunicorn] Worker {worker.pid} 已退出")
