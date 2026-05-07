import json
import os
import re
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config


class PanelUserStore:
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,32}$')
    PERMISSION_DEFAULTS = {
        'files.read': False,
        'files.write': False,
        'files.delete': False,
        'files.upload': False,
        'files.download': False,
        'files.rename': False,
        'terminal.access': False,
        'panel_users.manage': False,
        'audit.read': False,
    }
    PERMISSION_LABELS = {
        'files.read': '文件浏览',
        'files.write': '文件写入/新建',
        'files.delete': '文件删除',
        'files.upload': '文件上传',
        'files.download': '文件下载',
        'files.rename': '文件重命名',
        'terminal.access': '终端访问',
        'panel_users.manage': '面板用户管理',
        'audit.read': '审计日志查看',
    }

    @classmethod
    def permission_definition_list(cls):
        return [
            {'key': key, 'label': cls.PERMISSION_LABELS.get(key, key)}
            for key in cls.PERMISSION_DEFAULTS.keys()
        ]

    @classmethod
    def build_permissions(cls, is_admin=False, permissions=None):
        if bool(is_admin):
            return {key: True for key in cls.PERMISSION_DEFAULTS.keys()}

        normalized = dict(cls.PERMISSION_DEFAULTS)
        if isinstance(permissions, dict):
            for key in normalized.keys():
                if key in permissions:
                    normalized[key] = bool(permissions.get(key))
        return normalized

    @classmethod
    def _default_data(cls):
        return {
            'version': 1,
            'users': [
                {
                    'username': Config.DEFAULT_USERNAME,
                    'password_hash': generate_password_hash(Config.DEFAULT_PASSWORD),
                    'is_admin': True,
                    'permissions': cls.build_permissions(is_admin=True),
                    'created_at': datetime.utcnow().isoformat()
                }
            ]
        }

    @classmethod
    def _ensure_store(cls):
        path = Config.PANEL_USERS_FILE
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if not os.path.exists(path):
            cls._write_data(cls._default_data())
            return

        data = cls._read_data()
        if not data.get('users'):
            cls._write_data(cls._default_data())

    @classmethod
    def _read_data(cls):
        cls._ensure_parent_dir()
        try:
            with open(Config.PANEL_USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {'version': 1, 'users': []}
            if 'users' not in data or not isinstance(data['users'], list):
                data['users'] = []
            if 'version' not in data:
                data['version'] = 1
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {'version': 1, 'users': []}

    @classmethod
    def _ensure_parent_dir(cls):
        parent = os.path.dirname(Config.PANEL_USERS_FILE)
        if parent:
            os.makedirs(parent, exist_ok=True)

    @classmethod
    def _write_data(cls, data):
        cls._ensure_parent_dir()
        tmp_path = Config.PANEL_USERS_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=True, indent=2)
        os.replace(tmp_path, Config.PANEL_USERS_FILE)

    @classmethod
    def _find_user(cls, username):
        data = cls._read_data()
        for user in data['users']:
            if user.get('username') == username:
                return user
        return None

    @classmethod
    def validate_username(cls, username):
        return bool(username and cls.USERNAME_PATTERN.match(username))

    @classmethod
    def list_users(cls):
        cls._ensure_store()
        data = cls._read_data()
        users = []
        for user in data['users']:
            users.append({
                'username': user.get('username'),
                'is_admin': bool(user.get('is_admin', False)),
                'permissions': cls.build_permissions(
                    is_admin=bool(user.get('is_admin', False)),
                    permissions=user.get('permissions', {})
                ),
                'created_at': user.get('created_at', '')
            })
        users.sort(key=lambda x: x['username'])
        return users

    @classmethod
    def exists(cls, username):
        cls._ensure_store()
        return cls._find_user(username) is not None

    @classmethod
    def get_user(cls, username):
        cls._ensure_store()
        return cls._find_user(username)

    @classmethod
    def verify_password(cls, username, password):
        cls._ensure_store()
        user = cls._find_user(username)
        if not user:
            return False
        password_hash = user.get('password_hash', '')
        if not password_hash:
            return False
        return check_password_hash(password_hash, password)

    @classmethod
    def add_user(cls, username, password, is_admin=False):
        cls._ensure_store()
        if not cls.validate_username(username):
            return {'success': False, 'error': '用户名需为3-32位字母、数字或下划线'}
        if len(password or '') < 6:
            return {'success': False, 'error': '密码长度至少6位'}

        data = cls._read_data()
        if any(u.get('username') == username for u in data['users']):
            return {'success': False, 'error': '用户名已存在'}

        data['users'].append({
            'username': username,
            'password_hash': generate_password_hash(password),
            'is_admin': bool(is_admin),
            'permissions': cls.build_permissions(is_admin=bool(is_admin)),
            'created_at': datetime.utcnow().isoformat()
        })
        cls._write_data(data)
        return {'success': True}

    @classmethod
    def delete_user(cls, username):
        cls._ensure_store()
        data = cls._read_data()
        users = data['users']

        target = None
        for user in users:
            if user.get('username') == username:
                target = user
                break

        if not target:
            return {'success': False, 'error': '用户不存在'}

        admin_count = sum(1 for u in users if u.get('is_admin'))
        if target.get('is_admin') and admin_count <= 1:
            return {'success': False, 'error': '至少需要保留一个管理员账号'}

        data['users'] = [u for u in users if u.get('username') != username]
        cls._write_data(data)
        return {'success': True}

    @classmethod
    def set_password(cls, username, password):
        cls._ensure_store()
        if len(password or '') < 6:
            return {'success': False, 'error': '密码长度至少6位'}

        data = cls._read_data()
        for user in data['users']:
            if user.get('username') == username:
                user['password_hash'] = generate_password_hash(password)
                cls._write_data(data)
                return {'success': True}
        return {'success': False, 'error': '用户不存在'}

    @classmethod
    def set_permissions(cls, username, permissions):
        cls._ensure_store()
        data = cls._read_data()

        for user in data['users']:
            if user.get('username') == username:
                user['permissions'] = cls.build_permissions(
                    is_admin=bool(user.get('is_admin', False)),
                    permissions=permissions if isinstance(permissions, dict) else {}
                )
                cls._write_data(data)
                return {'success': True}
        return {'success': False, 'error': '用户不存在'}


class User(UserMixin):
    def __init__(self, username, is_admin=False, permissions=None):
        self.id = username
        self.username = username
        self.is_admin = bool(is_admin)
        self.permissions = PanelUserStore.build_permissions(
            is_admin=self.is_admin,
            permissions=permissions if isinstance(permissions, dict) else {}
        )

    def has_permission(self, key):
        if self.is_admin:
            return True
        return bool(self.permissions.get(key, False))

    @staticmethod
    def verify(username, password):
        if not PanelUserStore.verify_password(username, password):
            return None
        user_data = PanelUserStore.get_user(username)
        if not user_data:
            return None
        return User(
            username,
            user_data.get('is_admin', False),
            user_data.get('permissions', {})
        )

    @staticmethod
    def get(user_id):
        user_data = PanelUserStore.get_user(user_id)
        if not user_data:
            return None
        return User(
            user_data.get('username'),
            user_data.get('is_admin', False),
            user_data.get('permissions', {})
        )
