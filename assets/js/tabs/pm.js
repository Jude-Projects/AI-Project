/* Project Management tab — Gantt of releases + task list. Source:
   plan.releases[] for the bars (week_start/week_end — this plan has no
   calendar dates assigned yet, so the Gantt is week-relative, not
   date-based) and per story plan.due_on/due_baseline_on when present
   (the gap between them would be slippage — shown, never hidden),
   joined against progress.stories[].verification for status. Sample
   mode fabricates a plausible mix of statuses so the finished look is
   visible; release/story content itself is real either way, since
   that's plan content, not a system-produced result. */

window.TABS = window.TABS || {};

const SAMPLE_STATE_BY_STORY = {
  "STORY-001": "verified",
  "STORY-002": "verified",
  "STORY-003": "verified",
  "STORY-004": "in_progress",
  "STORY-005": "in_progress",
  "STORY-011": "submitted",
  "STORY-012": "not_started",
  "STORY-006": "not_started",
  "STORY-007": "not_started",
  "STORY-013": "not_started",
  "STORY-014": "not_started",
  "STORY-008": "not_started",
  "STORY-009": "not_started",
  "STORY-010": "not_started",
};

function weekRange(releases) {
  const starts = releases.map((r) => r.week_start).filter((n) => typeof n === "number");
  const ends = releases.map((r) => r.week_end).filter((n) => typeof n === "number");
  const min = starts.length ? Math.min(...starts) : 1;
  const max = ends.length ? Math.max(...ends) : min + 1;
  return { min, max, span: Math.max(1, max - min + 1) };
}

function pctFromWeek(range, week, edge) {
  const w = typeof week === "number" ? week : range.min;
  const offset = edge === "end" ? w - range.min + 1 : w - range.min;
  return (offset / range.span) * 100;
}

function ganttHtml(plan) {
  const releases = plan.releases || [];
  const hasWeeks = releases.some((r) => typeof r.week_start === "number");
  if (!hasWeeks) {
    return `<div class="section"><h2>Releases</h2>${emptyState("No schedule yet", "This plan's releases don't carry week or calendar bounds yet.")}</div>`;
  }
  const range = weekRange(releases);
  const anyDemoTarget = releases.some((r) => r.is_demo_target);

  const rows = releases
    .map((r) => {
      const left = pctFromWeek(range, r.week_start, "start");
      const right = pctFromWeek(range, r.week_end, "end");
      const width = Math.max(2, right - left);
      return `
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
        <div style="width:150px; flex-shrink:0; font-size:0.82rem; font-weight:600;">
          ${esc(r.key)} ${r.is_demo_target ? '<span class="pill ok" style="margin-left:4px;">Demo target</span>' : ""}
        </div>
        <div style="position:relative; flex:1; height:26px; background:var(--surface-alt); border-radius:4px;">
          <div title="${esc(r.name)}: week ${esc(r.week_start)} to week ${esc(r.week_end)}${r.goal ? ` — ${esc(r.goal)}` : ""}"
               style="position:absolute; left:${left}%; width:${width}%; top:0; bottom:0; background:${r.is_demo_target ? "var(--accent)" : "var(--grey)"}; border-radius:4px; opacity:${r.is_demo_target ? 1 : 0.55};">
          </div>
        </div>
        <div style="width:230px; flex-shrink:0; font-size:0.78rem; color:var(--text-muted);">${esc(r.name)}</div>
      </div>`;
    })
    .join("");

  return `
    <div class="section">
      <h2>Releases</h2>
      <p class="card-sub">Week ${esc(range.min)} &rarr; week ${esc(range.max)}. No calendar dates are set for this build yet, so this is week-relative, not date-based. ${anyDemoTarget ? "Releases after the demo-target release are the roadmap, not this term's work." : "No release is currently marked as the demo target."}</p>
      <div style="position:relative;">
        ${rows}
      </div>
    </div>
  `;
}

function dueLabel(dateStr) {
  return dateStr ? esc(dateStr) : "Not yet scheduled";
}

function taskTableHtml(state, mode) {
  const isSample = mode === "sample";
  const stories = state.joinedStories.slice().sort((a, b) => {
    if (a.due_on && b.due_on) return a.due_on < b.due_on ? -1 : 1;
    if (a.due_on) return -1;
    if (b.due_on) return 1;
    return a.release < b.release ? -1 : a.release > b.release ? 1 : a.id < b.id ? -1 : 1;
  });
  return `
    <div class="section">
      <h2>Tasks</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Story</th><th>Title</th><th>Release</th><th>Due</th><th>Originally due</th><th>Status</th></tr></thead>
          <tbody>
          ${stories
            .map((s) => {
              const slipped = s.due_on && s.due_baseline_on && s.due_on !== s.due_baseline_on;
              const stateVal = isSample ? (SAMPLE_STATE_BY_STORY[s.id] || "not_started") : s.verification.state;
              return `<tr>
                <td><a href="#pm/${s.id}">${s.id}</a></td>
                <td>${esc(s.title)}</td>
                <td>${esc(s.release)}</td>
                <td>${dueLabel(s.due_on)}</td>
                <td>${dueLabel(s.due_baseline_on)}${slipped ? ` <span class="pill warn">slipped</span>` : ""}</td>
                <td>${verificationPill(stateVal)}</td>
              </tr>`;
            })
            .join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function pmList(container, state, mode) {
  const isSample = mode === "sample";
  container.innerHTML = `
    ${sampleBanner(isSample, "task status below is a fabricated mix so you can see verified/in-progress/not-started states.")}
    <h1>Project Management${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <p class="lede">A Gantt view of releases, and every task underneath it with its due date. Click a task to open its detail.</p>
    ${ganttHtml(state.plan)}
    ${taskTableHtml(state, mode)}
  `;
}

function pmDetail(container, state, mode, storyId) {
  const isSample = mode === "sample";
  const story = findStory(state, storyId);
  if (!story) {
    container.innerHTML = `${breadcrumb("Project Management", "pm", "Not found")}${emptyState("Not found", "No story with this id exists in the plan.")}`;
    return;
  }
  const release = (state.plan.releases || []).find((r) => r.key === story.release);
  const stateVal = isSample ? (SAMPLE_STATE_BY_STORY[story.id] || "not_started") : story.verification.state;
  const slipped = story.due_on && story.due_baseline_on && story.due_on !== story.due_baseline_on;

  container.innerHTML = `
    ${sampleBanner(isSample)}
    ${breadcrumb("Project Management", "pm", story.id)}
    <h1>${story.id}: ${esc(story.title)}${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <div class="section">
      <p style="font-size:1.02rem;">${esc(story.narrative)}</p>
      <table style="margin-top:10px;">
        <tbody>
          <tr><th>Release</th><td>${esc(story.release)}${release ? ` — ${esc(release.name)}` : ""}</td></tr>
          <tr><th>Owner</th><td>${esc(story.owner_agent)}</td></tr>
          <tr><th>Due</th><td>${dueLabel(story.due_on)}</td></tr>
          <tr><th>Originally due</th><td>${dueLabel(story.due_baseline_on)} ${slipped ? `<span class="pill warn">slipped</span>` : (story.due_on && story.due_baseline_on ? `<span class="pill grey">no slippage</span>` : "")}</td></tr>
          <tr><th>Status</th><td>${verificationPill(stateVal)}</td></tr>
          <tr><th>Criteria</th><td>${isSample ? "—" : `${story.verification.criteria_passed || 0} of ${story.verification.criteria_total || 0}`}</td></tr>
          <tr><th>Commit</th><td>${
            story.verification.commit_sha
              ? (story.verification.commit_url ? `<a href="${esc(story.verification.commit_url)}">${esc(story.verification.commit_sha.slice(0, 7))}</a>` : esc(story.verification.commit_sha))
              : "—"
          }</td></tr>
          <tr><th>Points</th><td>${isSample ? "—" : (story.verification.points_awarded || 0)}</td></tr>
        </tbody>
      </table>
    </div>
    ${
      story.acceptance && story.acceptance.length
        ? `<div class="section"><h2>Acceptance criteria</h2><ul>${story.acceptance.map((c) => `<li>${esc(c)}</li>`).join("")}</ul></div>`
        : ""
    }
  `;
}

window.TABS.pm = function renderPm(container, state, mode, subpath) {
  if (subpath && subpath[0]) {
    pmDetail(container, state, mode, subpath[0]);
  } else {
    pmList(container, state, mode);
  }
};
