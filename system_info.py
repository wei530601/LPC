import psutil
import os
import time

class SystemInfo:
    @staticmethod
    def get_cpu_info():
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        return {
            'percent': cpu_percent,
            'count': psutil.cpu_count(),
            'freq': {
                'current': cpu_freq.current if cpu_freq else 0,
                'min': cpu_freq.min if cpu_freq else 0,
                'max': cpu_freq.max if cpu_freq else 0
            }
        }
    
    @staticmethod
    def get_memory_info():
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percent': mem.percent,
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'percent': swap.percent
            }
        }
    
    @staticmethod
    def get_disk_info():
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except:
                pass
        return disks
    
    @staticmethod
    def get_temperature():
        try:
            # 树莓派温度
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = float(f.read()) / 1000.0
                    return {'cpu': temp}
            
            # 通用方法
            temps = psutil.sensors_temperatures()
            if temps:
                result = {}
                for name, entries in temps.items():
                    if entries:
                        result[name] = entries[0].current
                return result
        except:
            pass
        return {}
    
    @staticmethod
    def get_network_info():
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    
    @staticmethod
    def get_uptime():
        return int(time.time() - psutil.boot_time())
    
    @staticmethod
    def get_all():
        return {
            'cpu': SystemInfo.get_cpu_info(),
            'memory': SystemInfo.get_memory_info(),
            'disk': SystemInfo.get_disk_info(),
            'temperature': SystemInfo.get_temperature(),
            'network': SystemInfo.get_network_info(),
            'uptime': SystemInfo.get_uptime()
        }
