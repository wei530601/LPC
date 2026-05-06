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
        } else if (page === 'settings') {
            loadSystemInfo();
            applySettings();
        } else if (page === 'control') {
            loadSystemControl();
        } else if (page === 'history') {
            loadHistoryData();
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
    
    // 更新界面
    document.getElementById('refresh-interval').value = refreshInterval;
    document.getElementById('terminal-font-size').value = terminalFontSize;
    
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
        
    } catch (error) {
        console.error('加载系统信息失败:', error);
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

// ==================== 历史数据功能 ====================

let currentDuration = '24h';
let charts = {};

// 加载历史数据
async function loadHistoryData() {
    await loadStatistics();
    await loadCharts();
}

// 切换时间范围
function changeDuration(duration) {
    currentDuration = duration;
    
    // 更新按钮状态
    document.querySelectorAll('.duration-selector .btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.duration === duration) {
            btn.classList.add('active');
        }
    });
    
    loadHistoryData();
}

// 加载统计信息
async function loadStatistics() {
    try {
        const response = await fetch(`/api/history/statistics?duration=${currentDuration}`);
        const data = await response.json();
        
        if (data.success) {
            const stats = data.statistics;
            
            // CPU
            document.getElementById('stat-cpu-current').textContent = stats.cpu.current + '%';
            document.getElementById('stat-cpu-avg').textContent = stats.cpu.avg + '%';
            document.getElementById('stat-cpu-max').textContent = stats.cpu.max + '%';
            
            // 内存
            document.getElementById('stat-memory-current').textContent = stats.memory.current + '%';
            document.getElementById('stat-memory-avg').textContent = stats.memory.avg + '%';
            document.getElementById('stat-memory-max').textContent = stats.memory.max + '%';
            
            // 温度
            document.getElementById('stat-temp-current').textContent = stats.temperature.current + '°C';
            document.getElementById('stat-temp-avg').textContent = stats.temperature.avg + '°C';
            document.getElementById('stat-temp-max').textContent = stats.temperature.max + '°C';
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 加载图表
async function loadCharts() {
    await loadChart('cpu', 'CPU 使用率 (%)', '#4CAF50');
    await loadChart('memory', '内存使用率 (%)', '#2196F3');
    await loadChart('temperature', '温度 (°C)', '#FF9800');
    await loadNetworkChart();
}

// 加载单个图表
async function loadChart(metric, label, color) {
    try {
        const response = await fetch(`/api/history/${metric}?duration=${currentDuration}`);
        const data = await response.json();
        
        if (data.success) {
            const chartId = `${metric}-chart`;
            const ctx = document.getElementById(chartId);
            
            // 销毁旧图表
            if (charts[chartId]) {
                charts[chartId].destroy();
            }
            
            // 创建新图表
            charts[chartId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.data.map(d => new Date(d.time).toLocaleTimeString('zh-CN', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    })),
                    datasets: [{
                        label: label,
                        data: data.data.map(d => d.value),
                        borderColor: color,
                        backgroundColor: color + '20',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.7)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.7)',
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error(`加载${metric}图表失败:`, error);
    }
}

// 加载网络图表
async function loadNetworkChart() {
    try {
        const [sentResponse, recvResponse] = await Promise.all([
            fetch(`/api/history/network_sent?duration=${currentDuration}`),
            fetch(`/api/history/network_recv?duration=${currentDuration}`)
        ]);
        
        const sentData = await sentResponse.json();
        const recvData = await recvResponse.json();
        
        if (sentData.success && recvData.success) {
            const chartId = 'network-chart';
            const ctx = document.getElementById(chartId);
            
            if (charts[chartId]) {
                charts[chartId].destroy();
            }
            
            charts[chartId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: sentData.data.map(d => new Date(d.time).toLocaleTimeString('zh-CN', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    })),
                    datasets: [
                        {
                            label: '发送 (MB)',
                            data: sentData.data.map(d => d.value),
                            borderColor: '#E91E63',
                            backgroundColor: '#E91E6320',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: '接收 (MB)',
                            data: recvData.data.map(d => d.value),
                            borderColor: '#9C27B0',
                            backgroundColor: '#9C27B020',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: 'rgba(255, 255, 255, 0.7)'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.7)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'rgba(255, 255, 255, 0.7)',
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('加载网络图表失败:', error);
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

// ==================== 初始化 ====================

// 页面加载完成后启动仪表板更新
document.addEventListener('DOMContentLoaded', () => {
    startDashboardUpdates();
    applySettings();
    startAlertChecking();
});
