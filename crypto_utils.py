"""
Ghost-Bridge - Utilitários de Criptografia
Usa AES-256 (Fernet) para criptografar todo o tráfego C2.
"""
from cryptography.fernet import Fernet
import os
import config

# Nome do arquivo que guarda a chave secreta
KEY_FILE = "secret.key"


def load_or_generate_key():
    """
    Carrega a chave de criptografia na seguinte ordem de prioridade:
    1. Variável de ambiente ENCRYPTION_KEY (do .env)
    2. Arquivo local secret.key
    3. Gera uma nova chave (apenas em desenvolvimento)
    
    Em produção, a mesma chave deve estar no agente e no controlador.
    """
    # 1. Tenta carregar do .env
    env_key = config.ENCRYPTION_KEY
    if env_key:
        print("[*] Usando chave de criptografia do .env")
        return env_key.encode('utf-8')
    
    # 2. Tenta carregar do arquivo
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    
    # 3. Gera nova chave (apenas primeira execução / dev)
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
    
    print(f"[*] Nova chave de criptografia gerada: {KEY_FILE}")
    print(f"[!] IMPORTANTE: Copie esta chave para o .env em produção:")
    print(f"    ENCRYPTION_KEY={key.decode('utf-8')}")
    
    return key


# Inicializa a engine de criptografia
_key = load_or_generate_key()
_cipher = Fernet(_key)


def encrypt_data(data: str) -> str:
    """
    Criptografa uma string e retorna string base64.
    
    Args:
        data: Texto plano para criptografar
        
    Returns:
        Token Fernet (base64) que pode ser salvo em JSON/transmitido
    """
    if not data:
        return ""
    
    # Fernet precisa de bytes
    encrypted_bytes = _cipher.encrypt(data.encode('utf-8'))
    
    # Retorna como string para ser salvo no JSON/APIs
    return encrypted_bytes.decode('utf-8')


def decrypt_data(token: str) -> str:
    """
    Descriptografa um token Fernet e retorna a string original.
    
    Args:
        token: Token Fernet (base64) para descriptografar
        
    Returns:
        Texto plano original ou mensagem de erro
    """
    if not token:
        return ""
    
    try:
        decrypted_bytes = _cipher.decrypt(token.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    
    except Exception as e:
        print(f"[!] Erro de descriptografia: {e}")
        return "[ERRO: DADOS CORROMPIDOS OU CHAVE INVÁLIDA]"


def get_key_for_export() -> str:
    """
    Retorna a chave atual em formato string para exportação.
    Útil para copiar para o .env de outras instâncias.
    """
    return _key.decode('utf-8')
