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
from history_data import HistoryData

app = Flask(__name__)
app.config.from_object(Config)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

file_manager = FileManager(Config.FILE_ROOT)
history_data = HistoryData()

# 告警阈值配置
ALERT_THRESHOLDS = {
    'cpu': 90,  # CPU使用率 > 90%
    'memory': 85,  # 内存使用率 > 85%
    'disk': 90,  # 磁盘使用率 > 90%
    'temperature': 80  # 温度 > 80°C
}

# 存储终端会话
terminals = {}

# 后台任务：定期记录历史数据
def background_data_recorder():
    """后台任务：每分钟记录一次系统数据"""
    import time
    # 启动时立即记录一次
    try:
        system_info = SystemInfo.get_all()
        history_data.add_record(system_info)
        history_data.save_data()
    except Exception as e:
        print(f"初始记录历史数据失败: {e}")
    
    while True:
        try:
            time.sleep(60)  # 每60秒记录一次
            system_info = SystemInfo.get_all()
            history_data.add_record(system_info)
            history_data.save_data()
        except Exception as e:
            print(f"记录历史数据失败: {e}")

# 启动后台任务
def start_background_tasks():
    recorder_thread = threading.Thread(target=background_data_recorder, daemon=True)
    recorder_thread.start()

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

@app.route('/api/history/<metric>')
@login_required
def get_history(metric):
    duration = request.args.get('duration', '1h')
    records = history_data.get_records(metric, duration)
    return jsonify({'success': True, 'data': records})

@app.route('/api/history/statistics')
@login_required
def get_statistics():
    duration = request.args.get('duration', '24h')
    stats = history_data.get_all_statistics(duration)
    return jsonify({'success': True, 'statistics': stats})

@app.route('/api/alerts/check')
@login_required
def check_alerts():
    """检查是否有告警"""
    system_info = SystemInfo.get_all()
    alerts = []
    
    # 检查CPU
    cpu_percent = system_info.get('cpu', {}).get('percent', 0)
    if cpu_percent > ALERT_THRESHOLDS['cpu']:
        alerts.append({
            'type': 'cpu',
            'level': 'warning',
            'message': f'CPU使用率过高: {cpu_percent}%'
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
    
    # 检查温度
    temperature = system_info.get('temperature', 0)
    if temperature > ALERT_THRESHOLDS['temperature']:
        alerts.append({
            'type': 'temperature',
            'level': 'warning',
            'message': f'温度过高: {temperature}°C'
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
        # 执行 git pull
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': '更新成功！请重启服务使更改生效。',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr or result.stdout
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
        
        set_winsize(fd, data.get('rows', 24), data.get('cols', 80))
        
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
        set_winsize(fd, data['rows'], data['cols'])

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
    start_background_tasks()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
