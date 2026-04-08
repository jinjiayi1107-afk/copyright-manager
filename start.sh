#!/bin/bash
# 版权管理系统启动脚本

cd "$(dirname "$0")"

echo "=================================================="
echo "           版权管理系统启动脚本"
echo "=================================================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 检查依赖
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装依赖..."
    pip install -r requirements.txt --quiet
fi

echo ""
echo "启动服务中..."
echo ""
python3 app.py
