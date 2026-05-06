# 树莓派控制面板 (Pi Panel)

一个功能完整的树莓派Web管理控制面板，支持系统监控、服务管理、Web终端和文件管理。

## 功能特性

- **仪表板监控**
  - CPU使用率（每核心独立显示）
  - 内存和Swap使用情况
  - 磁盘使用统计
  - 系统温度监控
  - 实时网络流量

- **服务管理**
  - systemctl服务控制（启动/停止/重启）
  - 实时状态查看

- **Web终端**
  - 基于xterm.js的完整终端体验
  - WebSocket实时通信
  - 支持bash shell

- **文件管理器**
  - 文件浏览和导航
  - 文件上传下载
  - 在线编辑
  - 权限管理

## 快速开始

### 安装

```bash
chmod +x install.sh
sudo ./install.sh
```

### 手动安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行服务
python app.py
```

### 访问

打开浏览器访问: `http://localhost:5000`

默认账号:
- 用户名: `admin`
- 密码: `pi-panel`

## 系统要求

- Python 3.7+
- Linux系统（推荐树莓派OS）
- sudo权限（用于系统管理功能）

## 技术栈

- **后端**: Flask + Flask-SocketIO
- **前端**: 原生JavaScript + xterm.js
- **系统监控**: psutil
- **WebSocket**: python-socketio (threading 模式)

## 安全提示

⚠️ 首次部署后请立即修改默认密码
⚠️ 建议仅在内网环境使用或配置反向代理+SSL

## 疑难解答

遇到问题？查看 [疑难解答文档](TROUBLESHOOTING.md)

常见问题：
- Python 3.13+ 安装错误：已使用 eventlet 替代 gevent
- 端口占用、权限问题、终端连接失败等

## 许可

MIT License
