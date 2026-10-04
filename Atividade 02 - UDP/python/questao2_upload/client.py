"""
Cliente UDP para Upload de Arquivos (Questão 2)
Funcionalidades:
- Fragmenta o arquivo em partes de 1024 bytes (CHUNK_PAYLOAD_SIZE)
- Calcula o checksum SHA-1 do arquivo completo
- Envia pacote START inicial, transmite os chunks com controle de retransmissão/timeout (Stop-and-Wait / ARQ confiável sobre UDP)
- Envia pacote END com o Checksum SHA-1
- Exibe barra de progresso / percentual de transferência
"""

import os
import sys
import time
import socket
import random
import hashlib
import argparse
from protocol import (
    CHUNK_PAYLOAD_SIZE,
    build_start_packet, build_data_packet, build_end_packet,
    parse_ack_packet,
    STATUS_SUCCESS, STATUS_CHECKSUM_MISMATCH
)

class UDPUploadClient:
    def __init__(self, target_host: str, target_port: int, timeout: float = 2.0, max_retries: int = 5):
        self.target_host = target_host
        self.target_port = target_port
        self.timeout = timeout
        self.max_retries = max_retries
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)

    def _send_and_wait_ack(self, packet: bytes, transfer_id: int, expected_seq: int) -> bool:
        """Envia um pacote e aguarda o respectivo ACK com retransmissão."""
        for attempt in range(self.max_retries):
            try:
                self.sock.sendto(packet, (self.target_host, self.target_port))
                resp, _ = self.sock.recvfrom(1024)
                ack_tid, status, ack_seq = parse_ack_packet(resp)

                if ack_tid == transfer_id and status == STATUS_SUCCESS:
                    return True
                elif status == STATUS_CHECKSUM_MISMATCH:
                    print("[!] Servidor reportou divergência no Checksum SHA-1!")
                    return False
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[!] Erro de socket: {e}")
                return False
        return False

    def upload_file(self, filepath: str, show_progress: bool = True) -> bool:
        if not os.path.exists(filepath):
            print(f"[!] Arquivo não encontrado: {filepath}")
            return False

        file_size = os.path.getsize(filepath)
        filename = os.path.basename(filepath)
        transfer_id = random.randint(1, 0xFFFFFFFE)

        # 1. Pré-computa o Checksum SHA-1
        hasher = hashlib.sha1()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        full_sha1 = hasher.digest()

        total_chunks = (file_size + CHUNK_PAYLOAD_SIZE - 1) // CHUNK_PAYLOAD_SIZE
        if total_chunks == 0:
            total_chunks = 1 # Arquivo vazio de 0 bytes tem 1 bloco vazio

        if show_progress:
            print(f"[*] Iniciando Upload: {filename}")
            print(f"    Tamanho: {file_size} bytes | Chunks de 1024 bytes: {total_chunks}")
            print(f"    SHA-1: {full_sha1.hex()}")

        # 2. Envia START
        start_pkt = build_start_packet(transfer_id, file_size, filename)
        if not self._send_and_wait_ack(start_pkt, transfer_id, 0):
            print("[!] Falha ao iniciar transferência com o servidor (Sem resposta ao START).")
            return False

        # 3. Envia Chunks DATA
        bytes_sent = 0
        start_time = time.time()

        with open(filepath, "rb") as f:
            for seq in range(total_chunks):
                chunk_data = f.read(CHUNK_PAYLOAD_SIZE)
                data_pkt = build_data_packet(transfer_id, seq, chunk_data)

                if not self._send_and_wait_ack(data_pkt, transfer_id, seq):
                    print(f"\n[!] Falha no envio do chunk #{seq}")
                    return False

                bytes_sent += len(chunk_data)

                if show_progress and total_chunks > 1:
                    percent = (bytes_sent / file_size) * 100 if file_size > 0 else 100
                    bar_len = 30
                    filled = int(bar_len * percent / 100)
                    bar = "=" * filled + "-" * (bar_len - filled)
                    sys.stdout.write(f"\rProgresso: [{bar}] {percent:5.1f}% ({bytes_sent}/{file_size} bytes)")
                    sys.stdout.flush()

        if show_progress and total_chunks > 1:
            sys.stdout.write("\n")

        # 4. Envia END com Checksum SHA-1
        end_pkt = build_end_packet(transfer_id, total_chunks, full_sha1)
        if not self._send_and_wait_ack(end_pkt, transfer_id, total_chunks):
            print("[!] Falha na finalização ou integridade reprovada pelo servidor.")
            return False

        elapsed = time.time() - start_time
        if show_progress:
            speed = (file_size / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            print(f"[+] Upload finalizado com SUCESSO! Tempo: {elapsed:.2f}s (~{speed:.2f} MB/s)")

        return True

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser(description="Cliente UDP para Upload de Arquivos (Questão 2)")
    parser.add_argument("file", help="Caminho do arquivo local a ser enviado")
    parser.add_argument("--host", default="127.0.0.1", help="IP do servidor UDP (padrão: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9005, help="Porta do servidor UDP (padrão: 9005)")
    args = parser.parse_args()

    client = UDPUploadClient(args.host, args.port)
    try:
        ok = client.upload_file(args.file)
        if not ok:
            sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()
