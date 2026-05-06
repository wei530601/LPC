"""
系统控制模块 - 提供重启、关机、日志查看、进程管理等功能
"""
import subprocess
import psutil
import os
from datetime import datetime


class SystemControl:
    """系统控制类"""
    
    @staticmethod
    def reboot_system():
        """重启系统"""
        try:
            subprocess.run(['sudo', 'reboot'], check=True)
            return {'success': True}
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def shutdown_system():
        """关机"""
        try:
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
            return {'success': True}
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_system_logs(lines=100, service=None):
        """获取系统日志"""
        try:
            if service:
                # 获取特定服务的日志
                cmd = ['journalctl', '-u', service, '-n', str(lines), '--no-pager']
            else:
                # 获取系统日志
                cmd = ['journalctl', '-n', str(lines), '--no-pager']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return {
                'success': True,
                'logs': result.stdout
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '获取日志超时'}
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_processes():
        """获取进程列表"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'user': pinfo['username'],
                        'cpu': round(pinfo['cpu_percent'], 1),
                        'memory': round(pinfo['memory_percent'], 1),
                        'status': pinfo['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x['cpu'], reverse=True)
            
            return {
                'success': True,
                'processes': processes
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def kill_process(pid):
        """结束进程"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            return {'success': True}
        except psutil.NoSuchProcess:
            return {'success': False, 'error': '进程不存在'}
        except psutil.AccessDenied:
            return {'success': False, 'error': '权限不足'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_uptime():
        """获取系统运行时间"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return {
                'success': True,
                'uptime': f"{days}天 {hours}小时 {minutes}分钟",
                'boot_time': datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
