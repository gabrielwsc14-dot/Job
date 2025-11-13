#!/usr/bin/env python3
# bot_vagas.py — versão ultra-robusta
# - 7 sites confiáveis
# - filtro estrito JEQUITINHONHA/MG
# - salvamento seguro em ./site/vagas.json
# - envio ao Telegram apenas para vagas novas
# - anticorrupt, anti-duplicação
# - pronto p/ monitor_bot.py

import requests
from bs4 import BeautifulSoup
import time
import json
import os
from urllib.parse import urljoin, quote_plus
    
# ===================== CONFIG =====================
TOKEN = ""  # <-- COLE SEU TOKEN AQUI
CHAT_ID = ""  # <-- COLE SEU CHAT_ID AQUI

CHECK_INTERVAL_SECONDS = 3 * 60 * 60   # 3 horas
SEEN_FILE = "seen_links.json"
VAGAS_JSON = "./site/vagas.json"

CIDADE = "Jequitinhonha"
UF = "MG"

KEYWORDS = ["jovem aprendiz", "menor aprendiz", "aprendiz"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

HEADERS = {"User-Agent": USER_AGENT}

# ===================== UTILIDADES =====================

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("TOKEN/CHAT_ID não definidos.")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=12
        )
    except Exception as e:
        print("Erro enviando mensagem:", e)

def normalize_link(base, href):
    if href.startswith("http"):
        return href
    return urljoin(base, href)

def looks_like_job_title(text):
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in KEYWORDS)

# ===================== FILTRO JEQUITINHONHA =====================

def filtrar_jequitinhonha(v):
    titulo = v["titulo"].lower()
    link = v["link"].lower()

    # req.1 — tem que conter jequitinhonha em título ou link
    if "jequitinhonha" not in titulo and "jequitinhonha" not in link:
        return False

    # req.2 — excluir cidades próximas para evitar vagas erradas
    cidades_proibidas = [
        "itaobim", "almenara", "virgem da lapa",
        "pedra azul", "berilo", "salinas", "araçuaí",
        "capelinha"
    ]
    for c in cidades_proibidas:
        if c in titulo or c in link:
            return False

    # req.3 — deve ser de jovem aprendiz
    if not any(k in titulo for k in KEYWORDS):
        return False

    return True

# ===================== PARSERS DOS 7 SITES =====================

def buscar_trabalhabrasil():
    base = "https://www.trabalhabrasil.com.br"
    url = f"{base}/vagas-empregos/em-jequitinhonha-mg/jovem-aprendiz"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(txt):
                link = normalize_link(base, href)
                vagas.append({"titulo": txt or "Vaga", "link": link, "origem": "TrabalhaBrasil"})
    except Exception as e:
        print("TrabalhaBrasil erro:", e)
    return vagas

def buscar_indeed():
    base = "https://br.indeed.com"
    url = f"{base}/empregos?q=jovem+aprendiz&l={quote_plus(CIDADE + ', ' + UF)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.select("a.tapItem[href]"):
            title_tag = link.find("h2")
            if not title_tag:
                continue
            titulo = title_tag.get_text(strip=True)
            href = link.get("href")
            full = normalize_link(base, href)
            vagas.append({"titulo": titulo, "link": full, "origem": "Indeed"})
    except Exception as e:
        print("Indeed erro:", e)
    return vagas

def buscar_infojobs():
    base = "https://www.infojobs.com.br"
    url = f"{base}/empregos.aspx?Palabra=jovem+aprendiz&Location={quote_plus(CIDADE)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(txt):
                link = normalize_link(base, href)
                vagas.append({"titulo": txt, "link": link, "origem": "InfoJobs"})
    except Exception as e:
        print("InfoJobs erro:", e)
    return vagas

def buscar_bne():
    base = "https://www.bne.com.br"
    url = f"{base}/busca?q=jovem+aprendiz+{quote_plus(CIDADE)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(txt):
                link = normalize_link(base, href)
                vagas.append({"titulo": txt, "link": link, "origem": "BNE"})
    except Exception as e:
        print("BNE erro:", e)
    return vagas

def buscar_empregos_com_br():
    base = "https://www.empregos.com.br"
    url = f"{base}/vagas?palavra=jovem+aprendiz+{quote_plus(CIDADE)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(txt):
                link = normalize_link(base, href)
                vagas.append({"titulo": txt, "link": link, "origem": "Empregos.com.br"})
    except Exception as e:
        print("Empregos.com.br erro:", e)
    return vagas

def buscar_jooble():
    base = "https://br.jooble.org"
    url = f"{base}/search?q=jovem+aprendiz+{quote_plus(CIDADE)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(txt):
                link = normalize_link(base, href)
                vagas.append({"titulo": txt, "link": link, "origem": "Jooble"})
    except Exception as e:
        print("Jooble erro:", e)
    return vagas

def buscar_catho():
    base = "https://www.catho.com.br"
    url = f"{base}/vagas?q=jovem+aprendiz+{quote_plus(CIDADE)}"
    vagas = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            href = a["href"]
            if looks_like_job_title(txt):
                link = normalize_link(base, href)
                vagas.append({"titulo": txt, "link": link, "origem": "Catho"})
    except Exception as e:
        print("Catho erro:", e)
    return vagas

# ===================== CONSOLIDAÇÃO =====================

def buscar_todas():
    buscadores = [
        buscar_trabalhabrasil,
        buscar_indeed,
        buscar_infojobs,
        buscar_bne,
        buscar_empregos_com_br,
        buscar_jooble,
        buscar_catho
    ]

    vagas = []
    for f in buscadores:
        try:
            achadas = f()
            for v in achadas:
                vagas.append(v)
        except Exception as e:
            print(f"Erro em {f.__name__}:", e)
        time.sleep(1)

    # remover duplicadas por link
    unico = {}
    for v in vagas:
        unico[v["link"]] = v

    # aplicar filtro JEQUITINHONHA
    filtradas = [v for v in unico.values() if filtrar_jequitinhonha(v)]

    return filtradas

# ===================== LOOP PRINCIPAL =====================

def main():
    seen = load_seen()

    while True:
        try:
            todas = buscar_todas()

            # salvar SEMPRE o vagas.json
            try:
                os.makedirs("./site", exist_ok=True)
                with open(VAGAS_JSON, "w", encoding="utf-8") as f:
                    json.dump(todas, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print("Erro salvando vagas.json:", e)

            # notificar apenas as novas
            novas = [v for v in todas if v["link"] not in seen]

            if novas:
                msg = "🚨 *Novas vagas de Jovem Aprendiz em Jequitinhonha/MG:*\n\n"
                for v in novas:
                    msg += f"🔹 {v['titulo']}\n🔗 {v['link']}\n\n"
                msg += "💼 Boa sorte!"
                send_telegram(msg)

                for v in novas:
                    seen.add(v["link"])
                save_seen(seen)

            time.sleep(CHECK_INTERVAL_SECONDS)

        except Exception as e:
            print("Erro no loop principal:", e)
            time.sleep(120)

if __name__ == "__main__":
    main()
