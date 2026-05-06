// ==================== 折叠面板功能 ====================

function toggleCollapse(header) {
    const content = header.nextElementSibling;
    const isActive = header.classList.contains('active');
    
    if (isActive) {
        header.classList.remove('active');
        content.classList.remove('active');
    } else {
        header.classList.add('active');
        content.classList.add('active');
    }
}

// 全部展开
function expandAll() {
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.classList.add('active');
        header.nextElementSibling.classList.add('active');
    });
}

// 全部折叠
function collapseAll() {
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.classList.remove('active');
        header.nextElementSibling.classList.remove('active');
    });
}

// ==================== 页面切换 ====================

// 页面切换
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        const page = item.dataset.page;
        
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        
        item.classList.add('active');
        document.getElementById(page).classList.add('active');
        
        // 页面切换时的初始化
        if (page === 'dashboard') {
            startDashboardUpdates();
        } else if (page === 'services') {
            loadServices();
        } else if (page === 'docker') {
            loadDockerData();
        } else if (page === 'packages') {
            loadPackages();
        } else if (page === 'users') {
            loadUsers();
        } else if (page === 'terminal') {
            initTerminal();
        } else if (page === 'files') {
            loadFiles('/');
        } else if (page === 'settings') {
            loadSystemInfo();
            applySettings();
        } else if (page === 'control') {
            loadSystemControl();
        } else if (page === 'network') {
            loadNetworkPage();
        } else if (page === 'performance') {
            loadPerformancePage();
        }
    });
});

// ==================== 仪表板 ====================

let dashboardInterval = null;
let lastNetworkStats = null;

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
}

function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    const parts = [];
    if (days > 0) parts.push(`${days}天`);
    if (hours > 0) parts.push(`${hours}小时`);
    if (minutes > 0) parts.push(`${minutes}分钟`);
    
    return parts.join(' ') || '刚启动';
}

async function updateDashboard() {
    try {
        const response = await fetch('/api/system/info');
        const data = await response.json();
        
        // CPU
        const cpuCores = document.getElementById('cpu-cores');
        cpuCores.innerHTML = '';
        let totalCpu = 0;
        
        data.cpu.percent.forEach((percent, index) => {
            totalCpu += percent;
            const coreDiv = document.createElement('div');
            coreDiv.className = 'cpu-core';
            coreDiv.innerHTML = `
                <div class="cpu-core-label">核心 ${index}</div>
                <div class="cpu-core-value">${percent.toFixed(1)}%</div>
            `;
            cpuCores.appendChild(coreDiv);
        });
        
        const avgCpu = (totalCpu / data.cpu.percent.length).toFixed(1);
        document.getElementById('cpu-avg').textContent = avgCpu + '%';
        
        // 更新统计卡片 - CPU
        const cpuStatEl = document.getElementById('cpu-avg-stat');
        if (cpuStatEl) {
            cpuStatEl.textContent = avgCpu + '%';
        }
        
        // 内存
        const memPercent = data.memory.percent;
        document.getElementById('mem-percent').textContent = memPercent.toFixed(1) + '%';
        document.getElementById('mem-bar').style.width = memPercent + '%';
        document.getElementById('mem-used').textContent = formatBytes(data.memory.used);
        document.getElementById('mem-total').textContent = formatBytes(data.memory.total);
        document.getElementById('swap-used').textContent = formatBytes(data.memory.swap.used);
        document.getElementById('swap-total').textContent = formatBytes(data.memory.swap.total);
        
        // 更新统计卡片 - 内存
        const memStatEl = document.getElementById('mem-percent-stat');
        if (memStatEl) {
            memStatEl.textContent = memPercent.toFixed(1) + '%';
        }
        
        // 磁盘
        const diskList = document.getElementById('disk-list');
        diskList.innerHTML = '';
        let maxDiskPercent = 0;
        data.disk.forEach(disk => {
            if (disk.percent > maxDiskPercent) {
                maxDiskPercent = disk.percent;
            }
            const diskDiv = document.createElement('div');
            diskDiv.className = 'disk-item';
            diskDiv.innerHTML = `
                <div class="disk-header">
                    <span class="disk-path">${disk.mountpoint}</span>
                    <span class="disk-usage">${disk.percent.toFixed(1)}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${disk.percent}%"></div>
                </div>
                <div class="stats">
                    ${formatBytes(disk.used)} / ${formatBytes(disk.total)}
                </div>
            `;
            diskList.appendChild(diskDiv);
        });
        
        // 更新统计卡片 - 磁盘
        const diskStatEl = document.getElementById('disk-percent-stat');
        if (diskStatEl) {
            diskStatEl.textContent = maxDiskPercent.toFixed(1) + '%';
        }
        
        // 温度
        const tempList = document.getElementById('temperature-list');
        tempList.innerHTML = '';
        let avgTemp = 0;
        let tempCount = 0;
        
        for (const [name, temp] of Object.entries(data.temperature)) {
            avgTemp += temp;
            tempCount++;
            
            const tempDiv = document.createElement('div');
            tempDiv.className = 'temp-item';
            
            let tempClass = '';
            if (temp > 70) tempClass = 'danger';
            else if (temp > 60) tempClass = 'warning';
            
            tempDiv.innerHTML = `
                <span class="temp-label">${name}</span>
                <span class="temp-value ${tempClass}">${temp.toFixed(1)}°C</span>
            `;
            tempList.appendChild(tempDiv);
        }
        
        if (Object.keys(data.temperature).length === 0) {
            tempList.innerHTML = '<div class="stats">温度信息不可用</div>';
        }
        
        // 更新统计卡片 - 温度
        const tempStatEl = document.getElementById('temp-stat');
        if (tempStatEl) {
            if (tempCount > 0) {
                tempStatEl.textContent = (avgTemp / tempCount).toFixed(1) + '°C';
            } else {
                tempStatEl.textContent = 'N/A';
            }
        }
        
        // 网络（计算速度）
        if (lastNetworkStats) {
            const timeDiff = 2; // 更新间隔（秒）
            const sentSpeed = (data.network.bytes_sent - lastNetworkStats.bytes_sent) / timeDiff;
            const recvSpeed = (data.network.bytes_recv - lastNetworkStats.bytes_recv) / timeDiff;
            
            document.getElementById('net-sent').textContent = formatBytes(sentSpeed) + '/s';
            document.getElementById('net-recv').textContent = formatBytes(recvSpeed) + '/s';
        }
        lastNetworkStats = data.network;
        
        // 运行时间
        document.getElementById('uptime').textContent = formatUptime(data.uptime);
        
    } catch (error) {
        console.error('更新仪表板失败:', error);
    }
}

function startDashboardUpdates() {
    if (dashboardInterval) {
        clearInterval(dashboardInterval);
    }
    updateDashboard();
    dashboardInterval = setInterval(updateDashboard, 2000);
}

// ==================== 服务管理 ====================

let allServices = [];

async function loadServices() {
    try {
        const response = await fetch('/api/services');
        allServices = await response.json();
        displayServices(allServices);
    } catch (error) {
        console.error('加载服务失败:', error);
    }
}

function displayServices(services) {
    const tbody = document.getElementById('services-list');
    tbody.innerHTML = '';
    
    if (services.error) {
        tbody.innerHTML = '<tr><td colspan="4">加载失败: ' + services.error + '</td></tr>';
        return;
    }
    
    services.forEach(service => {
        const row = document.createElement('tr');
        
        const statusClass = service.active === 'active' ? 'status-active' : 'status-inactive';
        const statusText = service.active === 'active' ? '运行中' : '已停止';
        
        row.innerHTML = `
            <td>${service.name}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${service.loaded}</td>
            <td class="service-actions">
                <button class="btn btn-sm btn-success" onclick="controlService('${service.name}', 'start')">启动</button>
                <button class="btn btn-sm btn-danger" onclick="controlService('${service.name}', 'stop')">停止</button>
                <button class="btn btn-sm btn-warning" onclick="controlService('${service.name}', 'restart')">重启</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

async function controlService(serviceName, action) {
    if (!confirm(`确定要${action === 'start' ? '启动' : action === 'stop' ? '停止' : '重启'} ${serviceName} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/services/${serviceName}/${action}`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            loadServices();
        } else {
            alert('操作失败: ' + result.error);
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

// 服务搜索
document.getElementById('service-search')?.addEventListener('input', (e) => {
    const search = e.target.value.toLowerCase();
    const filtered = allServices.filter(service => 
        service.name.toLowerCase().includes(search)
    );
    displayServices(filtered);
});

// ==================== 终端 ====================

let term = null;
let fitAddon = null;
let socket = null;

function initTerminal() {
    if (term) return;
    
    term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
        theme: {
            background: '#1e1e1e',
            foreground: '#f0f0f0'
        }
    });
    
    fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    
    term.open(document.getElementById('terminal-container'));
    fitAddon.fit();
    
    // 连接 WebSocket
    socket = io('/terminal');
    
    socket.on('connect', () => {
        const dimensions = fitAddon.proposeDimensions();
        socket.emit('start_terminal', {
            rows: dimensions.rows,
            cols: dimensions.cols
        });
    });
    
    socket.on('terminal_ready', () => {
        term.write('\r\n欢迎使用 Pi Panel Web 终端\r\n\r\n');
    });
    
    socket.on('terminal_output', (data) => {
        term.write(data.output);
    });
    
    term.onData((data) => {
        socket.emit('terminal_input', { input: data });
    });
    
    // 窗口大小调整
    window.addEventListener('resize', () => {
        if (term && fitAddon) {
            fitAddon.fit();
            const dimensions = fitAddon.proposeDimensions();
            socket.emit('terminal_resize', {
                rows: dimensions.rows,
                cols: dimensions.cols
            });
        }
    });
}

// ==================== 文件管理 ====================

let currentPath = '/';
let editingFile = null;

async function loadFiles(path) {
    currentPath = path;
    
    try {
        const response = await fetch(`/api/files/list?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        if (data.error) {
            alert('加载失败: ' + data.error);
            return;
        }
        
        // 更新面包屑
        updateBreadcrumb(path);
        
        // 显示文件列表
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '';
        
        // 返回上级目录
        if (path !== '/') {
            const parentDir = path.split('/').slice(0, -1).join('/') || '/';
            const item = createFileItem({
                name: '..',
                type: 'directory'
            }, parentDir);
            fileList.appendChild(item);
        }
        
        data.items.forEach(item => {
            fileList.appendChild(createFileItem(item, path));
        });
        
    } catch (error) {
        alert('加载失败: ' + error.message);
    }
}

function updateBreadcrumb(path) {
    const breadcrumb = document.getElementById('breadcrumb');
    const parts = path.split('/').filter(p => p);
    
    let html = '<a href="#" onclick="loadFiles(\'/\'); return false;">根目录</a>';
    let currentPath = '';
    
    parts.forEach((part, index) => {
        currentPath += '/' + part;
        html += ' / ';
        html += `<a href="#" onclick="loadFiles('${currentPath}'); return false;">${part}</a>`;
    });
    
    breadcrumb.innerHTML = html;
}

function createFileItem(item, basePath) {
    const div = document.createElement('div');
    div.className = 'file-item';
    
    const isDir = item.type === 'directory';
    const icon = isDir ? '<img src="/static/images/folder.svg" class="file-item-icon">' : '<img src="/static/images/file.svg" class="file-item-icon">';
    const itemPath = item.name === '..' ? basePath.split('/').slice(0, -1).join('/') || '/' : 
                     `${basePath}/${item.name}`.replace('//', '/');
    
    div.innerHTML = `
        <span class="file-icon">${icon}</span>
        <div class="file-info">
            <div class="file-name">${item.name}</div>
            ${item.size !== undefined ? `<div class="file-meta">${formatBytes(item.size)} | ${item.permissions || ''}</div>` : ''}
        </div>
        <div class="file-actions-btn">
            ${!isDir ? `
                <button class="btn btn-sm btn-primary" onclick="editFile('${itemPath}'); event.stopPropagation();">编辑</button>
                <button class="btn btn-sm btn-secondary" onclick="downloadFile('${itemPath}'); event.stopPropagation();">下载</button>
            ` : ''}
            ${item.name !== '..' ? `
                <button class="btn btn-sm btn-danger" onclick="deleteItem('${itemPath}'); event.stopPropagation();">删除</button>
            ` : ''}
        </div>
    `;
    
    if (isDir) {
        div.onclick = () => loadFiles(itemPath);
        div.style.cursor = 'pointer';
    }
    
    return div;
}

async function editFile(path) {
    try {
        const response = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        if (data.error) {
            alert('读取文件失败: ' + data.error);
            return;
        }
        
        editingFile = path;
        document.getElementById('editor-filename').textContent = path;
        document.getElementById('file-editor').value = data.content;
        document.getElementById('editor-modal').classList.add('active');
        
    } catch (error) {
        alert('读取文件失败: ' + error.message);
    }
}

async function saveFile() {
    if (!editingFile) return;
    
    const content = document.getElementById('file-editor').value;
    
    try {
        const response = await fetch('/api/files/write', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: editingFile,
                content: content
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('保存成功');
            closeEditor();
            loadFiles(currentPath);
        } else {
            alert('保存失败: ' + result.error);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

function closeEditor() {
    document.getElementById('editor-modal').classList.remove('active');
    editingFile = null;
}

async function deleteItem(path) {
    if (!confirm(`确定要删除 ${path} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/files/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: path })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('删除成功');
            loadFiles(currentPath);
        } else {
            alert('删除失败: ' + result.error);
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

function downloadFile(path) {
    window.open(`/api/files/download?path=${encodeURIComponent(path)}`, '_blank');
}

function createFolder() {
    const name = prompt('输入文件夹名称:');
    if (!name) return;
    
    const path = `${currentPath}/${name}`.replace('//', '/');
    
    fetch('/api/files/mkdir', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ path: path })
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            alert('创建成功');
            loadFiles(currentPath);
        } else {
            alert('创建失败: ' + result.error);
        }
    })
    .catch(error => {
        alert('创建失败: ' + error.message);
    });
}

function createFile() {
    const name = prompt('输入文件名:');
    if (!name) return;
    
    const path = `${currentPath}/${name}`.replace('//', '/');
    
    fetch('/api/files/write', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ path: path, content: '' })
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            alert('创建成功');
            loadFiles(currentPath);
        } else {
            alert('创建失败: ' + result.error);
        }
    })
    .catch(error => {
        alert('创建失败: ' + error.message);
    });
}

function uploadFile() {
    const input = document.createElement('input');
    input.type = 'file';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('path', currentPath);
        
        try {
            const response = await fetch('/api/files/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('上传成功');
                loadFiles(currentPath);
            } else {
                alert('上传失败: ' + result.error);
            }
        } catch (error) {
            alert('上传失败: ' + error.message);
        }
    };
    input.click();
}

// ==================== 设置功能 ====================

// 修改密码
function changePassword() {
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    if (!newPassword || !confirmPassword) {
        alert('请输入密码');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        alert('两次输入的密码不一致');
        return;
    }
    
    if (newPassword.length < 6) {
        alert('密码长度至少6位');
        return;
    }
    
    alert('密码修改功能需要在 config.py 中手动修改\n\n当前默认密码在配置文件中设置:\nDEFAULT_PASSWORD = "' + newPassword + '"\n\n修改后重启服务生效。');
    
    document.getElementById('new-password').value = '';
    document.getElementById('confirm-password').value = '';
}

// 保存界面设置
function saveSettings() {
    const refreshInterval = document.getElementById('refresh-interval').value;
    const terminalFontSize = document.getElementById('terminal-font-size').value;
    
    // 保存到 localStorage
    localStorage.setItem('refreshInterval', refreshInterval);
    localStorage.setItem('terminalFontSize', terminalFontSize);
    
    // 应用设置
    applySettings();
    
    alert('设置已保存');
}

// 应用设置
function applySettings() {
    const refreshInterval = localStorage.getItem('refreshInterval') || '2';
    const terminalFontSize = localStorage.getItem('terminalFontSize') || '14';
    const theme = localStorage.getItem('theme') || 'dark';
    
    // 更新界面
    document.getElementById('refresh-interval').value = refreshInterval;
    document.getElementById('terminal-font-size').value = terminalFontSize;
    document.getElementById('theme-select').value = theme;
    
    // 应用主题
    if (theme === 'light') {
        document.body.classList.add('light-theme');
    } else {
        document.body.classList.remove('light-theme');
    }
    
    // 应用仪表板刷新间隔
    if (dashboardInterval) {
        clearInterval(dashboardInterval);
        dashboardInterval = setInterval(updateDashboard, parseInt(refreshInterval) * 1000);
    }
    
    // 应用终端字体大小
    if (term) {
        term.options.fontSize = parseInt(terminalFontSize);
        if (fitAddon) {
            fitAddon.fit();
        }
    }
}

// 切换主题
function changeTheme() {
    const theme = document.getElementById('theme-select').value;
    localStorage.setItem('theme', theme);
    
    if (theme === 'light') {
        document.body.classList.add('light-theme');
        showMessage('已切换到浅色主题', 'success');
    } else {
        document.body.classList.remove('light-theme');
        showMessage('已切换到深色主题', 'success');
    }
}

// 加载系统信息
async function loadSystemInfo() {
    try {
        const response = await fetch('/api/system/info');
        const data = await response.json();
        
        // 这里可以获取主机名等信息
        // 由于系统信息API不包含这些，显示占位符
        document.getElementById('hostname').textContent = 'raspberrypi';
        document.getElementById('os-info').textContent = 'Raspberry Pi OS';
        document.getElementById('kernel').textContent = 'Linux';
        document.getElementById('python-version').textContent = 'Python 3.x';
        
        // 自动检查更新
        checkForUpdates();
        
    } catch (error) {
        console.error('加载系统信息失败:', error);
    }
}

// ==================== 系统更新功能 ====================

// 检查更新
async function checkForUpdates() {
    try {
        document.getElementById('update-status').textContent = '检查中...';
        
        const response = await fetch('/api/update/check');
        const data = await response.json();
        
        if (data.success) {
            const versionEl = document.getElementById('current-version');
            const statusEl = document.getElementById('update-status');
            const updateBtn = document.getElementById('update-btn');
            
            // 显示当前版本（只显示前7位commit hash）
            const shortHash = data.current_version.split(' ')[0].substring(0, 7);
            versionEl.textContent = shortHash;
            
            if (data.has_update) {
                statusEl.textContent = `有 ${data.commits_behind} 个更新可用`;
                statusEl.style.color = '#FFC107';
                updateBtn.style.display = 'inline-block';
                
                showUpdateMessage(`发现新版本！落后 ${data.commits_behind} 个提交`, 'warning');
            } else {
                statusEl.textContent = '已是最新版本';
                statusEl.style.color = '#4CAF50';
                updateBtn.style.display = 'none';
                
                showUpdateMessage('您的系统已是最新版本', 'success');
            }
        } else {
            document.getElementById('update-status').textContent = '检查失败';
            showUpdateMessage('检查更新失败: ' + data.error, 'error');
        }
    } catch (error) {
        document.getElementById('update-status').textContent = '检查失败';
        showUpdateMessage('检查更新失败: ' + error.message, 'error');
    }
}

// 执行更新
async function performUpdate() {
    if (!confirm('确定要更新系统吗？更新后需要重启服务。')) return;
    
    try {
        const updateBtn = document.getElementById('update-btn');
        const forceUpdateBtn = document.getElementById('force-update-btn');
        const restartBtn = document.getElementById('restart-btn');
        
        updateBtn.disabled = true;
        updateBtn.textContent = '更新中...';
        
        showUpdateMessage('正在从 GitHub 拉取最新代码...', 'warning');
        
        const response = await fetch('/api/update/pull', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showUpdateMessage('更新成功！' + data.message, 'success');
            updateBtn.style.display = 'none';
            forceUpdateBtn.style.display = 'none';
            restartBtn.style.display = 'inline-block';
            
            // 重新检查版本
            setTimeout(checkForUpdates, 2000);
        } else {
            showUpdateMessage('更新失败: ' + data.error + '\n如果有本地修改冲突，请使用"强制更新"', 'error');
            updateBtn.disabled = false;
            updateBtn.textContent = '立即更新';
            // 显示强制更新按钮
            forceUpdateBtn.style.display = 'inline-block';
        }
    } catch (error) {
        showUpdateMessage('更新失败: ' + error.message, 'error');
        const updateBtn = document.getElementById('update-btn');
        updateBtn.disabled = false;
        updateBtn.textContent = '立即更新';
        // 显示强制更新按钮
        document.getElementById('force-update-btn').style.display = 'inline-block';
    }
}

// 强制更新（丢弃本地修改）
async function forceUpdate() {
    if (!confirm('⚠️ 警告：强制更新会丢弃所有本地修改！\n\n确定要继续吗？')) return;
    
    try {
        const forceUpdateBtn = document.getElementById('force-update-btn');
        const updateBtn = document.getElementById('update-btn');
        const restartBtn = document.getElementById('restart-btn');
        
        forceUpdateBtn.disabled = true;
        forceUpdateBtn.textContent = '强制更新中...';
        
        showUpdateMessage('正在重置本地修改并拉取最新代码...', 'warning');
        
        const response = await fetch('/api/update/force', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showUpdateMessage('强制更新成功！' + data.message, 'success');
            forceUpdateBtn.style.display = 'none';
            updateBtn.style.display = 'none';
            restartBtn.style.display = 'inline-block';
            
            // 重新检查版本
            setTimeout(checkForUpdates, 2000);
        } else {
            showUpdateMessage('强制更新失败: ' + data.error, 'error');
            forceUpdateBtn.disabled = false;
            forceUpdateBtn.textContent = '强制更新';
        }
    } catch (error) {
        showUpdateMessage('强制更新失败: ' + error.message, 'error');
        const forceUpdateBtn = document.getElementById('force-update-btn');
        forceUpdateBtn.disabled = false;
        forceUpdateBtn.textContent = '强制更新';
    }
}

// 重启应用
async function restartApp() {
    if (!confirm('确定要重启应用吗？')) return;
    
    try {
        showUpdateMessage('正在重启应用...', 'warning');
        
        const response = await fetch('/api/update/restart', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showUpdateMessage('应用正在重启，页面将在5秒后刷新...', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        } else if (data.manual) {
            showUpdateMessage(data.error, 'warning');
        } else {
            showUpdateMessage('重启失败: ' + data.error, 'error');
        }
    } catch (error) {
        showUpdateMessage('重启请求失败，请手动重启应用', 'warning');
    }
}

// 显示更新消息
function showUpdateMessage(message, type = 'success') {
    const messageEl = document.getElementById('update-message');
    messageEl.textContent = message;
    messageEl.className = 'update-message';
    
    if (type === 'error') {
        messageEl.classList.add('error');
    } else if (type === 'warning') {
        messageEl.classList.add('warning');
    }
    
    messageEl.style.display = 'block';
    
    // 3秒后自动隐藏成功消息
    if (type === 'success') {
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 3000);
    }
}

// ==================== 系统控制功能 ====================

// 加载系统控制页面
async function loadSystemControl() {
    loadUptime();
    loadProcesses();
    loadSystemLogs();
}

// 加载系统运行时间
async function loadUptime() {
    try {
        const response = await fetch('/api/control/uptime');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('system-uptime').textContent = data.uptime;
            document.getElementById('boot-time').textContent = data.boot_time;
        }
    } catch (error) {
        console.error('加载运行时间失败:', error);
    }
}

// 重启系统
async function rebootSystem() {
    if (!confirm('确定要重启系统吗？')) return;
    
    try {
        const response = await fetch('/api/control/reboot', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            alert('系统正在重启...');
        } else {
            alert('重启失败: ' + data.error);
        }
    } catch (error) {
        alert('重启失败: ' + error.message);
    }
}

// 关机
async function shutdownSystem() {
    if (!confirm('确定要关闭系统吗？')) return;
    
    try {
        const response = await fetch('/api/control/shutdown', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            alert('系统正在关机...');
        } else {
            alert('关机失败: ' + data.error);
        }
    } catch (error) {
        alert('关机失败: ' + error.message);
    }
}

// 加载进程列表
async function loadProcesses() {
    try {
        const response = await fetch('/api/control/processes');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.getElementById('process-list');
            tbody.innerHTML = '';
            
            // 只显示前50个进程
            const processes = data.processes.slice(0, 50);
            
            processes.forEach(proc => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${proc.pid}</td>
                    <td>${proc.name}</td>
                    <td>${proc.user}</td>
                    <td>${proc.cpu}%</td>
                    <td>${proc.memory}%</td>
                    <td>${proc.status}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="killProcess(${proc.pid})">结束</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('加载进程列表失败:', error);
    }
}

// 结束进程
async function killProcess(pid) {
    if (!confirm(`确定要结束进程 ${pid} 吗？`)) return;
    
    try {
        const response = await fetch(`/api/control/processes/${pid}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            alert('进程已结束');
            loadProcesses();
        } else {
            alert('结束进程失败: ' + data.error);
        }
    } catch (error) {
        alert('结束进程失败: ' + error.message);
    }
}

// 加载系统日志
async function loadSystemLogs() {
    try {
        const lines = document.getElementById('log-lines').value;
        const response = await fetch(`/api/control/logs?lines=${lines}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('system-logs').textContent = data.logs;
        } else {
            document.getElementById('system-logs').textContent = '加载日志失败: ' + data.error;
        }
    } catch (error) {
        document.getElementById('system-logs').textContent = '加载日志失败: ' + error.message;
    }
}

// ==================== Docker 管理功能 ====================

// 加载 Docker 数据
async function loadDockerData() {
    // 检查 Docker 是否安装
    const checkResponse = await fetch('/api/docker/check');
    const checkData = await checkResponse.json();
    
    if (!checkData.installed) {
        document.getElementById('docker-not-installed').style.display = 'block';
        document.getElementById('docker-content').style.display = 'none';
        return;
    }
    
    document.getElementById('docker-not-installed').style.display = 'none';
    document.getElementById('docker-content').style.display = 'block';
    
    // 加载 Docker 信息
    await loadDockerInfo();
    await loadDockerContainers();
    await loadDockerImages();
}

// 加载 Docker 系统信息
async function loadDockerInfo() {
    try {
        const response = await fetch('/api/docker/info');
        const data = await response.json();
        
        if (data.success) {
            const info = data.info;
            document.getElementById('docker-containers-total').textContent = info.containers || 0;
            document.getElementById('docker-containers-running').textContent = info.running || 0;
            document.getElementById('docker-containers-stopped').textContent = info.stopped || 0;
            document.getElementById('docker-images-total').textContent = info.images || 0;
        }
    } catch (error) {
        console.error('加载 Docker 信息失败:', error);
    }
}

// 加载容器列表
async function loadDockerContainers() {
    try {
        const showAll = document.getElementById('show-all-containers').checked;
        const response = await fetch(`/api/docker/containers?all=${showAll}`);
        const data = await response.json();
        
        const tbody = document.getElementById('docker-containers-list');
        tbody.innerHTML = '';
        
        if (data.success && data.containers.length > 0) {
            data.containers.forEach(container => {
                const row = document.createElement('tr');
                const isRunning = container.state.toLowerCase() === 'running';
                
                row.innerHTML = `
                    <td>${container.name}</td>
                    <td>${container.image}</td>
                    <td>
                        <span class="status-badge ${isRunning ? 'status-running' : 'status-stopped'}">
                            ${container.status}
                        </span>
                    </td>
                    <td>${container.ports || '-'}</td>
                    <td>
                        <div class="btn-group">
                            ${isRunning ? 
                                `<button class="btn btn-sm btn-warning" onclick="controlDockerContainer('${container.id}', 'stop')">停止</button>
                                 <button class="btn btn-sm" onclick="viewContainerLogs('${container.id}')">日志</button>` :
                                `<button class="btn btn-sm btn-primary" onclick="controlDockerContainer('${container.id}', 'start')">启动</button>`
                            }
                            <button class="btn btn-sm btn-warning" onclick="controlDockerContainer('${container.id}', 'restart')">重启</button>
                            <button class="btn btn-sm btn-danger" onclick="controlDockerContainer('${container.id}', 'rm')">删除</button>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: rgba(255,255,255,0.5);">暂无容器</td></tr>';
        }
    } catch (error) {
        console.error('加载容器列表失败:', error);
        document.getElementById('docker-containers-list').innerHTML = 
            '<tr><td colspan="5" style="text-align: center; color: #f44336;">加载失败</td></tr>';
    }
}

// 加载镜像列表
async function loadDockerImages() {
    try {
        const response = await fetch('/api/docker/images');
        const data = await response.json();
        
        const tbody = document.getElementById('docker-images-list');
        tbody.innerHTML = '';
        
        if (data.success && data.images.length > 0) {
            data.images.forEach(image => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${image.repository}</td>
                    <td>${image.tag}</td>
                    <td>${image.size}</td>
                    <td>${image.created}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="removeDockerImage('${image.id}')">删除</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: rgba(255,255,255,0.5);">暂无镜像</td></tr>';
        }
    } catch (error) {
        console.error('加载镜像列表失败:', error);
        document.getElementById('docker-images-list').innerHTML = 
            '<tr><td colspan="5" style="text-align: center; color: #f44336;">加载失败</td></tr>';
    }
}

// 控制容器
async function controlDockerContainer(containerId, action) {
    const actionMap = {
        'start': '启动',
        'stop': '停止',
        'restart': '重启',
        'rm': '删除'
    };
    
    if (action === 'rm' && !confirm(`确定要删除容器 ${containerId.substring(0, 12)} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/docker/containers/${containerId}/${action}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`容器${actionMap[action]}成功`);
            loadDockerData();
        } else {
            alert(`容器${actionMap[action]}失败: ${data.error}`);
        }
    } catch (error) {
        alert(`操作失败: ${error.message}`);
    }
}

// 查看容器日志
async function viewContainerLogs(containerId) {
    try {
        const response = await fetch(`/api/docker/containers/${containerId}/logs?lines=200`);
        const data = await response.json();
        
        if (data.success) {
            const logWindow = window.open('', '_blank', 'width=800,height=600');
            logWindow.document.write(`
                <html>
                <head>
                    <title>容器日志 - ${containerId.substring(0, 12)}</title>
                    <style>
                        body { 
                            background: #1a1a1a; 
                            color: #fff; 
                            font-family: 'Courier New', monospace; 
                            padding: 20px;
                            margin: 0;
                        }
                        pre { 
                            white-space: pre-wrap; 
                            word-wrap: break-word;
                            font-size: 12px;
                            line-height: 1.5;
                        }
                    </style>
                </head>
                <body>
                    <h2>容器日志: ${containerId.substring(0, 12)}</h2>
                    <pre>${data.logs}</pre>
                </body>
                </html>
            `);
        } else {
            alert('获取日志失败: ' + data.error);
        }
    } catch (error) {
        alert('获取日志失败: ' + error.message);
    }
}

// 删除镜像
async function removeDockerImage(imageId) {
    if (!confirm(`确定要删除镜像 ${imageId} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/docker/images/${imageId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            alert('镜像删除成功');
            loadDockerData();
        } else {
            alert('镜像删除失败: ' + data.error);
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 显示拉取镜像对话框
function showPullImageDialog() {
    const imageName = prompt('请输入要拉取的镜像名称\n例如: nginx:latest, mysql:8.0');
    
    if (imageName) {
        pullDockerImage(imageName);
    }
}

// 拉取镜像
async function pullDockerImage(imageName) {
    try {
        alert('正在拉取镜像，请稍候...');
        
        const response = await fetch('/api/docker/images/pull', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageName })
        });
        const data = await response.json();
        
        if (data.success) {
            alert('镜像拉取成功！');
            loadDockerData();
        } else {
            alert('镜像拉取失败: ' + data.error);
        }
    } catch (error) {
        alert('拉取失败: ' + error.message);
    }
}

// 清理 Docker 资源
async function pruneDocker() {
    if (!confirm('确定要清理未使用的 Docker 资源吗？\n这将删除:\n- 停止的容器\n- 未使用的网络\n- 悬空的镜像\n- 构建缓存')) {
        return;
    }
    
    try {
        const response = await fetch('/api/docker/system/prune', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert('清理完成！\n' + data.output);
            loadDockerData();
        } else {
            alert('清理失败: ' + data.error);
        }
    } catch (error) {
        alert('清理失败: ' + error.message);
    }
}

// ==================== 告警功能 ====================

let alertCheckInterval = null;

// 启动告警检查
function startAlertChecking() {
    // 每30秒检查一次
    alertCheckInterval = setInterval(checkAlerts, 30000);
    checkAlerts(); // 立即检查一次
}

// 检查告警
async function checkAlerts() {
    try {
        const response = await fetch('/api/alerts/check');
        const data = await response.json();
        
        if (data.success && data.alerts.length > 0) {
            // 请求通知权限
            if (Notification.permission === 'default') {
                await Notification.requestPermission();
            }
            
            // 显示告警
            data.alerts.forEach(alert => {
                showAlert(alert);
                
                // 浏览器通知
                if (Notification.permission === 'granted') {
                    new Notification('系统告警', {
                        body: alert.message,
                        icon: '/static/images/logo.svg'
                    });
                }
            });
        }
    } catch (error) {
        console.error('检查告警失败:', error);
    }
}

// 显示告警消息
function showAlert(alert) {
    // 创建告警容器（如果不存在）
    let container = document.querySelector('.alert-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'alert-container';
        document.body.appendChild(container);
    }
    
    // 创建告警元素
    const alertEl = document.createElement('div');
    alertEl.className = `alert ${alert.level}`;
    alertEl.innerHTML = `
        <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        <strong>${alert.type.toUpperCase()}</strong><br>
        ${alert.message}
    `;
    
    container.appendChild(alertEl);
    
    // 5秒后自动关闭
    setTimeout(() => {
        alertEl.remove();
    }, 5000);
}

// ==================== 包管理 ====================

let currentPackageTab = 'installed';

function loadPackages() {
    loadInstalledPackages();
}

function switchPackageTab(tab) {
    currentPackageTab = tab;
    
    // 切换tab按钮状态
    document.querySelectorAll('.package-tabs .tab-btn').forEach((btn, index) => {
        btn.classList.remove('active');
        if ((index === 0 && tab === 'installed') ||
            (index === 1 && tab === 'upgradable') ||
            (index === 2 && tab === 'search')) {
            btn.classList.add('active');
        }
    });
    
    // 切换内容
    document.querySelectorAll('.package-content .tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tab}`).classList.add('active');
    
    // 加载对应数据
    if (tab === 'installed') {
        loadInstalledPackages();
    } else if (tab === 'upgradable') {
        loadUpgradablePackages();
    }
}

async function loadInstalledPackages() {
    try {
        const response = await fetch('/api/apt/installed?limit=200');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('installed-packages');
            if (data.packages.length === 0) {
                container.innerHTML = '<p style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.5);">未找到已安装的软件包</p>';
                return;
            }
            
            container.innerHTML = data.packages.map(pkg => `
                <div class="package-item" data-name="${pkg.name}">
                    <div class="package-info">
                        <div class="package-name">${pkg.name}</div>
                        <div class="package-version">${pkg.version} (${pkg.architecture})</div>
                        <div class="package-description">${pkg.description || ''}</div>
                    </div>
                    <div class="package-actions">
                        <button class="btn btn-sm" onclick="showPackageInfo('${pkg.name}')">详情</button>
                        <button class="btn btn-sm btn-danger" onclick="removePackage('${pkg.name}')">卸载</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        showMessage('加载已安装软件包失败: ' + error.message, 'error');
    }
}

async function loadUpgradablePackages() {
    try {
        const response = await fetch('/api/apt/upgradable');
        const data = await response.json();
        
        if (data.success) {
            const info = document.getElementById('upgradable-info');
            const container = document.getElementById('upgradable-packages');
            
            info.innerHTML = `<p>发现 <strong>${data.total}</strong> 个可更新的软件包</p>`;
            
            if (data.packages.length === 0) {
                container.innerHTML = '<p style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.5);">所有软件包都是最新的</p>';
                return;
            }
            
            container.innerHTML = data.packages.map(pkg => `
                <div class="package-item">
                    <div class="package-info">
                        <div class="package-name">${pkg.name}</div>
                        <div class="package-version">
                            ${pkg.current_version} → <strong style="color: #4CAF50;">${pkg.new_version}</strong>
                        </div>
                    </div>
                    <div class="package-actions">
                        <button class="btn btn-sm btn-primary" onclick="installPackage('${pkg.name}')">更新</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        showMessage('加载可更新软件包失败: ' + error.message, 'error');
    }
}

async function searchPackages() {
    const keyword = document.getElementById('search-keyword').value.trim();
    if (!keyword) {
        showMessage('请输入搜索关键词', 'warning');
        return;
    }
    
    try {
        const container = document.getElementById('search-results');
        container.innerHTML = '<p style="text-align: center; padding: 2rem;">搜索中...</p>';
        
        const response = await fetch(`/api/apt/search?keyword=${encodeURIComponent(keyword)}&limit=50`);
        const data = await response.json();
        
        if (data.success) {
            if (data.packages.length === 0) {
                container.innerHTML = '<p style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.5);">未找到匹配的软件包</p>';
                return;
            }
            
            container.innerHTML = data.packages.map(pkg => `
                <div class="package-item">
                    <div class="package-info">
                        <div class="package-name">${pkg.name}</div>
                        <div class="package-version">${pkg.version} ${pkg.status ? `[${pkg.status}]` : ''}</div>
                        <div class="package-description">${pkg.description || ''}</div>
                    </div>
                    <div class="package-actions">
                        <button class="btn btn-sm" onclick="showPackageInfo('${pkg.name}')">详情</button>
                        <button class="btn btn-sm btn-primary" onclick="installPackage('${pkg.name}')">安装</button>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `<p style="text-align: center; padding: 2rem; color: #f44336;">${data.error}</p>`;
        }
    } catch (error) {
        document.getElementById('search-results').innerHTML = `<p style="text-align: center; padding: 2rem; color: #f44336;">搜索失败: ${error.message}</p>`;
    }
}

function filterPackages(type) {
    const input = document.getElementById(`filter-${type}`);
    const filter = input.value.toLowerCase();
    const items = document.querySelectorAll(`#${type}-packages .package-item`);
    
    items.forEach(item => {
        const name = item.dataset.name.toLowerCase();
        if (name.includes(filter)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

async function aptUpdate() {
    if (!confirm('确定要更新软件包列表吗？')) return;
    
    try {
        showMessage('正在更新软件包列表...', 'info');
        const response = await fetch('/api/apt/update', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showMessage('软件包列表更新成功', 'success');
            if (currentPackageTab === 'upgradable') {
                loadUpgradablePackages();
            }
        } else {
            showMessage('更新失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('更新失败: ' + error.message, 'error');
    }
}

async function aptUpgrade() {
    if (!confirm('确定要升级所有软件包吗？这可能需要较长时间。')) return;
    
    try {
        showMessage('正在升级系统，请稍候...', 'info');
        const response = await fetch('/api/apt/upgrade', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showMessage('系统升级成功', 'success');
            loadUpgradablePackages();
        } else {
            showMessage('升级失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('升级失败: ' + error.message, 'error');
    }
}

async function installPackage(packageName) {
    if (!confirm(`确定要安装 ${packageName} 吗？`)) return;
    
    try {
        showMessage(`正在安装 ${packageName}...`, 'info');
        const response = await fetch('/api/apt/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ package: packageName })
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            if (currentPackageTab === 'installed') {
                loadInstalledPackages();
            }
        } else {
            showMessage('安装失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('安装失败: ' + error.message, 'error');
    }
}

async function removePackage(packageName) {
    const purge = confirm(`确定要卸载 ${packageName} 吗？\n\n点击"确定"完全清除（包括配置文件）\n点击"取消"放弃操作`);
    if (purge === null) return;
    
    try {
        showMessage(`正在卸载 ${packageName}...`, 'info');
        const response = await fetch('/api/apt/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ package: packageName, purge: purge })
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadInstalledPackages();
        } else {
            showMessage('卸载失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('卸载失败: ' + error.message, 'error');
    }
}

async function showPackageInfo(packageName) {
    try {
        const response = await fetch(`/api/apt/info?package=${encodeURIComponent(packageName)}`);
        const data = await response.json();
        
        if (data.success) {
            const info = data.info;
            let details = '';
            for (const [key, value] of Object.entries(info)) {
                if (value && key !== 'Description') {
                    details += `<strong>${key}:</strong> ${value}<br>`;
                }
            }
            
            alert(`软件包信息：\n\n${packageName}\n\n${details.replace(/<br>/g, '\n').replace(/<\/?strong>/g, '')}`);
        } else {
            showMessage('获取软件包信息失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('获取软件包信息失败: ' + error.message, 'error');
    }
}

async function aptClean() {
    if (!confirm('确定要清理 APT 缓存吗？')) return;
    
    try {
        const response = await fetch('/api/apt/clean', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showMessage('缓存清理成功', 'success');
        } else {
            showMessage('清理失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('清理失败: ' + error.message, 'error');
    }
}

async function aptAutoremove() {
    if (!confirm('确定要自动移除不需要的软件包吗？')) return;
    
    try {
        showMessage('正在清理...', 'info');
        const response = await fetch('/api/apt/autoremove', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showMessage('自动清理完成', 'success');
            loadInstalledPackages();
        } else {
            showMessage('清理失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('清理失败: ' + error.message, 'error');
    }
}

// ==================== 用户管理 ====================

let currentUserTab = 'users';

function switchUserTab(tab) {
    currentUserTab = tab;
    
    // 切换tab按钮状态
    document.querySelectorAll('.user-tabs .tab-btn').forEach((btn, index) => {
        btn.classList.remove('active');
        if ((index === 0 && tab === 'users') ||
            (index === 1 && tab === 'groups') ||
            (index === 2 && tab === 'logged')) {
            btn.classList.add('active');
        }
    });
    
    // 切换内容
    document.querySelectorAll('.user-content .tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tab}`).classList.add('active');
    
    // 加载对应数据
    if (tab === 'users') {
        loadUsers();
    } else if (tab === 'groups') {
        loadUserGroups();
    } else if (tab === 'logged') {
        loadLoggedInUsers();
    }
}

async function loadUsers() {
    try {
        const includeSystem = document.getElementById('show-system-users')?.checked || false;
        const response = await fetch(`/api/users/list?include_system=${includeSystem}`);
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.getElementById('users-table-body');
            if (data.users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.5);">无用户数据</td></tr>';
                return;
            }
            
            tbody.innerHTML = data.users.map(user => `
                <tr>
                    <td><strong>${user.username}</strong></td>
                    <td>${user.uid}</td>
                    <td>${user.home}</td>
                    <td>${user.shell}</td>
                    <td>${user.groups.join(', ')}</td>
                    <td>
                        ${user.is_sudo ? '<span class="badge badge-success">sudo</span>' : '<span class="badge">普通</span>'}
                    </td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm" onclick="changeUserPassword('${user.username}')">改密</button>
                            <button class="btn btn-sm" onclick="manageUserGroups('${user.username}')">组管理</button>
                            ${!user.is_sudo ? `<button class="btn btn-sm btn-danger" onclick="deleteUser('${user.username}')">删除</button>` : ''}
                        </div>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        showMessage('加载用户列表失败: ' + error.message, 'error');
    }
}

async function loadUserGroups() {
    try {
        const response = await fetch('/api/users/groups');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.getElementById('groups-table-body');
            if (data.groups.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.5);">无用户组数据</td></tr>';
                return;
            }
            
            tbody.innerHTML = data.groups.filter(g => g.gid >= 1000 || ['sudo', 'docker', 'www-data'].includes(g.name))
                .map(group => `
                <tr>
                    <td><strong>${group.name}</strong></td>
                    <td>${group.gid}</td>
                    <td>${group.members.join(', ') || '无'}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        showMessage('加载用户组失败: ' + error.message, 'error');
    }
}

async function loadLoggedInUsers() {
    try {
        const response = await fetch('/api/users/logged');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.getElementById('logged-table-body');
            if (data.users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.5);">当前无登录用户</td></tr>';
                return;
            }
            
            tbody.innerHTML = data.users.map(user => `
                <tr>
                    <td><strong>${user.username}</strong></td>
                    <td>${user.terminal}</td>
                    <td>${user.login_time}</td>
                    <td>${user.ip}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        showMessage('加载在线用户失败: ' + error.message, 'error');
    }
}

function showAddUserDialog() {
    const username = prompt('请输入用户名（小写字母、数字、下划线）:');
    if (!username) return;
    
    const password = prompt('请输入密码:');
    if (!password) return;
    
    const addToSudo = confirm('是否授予 sudo 权限？');
    
    addUser(username, password, addToSudo ? ['sudo'] : []);
}

async function addUser(username, password, groups = []) {
    try {
        showMessage(`正在创建用户 ${username}...`, 'info');
        const response = await fetch('/api/users/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                password,
                groups,
                create_home: true
            })
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadUsers();
        } else {
            showMessage('创建用户失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('创建用户失败: ' + error.message, 'error');
    }
}

async function deleteUser(username) {
    if (!confirm(`确定要删除用户 ${username} 吗？`)) return;
    
    const removeHome = confirm('是否同时删除用户的主目录？');
    
    try {
        const response = await fetch('/api/users/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, remove_home: removeHome })
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadUsers();
        } else {
            showMessage('删除用户失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('删除用户失败: ' + error.message, 'error');
    }
}

async function changeUserPassword(username) {
    const password = prompt(`请输入 ${username} 的新密码:`);
    if (!password) return;
    
    try {
        const response = await fetch('/api/users/password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
        } else {
            showMessage('修改密码失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('修改密码失败: ' + error.message, 'error');
    }
}

async function manageUserGroups(username) {
    const action = prompt(`用户组管理：${username}\n\n输入 "add" 添加到组\n输入 "remove" 从组移除`);
    if (!action) return;
    
    const group = prompt('请输入组名（如: sudo, docker）:');
    if (!group) return;
    
    try {
        const endpoint = action === 'add' ? '/api/users/group/add' : '/api/users/group/remove';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, group })
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadUsers();
        } else {
            showMessage('操作失败: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('操作失败: ' + error.message, 'error');
    }
}

function showMessage(message, type = 'info') {
    const colors = {
        info: '#2196F3',
        success: '#4CAF50',
        warning: '#FF9800',
        error: '#f44336'
    };
    
    const msgDiv = document.createElement('div');
    msgDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        z-index: 10000;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    msgDiv.textContent = message;
    
    document.body.appendChild(msgDiv);
    
    setTimeout(() => {
        msgDiv.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => msgDiv.remove(), 300);
    }, 3000);
}

// ==================== 初始化 ====================

// 页面加载完成后启动仪表板更新
document.addEventListener('DOMContentLoaded', () => {
    startDashboardUpdates();
    applySettings();
    startAlertChecking();
});
