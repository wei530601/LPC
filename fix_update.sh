#!/bin/bash
# 紧急修复脚本 - 修复更新冲突并拉取最新代码

echo "========================================"
echo "   Pi Panel 紧急修复脚本"
echo "========================================"
echo ""
echo "此脚本将："
echo "1. 保存当前本地修改到 stash"
echo "2. 拉取最新代码"
echo "3. 尝试恢复本地修改"
echo ""

# 进入项目目录
cd "$(dirname "$0")"

echo "当前目录: $(pwd)"
echo ""

# 显示当前状态
echo "=== Git 状态 ==="
git status
echo ""

# 询问用户
read -p "是否继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "已取消"
    exit 1
fi

echo ""
echo "=== 步骤 1: Stash 本地修改 ==="
git stash
echo ""

echo "=== 步骤 2: 拉取最新代码 ==="
git pull origin main
echo ""

echo "=== 步骤 3: 恢复 Stash ==="
git stash pop
echo ""

echo "=== 完成！==="
echo ""
echo "如果有冲突，请手动解决："
echo "1. 编辑冲突文件"
echo "2. git add <冲突文件>"
echo "3. git stash drop"
echo ""
echo "然后重启服务："
echo "  sudo systemctl restart pi-panel"
echo "  或"
echo "  python app.py"
echo ""
