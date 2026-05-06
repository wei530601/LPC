import psutil
import subprocess
import os
from collections import defaultdict


class PerformanceAnalyzer:
    """性能分析类"""
    
    def __init__(self):
        self._last_disk_io = {}
        self._last_net_io = {}
    
    # ============ 进程资源占用排行榜 ============
    
    def get_top_processes_by_cpu(self, limit=10):
        """获取CPU占用最高的进程"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    # 获取CPU百分比（需要一点时间来计算）
                    proc.info['cpu_percent'] = proc.cpu_percent(interval=0.1)
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            return processes[:limit]
        
        except Exception as e:
            print(f"获取CPU进程排行失败: {e}")
            return []
    
    def get_top_processes_by_memory(self, limit=10):
        """获取内存占用最高的进程"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    info = proc.info.copy()
                    # 添加内存使用量（MB）
                    if 'memory_info' in info and info['memory_info']:
                        info['memory_mb'] = info['memory_info'].rss / 1024 / 1024
                    else:
                        info['memory_mb'] = 0
                    processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按内存使用率排序
            processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            
            return processes[:limit]
        
        except Exception as e:
            print(f"获取内存进程排行失败: {e}")
            return []
    
    def get_process_details(self, pid):
        """获取进程详细信息"""
        try:
            proc = psutil.Process(pid)
            
            # 获取进程详细信息
            with proc.oneshot():
                return {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'username': proc.username(),
                    'status': proc.status(),
                    'cpu_percent': proc.cpu_percent(interval=0.1),
                    'memory_percent': proc.memory_percent(),
                    'memory_mb': proc.memory_info().rss / 1024 / 1024,
                    'num_threads': proc.num_threads(),
                    'create_time': proc.create_time(),
                    'cmdline': ' '.join(proc.cmdline()) if proc.cmdline() else '',
                    'cwd': proc.cwd() if proc.cwd() else '',
                    'num_fds': proc.num_fds() if hasattr(proc, 'num_fds') else 0
                }
        
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            return None
        except Exception as e:
            print(f"获取进程详情失败: {e}")
            return None
    
    # ============ 磁盘 I/O 实时监控 ============
    
    def get_disk_io_stats(self):
        """获取磁盘I/O统计"""
        try:
            disk_io = psutil.disk_io_counters(perdisk=True)
            
            stats = []
            for disk_name, io_counters in disk_io.items():
                # 计算速度（如果有上一次的数据）
                read_speed = 0
                write_speed = 0
                
                if disk_name in self._last_disk_io:
                    last = self._last_disk_io[disk_name]
                    time_delta = 1  # 假设1秒间隔
                    
                    read_speed = (io_counters.read_bytes - last['read_bytes']) / time_delta
                    write_speed = (io_counters.write_bytes - last['write_bytes']) / time_delta
                
                # 保存当前数据
                self._last_disk_io[disk_name] = {
                    'read_bytes': io_counters.read_bytes,
                    'write_bytes': io_counters.write_bytes
                }
                
                stats.append({
                    'disk': disk_name,
                    'read_count': io_counters.read_count,
                    'write_count': io_counters.write_count,
                    'read_bytes': io_counters.read_bytes,
                    'write_bytes': io_counters.write_bytes,
                    'read_time': io_counters.read_time,
                    'write_time': io_counters.write_time,
                    'read_speed': read_speed,
                    'write_speed': write_speed
                })
            
            return stats
        
        except Exception as e:
            print(f"获取磁盘IO失败: {e}")
            return []
    
    def get_disk_usage_by_directory(self, path='/', depth=2):
        """获取目录磁盘使用情况"""
        try:
            # 使用 du 命令获取目录大小
            result = subprocess.run(
                ['du', '-h', '-d', str(depth), path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            directories = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split('\t')
                if len(parts) == 2:
                    directories.append({
                        'size': parts[0],
                        'path': parts[1]
                    })
            
            return directories
        
        except subprocess.TimeoutExpired:
            return []
        except Exception as e:
            print(f"获取目录使用情况失败: {e}")
            return []
    
    # ============ 网络连接状态 ============
    
    def get_network_connections_detailed(self):
        """获取详细的网络连接信息"""
        try:
            connections = []
            
            for conn in psutil.net_connections(kind='inet'):
                try:
                    # 获取进程信息
                    process_name = ''
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            process_name = proc.name()
                        except:
                            pass
                    
                    # 本地地址
                    local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ''
                    
                    # 远程地址
                    remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ''
                    
                    connections.append({
                        'protocol': 'TCP' if conn.type == 1 else 'UDP',
                        'local_address': local_addr,
                        'remote_address': remote_addr,
                        'status': conn.status,
                        'pid': conn.pid,
                        'process': process_name
                    })
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return connections
        
        except Exception as e:
            print(f"获取网络连接详情失败: {e}")
            return []
    
    def get_network_io_stats(self):
        """获取网络I/O统计"""
        try:
            net_io = psutil.net_io_counters(pernic=True)
            
            stats = []
            for interface_name, io_counters in net_io.items():
                # 计算速度
                recv_speed = 0
                sent_speed = 0
                
                if interface_name in self._last_net_io:
                    last = self._last_net_io[interface_name]
                    time_delta = 1  # 假设1秒间隔
                    
                    recv_speed = (io_counters.bytes_recv - last['bytes_recv']) / time_delta
                    sent_speed = (io_counters.bytes_sent - last['bytes_sent']) / time_delta
                
                # 保存当前数据
                self._last_net_io[interface_name] = {
                    'bytes_recv': io_counters.bytes_recv,
                    'bytes_sent': io_counters.bytes_sent
                }
                
                stats.append({
                    'interface': interface_name,
                    'bytes_sent': io_counters.bytes_sent,
                    'bytes_recv': io_counters.bytes_recv,
                    'packets_sent': io_counters.packets_sent,
                    'packets_recv': io_counters.packets_recv,
                    'errin': io_counters.errin,
                    'errout': io_counters.errout,
                    'dropin': io_counters.dropin,
                    'dropout': io_counters.dropout,
                    'recv_speed': recv_speed,
                    'sent_speed': sent_speed
                })
            
            return stats
        
        except Exception as e:
            print(f"获取网络IO失败: {e}")
            return []
    
    # ============ 系统负载分析 ============
    
    def get_system_load(self):
        """获取系统负载（1/5/15分钟）"""
        try:
            # 获取系统负载平均值
            load_avg = os.getloadavg()
            
            # 获取CPU核心数
            cpu_count = psutil.cpu_count()
            
            return {
                'load_1min': load_avg[0],
                'load_5min': load_avg[1],
                'load_15min': load_avg[2],
                'cpu_count': cpu_count,
                'load_1min_percent': (load_avg[0] / cpu_count) * 100 if cpu_count else 0,
                'load_5min_percent': (load_avg[1] / cpu_count) * 100 if cpu_count else 0,
                'load_15min_percent': (load_avg[2] / cpu_count) * 100 if cpu_count else 0
            }
        
        except Exception as e:
            print(f"获取系统负载失败: {e}")
            return {
                'load_1min': 0,
                'load_5min': 0,
                'load_15min': 0,
                'cpu_count': 0,
                'load_1min_percent': 0,
                'load_5min_percent': 0,
                'load_15min_percent': 0
            }
    
    def get_cpu_stats(self):
        """获取CPU详细统计"""
        try:
            # CPU时间占比
            cpu_times_percent = psutil.cpu_times_percent(interval=1)
            
            # CPU频率
            cpu_freq = psutil.cpu_freq()
            
            # 上下文切换和中断
            cpu_stats = psutil.cpu_stats()
            
            return {
                'user': cpu_times_percent.user,
                'system': cpu_times_percent.system,
                'idle': cpu_times_percent.idle,
                'iowait': getattr(cpu_times_percent, 'iowait', 0),
                'irq': getattr(cpu_times_percent, 'irq', 0),
                'softirq': getattr(cpu_times_percent, 'softirq', 0),
                'freq_current': cpu_freq.current if cpu_freq else 0,
                'freq_min': cpu_freq.min if cpu_freq else 0,
                'freq_max': cpu_freq.max if cpu_freq else 0,
                'ctx_switches': cpu_stats.ctx_switches,
                'interrupts': cpu_stats.interrupts,
                'soft_interrupts': cpu_stats.soft_interrupts
            }
        
        except Exception as e:
            print(f"获取CPU统计失败: {e}")
            return {}
    
    def get_memory_details(self):
        """获取内存详细信息"""
        try:
            # 虚拟内存
            vmem = psutil.virtual_memory()
            
            # 交换内存
            swap = psutil.swap_memory()
            
            return {
                'total': vmem.total,
                'available': vmem.available,
                'used': vmem.used,
                'free': vmem.free,
                'percent': vmem.percent,
                'buffers': getattr(vmem, 'buffers', 0),
                'cached': getattr(vmem, 'cached', 0),
                'shared': getattr(vmem, 'shared', 0),
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': swap.percent
            }
        
        except Exception as e:
            print(f"获取内存详情失败: {e}")
            return {}
    
    # ============ 综合性能分析 ============
    
    def get_performance_summary(self):
        """获取性能综合摘要"""
        try:
            return {
                'load': self.get_system_load(),
                'cpu_stats': self.get_cpu_stats(),
                'memory': self.get_memory_details(),
                'disk_io': self.get_disk_io_stats(),
                'network_io': self.get_network_io_stats(),
                'top_cpu_processes': self.get_top_processes_by_cpu(5),
                'top_memory_processes': self.get_top_processes_by_memory(5)
            }
        
        except Exception as e:
            print(f"获取性能摘要失败: {e}")
            return {}
