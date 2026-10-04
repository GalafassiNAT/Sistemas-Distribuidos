"""
Módulo de Protocolo UDP para Upload de Arquivos (Questão 2)
Especificação do Protocolo:
1. Pacote START (Início da transferência):
   - [1 byte: PKT_TYPE = 0x01]
   - [4 bytes: transfer_id (uint32 big-endian)]
   - [8 bytes: total_file_size (uint64 big-endian)]
   - [2 bytes: filename_len (uint16 big-endian)]
   - [N bytes: filename UTF-8]

2. Pacote DATA (Partes do arquivo):
   - [1 byte: PKT_TYPE = 0x02]
   - [4 bytes: transfer_id (uint32 big-endian)]
   - [4 bytes: chunk_seq (uint32 big-endian, indexado a partir de 0)]
   - [2 bytes: chunk_size (uint16 big-endian, até 1024 bytes)]
   - [M bytes: chunk_bytes (payload bruto, 1024 bytes exceto o último)]

3. Pacote END (Fim da transferência com Checksum SHA-1):
   - [1 byte: PKT_TYPE = 0x03]
   - [4 bytes: transfer_id (uint32 big-endian)]
   - [4 bytes: total_chunks (uint32 big-endian)]
   - [20 bytes: checksum_sha1 (digest bruto de 20 bytes)]

4. Pacote ACK (Confirmação do Servidor para o Cliente):
   - [1 byte: PKT_TYPE = 0x04]
   - [4 bytes: transfer_id (uint32 big-endian)]
   - [1 byte: status_code (0x01 = SUCCESS, 0x02 = ERROR, 0x03 = CHECKSUM_MISMATCH)]
   - [4 bytes: ack_seq (seq do último bloco processado ou transfer_id)]
"""

import struct
import hashlib

PKT_START = 0x01
PKT_DATA = 0x02
PKT_END = 0x03
PKT_ACK = 0x04

STATUS_SUCCESS = 0x01
STATUS_ERROR = 0x02
STATUS_CHECKSUM_MISMATCH = 0x03

CHUNK_PAYLOAD_SIZE = 1024

def build_start_packet(transfer_id: int, file_size: int, filename: str) -> bytes:
    name_bytes = filename.encode("utf-8")
    header = struct.pack(">BQI H", PKT_START, file_size, transfer_id, len(name_bytes))
    # Para consistência:
    # 1 byte: tipo
    # 4 bytes: transfer_id
    # 8 bytes: file_size
    # 2 bytes: len(name)
    raw = struct.pack(">BIQH", PKT_START, transfer_id, file_size, len(name_bytes)) + name_bytes
    return raw

def parse_start_packet(data: bytes):
    if len(data) < 15:
        raise ValueError("Pacote START incompleto.")
    pkt_type, transfer_id, file_size, name_len = struct.unpack(">BIQH", data[:15])
    filename = data[15:15 + name_len].decode("utf-8", errors="replace")
    return transfer_id, file_size, filename

def build_data_packet(transfer_id: int, chunk_seq: int, payload: bytes) -> bytes:
    header = struct.pack(">BIIH", PKT_DATA, transfer_id, chunk_seq, len(payload))
    return header + payload

def parse_data_packet(data: bytes):
    if len(data) < 11:
        raise ValueError("Pacote DATA incompleto.")
    pkt_type, transfer_id, chunk_seq, chunk_size = struct.unpack(">BIIH", data[:11])
    payload = data[11:11 + chunk_size]
    return transfer_id, chunk_seq, payload

def build_end_packet(transfer_id: int, total_chunks: int, sha1_digest: bytes) -> bytes:
    header = struct.pack(">BII", PKT_END, transfer_id, total_chunks)
    return header + sha1_digest[:20]

def parse_end_packet(data: bytes):
    if len(data) < 9 + 20:
        raise ValueError("Pacote END incompleto.")
    pkt_type, transfer_id, total_chunks = struct.unpack(">BII", data[:9])
    sha1_digest = data[9:29]
    return transfer_id, total_chunks, sha1_digest

def build_ack_packet(transfer_id: int, status_code: int, ack_seq: int) -> bytes:
    return struct.pack(">BIBI", PKT_ACK, transfer_id, status_code, ack_seq)

def parse_ack_packet(data: bytes):
    if len(data) < 10:
        raise ValueError("Pacote ACK incompleto.")
    pkt_type, transfer_id, status_code, ack_seq = struct.unpack(">BIBI", data[:10])
    return transfer_id, status_code, ack_seq
