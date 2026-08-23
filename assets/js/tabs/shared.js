/* Shared helpers used across tab renderers — kept here once rather than
   copy-pasted per tab (breadcrumb markup, status pills, lookups). */

window.TABS = window.TABS || {};

function sampleBanner(isSample, msg) {
  return isSample
    ? `<div class="sample-banner">SAMPLE DATA — ${msg || "fabricated data shown so you can see the shape of this tab."} Switch to Real to see what the project has actually produced.</div>`
    : "";
}

function breadcrumb(parentLabel, parentHash, currentLabel) {
  return `<div class="breadcrumb"><a href="#${parentHash}">&larr; ${parentLabel}</a> / ${currentLabel}</div>`;
}

function findStory(state, id) {
  return state.joinedStories.find((s) => s.id === id);
}

function findRequirement(state, id) {
  return (state.plan.requirements || []).find((r) => r.id === id);
}

const STATE_TONE = {
  verified: "ok",
  submitted: "warn",
  in_progress: "warn",
  not_started: "grey",
};

const STATE_LABEL = {
  verified: "Verified",
  submitted: "Submitted",
  in_progress: "In progress",
  not_started: "Not started",
};

function verificationPill(state) {
  const tone = STATE_TONE[state] || "grey";
  const label = STATE_LABEL[state] || state || "unknown";
  return `<span class="pill ${tone}">${label}</span>`;
}

function emptyState(title, body) {
  return `<div class="empty-state"><strong>${title}</strong>${body}</div>`;
}

function esc(str) {
  const div = document.createElement("div");
  div.textContent = String(str == null ? "" : str);
  return div.innerHTML;
}
