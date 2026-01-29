┌─────────────────────────────────────────────────────────────────┐
│                      SEGURANÇA DO GHOST-BRIDGE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CRIPTOGRAFIA END-TO-END (AES-256)                          │
│     ├── Comandos criptografados ANTES de ir pro Discord        │
│     ├── Respostas criptografadas ANTES de ir pro Sheets        │
│     └── Nem Microsoft nem Google conseguem ler                  │
│                                                                 │
│  2. TRÁFEGO "LEGÍTIMO"                                         │
│     ├── Discord = App de comunicação comum                      │
│     ├── Google Sheets = Ferramenta de produtividade             │
│     └── Ambos usam HTTPS (porta 443)                            │
│                                                                 │
│  3. JITTER (Anti-Padrão)                                       │
│     ├── Polling varia entre 2-5 segundos (configurável)         │
│     └── Evita detecção por análise de tráfego                   │
│                                                                 │
│  4. SEPARAÇÃO DE CANAIS                                        │
│     ├── Downlink (Comandos) = Discord                           │
│     ├── Uplink (Dados) = Google Sheets                          │
│     └── Dificulta correlação                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘