import os
import time
import json
import requests
import subprocess
from datetime import datetime

# ====================================================
# CONFIGURAÇÃO
# ====================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1437598203741470906/TFM-sFFBfavWY26ESOZOQuY7I7v4pqXQ7-t6nJOgEore4ahYh9FkB3HEx8y8CTeu_7Xi"
SCRIPT_PRINCIPAL = "vaga_bot_pc.py"
LOG_FILE = "logs.txt"
CHECK_INTERVAL = 1800  # 30 min
JSON_ARQUIVO = "vagas.json"
# ====================================================


def enviar_log_discord(mensagem):
    """Envia logs e status para o Discord."""
    data = {
        "content": f"🧠 **Monitor:** {mensagem}\n🕓 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    }
    try:
        requests.post(WEBHOOK_URL, json=data)
    except:
        pass


def registrar_log(texto):
    """Grava logs locais."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {texto}\n")


def obter_pid_bot():
    """Retorna o PID do bot, se estiver rodando."""
    try:
        saida = subprocess.check_output(
            f'tasklist /FI "IMAGENAME eq python.exe" /V', shell=True
        ).decode()

        for linha in saida.splitlines():
            if SCRIPT_PRINCIPAL in linha:
                # Pega o PID (segunda coluna)
                partes = linha.split()
                pid = partes[1]
                return int(pid)
    except:
        return None

    return None


def processo_existe(pid):
    """Verifica se um processo ainda existe pelo PID."""
    try:
        saida = subprocess.check_output("tasklist", shell=True).decode()
        return str(pid) in saida
    except:
        return False


def bot_parou_de_atualizar_json():
    """Verifica se o JSON foi atualizado nas últimas 2 horas."""
    if not os.path.exists(JSON_ARQUIVO):
        return True  # se nem existe, tá errado

    ultima_mod = os.path.getmtime(JSON_ARQUIVO)
    horas = (time.time() - ultima_mod) / 3600

    return horas > 2  # limite: 2h sem atualizar


def iniciar_bot():
    """Inicia o bot principal."""
    try:
        subprocess.Popen(
            ["python", SCRIPT_PRINCIPAL],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        registrar_log("Bot principal iniciado.")
        enviar_log_discord("✅ Bot principal iniciado.")
    except Exception as e:
        registrar_log(f"Erro ao iniciar: {e}")
        enviar_log_discord(f"❌ Falha ao iniciar: {e}")


def monitorar():
    """Loop principal."""
    enviar_log_discord("🔍 Monitor iniciado.")
    registrar_log("Monitor iniciado.")

    pid_atual = None

    while True:
        try:
            # SE O BOT NÃO TEM PID ATUAL, TENTAR LOCALIZAR
            if pid_atual is None:
                pid_atual = obter_pid_bot()
                if pid_atual:
                    registrar_log(f"PID detectado: {pid_atual}")
                else:
                    registrar_log("Bot não encontrado. Iniciando...")
                    enviar_log_discord("⚠️ Bot não encontrado. Reiniciando...")
                    iniciar_bot()
                    time.sleep(30)
                    continue

            # Verificar se o processo existe
            if not processo_existe(pid_atual):
                registrar_log("Bot caiu (PID sumiu). Reiniciando...")
                enviar_log_discord("⚠️ Bot caiu (processo sumiu). Reiniciando...")
                pid_atual = None
                iniciar_bot()
                time.sleep(30)
                continue

            # Verificar se bot está travado (JSON congelado)
            if bot_parou_de_atualizar_json():
                registrar_log("JSON não atualiza há muito tempo. Reiniciando bot...")
                enviar_log_discord("🟡 JSON congelado. Reiniciando bot...")
                subprocess.Popen(["taskkill", "/PID", str(pid_atual), "/F"])
                pid_atual = None
                iniciar_bot()
                time.sleep(30)
                continue

            # Log normal
            registrar_log(f"Bot OK (PID {pid_atual}).")
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            registrar_log(f"Erro do monitor: {e}")
            enviar_log_discord(f"❌ Erro do monitor: {e}")
            time.sleep(300)  # espera 5 min


if __name__ == "__main__":
    monitorar()
