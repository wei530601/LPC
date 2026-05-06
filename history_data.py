"""
历史数据模块 - 存储和查询系统监控历史数据
"""
import json
import os
from datetime import datetime, timedelta
from collections import deque
import threading


class HistoryData:
    """历史数据管理类"""
    
    def __init__(self, data_file='data/history.json', max_records=10080):
        """
        初始化历史数据管理器
        max_records: 最大记录数，默认10080（7天*24小时*60分钟，每分钟一条）
        """
        self.data_file = data_file
        self.max_records = max_records
        self.data = {
            'cpu': deque(maxlen=max_records),
            'memory': deque(maxlen=max_records),
            'disk': deque(maxlen=max_records),
            'network_sent': deque(maxlen=max_records),
            'network_recv': deque(maxlen=max_records),
            'temperature': deque(maxlen=max_records)
        }
        self.lock = threading.Lock()
        self._ensure_data_dir()
        self._load_data()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def _load_data(self):
        """从文件加载历史数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    for key in self.data:
                        if key in loaded_data:
                            self.data[key] = deque(loaded_data[key], maxlen=self.max_records)
        except Exception as e:
            print(f"加载历史数据失败: {e}")
    
    def save_data(self):
        """保存历史数据到文件"""
        try:
            with self.lock:
                data_to_save = {key: list(value) for key, value in self.data.items()}
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f)
        except Exception as e:
            print(f"保存历史数据失败: {e}")
    
    def add_record(self, system_info):
        """添加一条记录"""
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            self.data['cpu'].append({
                'time': timestamp,
                'value': system_info.get('cpu', {}).get('percent', 0)
            })
            
            self.data['memory'].append({
                'time': timestamp,
                'value': system_info.get('memory', {}).get('percent', 0)
            })
            
            disk_info = system_info.get('disk', [])
            if disk_info:
                self.data['disk'].append({
                    'time': timestamp,
                    'value': disk_info[0].get('percent', 0)
                })
            
            network = system_info.get('network', {})
            self.data['network_sent'].append({
                'time': timestamp,
                'value': network.get('sent_mb', 0)
            })
            
            self.data['network_recv'].append({
                'time': timestamp,
                'value': network.get('recv_mb', 0)
            })
            
            self.data['temperature'].append({
                'time': timestamp,
                'value': system_info.get('temperature', 0)
            })
    
    def get_records(self, metric, duration='1h'):
        """
        获取指定时间范围的记录
        metric: cpu, memory, disk, network_sent, network_recv, temperature
        duration: 1h, 24h, 7d
        """
        with self.lock:
            if metric not in self.data:
                return []
            
            now = datetime.now()
            if duration == '1h':
                cutoff = now - timedelta(hours=1)
            elif duration == '24h':
                cutoff = now - timedelta(hours=24)
            elif duration == '7d':
                cutoff = now - timedelta(days=7)
            else:
                cutoff = now - timedelta(hours=1)
            
            # 过滤时间范围内的数据
            records = []
            for record in self.data[metric]:
                try:
                    record_time = datetime.fromisoformat(record['time'])
                    if record_time >= cutoff:
                        records.append(record)
                except Exception:
                    continue
            
            return records
    
    def get_statistics(self, metric, duration='24h'):
        """获取统计信息"""
        records = self.get_records(metric, duration)
        
        if not records:
            return {
                'min': 0,
                'max': 0,
                'avg': 0,
                'current': 0
            }
        
        values = [r['value'] for r in records]
        
        return {
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'avg': round(sum(values) / len(values), 2),
            'current': round(values[-1], 2) if values else 0
        }
    
    def get_all_statistics(self, duration='24h'):
        """获取所有指标的统计信息"""
        return {
            'cpu': self.get_statistics('cpu', duration),
            'memory': self.get_statistics('memory', duration),
            'disk': self.get_statistics('disk', duration),
            'network_sent': self.get_statistics('network_sent', duration),
            'network_recv': self.get_statistics('network_recv', duration),
            'temperature': self.get_statistics('temperature', duration)
        }
    
    def has_data(self):
        """检查是否有数据"""
        with self.lock:
            return any(len(self.data[key]) > 0 for key in self.data)
