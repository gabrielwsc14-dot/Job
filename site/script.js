// script.js - versão com thumb e background support
const DEFAULT_REMOTE_JSON = "";
const AUTO_REFRESH_MINUTES = 60;

const listEl = document.getElementById("list");
const lastCollectedEl = document.getElementById("lastCollected");
const totalCountEl = document.getElementById("totalCount");
const filterEl = document.getElementById("filter");
const orderEl = document.getElementById("order");
const refreshBtn = document.getElementById("refreshBtn");
const remoteUrlInput = document.getElementById("remoteUrl");
const autoToggleBtn = document.getElementById("autoToggle");

let autoInterval = null;
let autoMinutes = AUTO_REFRESH_MINUTES;
remoteUrlInput.value = DEFAULT_REMOTE_JSON || "";
autoToggleBtn.textContent = `Auto: ${autoMinutes}min`;

async function fetchJson() {
  try {
    const r = await fetch("vagas.json", { cache: "no-cache" });
    if (!r.ok) throw new Error("Erro HTTP " + r.status);
    const data = await r.json();
    console.log("JSON carregado:", data);
    return data;
  } catch (e) {
    console.error("Falha ao buscar vagas.json:", e);
    return [];
  }
}


function isoToDate(iso) {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? new Date(0) : d;
}

function isoToDate(iso) {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? new Date(0) : d;
}

function isoToDate(iso) {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? new Date(0) : d;
}

function filterItems(items, range) {
  if (!items) return [];
  const now = new Date();
  let cutoff = new Date(0);
  if (range === "day") cutoff = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  else if (range === "week") cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  else if (range === "month") cutoff = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  return items.filter(it => {
    const d = isoToDate(it.collected_at);
    return d >= cutoff;
  });
}

function filterJequitinhonha(items) {
  return items.filter(it => {
    const txt = `${it.title || ""} ${it.description || ""} ${it.location || ""}`.toLowerCase();
    return txt.includes("jequitinhonha");
  });
}

function render(items) {
  listEl.innerHTML = "";
  if (!items || items.length === 0) {
    listEl.innerHTML = '<div class="empty">Nenhuma vaga encontrada para o filtro selecionado.</div>';
    totalCountEl.textContent = "0";
    lastCollectedEl.textContent = "—";
    return;
  }

  items.forEach(it => {
    const d = isoToDate(it.collected_at);

    const card = document.createElement("article");
    card.className = "card";

    // imagem/thumb: usar it.thumbnail (se existir) ou fallback local
    const thumb = document.createElement("img");
    thumb.className = "thumb";
    thumb.alt = it.title || "vaga";
    // se o JSON trouxer uma url absoluta, usar; senão usar padrão local
    thumb.src = (it.thumbnail && it.thumbnail.startsWith("http"))
  ? it.thumbnail : "./img/vagas-img.jpg";

    // conteúdo textual do card
    const content = document.createElement("div");
    content.className = "content";

    const top = document.createElement("div");
    top.className = "top";

    const a = document.createElement("a");
    a.href = it.link || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = it.title || "(sem título)";

    const origin = document.createElement("div");
    origin.className = "origin";
    origin.textContent = it.origin || (it.source || "");

    top.appendChild(a);
    top.appendChild(origin);

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `Coletado: ${d.toLocaleString()}${it.link ? " • " + it.link : ""}`;

    // botão Candidatar (opcional)
    const btn = document.createElement("button");
    btn.className = "apply";
    btn.textContent = "Candidatar";
    btn.onclick = () => {
      if (it.link) window.open(it.link, "_blank");
    };

    content.appendChild(top);
    content.appendChild(meta);
    content.appendChild(btn);

    // montar card: thumb + content
    card.appendChild(thumb);
    card.appendChild(content);
    listEl.appendChild(card);
  });

  totalCountEl.textContent = items.length;
  const sorted = items.slice().sort((a,b)=> new Date(b.collected_at) - new Date(a.collected_at));
  lastCollectedEl.textContent = new Date(sorted[0].collected_at).toLocaleString();
}

async function loadAndRender() {
  refreshBtn.disabled = true;
  refreshBtn.textContent = "Carregando...";
  try {
    const data = await fetchJson();
    if (!data) {
      listEl.innerHTML = '<div class="empty">Não foi possível carregar vagas.json (remoto/local).</div>';
      lastCollectedEl.textContent = "—";
      totalCountEl.textContent = "0";
      return;
    }

    const order = orderEl.value;
    let items = Array.isArray(data) ? data.slice() : (Array.isArray(data.items) ? data.items.slice() : []);
    // se for um objeto simples (ex: {items:[...]}) tenta pegar items
    items.sort((a,b) => {
      const da = new Date(a.collected_at).getTime();
      const db = new Date(b.collected_at).getTime();
      return order === "asc" ? da - db : db - da;
    });

    let filtered = filterJequitinhonha(items);
    filtered = filterItems(filtered, filterEl.value);

    render(filtered);
  } catch (e) {
    console.error("Erro ao carregar/mostrar vagas:", e);
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = "Atualizar";
  }
}

function startAuto() {
  stopAuto();
  autoInterval = setInterval(loadAndRender, autoMinutes * 60 * 1000);
  autoToggleBtn.textContent = `Auto: ${autoMinutes}min (ON)`;
}
function stopAuto() {
  if (autoInterval) {
    clearInterval(autoInterval);
    autoInterval = null;
  }
  autoToggleBtn.textContent = `Auto: ${autoMinutes}min (OFF)`;
}

refreshBtn.addEventListener("click", loadAndRender);
filterEl.addEventListener("change", loadAndRender);
orderEl.addEventListener("change", loadAndRender);
remoteUrlInput.addEventListener("change", loadAndRender);
autoToggleBtn.addEventListener("click", () => {
  if (autoInterval) stopAuto();
  else startAuto();
});

loadAndRender();
startAuto();