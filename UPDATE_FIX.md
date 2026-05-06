# 更新问题修复指南

## 问题描述

如果在使用Web界面更新时遇到以下错误：
```
error: Your local changes to the following files would be overwritten by merge:
    app.py
Please commit your changes or stash them before you merge.
```

## 解决方案

### 方案 1: 使用强制更新（推荐）

1. 在Web界面 → 设置 → 系统更新
2. 点击"检查更新"
3. 如果普通更新失败，会显示"强制更新"按钮
4. 点击"强制更新"（会丢弃本地修改）
5. 点击"重启应用"

**注意：** 强制更新会丢弃所有本地修改！

### 方案 2: 手动修复（SSH）

如果Web界面无法访问，使用SSH登录树莓派：

```bash
cd ~/pi-panel

# 方式 A: 使用修复脚本（推荐）
bash fix_update.sh

# 方式 B: 手动执行
git stash                # 保存本地修改
git pull origin main     # 拉取最新代码
git stash pop           # 恢复本地修改（可选）

# 重启服务
sudo systemctl restart pi-panel
# 或
python app.py
```

### 方案 3: 完全重置

如果以上方法都不行，完全重置到最新版本：

```bash
cd ~/pi-panel
git fetch origin
git reset --hard origin/main
git clean -fd
sudo systemctl restart pi-panel
```

## CPU 告警错误修复

如果看到以下错误：
```
TypeError: '>' not supported between instances of 'list' and 'int'
```

这个问题已经在最新版本中修复。请按照上述方法更新到最新版本。

## 验证修复

更新后，检查日志确认没有错误：

```bash
# 查看应用日志
journalctl -u pi-panel -f

# 或直接运行
python app.py
```

如果仍有问题，请在 GitHub 提交 Issue: https://github.com/wei530601/pi-panel/issues

## 本次更新内容

- ✅ 修复 CPU 告警数据类型错误
- ✅ 改进更新机制（自动 stash 本地修改）
- ✅ 新增强制更新功能
- ✅ 新增 Docker 容器管理功能
