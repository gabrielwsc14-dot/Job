// script.js
// Ajustes:
// - DEFAULT_REMOTE_JSON: troque pela URL RAW do seu repo (opcional).
// - AUTO_REFRESH_MINUTES: auto refresh padrão (60) — pode ser alternado pela UI.

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
  const remote = remoteUrlInput.value.trim();
  if (remote) {
    try {
      const r = await fetch(remote, { cache: "no-cache" });
      if (r.ok) return await r.json();
    } catch (e) {
      console.warn("Falha ao buscar JSON remoto:", e);
    }
  }
  try {
    const r2 = await fetch("vagas.json", { cache: "no-cache" });
    if (r2.ok) return await r2.json();
  } catch (e) {
    console.warn("Falha ao buscar vagas.json local:", e);
  }
  return null;
}

function isoToDate(iso) {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? new Date(0) : d;
}

// ✅ Filtro de data ajustado
function filterItems(items, range) {
  if (!items) return [];

  const now = new Date();
  let cutoff = new Date(0);

  if (range === "day") {
    cutoff = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  } else if (range === "week") {
    cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  } else if (range === "month") {
    cutoff = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  }

  return items.filter(it => {
    const d = isoToDate(it.collected_at);
    return d >= cutoff;
  });
}

// ✅ Filtro de cidade (Jequitinhonha)
function filterJequitinhonha(items) {
  return items.filter(it => {
    const txt = `${it.title} ${it.description || ""} ${it.location || ""}`.toLowerCase();
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

    const top = document.createElement("div");
    top.className = "top";
    const a = document.createElement("a");
    a.href = it.link || "#";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = it.title || "(sem título)";
    const origin = document.createElement("div");
    origin.className = "origin";
    origin.textContent = it.origin || "";
    top.appendChild(a);
    top.appendChild(origin);

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `Coletado: ${d.toLocaleString()} • ${it.link || ""}`;

    card.appendChild(top);
    card.appendChild(meta);
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

    // Ordenação
    const order = orderEl.value;
    let items = data.slice();
    items.sort((a,b) => {
      const da = new Date(a.collected_at).getTime();
      const db = new Date(b.collected_at).getTime();
      return order === "asc" ? da - db : db - da;
    });

    // Filtro de cidade + data
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

// Auto refresh
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

// Eventos
refreshBtn.addEventListener("click", loadAndRender);
filterEl.addEventListener("change", loadAndRender);
orderEl.addEventListener("change", loadAndRender);
remoteUrlInput.addEventListener("change", loadAndRender);
autoToggleBtn.addEventListener("click", () => {
  if (autoInterval) stopAuto();
  else startAuto();
});

// Inicialização
loadAndRender();
startAuto();
