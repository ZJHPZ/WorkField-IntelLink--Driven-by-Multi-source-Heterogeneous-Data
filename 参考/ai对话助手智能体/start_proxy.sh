#!/bin/bash

# 「数知」智能学习平台 - 代理服务启动脚本

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║          「数知」智能学习平台 - 本地代理服务              ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python版本: $python_version"

# 检查依赖
echo ""
echo "📦 检查依赖..."
if pip show fastapi > /dev/null 2>&1; then
    echo "   ✅ FastAPI 已安装"
else
    echo "   📥 正在安装 FastAPI..."
    pip install fastapi uvicorn httpx
fi

# 启动服务
echo ""
echo "🚀 启动代理服务..."
echo ""
echo "📝 请确保已配置正确的 SERVER_BASE_URL"
echo "   编辑 proxy_server.py 修改: SERVER_BASE_URL = \"https://你的服务器地址\""
echo ""

python3 proxy_server.py
