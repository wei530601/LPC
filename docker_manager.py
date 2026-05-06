"""
Docker 管理模块 - 提供容器、镜像、网络等管理功能
"""
import subprocess
import json


class DockerManager:
    """Docker 管理类"""
    
    @staticmethod
    def is_docker_installed():
        """检查 Docker 是否已安装"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def get_containers(all_containers=True):
        """获取容器列表"""
        try:
            cmd = ['docker', 'ps', '--format', '{{json .}}']
            if all_containers:
                cmd.append('-a')
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return {'success': False, 'error': result.stderr}
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container = json.loads(line)
                        containers.append({
                            'id': container.get('ID', ''),
                            'name': container.get('Names', ''),
                            'image': container.get('Image', ''),
                            'status': container.get('Status', ''),
                            'state': container.get('State', ''),
                            'ports': container.get('Ports', '')
                        })
                    except json.JSONDecodeError:
                        continue
            
            return {'success': True, 'containers': containers}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '命令执行超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_images():
        """获取镜像列表"""
        try:
            result = subprocess.run(
                ['docker', 'images', '--format', '{{json .}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {'success': False, 'error': result.stderr}
            
            images = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        image = json.loads(line)
                        images.append({
                            'id': image.get('ID', ''),
                            'repository': image.get('Repository', ''),
                            'tag': image.get('Tag', ''),
                            'size': image.get('Size', ''),
                            'created': image.get('CreatedSince', '')
                        })
                    except json.JSONDecodeError:
                        continue
            
            return {'success': True, 'images': images}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def control_container(container_id, action):
        """控制容器（start/stop/restart/remove）"""
        try:
            valid_actions = ['start', 'stop', 'restart', 'rm', 'pause', 'unpause']
            if action not in valid_actions:
                return {'success': False, 'error': '无效的操作'}
            
            cmd = ['docker', action, container_id]
            if action == 'rm':
                cmd.append('-f')  # 强制删除
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {'success': True, 'message': f'容器 {action} 成功'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_container_logs(container_id, lines=100):
        """获取容器日志"""
        try:
            result = subprocess.run(
                ['docker', 'logs', '--tail', str(lines), container_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                'success': True,
                'logs': result.stdout + result.stderr
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_container_stats(container_id):
        """获取容器资源使用统计"""
        try:
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', '{{json .}}', container_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                stats = json.loads(result.stdout.strip())
                return {
                    'success': True,
                    'stats': {
                        'cpu': stats.get('CPUPerc', '0%'),
                        'memory': stats.get('MemUsage', '0B / 0B'),
                        'memory_percent': stats.get('MemPerc', '0%'),
                        'network': stats.get('NetIO', '0B / 0B'),
                        'block_io': stats.get('BlockIO', '0B / 0B')
                    }
                }
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def remove_image(image_id):
        """删除镜像"""
        try:
            result = subprocess.run(
                ['docker', 'rmi', '-f', image_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': '镜像删除成功'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def pull_image(image_name):
        """拉取镜像"""
        try:
            result = subprocess.run(
                ['docker', 'pull', image_name],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': '镜像拉取成功', 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '拉取超时（5分钟）'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_docker_info():
        """获取 Docker 系统信息"""
        try:
            result = subprocess.run(
                ['docker', 'info', '--format', '{{json .}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return {
                    'success': True,
                    'info': {
                        'containers': info.get('Containers', 0),
                        'running': info.get('ContainersRunning', 0),
                        'paused': info.get('ContainersPaused', 0),
                        'stopped': info.get('ContainersStopped', 0),
                        'images': info.get('Images', 0),
                        'server_version': info.get('ServerVersion', 'N/A'),
                        'storage_driver': info.get('Driver', 'N/A'),
                        'memory': info.get('MemTotal', 0)
                    }
                }
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def prune_system():
        """清理未使用的 Docker 资源"""
        try:
            result = subprocess.run(
                ['docker', 'system', 'prune', '-a', '-f'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': '清理完成', 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
