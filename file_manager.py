import os
import subprocess
import json
from pathlib import Path
from werkzeug.utils import secure_filename

class FileManager:
    def __init__(self, root_path='/home/pi'):
        self.root_path = os.path.abspath(root_path)
    
    def _is_safe_path(self, path):
        """检查路径是否在允许的根目录下"""
        abs_path = os.path.abspath(path)
        return abs_path.startswith(self.root_path)
    
    def list_directory(self, path):
        """列出目录内容"""
        try:
            full_path = os.path.join(self.root_path, path.lstrip('/'))
            if not self._is_safe_path(full_path):
                return {'error': '无权访问此路径'}
            
            if not os.path.exists(full_path):
                return {'error': '路径不存在'}
            
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                try:
                    stat = os.stat(item_path)
                    items.append({
                        'name': item,
                        'type': 'directory' if os.path.isdir(item_path) else 'file',
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'permissions': oct(stat.st_mode)[-3:]
                    })
                except:
                    pass
            
            return {
                'path': path,
                'items': sorted(items, key=lambda x: (x['type'] != 'directory', x['name']))
            }
        except Exception as e:
            return {'error': str(e)}
    
    def read_file(self, path):
        """读取文件内容"""
        try:
            full_path = os.path.join(self.root_path, path.lstrip('/'))
            if not self._is_safe_path(full_path):
                return {'error': '无权访问此文件'}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {'content': content}
        except UnicodeDecodeError:
            return {'error': '无法读取二进制文件'}
        except Exception as e:
            return {'error': str(e)}
    
    def write_file(self, path, content):
        """写入文件内容"""
        try:
            full_path = os.path.join(self.root_path, path.lstrip('/'))
            if not self._is_safe_path(full_path):
                return {'error': '无权访问此文件'}
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def delete_file(self, path):
        """删除文件或目录"""
        try:
            full_path = os.path.join(self.root_path, path.lstrip('/'))
            if not self._is_safe_path(full_path):
                return {'error': '无权访问此路径'}
            
            if os.path.isdir(full_path):
                os.rmdir(full_path)
            else:
                os.remove(full_path)
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def create_directory(self, path):
        """创建目录"""
        try:
            full_path = os.path.join(self.root_path, path.lstrip('/'))
            if not self._is_safe_path(full_path):
                return {'error': '无权访问此路径'}
            
            os.makedirs(full_path, exist_ok=True)
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def get_file_path(self, path):
        """获取文件的完整路径（用于下载）"""
        full_path = os.path.join(self.root_path, path.lstrip('/'))
        if self._is_safe_path(full_path) and os.path.isfile(full_path):
            return full_path
        return None
