// ==================== 网络管理功能 ====================

let networkRefreshInterval = null;
let currentPerformanceTab = 'cpu';

// 加载网络管理页面
function loadNetworkPage() {
    getWiFiStatus();
    loadNetworkInterfaces();
    loadFirewallStatus();
    loadListeningPorts();
    
    // 启动自动刷新网络连接统计
    if (networkRefreshInterval) {
        clearInterval(networkRefreshInterval);
    }
    loadNetworkConnectionStats();
    networkRefreshInterval = setInterval(loadNetworkConnectionStats, 5000);
}

// ========== WiFi 管理 ==========

async function scanWiFi() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '扫描中...';
    
    try {
        const response = await fetch('/api/network/wifi/scan');
        const data = await response.json();
        
        if (data.success && data.networks.length > 0) {
            const html = `
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>SSID</th>
                            <th>信号强度</th>
                            <th>加密</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.networks.map(network => `
                            <tr>
                                <td>${network.ssid || '(隐藏网络)'}</td>
                                <td>${network.quality || network.signal || 'N/A'}</td>
                                <td>${network.encrypted ? '是' : '否'}</td>
                                <td>
                                    <button class="btn btn-sm" onclick="connectToWiFi('${network.ssid}', ${network.encrypted})">连接</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            document.getElementById('wifi-list').innerHTML = html;
        } else {
            document.getElementById('wifi-list').innerHTML = '<p>未找到WiFi网络</p>';
        }
    } catch (error) {
        showMessage('扫描WiFi失败: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '扫描WiFi';
    }
}

async function getWiFiStatus() {
    try {
        const response = await fetch('/api/network/wifi/current');
        const data = await response.json();
        
        if (data.success && data.wifi.connected) {
            document.getElementById('wifi-current').innerHTML = `
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">当前网络</div>
                        <div class="info-value">${data.wifi.ssid}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">信号强度</div>
                        <div class="info-value">${data.wifi.signal || 'N/A'}</div>
                    </div>
                </div>
                <button class="btn btn-danger btn-sm" onclick="disconnectWiFi()">断开连接</button>
            `;
        } else {
            document.getElementById('wifi-current').innerHTML = '<p>未连接WiFi</p>';
        }
    } catch (error) {
        console.error('获取WiFi状态失败:', error);
    }
}

async function connectToWiFi(ssid, encrypted) {
    let password = '';
    if (encrypted) {
        password = prompt('请输入WiFi密码:');
        if (!password) return;
    }
    
    try {
        const response = await fetch('/api/network/wifi/connect', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ssid, password})
        });
        
        const data = await response.json();
        showMessage(data.message, data.success ? 'success' : 'error');
        
        if (data.success) {
            setTimeout(getWiFiStatus, 3000);
        }
    } catch (error) {
        showMessage('连接失败: ' + error.message, 'error');
    }
}

async function disconnectWiFi() {
    if (!confirm('确定要断开WiFi连接吗？')) return;
    
    try {
        const response = await fetch('/api/network/wifi/disconnect', {
            method: 'POST'
        });
        
        const data = await response.json();
        showMessage(data.message, data.success ? 'success' : 'error');
        
        if (data.success) {
            setTimeout(getWiFiStatus, 1000);
        }
    } catch (error) {
        showMessage('断开失败: ' + error.message, 'error');
    }
}

// ========== 网络接口 ==========

async function loadNetworkInterfaces() {
    try {
        const [interfacesResp, dnsResp] = await Promise.all([
            fetch('/api/network/interfaces'),
            fetch('/api/network/dns')
        ]);
        
        const interfacesData = await interfacesResp.json();
        const dnsData = await dnsResp.json();
        
        if (interfacesData.success) {
            const html = interfacesData.interfaces.map(iface => `
                <div class="card" style="margin-bottom: 1rem;">
                    <div class="card-header">
                        <h4>${iface.name} <span class="badge ${iface.state === 'UP' ? 'badge-success' : 'badge-secondary'}">${iface.state}</span></h4>
                    </div>
                    <div class="card-body">
                        ${iface.ipv4.length > 0 ? `
                            <div><strong>IPv4:</strong> ${iface.ipv4.map(ip => `${ip.address}/${ip.prefix}`).join(', ')}</div>
                        ` : ''}
                        ${iface.ipv6.length > 0 ? `
                            <div><strong>IPv6:</strong> ${iface.ipv6.map(ip => `${ip.address}/${ip.prefix}`).join(', ')}</div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
            document.getElementById('network-interfaces-list').innerHTML = html || '<p>无网络接口</p>';
        }
        
        if (dnsData.success) {
            const dnsHtml = dnsData.dns_servers.length > 0 
                ? dnsData.dns_servers.map(dns => `<div class="badge">${dns}</div>`).join(' ')
                : '<p>无DNS服务器</p>';
            document.getElementById('dns-servers').innerHTML = dnsHtml;
        }
    } catch (error) {
        console.error('加载网络接口失败:', error);
    }
}

// ========== 防火墙管理 ==========

async function loadFirewallStatus() {
    try {
        const response = await fetch('/api/network/firewall/status');
        const data = await response.json();
        
        if (!data.success) {
            document.getElementById('firewall-status').innerHTML = '<p>UFW未安装</p>';
            return;
        }
        
        const status = data.status;
        const html = `
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">状态</div>
                    <div class="info-value">
                        <span class="badge ${status.enabled ? 'badge-success' : 'badge-danger'}">
                            ${status.enabled ? '已启用' : '已禁用'}
                        </span>
                    </div>
                </div>
                <div class="info-item">
                    <div class="info-label">默认入站</div>
                    <div class="info-value">${status.default_incoming}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">默认出站</div>
                    <div class="info-value">${status.default_outgoing}</div>
                </div>
            </div>
            ${status.rules.length > 0 ? `
                <table class="modern-table" style="margin-top: 1rem;">
                    <thead>
                        <tr>
                            <th>目标</th>
                            <th>动作</th>
                            <th>来源</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${status.rules.map((rule, i) => `
                            <tr>
                                <td>${rule.to}</td>
                                <td>${rule.action}</td>
                                <td>${rule.from}</td>
                                <td><button class="btn btn-sm btn-danger" onclick="deleteFirewallRule(${i})">删除</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<p style="margin-top: 1rem;">暂无防火墙规则</p>'}
        `;
        document.getElementById('firewall-status').innerHTML = html;
    } catch (error) {
        console.error('加载防火墙状态失败:', error);
    }
}

async function enableFirewall() {
    try {
        const response = await fetch('/api/network/firewall/enable', {method: 'POST'});
        const data = await response.json();
        showMessage(data.success ? '防火墙已启用' : '启用失败', data.success ? 'success' : 'error');
        if (data.success) loadFirewallStatus();
    } catch (error) {
        showMessage('启用失败: ' + error.message, 'error');
    }
}

async function disableFirewall() {
    if (!confirm('确定要禁用防火墙吗？这可能导致安全风险。')) return;
    
    try {
        const response = await fetch('/api/network/firewall/disable', {method: 'POST'});
        const data = await response.json();
        showMessage(data.success ? '防火墙已禁用' : '禁用失败', data.success ? 'success' : 'error');
        if (data.success) loadFirewallStatus();
    } catch (error) {
        showMessage('禁用失败: ' + error.message, 'error');
    }
}

function showAddFirewallRuleDialog() {
    const port = prompt('请输入端口号:');
    if (!port || isNaN(port)) return;
    
    const protocol = prompt('请输入协议 (tcp/udp):', 'tcp');
    if (!protocol) return;
    
    addFirewallRule(port, protocol);
}

async function addFirewallRule(port, protocol) {
    try {
        const response = await fetch('/api/network/firewall/rule/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({port, protocol, action: 'allow'})
        });
        
        const data = await response.json();
        showMessage(data.message || (data.success ? '规则已添加' : '添加失败'), data.success ? 'success' : 'error');
        if (data.success) loadFirewallStatus();
    } catch (error) {
        showMessage('添加失败: ' + error.message, 'error');
    }
}

// ========== 端口监听 ==========

async function loadListeningPorts() {
    try {
        const response = await fetch('/api/network/ports');
        const data = await response.json();
        
        if (data.success && data.ports.length > 0) {
            const html = `
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>协议</th>
                            <th>地址</th>
                            <th>端口</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.ports.map(port => `
                            <tr>
                                <td>${port.protocol}</td>
                                <td>${port.address}</td>
                                <td>${port.port}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            document.getElementById('listening-ports').innerHTML = html;
        } else {
            document.getElementById('listening-ports').innerHTML = '<p>暂无监听端口</p>';
        }
    } catch (error) {
        console.error('加载监听端口失败:', error);
    }
}

// ========== 网络连接监控 ==========

async function loadNetworkConnectionStats() {
    try {
        const response = await fetch('/api/network/connections');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            document.getElementById('network-connection-stats').innerHTML = `
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">ESTABLISHED</div>
                        <div class="info-value">${stats.established || 0}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">LISTEN</div>
                        <div class="info-value">${stats.listen || 0}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">TIME_WAIT</div>
                        <div class="info-value">${stats.time_wait || 0}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">CLOSE_WAIT</div>
                        <div class="info-value">${stats.close_wait || 0}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">总连接数</div>
                        <div class="info-value">${stats.total || 0}</div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载网络连接统计失败:', error);
    }
}

// ==================== 性能分析功能 ====================

let performanceRefreshInterval = null;

// 加载性能分析页面
function loadPerformancePage() {
    loadSystemLoadInfo();
    loadProcessList('cpu');
    loadDiskIOStats();
    
    // 启动自动刷新
    if (performanceRefreshInterval) {
        clearInterval(performanceRefreshInterval);
    }
    performanceRefreshInterval = setInterval(() => {
        loadSystemLoadInfo();
        loadProcessList(currentPerformanceTab);
        loadDiskIOStats();
    }, 3000);
}

// ========== 系统负载 ==========

async function loadSystemLoadInfo() {
    try {
        const response = await fetch('/api/performance/load');
        const data = await response.json();
        
        if (data.success) {
            const load = data.load;
            document.getElementById('system-load-info').innerHTML = `
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">1分钟负载</div>
                        <div class="info-value">${load.load_1min.toFixed(2)} (${load.load_1min_percent.toFixed(1)}%)</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">5分钟负载</div>
                        <div class="info-value">${load.load_5min.toFixed(2)} (${load.load_5min_percent.toFixed(1)}%)</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">15分钟负载</div>
                        <div class="info-value">${load.load_15min.toFixed(2)} (${load.load_15min_percent.toFixed(1)}%)</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">CPU核心数</div>
                        <div class="info-value">${load.cpu_count}</div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载系统负载失败:', error);
    }
}

// ========== 进程排行 ==========

function switchPerformanceTab(tab) {
    currentPerformanceTab = tab;
    
    // 更新按钮状态
    document.querySelectorAll('.tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    loadProcessList(tab);
}

async function loadProcessList(type) {
    try {
        const url = type === 'cpu' 
            ? '/api/performance/processes/cpu?limit=15'
            : '/api/performance/processes/memory?limit=15';
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success && data.processes.length > 0) {
            const html = `
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>PID</th>
                            <th>进程名</th>
                            <th>用户</th>
                            <th>${type === 'cpu' ? 'CPU%' : '内存%'}</th>
                            ${type === 'memory' ? '<th>内存(MB)</th>' : ''}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.processes.map(proc => `
                            <tr>
                                <td>${proc.pid}</td>
                                <td>${proc.name}</td>
                                <td>${proc.username}</td>
                                <td>${type === 'cpu' ? proc.cpu_percent.toFixed(1) : proc.memory_percent.toFixed(1)}%</td>
                                ${type === 'memory' ? `<td>${proc.memory_mb ? proc.memory_mb.toFixed(1) : 'N/A'}</td>` : ''}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            document.getElementById('performance-process-list').innerHTML = html;
        } else {
            document.getElementById('performance-process-list').innerHTML = '<p>暂无数据</p>';
        }
    } catch (error) {
        console.error('加载进程列表失败:', error);
    }
}

// ========== 磁盘I/O ==========

async function loadDiskIOStats() {
    try {
        const response = await fetch('/api/performance/disk/io');
        const data = await response.json();
        
        if (data.success && data.stats.length > 0) {
            const html = `
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>磁盘</th>
                            <th>读取速度</th>
                            <th>写入速度</th>
                            <th>读取次数</th>
                            <th>写入次数</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.stats.map(disk => `
                            <tr>
                                <td>${disk.disk}</td>
                                <td>${formatBytes(disk.read_speed)}/s</td>
                                <td>${formatBytes(disk.write_speed)}/s</td>
                                <td>${disk.read_count.toLocaleString()}</td>
                                <td>${disk.write_count.toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            document.getElementById('disk-io-stats').innerHTML = html;
        } else {
            document.getElementById('disk-io-stats').innerHTML = '<p>暂无数据</p>';
        }
    } catch (error) {
        console.error('加载磁盘IO失败:', error);
    }
}

// ========== 网络连接详情 ==========

async function loadNetworkConnections() {
    try {
        const response = await fetch('/api/performance/network/connections');
        const data = await response.json();
        
        if (data.success && data.connections.length > 0) {
            const html = `
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>协议</th>
                            <th>本地地址</th>
                            <th>远程地址</th>
                            <th>状态</th>
                            <th>进程</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.connections.slice(0, 100).map(conn => `
                            <tr>
                                <td>${conn.protocol}</td>
                                <td>${conn.local_address}</td>
                                <td>${conn.remote_address || '-'}</td>
                                <td>${conn.status || '-'}</td>
                                <td>${conn.process || '-'} ${conn.pid ? `(${conn.pid})` : ''}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                ${data.connections.length > 100 ? `<p>仅显示前100个连接，共${data.connections.length}个</p>` : ''}
            `;
            document.getElementById('network-connections-detailed').innerHTML = html;
        } else {
            document.getElementById('network-connections-detailed').innerHTML = '<p>暂无连接</p>';
        }
    } catch (error) {
        console.error('加载网络连接失败:', error);
    }
}
