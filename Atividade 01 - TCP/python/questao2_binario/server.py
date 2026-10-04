"""
Servidor TCP com Protocolo Binário (Questão 2)
Gerencia conjunto de arquivos remotos entre múltiplos usuários.
Suporta:
- ADDFILE (1): adiciona um arquivo novo.
- DELETE (2): remove um arquivo existente.
- GETFILESLIST (3): retorna uma lista com o nome dos arquivos.
- GETFILE (4): faz download de um arquivo.

Possui sistema de logging com biblioteca padrão da linguagem (logging).
"""

import os
import sys
import socket
import threading
import struct
import logging
import argparse
from protocol import (
    MSG_TYPE_REQ, MSG_TYPE_RESP,
    CMD_ADDFILE, CMD_DELETE, CMD_GETFILESLIST, CMD_GETFILE,
    STATUS_SUCCESS, STATUS_ERROR,
    recv_exact, send_stream, recv_to_file
)

# Configuração do Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("server_binary.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("TCPServerBinary")

class BinaryClientHandler(threading.Thread):
    def __init__(self, client_sock: socket.socket, client_addr: tuple, storage_dir: str):
        super().__init__(daemon=True)
        self.sock = client_sock
        self.addr = client_addr
        self.storage_dir = os.path.abspath(storage_dir)

    def run(self):
        logger.info(f"Nova conexão iniciada de {self.addr}")
        try:
            while True:
                # 1. Lê cabeçalho comum da requisição (3 bytes)
                # 1 byte msg_type, 1 byte cmd_id, 1 byte filename_size
                header = self.sock.recv(3)
                if not header:
                    break
                if len(header) < 3:
                    header += recv_exact(self.sock, 3 - len(header))

                msg_type, cmd_id, filename_len = struct.unpack(">BBB", header)
                if msg_type != MSG_TYPE_REQ:
                    logger.warning(f"Tipo de mensagem inválido recebido: {msg_type}")
                    break

                # Lê nome do arquivo
                filename = ""
                if filename_len > 0:
                    raw_filename = recv_exact(self.sock, filename_len)
                    filename = raw_filename.decode("utf-8", errors="replace")

                logger.info(f"Requisição: Cmd={cmd_id}, Arquivo='{filename}' do cliente {self.addr}")

                if cmd_id == CMD_ADDFILE:
                    self.handle_addfile(filename)
                elif cmd_id == CMD_DELETE:
                    self.handle_delete(filename)
                elif cmd_id == CMD_GETFILESLIST:
                    self.handle_getfileslist()
                elif cmd_id == CMD_GETFILE:
                    self.handle_getfile(filename)
                else:
                    logger.warning(f"Comando desconhecido {cmd_id}")
                    self.send_response_header(cmd_id, STATUS_ERROR)

        except ConnectionError as e:
            logger.info(f"Conexão encerrada pelo cliente {self.addr}: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado no cliente {self.addr}: {e}", exc_info=True)
        finally:
            self.sock.close()
            logger.info(f"Conexão finalizada com {self.addr}")

    def send_response_header(self, cmd_id: int, status_code: int):
        """Envia o cabeçalho comum de resposta (3 bytes): [MSG_TYPE_RESP, cmd_id, status_code]"""
        hdr = struct.pack(">BBB", MSG_TYPE_RESP, cmd_id, status_code)
        self.sock.sendall(hdr)

    def handle_addfile(self, filename: str):
        try:
            # Para ADDFILE, recebem-se 4 bytes de tamanho do arquivo
            size_bytes = recv_exact(self.sock, 4)
            file_size, = struct.unpack(">I", size_bytes)
            logger.info(f"Recebendo ADDFILE: '{filename}', tamanho={file_size} bytes")

            safe_name = os.path.basename(filename)
            dest_path = os.path.join(self.storage_dir, safe_name)

            with open(dest_path, "wb") as f:
                recv_to_file(self.sock, f, file_size)

            logger.info(f"Arquivo '{safe_name}' salvo com sucesso ({file_size} bytes).")
            self.send_response_header(CMD_ADDFILE, STATUS_SUCCESS)
        except Exception as e:
            logger.error(f"Erro no ADDFILE '{filename}': {e}")
            self.send_response_header(CMD_ADDFILE, STATUS_ERROR)

    def handle_delete(self, filename: str):
        try:
            safe_name = os.path.basename(filename)
            target_path = os.path.join(self.storage_dir, safe_name)
            if os.path.exists(target_path) and os.path.isfile(target_path):
                os.remove(target_path)
                logger.info(f"Arquivo '{safe_name}' removido com sucesso.")
                self.send_response_header(CMD_DELETE, STATUS_SUCCESS)
            else:
                logger.warning(f"Tentativa de remoção falhou: '{safe_name}' não encontrado.")
                self.send_response_header(CMD_DELETE, STATUS_ERROR)
        except Exception as e:
            logger.error(f"Erro no DELETE '{filename}': {e}")
            self.send_response_header(CMD_DELETE, STATUS_ERROR)

    def handle_getfileslist(self):
        try:
            entries = [f for f in os.listdir(self.storage_dir) if os.path.isfile(os.path.join(self.storage_dir, f))]
            # Resposta comum
            self.send_response_header(CMD_GETFILESLIST, STATUS_SUCCESS)
            # 2 bytes com número de arquivos (big endian)
            num_files = len(entries)
            payload = bytearray(struct.pack(">H", num_files))
            for f in entries:
                f_bytes = f.encode("utf-8")[:255]
                payload.append(len(f_bytes))
                payload.extend(f_bytes)
            self.sock.sendall(payload)
            logger.info(f"GETFILESLIST enviado: {num_files} arquivo(s).")
        except Exception as e:
            logger.error(f"Erro no GETFILESLIST: {e}")
            self.send_response_header(CMD_GETFILESLIST, STATUS_ERROR)

    def handle_getfile(self, filename: str):
        try:
            safe_name = os.path.basename(filename)
            target_path = os.path.join(self.storage_dir, safe_name)

            if os.path.exists(target_path) and os.path.isfile(target_path):
                file_size = os.path.getsize(target_path)
                self.send_response_header(CMD_GETFILE, STATUS_SUCCESS)
                # 4 bytes de tamanho do arquivo (big endian)
                self.sock.sendall(struct.pack(">I", file_size))
                # Conteúdo do arquivo
                with open(target_path, "rb") as f:
                    send_stream(self.sock, f, file_size)
                logger.info(f"Arquivo '{safe_name}' transmitido com sucesso ({file_size} bytes).")
            else:
                logger.warning(f"Arquivo '{safe_name}' não encontrado para GETFILE.")
                self.send_response_header(CMD_GETFILE, STATUS_ERROR)
        except Exception as e:
            logger.error(f"Erro no GETFILE '{filename}': {e}")
            self.send_response_header(CMD_GETFILE, STATUS_ERROR)

def main():
    parser = argparse.ArgumentParser(description="Servidor TCP - Protocolo Binário (Questão 2)")
    parser.add_argument("--host", default="0.0.0.0", help="Endereço IP para bind (padrão: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8002, help="Porta TCP para escuta (padrão: 8002)")
    parser.add_argument("--storage", default="./server_storage", help="Diretório de armazenamento de arquivos")
    args = parser.parse_args()

    os.makedirs(args.storage, exist_ok=True)
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_sock.bind((args.host, args.port))
        server_sock.listen(10)
        logger.info(f"Servidor TCP Binário ativo em {args.host}:{args.port}")
        logger.info(f"Pasta de armazenamento: {os.path.abspath(args.storage)}")

        while True:
            client_sock, client_addr = server_sock.accept()
            handler = BinaryClientHandler(client_sock, client_addr, args.storage)
            handler.start()
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário.")
    finally:
        server_sock.close()

if __name__ == "__main__":
    main()
