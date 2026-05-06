# Pi Panel 部署指南

## 在树莓派上部署

### 1. 克隆或上传项目到树莓派

```bash
cd /home/pi
# 如果使用 git
git clone <repository-url> pi-panel
cd pi-panel

# 或者直接上传项目文件
```

### 2. 运行安装脚本

```bash
chmod +x install.sh
./install.sh
```

### 3. 启动服务

#### 方式一：手动启动（用于测试）

```bash
chmod +x start.sh
./start.sh
```

#### 方式二：作为系统服务（推荐）

```bash
# 复制服务文件
sudo cp pi-panel.service /etc/systemd/system/

# 重载 systemd
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable pi-panel

# 启动服务
sudo systemctl start pi-panel

# 查看状态
sudo systemctl status pi-panel

# 查看日志
sudo journalctl -u pi-panel -f
```

### 4. 访问面板

打开浏览器访问：`http://树莓派IP:5000`

默认登录信息：
- 用户名: `admin`
- 密码: `pi-panel`

## 配置说明

### 修改默认密码

编辑 `config.py`:

```python
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'your-new-password'
```

然后重启服务：

```bash
sudo systemctl restart pi-panel
```

### 修改文件管理根目录

编辑 `config.py`:

```python
FILE_ROOT = '/home/pi'  # 改为你想要的路径
```

### 修改端口

编辑 `app.py` 最后一行:

```python
socketio.run(app, host='0.0.0.0', port=5000, debug=False)  # 修改 port
```

## 安全建议

1. **修改默认密码**：首次部署后立即修改
2. **防火墙**：如果对外网开放，建议配置防火墙规则
3. **反向代理**：生产环境建议使用 Nginx + SSL

### 使用 Nginx 反向代理示例

```nginx
server {
    listen 80;
    server_name pi.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 故障排查

### 服务无法启动

检查日志：

```bash
sudo journalctl -u pi-panel -n 50
```

### 权限问题

确保服务运行用户有权限访问必要的系统信息：

```bash
# 将用户添加到必要的组
sudo usermod -aG sudo pi
```

### 端口被占用

检查端口占用：

```bash
sudo lsof -i :5000
```

修改配置文件中的端口号。

## 卸载

```bash
# 停止服务
sudo systemctl stop pi-panel
sudo systemctl disable pi-panel

# 删除服务文件
sudo rm /etc/systemd/system/pi-panel.service
sudo systemctl daemon-reload

# 删除项目文件
cd /home/pi
rm -rf pi-panel
```

## 更新

```bash
cd /home/pi/pi-panel

# 拉取最新代码
git pull

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl restart pi-panel
```
