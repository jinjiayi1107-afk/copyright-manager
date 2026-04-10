#!/bin/bash
# ============================================================
# SMPH外版图书管理系统 - 自动备份脚本
# 功能：备份MySQL数据库和上传文件目录
# 用法：./backup.sh
# 建议：通过crontab定时执行（如每天凌晨2点）
# ============================================================

# ==================== 配置区域 ====================
# 请根据实际环境修改以下配置

# 数据库配置（与database.py保持一致）
DB_HOST="localhost"              # MySQL服务器地址
DB_PORT="3306"                   # MySQL端口
DB_USER="copyright_user"         # 数据库用户名
DB_PASSWORD="copyright123"       # 数据库密码
DB_NAME="copyright_manager"      # 数据库名称

# 备份目录配置
BACKUP_ROOT="/data/backups"      # 备份文件存放根目录
UPLOAD_DIR="/data/uploads"       # 上传文件目录

# 保留天数（超过此天数的备份会被自动删除）
KEEP_DAYS=30

# ==================== 脚本开始 ====================

# 获取当前日期时间（格式：2024-01-01_020000）
DATE_TIME=$(date +"%Y-%m-%d_%H%M%S")

# 创建今日备份目录
BACKUP_DIR="${BACKUP_ROOT}/${DATE_TIME}"
mkdir -p "${BACKUP_DIR}"

# 日志文件路径
LOG_FILE="${BACKUP_DIR}/backup.log"

# 打印日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "========== 备份任务开始 =========="
log "备份目录: ${BACKUP_DIR}"

# ==================== 1. 数据库备份 ====================
log "开始备份数据库: ${DB_NAME}"

# 数据库备份文件路径
DB_BACKUP_FILE="${BACKUP_DIR}/database_${DATE_TIME}.sql"

# 使用mysqldump导出数据库
# 参数说明：
#   -h: 主机地址
#   -P: 端口
#   -u: 用户名
#   -p: 密码（注意：-p和密码之间不能有空格）
#   --single-transaction: InnoDB表一致性备份（不锁表）
#   --routines: 包含存储过程和函数
#   --triggers: 包含触发器
#   --events: 包含事件
#   --no-tablespaces: 不备份表空间（避免权限问题）
mysqldump -h"${DB_HOST}" \
          -P"${DB_PORT}" \
          -u"${DB_USER}" \
          -p"${DB_PASSWORD}" \
          --single-transaction \
          --routines \
          --triggers \
          --events \
          --no-tablespaces \
          "${DB_NAME}" > "${DB_BACKUP_FILE}" 2>> "${LOG_FILE}"

# 检查备份是否成功
if [ $? -eq 0 ]; then
    # 压缩SQL文件（节省空间）
    gzip "${DB_BACKUP_FILE}"
    
    # 获取压缩后文件大小
    COMPRESSED_SIZE=$(du -h "${DB_BACKUP_FILE}.gz" | cut -f1)
    log "数据库备份成功: ${DB_BACKUP_FILE}.gz (${COMPRESSED_SIZE})"
else
    log "错误：数据库备份失败！"
fi

# ==================== 2. 上传文件备份 ====================
log "开始备份上传文件目录: ${UPLOAD_DIR}"

# 文件备份路径
FILES_BACKUP_FILE="${BACKUP_DIR}/uploads_${DATE_TIME}.tar.gz"

# 检查上传目录是否存在
if [ -d "${UPLOAD_DIR}" ]; then
    # 打包压缩上传目录
    # 参数说明：
    #   -c: 创建新归档
    #   -z: 使用gzip压缩
    #   -f: 指定输出文件
    #   -C: 切换到指定目录
    #   .: 打包当前目录内容（不包含父目录路径）
    tar -czf "${FILES_BACKUP_FILE}" -C "${UPLOAD_DIR}" . 2>> "${LOG_FILE}"
    
    # 检查备份是否成功
    if [ $? -eq 0 ]; then
        # 获取压缩文件大小
        COMPRESSED_SIZE=$(du -h "${FILES_BACKUP_FILE}" | cut -f1)
        log "上传文件备份成功: ${FILES_BACKUP_FILE} (${COMPRESSED_SIZE})"
    else
        log "错误：上传文件备份失败！"
    fi
else
    log "警告：上传目录不存在，跳过文件备份"
fi

# ==================== 3. 清理旧备份 ====================
log "开始清理超过 ${KEEP_DAYS} 天的旧备份"

# 查找并删除超过保留天数的备份目录
# 参数说明：
#   ${BACKUP_ROOT}: 备份根目录
#   -type d: 只查找目录
#   -name "20*": 匹配以20开头的目录名（日期格式）
#   -mtime +${KEEP_DAYS}: 修改时间超过KEEP_DAYS天
#   -exec rm -rf {} \;: 对找到的目录执行删除命令
DELETED_COUNT=$(find "${BACKUP_ROOT}" -type d -name "20*" -mtime +${KEEP_DAYS} | wc -l)

if [ ${DELETED_COUNT} -gt 0 ]; then
    find "${BACKUP_ROOT}" -type d -name "20*" -mtime +${KEEP_DAYS} -exec rm -rf {} \; 2>/dev/null
    log "已清理 ${DELETED_COUNT} 个旧备份目录"
else
    log "没有需要清理的旧备份"
fi

# ==================== 4. 备份统计 ====================
log "========== 备份统计 =========="

# 统计当前备份目录大小
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
log "本次备份大小: ${BACKUP_SIZE}"

# 统计总备份数量和大小
TOTAL_COUNT=$(find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "20*" | wc -l)
TOTAL_SIZE=$(du -sh "${BACKUP_ROOT}" | cut -f1)
log "总备份数量: ${TOTAL_COUNT} 个"
log "总备份占用: ${TOTAL_SIZE}"

log "========== 备份任务完成 =========="

# 退出状态（0=成功，1=失败）
exit 0
