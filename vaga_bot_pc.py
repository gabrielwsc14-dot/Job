#!/usr/bin/env python3
# vaga_bot_pc.py
# Buscador de vagas (PC) — gera vagas.json compatível com o site (sem Telegram).
# Compatível Windows 10+, Python 3.8+

import requests
from bs4 import BeautifulSoup
import time
import json
import os
from urllib.parse import urljoin, quote_plus
from datetime import datetime
import subprocess
import sys
import traceback
import shutil

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CONFIG2_PATH = os.path.join(BASE_DIR, "config2.json")  # monitor/logs

# Agora o JSON principal fica dentro da pasta "site"
VAGAS_PATH = os.path.join(BASE_DIR, "site", "vagas.json")
SITE_VAGAS_PATH = os.path.join(BASE_DIR, "site", "vagas.json")

# ---------- Config ----------
def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

cfg = load_json(CONFIG_PATH)
cfg2 = load_json(CONFIG2_PATH)

CIDADE = cfg.get("cidade", "Jequitinhonha", "Belo Horizonte")
UF = cfg.get("uf", "MG")
KEYWORDS = [k.lower() for k in cfg.get("keywords", ["jovem aprendiz"])]
HEADERS = {"User-Agent": cfg.get("user_agent", "VagasPCBot/1.0")}
DELAY_BETWEEN = cfg.get("check_delay_between_sites_seconds", 1)
MAX_RESULTS_PER_SITE = cfg.get("max_results_per_site", 50)
DISCORD_WEBHOOK = cfg2.get("discord_webhook", "")

GIT_PUSH_CFG = cfg.get("git_push", {})

# ---------- Utils ----------
def log(msg):
    print(msg)
    if DISCORD_WEBHOOK:
        try:
            requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=10)
        except Exception:
            pass

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def read_existing():
    if not os.path.exists(VAGAS_PATH):
        return []
    try:
        with open(VAGAS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Falha ao ler vagas.json:", e)
        return []

def write_vagas(list_of_vagas):
    # salva vagas.json principal
    with open(VAGAS_PATH, "w", encoding="utf-8") as f:
        json.dump(list_of_vagas, f, ensure_ascii=False, indent=2)
    # copia também para o site
    try:
        shutil.copyfile(VAGAS_PATH, SITE_VAGAS_PATH)
    except Exception as e:
        print("Erro ao copiar vagas.json para site:", e)

def normalize_link(base, href):
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return urljoin(base, href)

def looks_like_job_title(text):
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in KEYWORDS)

# ---------- Parsers ----------
def buscar_trabalhabrasil():
    base = "https://www.trabalhabrasil.com.br"
    url = f"{base}/vagas-empregos/em-{quote_plus(CIDADE.lower())}-{UF.lower()}/jovem-aprendiz"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(text) or CIDADE.lower() in (text+href).lower():
                link = normalize_link(base, href)
                vagas.append({"title": text or "Vaga (sem título)", "link": link, "origin": "TrabalhaBrasil", "collected_at": now_iso()})
                if len(vagas) >= MAX_RESULTS_PER_SITE:
                    break
    except Exception as e:
        log(f"⚠️ Erro TrabalhaBrasil: {e}")
    return vagas

def buscar_indeed():
    base = "https://br.indeed.com"
    q = "jovem aprendiz"
    url = f"{base}/empregos?q={quote_plus(q)}&l={quote_plus(CIDADE + ', ' + UF)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.select("a.tapItem[href]")[:MAX_RESULTS_PER_SITE]:
            title_tag = link.find("h2")
            titulo = title_tag.get_text(strip=True) if title_tag else link.get_text(strip=True)
            href = link.get("href")
            if titulo and (looks_like_job_title(titulo) or CIDADE.lower() in titulo.lower()):
                vagas.append({"title": titulo, "link": normalize_link(base, href), "origin": "Indeed", "collected_at": now_iso()})
    except Exception as e:
        log(f"⚠️ Erro Indeed: {e}")
    return vagas

def buscar_infojobs():
    base = "https://www.infojobs.com.br"
    q = "jovem aprendiz"
    url = f"{base}/empregos.aspx?Palabra={quote_plus(q)}&Location={quote_plus(CIDADE)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True)[:MAX_RESULTS_PER_SITE]:
            text = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(text) or CIDADE.lower() in (text+href).lower():
                vagas.append({"title": text, "link": normalize_link(base, href), "origin": "InfoJobs", "collected_at": now_iso()})
    except Exception as e:
        log(f"⚠️ Erro InfoJobs: {e}")
    return vagas

def buscar_bne():
    base = "https://www.bne.com.br"
    query = f"jovem aprendiz {CIDADE}"
    url = f"{base}/busca?q={quote_plus(query)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True)[:MAX_RESULTS_PER_SITE]:
            text = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(text) or CIDADE.lower() in text.lower():
                vagas.append({"title": text, "link": normalize_link(base, href), "origin": "BNE", "collected_at": now_iso()})
    except Exception as e:
        log(f"⚠️ Erro BNE: {e}")
    return vagas

def buscar_empregos_com_br():
    base = "https://www.empregos.com.br"
    query = f"jovem aprendiz {CIDADE}"
    url = f"{base}/vagas?palavra={quote_plus(query)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True)[:MAX_RESULTS_PER_SITE]:
            text = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(text) or CIDADE.lower() in text.lower():
                vagas.append({"title": text, "link": normalize_link(base, href), "origin": "Empregos.com.br", "collected_at": now_iso()})
    except Exception as e:
        log(f"⚠️ Erro Empregos.com.br: {e}")
    return vagas

def buscar_jooble():
    base = "https://br.jooble.org"
    query = f"jovem aprendiz {CIDADE} {UF}"
    url = f"{base}/search?q={quote_plus(query)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True)[:MAX_RESULTS_PER_SITE]:
            text = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(text) or CIDADE.lower() in text.lower():
                vagas.append({"title": text, "link": normalize_link(base, href), "origin": "Jooble", "collected_at": now_iso()})
    except Exception as e:
        log(f"⚠️ Erro Jooble: {e}")
    return vagas

def buscar_catho():
    base = "https://www.catho.com.br"
    query = f"jovem aprendiz {CIDADE}"
    url = f"{base}/vagas?q={quote_plus(query)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True)[:MAX_RESULTS_PER_SITE]:
            text = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(text) or CIDADE.lower() in text.lower():
                vagas.append({"title": text, "link": normalize_link(base, href), "origin": "Catho", "collected_at": now_iso()})
    except Exception as e:
        log(f"⚠️ Erro Catho: {e}")
    return vagas

SCRAPERS = [
    buscar_trabalhabrasil,
    buscar_indeed,
    buscar_infojobs,
    buscar_bne,
    buscar_empregos_com_br,
    buscar_jooble,
    buscar_catho
]

# ---------- Core ----------
def pertence_a_jequitinhonha(vaga):
    """Retorna True se a vaga pertence à cidade configurada."""
    texto = f"{vaga.get('title','')} {vaga.get('link','')} {vaga.get('origin','')}".lower()
    return CIDADE.lower() in texto and UF.lower() in texto

def collect_once():
    log("🚀 Coleta iniciada.")
    existing = read_existing()
    existing_links = set(item.get("link") for item in existing if item.get("link"))
    found = []

    for fn in SCRAPERS:
        try:
            items = fn()
            for it in items:
                link = it.get("link") or ""
                # ⚙️ aplica filtro de cidade e duplicidade
                if (
                    link
                    and pertence_a_jequitinhonha(it)
                    and link not in existing_links
                    and all(link != x["link"] for x in found)
                ):
                    found.append(it)
            time.sleep(DELAY_BETWEEN)
        except Exception as e:
            log(f"Erro no scraper {fn.__name__}: {e}")
            traceback.print_exc()

    if found:
        combined = found + existing
        combined_sorted = sorted(combined, key=lambda x: x.get("collected_at", ""), reverse=True)
        write_vagas(combined_sorted)
        log(f"✅ {len(found)} novas vagas adicionadas e site atualizado!")
    else:
        log("ℹ️ Nenhuma nova vaga encontrada.")

    # --- git push opcional ---
    try:
        if GIT_PUSH_CFG.get("enabled"):
            repo = GIT_PUSH_CFG.get("repo_path")
            msg = GIT_PUSH_CFG.get("commit_message", "Atualiza vagas.json (automático)")
            if repo and os.path.isdir(repo):
                log(f"Executando git push em {repo}")
                cmds = [
                    ["git", "-C", repo, "add", "vagas.json"],
                    ["git", "-C", repo, "commit", "-m", msg],
                    ["git", "-C", repo, "push"]
                ]
                for c in cmds:
                    subprocess.run(c, check=False)
    except Exception as e:
        log(f"Erro ao executar git push: {e}")

if __name__ == "__main__":
    while True:
        collect_once()
        log("⏳ Aguardando 12 horas para a próxima coleta...")
        time.sleep(12 * 60 * 60)  # 12 horas

