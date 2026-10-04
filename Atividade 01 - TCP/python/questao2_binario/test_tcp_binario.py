"""
Teste Automatizado para a Questão 2 (TCP Binário)
Valida:
1. ADDFILE com arquivos binários e textos
2. GETFILESLIST para listar arquivos
3. GETFILE para fazer download e conferir integridade binária byte a byte
4. DELETE para remover arquivo
5. GETFILESLIST para conferir remoção
"""

import os
import sys
import time
import subprocess
from client import TCPBinaryClient

def run_automated_test():
    host = "127.0.0.1"
    port = 8002
    storage_test = "./test_storage_binary"
    download_test = "./test_downloads_binary"

    os.makedirs(storage_test, exist_ok=True)
    os.makedirs(download_test, exist_ok=True)

    # Inicia o servidor binário
    server_process = subprocess.Popen(
        [sys.executable, "server.py", "--host", host, "--port", str(port), "--storage", storage_test],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1.0)

    try:
        # Cria arquivos locais de teste (um texto e um binário arbitrário com bytes aleatórios)
        test_txt = "sample.txt"
        with open(test_txt, "w", encoding="utf-8") as f:
            f.write("Conteudo de teste para protocolo binario em Sistemas Distribuidos!")

        test_bin = "sample.bin"
        test_bin_data = os.urandom(128 * 1024) # 128 KiB de dados binários
        with open(test_bin, "wb") as f:
            f.write(test_bin_data)

        client = TCPBinaryClient(host, port, download_dir=download_test)
        client.connect()
        print("[TEST] Cliente conectado ao servidor TCP binário.")

        # 1. ADDFILE (texto)
        print("[TEST 1] Enviando arquivo de texto via ADDFILE...")
        ok = client.add_file(test_txt, "remoto_sample.txt")
        assert ok, "Falha ao enviar sample.txt via ADDFILE"
        print("  -> OK: sample.txt adicionado.")

        # 2. ADDFILE (binário 128KB)
        print("[TEST 2] Enviando arquivo binário (128 KB) via ADDFILE...")
        ok = client.add_file(test_bin, "remoto_sample.bin")
        assert ok, "Falha ao enviar sample.bin via ADDFILE"
        print("  -> OK: sample.bin adicionado.")

        # 3. GETFILESLIST
        print("[TEST 3] Listando arquivos remotos via GETFILESLIST...")
        files = client.get_files_list()
        print(f"  -> Lista recebida: {files}")
        assert "remoto_sample.txt" in files and "remoto_sample.bin" in files, f"Arquivos esperados ausentes: {files}"

        # 4. GETFILE (download do binário e verificação de integridade)
        print("[TEST 4] Baixando arquivo binário via GETFILE...")
        dl_path = client.get_file("remoto_sample.bin")
        assert dl_path is not None and os.path.exists(dl_path), "Falha no download de remoto_sample.bin"
        with open(dl_path, "rb") as f:
            downloaded_bytes = f.read()
        assert downloaded_bytes == test_bin_data, "Bytes baixados diferem do arquivo original!"
        print(f"  -> OK: Download de {len(downloaded_bytes)} bytes verificado com integridade idêntica!")

        # 5. DELETE
        print("[TEST 5] Removendo remoto_sample.txt via DELETE...")
        ok = client.delete_file("remoto_sample.txt")
        assert ok, "Falha ao deletar remoto_sample.txt"
        print("  -> OK: Arquivo deletado com sucesso.")

        # 6. Conferindo pós-delete
        files_after = client.get_files_list()
        print(f"  -> Lista após delete: {files_after}")
        assert "remoto_sample.txt" not in files_after, "Arquivo ainda consta após remoção!"
        assert "remoto_sample.bin" in files_after, "Arquivo preservado não encontrado!"

        client.close()
        print("\n==============================================")
        print(">>> TODOS OS TESTES DA QUESTÃO 2 PASSARAM! <<<")
        print("==============================================")

    finally:
        server_process.terminate()
        server_process.wait()
        # Limpeza de arquivos temporários do teste
        for f in [test_txt, test_bin]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    run_automated_test()
