"""
APT 包管理器模块
提供软件包的搜索、安装、卸载、更新等功能
"""

import subprocess
import re
from typing import List, Dict, Optional


class AptManager:
    """APT 包管理器"""
    
    @staticmethod
    def update_package_list() -> Dict:
        """更新软件包列表（apt update）"""
        try:
            result = subprocess.run(
                ['sudo', 'apt', 'update'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': '软件包列表更新成功',
                    'output': result.stdout
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
    def upgrade_packages() -> Dict:
        """升级所有可更新的软件包（apt upgrade -y）"""
        try:
            result = subprocess.run(
                ['sudo', 'apt', 'upgrade', '-y'],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': '系统升级成功',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '操作超时（升级时间过长）'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def install_package(package_name: str) -> Dict:
        """安装软件包"""
        try:
            result = subprocess.run(
                ['sudo', 'apt', 'install', '-y', package_name],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'软件包 {package_name} 安装成功',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '安装超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def remove_package(package_name: str, purge: bool = False) -> Dict:
        """卸载软件包"""
        try:
            cmd = ['sudo', 'apt', 'purge' if purge else 'remove', '-y', package_name]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                action = '清除' if purge else '卸载'
                return {
                    'success': True,
                    'message': f'软件包 {package_name} {action}成功',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '卸载超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def search_packages(keyword: str, limit: int = 50) -> Dict:
        """搜索软件包"""
        try:
            result = subprocess.run(
                ['apt', 'search', keyword],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            packages = []
            lines = result.stdout.split('\n')
            
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):
                    # 第一行是包名和架构
                    match = re.match(r'^(\S+)/\S+\s+(\S+)\s+(\S+)\s*\[(.+)\]', lines[i])
                    if not match:
                        match = re.match(r'^(\S+)/\S+\s+(\S+)\s+(\S+)', lines[i])
                    
                    if match:
                        name = match.group(1)
                        version = match.group(2)
                        arch = match.group(3)
                        status = match.group(4) if len(match.groups()) >= 4 else ''
                        
                        # 第二行是描述
                        description = lines[i + 1].strip()
                        
                        packages.append({
                            'name': name,
                            'version': version,
                            'architecture': arch,
                            'status': status,
                            'description': description
                        })
                        
                        if len(packages) >= limit:
                            break
            
            return {
                'success': True,
                'packages': packages,
                'total': len(packages)
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '搜索超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def list_installed_packages(limit: int = 100) -> Dict:
        """列出已安装的软件包"""
        try:
            result = subprocess.run(
                ['dpkg', '-l'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            packages = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                # 跳过标题行
                if line.startswith('ii'):
                    parts = line.split()
                    if len(parts) >= 4:
                        packages.append({
                            'name': parts[1],
                            'version': parts[2],
                            'architecture': parts[3],
                            'description': ' '.join(parts[4:]) if len(parts) > 4 else ''
                        })
                        
                        if len(packages) >= limit:
                            break
            
            return {
                'success': True,
                'packages': packages,
                'total': len(packages)
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '查询超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_package_info(package_name: str) -> Dict:
        """获取软件包详细信息"""
        try:
            result = subprocess.run(
                ['apt', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                info = {}
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                
                return {
                    'success': True,
                    'info': info
                }
            else:
                return {
                    'success': False,
                    'error': '软件包不存在'
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '查询超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def list_upgradable() -> Dict:
        """列出可更新的软件包"""
        try:
            result = subprocess.run(
                ['apt', 'list', '--upgradable'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            packages = []
            lines = result.stdout.split('\n')[1:]  # 跳过标题行
            
            for line in lines:
                if '/' in line:
                    match = re.match(r'^(\S+)/\S+\s+(\S+)\s+\S+\s+\[upgradable from: (\S+)\]', line)
                    if match:
                        packages.append({
                            'name': match.group(1),
                            'new_version': match.group(2),
                            'current_version': match.group(3)
                        })
            
            return {
                'success': True,
                'packages': packages,
                'total': len(packages)
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '查询超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def clean_cache() -> Dict:
        """清理 APT 缓存"""
        try:
            result = subprocess.run(
                ['sudo', 'apt', 'clean'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': '缓存清理成功'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '清理超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def autoremove() -> Dict:
        """自动移除不需要的软件包"""
        try:
            result = subprocess.run(
                ['sudo', 'apt', 'autoremove', '-y'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': '自动清理完成',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '清理超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
