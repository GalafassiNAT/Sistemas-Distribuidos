"""
Servidor UDP para Upload de Arquivos (Questão 2)
Requisitos atendidos:
- Recebe partes de arquivos de 1024 bytes via UDP
- Confere o checksum SHA-1 ao término da transmissão
- Armazena o arquivo reconstruído em pasta padrão configurável
- Suporta transferências concorrentes através de transfer_id (uint32)
- Registra logs detalhados: horário de início, término, nome, tamanho e origem
"""

import os
import sys
import time
import socket
import hashlib
import logging
import argparse
from datetime import datetime
from protocol import (
    PKT_START, PKT_DATA, PKT_END, PKT_ACK,
    STATUS_SUCCESS, STATUS_ERROR, STATUS_CHECKSUM_MISMATCH,
    parse_start_packet, parse_data_packet, parse_end_packet,
    build_ack_packet
)

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("server_upload_udp.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("UDPUploadServer")

class TransferSession:
    def __init__(self, transfer_id: int, filename: str, file_size: int, client_addr: tuple, storage_dir: str):
        self.transfer_id = transfer_id
        self.filename = os.path.basename(filename)
        self.file_size = file_size
        self.client_addr = client_addr
        self.storage_dir = storage_dir
        self.start_time = datetime.now()
        self.received_chunks = {} # seq -> bytes
        self.temp_filepath = os.path.join(storage_dir, f".tmp_{transfer_id}_{self.filename}")

class UDPUploadServer:
    def __init__(self, host: str, port: int, storage_dir: str = "./received_files"):
        self.host = host
        self.port = port
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.running = False
        self.sessions = {} # transfer_id -> TransferSession

    def start(self):
        self.running = True
        logger.info(f"Servidor UDP de Upload ativo em {self.host}:{self.port}")
        logger.info(f"Diretório de salvamento: {self.storage_dir}")

        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                if not data:
                    continue

                pkt_type = data[0]

                if pkt_type == PKT_START:
                    self._handle_start(data, addr)
                elif pkt_type == PKT_DATA:
                    self._handle_data(data, addr)
                elif pkt_type == PKT_END:
                    self._handle_end(data, addr)
                else:
                    logger.warning(f"Tipo de pacote desconhecido: {pkt_type} de {addr}")

            except OSError:
                break
            except Exception as e:
                logger.error(f"Erro no processamento UDP: {e}", exc_info=True)

    def _handle_start(self, data: bytes, addr: tuple):
        transfer_id, file_size, filename = parse_start_packet(data)
        session = TransferSession(transfer_id, filename, file_size, addr, self.storage_dir)
        self.sessions[transfer_id] = session

        logger.info(f"[INÍCIO] Transferência ID {transfer_id} iniciada de {addr[0]}:{addr[1]}")
        logger.info(f"         Arquivo: '{session.filename}', Tamanho: {file_size} bytes")

        # Envia ACK do START
        ack = build_ack_packet(transfer_id, STATUS_SUCCESS, 0)
        self.sock.sendto(ack, addr)

    def _handle_data(self, data: bytes, addr: tuple):
        transfer_id, chunk_seq, payload = parse_data_packet(data)
        session = self.sessions.get(transfer_id)
        if not session:
            # Sessão desconhecida
            ack = build_ack_packet(transfer_id, STATUS_ERROR, chunk_seq)
            self.sock.sendto(ack, addr)
            return

        session.received_chunks[chunk_seq] = payload

        # Responde ACK do bloco
        ack = build_ack_packet(transfer_id, STATUS_SUCCESS, chunk_seq)
        self.sock.sendto(ack, addr)

    def _handle_end(self, data: bytes, addr: tuple):
        transfer_id, total_chunks, expected_sha1 = parse_end_packet(data)
        session = self.sessions.get(transfer_id)

        if not session:
            ack = build_ack_packet(transfer_id, STATUS_ERROR, 0)
            self.sock.sendto(ack, addr)
            return

        end_time = datetime.now()
        duration = (end_time - session.start_time).total_seconds()

        # Reconstrução ordenada das partes
        reconstructed = bytearray()
        missing = False
        for seq in range(total_chunks):
            if seq not in session.received_chunks:
                logger.error(f"[TRANSFER {transfer_id}] Faltando chunk #{seq} de {total_chunks}")
                missing = True
                break
            reconstructed.extend(session.received_chunks[seq])

        if missing:
            ack = build_ack_packet(transfer_id, STATUS_ERROR, 0)
            self.sock.sendto(ack, addr)
            return

        # Verificação do Checksum SHA-1
        calc_sha1 = hashlib.sha1(reconstructed).digest()

        if calc_sha1 != expected_sha1:
            logger.error(f"[TRANSFER {transfer_id}] Falha de integridade! Checksum SHA-1 não confere.")
            logger.error(f"  Esperado: {expected_sha1.hex()}")
            logger.error(f"  Calculado: {calc_sha1.hex()}")
            ack = build_ack_packet(transfer_id, STATUS_CHECKSUM_MISMATCH, 0)
            self.sock.sendto(ack, addr)
            return

        # Grava arquivo final em pasta padrão
        final_path = os.path.join(self.storage_dir, session.filename)
        with open(final_path, "wb") as f:
            f.write(reconstructed)

        logger.info(f"[TÉRMINO] Transferência ID {transfer_id} CONCLUÍDA com sucesso!")
        logger.info(f"          Origem: {session.client_addr[0]}:{session.client_addr[1]}")
        logger.info(f"          Arquivo: {session.filename} salvo em {final_path}")
        logger.info(f"          Tamanho: {len(reconstructed)} bytes")
        logger.info(f"          SHA-1: {calc_sha1.hex()}")
        logger.info(f"          Tempo de transferência: {duration:.3f} s")

        # Limpa sessão da memória
        del self.sessions[transfer_id]

        # Envia ACK final de SUCESSO
        ack = build_ack_packet(transfer_id, STATUS_SUCCESS, total_chunks)
        self.sock.sendto(ack, addr)

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser(description="Servidor UDP de Upload de Arquivos (Questão 2)")
    parser.add_argument("--host", default="0.0.0.0", help="IP para escuta (padrão: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9005, help="Porta UDP (padrão: 9005)")
    parser.add_argument("--storage", default="./server_received_files", help="Pasta de armazenamento padrão")
    args = parser.parse_args()

    server = UDPUploadServer(args.host, args.port, args.storage)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[*] Encerrando servidor UDP...")
        server.stop()

if __name__ == "__main__":
    main()
