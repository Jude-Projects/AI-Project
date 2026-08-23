/* App shell: loads data once, renders header/nav, and routes hash changes
   to the tab renderer registered in window.TABS. Only "overview" has a
   real renderer today — every other tab falls back to the shared
   "not built yet" placeholder so it stays reachable, never locked. */

const TAB_ORDER = [
  { id: "overview", label: "Overview" },
  { id: "outcomes", label: "Outcomes" },
  { id: "users", label: "Users & Use Case" },
  { id: "guardrails", label: "Guardrails" },
  { id: "systems", label: "Systems" },
  { id: "pm", label: "Project Management" },
  { id: "agents", label: "AI Agents" },
  { id: "kb", label: "Knowledge Base" },
  { id: "datamodel", label: "Data Model" },
];

const MODE_KEY = "cc_mode"; // "sample" | "real"

function getMode() {
  try {
    return localStorage.getItem(MODE_KEY) === "sample" ? "sample" : "real";
  } catch (e) {
    return "real";
  }
}

function setMode(mode) {
  try {
    localStorage.setItem(MODE_KEY, mode);
  } catch (e) {
    /* storage unavailable — mode just won't persist across reloads */
  }
}

function renderPlaceholder(container, tabLabel) {
  container.innerHTML = `
    <h1>${tabLabel}</h1>
    <div class="empty-state">
      <strong>Not built yet</strong>
      Say <strong>build the rest</strong> when the Overview tab looks right, and this tab gets built next.
    </div>
  `;
}

function renderHeader(state) {
  const stampEl = document.getElementById("data-stamp");
  const { manifest } = state;
  const label = dataAsOfLabel(manifest.generated_at);
  const { isStale } = manifestAge(manifest.generated_at);
  stampEl.textContent = isStale ? `${label} — sync from the portal to refresh` : label;
  stampEl.classList.toggle("stale", isStale);
}

function renderModeToggle(state) {
  const el = document.getElementById("mode-toggle");
  const mode = getMode();
  el.innerHTML = `
    <button data-mode="real" class="${mode === "real" ? "active" : ""}">Real</button>
    <button data-mode="sample" class="${mode === "sample" ? "active sample-active" : ""}">Sample</button>
  `;
  el.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      setMode(btn.dataset.mode);
      renderModeToggle(state);
      route(state);
    });
  });
}

function currentTabId() {
  const raw = location.hash.replace("#", "");
  return (raw.split("/")[0] || "overview");
}

function renderNav() {
  const nav = document.getElementById("tab-nav");
  const current = currentTabId();
  nav.innerHTML = TAB_ORDER.map(
    (t) => `<a href="#${t.id}" class="${t.id === current ? "active" : ""}">${t.label}</a>`
  ).join("");
}

function route(state) {
  renderNav();
  const raw = location.hash.replace("#", "");
  const parts = raw.split("/").filter(Boolean);
  const tabId = parts[0] || "overview";
  const subpath = parts.slice(1);
  const tab = TAB_ORDER.find((t) => t.id === tabId) || TAB_ORDER[0];
  const main = document.getElementById("tab-content");
  const mode = getMode();

  if (window.TABS && typeof window.TABS[tab.id] === "function") {
    window.TABS[tab.id](main, state, mode, subpath);
  } else {
    renderPlaceholder(main, tab.label);
  }
}

async function init() {
  const main = document.getElementById("tab-content");
  try {
    const state = await loadColaberryData();
    renderHeader(state);
    renderModeToggle(state);
    window.addEventListener("hashchange", () => route(state));
    route(state);
  } catch (err) {
    main.innerHTML = `
      <div class="empty-state">
        <strong>Could not load project data</strong>
        ${err.message}. The Command Center reads .colaberry/plan.json, progress.json and manifest.json at runtime — confirm they are committed and being served alongside this page.
      </div>
    `;
  }
}

document.addEventListener("DOMContentLoaded", init);
