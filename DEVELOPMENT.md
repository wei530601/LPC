# Pi Panel 开发文档

## 项目结构

```
pi-panel/
├── app.py                  # Flask 主应用
├── config.py               # 配置文件
├── auth.py                 # 认证模块
├── system_info.py          # 系统信息采集
├── file_manager.py         # 文件管理模块
├── service_manager.py      # 服务管理模块
├── requirements.txt        # Python 依赖
├── install.sh              # 安装脚本
├── start.sh                # 启动脚本（Linux）
├── start.bat               # 启动脚本（Windows）
├── templates/
│   ├── index.html          # 主页面
│   └── login.html          # 登录页面
└── static/
    ├── style.css           # 样式文件
    └── app.js              # 前端逻辑
```

## 技术架构

### 后端

- **框架**: Flask 3.0
- **WebSocket**: Flask-SocketIO + eventlet
- **认证**: Flask-Login
- **系统信息**: psutil

### 前端

- **UI**: 原生 HTML/CSS/JavaScript
- **终端**: xterm.js + xterm-addon-fit
- **WebSocket**: Socket.IO Client

### 数据流

```
前端 <--HTTP/WebSocket--> Flask <--psutil--> 系统
                           |
                           +--> systemctl (服务管理)
                           +--> bash (终端)
                           +--> 文件系统
```

## API 接口

### 系统信息

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/system/info` | GET | 获取所有系统信息 |
| `/api/system/cpu` | GET | CPU 使用率 |
| `/api/system/memory` | GET | 内存使用 |
| `/api/system/disk` | GET | 磁盘使用 |
| `/api/system/temperature` | GET | 系统温度 |
| `/api/system/network` | GET | 网络流量 |

### 服务管理

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/services` | GET | 列出所有服务 |
| `/api/services/<name>/status` | GET | 获取服务状态 |
| `/api/services/<name>/<action>` | POST | 控制服务 (start/stop/restart) |

### 文件管理

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/files/list` | GET | 列出目录内容 |
| `/api/files/read` | GET | 读取文件 |
| `/api/files/write` | POST | 写入文件 |
| `/api/files/delete` | POST | 删除文件/目录 |
| `/api/files/mkdir` | POST | 创建目录 |
| `/api/files/download` | GET | 下载文件 |
| `/api/files/upload` | POST | 上传文件 |

### WebSocket 事件（/terminal）

| 事件 | 方向 | 说明 |
|------|------|------|
| `start_terminal` | Client → Server | 启动终端会话 |
| `terminal_ready` | Server → Client | 终端就绪 |
| `terminal_input` | Client → Server | 发送输入 |
| `terminal_output` | Server → Client | 接收输出 |
| `terminal_resize` | Client → Server | 调整终端大小 |

## 开发指南

### 环境搭建

```bash
# 克隆项目
git clone <repository-url>
cd pi-panel

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python app.py
```

### 调试

启用 debug 模式，修改 `app.py`:

```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

查看日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 添加新功能

#### 1. 添加新的 API 路由

在 `app.py` 中添加：

```python
@app.route('/api/new-feature')
@login_required
def new_feature():
    # 处理逻辑
    return jsonify({'result': 'data'})
```

#### 2. 添加新的系统信息采集

在 `system_info.py` 中添加方法：

```python
@staticmethod
def get_new_info():
    # 采集逻辑
    return {}
```

#### 3. 添加前端功能

在 `static/app.js` 中添加函数：

```javascript
async function loadNewFeature() {
    const response = await fetch('/api/new-feature');
    const data = await response.json();
    // 更新 UI
}
```

在 `templates/index.html` 中添加 UI 元素。

### 代码规范

- Python: PEP 8
- JavaScript: ES6+
- 缩进: 4 空格（Python），2 空格（HTML/CSS/JS）
- 命名: 
  - Python: `snake_case`
  - JavaScript: `camelCase`
  - CSS: `kebab-case`

### 测试

```bash
# 单元测试（待实现）
python -m pytest tests/

# 手动测试
# 1. 启动服务
# 2. 访问 http://localhost:5000
# 3. 测试各项功能
```

## 性能优化

### 后端

1. **缓存**：对不常变化的系统信息进行缓存
2. **异步**：使用 gevent 处理并发请求
3. **数据库**：如需持久化，使用 SQLite

### 前端

1. **节流**：仪表板更新使用固定间隔（2 秒）
2. **懒加载**：页面切换时才加载数据
3. **压缩**：生产环境压缩 CSS/JS

## 安全考虑

### 已实现

- ✅ 登录认证（Flask-Login）
- ✅ 路径遍历防护（文件管理）
- ✅ CSRF 保护（Flask 内置）
- ✅ WebSocket 认证

### 建议增强

- [ ] 添加 HTTPS 支持
- [ ] 实现多用户系统
- [ ] 添加操作日志
- [ ] 实现 2FA 认证
- [ ] 限制 API 访问频率

### 生产部署建议

```python
# config.py
import secrets

class ProductionConfig(Config):
    SECRET_KEY = secrets.token_hex(32)  # 随机生成
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # 仅 HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

## 扩展建议

### 计划功能

- [ ] Docker 容器管理
- [ ] 进程管理器
- [ ] 日志查看器
- [ ] 系统更新管理
- [ ] 网络配置管理
- [ ] 定时任务管理（crontab）
- [ ] 系统备份与恢复
- [ ] 监控告警（邮件/Webhook）

### 插件系统

可以设计插件架构，允许第三方扩展：

```python
# plugins/example_plugin.py
class ExamplePlugin:
    def __init__(self, app):
        self.app = app
    
    def register_routes(self):
        @self.app.route('/api/plugin/example')
        def example():
            return jsonify({'status': 'ok'})
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- Issues: GitHub Issues
- Discussions: GitHub Discussions
