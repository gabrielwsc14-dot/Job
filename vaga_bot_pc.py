#!/usr/bin/env python3
# bot_vagas.py — versão otimizada e 100% compatível

import requests
from bs4 import BeautifulSoup
import time
import json
import os
from urllib.parse import urljoin, quote_plus
from datetime import datetime
from requests.adapters import HTTPAdapter, Retry

# ===================== CONFIG =====================
TOKEN = ""      # Telegram
CHAT_ID = ""    # Telegram

CHECK_INTERVAL_SECONDS = 3 * 60 * 60
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

# ===================== SESSÃO REUTILIZÁVEL =====================

def nova_sessao():
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

session = nova_sessao()

# ===================== UTILIDADES =====================

def iso_now():
    return datetime.now().isoformat(timespec="seconds")

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
        print("TOKEN/CHAT_ID ausentes")
        return

    try:
        session.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=15
        )
    except Exception as e:
        print("Erro Telegram:", e)

def normalize_link(base, href):
    if not href:
        return None
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
    titulo = v["title"].lower()
    link = v["link"].lower()

    # Jequitinhonha obrigatório
    if "jequitinhonha" not in titulo and "jequitinhonha" not in link:
        return False

    cidades_proibidas = [
        "itaobim", "almenara", "virgem da lapa",
        "pedra azul", "berilo", "salinas", "araçuaí",
        "capelinha"
    ]
    if any(c in titulo or c in link for c in cidades_proibidas):
        return False

    # deve conter palavras-chave
    if not any(k in titulo for k in KEYWORDS):
        return False

    return True

# ===================== MODELO DE VAGA =====================

def wrap(title, link, origin):
    return {
        "title": title,
        "link": link,
        "origin": origin,
        "collected_at": iso_now()
    }

# ===================== MODELO DE BUSCA SEGURO =====================

def get_soup(url):
    try:
        r = session.get(url, headers=HEADERS, timeout=20)
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[ERRO] Falha ao acessar {url} →", e)
        return None

# ===================== 7 PARSERS (OTIMIZADOS) =====================

def buscar_trabalhabrasil():
    base = "https://www.trabalhabrasil.com.br"
    url = f"{base}/vagas-empregos/em-jequitinhonha-mg/jovem-aprendiz"

    soup = get_soup(url)
    if not soup:
        return []

    vagas = []
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if looks_like_job_title(txt):
            link = normalize_link(base, a["href"])
            vagas.append(wrap(txt, link, "TrabalhaBrasil"))
    return vagas


def buscar_indeed():
    base = "https://br.indeed.com"
    url = f"{base}/empregos?q=jovem+aprendiz&l={quote_plus(CIDADE + ', ' + UF)}"

    soup = get_soup(url)
    if not soup:
        return []

    vagas = []
    for link in soup.select("a.tapItem[href]"):
        h2 = link.find("h2")
        if not h2:
            continue
        titulo = h2.get_text(strip=True)
        full = normalize_link(base, link.get("href"))
        vagas.append(wrap(titulo, full, "Indeed"))
    return vagas


def buscar_infojobs():
    base = "https://www.infojobs.com.br"
    url = f"{base}/empregos.aspx?Palabra=jovem+aprendiz&Location={quote_plus(CIDADE)}"

    soup = get_soup(url)
    if not soup:
        return []

    vagas = []
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if looks_like_job_title(txt):
            link = normalize_link(base, a["href"])
            vagas.append(wrap(txt, link, "InfoJobs"))
    return vagas


def buscar_bne():
    base = "https://www.bne.com.br"
    url = f"{base}/busca?q=jovem+aprendiz+{quote_plus(CIDADE)}"

    soup = get_soup(url)
    if not soup:
        return []

    vagas = []
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if looks_like_job_title(txt):
            link = normalize_link(base, a["href"])
            vagas.append(wrap(txt, link, "BNE"))
    return vagas


def buscar_empregos_com_br():
    base = "https://www.empregos.com.br"
    url = f"{base}/vagas?palavra=jovem+aprendiz+{quote_plus(CIDADE)}"

    soup = get_soup(url)
    if not soup:
        return []

    vagas = []
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if looks_like_job_title(txt):
            link = normalize_link(base, a["href"])
            vagas.append(wrap(txt, link, "Empregos.com.br"))
    return vagas


def buscar_jooble():
    base = "https://br.jooble.org"
    url = f"{base}/search?q=jovem+aprendiz+{quote_plus(CIDADE)}"

    soup = get_soup(url)
    if not soup:
        return []

    vagas = []
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if looks_like_job_title(txt):
            link = normalize_link(base, a["href"])
            vagas.append(wrap(txt, link, "Jooble"))
    return vagas


def buscar_catho():
    base = "https://www.catho.com.br"
    url = f"{base}/vagas?q=jovem+aprendiz+{quote_plus(CIDADE)}"

    soup = get_soup(url)
    if not soup:
        return []

    vagas = []
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if looks_like_job_title(txt):
            link = normalize_link(base, a["href"])
            vagas.append(wrap(txt, link, "Catho"))
    return vagas

# ===================== CONSOLIDAÇÃO =====================

def buscar_todas():
    fontes = [
        buscar_trabalhabrasil,
        buscar_indeed,
        buscar_infojobs,
        buscar_bne,
        buscar_empregos_com_br,
        buscar_jooble,
        buscar_catho
    ]

    todas = []

    for f in fontes:
        try:
            achadas = f()
            todas.extend(achadas)
        except Exception as e:
            print(f"[ERRO] Fonte {f.__name__} falhou →", e)
        time.sleep(0.7)

    # Remover duplicadas (link)
    unico = {v["link"]: v for v in todas}

    # Filtrar Jequitinhonha
    return [v for v in unico.values() if filtrar_jequitinhonha(v)]

# ===================== LOOP PRINCIPAL =====================

def main():
    seen = load_seen()

    while True:
        try:
            vagas = buscar_todas()

            # salvar JSON para o site (idêntico ao antigo)
            try:
                os.makedirs("./site", exist_ok=True)
                with open(VAGAS_JSON, "w", encoding="utf-8") as f:
                    json.dump(vagas, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print("Erro salvando vagas.json:", e)

            novas = [v for v in vagas if v["link"] not in seen]

            if novas:
                msg = "🚨 *Novas vagas de Jovem Aprendiz em Jequitinhonha/MG:*\n\n"
                for v in novas:
                    msg += f"🔹 {v['title']}\n🔗 {v['link']}\n\n"
                msg += "Boa sorte!"

                send_telegram(msg)

                for v in novas:
                    seen.add(v["link"])
                save_seen(seen)

            time.sleep(CHECK_INTERVAL_SECONDS)

        except Exception as e:
            print("Erro no loop principal:", e)
            time.sleep(180)

if __name__ == "__main__":
    main()
