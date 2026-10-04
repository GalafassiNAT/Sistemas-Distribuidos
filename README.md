# Sistemas Distribuídos - Atividades Práticas

Repositório para as atividades práticas da disciplina de Sistemas Distribuídos (Prof. Rodrigo Campiolo).

Trabalho em dupla com implementação de comunicação entre linguagens distintas (**Python** e **Go**):
- Implementação A: **Python** (disponível nas pastas `python/`)
- Implementação B: **Go** (para inclusão da dupla nas pastas `go/`)

---

## Estrutura do Repositório

```text
├── .gitignore
├── Atividade 01 - TCP/
│   ├── Atividade 01 - TCP - v2.pdf
│   ├── README.md
│   └── python/
│       ├── questao1_textual/
│       │   ├── protocol.py
│       │   ├── server.py
│       │   ├── client.py
│       │   └── test_tcp_textual.py
│       └── questao2_binario/
│           ├── protocol.py
│           ├── server.py
│           ├── client.py
│           └── test_tcp_binario.py
│
└── Atividade 02 - UDP/
    ├── Atividade 02 - UDP_v1.pdf
    ├── README.md
    └── python/
        ├── questao1_chat_p2p/
        │   ├── protocol.py
        │   ├── p2p_node.py
        │   └── test_p2p_chat.py
        └── questao2_upload/
            ├── protocol.py
            ├── server.py
            ├── client.py
            └── test_udp_upload.py
```

---

## Atividades

### [Atividade 01 - TCP](Atividade%2001%20-%20TCP/README.md)
1. **Questão 1:** Protocolo Textual com autenticação via SHA-512, comandos `CONNECT`, `PWD`, `CHDIR`, `GETFILES`, `GETDIRS` e `EXIT`.
2. **Questão 2:** Protocolo Binário com Big-Endian (`>B`, `>H`, `>I`), transferência de arquivos remotos (`ADDFILE`, `DELETE`, `GETFILESLIST`, `GETFILE`) e logs.

### [Atividade 02 - UDP](Atividade%2002%20-%20UDP/README.md)
1. **Questão 1:** Chat P2P com datagramas para mensagens normais, emojis, URLs e ECHO (liveness check).
2. **Questão 2:** Upload de arquivos em partes de 1024 bytes com validação de integridade por Checksum SHA-1 e logs de transferência.
