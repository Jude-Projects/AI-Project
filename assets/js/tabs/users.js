/* Users & Use Case tab — who this is for, taken from the stories' own
   "As a <role>, I want ..." narratives rather than invented personas.
   Source: plan.derived.roles (the extracted list) and
   plan.stories[].narrative for the drill-down. This content is real
   plan structure, not a system-produced result, so it does not change
   between Real and Sample mode. */

window.TABS = window.TABS || {};

function extractRole(narrative) {
  const m = /^As an? (.+?),/.exec(narrative || "");
  return m ? m[1] : null;
}

function storiesForRole(state, role) {
  return state.joinedStories.filter((s) => extractRole(s.narrative) === role);
}

function usersList(container, state, mode) {
  const roles = state.plan.derived.roles || [];
  container.innerHTML = `
    ${sampleBanner(mode === "sample", "role definitions below are real plan content and don't change with the toggle.")}
    <h1>Users & Use Case</h1>
    <p class="lede">Who this is for and what they're trying to get done, taken directly from the "As a &lt;role&gt;, I want …" wording in each story.</p>
    <div class="card-grid">
      ${roles
        .map((role) => {
          const stories = storiesForRole(state, role);
          return `
        <a class="card" href="#users/${encodeURIComponent(role)}">
          <span class="card-label">Role</span>
          <span class="card-value" style="font-size:1.2rem;">${esc(role)}</span>
          <span class="card-sub">${stories.length} stor${stories.length === 1 ? "y" : "ies"}</span>
          <span class="card-drill">See narratives &rarr;</span>
        </a>`;
        })
        .join("")}
    </div>
  `;
}

function usersDetail(container, state, mode, roleRaw) {
  const role = decodeURIComponent(roleRaw);
  const stories = storiesForRole(state, role);
  container.innerHTML = `
    ${breadcrumb("Users & Use Case", "users", esc(role))}
    <h1>${esc(role)}</h1>
    ${
      stories.length
        ? `<div class="table-wrap"><table>
        <thead><tr><th>Story</th><th>Narrative</th><th>Release</th><th>Status</th></tr></thead>
        <tbody>
        ${stories
          .map(
            (s) => `<tr>
              <td><a href="#pm/${s.id}">${s.id}</a></td>
              <td>${esc(s.narrative)}</td>
              <td>${esc(s.release)}</td>
              <td>${verificationPill(s.verification.state)}</td>
            </tr>`
          )
          .join("")}
        </tbody>
      </table></div>`
        : emptyState("No stories found", "No story in the plan currently carries this role in its narrative.")
    }
  `;
}

window.TABS.users = function renderUsers(container, state, mode, subpath) {
  if (subpath && subpath[0]) {
    usersDetail(container, state, mode, subpath[0]);
  } else {
    usersList(container, state, mode);
  }
};
