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
        } else if (page === 'terminal') {
            initTerminal();
        } else if (page === 'files') {
            loadFiles('/');
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
        
        document.getElementById('cpu-avg').textContent = 
            (totalCpu / data.cpu.percent.length).toFixed(1) + '%';
        
        // 内存
        const memPercent = data.memory.percent;
        document.getElementById('mem-percent').textContent = memPercent.toFixed(1) + '%';
        document.getElementById('mem-bar').style.width = memPercent + '%';
        document.getElementById('mem-used').textContent = formatBytes(data.memory.used);
        document.getElementById('mem-total').textContent = formatBytes(data.memory.total);
        document.getElementById('swap-used').textContent = formatBytes(data.memory.swap.used);
        document.getElementById('swap-total').textContent = formatBytes(data.memory.swap.total);
        
        // 磁盘
        const diskList = document.getElementById('disk-list');
        diskList.innerHTML = '';
        data.disk.forEach(disk => {
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
        
        // 温度
        const tempList = document.getElementById('temperature-list');
        tempList.innerHTML = '';
        
        for (const [name, temp] of Object.entries(data.temperature)) {
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
    const icon = isDir ? '▶' : '▫';
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

// ==================== 初始化 ====================

// 页面加载完成后启动仪表板更新
document.addEventListener('DOMContentLoaded', () => {
    startDashboardUpdates();
});
