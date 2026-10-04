"""
Servidor TCP Multithreaded com Protocolo Textual (Questão 1)
Processa comandos dos clientes em formato String UTF:
- CONNECT user, password (com hash SHA-512)
- PWD
- CHDIR path
- GETFILES
- GETDIRS
- EXIT
"""

import os
import sys
import socket
import threading
import argparse
from protocol import STATUS_SUCCESS, STATUS_ERROR, send_msg, recv_msg

# Base de usuários cadastrados para simulação (usuário -> hash sha-512 da senha)
# Senhas de exemplo:
# admin: "admin123" -> hash calculado
# user1: "senha1"   -> hash calculado
import hashlib
USERS_DB = {
    "admin": hashlib.sha512("admin123".encode("utf-8")).hexdigest(),
    "user1": hashlib.sha512("senha1".encode("utf-8")).hexdigest(),
    "aluno": hashlib.sha512("sd2026".encode("utf-8")).hexdigest()
}

class ClientHandler(threading.Thread):
    def __init__(self, client_sock: socket.socket, client_addr: tuple, root_dir: str):
        super().__init__(daemon=True)
        self.sock = client_sock
        self.addr = client_addr
        self.root_dir = os.path.abspath(root_dir)
        self.current_dir = self.root_dir
        self.authenticated = False
        self.username = None
        self.buffer = {"data": ""}

    def run(self):
        print(f"[+] Conexão recebida de {self.addr[0]}:{self.addr[1]}")
        try:
            while True:
                line = recv_msg(self.sock, self.buffer)
                if line is None:
                    break

                line = line.strip()
                if not line:
                    continue

                parts = line.split(" ", 1)
                cmd = parts[0].upper()
                arg = parts[1].strip() if len(parts) > 1 else ""

                if cmd == "CONNECT":
                    self.handle_connect(arg)
                elif not self.authenticated:
                    send_msg(self.sock, f"{STATUS_ERROR}: Necessario autenticar primeiro via CONNECT user, password")
                elif cmd == "PWD":
                    self.handle_pwd()
                elif cmd == "CHDIR":
                    self.handle_chdir(arg)
                elif cmd == "GETFILES":
                    self.handle_getfiles()
                elif cmd == "GETDIRS":
                    self.handle_getdirs()
                elif cmd == "EXIT":
                    print(f"[-] Cliente {self.addr} solicitou EXIT.")
                    break
                else:
                    send_msg(self.sock, f"{STATUS_ERROR}: Comando desconhecido '{cmd}'")
        except Exception as e:
            print(f"[!] Erro na conexão {self.addr}: {e}")
        finally:
            self.sock.close()
            print(f"[-] Conexão encerrada com {self.addr}")

    def handle_connect(self, arg: str):
        """
        Formato: CONNECT user, password_hash
        Conecta o usuário à sua área se senha conferir e usuário existir.
        """
        try:
            if "," not in arg:
                send_msg(self.sock, STATUS_ERROR)
                return
            user_part, pass_hash = arg.split(",", 1)
            user = user_part.strip()
            pass_hash = pass_hash.strip().lower()

            if user in USERS_DB and USERS_DB[user] == pass_hash:
                self.authenticated = True
                self.username = user
                # Cria área pessoal do usuário se não existir
                user_home = os.path.join(self.root_dir, user)
                os.makedirs(user_home, exist_ok=True)
                self.current_dir = user_home
                print(f"[AUTH] Usuário '{user}' autenticado com sucesso.")
                send_msg(self.sock, STATUS_SUCCESS)
            else:
                print(f"[AUTH] Falha ao autenticar usuário '{user}'.")
                send_msg(self.sock, STATUS_ERROR)
        except Exception:
            send_msg(self.sock, STATUS_ERROR)

    def handle_pwd(self):
        """
        Devolve o caminho corrente (PATH) usando String UTF separando diretórios por barra(/).
        """
        try:
            # Retorna caminho relativo à raiz ou absoluto formatado com /
            rel_path = os.path.relpath(self.current_dir, self.root_dir)
            if rel_path == ".":
                path_str = "/"
            else:
                path_str = "/" + rel_path.replace("\\", "/")
            send_msg(self.sock, path_str)
        except Exception:
            send_msg(self.sock, "/")

    def handle_chdir(self, path: str):
        """
        Altera o diretório corrente para path, retornando SUCCESS ou ERROR.
        Garante que o usuário não escape da raiz do servidor.
        """
        try:
            if not path:
                send_msg(self.sock, STATUS_ERROR)
                return

            if os.path.isabs(path) or path.startswith("/"):
                # Relativo à raiz do servidor
                target_dir = os.path.abspath(os.path.join(self.root_dir, path.lstrip("/\\")))
            else:
                target_dir = os.path.abspath(os.path.join(self.current_dir, path))

            # Validação de segurança: permanecer dentro de root_dir
            if os.path.commonpath([self.root_dir]) == os.path.commonpath([self.root_dir, target_dir]):
                if os.path.isdir(target_dir):
                    self.current_dir = target_dir
                    send_msg(self.sock, STATUS_SUCCESS)
                    return
            send_msg(self.sock, STATUS_ERROR)
        except Exception:
            send_msg(self.sock, STATUS_ERROR)

    def handle_getfiles(self):
        """
        Devolve arquivos do diretório corrente:
        - Primeiro devolve um inteiro indicando o número de arquivos como String UTF
        - Depois devolve cada arquivo como uma String UTF
        """
        try:
            entries = os.listdir(self.current_dir)
            files = [f for f in entries if os.path.isfile(os.path.join(self.current_dir, f))]
            send_msg(self.sock, str(len(files)))
            for f in files:
                send_msg(self.sock, f)
        except Exception:
            send_msg(self.sock, "0")

    def handle_getdirs(self):
        """
        Devolve diretórios do diretório corrente:
        - Primeiro devolve um inteiro indicando o número de diretórios como String UTF
        - Depois devolve cada diretório como uma String UTF
        """
        try:
            entries = os.listdir(self.current_dir)
            dirs = [d for d in entries if os.path.isdir(os.path.join(self.current_dir, d))]
            send_msg(self.sock, str(len(dirs)))
            for d in dirs:
                send_msg(self.sock, d)
        except Exception:
            send_msg(self.sock, "0")

def main():
    parser = argparse.ArgumentParser(description="Servidor TCP - Protocolo Textual (Questão 1)")
    parser.add_argument("--host", default="0.0.0.0", help="Endereço IP para bind (padrão: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="Porta TCP para escuta (padrão: 8001)")
    parser.add_argument("--storage", default="./server_storage", help="Diretório raiz de armazenamento")
    args = parser.parse_args()

    os.makedirs(args.storage, exist_ok=True)
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_sock.bind((args.host, args.port))
        server_sock.listen(10)
        print(f"[*] Servidor TCP Textual rodando em {args.host}:{args.port}")
        print(f"[*] Diretório de armazenamento: {os.path.abspath(args.storage)}")

        while True:
            client_sock, client_addr = server_sock.accept()
            handler = ClientHandler(client_sock, client_addr, args.storage)
            handler.start()
    except KeyboardInterrupt:
        print("\n[*] Encerrando servidor TCP...")
    finally:
        server_sock.close()

if __name__ == "__main__":
    main()
