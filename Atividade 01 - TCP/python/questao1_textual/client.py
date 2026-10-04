"""
Cliente TCP com Protocolo Textual (Questão 1)
Implementa interface interativa ou automatizada para se conectar ao servidor TCP
e executar os comandos:
- CONNECT user, password (calculando hash SHA-512)
- PWD
- CHDIR path
- GETFILES
- GETDIRS
- EXIT
"""

import socket
import argparse
import sys
from protocol import hash_password, send_msg, recv_msg

class TCPTextualClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self.buffer = {"data": ""}

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print(f"[*] Conectado ao servidor {self.host}:{self.port}")

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def cmd_connect(self, username: str, password: str) -> str:
        """Calcula o SHA-512 e envia 'CONNECT user, <hash_sha512>'"""
        pass_hash = hash_password(password)
        command = f"CONNECT {username}, {pass_hash}"
        send_msg(self.sock, command)
        resp = recv_msg(self.sock, self.buffer)
        return resp

    def cmd_pwd(self) -> str:
        send_msg(self.sock, "PWD")
        return recv_msg(self.sock, self.buffer)

    def cmd_chdir(self, path: str) -> str:
        send_msg(self.sock, f"CHDIR {path}")
        return recv_msg(self.sock, self.buffer)

    def cmd_getfiles(self) -> list:
        send_msg(self.sock, "GETFILES")
        count_str = recv_msg(self.sock, self.buffer)
        if not count_str or not count_str.isdigit():
            return []
        count = int(count_str)
        files = []
        for _ in range(count):
            f = recv_msg(self.sock, self.buffer)
            if f is not None:
                files.append(f)
        return files

    def cmd_getdirs(self) -> list:
        send_msg(self.sock, "GETDIRS")
        count_str = recv_msg(self.sock, self.buffer)
        if not count_str or not count_str.isdigit():
            return []
        count = int(count_str)
        dirs = []
        for _ in range(count):
            d = recv_msg(self.sock, self.buffer)
            if d is not None:
                dirs.append(d)
        return dirs

    def cmd_exit(self):
        send_msg(self.sock, "EXIT")
        self.close()

def interactive_session(host: str, port: int):
    client = TCPTextualClient(host, port)
    try:
        client.connect()
    except Exception as e:
        print(f"[!] Falha ao conectar: {e}")
        return

    print("=== Cliente TCP Textual (Questão 1) ===")
    print("Comandos disponíveis:")
    print("  CONNECT <usuario> <senha>")
    print("  PWD")
    print("  CHDIR <caminho>")
    print("  GETFILES")
    print("  GETDIRS")
    print("  EXIT")
    print("---------------------------------------")

    try:
        while True:
            cmd_line = input("TCP> ").strip()
            if not cmd_line:
                continue
            parts = cmd_line.split(" ", 1)
            action = parts[0].upper()
            args = parts[1].strip() if len(parts) > 1 else ""

            if action == "CONNECT":
                auth_parts = [p.strip() for p in args.split(" ", 1)]
                if len(auth_parts) < 2:
                    print("[!] Uso correto: CONNECT <usuario> <senha>")
                    continue
                resp = client.cmd_connect(auth_parts[0], auth_parts[1])
                print(f"<- {resp}")
            elif action == "PWD":
                resp = client.cmd_pwd()
                print(f"<- PATH: {resp}")
            elif action == "CHDIR":
                if not args:
                    print("[!] Uso correto: CHDIR <caminho>")
                    continue
                resp = client.cmd_chdir(args)
                print(f"<- {resp}")
            elif action == "GETFILES":
                files = client.cmd_getfiles()
                print(f"<- {len(files)} arquivo(s):")
                for f in files:
                    print(f"    - {f}")
            elif action == "GETDIRS":
                dirs = client.cmd_getdirs()
                print(f"<- {len(dirs)} diretório(s):")
                for d in dirs:
                    print(f"    - {d}")
            elif action == "EXIT":
                client.cmd_exit()
                print("[*] Desconectado.")
                break
            else:
                print(f"[!] Comando '{action}' não reconhecido.")
    except (KeyboardInterrupt, EOFError):
        print("\n[*] Saindo...")
        client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente TCP - Protocolo Textual (Questão 1)")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço IP do servidor (padrão: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="Porta TCP do servidor (padrão: 8001)")
    args = parser.parse_args()
    interactive_session(args.host, args.port)
