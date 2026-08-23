/* Outcomes tab — the numbers this project has to move.
   Source: plan.derived.measures ([{id, statement}]). The real plan
   carries none yet, so the honest real-mode state is an empty list that
   still drills down to a page explaining what has to happen first. */

window.TABS = window.TABS || {};

const SAMPLE_MEASURES = [
  { id: "m1", statement: "Reduce time-to-insight for a business question from hours to minutes." },
  { id: "m2", statement: "Increase the share of ad-hoc questions answered without a Data Analyst in the loop." },
];

function outcomesList(container, state, mode) {
  const isSample = mode === "sample";
  const measures = isSample ? SAMPLE_MEASURES : (state.plan.derived.measures || []);

  container.innerHTML = `
    ${sampleBanner(isSample, "these outcome measures are illustrative, not real targets.")}
    <h1>Outcomes${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <p class="lede">The numbers this project has to move. Your plan carries no numeric target yet.</p>
    ${
      measures.length
        ? `<div class="card-grid">${measures
            .map(
              (m) => `
          <a class="card" href="#outcomes/${m.id}">
            <span class="card-label">Measure</span>
            <span class="card-sub" style="font-size:0.95rem;color:var(--text);">${esc(m.statement)}</span>
            <span class="card-drill">Details &rarr;</span>
          </a>`
            )
            .join("")}</div>`
        : `<div class="card-grid"><a class="card" href="#outcomes/none">
             <span class="card-label">Measures</span>
             <span class="card-value" style="font-size:1.1rem;">None defined yet</span>
             <span class="card-sub">No numeric target has been set for this project.</span>
             <span class="card-drill">What has to happen first &rarr;</span>
           </a></div>`
    }
  `;
}

function outcomesDetail(container, state, mode, id) {
  const isSample = mode === "sample";
  const measures = isSample ? SAMPLE_MEASURES : (state.plan.derived.measures || []);
  const measure = measures.find((m) => m.id === id);

  if (!measure) {
    container.innerHTML = `
      ${breadcrumb("Outcomes", "outcomes", "No measures yet")}
      <h1>No outcome measures yet</h1>
      ${emptyState(
        "Nothing to show",
        "This project has not defined a numeric outcome measure yet. Before one can be tracked here, someone needs to state what the AI Data Assistant is meant to move — a metric, a baseline, and a target — and add it to the plan. Once it's added, it will appear on this tab automatically."
      )}
    `;
    return;
  }

  container.innerHTML = `
    ${sampleBanner(isSample)}
    ${breadcrumb("Outcomes", "outcomes", "Measure detail")}
    <h1>Measure${isSample ? '<span class="sample-tag">Sample</span>' : ""}</h1>
    <div class="section">
      <p style="font-size:1.05rem;">${esc(measure.statement)}</p>
      ${isSample
        ? `<p class="card-sub">Sample baseline/target/trend would render here once real measurement data exists. This is a fabricated example.</p>`
        : ""}
    </div>
  `;
}

window.TABS.outcomes = function renderOutcomes(container, state, mode, subpath) {
  if (subpath && subpath[0]) {
    outcomesDetail(container, state, mode, subpath[0]);
  } else {
    outcomesList(container, state, mode);
  }
};
