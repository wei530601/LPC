#!/bin/bash

# Pi Panel 安装脚本
# 用于树莓派或其他 Linux 系统

set -e

echo "======================================"
echo "    Pi Panel 安装向导"
echo "======================================"
echo ""

# 检查 Python 版本
echo "[1/6] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3"
    echo "请先安装 Python 3.7 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ 找到 Python $PYTHON_VERSION"

# 安装系统依赖
echo ""
echo "[2/6] 安装系统依赖..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip
    echo "✓ 系统依赖安装完成"
else
    echo "! 未检测到 apt-get，请手动确保 python3-venv 已安装"
fi

# 创建虚拟环境
echo ""
echo "[3/6] 创建 Python 虚拟环境..."
if [ -d "venv" ]; then
    echo "! 虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
fi

# 激活虚拟环境并安装依赖
echo ""
echo "[4/6] 安装 Python 依赖包..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ 依赖包安装完成"

# 创建必要的目录
echo ""
echo "[5/6] 创建必要的目录..."
mkdir -p sessions
mkdir -p /tmp/uploads
echo "✓ 目录创建完成"

# 创建 systemd 服务文件
echo ""
echo "[6/6] 创建系统服务..."

CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

cat > pi-panel.service << EOF
[Unit]
Description=Pi Panel Web Interface
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ 服务文件已创建: pi-panel.service"
echo ""
echo "======================================"
echo "    安装完成！"
echo "======================================"
echo ""
echo "启动方式："
echo ""
echo "1. 手动启动（用于测试）："
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "2. 作为系统服务运行："
echo "   sudo cp pi-panel.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable pi-panel"
echo "   sudo systemctl start pi-panel"
echo ""
echo "访问地址: http://localhost:5000"
echo "默认账号: admin"
echo "默认密码: pi-panel"
echo ""
echo "⚠️  重要: 首次登录后请立即修改密码！"
echo ""
