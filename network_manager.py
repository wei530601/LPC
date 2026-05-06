import subprocess
import re
import os


class NetworkManager:
    """网络管理类"""
    
    def __init__(self):
        pass
    
    # ============ WiFi 管理 ============
    
    def scan_wifi(self):
        """扫描可用的WiFi网络"""
        try:
            # 使用 iwlist 扫描
            result = subprocess.run(
                ['sudo', 'iwlist', 'wlan0', 'scan'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                return []
            
            networks = []
            current_network = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                # 新的网络
                if 'Cell' in line and 'Address:' in line:
                    if current_network:
                        networks.append(current_network)
                    current_network = {}
                    # 提取MAC地址
                    match = re.search(r'Address: ([\w:]+)', line)
                    if match:
                        current_network['mac'] = match.group(1)
                
                # SSID
                elif 'ESSID:' in line:
                    match = re.search(r'ESSID:"(.+)"', line)
                    if match:
                        current_network['ssid'] = match.group(1)
                
                # 信号质量
                elif 'Quality=' in line:
                    match = re.search(r'Quality=(\d+)/(\d+)', line)
                    if match:
                        quality = int(match.group(1))
                        max_quality = int(match.group(2))
                        current_network['quality'] = int((quality / max_quality) * 100)
                    
                    # 信号强度
                    match = re.search(r'Signal level=(-?\d+)', line)
                    if match:
                        current_network['signal'] = int(match.group(1))
                
                # 加密方式
                elif 'Encryption key:' in line:
                    current_network['encrypted'] = 'on' in line.lower()
                
                # WPA/WPA2
                elif 'IEEE 802.11i/WPA2' in line or 'WPA Version' in line:
                    current_network['encryption_type'] = 'WPA2'
            
            if current_network:
                networks.append(current_network)
            
            return networks
        
        except subprocess.TimeoutExpired:
            return []
        except Exception as e:
            print(f"WiFi扫描失败: {e}")
            return []
    
    def get_current_wifi(self):
        """获取当前连接的WiFi信息"""
        try:
            result = subprocess.run(
                ['iwgetid', '-r'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                ssid = result.stdout.strip()
                
                # 获取信号强度
                result2 = subprocess.run(
                    ['iwconfig', 'wlan0'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                signal = None
                if result2.returncode == 0:
                    match = re.search(r'Signal level=(-?\d+)', result2.stdout)
                    if match:
                        signal = int(match.group(1))
                
                return {
                    'connected': True,
                    'ssid': ssid,
                    'signal': signal
                }
            
            return {'connected': False}
        
        except Exception as e:
            print(f"获取当前WiFi失败: {e}")
            return {'connected': False}
    
    def connect_wifi(self, ssid, password=None):
        """连接到WiFi网络"""
        try:
            # 使用 wpa_passphrase 生成配置（如果有密码）
            if password:
                config_file = '/tmp/wpa_temp.conf'
                result = subprocess.run(
                    ['wpa_passphrase', ssid, password],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    return False, "生成WiFi配置失败"
                
                with open(config_file, 'w') as f:
                    f.write(result.stdout)
                
                # 使用 wpa_supplicant 连接
                subprocess.run(
                    ['sudo', 'wpa_supplicant', '-B', '-i', 'wlan0', '-c', config_file],
                    timeout=15
                )
                
                # 获取IP地址
                subprocess.run(
                    ['sudo', 'dhclient', 'wlan0'],
                    timeout=15
                )
                
                os.remove(config_file)
            
            return True, "连接成功"
        
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def disconnect_wifi(self):
        """断开WiFi连接"""
        try:
            subprocess.run(
                ['sudo', 'ifconfig', 'wlan0', 'down'],
                timeout=5
            )
            subprocess.run(
                ['sudo', 'ifconfig', 'wlan0', 'up'],
                timeout=5
            )
            return True, "断开成功"
        except Exception as e:
            return False, f"断开失败: {str(e)}"
    
    # ============ 网络接口配置 ============
    
    def get_network_interfaces(self):
        """获取所有网络接口信息"""
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            interfaces = []
            current_interface = {}
            
            for line in result.stdout.split('\n'):
                # 新接口
                if re.match(r'^\d+:', line):
                    if current_interface:
                        interfaces.append(current_interface)
                    
                    match = re.search(r'\d+: ([\w]+):', line)
                    if match:
                        current_interface = {
                            'name': match.group(1),
                            'state': 'UP' if 'UP' in line else 'DOWN',
                            'ipv4': [],
                            'ipv6': []
                        }
                
                # IPv4地址
                elif 'inet ' in line and current_interface:
                    match = re.search(r'inet ([\d.]+)/(\d+)', line)
                    if match:
                        current_interface['ipv4'].append({
                            'address': match.group(1),
                            'prefix': match.group(2)
                        })
                
                # IPv6地址
                elif 'inet6 ' in line and current_interface:
                    match = re.search(r'inet6 ([\w:]+)/(\d+)', line)
                    if match:
                        current_interface['ipv6'].append({
                            'address': match.group(1),
                            'prefix': match.group(2)
                        })
            
            if current_interface:
                interfaces.append(current_interface)
            
            return interfaces
        
        except Exception as e:
            print(f"获取网络接口失败: {e}")
            return []
    
    def get_dns_servers(self):
        """获取DNS服务器配置"""
        try:
            dns_servers = []
            
            if os.path.exists('/etc/resolv.conf'):
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.strip().startswith('nameserver'):
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                dns_servers.append(parts[1])
            
            return dns_servers
        
        except Exception as e:
            print(f"获取DNS服务器失败: {e}")
            return []
    
    # ============ 防火墙管理 (UFW) ============
    
    def is_ufw_installed(self):
        """检查UFW是否已安装"""
        try:
            result = subprocess.run(
                ['which', 'ufw'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def get_ufw_status(self):
        """获取UFW状态"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', 'status', 'verbose'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            status = {
                'enabled': 'Status: active' in result.stdout,
                'default_incoming': 'deny',
                'default_outgoing': 'allow',
                'rules': []
            }
            
            # 解析规则
            in_rules_section = False
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                if 'Default:' in line:
                    if 'deny (incoming)' in line:
                        status['default_incoming'] = 'deny'
                    elif 'allow (incoming)' in line:
                        status['default_incoming'] = 'allow'
                    
                    if 'deny (outgoing)' in line:
                        status['default_outgoing'] = 'deny'
                    elif 'allow (outgoing)' in line:
                        status['default_outgoing'] = 'allow'
                
                elif line.startswith('To') or line.startswith('--'):
                    in_rules_section = True
                    continue
                
                elif in_rules_section and line:
                    parts = re.split(r'\s{2,}', line)
                    if len(parts) >= 2:
                        status['rules'].append({
                            'action': parts[1] if len(parts) > 1 else '',
                            'from': parts[2] if len(parts) > 2 else '',
                            'to': parts[0] if parts else ''
                        })
            
            return status
        
        except Exception as e:
            print(f"获取UFW状态失败: {e}")
            return None
    
    def ufw_enable(self):
        """启用UFW"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', '--force', 'enable'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def ufw_disable(self):
        """禁用UFW"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', 'disable'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def ufw_add_rule(self, port, protocol='tcp', action='allow'):
        """添加UFW规则"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', action, f'{port}/{protocol}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)
    
    def ufw_delete_rule(self, port, protocol='tcp'):
        """删除UFW规则"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', 'delete', 'allow', f'{port}/{protocol}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)
    
    # ============ 端口监听状态 ============
    
    def get_listening_ports(self):
        """获取正在监听的端口"""
        try:
            result = subprocess.run(
                ['sudo', 'ss', '-tuln'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return []
            
            ports = []
            for line in result.stdout.split('\n')[1:]:  # 跳过标题行
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    protocol = parts[0]
                    local_address = parts[4]
                    
                    # 提取端口
                    match = re.search(r':(\d+)$', local_address)
                    if match:
                        port = match.group(1)
                        
                        # 提取地址
                        address = local_address.rsplit(':', 1)[0]
                        if address.startswith('['):
                            address = address[1:-1] if address.endswith(']') else address[1:]
                        
                        ports.append({
                            'protocol': protocol,
                            'address': address if address else '*',
                            'port': port
                        })
            
            return ports
        
        except Exception as e:
            print(f"获取监听端口失败: {e}")
            return []
    
    # ============ 网络连接实时监控 ============
    
    def get_network_connections(self):
        """获取网络连接状态"""
        try:
            result = subprocess.run(
                ['ss', '-tuna'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {'established': 0, 'listen': 0, 'time_wait': 0, 'close_wait': 0}
            
            stats = {
                'established': 0,
                'listen': 0,
                'time_wait': 0,
                'close_wait': 0,
                'syn_sent': 0,
                'syn_recv': 0,
                'total': 0
            }
            
            for line in result.stdout.split('\n')[1:]:
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 1:
                    state = parts[0].lower()
                    
                    if 'estab' in state:
                        stats['established'] += 1
                    elif 'listen' in state:
                        stats['listen'] += 1
                    elif 'time-wait' in state or 'time_wait' in state:
                        stats['time_wait'] += 1
                    elif 'close-wait' in state or 'close_wait' in state:
                        stats['close_wait'] += 1
                    elif 'syn-sent' in state or 'syn_sent' in state:
                        stats['syn_sent'] += 1
                    elif 'syn-recv' in state or 'syn_recv' in state:
                        stats['syn_recv'] += 1
                    
                    stats['total'] += 1
            
            return stats
        
        except Exception as e:
            print(f"获取网络连接失败: {e}")
            return {'established': 0, 'listen': 0, 'time_wait': 0, 'close_wait': 0}
    
    def get_network_stats(self):
        """获取网络流量统计"""
        try:
            result = subprocess.run(
                ['cat', '/proc/net/dev'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return []
            
            stats = []
            lines = result.stdout.split('\n')[2:]  # 跳过前两行标题
            
            for line in lines:
                if not line.strip() or ':' not in line:
                    continue
                
                parts = line.split(':')
                if len(parts) != 2:
                    continue
                
                interface = parts[0].strip()
                values = parts[1].split()
                
                if len(values) >= 16:
                    stats.append({
                        'interface': interface,
                        'rx_bytes': int(values[0]),
                        'rx_packets': int(values[1]),
                        'rx_errors': int(values[2]),
                        'tx_bytes': int(values[8]),
                        'tx_packets': int(values[9]),
                        'tx_errors': int(values[10])
                    })
            
            return stats
        
        except Exception as e:
            print(f"获取网络统计失败: {e}")
            return []
