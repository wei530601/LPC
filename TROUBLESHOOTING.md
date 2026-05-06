# Pi Panel 疑难解答

## 安装问题

### Python 3.13+ gevent 编译错误

**问题描述:**

安装依赖时出现以下错误：

```
Error compiling Cython file:
undeclared name not builtin: long
ERROR: Failed to build 'gevent' when getting requirements to build wheel
```

**原因:**

gevent 的某些版本与 Python 3.13+ 不兼容，因为 Cython 代码中使用了 Python 2 的 `long` 类型。

**解决方案:**

项目已改用 `eventlet` 替代 `gevent`。确保使用最新的 `requirements.txt`：

```bash
# 重新安装依赖
source venv/bin/activate
pip install -r requirements.txt
```

### pip 版本过低

**问题:** 安装时提示 pip 版本过低

**解决方案:**

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### 缺少系统依赖

**问题:** 提示缺少 Python 开发头文件

**解决方案:**

```bash
# Debian/Ubuntu/树莓派 OS
sudo apt-get update
sudo apt-get install python3-dev python3-venv build-essential

# CentOS/RHEL
sudo yum install python3-devel gcc
```

## 运行时问题

### 端口 5000 已被占用

**错误信息:** `OSError: [Errno 98] Address already in use`

**解决方案:**

```bash
# 查找占用端口的进程
sudo lsof -i :5000

# 杀死进程
sudo kill -9 <PID>

# 或者修改端口
# 编辑 app.py 最后一行，改为其他端口如 8080
```

### 权限被拒绝 (Permission Denied)

**问题:** 无法读取系统信息或管理服务

**解决方案:**

```bash
# 方案 1: 使用 sudo 运行（不推荐）
sudo venv/bin/python app.py

# 方案 2: 配置 sudo 无密码权限（推荐）
sudo visudo

# 添加以下行（将 pi 替换为你的用户名）
pi ALL=(ALL) NOPASSWD: /bin/systemctl
```

### 终端无法启动

**问题:** Web 终端连接失败或无响应

**解决方案:**

1. 检查 WebSocket 连接

```javascript
// 浏览器控制台查看错误
console.log('WebSocket status')
```

2. 确保 eventlet 正确安装

```bash
pip install eventlet --upgrade
```

3. 检查防火墙设置

```bash
sudo ufw allow 5000/tcp
```

### 文件管理器无法访问目录

**问题:** 提示"无权访问此路径"

**解决方案:**

检查 `config.py` 中的 `FILE_ROOT` 设置：

```python
FILE_ROOT = '/home/pi'  # 确保用户有权限访问
```

确保运行用户有目录访问权限：

```bash
chmod 755 /home/pi
```

## 浏览器兼容性问题

### 终端显示异常

**问题:** xterm.js 显示错误或乱码

**解决方案:**

1. 使用现代浏览器（Chrome 90+, Firefox 88+, Safari 14+）
2. 清除浏览器缓存
3. 检查浏览器控制台错误

### WebSocket 连接失败

**问题:** 浏览器提示 WebSocket 连接错误

**解决方案:**

1. 检查浏览器是否支持 WebSocket
2. 如果使用反向代理，确保配置了 WebSocket 升级

```nginx
# Nginx 配置示例
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## 性能问题

### 仪表板更新卡顿

**解决方案:**

调整更新间隔，编辑 `static/app.js`：

```javascript
// 将 2000 改为更大的值（毫秒）
dashboardInterval = setInterval(updateDashboard, 5000);
```

### 内存占用过高

**解决方案:**

1. 限制终端会话数量
2. 定期清理日志文件
3. 使用生产级 WSGI 服务器（gunicorn）

```bash
pip install gunicorn
gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 app:app
```

## 服务管理问题

### 服务操作无响应

**问题:** 点击启动/停止/重启按钮没有反应

**解决方案:**

1. 检查 sudo 权限
2. 查看浏览器控制台错误
3. 检查服务名称是否正确

### systemd 服务无法启动

**错误:** Pi Panel 作为系统服务无法启动

**解决方案:**

```bash
# 查看详细错误
sudo journalctl -u pi-panel -n 50 --no-pager

# 检查服务文件
sudo systemctl cat pi-panel

# 检查 Python 路径
which python3
# 更新服务文件中的路径

# 重新加载
sudo systemctl daemon-reload
sudo systemctl restart pi-panel
```

## 安全问题

### 登录后立即退出

**问题:** 登录成功但马上跳转回登录页

**解决方案:**

检查 `config.py` 中的 `SECRET_KEY`：

```python
# 使用随机密钥
import secrets
SECRET_KEY = secrets.token_hex(32)
```

### 跨域 CORS 错误

**问题:** 前端无法访问 API

**解决方案:**

```python
# app.py 中添加
from flask_cors import CORS
CORS(app)
```

## 数据问题

### 温度显示为空

**原因:** 某些系统或虚拟机不支持温度传感器

**解决方案:**

这是正常现象，树莓派通常可以正常显示。虚拟机或某些服务器无法获取温度数据。

### 网络速度显示 0

**原因:** 首次加载时没有历史数据

**解决方案:**

等待几秒钟，系统会自动计算网络速度。

## 联系支持

如果以上方案都无法解决问题：

1. 查看日志文件
2. 检查系统环境（Python 版本、操作系统）
3. 在 GitHub Issues 中报告问题，包含：
   - 错误信息
   - 系统环境
   - 复现步骤
