┌────────────────────────────────────────────────────────────────────────────┐
│                           FASE 1: ENTREGA (Delivery)                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Atacante                        Vítima                                   │
│   ┌──────┐                       ┌──────┐                                  │
│   │ YOU  │ ──── Phishing ────▶  │ USER │                                  │
│   └──────┘      Email/USB        └──┬───┘                                  │
│                                     │                                      │
│                                     ▼                                      │
│                              ┌─────────────┐                               │
│                              │ ghost.exe   │  (Agente disfarçado)          │
│                              │ "Relatório" │                               │
│                              └─────────────┘                               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        FASE 2: EXECUÇÃO INICIAL                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Vítima executa o arquivo:                                                │
│                                                                            │
│   1. Agente inicia silenciosamente                                         │
│   2. Registra persistência no Windows:                                     │
│      HKCU\Software\Microsoft\Windows\CurrentVersion\Run\GhostUpdater       │
│   3. Entra em modo "stealth" (polling silencioso)                          │
│                                                                            │
│   ✅ Resultado: Agente sobrevive reboot, inicia com Windows                │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    FASE 3: COMUNICAÇÃO C2 (O Truque)                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Por que é "invisível"?                                                   │
│   ─────────────────────                                                    │
│   ❌ C2 Tradicional: Agente → IP:4444 (evil-server.com)                    │
│      └── Firewall bloqueia, EDR alerta, logs suspeitos                     │
│                                                                            │
│   ✅ Ghost-Bridge: Agente → discord.com / googleapis.com                   │
│      └── Tráfego "normal", permitido, criptografado TLS                    │
│                                                                            │
│   ┌─────────────┐                              ┌─────────────┐             │
│   │   Agente    │ ◀══════ Discord API ═══════▶ │ Controlador │             │
│   │  (Vítima)   │         (Comandos)           │  (Atacante) │             │
│   └──────┬──────┘                              └──────┬──────┘             │
│          │                                            │                    │
│          │          Google Sheets API                 │                    │
│          └═══════════ (Exfiltração) ═════════════════▶│                    │
│                                                                            │
│   O Firewall vê:                                                           │
│   - Conexão para discord.com (porta 443) ← Normal, apps usam               │
│   - Conexão para sheets.googleapis.com ← Normal, Office365 usa             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      FASE 4: LOOP DE OPERAÇÃO                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CONTROLADOR (Você)                    AGENTE (Na Vítima)                 │
│   ══════════════════                    ══════════════════                 │
│                                                                            │
│   1. Você digita comando:               ┌──────────────────┐               │
│      > whoami                           │ while True:      │               │
│                                         │   poll_discord() │ ◀─ Jitter     │
│   2. Comando criptografado:             │   sleep(2-5s)    │    aleatório  │
│      AES-256("whoami") →                └────────┬─────────┘               │
│      gAAAAABlabc123...                           │                         │
│                                                  │                         │
│   3. Postado no Discord:                         │                         │
│      CMD|1706534400|gAAAAABlabc...               │                         │
│                     ↓                            │                         │
│              ┌─────────────┐                     │                         │
│              │   Discord   │ ◀───────────────────┘                         │
│              │   Channel   │    (Agente lê)                                │
│              └─────────────┘                                               │
│                                                                            │
│   4. Agente executa:                                                       │
│      decrypt("gAAAB...") → "whoami"                                        │
│      subprocess("whoami") → "CORP\john.doe"                                │
│                                                                            │
│   5. Resultado criptografado → Google Sheets:                              │
│      ┌──────────────────────────────────────────────┐                      │
│      │ Timestamp          │ Cmd_ID     │ Data       │                      │
│      │ 2026-01-29 12:40   │ 1706534400 │ gAAABx... │                      │
│      └──────────────────────────────────────────────┘                      │
│                                                                            │
│   6. Controlador lê Sheets:                                                │
│      decrypt("gAAABx...") → "CORP\john.doe"                                │
│      [+] RESPOSTA: CORP\john.doe                                           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘