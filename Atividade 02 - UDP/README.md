# Atividade 02 - Programação com Sockets UDP
Sistemas Distribuídos – Prof. Rodrigo Campiolo

Status: **Concluída - Pendente teste interlinguagens (com implementação em Go)**

---

## Estrutura do Diretório
- `questao1_chat_p2p/`:
  - `protocol.py`: Especificação binária estrita dos pacotes do Chat P2P:
    - `Tipo (1B)` + `Tam Nick (1B)` + `Nick (N B)` + `Tam Msg (1B)` + `Msg (M B)`.
    - Tipos: 1 = normal, 2 = emoji, 3 = URL, 4 = ECHO.
  - `p2p_node.py`: Nó P2P completo atuando simultaneamente como receptor (thread dedicada) e emissor, com suporte a comandos `/msg`, `/emoji`, `/url`, `/echo` e `/target`. Responde automaticamente a requisições de ECHO (liveness check).
  - `test_p2p_chat.py`: Bateria de testes automatizados com dois nós simultâneos (Alice e Bob).
- `questao2_upload/`:
  - `protocol.py`: Protocolo de transferência em datagramas UDP em blocos de 1024 bytes, cabeçalhos `START`, `DATA`, `END` (com SHA-1 digest) e `ACK` do servidor.
  - `server.py`: Servidor UDP com suporte a transferências simultâneas identificadas por `transfer_id`, cálculo e validação de Checksum SHA-1 e logs detalhados (data, início, término, tamanho, arquivo, origem).
  - `client.py`: Cliente UDP com fragmentação em 1024 bytes, retransmissão por timeout (ARQ) e barra de progresso visual.
  - `test_udp_upload.py`: Bateria de testes automatizados com arquivos de 100 bytes, 4 KiB e 1 MiB.

---

## Como Executar

### Questão 1 (Chat P2P UDP)
1. Iniciar o Peer A (escutando na 9001 e enviando para a 9002):
   ```bash
   python p2p_node.py --nick Alice --bind-port 9001 --target-port 9002
   ```
2. Iniciar o Peer B (escutando na 9002 e enviando para a 9001):
   ```bash
   python p2p_node.py --nick Bob --bind-port 9002 --target-port 9001
   ```
3. Executar o teste automatizado:
   ```bash
   python test_p2p_chat.py
   ```

### Questão 2 (Upload de Arquivos UDP)
1. Iniciar o servidor UDP (por padrão na porta 9005):
   ```bash
   python server.py --host 0.0.0.0 --port 9005
   ```
2. Iniciar o upload de um arquivo:
   ```bash
   python client.py caminho/do/arquivo.ext --host 127.0.0.1 --port 9005
   ```
3. Executar o teste automatizado:
   ```bash
   python test_udp_upload.py
   ```
