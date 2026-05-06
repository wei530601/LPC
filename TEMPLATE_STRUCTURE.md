# 模板结构说明

## 目录结构

```
templates/
├── base.html                    # 基础模板（包含HTML结构、head、scripts）
├── index.html                   # 主页面（继承base.html，引入所有页面）
├── login.html                   # 登录页面（独立页面）
├── index_old.html.backup        # 原始的单文件模板（备份）
├── components/                  # 可复用组件
│   ├── sidebar.html            # 侧边栏导航
│   └── modals.html             # 模态对话框（文件编辑器等）
└── pages/                       # 各个功能页面
    ├── dashboard.html          # 仪表板
    ├── services.html           # 服务管理
    ├── docker.html             # Docker管理
    ├── terminal.html           # Web终端
    ├── files.html              # 文件管理
    ├── packages.html           # 包管理
    ├── users.html              # 用户管理
    ├── control.html            # 系统控制
    ├── network.html            # 网络管理
    ├── performance.html        # 性能分析
    └── settings.html           # 系统设置
```

## 文件说明

### base.html
- 包含完整的HTML文档结构
- 定义了CSS和JavaScript引用
- 提供了可扩展的block区域（title、content、extra_css、extra_js）
- 引入sidebar和modals组件

### index.html
- 继承base.html
- 通过include引入所有功能页面
- 保持SPA（单页应用）的结构

### components/
**sidebar.html**
- 导航菜单
- Logo和应用标题
- 退出登录按钮

**modals.html**
- 文件编辑器模态框
- 可以添加其他通用模态框

### pages/
每个页面文件包含对应功能的完整HTML结构：
- dashboard.html - 系统监控仪表板
- services.html - systemd服务管理
- docker.html - Docker容器和镜像管理
- terminal.html - Web终端
- files.html - 文件浏览器
- packages.html - APT包管理
- users.html - 用户和权限管理
- control.html - 系统控制（重启、进程、日志）
- network.html - 网络配置（WiFi、接口、防火墙）
- performance.html - 性能分析（负载、进程、磁盘I/O）
- settings.html - 系统设置和信息

## 优势

1. **模块化**：每个功能独立文件，便于维护
2. **可复用**：组件可以在多个地方引用
3. **易扩展**：添加新页面只需创建新文件并在index.html中引入
4. **清晰结构**：代码组织更清晰，易于理解
5. **团队协作**：多人可以同时编辑不同的页面文件

## 修改指南

### 添加新页面
1. 在`templates/pages/`创建新的HTML文件
2. 在`templates/index.html`中添加`{% include 'pages/your_page.html' %}`
3. 在`templates/components/sidebar.html`中添加导航链接

### 修改现有页面
- 直接编辑`templates/pages/`下对应的文件即可

### 添加新组件
1. 在`templates/components/`创建组件文件
2. 在需要的地方使用`{% include 'components/your_component.html' %}`引入

### 修改全局样式或脚本
- 编辑`templates/base.html`

## 恢复原始文件

如果需要恢复原始的单文件模板：
```bash
cp templates/index_old.html.backup templates/index.html
```

## 注意事项

- 所有页面文件都是SPA的一部分，通过JavaScript控制显示/隐藏
- 页面切换逻辑在`static/app.js`中实现
- 保持原有的class名称和id，确保JavaScript功能正常
