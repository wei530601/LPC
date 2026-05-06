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

app = Flask(__name__)
app.config.from_object(Config)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

file_manager = FileManager(Config.FILE_ROOT)

# 存储终端会话
terminals = {}
terminal_locks = {}

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
    """读取 pty 输出并通过 WebSocket 转发"""
    max_read_bytes = 1024 * 20
    while True:
        try:
            # 检查终端是否还存在
            if sid not in terminals:
                break
            
            # 使用 select 检查是否有数据可读
            timeout_sec = 0.1
            (data_ready, _, _) = select.select([fd], [], [], timeout_sec)
            
            if data_ready:
                output = os.read(fd, max_read_bytes).decode('utf-8', errors='ignore')
                if output:
                    socketio.emit('terminal_output', {'output': output}, room=sid, namespace='/terminal')
        except (OSError, ValueError):
            # 文件描述符关闭或出错
            break
        except Exception as e:
            print(f"Terminal read error: {e}")
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
    
    try:
        (child_pid, fd) = pty.fork()
        
        if child_pid == 0:
            # 子进程 - 执行 bash
            subprocess.run(['bash', '-i'])
            os._exit(0)
        else:
            # 父进程
            terminals[sid] = {
                'pid': child_pid,
                'fd': fd
            }
            
            # 设置终端大小
            set_winsize(fd, data.get('rows', 24), data.get('cols', 80))
            
            # 使用 threading.Thread 启动读取线程
            reader_thread = threading.Thread(
                target=read_and_forward_pty_output,
                args=(fd, sid),
                daemon=True
            )
            reader_thread.start()
            
            emit('terminal_ready', {'status': 'ready'})
    except Exception as e:
        print(f"Failed to start terminal: {e}")
        emit('terminal_error', {'error': str(e)})

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
            # 关闭文件描述符
            os.close(terminals[sid]['fd'])
        except:
            pass
        
        try:
            # 终止子进程
            os.kill(terminals[sid]['pid'], 9)
        except:
            pass
        
        # 从字典中删除
        del terminals[sid]

if __name__ == '__main__':
    os.makedirs('sessions', exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
