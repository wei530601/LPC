# Pi Panel 项目文件清单

## 核心文件

### 后端服务
- `app.py` - Flask 主应用，包含所有路由和 WebSocket 处理
- `config.py` - 配置文件
- `auth.py` - 用户认证模块
- `system_info.py` - 系统信息采集（CPU、内存、磁盘等）
- `file_manager.py` - 文件管理功能
- `service_manager.py` - systemd 服务管理

### 前端
- `templates/login.html` - 登录页面
- `templates/index.html` - 主控制面板页面
- `static/style.css` - 样式表
- `static/app.js` - 前端 JavaScript 逻辑

### 配置和依赖
- `requirements.txt` - Python 依赖包列表
- `.gitignore` - Git 忽略配置

### 安装和部署
- `install.sh` - Linux 自动安装脚本
- `start.sh` - Linux 启动脚本
- `start.bat` - Windows 启动脚本（用于本地测试）

### 文档
- `README.md` - 项目说明
- `DEPLOYMENT.md` - 部署指南
- `USER_GUIDE.md` - 用户使用指南
- `DEVELOPMENT.md` - 开发文档
- `LICENSE` - MIT 许可证
- `PROJECT_FILES.md` - 本文件

## 功能模块

### 1. 仪表板（Dashboard）
- ✅ CPU 使用率（每核心）
- ✅ 内存使用情况
- ✅ 磁盘使用统计
- ✅ 系统温度监控
- ✅ 网络流量实时显示
- ✅ 系统运行时间

### 2. 服务管理（Service Manager）
- ✅ 列出所有 systemd 服务
- ✅ 启动/停止/重启服务
- ✅ 查看服务状态
- ✅ 服务搜索过滤

### 3. Web 终端（Terminal）
- ✅ 基于 xterm.js 的完整终端
- ✅ WebSocket 实时通信
- ✅ bash shell 支持
- ✅ 窗口大小自适应

### 4. 文件管理器（File Manager）
- ✅ 浏览目录和文件
- ✅ 上传文件
- ✅ 下载文件
- ✅ 在线编辑文本文件
- ✅ 创建文件夹和文件
- ✅ 删除文件和目录
- ✅ 路径安全检查

### 5. 认证系统
- ✅ 登录页面
- ✅ 会话管理
- ✅ 路由保护
- ✅ 默认账号：admin / pi-panel

## 技术栈

### 后端
- Python 3.7+
- Flask 3.0
- Flask-SocketIO
- Flask-Login
- psutil
- eventlet

### 前端
- 原生 HTML5/CSS3/JavaScript
- xterm.js（终端模拟）
- Socket.IO Client（WebSocket）

## 目录结构

```
LCP/
├── app.py
├── auth.py
├── config.py
├── file_manager.py
├── service_manager.py
├── system_info.py
├── requirements.txt
├── .gitignore
├── install.sh
├── start.sh
├── start.bat
├── README.md
├── DEPLOYMENT.md
├── USER_GUIDE.md
├── DEVELOPMENT.md
├── LICENSE
├── PROJECT_FILES.md
├── templates/
│   ├── index.html
│   └── login.html
└── static/
    ├── style.css
    └── app.js
```

## 快速开始

### Linux/树莓派

```bash
chmod +x install.sh
./install.sh
```

### 手动启动

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

### 访问

浏览器打开：`http://localhost:5000`

默认账号：
- 用户名：`admin`
- 密码：`pi-panel`

## 注意事项

1. ⚠️ 首次部署后请立即修改默认密码
2. ⚠️ 服务管理功能需要 sudo 权限
3. ⚠️ 生产环境建议配置反向代理和 SSL
4. ⚠️ 建议仅在内网使用或通过 VPN 访问

## 系统要求

- Python 3.7+
- Linux 系统（树莓派 OS 推荐）
- sudo 权限（用于系统管理功能）
- 现代浏览器（支持 WebSocket）

## 版本信息

- 版本：1.0.0
- 创建日期：2026-05-06
- 授权：MIT License
