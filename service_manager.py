import subprocess
import shlex

class ServiceManager:
    @staticmethod
    def get_service_status(service_name):
        """获取服务状态"""
        try:
            result = subprocess.run(
                ['systemctl', 'status', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 检查是否激活
            is_active = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True
            ).stdout.strip() == 'active'
            
            # 检查是否启用
            is_enabled = subprocess.run(
                ['systemctl', 'is-enabled', service_name],
                capture_output=True,
                text=True
            ).stdout.strip() == 'enabled'
            
            return {
                'name': service_name,
                'active': is_active,
                'enabled': is_enabled,
                'status': result.stdout
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def list_services():
        """列出所有服务"""
        try:
            result = subprocess.run(
                ['systemctl', 'list-units', '--type=service', '--all', '--no-pager'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            services = []
            for line in result.stdout.split('\n'):
                if '.service' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        services.append({
                            'name': parts[0].replace('.service', ''),
                            'loaded': parts[1],
                            'active': parts[2],
                            'sub': parts[3]
                        })
            
            return services
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def control_service(service_name, action):
        """控制服务（start/stop/restart）"""
        if action not in ['start', 'stop', 'restart', 'enable', 'disable']:
            return {'error': '无效的操作'}
        
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', action, service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {'success': True, 'message': f'{action} {service_name} 成功'}
            else:
                return {'error': result.stderr}
        except Exception as e:
            return {'error': str(e)}
