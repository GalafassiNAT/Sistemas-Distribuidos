"""
Teste Automatizado para a Questão 1 (TCP Textual)
Valida:
1. Conexão e falha com credencial inválida
2. Sucesso com credencial válida (CONNECT)
3. PWD inicial
4. Criação e listagem de diretórios/arquivos (GETDIRS, GETFILES)
5. Navegação com CHDIR
6. Finalização com EXIT
"""

import os
import sys
import time
import subprocess
from client import TCPTextualClient

def run_automated_test():
    host = "127.0.0.1"
    port = 8001
    storage_test = "./test_storage_textual"

    # Inicia o servidor em processo separado
    server_process = subprocess.Popen(
        [sys.executable, "server.py", "--host", host, "--port", str(port), "--storage", storage_test],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1.0) # Aguarda inicialização

    try:
        print("[TEST] Conectando cliente...")
        client = TCPTextualClient(host, port)
        client.connect()

        # 1. Tentativa com senha errada
        print("[TEST 1] Tentando autenticação inválida...")
        res = client.cmd_connect("admin", "senha_incorreta")
        assert res == "ERROR", f"Esperado ERROR, recebido: {res}"
        print("  -> OK: Autenticação inválida rejeitada.")

        # 2. Tentativa com senha correta
        print("[TEST 2] Autenticando com 'admin' e 'admin123'...")
        res = client.cmd_connect("admin", "admin123")
        assert res == "SUCCESS", f"Esperado SUCCESS, recebido: {res}"
        print("  -> OK: Autenticação bem sucedida.")

        # 3. PWD
        print("[TEST 3] Verificando PWD...")
        pwd = client.cmd_pwd()
        print(f"  -> PWD retornado: {pwd}")
        assert pwd.startswith("/admin"), f"Esperado path relativo a admin, recebido {pwd}"

        # Prepara arquivos no diretório do admin para testar GETFILES e GETDIRS
        admin_dir = os.path.join(storage_test, "admin")
        os.makedirs(os.path.join(admin_dir, "pasta_teste"), exist_ok=True)
        with open(os.path.join(admin_dir, "arquivo1.txt"), "w") as f:
            f.write("conteudo 1")
        with open(os.path.join(admin_dir, "arquivo2.txt"), "w") as f:
            f.write("conteudo 2")

        # 4. GETFILES
        print("[TEST 4] Testando GETFILES...")
        files = client.cmd_getfiles()
        print(f"  -> Arquivos encontrados: {files}")
        assert "arquivo1.txt" in files and "arquivo2.txt" in files, f"Arquivos esperados faltando: {files}"

        # 5. GETDIRS
        print("[TEST 5] Testando GETDIRS...")
        dirs = client.cmd_getdirs()
        print(f"  -> Diretórios encontrados: {dirs}")
        assert "pasta_teste" in dirs, f"Diretório esperado faltando: {dirs}"

        # 6. CHDIR
        print("[TEST 6] Testando CHDIR para 'pasta_teste'...")
        res_chdir = client.cmd_chdir("pasta_teste")
        assert res_chdir == "SUCCESS", f"Esperado SUCCESS no chdir, recebido {res_chdir}"
        pwd_depois = client.cmd_pwd()
        print(f"  -> Novo PWD: {pwd_depois}")
        assert "pasta_teste" in pwd_depois

        # 7. EXIT
        print("[TEST 7] Testando comando EXIT...")
        client.cmd_exit()
        print("  -> OK: Conexão finalizada com sucesso.")

        print("\n==============================================")
        print(">>> TODOS OS TESTES DA QUESTÃO 1 PASSARAM! <<<")
        print("==============================================")

    finally:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    run_automated_test()
