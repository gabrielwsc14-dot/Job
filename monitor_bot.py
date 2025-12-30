import os
import time
import json
import psutil
import requests
from datetime import datetime

# ====================================================
# CONFIGURAÇÃO
# ====================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1437598203741470906/TFM-sFFBfavWY26ESOZOQuY7I7v4pqXQ7-t6nJOgEore4ahYh9FkB3HEx8y8CTeu_7Xi"
SCRIPT_PRINCIPAL = "vaga_bot_pc.py"
LOG_FILE = "logs.txt"
CHECK_INTERVAL = 1800  # 30 minutos
# ====================================================


def enviar_log_discord(mensagem):
    data = {
        "content": f"🧠 **Monitor:** {mensagem}\n🕓 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    }
    try:
        requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"Erro ao enviar log para o Discord: {e}")


def registrar_log(texto):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {texto}\n")


def bot_esta_rodando():
    """Verifica se o bot está rodando."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            nome = proc.info['name']
            cmd = proc.info['cmdline']

            if nome and "python" in nome.lower():
                if cmd and any(SCRIPT_PRINCIPAL.lower() in c.lower() for c in cmd):
                    return True

        except:
            pass

    return False


def monitorar():
    enviar_log_discord("🔍 Monitor iniciado.")
    registrar_log("Monitor iniciado.")

    while True:
        try:
            if bot_esta_rodando():
                registrar_log("Bot em execução normal.")
            else:
                registrar_log("⚠️ Bot apagado (não está rodando).")
                enviar_log_discord("⚠️ Bot desligado. Inicie manualmente pelo .BAT.")

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            registrar_log(f"Erro no monitor: {e}")
            enviar_log_discord(f"❌ Erro no monitor: {e}")
            time.sleep(300)


if __name__ == "__main__":
    monitorar()
