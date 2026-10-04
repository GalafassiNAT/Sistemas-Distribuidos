"""
Cliente TCP com Protocolo Binário (Questão 2)
Interage com o servidor para:
- ADDFILE (1): envia arquivo local ao servidor
- DELETE (2): solicita remoção de arquivo
- GETFILESLIST (3): lista arquivos remotos
- GETFILE (4): baixa arquivo do servidor gravando em pasta padrão
"""

import os
import sys
import socket
import struct
import argparse
from protocol import (
    MSG_TYPE_REQ, MSG_TYPE_RESP,
    CMD_ADDFILE, CMD_DELETE, CMD_GETFILESLIST, CMD_GETFILE,
    STATUS_SUCCESS, STATUS_ERROR,
    recv_exact, send_stream, recv_to_file
)

class TCPBinaryClient:
    def __init__(self, host: str, port: int, download_dir: str = "./downloads"):
        self.host = host
        self.port = port
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _send_req_header(self, cmd_id: int, filename: str):
        fn_bytes = filename.encode("utf-8")[:255]
        hdr = struct.pack(">BBB", MSG_TYPE_REQ, cmd_id, len(fn_bytes))
        self.sock.sendall(hdr + fn_bytes)

    def _recv_resp_header(self):
        hdr = recv_exact(self.sock, 3)
        msg_type, cmd_id, status_code = struct.unpack(">BBB", hdr)
        return msg_type, cmd_id, status_code

    def add_file(self, local_path: str, remote_name: str = None) -> bool:
        """Envia um arquivo local para o servidor."""
        if not os.path.exists(local_path):
            print(f"[!] Arquivo local não encontrado: {local_path}")
            return False

        if not remote_name:
            remote_name = os.path.basename(local_path)

        file_size = os.path.getsize(local_path)
        self._send_req_header(CMD_ADDFILE, remote_name)

        # 4 bytes de tamanho em Big Endian
        self.sock.sendall(struct.pack(">I", file_size))

        # Envio dos bytes do arquivo
        with open(local_path, "rb") as f:
            send_stream(self.sock, f, file_size)

        _, _, status = self._recv_resp_header()
        return status == STATUS_SUCCESS

    def delete_file(self, remote_name: str) -> bool:
        """Solicita exclusão de um arquivo no servidor."""
        self._send_req_header(CMD_DELETE, remote_name)
        _, _, status = self._recv_resp_header()
        return status == STATUS_SUCCESS

    def get_files_list(self) -> list:
        """Solicita a lista de arquivos presentes no servidor."""
        self._send_req_header(CMD_GETFILESLIST, "")
        _, _, status = self._recv_resp_header()
        if status != STATUS_SUCCESS:
            return []

        # 2 bytes com a contagem de arquivos
        count_bytes = recv_exact(self.sock, 2)
        num_files, = struct.unpack(">H", count_bytes)

        files = []
        for _ in range(num_files):
            name_len = struct.unpack(">B", recv_exact(self.sock, 1))[0]
            name = recv_exact(self.sock, name_len).decode("utf-8", errors="replace")
            files.append(name)
        return files

    def get_file(self, remote_name: str, dest_dir: str = None) -> str:
        """Baixa um arquivo do servidor gravando em pasta padrão."""
        if dest_dir is None:
            dest_dir = self.download_dir

        self._send_req_header(CMD_GETFILE, remote_name)
        _, _, status = self._recv_resp_header()
        if status != STATUS_SUCCESS:
            return None

        # 4 bytes de tamanho do arquivo
        size_bytes = recv_exact(self.sock, 4)
        file_size, = struct.unpack(">I", size_bytes)

        safe_name = os.path.basename(remote_name)
        dest_path = os.path.join(dest_dir, safe_name)

        with open(dest_path, "wb") as f:
            recv_to_file(self.sock, f, file_size)

        return dest_path

def interactive_client(host: str, port: int, download_dir: str):
    client = TCPBinaryClient(host, port, download_dir)
    try:
        client.connect()
    except Exception as e:
        print(f"[!] Não foi possível conectar ao servidor: {e}")
        return

    print("=== Cliente TCP Binário (Questão 2) ===")
    print("Comandos:")
    print("  add <caminho_local> [nome_remoto]")
    print("  del <nome_remoto>")
    print("  list")
    print("  get <nome_remoto>")
    print("  exit")
    print("---------------------------------------")

    try:
        while True:
            cmd = input("BIN-TCP> ").strip()
            if not cmd:
                continue
            parts = cmd.split()
            op = parts[0].lower()

            if op == "add":
                if len(parts) < 2:
                    print("[!] Uso: add <caminho_local> [nome_remoto]")
                    continue
                loc = parts[1]
                rem = parts[2] if len(parts) > 2 else os.path.basename(loc)
                ok = client.add_file(loc, rem)
                print("<- SUCESSO (ADDFILE)" if ok else "<- ERRO (ADDFILE)")
            elif op == "del":
                if len(parts) < 2:
                    print("[!] Uso: del <nome_remoto>")
                    continue
                ok = client.delete_file(parts[1])
                print("<- SUCESSO (DELETE)" if ok else "<- ERRO (DELETE)")
            elif op == "list":
                files = client.get_files_list()
                print(f"<- {len(files)} arquivo(s) no servidor:")
                for f in files:
                    print(f"    - {f}")
            elif op == "get":
                if len(parts) < 2:
                    print("[!] Uso: get <nome_remoto>")
                    continue
                path = client.get_file(parts[1])
                if path:
                    print(f"<- Download concluído com sucesso em: {path}")
                else:
                    print("<- ERRO ao baixar arquivo.")
            elif op == "exit":
                print("[*] Encerrando sessão...")
                break
            else:
                print(f"[!] Operação desconhecida: {op}")
    except (KeyboardInterrupt, EOFError):
        print("\n[*] Saindo...")
    finally:
        client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente TCP - Protocolo Binário (Questão 2)")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço IP do servidor")
    parser.add_argument("--port", type=int, default=8002, help="Porta TCP do servidor")
    parser.add_argument("--download-dir", default="./downloads", help="Diretório padrão para salvar downloads")
    args = parser.parse_args()
    interactive_client(args.host, args.port, args.download_dir)
