/* Loads .colaberry/*.json at runtime. Nothing from these files is ever
   copied into component code — every render reads the object returned
   here, so a sync that changes the files changes the page on next load. */

const DATA_BASE = ".colaberry";

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

async function loadColaberryData() {
  const [plan, progress, manifest] = await Promise.all([
    fetchJson(`${DATA_BASE}/plan.json`),
    fetchJson(`${DATA_BASE}/progress.json`),
    fetchJson(`${DATA_BASE}/manifest.json`),
  ]);

  let profile = null;
  try {
    profile = await fetchJson(`${DATA_BASE}/profile.json`);
  } catch (e) {
    profile = null;
  }

  const progressById = new Map();
  for (const s of progress.stories || []) {
    progressById.set(s.id, s);
  }

  const joinedStories = (plan.stories || []).map((story) => {
    const prog = progressById.get(story.id);
    return {
      ...story,
      verification: prog && prog.verification ? prog.verification : { state: "not_started", criteria_passed: 0, criteria_total: 0, commit_sha: null, commit_url: null, points_awarded: 0 },
    };
  });

  return { plan, progress, manifest, profile, joinedStories, progressById };
}

function manifestAge(generatedAtIso) {
  const generated = new Date(generatedAtIso);
  const now = new Date();
  const ms = now - generated;
  const days = ms / (1000 * 60 * 60 * 24);
  return { generated, days, isStale: days > 7 };
}

function formatAbsoluteDate(d) {
  return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}

function formatRelative(days) {
  if (days < 1) {
    const hours = Math.max(0, Math.round(days * 24));
    if (hours < 1) return "less than an hour ago";
    return hours === 1 ? "1 hour ago" : `${hours} hours ago`;
  }
  const wholeDays = Math.round(days);
  return wholeDays === 1 ? "1 day ago" : `${wholeDays} days ago`;
}

function dataAsOfLabel(generatedAtIso) {
  const { generated, days } = manifestAge(generatedAtIso);
  return `Data as of ${formatAbsoluteDate(generated)} (${formatRelative(days)})`;
}
