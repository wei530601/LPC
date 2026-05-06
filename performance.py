"""
性能分析模块
提供进程监控、磁盘I/O分析、系统负载等功能
"""

import psutil
import subprocess
import os


class PerformanceAnalyzer:
    """性能分析类"""
    
    @staticmethod
    def get_top_processes(limit=10, sort_by='cpu'):
        """获取资源占用最高的进程
        
        Args:
            limit: 返回进程数量
            sort_by: 排序方式 ('cpu', 'memory', 'io')
        """
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    pinfo = proc.info
                    pinfo['memory_mb'] = proc.memory_info().rss / (1024 * 1024)  # MB
                    
                    # 获取IO信息（如果可用）
                    try:
                        io_counters = proc.io_counters()
                        pinfo['io_read_mb'] = io_counters.read_bytes / (1024 * 1024)
                        pinfo['io_write_mb'] = io_counters.write_bytes / (1024 * 1024)
                    except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                        pinfo['io_read_mb'] = 0
                        pinfo['io_write_mb'] = 0
                    
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # 排序
            if sort_by == 'cpu':
                processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            elif sort_by == 'memory':
                processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            elif sort_by == 'io':
                processes.sort(key=lambda x: x.get('io_read_mb', 0) + x.get('io_write_mb', 0), reverse=True)
            
            return {'success': True, 'processes': processes[:limit]}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_disk_io():
        """获取磁盘I/O统计"""
        try:
            disk_io = psutil.disk_io_counters(perdisk=True)
            
            io_stats = []
            for disk, counters in disk_io.items():
                io_stats.append({
                    'disk': disk,
                    'read_count': counters.read_count,
                    'write_count': counters.write_count,
                    'read_mb': counters.read_bytes / (1024 * 1024),
                    'write_mb': counters.write_bytes / (1024 * 1024),
                    'read_time_ms': counters.read_time,
                    'write_time_ms': counters.write_time
                })
            
            return {'success': True, 'io_stats': io_stats}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_disk_io_rate():
        """获取实时磁盘I/O速率（需要两次采样）"""
        try:
            # 第一次采样
            io_1 = psutil.disk_io_counters()
            
            import time
            time.sleep(1)  # 等待1秒
            
            # 第二次采样
            io_2 = psutil.disk_io_counters()
            
            read_rate = (io_2.read_bytes - io_1.read_bytes) / (1024 * 1024)  # MB/s
            write_rate = (io_2.write_bytes - io_1.write_bytes) / (1024 * 1024)  # MB/s
            
            return {
                'success': True,
                'read_rate_mb': round(read_rate, 2),
                'write_rate_mb': round(write_rate, 2),
                'total_rate_mb': round(read_rate + write_rate, 2)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_system_load():
        """获取系统负载（1/5/15分钟）"""
        try:
            load_avg = os.getloadavg()
            cpu_count = psutil.cpu_count()
            
            return {
                'success': True,
                'load_1min': round(load_avg[0], 2),
                'load_5min': round(load_avg[1], 2),
                'load_15min': round(load_avg[2], 2),
                'cpu_count': cpu_count,
                'load_1min_percent': round((load_avg[0] / cpu_count) * 100, 1),
                'load_5min_percent': round((load_avg[1] / cpu_count) * 100, 1),
                'load_15min_percent': round((load_avg[2] / cpu_count) * 100, 1)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_network_connections_stats():
        """获取网络连接统计"""
        try:
            connections = psutil.net_connections(kind='inet')
            
            stats = {
                'ESTABLISHED': 0,
                'LISTEN': 0,
                'TIME_WAIT': 0,
                'CLOSE_WAIT': 0,
                'SYN_SENT': 0,
                'SYN_RECV': 0,
                'FIN_WAIT1': 0,
                'FIN_WAIT2': 0,
                'CLOSING': 0,
                'LAST_ACK': 0,
                'NONE': 0
            }
            
            connection_list = []
            
            for conn in connections:
                status = conn.status if conn.status else 'NONE'
                
                if status in stats:
                    stats[status] += 1
                
                # 获取进程信息
                process_name = '-'
                try:
                    if conn.pid:
                        proc = psutil.Process(conn.pid)
                        process_name = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else '-'
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else '-'
                
                connection_list.append({
                    'protocol': 'TCP' if conn.type == 1 else 'UDP',
                    'local': laddr,
                    'remote': raddr,
                    'status': status,
                    'pid': conn.pid,
                    'process': process_name
                })
            
            return {
                'success': True,
                'summary': stats,
                'total': len(connections),
                'connections': connection_list[:100]  # 限制返回100条
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_cpu_per_core():
        """获取每个CPU核心的使用率"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq(percpu=True)
            
            cores = []
            for i, percent in enumerate(cpu_percent):
                core_info = {
                    'core': i,
                    'percent': round(percent, 1)
                }
                
                if cpu_freq and i < len(cpu_freq):
                    core_info['frequency'] = round(cpu_freq[i].current, 0)
                
                cores.append(core_info)
            
            return {'success': True, 'cores': cores}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_memory_details():
        """获取详细的内存信息"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'success': True,
                'virtual': {
                    'total_mb': round(mem.total / (1024 * 1024), 0),
                    'available_mb': round(mem.available / (1024 * 1024), 0),
                    'used_mb': round(mem.used / (1024 * 1024), 0),
                    'free_mb': round(mem.free / (1024 * 1024), 0),
                    'percent': mem.percent,
                    'buffers_mb': round(mem.buffers / (1024 * 1024), 0) if hasattr(mem, 'buffers') else 0,
                    'cached_mb': round(mem.cached / (1024 * 1024), 0) if hasattr(mem, 'cached') else 0
                },
                'swap': {
                    'total_mb': round(swap.total / (1024 * 1024), 0),
                    'used_mb': round(swap.used / (1024 * 1024), 0),
                    'free_mb': round(swap.free / (1024 * 1024), 0),
                    'percent': swap.percent
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_network_io():
        """获取网络I/O统计"""
        try:
            net_io = psutil.net_io_counters(pernic=True)
            
            io_stats = []
            for interface, counters in net_io.items():
                io_stats.append({
                    'interface': interface,
                    'bytes_sent_mb': round(counters.bytes_sent / (1024 * 1024), 2),
                    'bytes_recv_mb': round(counters.bytes_recv / (1024 * 1024), 2),
                    'packets_sent': counters.packets_sent,
                    'packets_recv': counters.packets_recv,
                    'errin': counters.errin,
                    'errout': counters.errout,
                    'dropin': counters.dropin,
                    'dropout': counters.dropout
                })
            
            return {'success': True, 'io_stats': io_stats}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_process_tree():
        """获取进程树结构"""
        try:
            # 获取所有进程
            all_procs = {}
            for proc in psutil.process_iter(['pid', 'name', 'ppid']):
                try:
                    info = proc.info
                    all_procs[info['pid']] = {
                        'pid': info['pid'],
                        'name': info['name'],
                        'ppid': info['ppid'],
                        'children': []
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 构建树结构
            root_procs = []
            for pid, info in all_procs.items():
                ppid = info['ppid']
                if ppid in all_procs:
                    all_procs[ppid]['children'].append(info)
                else:
                    root_procs.append(info)
            
            return {'success': True, 'tree': root_procs[:20]}  # 限制返回数量
        except Exception as e:
            return {'success': False, 'error': str(e)}
