"""
Ghost-Bridge - System Recon Module
Coleta informações detalhadas do sistema.
"""
import os
import socket
import platform
import subprocess
import json
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


class SystemRecon:
    """
    Reconhecimento completo do sistema alvo.
    
    Features:
    - Informações de hardware/software
    - Rede (interfaces, conexões, ARP)
    - Processos ativos
    - Usuários e privilégios
    - Software instalado
    - Antivírus detectado
    """
    
    def __init__(self):
        self.wmi_client = None
        if WMI_AVAILABLE:
            try:
                self.wmi_client = wmi.WMI()
            except:
                pass
    
    def get_system_info(self):
        """Informações básicas do sistema."""
        info = {
            'hostname': socket.gethostname(),
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'username': os.environ.get('USERNAME', os.environ.get('USER', 'unknown')),
            'domain': os.environ.get('USERDOMAIN', 'WORKGROUP'),
            'home_dir': os.path.expanduser('~'),
            'temp_dir': os.environ.get('TEMP', '/tmp'),
        }
        
        # CPUs e RAM
        if PSUTIL_AVAILABLE:
            info['cpu_count'] = psutil.cpu_count()
            info['cpu_percent'] = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            info['ram_total_gb'] = round(mem.total / (1024**3), 2)
            info['ram_available_gb'] = round(mem.available / (1024**3), 2)
            info['ram_percent'] = mem.percent
        
        return info
    
    def get_network_info(self):
        """Informações de rede."""
        network = {
            'hostname': socket.gethostname(),
            'fqdn': socket.getfqdn(),
            'interfaces': [],
            'connections': [],
            'arp_table': []
        }
        
        # Interfaces de rede
        if PSUTIL_AVAILABLE:
            for iface, addrs in psutil.net_if_addrs().items():
                iface_info = {'name': iface, 'addresses': []}
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        iface_info['addresses'].append({
                            'type': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                    elif addr.family == socket.AF_INET6:
                        iface_info['addresses'].append({
                            'type': 'IPv6',
                            'address': addr.address
                        })
                if iface_info['addresses']:
                    network['interfaces'].append(iface_info)
            
            # Conexões ativas
            try:
                for conn in psutil.net_connections()[:50]:
                    if conn.status == 'ESTABLISHED':
                        network['connections'].append({
                            'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                            'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                            'status': conn.status,
                            'pid': conn.pid
                        })
            except:
                pass
        
        # Tabela ARP
        try:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            network['arp_raw'] = result.stdout
        except:
            pass
        
        return network
    
    def get_processes(self, limit=50):
        """Lista de processos ativos."""
        processes = []
        
        if PSUTIL_AVAILABLE:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'user': info['username'],
                        'cpu': info['cpu_percent'],
                        'memory': round(info['memory_percent'], 2)
                    })
                except:
                    pass
            
            # Ordena por uso de memória
            processes.sort(key=lambda x: x.get('memory', 0), reverse=True)
            return processes[:limit]
        
        return processes
    
    def get_users(self):
        """Usuários do sistema."""
        users = {
            'current': os.environ.get('USERNAME', 'unknown'),
            'domain': os.environ.get('USERDOMAIN', 'WORKGROUP'),
            'logged_in': [],
            'local_users': [],
            'admin_group': []
        }
        
        # Usuários logados
        if PSUTIL_AVAILABLE:
            for user in psutil.users():
                users['logged_in'].append({
                    'name': user.name,
                    'terminal': user.terminal,
                    'host': user.host,
                    'started': datetime.fromtimestamp(user.started).isoformat()
                })
        
        # Usuários locais (Windows)
        try:
            result = subprocess.run(['net', 'user'], capture_output=True, text=True)
            users['local_users_raw'] = result.stdout
        except:
            pass
        
        # Grupo de administradores
        try:
            result = subprocess.run(
                ['net', 'localgroup', 'Administrators'],
                capture_output=True, text=True
            )
            users['admin_group_raw'] = result.stdout
        except:
            pass
        
        return users
    
    def get_installed_software(self):
        """Software instalado."""
        software = []
        
        if self.wmi_client:
            try:
                for product in self.wmi_client.Win32_Product():
                    software.append({
                        'name': product.Name,
                        'version': product.Version,
                        'vendor': product.Vendor
                    })
            except:
                pass
        
        # Fallback: registro
        if not software:
            try:
                import winreg
                paths = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
                ]
                
                for path in paths:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                    software.append({'name': name, 'version': version})
                                except:
                                    pass
                                
                                winreg.CloseKey(subkey)
                            except:
                                pass
                        winreg.CloseKey(key)
                    except:
                        pass
            except:
                pass
        
        return software[:100]  # Limita
    
    def get_antivirus(self):
        """Detecta antivírus instalados."""
        av_list = []
        
        if self.wmi_client:
            try:
                # Namespace de segurança
                security_center = wmi.WMI(namespace="root\\SecurityCenter2")
                
                for av in security_center.AntiVirusProduct():
                    av_list.append({
                        'name': av.displayName,
                        'state': av.productState,
                        'path': av.pathToSignedProductExe
                    })
            except:
                pass
        
        # Fallback: processos conhecidos
        if PSUTIL_AVAILABLE and not av_list:
            known_av = [
                'MsMpEng.exe',      # Windows Defender
                'avp.exe',          # Kaspersky
                'avgnt.exe',        # Avira
                'avgsvc.exe',       # AVG
                'mbam.exe',         # Malwarebytes
                'ccSvcHst.exe',     # Norton
                'mcshield.exe',     # McAfee
                'bdagent.exe',      # Bitdefender
                'SavService.exe',   # Sophos
            ]
            
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] in known_av:
                        av_list.append({
                            'name': proc.info['name'],
                            'detected_by': 'process'
                        })
                except:
                    pass
        
        return av_list
    
    def get_startup_programs(self):
        """Programas que iniciam com o Windows."""
        startup = []
        
        try:
            import winreg
            
            paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]
            
            for hkey, path in paths:
                try:
                    key = winreg.OpenKey(hkey, path)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup.append({
                                'name': name,
                                'command': value,
                                'location': 'HKCU' if hkey == winreg.HKEY_CURRENT_USER else 'HKLM'
                            })
                            i += 1
                        except WindowsError:
                            break
                    winreg.CloseKey(key)
                except:
                    pass
        except:
            pass
        
        return startup
    
    def get_drives(self):
        """Discos e partições."""
        drives = []
        
        if PSUTIL_AVAILABLE:
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    drives.append({
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'fstype': part.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'percent': usage.percent
                    })
                except:
                    pass
        
        return drives
    
    def full_recon(self):
        """Reconhecimento completo."""
        return {
            'timestamp': datetime.now().isoformat(),
            'system': self.get_system_info(),
            'network': self.get_network_info(),
            'users': self.get_users(),
            'processes': self.get_processes(limit=30),
            'antivirus': self.get_antivirus(),
            'startup': self.get_startup_programs(),
            'drives': self.get_drives(),
            'software': self.get_installed_software()[:50]
        }


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste do System Recon")
    
    recon = SystemRecon()
    
    print("\n[+] Sistema:")
    info = recon.get_system_info()
    for k, v in info.items():
        print(f"    {k}: {v}")
    
    print("\n[+] Rede:")
    net = recon.get_network_info()
    for iface in net['interfaces'][:3]:
        print(f"    {iface['name']}: {iface['addresses']}")
    
    print("\n[+] Antivírus:")
    avs = recon.get_antivirus()
    for av in avs:
        print(f"    {av['name']}")
