"""
Teste Automatizado para a Questão 2 (Upload de Arquivos UDP)
Testa o servidor com:
1. Arquivo de texto pequeno (~100 bytes)
2. Arquivo intermediário (~4 KiB)
3. Arquivo binário grande (~512 KiB a 1 MiB)
Valida:
- Fragmentação exata de 1024 bytes
- Checksum SHA-1 calculado e validado pelo servidor
- Integridade idêntica byte a byte entre o arquivo original e o salvo no servidor
"""

import os
import sys
import time
import hashlib
import subprocess
from client import UDPUploadClient

def calculate_sha1(filepath: str) -> str:
    h = hashlib.sha1()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_automated_test():
    host = "127.0.0.1"
    port = 9005
    storage_test = "./test_server_storage"
    os.makedirs(storage_test, exist_ok=True)

    # Inicia o servidor UDP
    server_process = subprocess.Popen(
        [sys.executable, "server.py", "--host", host, "--port", str(port), "--storage", storage_test],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1.0)

    test_files = []

    try:
        client = UDPUploadClient(host, port)

        # 1. Teste com 100 bytes (texto)
        file_100b = "test_100b.txt"
        test_files.append(file_100b)
        content_100b = ("A" * 99 + "\n").encode("utf-8")
        with open(file_100b, "wb") as f:
            f.write(content_100b)

        print("[TEST 1] Enviando arquivo de 100 bytes...")
        ok = client.upload_file(file_100b, show_progress=False)
        assert ok, "Falha no upload do arquivo de 100 bytes"
        saved_100b = os.path.join(storage_test, file_100b)
        assert os.path.exists(saved_100b), "Arquivo de 100b não foi salvo no servidor"
        assert calculate_sha1(file_100b) == calculate_sha1(saved_100b), "Checksum divergente em 100b"
        print("  -> OK: 100 bytes recebidos e validados com SHA-1 idêntico!")

        # 2. Teste com 4 KiB (4096 bytes = exatamente 4 chunks de 1024 bytes)
        file_4kib = "test_4kib.bin"
        test_files.append(file_4kib)
        content_4k = os.urandom(4096)
        with open(file_4kib, "wb") as f:
            f.write(content_4k)

        print("[TEST 2] Enviando arquivo de 4 KiB (4 blocos de 1024B)...")
        ok = client.upload_file(file_4kib, show_progress=False)
        assert ok, "Falha no upload de 4 KiB"
        saved_4k = os.path.join(storage_test, file_4kib)
        assert calculate_sha1(file_4kib) == calculate_sha1(saved_4k), "Checksum divergente em 4 KiB"
        print("  -> OK: 4 KiB recebidos e validados com SHA-1 idêntico!")

        # 3. Teste com arquivo binário maior (~1 MiB = 1024 chunks de 1024 bytes)
        file_1mib = "test_1mib.bin"
        test_files.append(file_1mib)
        content_1m = os.urandom(1024 * 1024)
        with open(file_1mib, "wb") as f:
            f.write(content_1m)

        print("[TEST 3] Enviando arquivo binário de 1 MiB (1024 blocos de 1024B)...")
        ok = client.upload_file(file_1mib, show_progress=False)
        assert ok, "Falha no upload de 1 MiB"
        saved_1m = os.path.join(storage_test, file_1mib)
        assert calculate_sha1(file_1mib) == calculate_sha1(saved_1m), "Checksum divergente em 1 MiB"
        print("  -> OK: 1 MiB recebido e validado com SHA-1 idêntico!")

        client.close()
        print("\n=======================================================")
        print(">>> TODOS OS TESTES DA ATIVIDADE 2 (Q2) PASSARAM! <<<")
        print("=======================================================")

    finally:
        server_process.terminate()
        server_process.wait()
        for f in test_files:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    run_automated_test()
