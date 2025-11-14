import os
import time
import json
import psutil
import requests
import subprocess
from datetime import datetime

# ====================================================
# CONFIGURAÇÃO
# ====================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1437598203741470906/TFM-sFFBfavWY26ESOZOQuY7I7v4pqXQ7-t6nJOgEore4ahYh9FkB3HEx8y8CTeu_7Xi"
SCRIPT_PRINCIPAL = "vaga_bot_pc.py"
LOG_FILE = "logs.txt"
CHECK_INTERVAL = 1800  # 30 minutos entre verificações
# ====================================================


# ====================================================
# Funções auxiliares
# ====================================================

def enviar_log_discord(mensagem):
    """Envia logs e status para o Discord."""
    data = {
        "content": f"🧠 **Monitor de Vagas:** {mensagem}\n🕓 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    }
    try:
        requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"Erro ao enviar log para o Discord: {e}")


def registrar_log(texto):
    """Grava logs locais."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {texto}\n")


def bot_esta_rodando():
    """
    Verifica se o processo do bot está rodando EXATAMENTE,
    usando psutil para detectar o python + script correto.
    """
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


def matar_bots_duplicados():
    """Mata TODAS as instâncias duplicadas do bot, deixando apenas uma."""
    processos = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            nome = proc.info['name']
            cmd = proc.info['cmdline']

            if nome and "python" in nome.lower():
                if cmd and any(SCRIPT_PRINCIPAL.lower() in c.lower() for c in cmd):
                    processos.append(proc)
        except:
            pass

    # Mantém só a primeira
    if len(processos) > 1:
        for p in processos[1:]:
            try:
                p.kill()
                registrar_log(f"Processo duplicado finalizado: PID {p.pid}")
            except:
                pass


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

    # Mata duplicatas logo no início
    matar_bots_duplicados()

    while True:
        try:
            if not bot_esta_rodando():
                registrar_log("Bot não detectado. Reiniciando...")
                enviar_log_discord("⚠️ Bot não detectado. Reiniciando...")
                iniciar_bot()
                time.sleep(5)  # aguarda inicialização
            else:
                matar_bots_duplicados()
                registrar_log("Bot em execução normal.")

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            registrar_log(f"Erro no monitor: {e}")
            enviar_log_discord(f"❌ Erro no monitor: {e}")
            time.sleep(300)


if __name__ == "__main__":
    monitorar()
