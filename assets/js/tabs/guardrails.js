/* Guardrails tab — what must never happen. Source: plan.derived.guardrails
   + plan.requirements[].fulfilled_by, cross-checked against each story's
   verification.state in progress.json. A guardrail whose stories aren't
   verified is an unkept promise, and this tab says so in those words. */

window.TABS = window.TABS || {};

function guardrailEnforcement(state, guardrailId) {
  const req = findRequirement(state, guardrailId);
  const storyIds = req ? req.fulfilled_by || [] : [];
  const stories = storyIds.map((id) => findStory(state, id)).filter(Boolean);
  const allVerified = stories.length > 0 && stories.every((s) => s.verification.state === "verified");
  return { req, stories, allVerified };
}

function guardrailsList(container, state, mode) {
  const isSample = mode === "sample";
  const guardrails = state.plan.derived.guardrails || [];

  container.innerHTML = `
    ${sampleBanner(isSample, "enforcement status below is fabricated to show what an enforced guardrail looks like.")}
    <h1>Guardrails${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <p class="lede">The promises this system makes. Each one is shown against whether anything in the build currently enforces it.</p>
    ${
      guardrails.length
        ? `<div class="card-grid">${guardrails
            .map((g) => {
              const { stories, allVerified } = guardrailEnforcement(state, g.id);
              const enforced = isSample ? true : allVerified;
              return `
          <a class="card" href="#guardrails/${g.id}">
            <span class="card-label">${g.id}</span>
            <span class="card-sub" style="color:var(--text);">${esc(g.statement)}</span>
            <span class="card-value" style="font-size:1rem;">${
              enforced
                ? `<span class="pill ok">Enforced</span>`
                : `<span class="pill grey">${stories.length ? "Not yet kept" : "Not yet covered"}</span>`
            }</span>
            <span class="card-drill">Details &rarr;</span>
          </a>`;
            })
            .join("")}</div>`
        : emptyState(
            "No guardrails defined",
            "This plan has no SAFE-priority requirement, so there is nothing to show here yet. That's worth fixing before the build goes further."
          )
    }
  `;
}

function guardrailsDetail(container, state, mode, id) {
  const isSample = mode === "sample";
  const guardrails = state.plan.derived.guardrails || [];
  const g = guardrails.find((x) => x.id === id);
  if (!g) {
    container.innerHTML = `${breadcrumb("Guardrails", "guardrails", "Not found")}${emptyState("Not found", "No guardrail with this id exists in the plan.")}`;
    return;
  }
  const { req, stories, allVerified } = guardrailEnforcement(state, g.id);
  const enforced = isSample ? true : allVerified;

  container.innerHTML = `
    ${sampleBanner(isSample)}
    ${breadcrumb("Guardrails", "guardrails", g.id)}
    <h1>${g.id}${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <div class="section">
      <p style="font-size:1.05rem;">${esc(g.statement)}</p>
      <p>${enforced ? `<span class="pill ok">Enforced</span>` : `<span class="pill grey">Not yet kept</span>`}
        ${req ? `<span class="card-sub">(kind: ${esc(req.kind)}, priority: ${esc(req.priority)})</span>` : ""}
      </p>
    </div>
    <h2>Stories that fulfil this requirement</h2>
    ${
      stories.length
        ? `<div class="table-wrap"><table>
          <thead><tr><th>Story</th><th>Title</th><th>Status</th></tr></thead>
          <tbody>
          ${stories
            .map(
              (s) => `<tr><td><a href="#pm/${s.id}">${s.id}</a></td><td>${esc(s.title)}</td><td>${verificationPill(isSample ? "verified" : s.verification.state)}</td></tr>`
            )
            .join("")}
          </tbody>
        </table></div>`
        : emptyState("No story fulfils this requirement yet", "This requirement has no fulfilled_by story linked in the plan — that's a real gap, not a rendering issue.")
    }
  `;
}

window.TABS.guardrails = function renderGuardrails(container, state, mode, subpath) {
  if (subpath && subpath[0]) {
    guardrailsDetail(container, state, mode, subpath[0]);
  } else {
    guardrailsList(container, state, mode);
  }
};
