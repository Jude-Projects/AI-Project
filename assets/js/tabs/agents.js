/* AI Agents tab — this plan carries no scoped agent roster yet, so the
   roster shown here is built live from each story's owner_agent field.
   These are owners, not scoped AI agents, and the tab says so rather than
   presenting a job title as if it were an autonomous agent. There is no
   run history in these files — real mode says "no runs recorded", never a
   fabricated 0% success rate, which would read as a failing agent. */

window.TABS = window.TABS || {};

const SAMPLE_RUNS = {
  "Data Analyst": { runs: 14, success_rate: "93%" },
  "Business User": { runs: 9, success_rate: "89%" },
  "Data Visualization Specialist": { runs: 4, success_rate: "100%" },
  "Business Analyst": { runs: 3, success_rate: "100%" },
  "System Administrator": { runs: 1, success_rate: "100%" },
  "Data Engineer": { runs: 6, success_rate: "83%" },
  "User": { runs: 11, success_rate: "91%" },
  "Executive": { runs: 2, success_rate: "100%" },
};

function ownerStories(state, storyIds) {
  return storyIds.map((id) => findStory(state, id)).filter(Boolean);
}

function deriveOwners(state) {
  const byRole = new Map();
  state.joinedStories.forEach((s) => {
    if (!s.owner_agent) return;
    if (!byRole.has(s.owner_agent)) byRole.set(s.owner_agent, []);
    byRole.get(s.owner_agent).push(s.id);
  });
  return Array.from(byRole.entries()).map(([role, story_ids]) => ({ role, story_ids }));
}

function agentsList(container, state, mode) {
  const isSample = mode === "sample";
  const owners = deriveOwners(state);

  container.innerHTML = `
    ${sampleBanner(isSample, "run counts and success rates below are fabricated — no run history exists in these files.")}
    <h1>AI Agents${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <p class="lede">Your plan does not carry a scoped agent roster yet. These are story <strong>owners</strong>, not AI agents — shown here as the closest available roster.</p>
    <div class="card-grid">
      ${owners
        .map((o) => {
          const stories = ownerStories(state, o.story_ids);
          const run = SAMPLE_RUNS[o.role];
          return `
        <a class="card" href="#agents/${encodeURIComponent(o.role)}">
          <span class="card-label">Owner</span>
          <span class="card-value" style="font-size:1.15rem;">${esc(o.role)}</span>
          <span class="card-sub">Owns ${stories.length} stor${stories.length === 1 ? "y" : "ies"}</span>
          <span class="card-sub">${isSample && run ? `${run.runs} runs recorded (sample), ${run.success_rate} success` : "No runs recorded"}</span>
          <span class="card-drill">Details &rarr;</span>
        </a>`;
        })
        .join("")}
    </div>
  `;
}

function agentsDetail(container, state, mode, roleRaw) {
  const role = decodeURIComponent(roleRaw);
  const isSample = mode === "sample";
  const owner = deriveOwners(state).find((o) => o.role === role);
  if (!owner) {
    container.innerHTML = `${breadcrumb("AI Agents", "agents", "Not found")}${emptyState("Not found", "No owner with this role exists in the plan.")}`;
    return;
  }
  const stories = ownerStories(state, owner.story_ids);
  const run = SAMPLE_RUNS[role];

  container.innerHTML = `
    ${sampleBanner(isSample)}
    ${breadcrumb("AI Agents", "agents", esc(role))}
    <h1>${esc(role)}${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <div class="section">
      <table>
        <tbody>
          <tr><th>Role</th><td>${esc(role)} (story owner, not a scoped AI agent)</td></tr>
          <tr><th>Skills</th><td>No skills registered yet</td></tr>
          <tr><th>Run history</th><td>${isSample && run ? `${run.runs} runs recorded (sample), ${run.success_rate} success rate` : "No runs recorded"}</td></tr>
        </tbody>
      </table>
    </div>
    <h2>Owned stories</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Story</th><th>Title</th><th>Release</th><th>Status</th></tr></thead>
        <tbody>
        ${stories
          .map(
            (s) => `<tr><td><a href="#pm/${s.id}">${s.id}</a></td><td>${esc(s.title)}</td><td>${esc(s.release)}</td><td>${verificationPill(s.verification.state)}</td></tr>`
          )
          .join("")}
        </tbody>
      </table>
    </div>
  `;
}

window.TABS.agents = function renderAgents(container, state, mode, subpath) {
  if (subpath && subpath[0]) {
    agentsDetail(container, state, mode, subpath[0]);
  } else {
    agentsList(container, state, mode);
  }
};
