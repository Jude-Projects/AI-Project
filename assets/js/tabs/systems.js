/* Systems tab — what this connects to. Source: plan.derived.systems is
   just a list of names; nothing in this repo can say whether any of
   them is actually connected right now, so every indicator renders grey
   until a real running system reports otherwise. Sample mode fabricates
   a "connected" state so the finished look is visible. */

window.TABS = window.TABS || {};

function systemsList(container, state, mode) {
  const isSample = mode === "sample";
  const systems = state.plan.derived.systems || [];

  container.innerHTML = `
    ${sampleBanner(isSample, "connection status below is fabricated — nothing in this repo can check a live connection.")}
    <h1>Systems${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <p class="lede">What this connects to. None of these are connected on day one — the indicator says so honestly rather than defaulting to green.</p>
    <div class="table-wrap">
      <table>
        <thead><tr><th>System</th><th>Status</th><th>Last checked</th></tr></thead>
        <tbody>
          ${systems
            .map(
              (name) => `
            <tr>
              <td><a href="#systems/${encodeURIComponent(name)}">${esc(name)}</a></td>
              <td>${
                isSample
                  ? `<span class="dot ok"></span><span class="pill ok">Connected</span>`
                  : `<span class="dot"></span><span class="pill grey">Not checked from here</span>`
              }</td>
              <td>${isSample ? "moments ago (sample)" : "never"}</td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function systemsDetail(container, state, mode, nameRaw) {
  const name = decodeURIComponent(nameRaw);
  const isSample = mode === "sample";
  const known = (state.plan.derived.systems || []).includes(name);

  container.innerHTML = `
    ${sampleBanner(isSample)}
    ${breadcrumb("Systems", "systems", esc(name))}
    <h1>${esc(name)}${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    ${
      known
        ? `<div class="section">
            <p>${
              isSample
                ? `<span class="dot ok"></span><span class="pill ok">Connected</span> (sample)`
                : `<span class="dot"></span><span class="pill grey">Not checked from here</span>`
            }</p>
            <p class="card-sub">This page is static and holds no credentials, so it cannot open a live connection to check this itself. A real status here has to come from the running system reporting it back, which hasn't happened yet.</p>
          </div>`
        : emptyState("Unknown system", "This system isn't listed in the plan.")
    }
  `;
}

window.TABS.systems = function renderSystems(container, state, mode, subpath) {
  if (subpath && subpath[0]) {
    systemsDetail(container, state, mode, subpath[0]);
  } else {
    systemsList(container, state, mode);
  }
};
