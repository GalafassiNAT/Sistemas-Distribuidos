# Atividade 01 - Programação com Sockets TCP
Sistemas Distribuídos – Prof. Rodrigo Campiolo

Status: **Concluída - Pendente teste interlinguagens (com implementação em Go)**

---

## Estrutura do Diretório
- `questao1_textual/`:
  - `protocol.py`: Definição de mensagens UTF-8, tratamento de quebra de linha `\n` e hashing de senha SHA-512.
  - `server.py`: Servidor TCP multithreaded que suporta múltiplos clientes simultâneos, autenticação e navegação no diretório. Aceita flags `--host`, `--port` e `--storage`.
  - `client.py`: Cliente TCP interativo e programático. Aceita flags `--host` e `--port`.
  - `test_tcp_textual.py`: Bateria de testes automatizados completa.
- `questao2_binario/`:
  - `protocol.py`: Especificação binária estrita dos cabeçalhos de requisição e resposta com ordenação Big-Endian (`>B`, `>H`, `>I`).
  - `server.py`: Servidor TCP com manipulação de arquivos remotos (`ADDFILE`, `DELETE`, `GETFILESLIST`, `GETFILE`) e sistema de log nativo em arquivo (`server_binary.log`) e console.
  - `client.py`: Cliente TCP binário para upload, listagem, remoção e download de arquivos com pasta padrão configurável.
  - `test_tcp_binario.py`: Bateria de testes automatizados com arquivos de texto e binários arbitrários.

---

## Como Executar

### Questão 1 (TCP Textual)
1. Iniciar o servidor (por padrão na porta 8001):
   ```bash
   python server.py --host 0.0.0.0 --port 8001
   ```
2. Iniciar o cliente:
   ```bash
   python client.py --host 127.0.0.1 --port 8001
   ```
3. Executar o teste automatizado:
   ```bash
   python test_tcp_textual.py
   ```

### Questão 2 (TCP Binário)
1. Iniciar o servidor (por padrão na porta 8002):
   ```bash
   python server.py --host 0.0.0.0 --port 8002
   ```
2. Iniciar o cliente:
   ```bash
   python client.py --host 127.0.0.1 --port 8002
   ```
3. Executar o teste automatizado:
   ```bash
   python test_tcp_binario.py
   ```
