/* Knowledge Base tab — everything the project knows about itself.
   Source: plan.requirements[] and plan.stories[]. The traceability table
   is requirements joined to fulfilled_by stories and their verification
   state; a must-requirement with no fulfilled_by story is a real gap and
   is shown, not hidden. The chat panel is a plain keyword search over
   the data already loaded on this page — not a real model — and says so
   when it can't answer rather than guessing. */

window.TABS = window.TABS || {};

function reqRow(state, req) {
  const stories = (req.fulfilled_by || []).map((id) => findStory(state, id)).filter(Boolean);
  const allVerified = stories.length > 0 && stories.every((s) => s.verification.state === "verified");
  const isGap = (req.fulfilled_by || []).length === 0;
  return { req, stories, allVerified, isGap };
}

function traceabilityTable(state) {
  const rows = (state.plan.requirements || []).map((r) => reqRow(state, r));
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Req</th><th>Statement</th><th>Priority</th><th>Fulfilled by</th><th>Status</th></tr></thead>
        <tbody>
        ${rows
          .map(
            (row) => `<tr ${row.isGap && row.req.priority === "must" ? 'style="background:var(--danger-bg);"' : ""}>
              <td><a href="#kb/${row.req.id}">${row.req.id}</a></td>
              <td>${esc(row.req.statement)}</td>
              <td>${esc(row.req.priority)}</td>
              <td>${row.stories.length ? row.stories.map((s) => esc(s.id)).join(", ") : `<span class="pill danger">none — gap</span>`}</td>
              <td>${row.stories.length ? (row.allVerified ? `<span class="pill ok">Verified</span>` : `<span class="pill grey">Not yet</span>`) : "—"}</td>
            </tr>`
          )
          .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function answerQuestion(state, question) {
  const q = question.toLowerCase();

  const reqHit = (state.plan.requirements || []).find((r) => q.includes(r.id.toLowerCase()));
  if (reqHit) {
    const row = reqRow(state, reqHit);
    return {
      text: `${reqHit.id}: ${reqHit.statement} Fulfilled by: ${row.stories.length ? row.stories.map((s) => s.id).join(", ") : "no story yet (a gap)."}`,
      cite: "Knowledge Base — requirements",
    };
  }

  const storyHit = state.joinedStories.find((s) => q.includes(s.id.toLowerCase()));
  if (storyHit) {
    return {
      text: `${storyHit.id} (${storyHit.title}) is in release ${storyHit.release}${storyHit.due_on ? `, due ${storyHit.due_on}` : ""}, currently ${storyHit.verification.state}.`,
      cite: "Project Management",
    };
  }

  if (q.includes("guardrail") || q.includes("safe") || q.includes("encrypt")) {
    const g = (state.plan.derived.guardrails || [])[0];
    if (g) {
      return { text: `${g.id}: ${g.statement}`, cite: "Guardrails" };
    }
  }

  if (q.includes("demo")) {
    const demoRelease = (state.plan.releases || []).find((r) => r.is_demo_target);
    const text = state.plan.schedule && state.plan.schedule.demo_day
      ? `Demo day is ${state.plan.schedule.demo_day}. The demo-target release is ${demoRelease ? demoRelease.key : "not yet marked"}.`
      : `No calendar demo day is set yet. ${demoRelease ? `The demo-target release is ${demoRelease.key}.` : "No release is currently marked as the demo target."}`;
    return { text, cite: "Overview / Project Management" };
  }

  if (q.includes("role") || q.includes("user")) {
    return {
      text: `Roles in this plan: ${(state.plan.derived.roles || []).join(", ")}.`,
      cite: "Users & Use Case",
    };
  }

  if (q.includes("system") || q.includes("connect")) {
    return {
      text: `This project connects to: ${(state.plan.derived.systems || []).join(", ")}. None are checked as connected from this page.`,
      cite: "Systems",
    };
  }

  return null;
}

function chatPanelHtml() {
  return `
    <div class="section">
      <h2>Ask the Knowledge Base</h2>
      <p class="card-sub">A plain keyword search over the plan and progress data already loaded on this page — not a language model. Try a requirement id (e.g. REQ-015), a story id (e.g. STORY-001), or a word like "demo", "role", or "system". If it can't find an answer here, it says so.</p>
      <div style="display:flex; gap:8px; margin:10px 0;">
        <input id="kb-q" type="text" placeholder="Ask about this project…" style="flex:1; padding:8px 10px; border:1px solid var(--border); border-radius:6px; font-size:0.9rem;" />
        <button id="kb-ask" style="padding:8px 16px; border:1px solid var(--accent); background:var(--accent); color:#fff; border-radius:6px; font-weight:600;">Ask</button>
      </div>
      <div id="kb-answer"></div>
    </div>
  `;
}

function wireChatPanel(state) {
  const input = document.getElementById("kb-q");
  const btn = document.getElementById("kb-ask");
  const out = document.getElementById("kb-answer");
  if (!input || !btn || !out) return;

  const ask = () => {
    const q = input.value.trim();
    if (!q) return;
    const result = answerQuestion(state, q);
    out.innerHTML = result
      ? `<div class="section" style="background:var(--surface-alt);"><p>${esc(result.text)}</p><p class="card-sub">Source: ${esc(result.cite)}</p></div>`
      : `<div class="section" style="background:var(--surface-alt);"><p>I can't answer that from the data on this page.</p></div>`;
  };

  btn.addEventListener("click", ask);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") ask();
  });
}

function kbList(container, state) {
  container.innerHTML = `
    <h1>Knowledge Base</h1>
    <p class="lede">Requirements, stories, and traceability between them — plus a search assistant over this project's own data.</p>
    <div class="section">
      <h2>Traceability</h2>
      ${traceabilityTable(state)}
    </div>
    ${chatPanelHtml()}
  `;
  wireChatPanel(state);
}

function kbDetail(container, state, mode, reqId) {
  const req = findRequirement(state, reqId);
  if (!req) {
    container.innerHTML = `${breadcrumb("Knowledge Base", "kb", "Not found")}${emptyState("Not found", "No requirement with this id exists in the plan.")}`;
    return;
  }
  const row = reqRow(state, req);
  container.innerHTML = `
    ${breadcrumb("Knowledge Base", "kb", req.id)}
    <h1>${req.id}</h1>
    <div class="section">
      <p style="font-size:1.05rem;">${esc(req.statement)}</p>
      <table style="margin-top:10px;">
        <tbody>
          <tr><th>Kind</th><td>${esc(req.kind)}</td></tr>
          <tr><th>Priority</th><td>${esc(req.priority)}</td></tr>
          <tr><th>Cluster</th><td>${esc(req.cluster)}</td></tr>
        </tbody>
      </table>
    </div>
    <h2>Fulfilled by</h2>
    ${
      row.stories.length
        ? `<div class="table-wrap"><table>
          <thead><tr><th>Story</th><th>Title</th><th>Status</th></tr></thead>
          <tbody>
          ${row.stories.map((s) => `<tr><td><a href="#pm/${s.id}">${s.id}</a></td><td>${esc(s.title)}</td><td>${verificationPill(s.verification.state)}</td></tr>`).join("")}
          </tbody>
        </table></div>`
        : emptyState("Gap", "No story in the plan currently fulfils this requirement.")
    }
  `;
}

window.TABS.kb = function renderKb(container, state, mode, subpath) {
  if (subpath && subpath[0]) {
    kbDetail(container, state, mode, subpath[0]);
  } else {
    kbList(container, state);
  }
};
