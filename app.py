from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import pty
import subprocess
import select
import termios
import struct
import fcntl
import shlex
import threading

from config import Config
from auth import User
from system_info import SystemInfo
from file_manager import FileManager
from service_manager import ServiceManager
from system_control import SystemControl
from docker_manager import DockerManager
from apt_manager import AptManager
from user_manager import UserManager
from network_manager import NetworkManager
from performance import PerformanceAnalyzer

app = Flask(__name__)
app.config.from_object(Config)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 处理API请求的未授权情况
@login_manager.unauthorized_handler
def unauthorized():
    # 如果是API请求，返回JSON而不是重定向
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': '未授权，请先登录'}), 401
    # 其他请求重定向到登录页面
    return redirect(url_for('login'))

file_manager = FileManager(Config.FILE_ROOT)

# 告警阈值配置
ALERT_THRESHOLDS = {
    'cpu': 90,  # CPU使用率 > 90%
    'memory': 85,  # 内存使用率 > 85%
    'disk': 90,  # 磁盘使用率 > 90%
    'temperature': 80  # 温度 > 80°C
}

# 存储终端会话
terminals = {}

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ============ 认证路由 ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.verify(username, password)
        if user:
            login_user(user)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ============ 主页面路由 ============

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# SPA 路由：所有前端页面路径均返回主页面（支持直接访问和浏览器刷新）
@app.route('/home')
@app.route('/services')
@app.route('/docker')
@app.route('/packages')
@app.route('/users')
@app.route('/control')
@app.route('/network')
@app.route('/performance')
@app.route('/terminal')
@app.route('/files')
@app.route('/settings')
@login_required
def spa_page():
    return render_template('index.html')

# ============ 系统信息API ============
@app.route('/api/system/info')
@login_required
def get_system_info():
    return jsonify(SystemInfo.get_all())

@app.route('/api/system/cpu')
@login_required
def get_cpu_info():
    return jsonify(SystemInfo.get_cpu_info())

@app.route('/api/system/memory')
@login_required
def get_memory_info():
    return jsonify(SystemInfo.get_memory_info())

@app.route('/api/system/disk')
@login_required
def get_disk_info():
    return jsonify(SystemInfo.get_disk_info())

@app.route('/api/system/temperature')
@login_required
def get_temperature():
    return jsonify(SystemInfo.get_temperature())

@app.route('/api/system/network')
@login_required
def get_network_info():
    return jsonify(SystemInfo.get_network_info())

# ============ 系统控制API ============

@app.route('/api/control/reboot', methods=['POST'])
@login_required
def reboot_system():
    return jsonify(SystemControl.reboot_system())

@app.route('/api/control/shutdown', methods=['POST'])
@login_required
def shutdown_system():
    return jsonify(SystemControl.shutdown_system())

@app.route('/api/control/uptime')
@login_required
def get_uptime():
    return jsonify(SystemControl.get_uptime())

@app.route('/api/control/logs')
@login_required
def get_logs():
    lines = request.args.get('lines', 100, type=int)
    service = request.args.get('service', None)
    return jsonify(SystemControl.get_system_logs(lines, service))

@app.route('/api/control/processes')
@login_required
def get_processes():
    return jsonify(SystemControl.get_processes())

@app.route('/api/control/processes/<int:pid>', methods=['DELETE'])
@login_required
def kill_process(pid):
    return jsonify(SystemControl.kill_process(pid))

# ============ 历史数据API ============

@app.route('/api/alerts/check')
@login_required
def check_alerts():
    """检查是否有告警"""
    system_info = SystemInfo.get_all()
    alerts = []
    
    # 检查CPU - 处理 percpu=True 返回的列表
    cpu_data = system_info.get('cpu', {}).get('percent', [])
    if isinstance(cpu_data, list):
        cpu_percent = sum(cpu_data) / len(cpu_data) if cpu_data else 0
    else:
        cpu_percent = cpu_data
    
    if cpu_percent > ALERT_THRESHOLDS['cpu']:
        alerts.append({
            'type': 'cpu',
            'level': 'warning',
            'message': f'CPU使用率过高: {cpu_percent:.1f}%'
        })
    
    # 检查内存
    memory_percent = system_info.get('memory', {}).get('percent', 0)
    if memory_percent > ALERT_THRESHOLDS['memory']:
        alerts.append({
            'type': 'memory',
            'level': 'warning',
            'message': f'内存使用率过高: {memory_percent}%'
        })
    
    # 检查磁盘
    disk_info = system_info.get('disk', [])
    for disk in disk_info:
        if disk.get('percent', 0) > ALERT_THRESHOLDS['disk']:
            alerts.append({
                'type': 'disk',
                'level': 'warning',
                'message': f'磁盘 {disk.get("mount")} 使用率过高: {disk.get("percent")}%'
            })
    
    # 检查温度 - 温度是字典，需要遍历所有传感器
    temperature_data = system_info.get('temperature', {})
    if isinstance(temperature_data, dict):
        for sensor_name, temp_value in temperature_data.items():
            if temp_value > ALERT_THRESHOLDS['temperature']:
                alerts.append({
                    'type': 'temperature',
                    'level': 'warning',
                    'message': f'{sensor_name} 温度过高: {temp_value:.1f}°C'
                })
    elif isinstance(temperature_data, (int, float)):
        # 兼容单个温度值的情况
        if temperature_data > ALERT_THRESHOLDS['temperature']:
            alerts.append({
                'type': 'temperature',
                'level': 'warning',
                'message': f'温度过高: {temperature_data:.1f}°C'
            })
    
    return jsonify({'success': True, 'alerts': alerts})

# ============ 系统更新API ============

@app.route('/api/update/check', methods=['GET'])
@login_required
def check_update():
    """检查是否有更新"""
    try:
        # 获取远程版本信息
        result = subprocess.run(
            ['git', 'fetch', 'origin', 'main'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # 比较本地和远程版本
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD..origin/main'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        commits_behind = int(result.stdout.strip()) if result.stdout.strip() else 0
        
        # 获取当前版本信息
        current_result = subprocess.run(
            ['git', 'log', '-1', '--format=%H %s'],
            capture_output=True,
            text=True,
            timeout=5
        )
        current_version = current_result.stdout.strip()
        
        return jsonify({
            'success': True,
            'has_update': commits_behind > 0,
            'commits_behind': commits_behind,
            'current_version': current_version
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update/pull', methods=['POST'])
@login_required
def pull_update():
    """执行更新"""
    try:
        cwd = os.path.dirname(os.path.abspath(__file__))
        
        # 1. 先 stash 本地修改
        stash_result = subprocess.run(
            ['git', 'stash'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd
        )
        
        # 2. 执行 git pull
        pull_result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd
        )
        
        # 3. 恢复 stash（如果有的话）
        if 'No local changes to save' not in stash_result.stdout:
            stash_pop_result = subprocess.run(
                ['git', 'stash', 'pop'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd
            )
            
            # 检查是否有冲突
            if stash_pop_result.returncode != 0:
                return jsonify({
                    'success': True,
                    'message': '更新成功！但本地修改可能有冲突，请检查。',
                    'output': pull_result.stdout,
                    'warning': stash_pop_result.stderr
                })
        
        if pull_result.returncode == 0:
            return jsonify({
                'success': True,
                'message': '更新成功！请重启服务使更改生效。',
                'output': pull_result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': pull_result.stderr or pull_result.stdout
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update/force', methods=['POST'])
@login_required
def force_update():
    """强制更新（丢弃本地修改）"""
    try:
        cwd = os.path.dirname(os.path.abspath(__file__))
        
        # 1. 重置所有本地修改
        reset_result = subprocess.run(
            ['git', 'reset', '--hard', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd
        )
        
        # 2. 清理未跟踪的文件
        clean_result = subprocess.run(
            ['git', 'clean', '-fd'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd
        )
        
        # 3. 拉取最新代码
        pull_result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd
        )
        
        if pull_result.returncode == 0:
            return jsonify({
                'success': True,
                'message': '强制更新成功！本地修改已丢弃。请重启服务。',
                'output': pull_result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': pull_result.stderr or pull_result.stdout
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update/restart', methods=['POST'])
@login_required
def restart_app():
    """重启应用"""
    try:
        # 使用 systemctl 重启（如果配置了服务）
        result = subprocess.run(
            ['sudo', 'systemctl', 'restart', 'pi-panel'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': '正在重启服务...'})
        else:
            # 如果没有配置 systemd 服务，提示手动重启
            return jsonify({
                'success': False,
                'error': '未配置 systemd 服务，请手动重启应用',
                'manual': True
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '请手动重启应用: sudo systemctl restart pi-panel 或 重新运行 python app.py',
            'manual': True
        })

# ============ 服务管理API ============

@app.route('/api/services')
@login_required
def list_services():
    return jsonify(ServiceManager.list_services())

@app.route('/api/services/<service_name>/status')
@login_required
def get_service_status(service_name):
    return jsonify(ServiceManager.get_service_status(service_name))

@app.route('/api/services/<service_name>/<action>', methods=['POST'])
@login_required
def control_service(service_name, action):
    return jsonify(ServiceManager.control_service(service_name, action))

# ============ 网络管理API ============

@app.route('/api/network/wifi/scan')
@login_required
def scan_wifi():
    """扫描WiFi网络"""
    return jsonify(NetworkManager.scan_wifi())

@app.route('/api/network/wifi/connect', methods=['POST'])
@login_required
def connect_wifi():
    """连接WiFi"""
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')
    return jsonify(NetworkManager.connect_wifi(ssid, password))

@app.route('/api/network/wifi/disconnect', methods=['POST'])
@login_required
def disconnect_wifi():
    """断开WiFi"""
    return jsonify(NetworkManager.disconnect_wifi())

@app.route('/api/network/interfaces')
@login_required
def get_network_interfaces():
    """获取网络接口"""
    return jsonify(NetworkManager.get_network_interfaces())

@app.route('/api/network/interfaces/static', methods=['POST'])
@login_required
def set_static_ip():
    """设置静态IP"""
    data = request.json
    return jsonify(NetworkManager.set_static_ip(
        data.get('interface'),
        data.get('ip'),
        data.get('netmask'),
        data.get('gateway'),
        data.get('dns')
    ))

@app.route('/api/network/interfaces/dhcp', methods=['POST'])
@login_required
def set_dhcp():
    """设置DHCP"""
    data = request.json
    return jsonify(NetworkManager.set_dhcp(data.get('interface')))

@app.route('/api/network/firewall/status')
@login_required
def get_firewall_status():
    """获取防火墙状态"""
    return jsonify(NetworkManager.get_firewall_status())

@app.route('/api/network/firewall/enable', methods=['POST'])
@login_required
def enable_firewall():
    """启用防火墙"""
    return jsonify(NetworkManager.enable_firewall())

@app.route('/api/network/firewall/disable', methods=['POST'])
@login_required
def disable_firewall():
    """禁用防火墙"""
    return jsonify(NetworkManager.disable_firewall())

@app.route('/api/network/firewall/rules', methods=['POST'])
@login_required
def add_firewall_rule():
    """添加防火墙规则"""
    data = request.json
    return jsonify(NetworkManager.add_firewall_rule(
        data.get('port'),
        data.get('protocol', 'tcp'),
        data.get('action', 'allow')
    ))

@app.route('/api/network/firewall/rules/<int:rule_number>', methods=['DELETE'])
@login_required
def delete_firewall_rule(rule_number):
    """删除防火墙规则"""
    return jsonify(NetworkManager.delete_firewall_rule(rule_number))

@app.route('/api/network/ports')
@login_required
def get_listening_ports():
    """获取监听端口"""
    return jsonify(NetworkManager.get_listening_ports())

@app.route('/api/network/connections')
@login_required
def get_network_connections():
    """获取网络连接"""
    return jsonify(NetworkManager.get_network_connections())

# ============ 性能分析API ============

@app.route('/api/performance/processes')
@login_required
def get_top_processes():
    """获取资源占用排行"""
    limit = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort', 'cpu')
    return jsonify(PerformanceAnalyzer.get_top_processes(limit, sort_by))

@app.route('/api/performance/disk-io')
@login_required
def get_disk_io():
    """获取磁盘I/O统计"""
    return jsonify(PerformanceAnalyzer.get_disk_io())

@app.route('/api/performance/disk-io/rate')
@login_required
def get_disk_io_rate():
    """获取磁盘I/O速率"""
    return jsonify(PerformanceAnalyzer.get_disk_io_rate())

@app.route('/api/performance/load')
@login_required
def get_system_load():
    """获取系统负载"""
    return jsonify(PerformanceAnalyzer.get_system_load())

@app.route('/api/performance/connections')
@login_required
def get_connection_stats():
    """获取网络连接统计"""
    return jsonify(PerformanceAnalyzer.get_network_connections_stats())

@app.route('/api/performance/cpu-cores')
@login_required
def get_cpu_cores():
    """获取每个CPU核心使用率"""
    return jsonify(PerformanceAnalyzer.get_cpu_per_core())

@app.route('/api/performance/memory')
@login_required
def get_memory_details():
    """获取详细内存信息"""
    return jsonify(PerformanceAnalyzer.get_memory_details())

@app.route('/api/performance/network-io')
@login_required
def get_network_io():
    """获取网络I/O统计"""
    return jsonify(PerformanceAnalyzer.get_network_io())

# ============ Docker 管理API ============

@app.route('/api/docker/check')
@login_required
def check_docker():
    """检查 Docker 是否已安装"""
    return jsonify({'installed': DockerManager.is_docker_installed()})

@app.route('/api/docker/info')
@login_required
def get_docker_info():
    """获取 Docker 系统信息"""
    return jsonify(DockerManager.get_docker_info())

@app.route('/api/docker/containers')
@login_required
def get_containers():
    """获取容器列表"""
    all_containers = request.args.get('all', 'true').lower() == 'true'
    return jsonify(DockerManager.get_containers(all_containers))

@app.route('/api/docker/containers/<container_id>/logs')
@login_required
def get_container_logs_api(container_id):
    """获取容器日志"""
    lines = request.args.get('lines', 100, type=int)
    return jsonify(DockerManager.get_container_logs(container_id, lines))

@app.route('/api/docker/containers/<container_id>/stats')
@login_required
def get_container_stats_api(container_id):
    """获取容器资源统计"""
    return jsonify(DockerManager.get_container_stats(container_id))

@app.route('/api/docker/containers/<container_id>/<action>', methods=['POST'])
@login_required
def control_container_api(container_id, action):
    """控制容器"""
    return jsonify(DockerManager.control_container(container_id, action))

@app.route('/api/docker/images')
@login_required
def get_images_api():
    """获取镜像列表"""
    return jsonify(DockerManager.get_images())

@app.route('/api/docker/images/<path:image_id>', methods=['DELETE'])
@login_required
def remove_image_api(image_id):
    """删除镜像"""
    return jsonify(DockerManager.remove_image(image_id))

@app.route('/api/docker/images/pull', methods=['POST'])
@login_required
def pull_image_api():
    """拉取镜像"""
    data = request.get_json()
    image_name = data.get('image')
    if not image_name:
        return jsonify({'success': False, 'error': '镜像名称不能为空'})
    return jsonify(DockerManager.pull_image(image_name))

@app.route('/api/docker/system/prune', methods=['POST'])
@login_required
def prune_system_api():
    """清理 Docker 系统"""
    return jsonify(DockerManager.prune_system())

# ============ APT 包管理API ============

@app.route('/api/apt/update', methods=['POST'])
@login_required
def apt_update():
    """更新软件包列表"""
    return jsonify(AptManager.update_package_list())

@app.route('/api/apt/upgrade', methods=['POST'])
@login_required
def apt_upgrade():
    """升级所有软件包"""
    return jsonify(AptManager.upgrade_packages())

@app.route('/api/apt/install', methods=['POST'])
@login_required
def apt_install():
    """安装软件包"""
    data = request.get_json()
    package = data.get('package')
    if not package:
        return jsonify({'success': False, 'error': '未指定软件包名称'}), 400
    return jsonify(AptManager.install_package(package))

@app.route('/api/apt/remove', methods=['POST'])
@login_required
def apt_remove():
    """卸载软件包"""
    data = request.get_json()
    package = data.get('package')
    purge = data.get('purge', False)
    if not package:
        return jsonify({'success': False, 'error': '未指定软件包名称'}), 400
    return jsonify(AptManager.remove_package(package, purge))

@app.route('/api/apt/search')
@login_required
def apt_search():
    """搜索软件包"""
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', 50, type=int)
    if not keyword:
        return jsonify({'success': False, 'error': '未指定搜索关键词'}), 400
    return jsonify(AptManager.search_packages(keyword, limit))

@app.route('/api/apt/installed')
@login_required
def apt_installed():
    """列出已安装的软件包"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(AptManager.list_installed_packages(limit))

@app.route('/api/apt/info')
@login_required
def apt_info():
    """获取软件包详细信息"""
    package = request.args.get('package')
    if not package:
        return jsonify({'success': False, 'error': '未指定软件包名称'}), 400
    return jsonify(AptManager.get_package_info(package))

@app.route('/api/apt/upgradable')
@login_required
def apt_upgradable():
    """列出可更新的软件包"""
    return jsonify(AptManager.list_upgradable())

@app.route('/api/apt/clean', methods=['POST'])
@login_required
def apt_clean():
    """清理缓存"""
    return jsonify(AptManager.clean_cache())

@app.route('/api/apt/autoremove', methods=['POST'])
@login_required
def apt_autoremove():
    """自动移除不需要的软件包"""
    return jsonify(AptManager.autoremove())

# ============ 用户管理API ============

@app.route('/api/users/list')
@login_required
def list_users():
    """列出所有用户"""
    include_system = request.args.get('include_system', 'false').lower() == 'true'
    return jsonify(UserManager.list_users(include_system))

@app.route('/api/users/add', methods=['POST'])
@login_required
def add_user():
    """添加用户"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    groups = data.get('groups', [])
    create_home = data.get('create_home', True)
    
    if not username or not password:
        return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
    
    return jsonify(UserManager.add_user(username, password, groups, create_home))

@app.route('/api/users/delete', methods=['POST'])
@login_required
def delete_user():
    """删除用户"""
    data = request.get_json()
    username = data.get('username')
    remove_home = data.get('remove_home', False)
    
    if not username:
        return jsonify({'success': False, 'error': '未指定用户名'}), 400
    
    return jsonify(UserManager.delete_user(username, remove_home))

@app.route('/api/users/password', methods=['POST'])
@login_required
def change_user_password():
    """修改用户密码"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
    
    return jsonify(UserManager.change_password(username, password))

@app.route('/api/users/groups')
@login_required
def list_groups():
    """列出所有用户组"""
    return jsonify(UserManager.list_groups())

@app.route('/api/users/group/add', methods=['POST'])
@login_required
def add_to_group():
    """添加用户到组"""
    data = request.get_json()
    username = data.get('username')
    group = data.get('group')
    
    if not username or not group:
        return jsonify({'success': False, 'error': '用户名和组名不能为空'}), 400
    
    return jsonify(UserManager.add_user_to_group(username, group))

@app.route('/api/users/group/remove', methods=['POST'])
@login_required
def remove_from_group():
    """从组中移除用户"""
    data = request.get_json()
    username = data.get('username')
    group = data.get('group')
    
    if not username or not group:
        return jsonify({'success': False, 'error': '用户名和组名不能为空'}), 400
    
    return jsonify(UserManager.remove_user_from_group(username, group))

@app.route('/api/users/logged')
@login_required
def logged_in_users():
    """获取当前登录的用户"""
    return jsonify(UserManager.get_logged_in_users())

@app.route('/api/users/sudo', methods=['POST'])
@login_required
def set_sudo():
    """设置 sudo 权限"""
    data = request.get_json()
    username = data.get('username')
    enable = data.get('enable', True)
    
    if not username:
        return jsonify({'success': False, 'error': '未指定用户名'}), 400
    
    return jsonify(UserManager.set_sudo_privilege(username, enable))

@app.route('/api/users/lock', methods=['POST'])
@login_required
def lock_user():
    """锁定用户"""
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'success': False, 'error': '未指定用户名'}), 400
    
    return jsonify(UserManager.lock_user(username))

@app.route('/api/users/unlock', methods=['POST'])
@login_required
def unlock_user():
    """解锁用户"""
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'success': False, 'error': '未指定用户名'}), 400
    
    return jsonify(UserManager.unlock_user(username))

# ============ 文件管理API ============

@app.route('/api/files/list')
@login_required
def list_files():
    path = request.args.get('path', '/')
    return jsonify(file_manager.list_directory(path))

@app.route('/api/files/read')
@login_required
def read_file():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': '未指定文件路径'}), 400
    return jsonify(file_manager.read_file(path))

@app.route('/api/files/write', methods=['POST'])
@login_required
def write_file():
    data = request.get_json()
    path = data.get('path')
    content = data.get('content')
    
    if not path:
        return jsonify({'error': '未指定文件路径'}), 400
    
    return jsonify(file_manager.write_file(path, content))

@app.route('/api/files/delete', methods=['POST'])
@login_required
def delete_file():
    data = request.get_json()
    path = data.get('path')
    
    if not path:
        return jsonify({'error': '未指定路径'}), 400
    
    return jsonify(file_manager.delete_file(path))

@app.route('/api/files/mkdir', methods=['POST'])
@login_required
def create_directory():
    data = request.get_json()
    path = data.get('path')
    
    if not path:
        return jsonify({'error': '未指定路径'}), 400
    
    return jsonify(file_manager.create_directory(path))

@app.route('/api/files/download')
@login_required
def download_file():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': '未指定文件路径'}), 400
    
    file_path = file_manager.get_file_path(path)
    if file_path:
        return send_file(file_path, as_attachment=True)
    
    return jsonify({'error': '文件不存在'}), 404

@app.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400
    
    file = request.files['file']
    path = request.form.get('path', '/')
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    target_path = os.path.join(path, file.filename)
    result = file_manager.write_file(target_path, file.read().decode('utf-8', errors='ignore'))
    
    return jsonify(result)

# ============ WebSocket 终端 ============

def set_winsize(fd, row, col, xpix=0, ypix=0):
    """设置终端窗口大小 - 确保所有参数都是整数"""
    # 转换为整数，防止 struct.pack 类型错误
    row = int(row) if row else 24
    col = int(col) if col else 80
    xpix = int(xpix) if xpix else 0
    ypix = int(ypix) if ypix else 0
    
    winsize = struct.pack("HHHH", row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

def read_and_forward_pty_output(fd, sid):
    max_read_bytes = 1024 * 20
    while True:
        import time
        time.sleep(0.01)
        if sid not in terminals:
            break
        if fd != terminals[sid]['fd']:
            break
        
        timeout_sec = 0
        (data_ready, _, _) = select.select([fd], [], [], timeout_sec)
        if data_ready:
            try:
                output = os.read(fd, max_read_bytes).decode('utf-8', errors='ignore')
                socketio.emit('terminal_output', {'output': output}, room=sid, namespace='/terminal')
            except OSError:
                break

@socketio.on('connect', namespace='/terminal')
def terminal_connect():
    if not current_user.is_authenticated:
        return False

@socketio.on('start_terminal', namespace='/terminal')
def start_terminal(data):
    if not current_user.is_authenticated:
        return
    
    sid = request.sid
    
    if sid in terminals:
        return
    
    (child_pid, fd) = pty.fork()
    
    if child_pid == 0:
        # 子进程 - 启动 shell
        # 尝试多个 shell，按优先级
        shells = ['/bin/bash', '/bin/sh', 'bash', 'sh']
        for shell in shells:
            try:
                os.execvp(shell, [shell])
            except FileNotFoundError:
                continue
        # 如果所有 shell 都失败，退出
        os._exit(1)
    else:
        # 父进程
        terminals[sid] = {
            'pid': child_pid,
            'fd': fd
        }
        
        # 确保 rows 和 cols 是整数
        rows = int(data.get('rows') or 24)
        cols = int(data.get('cols') or 80)
        set_winsize(fd, rows, cols)
        
        # 使用 threading 模块启动后台任务
        thread = threading.Thread(target=read_and_forward_pty_output, args=(fd, sid))
        thread.daemon = True
        thread.start()
        
        emit('terminal_ready', {'status': 'ready'})

@socketio.on('terminal_input', namespace='/terminal')
def terminal_input(data):
    if not current_user.is_authenticated:
        return
    
    sid = request.sid
    
    if sid in terminals:
        fd = terminals[sid]['fd']
        try:
            os.write(fd, data['input'].encode())
        except OSError:
            pass

@socketio.on('terminal_resize', namespace='/terminal')
def terminal_resize(data):
    if not current_user.is_authenticated:
        return
    
    sid = request.sid
    
    if sid in terminals:
        fd = terminals[sid]['fd']
        # 确保 rows 和 cols 是整数
        rows = int(data.get('rows') or 24)
        cols = int(data.get('cols') or 80)
        set_winsize(fd, rows, cols)

@socketio.on('disconnect', namespace='/terminal')
def terminal_disconnect():
    sid = request.sid
    
    if sid in terminals:
        try:
            os.close(terminals[sid]['fd'])
            os.kill(terminals[sid]['pid'], 9)
        except:
            pass
        del terminals[sid]

if __name__ == '__main__':
    os.makedirs('sessions', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
