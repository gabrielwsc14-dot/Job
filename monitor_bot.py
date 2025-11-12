import os
import time
import json
import requests
import subprocess
from datetime import datetime

# ====================================================
# CONFIGURAÇÃO
# ====================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1437598203741470906/TFM-sFFBfavWY26ESOZOQuY7I7v4pqXQ7-t6nJOgEore4ahYh9FkB3HEx8y8CTeu_7Xi"  # coloque seu link aqui
SCRIPT_PRINCIPAL = "vaga_bot_pc.py"  # nome do script principal
LOG_FILE = "logs.txt"
CHECK_INTERVAL = 1800  # 30 minutos entre verificações
# ====================================================


def enviar_log_discord(mensagem):
    """Envia logs e status para o Discord."""
    data = {
        "content": f"🧠 **Monitor de Vagas:** {mensagem}\n🕓 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    }
    try:
        requests.post(WEBHOOK_URL, data=json.dumps(data), headers={"Content-Type": "application/json"})
    except Exception as e:
        print(f"Erro ao enviar log para o Discord: {e}")


def registrar_log(texto):
    """Grava logs locais."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {texto}\n")


def bot_esta_rodando():
    """Verifica se o processo principal está em execução."""
    try:
        saida = subprocess.check_output("tasklist", shell=True).decode()
        return "python.exe" in saida and SCRIPT_PRINCIPAL in open("logs.txt", encoding="utf-8", errors="ignore").read()
    except Exception:
        return False


def iniciar_bot():
    """Inicia o bot principal."""
    try:
        subprocess.Popen(["python", SCRIPT_PRINCIPAL], creationflags=subprocess.CREATE_NEW_CONSOLE)
        registrar_log("Bot principal iniciado.")
        enviar_log_discord("✅ Bot principal iniciado com sucesso.")
    except Exception as e:
        registrar_log(f"Falha ao iniciar o bot: {e}")
        enviar_log_discord(f"❌ Falha ao iniciar o bot: {e}")


def monitorar():
    """Loop principal de monitoramento."""
    enviar_log_discord("🔍 Monitor iniciado.")
    registrar_log("Monitor iniciado.")
    while True:
        try:
            # Verifica se o bot principal ainda está rodando
            if not bot_esta_rodando():
                registrar_log("Bot não está rodando. Reiniciando...")
                enviar_log_discord("⚠️ Bot não detectado. Reiniciando...")
                iniciar_bot()
            else:
                registrar_log("Bot em execução normal.")
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            registrar_log(f"Erro no monitor: {e}")
            enviar_log_discord(f"❌ Erro no monitor: {e}")
            time.sleep(300)  # espera 5 minutos antes de tentar de novo


if __name__ == "__main__":
    monitorar()
