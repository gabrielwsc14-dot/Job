import os
import time
import json
import psutil
import subprocess
from datetime import datetime

# ====================================================
# CONFIGURAÇÃO
# ====================================================

SCRIPT_BOT = "vaga_bot_pc.py"           # Bot principal
SCRIPT_MONITOR = "monitor_botpy"    # Monitor do JSON
LOG_FILE = "iniciar_logs.txt"
CHECK_INTERVAL = 180    # Tempo entre verificações (segundos)
# ====================================================


# ====================================================
# LOGS
# ====================================================

def log(txt):
    """Registra logs locais, nunca falha."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {txt}\n")
    except:
        pass


# ====================================================
# SISTEMA DE PROCESSOS
# ====================================================

def listar_instancias(script):
    """Retorna todas as instâncias Python rodando com o script especificado."""
    instancias = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            nome = proc.info['name']
            cmd = proc.info['cmdline']

            if not nome:
                continue

            if "python" in nome.lower():
                if cmd and any(script.lower() in c.lower() for c in cmd):
                    instancias.append(proc)
        except:
            pass

    return instancias


def matar_duplicados(script):
    """Mantém somente UMA instância de um script."""
    instancias = listar_instancias(script)

    if len(instancias) > 1:
        for p in instancias[1:]:
            try:
                p.kill()
                log(f"[OK] Processo duplicado removido: {script} (PID {p.pid})")
            except:
                pass


def iniciar(script):
    """Inicia um script Python em janela separada."""
    try:
        subprocess.Popen(
            ["python", script],
            creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        )
        log(f"[OK] Iniciado: {script}")
    except Exception as e:
        log(f"[ERRO] Falha ao iniciar {script}: {e}")


def garantir_rodando(script):
    """Garante que sempre exista UMA instância rodando."""
    if len(listar_instancias(script)) == 0:
        log(f"[WARN] {script} não está rodando. Iniciando…")
        iniciar(script)
        time.sleep(2)
    else:
        matar_duplicados(script)
        log(f"[OK] {script} está rodando corretamente.")


# ====================================================
# LOOP PRINCIPAL
# ====================================================

def main():
    log("====================================================")
    log("INICIAR_BOT ULTRA-ROBUSTO INICIADO")
    log("====================================================")

    # Mata duplicados dos dois scripts ao iniciar
    matar_duplicados(SCRIPT_BOT)
    matar_duplicados(SCRIPT_MONITOR)

    # Garante que ambos iniciem
    garantir_rodando(SCRIPT_BOT)
    garantir_rodando(SCRIPT_MONITOR)

    while True:
        try:
            garantir_rodando(SCRIPT_BOT)
            garantir_rodando(SCRIPT_MONITOR)

            log("[OK] Ciclo completo.")
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            log(f"[ERRO NO LOOP] {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
