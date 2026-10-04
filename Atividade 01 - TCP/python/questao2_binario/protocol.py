"""
Módulo de Protocolo Binário TCP (Questão 2)
Especificação estrita conforme PDF da Atividade 1:

Solicitações (Request - Message Type 0x01):
  - 1 byte: Message Type (0x01)
  - 1 byte: Command Identifier (0x01 = ADDFILE, 0x02 = DELETE, 0x03 = GETFILESLIST, 0x04 = GETFILE)
  - 1 byte: Filename Size (0 a 255)
  - N bytes: Filename (codificado em UTF-8)
  Campos extras:
  - Para ADDFILE (1):
      - 4 bytes: Tamanho do arquivo em bytes (big endian - >I)
      - N bytes: Conteúdo do arquivo (enviado e recebido byte a byte/chunks)

Respostas (Response - Message Type 0x02):
  - 1 byte: Message Type (0x02)
  - 1 byte: Command Identifier (0x01 a 0x04)
  - 1 byte: Status Code (0x01 = SUCCESS, 0x02 = ERROR)
  Campos extras:
  - Para GETFILESLIST (3):
      - 2 bytes: Número de arquivos (big endian - >H)
      - Repete-se para cada arquivo:
          - 1 byte: Tamanho do nome (1-255)
          - N bytes: Nome do arquivo
  - Para GETFILE (4) [em caso de SUCCESS]:
      - 4 bytes: Tamanho do arquivo em bytes (big endian - >I)
      - N bytes: Conteúdo do arquivo
"""

import socket
import struct

# Tipos de Mensagem
MSG_TYPE_REQ = 0x01
MSG_TYPE_RESP = 0x02

# Identificadores de Comandos
CMD_ADDFILE = 0x01
CMD_DELETE = 0x02
CMD_GETFILESLIST = 0x03
CMD_GETFILE = 0x04

# Códigos de Status
STATUS_SUCCESS = 0x01
STATUS_ERROR = 0x02

def recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Recebe exatamente `num_bytes` do socket TCP.
    Garante que não ocorram leituras parciais devido à segmentação do stream TCP.
    """
    data = bytearray()
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            raise ConnectionError(f"Conexão encerrada inesperadamente esperando {num_bytes - len(data)} bytes.")
        data.extend(packet)
    return bytes(data)

def send_stream(sock: socket.socket, stream, total_bytes: int, chunk_size: int = 4096) -> None:
    """Envia dados de um stream/arquivo em blocos através do socket."""
    sent = 0
    while sent < total_bytes:
        to_read = min(chunk_size, total_bytes - sent)
        chunk = stream.read(to_read)
        if not chunk:
            break
        sock.sendall(chunk)
        sent += len(chunk)

def recv_to_file(sock: socket.socket, dest_file, total_bytes: int, chunk_size: int = 4096) -> None:
    """Recebe dados do socket e grava em um arquivo em disco."""
    received = 0
    while received < total_bytes:
        to_read = min(chunk_size, total_bytes - received)
        chunk = sock.recv(to_read)
        if not chunk:
            raise ConnectionError("Conexão interrompida durante recepção do arquivo.")
        dest_file.write(chunk)
        received += len(chunk)
