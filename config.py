import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pi-panel-secret-key-change-in-production'
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 默认用户凭据
    DEFAULT_USERNAME = 'admin'
    DEFAULT_PASSWORD = 'pi-panel'
    
    # 文件管理
    FILE_ROOT = '/'
    PANEL_USERS_FILE = os.path.join(BASE_DIR, 'data', 'panel_users.json')
    AUDIT_LOG_FILE = os.path.join(BASE_DIR, 'data', 'audit_log.jsonl')
    UPLOAD_FOLDER = '/tmp/uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # WebSocket
    SOCKETIO_ASYNC_MODE = 'threading'
    
    # 会话
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1小时
