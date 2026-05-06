"""
用户与权限管理模块
提供用户的创建、删除、密码修改、权限管理等功能
"""

import subprocess
import pwd
import grp
import re
from typing import List, Dict, Optional


class UserManager:
    """用户与权限管理器"""
    
    @staticmethod
    def list_users(include_system: bool = False) -> Dict:
        """列出所有用户"""
        try:
            users = []
            
            # 读取 /etc/passwd
            for user_info in pwd.getpwall():
                uid = user_info.pw_uid
                
                # 跳过系统用户（UID < 1000）
                if not include_system and uid < 1000:
                    continue
                
                # 获取用户所属组
                groups = []
                for group in grp.getgrall():
                    if user_info.pw_name in group.gr_mem or group.gr_gid == user_info.pw_gid:
                        groups.append(group.gr_name)
                
                users.append({
                    'username': user_info.pw_name,
                    'uid': uid,
                    'gid': user_info.pw_gid,
                    'home': user_info.pw_dir,
                    'shell': user_info.pw_shell,
                    'groups': groups,
                    'is_sudo': 'sudo' in groups or 'wheel' in groups or 'admin' in groups
                })
            
            return {
                'success': True,
                'users': sorted(users, key=lambda x: x['uid'])
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_user(username: str, password: str, groups: List[str] = None, create_home: bool = True) -> Dict:
        """添加新用户"""
        try:
            # 验证用户名格式
            if not re.match(r'^[a-z_][a-z0-9_-]*[$]?$', username):
                return {
                    'success': False,
                    'error': '用户名格式无效（只能包含小写字母、数字、下划线和连字符）'
                }
            
            # 创建用户
            cmd = ['sudo', 'useradd']
            
            if create_home:
                cmd.append('-m')
            
            if groups:
                cmd.extend(['-G', ','.join(groups)])
            
            cmd.append(username)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
            
            # 设置密码
            passwd_result = subprocess.run(
                ['sudo', 'chpasswd'],
                input=f'{username}:{password}',
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if passwd_result.returncode == 0:
                return {
                    'success': True,
                    'message': f'用户 {username} 创建成功'
                }
            else:
                return {
                    'success': False,
                    'error': '用户创建成功，但密码设置失败：' + passwd_result.stderr
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_user(username: str, remove_home: bool = False) -> Dict:
        """删除用户"""
        try:
            # 防止删除当前用户和系统关键用户
            if username in ['root', 'pi', 'admin']:
                return {
                    'success': False,
                    'error': '无法删除系统关键用户'
                }
            
            cmd = ['sudo', 'userdel']
            
            if remove_home:
                cmd.append('-r')
            
            cmd.append(username)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'用户 {username} 删除成功'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def change_password(username: str, new_password: str) -> Dict:
        """修改用户密码"""
        try:
            result = subprocess.run(
                ['sudo', 'chpasswd'],
                input=f'{username}:{new_password}',
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'用户 {username} 密码修改成功'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def list_groups() -> Dict:
        """列出所有用户组"""
        try:
            groups = []
            
            for group_info in grp.getgrall():
                groups.append({
                    'name': group_info.gr_name,
                    'gid': group_info.gr_gid,
                    'members': group_info.gr_mem
                })
            
            return {
                'success': True,
                'groups': sorted(groups, key=lambda x: x['gid'])
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_user_to_group(username: str, group: str) -> Dict:
        """将用户添加到组"""
        try:
            result = subprocess.run(
                ['sudo', 'usermod', '-aG', group, username],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'用户 {username} 已添加到组 {group}'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def remove_user_from_group(username: str, group: str) -> Dict:
        """将用户从组中移除"""
        try:
            result = subprocess.run(
                ['sudo', 'gpasswd', '-d', username, group],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'用户 {username} 已从组 {group} 中移除'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_logged_in_users() -> Dict:
        """获取当前登录的用户"""
        try:
            result = subprocess.run(
                ['who'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            users = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        users.append({
                            'username': parts[0],
                            'terminal': parts[1],
                            'login_time': ' '.join(parts[2:5]),
                            'ip': parts[5].strip('()') if len(parts) > 5 else 'local'
                        })
            
            return {
                'success': True,
                'users': users
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '查询超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def set_sudo_privilege(username: str, enable: bool) -> Dict:
        """设置用户 sudo 权限"""
        try:
            if enable:
                # 添加到 sudo 组
                result = subprocess.run(
                    ['sudo', 'usermod', '-aG', 'sudo', username],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                # 从 sudo 组移除
                result = subprocess.run(
                    ['sudo', 'gpasswd', '-d', username, 'sudo'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            if result.returncode == 0:
                action = '授予' if enable else '撤销'
                return {
                    'success': True,
                    'message': f'已{action}用户 {username} 的 sudo 权限'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def lock_user(username: str) -> Dict:
        """锁定用户账户"""
        try:
            result = subprocess.run(
                ['sudo', 'usermod', '-L', username],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'用户 {username} 已锁定'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def unlock_user(username: str) -> Dict:
        """解锁用户账户"""
        try:
            result = subprocess.run(
                ['sudo', 'usermod', '-U', username],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'用户 {username} 已解锁'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
