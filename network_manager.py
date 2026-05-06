"""
网络管理模块
提供WiFi配置、网络接口管理、防火墙管理等功能
"""

import subprocess
import re
import json


class NetworkManager:
    """网络管理类"""
    
    @staticmethod
    def scan_wifi():
        """扫描可用WiFi网络"""
        try:
            # 使用 nmcli 扫描WiFi
            result = subprocess.run(
                ['nmcli', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {'success': False, 'error': result.stderr}
            
            networks = []
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        ssid = parts[0]
                        signal = parts[1] if len(parts) > 1 else '0'
                        security = ' '.join(parts[2:]) if len(parts) > 2 else 'Open'
                        
                        networks.append({
                            'ssid': ssid,
                            'signal': signal,
                            'security': security
                        })
            
            return {'success': True, 'networks': networks}
        except FileNotFoundError:
            # 如果没有 nmcli，尝试使用 iwlist
            try:
                result = subprocess.run(
                    ['sudo', 'iwlist', 'wlan0', 'scan'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                networks = []
                current_network = {}
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'ESSID:' in line:
                        ssid = line.split('ESSID:')[1].strip('"')
                        if ssid:
                            current_network['ssid'] = ssid
                    elif 'Quality=' in line:
                        match = re.search(r'Quality=(\d+)/(\d+)', line)
                        if match:
                            quality = int(match.group(1))
                            max_quality = int(match.group(2))
                            signal = int((quality / max_quality) * 100)
                            current_network['signal'] = str(signal)
                    elif 'Encryption key:' in line:
                        if 'off' in line:
                            current_network['security'] = 'Open'
                        else:
                            current_network['security'] = 'WPA/WPA2'
                        
                        if 'ssid' in current_network:
                            networks.append(current_network.copy())
                            current_network = {}
                
                return {'success': True, 'networks': networks}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def connect_wifi(ssid, password=None):
        """连接到WiFi网络"""
        try:
            if password:
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            if result.returncode == 0:
                return {'success': True, 'message': f'成功连接到 {ssid}'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def disconnect_wifi():
        """断开WiFi连接"""
        try:
            result = subprocess.run(
                ['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': 'WiFi已断开'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_network_interfaces():
        """获取网络接口信息"""
        try:
            result = subprocess.run(
                ['ip', '-j', 'addr', 'show'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                interfaces = json.loads(result.stdout)
                interface_list = []
                
                for iface in interfaces:
                    info = {
                        'name': iface.get('ifname'),
                        'state': iface.get('operstate', 'unknown'),
                        'addresses': []
                    }
                    
                    for addr in iface.get('addr_info', []):
                        if addr.get('family') in ['inet', 'inet6']:
                            info['addresses'].append({
                                'family': addr.get('family'),
                                'address': addr.get('local'),
                                'prefix': addr.get('prefixlen')
                            })
                    
                    interface_list.append(info)
                
                return {'success': True, 'interfaces': interface_list}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def set_static_ip(interface, ip_address, netmask, gateway, dns):
        """设置静态IP（需要修改配置文件）"""
        try:
            # 使用 nmcli 设置静态IP
            commands = [
                ['sudo', 'nmcli', 'connection', 'modify', interface, 'ipv4.method', 'manual'],
                ['sudo', 'nmcli', 'connection', 'modify', interface, 'ipv4.addresses', f'{ip_address}/{netmask}'],
                ['sudo', 'nmcli', 'connection', 'modify', interface, 'ipv4.gateway', gateway],
                ['sudo', 'nmcli', 'connection', 'modify', interface, 'ipv4.dns', dns],
                ['sudo', 'nmcli', 'connection', 'up', interface]
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    return {'success': False, 'error': result.stderr}
            
            return {'success': True, 'message': '静态IP配置成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def set_dhcp(interface):
        """设置为DHCP"""
        try:
            commands = [
                ['sudo', 'nmcli', 'connection', 'modify', interface, 'ipv4.method', 'auto'],
                ['sudo', 'nmcli', 'connection', 'up', interface]
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    return {'success': False, 'error': result.stderr}
            
            return {'success': True, 'message': 'DHCP配置成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_firewall_status():
        """获取防火墙状态"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', 'status', 'numbered'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            status = 'inactive'
            rules = []
            
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Status:' in line:
                    status = 'active' if 'active' in line.lower() else 'inactive'
                elif re.match(r'\[\s*\d+\]', line):
                    # 解析规则
                    rules.append(line.strip())
            
            return {'success': True, 'status': status, 'rules': rules}
        except FileNotFoundError:
            return {'success': False, 'error': 'UFW未安装'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def enable_firewall():
        """启用防火墙"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', '--force', 'enable'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': '防火墙已启用'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def disable_firewall():
        """禁用防火墙"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', 'disable'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': '防火墙已禁用'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_firewall_rule(port, protocol='tcp', action='allow'):
        """添加防火墙规则"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', action, f'{port}/{protocol}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': f'规则已添加: {action} {port}/{protocol}'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_firewall_rule(rule_number):
        """删除防火墙规则"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', '--force', 'delete', str(rule_number)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': f'规则 {rule_number} 已删除'}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_listening_ports():
        """获取监听端口列表"""
        try:
            result = subprocess.run(
                ['ss', '-tulnp'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            ports = []
            lines = result.stdout.split('\n')[1:]  # 跳过标题
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        protocol = parts[0]
                        local_address = parts[4]
                        process = parts[6] if len(parts) > 6 else '-'
                        
                        # 提取端口
                        if ':' in local_address:
                            port = local_address.split(':')[-1]
                            address = ':'.join(local_address.split(':')[:-1])
                            
                            ports.append({
                                'protocol': protocol,
                                'address': address,
                                'port': port,
                                'process': process
                            })
            
            return {'success': True, 'ports': ports}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_network_connections():
        """获取网络连接状态"""
        try:
            result = subprocess.run(
                ['ss', '-tunap'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            connections = {'ESTABLISHED': 0, 'LISTEN': 0, 'TIME_WAIT': 0, 'CLOSE_WAIT': 0, 'OTHER': 0}
            connection_list = []
            
            lines = result.stdout.split('\n')[1:]  # 跳过标题
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        state = parts[1]
                        protocol = parts[0]
                        local = parts[4]
                        remote = parts[5]
                        process = parts[6] if len(parts) > 6 else '-'
                        
                        if state in connections:
                            connections[state] += 1
                        else:
                            connections['OTHER'] += 1
                        
                        connection_list.append({
                            'protocol': protocol,
                            'state': state,
                            'local': local,
                            'remote': remote,
                            'process': process
                        })
            
            return {'success': True, 'summary': connections, 'connections': connection_list[:100]}  # 限制返回100条
        except Exception as e:
            return {'success': False, 'error': str(e)}
