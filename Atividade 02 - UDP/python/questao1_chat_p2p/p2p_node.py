"""
Peer P2P para Chat via UDP (Questão 1)
Cada instância atua tanto como emissor quanto como receptor.
Funcionalidades:
- Escuta mensagens UDP em uma porta local (thread dedicada de recepção)
- Envia mensagens UDP diretamente para o endereço de destino (P2P)
- Suporta tipos:
    1: mensagem normal
    2: emoji (com atalhos textuais amigáveis :smile:, :heart:, etc.)
    3: URL
    4: ECHO (indica usuário ativo)
- Responde automaticamente a requisições de ECHO enviando a mesma mensagem de volta.
"""

import sys
import time
import socket
import threading
import argparse
from protocol import (
    pack_chat_message, unpack_chat_message,
    TYPE_NORMAL, TYPE_EMOJI, TYPE_URL, TYPE_ECHO, TYPE_NAMES
)

EMOJI_MAP = {
    ":smile:": "😀",
    ":happy:": "😊",
    ":laugh:": "😂",
    ":heart:": "❤️",
    ":thumbsup:": "👍",
    ":fire:": "🔥",
    ":wave:": "👋"
}

class P2PChatNode:
    def __init__(self, nickname: str, bind_host: str, bind_port: int, target_host: str = None, target_port: int = None):
        self.nickname = nickname
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.target_host = target_host
        self.target_port = target_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.bind_host, self.bind_port))
        self.running = False
        self.recv_thread = None

        # Histórico de mensagens recebidas para asserção em testes
        self.received_messages = []

    def start(self):
        self.running = True
        self.recv_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.recv_thread.start()

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(2048)
                msg_type, sender_nick, text = unpack_chat_message(data)

                self.received_messages.append({
                    "from_addr": addr,
                    "type": msg_type,
                    "nick": sender_nick,
                    "text": text
                })

                type_label = TYPE_NAMES.get(msg_type, f"TYPE_{msg_type}")

                # Se for ECHO recebido
                if msg_type == TYPE_ECHO:
                    # Se o texto indicar ping, responde com ECHO Pong
                    if text.startswith("[PING]"):
                        reply_pkt = pack_chat_message(TYPE_ECHO, self.nickname, f"[PONG] {text}")
                        self.sock.sendto(reply_pkt, addr)
                        print(f"\n[ECHO RECEBIDO de {sender_nick}@{addr[0]}:{addr[1]} - Resposta enviada!]")
                    else:
                        print(f"\n[ECHO RESPOSTA de {sender_nick}@{addr[0]}:{addr[1]}: '{text}']")
                else:
                    try:
                        print(f"\n[{type_label}] {sender_nick}@{addr[0]}:{addr[1]}: {text}")
                    except UnicodeEncodeError:
                        print(f"\n[{type_label}] {sender_nick}@{addr[0]}:{addr[1]}: {text.encode('ascii', errors='backslashreplace').decode('ascii')}")

                sys.stdout.write("P2P> ")
                sys.stdout.flush()

            except OSError:
                break
            except Exception as e:
                if self.running:
                    print(f"\n[!] Erro ao processar mensagem recebida: {e}")

    def send_to(self, msg_type: int, text: str, dest_host: str = None, dest_port: int = None):
        """Envia um pacote formatado para o nó destino."""
        target_h = dest_host or self.target_host
        target_p = dest_port or self.target_port

        if not target_h or not target_p:
            print("[!] Destino não especificado!")
            return False

        packet = pack_chat_message(msg_type, self.nickname, text)
        self.sock.sendto(packet, (target_h, target_p))
        return True

def interactive_chat(nickname: str, bind_host: str, bind_port: int, target_host: str, target_port: int):
    node = P2PChatNode(nickname, bind_host, bind_port, target_host, target_port)
    node.start()

    print(f"=== P2P UDP Chat - Iniciado ===")
    print(f"Apelido: {nickname}")
    print(f"Escutando em: {bind_host}:{bind_port}")
    print(f"Destino padrão: {target_host}:{target_port}")
    print("--------------------------------")
    print("Comandos:")
    print("  /msg <texto>        - Envia mensagem normal (Tipo 1)")
    print("  /emoji <emoji/tag>  - Envia emoji (Tipo 2, ex: :smile:, :heart: ou 😀)")
    print("  /url <link>         - Envia URL (Tipo 3)")
    print("  /echo [texto]       - Envia ECHO de verificação de liveness (Tipo 4)")
    print("  /target <ip> <port> - Altera destino padrão")
    print("  /exit               - Sair")
    print("--------------------------------\n")

    try:
        while True:
            line = input("P2P> ").strip()
            if not line:
                continue

            if line.startswith("/"):
                parts = line.split(" ", 1)
                cmd = parts[0].lower()
                arg = parts[1].strip() if len(parts) > 1 else ""

                if cmd == "/msg":
                    if not arg:
                        print("[!] Digite o texto da mensagem.")
                        continue
                    node.send_to(TYPE_NORMAL, arg)
                elif cmd == "/emoji":
                    emoji_text = EMOJI_MAP.get(arg, arg)
                    node.send_to(TYPE_EMOJI, emoji_text)
                elif cmd == "/url":
                    if not arg:
                        print("[!] Digite a URL.")
                        continue
                    node.send_to(TYPE_URL, arg)
                elif cmd == "/echo":
                    msg = f"[PING] {arg or 'KeepAlive'}"
                    node.send_to(TYPE_ECHO, msg)
                elif cmd == "/target":
                    tgt = arg.split()
                    if len(tgt) == 2:
                        node.target_host = tgt[0]
                        node.target_port = int(tgt[1])
                        print(f"[*] Destino alterado para {node.target_host}:{node.target_port}")
                    else:
                        print("[!] Uso: /target <ip> <porta>")
                elif cmd == "/exit":
                    break
                else:
                    print("[!] Comando não reconhecido.")
            else:
                # Texto direto padrão é enviado como mensagem normal
                node.send_to(TYPE_NORMAL, line)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\n[*] Encerrando P2P...")
        node.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P Chat UDP (Questão 1)")
    parser.add_argument("--nick", default="Usuario", help="Seu apelido no chat")
    parser.add_argument("--bind-host", default="0.0.0.0", help="IP local para escuta")
    parser.add_argument("--bind-port", type=int, default=9001, help="Porta local para escuta")
    parser.add_argument("--target-host", default="127.0.0.1", help="IP de destino")
    parser.add_argument("--target-port", type=int, default=9002, help="Porta de destino")
    args = parser.parse_args()

    interactive_chat(args.nick, args.bind_host, args.bind_port, args.target_host, args.target_port)
