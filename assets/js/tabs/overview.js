/* Overview tab — the 30-second screen. Reads plan.project, plan.schedule
   and progress.totals only; nothing here is computed by re-summing the
   story list (that would let this page and progress.json quietly
   disagree). Sample mode substitutes clearly-labelled fabricated totals
   so the shape of a finished dashboard is visible before the real system
   has produced anything. */

window.TABS = window.TABS || {};

const SAMPLE_TOTALS = {
  stories_total: 14,
  stories_verified: 6,
  criteria_total: 54,
  criteria_passed: 22,
  points_awarded: 38,
};

function schedulePosition(schedule) {
  if (!schedule || !schedule.build_start || !schedule.build_end || !schedule.demo_day) {
    return {
      status: "Not scheduled",
      detail: "No calendar dates have been set for this build yet.",
      tone: "grey",
    };
  }
  const now = new Date();
  const buildStart = new Date(schedule.build_start);
  const buildEnd = new Date(schedule.build_end);
  const demoDay = new Date(schedule.demo_day);
  const dayMs = 1000 * 60 * 60 * 24;

  if (now < buildStart) {
    const days = Math.ceil((buildStart - now) / dayMs);
    return {
      status: "Not started",
      detail: `Build begins ${schedule.build_start} — in ${days} day${days === 1 ? "" : "s"}.`,
      tone: "grey",
    };
  }
  if (now >= buildStart && now <= buildEnd) {
    const totalDays = Math.max(1, Math.round((buildEnd - buildStart) / dayMs));
    const elapsed = Math.round((now - buildStart) / dayMs);
    return {
      status: "In progress",
      detail: `Day ${Math.min(elapsed, totalDays)} of ${totalDays} — build ends ${schedule.build_end}.`,
      tone: "ok",
    };
  }
  if (now > buildEnd && now <= demoDay) {
    return {
      status: "Demo prep",
      detail: `Build ended ${schedule.build_end} — demo day is ${schedule.demo_day}.`,
      tone: "warn",
    };
  }
  return {
    status: "Past demo day",
    detail: `Demo day (${schedule.demo_day}) has passed.`,
    tone: "grey",
  };
}

function fmt(n) {
  return n === null || n === undefined ? "—" : n;
}

window.TABS.overview = function renderOverview(container, state, mode) {
  const { plan, progress } = state;
  const isSample = mode === "sample";
  const totals = isSample ? SAMPLE_TOTALS : progress.totals;
  const pos = schedulePosition(plan.schedule);
  const demoRelease = (plan.releases || []).find((r) =>
    plan.schedule && plan.schedule.demo_release_key ? r.key === plan.schedule.demo_release_key : r.is_demo_target
  );

  const criteriaLabel = totals.criteria_total === null || totals.criteria_total === undefined
    ? "not yet defined"
    : `${fmt(totals.criteria_passed)} of ${fmt(totals.criteria_total)}`;

  container.innerHTML = `
    ${isSample ? `<div class="sample-banner">SAMPLE DATA — this page is showing fabricated numbers so you can see the shape of the dashboard. Switch to Real to see what the project has actually produced.</div>` : ""}

    <h1>${esc(plan.project?.name || plan.project_name)}${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <p class="lede">${esc(plan.project?.descriptor || plan.descriptor)}</p>

    <div class="card-grid">
      <a class="card" href="#pm">
        <span class="card-label">Schedule</span>
        <span class="card-value" style="font-size:1.15rem;">
          <span class="pill ${pos.tone}">${pos.status}</span>
        </span>
        <span class="card-sub">${pos.detail}</span>
        <span class="card-drill">Project Management &rarr;</span>
      </a>

      <a class="card" href="#pm">
        <span class="card-label">Stories verified</span>
        <span class="card-value">${fmt(totals.stories_verified)} <span style="font-weight:400;font-size:1rem;color:var(--text-muted);">of ${fmt(totals.stories_total)}</span></span>
        <span class="card-sub">${totals.stories_verified === 0 ? "No stories verified yet." : "Verified against acceptance criteria."}</span>
        <span class="card-drill">Project Management &rarr;</span>
      </a>

      <a class="card" href="#kb">
        <span class="card-label">Criteria passed</span>
        <span class="card-value" style="font-size:${totals.criteria_total ? "1.6rem" : "1.1rem"};">${criteriaLabel}</span>
        <span class="card-sub">${totals.criteria_total === null || totals.criteria_total === undefined ? "Per-story acceptance criteria haven't been captured for this project yet." : "Across all story acceptance criteria."}</span>
        <span class="card-drill">Knowledge Base &rarr;</span>
      </a>

      <a class="card" href="#pm">
        <span class="card-label">Points awarded</span>
        <span class="card-value">${fmt(totals.points_awarded)}</span>
        <span class="card-sub">${totals.points_awarded === 0 ? "Nothing shipped yet." : "Awarded on verified stories."}</span>
        <span class="card-drill">Project Management &rarr;</span>
      </a>

      <a class="card" href="#systems">
        <span class="card-label">Systems</span>
        <span class="card-value" style="font-size:1.1rem;"><span class="dot"></span>Not checked from here</span>
        <span class="card-sub">${(plan.derived.systems || []).join(", ")}</span>
        <span class="card-drill">Systems &rarr;</span>
      </a>

      <a class="card" href="#pm">
        <span class="card-label">Demo target release</span>
        <span class="card-value" style="font-size:1.2rem;">${demoRelease ? esc(demoRelease.name) : "Not yet marked"}</span>
        <span class="card-sub">${plan.schedule && plan.schedule.demo_day ? `Demo day ${esc(plan.schedule.demo_day)}.` : "No demo day set yet."} ${demoRelease ? "Releases after this one are roadmap, not this term's work." : "No release is currently flagged as the demo target."}</span>
        <span class="card-drill">Project Management &rarr;</span>
      </a>
    </div>
  `;
};
