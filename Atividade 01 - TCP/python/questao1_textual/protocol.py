"""
Módulo de Protocolo Textual TCP (Questão 1)
Define comandos, formatos de mensagens e funções auxiliares de envio e recebimento de strings UTF-8 delimitadas por quebra de linha.
"""

import socket
import hashlib

# Respostas padrão do servidor
STATUS_SUCCESS = "SUCCESS"
STATUS_ERROR = "ERROR"

def hash_password(password: str) -> str:
    """Gera o hash SHA-512 da senha informada em formato hexadecimal minúsculo."""
    return hashlib.sha512(password.encode("utf-8")).hexdigest()

def send_msg(sock: socket.socket, message: str) -> None:
    """
    Envia uma mensagem de texto UTF-8 delimitada por '\\n'.
    Garante que a mensagem termine em nova linha para facilitar o parsing.
    """
    if not message.endswith("\n"):
        message += "\n"
    sock.sendall(message.encode("utf-8"))

def recv_msg(sock: socket.socket, buffer_ref: dict) -> str:
    """
    Lê do socket até encontrar '\\n', acumulando no buffer fornecido.
    buffer_ref deve ser um dict do tipo {'data': ''}.
    Retorna a linha lida sem '\\n', ou None se a conexão for encerrada.
    """
    while "\n" not in buffer_ref["data"]:
        chunk = sock.recv(1024)
        if not chunk:
            # Conexão encerrada pelo outro lado
            if buffer_ref["data"]:
                line = buffer_ref["data"]
                buffer_ref["data"] = ""
                return line
            return None
        buffer_ref["data"] += chunk.decode("utf-8", errors="replace")

    line, buffer_ref["data"] = buffer_ref["data"].split("\n", 1)
    return line.strip("\r")
