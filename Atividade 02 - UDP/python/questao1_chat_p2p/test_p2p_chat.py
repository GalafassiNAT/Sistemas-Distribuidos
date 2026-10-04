"""
Teste Automatizado para a Questão 1 (Chat P2P UDP)
Instancia dois peers (Alice na porta 9001 e Bob na porta 9002).
Testa:
1. Troca de Mensagem Normal (Tipo 1)
2. Troca de Emoji (Tipo 2)
3. Troca de URL (Tipo 3)
4. Envio de ECHO (Tipo 4) e resposta automática de liveness
"""

import time
from p2p_node import P2PChatNode
from protocol import TYPE_NORMAL, TYPE_EMOJI, TYPE_URL, TYPE_ECHO

def run_automated_test():
    print("[TEST] Inicializando Alice (9001 -> 9002) e Bob (9002 -> 9001)...")
    alice = P2PChatNode("Alice", "127.0.0.1", 9001, "127.0.0.1", 9002)
    bob = P2PChatNode("Bob", "127.0.0.1", 9002, "127.0.0.1", 9001)

    alice.start()
    bob.start()
    time.sleep(0.5)

    try:
        # 1. Mensagem Normal
        print("[TEST 1] Alice enviando mensagem normal para Bob...")
        alice.send_to(TYPE_NORMAL, "Olá Bob, tudo bem?")
        time.sleep(0.3)
        assert len(bob.received_messages) == 1, "Bob não recebeu a mensagem normal!"
        msg = bob.received_messages[-1]
        assert msg["type"] == TYPE_NORMAL and msg["nick"] == "Alice" and msg["text"] == "Olá Bob, tudo bem?"
        print("  -> OK: Mensagem normal recebida com integridade.")

        # 2. Mensagem Emoji
        print("[TEST 2] Bob respondendo com emoji para Alice...")
        bob.send_to(TYPE_EMOJI, "😀❤️")
        time.sleep(0.3)
        assert len(alice.received_messages) == 1, "Alice não recebeu o emoji!"
        msg = alice.received_messages[-1]
        assert msg["type"] == TYPE_EMOJI and msg["nick"] == "Bob" and msg["text"] == "😀❤️"
        print("  -> OK: Mensagem emoji recebida com sucesso.")

        # 3. Mensagem URL
        print("[TEST 3] Alice enviando URL para Bob...")
        alice.send_to(TYPE_URL, "https://github.com/exemplo/sd")
        time.sleep(0.3)
        assert len(bob.received_messages) == 2, "Bob não recebeu a URL!"
        msg = bob.received_messages[-1]
        assert msg["type"] == TYPE_URL and msg["text"] == "https://github.com/exemplo/sd"
        print("  -> OK: URL recebida com sucesso.")

        # 4. Mensagem ECHO
        print("[TEST 4] Bob enviando ECHO de liveness para Alice...")
        bob.send_to(TYPE_ECHO, "[PING] AliveCheck")
        time.sleep(0.5)
        # Alice deve ter recebido o PING e respondido com PONG para Bob
        assert len(alice.received_messages) == 2, "Alice não recebeu o PING!"
        assert len(bob.received_messages) == 3, "Bob não recebeu a resposta de PONG do ECHO!"
        echo_reply = bob.received_messages[-1]
        assert echo_reply["type"] == TYPE_ECHO and "[PONG]" in echo_reply["text"]
        print("  -> OK: Mecanismo de ECHO (Liveness) bidirecional validado.")

        print("\n=======================================================")
        print(">>> TODOS OS TESTES DA ATIVIDADE 2 (Q1) PASSARAM! <<<")
        print("=======================================================")

    finally:
        alice.stop()
        bob.stop()

if __name__ == "__main__":
    run_automated_test()
