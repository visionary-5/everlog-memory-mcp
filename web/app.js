const state = {
  dashboard: null,
  entries: [],
  artifacts: [],
  artifactTimeline: [],
  latestArtifact: null,
  objectDetails: new Map(),
  nextObjectId: 1,
};

const viewCopy = {
  map: ["Growth Map", "A diary-grounded overview of the current self-model."],
  threads: ["Threads", "Long-running lines of thought and behavior."],
  questions: ["Open Loops", "Decisions and questions that need future evidence."],
  seeds: ["Seeds", "Ideas that may become writing, products, or research."],
  library: ["Library", "Saved agent records with source and period metadata."],
  sources: ["Source Vault", "Diary entries are available only for inspection."],
};

document.addEventListener("DOMContentLoaded", async () => {
  bindNavigation();
  bindDialogs();
  bindObjectDrilldown();
  await loadAll();
});

async function loadAll() {
  const [dashboard, entries, artifacts] = await Promise.all([
    getJson("/api/dashboard"),
    getJson("/api/entries"),
    getJson("/api/artifacts"),
  ]);
  state.dashboard = dashboard;
  state.entries = entries.entries || [];
  state.artifacts = artifacts.artifacts || [];
  state.artifactTimeline = artifacts.timeline || [];
  state.latestArtifact = state.artifacts.length
    ? await getJson(`/api/artifact?id=${encodeURIComponent(state.artifacts[0].id)}`)
    : null;
  state.objectDetails = new Map();
  state.nextObjectId = 1;

  renderShellStatus();
  renderMap();
  renderThreads();
  renderQuestions();
  renderSeeds();
  renderLibrary();
  renderSources();
}

async function getJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(payload.error || response.statusText);
  }
  return response.json();
}

function bindNavigation() {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });
}

function bindDialogs() {
  document.getElementById("closeEntryDialog").addEventListener("click", () => {
    document.getElementById("entryDialog").close();
  });
  document.getElementById("closeArtifactDialog").addEventListener("click", () => {
    document.getElementById("artifactDialog").close();
  });
  document.getElementById("closeObjectDialog").addEventListener("click", () => {
    document.getElementById("objectDialog").close();
  });
}

function bindObjectDrilldown() {
  document.addEventListener("click", (event) => {
    const card = event.target.closest("[data-object-ref]");
    if (!card) return;
    openObject(card.dataset.objectRef);
  });
}

function showView(view) {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active-view", section.id === view);
  });
  const [title, subtitle] = viewCopy[view];
  document.getElementById("viewTitle").textContent = title;
  document.getElementById("viewSubtitle").textContent = subtitle;
}

function renderShellStatus() {
  const { privacy, stats } = state.dashboard;
  const scanOk = state.dashboard.scan.errors.length === 0;
  document.getElementById("syncStatus").textContent = scanOk ? "Synced" : "Review";
  document.getElementById("entryStatus").textContent = `${stats.entry_count} entries`;
  document.getElementById("storageMode").textContent = privacy.store_plaintext_index
    ? "Plaintext index"
    : "Metadata index";
  document.getElementById("storageDetail").textContent = privacy.body_persistence;
}

function renderMap() {
  const artifact = state.latestArtifact;
  const model = selfModel(artifact);
  const stats = state.dashboard.stats;

  document.getElementById("mapHero").innerHTML = artifact
    ? `
      <section class="hero-block">
        <div>
          <div class="eyebrow">${escapeHtml(artifact.date_range || artifact.created_at)}</div>
          <h2>${escapeHtml(artifact.title)}</h2>
          <p>${escapeHtml(artifact.summary || "No summary yet.")}</p>
        </div>
        <div class="hero-metrics">
          ${metricCell("Entries", stats.entry_count)}
          ${metricCell("Objects", modelObjectCount(model))}
          ${metricCell("Evidence", artifact.evidence_count || allEvidence(artifact).length)}
          ${metricCell("Records", state.artifacts.length)}
        </div>
      </section>
    `
    : emptyBlock("No growth map yet.");

  document.getElementById("mapMovement").innerHTML = model.threads
    .filter(isDiaryGrounded)
    .slice(0, 4)
    .map((item, index) => movementRow(item, index))
    .join("") || emptyBlock("No diary-grounded movement yet.");
  document.getElementById("mapMoments").innerHTML = model.moments
    .filter(isDiaryGrounded)
    .slice(0, 6)
    .map((item) => momentCard(item))
    .join("") || emptyBlock("No high-signal moments yet. Ask the agent to write model.moments instead of only macro themes.");
  document.getElementById("mapTensions").innerHTML = model.tensions
    .filter(isDiaryGrounded)
    .slice(0, 3)
    .map((item) => modelCard(item, "tension"))
    .join("") || emptyBlock("No tracked tensions.");
  document.getElementById("mapBeliefs").innerHTML = model.beliefs
    .filter(isDiaryGrounded)
    .slice(0, 3)
    .map((item) => modelCard(item, "belief"))
    .join("") || emptyBlock("No belief changes.");
}

function renderThreads() {
  const model = selfModel(state.latestArtifact);
  const threads = model.threads.filter(isDiaryGrounded);
  document.getElementById("threadBoard").innerHTML = threads.length
    ? threads.map((item) => threadDetailCard(item)).join("")
    : emptyBlock("No threads saved.");
}

function renderQuestions() {
  const model = selfModel(state.latestArtifact);
  const decisions = model.decisions.map((item) => questionRow(item, { expanded: true }));
  const questions = model.questions.map((item) => questionRow(item, { expanded: true }));
  document.getElementById("questionBoard").innerHTML =
    decisions.length || questions.length
      ? `
        <section class="loop-section">
          <div class="section-title"><h2>Decisions</h2></div>
          <div class="question-list">${decisions.join("") || emptyBlock("No active decisions.")}</div>
        </section>
        <section class="loop-section">
          <div class="section-title"><h2>Questions</h2></div>
          <div class="question-list">${questions.join("") || emptyBlock("No open questions.")}</div>
        </section>
      `
      : emptyBlock("No open loops saved.");
}

function renderSeeds() {
  const model = selfModel(state.latestArtifact);
  const seeds = model.seeds.filter(isDiaryGrounded);
  document.getElementById("seedBoard").innerHTML = seeds.length
    ? seeds.map((item) => modelCard(item, "seed", { expanded: true })).join("")
    : emptyBlock("No diary-grounded seeds yet. Project planning from the current chat belongs in repo docs or a product artifact, not in the diary self-model.");
}

function renderLibrary() {
  const container = document.getElementById("artifactList");
  container.innerHTML = state.artifacts.length
    ? state.artifacts.map(artifactCard).join("")
    : emptyBlock("No saved records.");
  document.querySelectorAll("[data-artifact-id]").forEach((card) => {
    card.addEventListener("click", () => openArtifact(card.dataset.artifactId));
  });
}

function renderSources() {
  const stats = state.dashboard.stats;
  document.getElementById("sourceSummary").innerHTML = sourceVaultSummary(stats);
  const container = document.getElementById("sourceList");
  container.innerHTML = sourceGroups(state.entries);
  document.querySelectorAll("[data-entry-id]").forEach((button) => {
    button.addEventListener("click", () => openEntry(button.dataset.entryId));
  });
}

function artifactCard(artifact) {
  return `
    <article class="record-card" data-artifact-id="${escapeHtml(artifact.id)}">
      <div class="record-topline">
        <div>
          <h3>${escapeHtml(artifact.title)}</h3>
          <div class="meta-line">${escapeHtml(artifact.source)} / ${escapeHtml(artifact.artifact_type)}</div>
        </div>
        <div class="date-chip">${escapeHtml(artifact.date_range || artifact.created_at)}</div>
      </div>
      <p>${escapeHtml(artifact.summary || "No summary.")}</p>
      <div class="stat-row">
        <span>${artifact.object_count || artifact.dimension_count || artifact.claim_count || 0} objects</span>
        <span>${artifact.claim_count || 0} claims</span>
        <span>${artifact.evidence_count || 0} evidence</span>
      </div>
      ${tagRow(artifact.tags)}
    </article>
  `;
}

function sourceVaultSummary(stats) {
  const averageChars = stats.entry_count ? Math.round(Number(stats.total_chars || 0) / stats.entry_count) : 0;
  return `
    <section class="vault-panel">
      <div>
        <div class="eyebrow">Source Vault</div>
        <h2>Raw evidence stays behind the model</h2>
        <p>Entries are kept as inspectable sources for citations and correction. The growth views should not become a second diary reader.</p>
      </div>
      <div class="vault-metrics">
        ${metricCell("Entries", stats.entry_count)}
        ${metricCell("Period", compactDateRange(stats.date_start, stats.date_end))}
        ${metricCell("Avg length", averageChars ? `${compactNumber(averageChars)} chars` : "n/a")}
        ${metricCell("Index", state.dashboard.privacy.store_plaintext_index ? "Plain" : "Meta")}
      </div>
    </section>
  `;
}

function sourceGroups(entries) {
  if (!entries.length) return emptyBlock("No source entries indexed.");
  const groups = new Map();
  entries.forEach((entry) => {
    const key = monthKey(entry.date);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(entry);
  });
  return Array.from(groups.entries())
    .map(
      ([month, items]) => `
        <section class="source-month">
          <div class="source-month-head">
            <h2>${escapeHtml(month)}</h2>
            <span>${items.length} entries</span>
          </div>
          <div class="source-timeline">
            ${items.map((entry, index) => sourceCard(entry, index)).join("")}
          </div>
        </section>
      `
    )
    .join("");
}

function sourceCard(entry, index) {
  return `
    <article class="source-card source-entry">
      <div class="source-date-block">
        <strong>${escapeHtml(dayNumber(entry.date))}</strong>
        <span>${escapeHtml(weekdayLabel(entry.date))}</span>
      </div>
      <div class="source-entry-main">
        <div class="object-head">
          <span>${escapeHtml(formatDate(entry.date))}</span>
          <span>${escapeHtml(compactNumber(entry.chars))} chars</span>
        </div>
        <h3>${escapeHtml(sourceEntryTitle(entry, index))}</h3>
        <p>Private source entry. Open only when an agent claim needs checking.</p>
      </div>
      <button class="quiet-button" data-entry-id="${escapeHtml(entry.id)}">Inspect</button>
    </article>
  `;
}

async function openEntry(id) {
  const entry = await getJson(`/api/entry?id=${encodeURIComponent(id)}`);
  document.getElementById("entryDetail").innerHTML = `
    <header class="detail-header">
      <div>
        <div class="eyebrow">${escapeHtml(formatDate(entry.date))}</div>
        <h2>Private source entry</h2>
      </div>
      <div class="date-chip">${escapeHtml(compactNumber(entry.chars))} chars</div>
    </header>
    <p class="detail-summary">This view is for evidence checks. The main product should interpret patterns without turning the vault into another diary interface.</p>
    <div class="source-body">${escapeHtml(entry.body)}</div>
  `;
  document.getElementById("entryDialog").showModal();
}

async function openArtifact(id) {
  const artifact = await getJson(`/api/artifact?id=${encodeURIComponent(id)}`);
  const model = selfModel(artifact);
  document.getElementById("artifactDetail").innerHTML = `
    <header class="detail-header">
      <div>
        <div class="eyebrow">${escapeHtml(artifact.source)} / ${escapeHtml(artifact.date_range || "")}</div>
        <h2>${escapeHtml(artifact.title)}</h2>
      </div>
      ${tagRow(artifact.tags)}
    </header>
    <p class="detail-summary">${escapeHtml(artifact.summary || "No summary.")}</p>
    <section class="detail-section">
      <h3>Self-Model Objects</h3>
      <div class="object-grid">
        ${[
          ...model.threads.slice(0, 3),
          ...model.moments.slice(0, 3),
          ...model.tensions.slice(0, 2),
          ...model.beliefs.slice(0, 2),
          ...model.seeds.slice(0, 2),
        ].map((item) => modelCard(item, item.kind || "object")).join("") || emptyBlock("No model objects.")}
      </div>
    </section>
    <section class="detail-section">
      <h3>Claims</h3>
      <div class="object-grid">
        ${(artifact.claims || []).map((claim) => claimCard(claim)).join("") || emptyBlock("No claims.")}
      </div>
    </section>
    <section class="detail-section">
      <h3>Evidence Notes</h3>
      ${evidenceList(allEvidence(artifact), 80)}
    </section>
    <details class="narrative-details">
      <summary>Full narrative</summary>
      <div class="artifact-body">${escapeHtml(artifact.body_markdown || "")}</div>
    </details>
  `;
  document.getElementById("artifactDialog").showModal();
}

function openObject(ref) {
  const item = state.objectDetails.get(ref);
  if (!item) return;
  document.getElementById("objectDetail").innerHTML = `
    <header class="detail-header">
      <div>
        <div class="eyebrow">${escapeHtml(kindLabel(item.kind || "object"))}</div>
        <h2>${escapeHtml(item.title || "Untitled")}</h2>
      </div>
      <div class="date-chip">${escapeHtml(item.status || "active")}</div>
    </header>
    ${item.summary ? `<p class="detail-summary">${escapeHtml(item.summary)}</p>` : ""}
    <section class="detail-section">
      <h3>Source Basis</h3>
      <div class="basis-panel">
        ${basisChip(item)}
        <span>${escapeHtml(basisDescription(item.basis))}</span>
      </div>
      ${item.basis_note ? `<p class="basis-note">${escapeHtml(item.basis_note)}</p>` : ""}
    </section>
    ${
      item.movement
        ? `<section class="detail-section"><h3>Movement</h3><div class="movement large">${escapeHtml(item.movement)}</div></section>`
        : ""
    }
    ${
      item.why_it_matters
        ? `<section class="detail-section"><h3>Why It Matters</h3><div class="movement large">${escapeHtml(item.why_it_matters)}</div></section>`
        : ""
    }
    ${
      item.feedback
        ? `<section class="detail-section"><h3>Agent Feedback</h3><div class="next-step large">${escapeHtml(item.feedback)}</div></section>`
        : ""
    }
    ${tagRow(item.signals || [])}
    ${
      item.next_step
        ? `<section class="detail-section"><h3>Next Step</h3><div class="next-step large">${escapeHtml(item.next_step)}</div></section>`
        : ""
    }
    <section class="detail-section">
      <h3>Evidence Notes</h3>
      ${evidenceList(item.evidence || [], 20)}
    </section>
  `;
  document.getElementById("objectDialog").showModal();
}

function selfModel(artifact) {
  const empty = {
    threads: [],
    moments: [],
    tensions: [],
    beliefs: [],
    seeds: [],
    decisions: [],
    questions: [],
  };
  if (!artifact) return empty;
  const model = artifact.model || {};
  const hasModel = Object.values(model).some((value) => Array.isArray(value) && value.length);
  if (hasModel) {
    const normalized = {
      threads: normalizeModelArray(model.threads, "thread"),
      moments: normalizeModelArray(model.moments, "moment"),
      tensions: normalizeModelArray(model.tensions, "tension"),
      beliefs: normalizeModelArray(model.beliefs, "belief"),
      seeds: normalizeModelArray(model.seeds, "seed"),
      decisions: normalizeModelArray(model.decisions, "decision"),
      questions: normalizeModelArray(model.questions, "question"),
    };
    if (!normalized.moments.length) normalized.moments = deriveMomentsFromModel(normalized);
    return normalized;
  }
  return deriveModel(artifact);
}

function deriveModel(artifact) {
  const claims = artifact.claims || [];
  const questions = artifact.questions || [];
  return {
    threads: deriveThreads(claims, artifact.tags),
    moments: deriveMoments(artifact),
    tensions: deriveTensions(claims, questions),
    beliefs: claims.slice(0, 5).map((claim) => claimToObject(claim, "belief")),
    seeds: [],
    decisions: claims
      .filter((claim) => looksLikeDecision(claim.claim, claim.interpretation))
      .slice(0, 3)
      .map((claim) => claimToObject(claim, "decision")),
    questions: questions.map((item) => ({
      kind: "question",
      title: item.question,
      summary: item.note || "",
      status: item.status || "open",
      basis: "prior_artifact",
      basis_note: "Derived from a saved artifact question, not from a newly written model object.",
      evidence: [],
    })),
  };
}

function deriveThreads(claims, tags = []) {
  const groups = new Map();
  claims.forEach((claim, index) => {
    const title = inferDimensionName(claim.claim, tags?.[index]);
    const existing = groups.get(title) || {
      kind: "thread",
      title,
      summary: "",
      movement: "",
      status: "derived",
      confidence: claim.confidence || "",
      basis: "prior_artifact",
      basis_note: "Derived from a saved artifact claim.",
      signals: [],
      evidence: [],
    };
    if (!existing.summary) existing.summary = claim.claim;
    if (claim.interpretation) {
      existing.movement = [existing.movement, claim.interpretation].filter(Boolean).join(" ");
    }
    existing.evidence.push(...(claim.evidence || []));
    groups.set(title, existing);
  });
  return Array.from(groups.values());
}

function deriveMoments(artifact) {
  return allEvidence(artifact)
    .filter((item) => itemDate(item) && itemNote(item))
    .slice(0, 6)
    .map((item) => ({
      kind: "moment",
      title: itemNote(item),
      summary: itemNote(item),
      status: "derived",
      confidence: "medium",
      basis: itemEntryId(item) ? "diary_evidence" : "prior_artifact",
      basis_note: "Derived from saved evidence notes because this artifact has no explicit model.moments.",
      evidence: [item],
    }));
}

function deriveMomentsFromModel(model) {
  return [...model.threads, ...model.tensions, ...model.beliefs]
    .flatMap((item) =>
      (item.evidence || []).slice(0, 1).map((evidence) => ({
        kind: "moment",
        title: item.title,
        summary: itemNote(evidence) || item.summary || "",
        status: "derived",
        confidence: "medium",
        basis: itemEntryId(evidence) ? "diary_evidence" : normalizeObjectBasis(item.basis, item),
        basis_note: "Derived from a model object's first evidence note because no explicit model.moments were saved.",
        signals: item.signals || [],
        evidence: [evidence],
      }))
    )
    .slice(0, 6);
}

function deriveTensions(claims, questions) {
  const explicit = claims
    .filter((claim) => looksLikeTension(claim.claim, claim.interpretation))
    .slice(0, 2)
    .map((claim) => claimToObject(claim, "tension"));
  const fromQuestions = questions
    .filter((item) => looksLikeTension(item.question, item.note || ""))
    .slice(0, 2)
    .map((item) => ({
      kind: "tension",
      title: item.question,
      summary: item.note || "",
      status: item.status || "open",
      basis: "prior_artifact",
      basis_note: "Derived from a saved artifact question.",
      evidence: [],
    }));
  return [...explicit, ...fromQuestions].slice(0, 3);
}

function normalizeModelArray(items, fallbackKind) {
  if (!Array.isArray(items)) return [];
  return items.map((item) => ({
    kind: item.kind || fallbackKind,
    title: item.title || item.name || item.question || "Untitled",
    summary: item.summary || item.state || item.current_read || "",
    movement: item.movement || item.trajectory || item.change || item.direction || "",
    why_it_matters: item.why_it_matters || item.why || "",
    feedback: item.feedback || item.response || "",
    status: item.status || item.phase || "",
    confidence: item.confidence || "",
    basis: normalizeObjectBasis(item.basis || item.source_basis, item),
    basis_note: item.basis_note || item.source_note || "",
    private_public: item.private_public || item.privacy || item.boundary || "",
    next_step: item.next_step || item.next_action || "",
    signals: Array.isArray(item.signals) ? item.signals : [],
    evidence: Array.isArray(item.evidence) ? item.evidence : [],
  }));
}

function normalizeObjectBasis(value, item = {}) {
  const basis = canonicalBasis(value);
  if (basis) {
    if (basis === "diary_evidence" && !hasEntryEvidence(item)) return "agent_hypothesis";
    return basis;
  }
  return hasEntryEvidence(item) ? "diary_evidence" : "agent_hypothesis";
}

function canonicalBasis(value) {
  const aliases = {
    diary: "diary_evidence",
    evidence: "diary_evidence",
    artifact: "prior_artifact",
    prior: "prior_artifact",
    conversation: "conversation_context",
    chat: "conversation_context",
    hypothesis: "agent_hypothesis",
    inference: "agent_hypothesis",
  };
  const raw = String(value || "").trim();
  const basis = aliases[raw] || raw;
  return ["diary_evidence", "prior_artifact", "conversation_context", "agent_hypothesis", "mixed"].includes(basis)
    ? basis
    : "";
}

function hasEntryEvidence(item) {
  return (item.evidence || []).some((evidence) => evidence.entry_id || evidence.entryId || evidence.id);
}

function isDiaryGrounded(item) {
  return normalizeObjectBasis(item.basis, item) === "diary_evidence";
}

function basisLabel(basis) {
  return (
    {
      diary_evidence: "Diary evidence",
      prior_artifact: "Prior artifact",
      conversation_context: "Conversation",
      agent_hypothesis: "Hypothesis",
      mixed: "Mixed basis",
    }[canonicalBasis(basis)] || "Hypothesis"
  );
}

function basisDescription(basis) {
  return (
    {
      diary_evidence: "This object is grounded in dated Everlog entries with entry ids.",
      prior_artifact: "This object was derived from an older saved artifact rather than a fresh diary pass.",
      conversation_context: "This object comes from the current project discussion, not directly from diary evidence.",
      agent_hypothesis: "This is an agent inference that still needs diary evidence before being treated as stable.",
      mixed: "This object combines diary evidence with another source, such as project context or prior artifacts.",
    }[canonicalBasis(basis)] || "This object has no clear source basis yet."
  );
}

function basisChip(item) {
  const basis = normalizeObjectBasis(item.basis, item);
  return `<span class="basis-chip ${escapeHtml(basis)}">${escapeHtml(basisLabel(basis))}</span>`;
}

function artifactDimensions(artifact) {
  if (artifact.dimensions && artifact.dimensions.length) return artifact.dimensions;
  return (artifact.claims || []).slice(0, 6).map((claim, index) => ({
    name: inferDimensionName(claim.claim, artifact.tags?.[index]),
    state: claim.claim,
    trajectory: claim.interpretation || "",
    confidence: claim.confidence || "",
    evidence: claim.evidence || [],
    signals: [],
  }));
}

function claimToObject(claim, kind) {
  return {
    kind,
    title: claim.claim,
    summary: claim.interpretation || "",
    movement: claim.interpretation || "",
    status: "active",
    confidence: claim.confidence || "",
    basis: "prior_artifact",
    basis_note: "Derived from a saved artifact claim.",
    evidence: claim.evidence || [],
  };
}

function modelCard(item, kind, options = {}) {
  const evidenceCount = (item.evidence || []).length;
  const ref = registerObject(item, kind);
  const basis = normalizeObjectBasis(item.basis, item);
  return `
    <article class="object-card ${escapeHtml(kind)} action-card" data-object-ref="${escapeHtml(ref)}">
      <div class="object-head">
        <span>${escapeHtml(kindLabel(kind))}</span>
        <span class="object-badges">
          ${basisChip({ ...item, basis })}
          ${item.status ? `<span>${escapeHtml(item.status)}</span>` : ""}
        </span>
      </div>
      <h3>${escapeHtml(item.title || "Untitled")}</h3>
      ${item.summary ? `<p>${escapeHtml(clip(item.summary, options.expanded ? 280 : 150))}</p>` : ""}
      ${item.movement ? `<div class="movement">${escapeHtml(clip(item.movement, options.expanded ? 260 : 130))}</div>` : ""}
      <div class="stat-row">
        ${item.confidence ? `<span>${escapeHtml(item.confidence)}</span>` : ""}
        <span>${evidenceCount} evidence</span>
        ${item.private_public ? `<span>${escapeHtml(item.private_public)}</span>` : ""}
      </div>
      ${tagRow(item.signals || [])}
      ${options.expanded && item.next_step ? `<div class="next-step">${escapeHtml(item.next_step)}</div>` : ""}
    </article>
  `;
}

function momentCard(item) {
  const ref = registerObject(item, "moment");
  const evidence = item.evidence || [];
  const primaryDate = evidence.length ? itemDate(evidence[0]) : "";
  return `
    <article class="moment-card action-card" data-object-ref="${escapeHtml(ref)}">
      <div class="moment-topline">
        <span>${escapeHtml(primaryDate ? formatDate(primaryDate) : "Undated")}</span>
        ${basisChip(item)}
      </div>
      <h3>${escapeHtml(item.title || "High-signal moment")}</h3>
      ${item.summary ? `<p>${escapeHtml(clip(item.summary, 190))}</p>` : ""}
      ${item.why_it_matters ? `<div class="moment-note">${escapeHtml(clip(item.why_it_matters, 180))}</div>` : ""}
      ${item.feedback ? `<div class="moment-feedback">${escapeHtml(clip(item.feedback, 180))}</div>` : ""}
    </article>
  `;
}

function movementRow(item, index) {
  const ref = registerObject(item, item.kind || "thread");
  const evidenceCount = (item.evidence || []).length;
  return `
    <article class="movement-row action-card" data-object-ref="${escapeHtml(ref)}">
      <div class="movement-index">${String(index + 1).padStart(2, "0")}</div>
      <div class="movement-main">
        <div class="object-head">
          <span>${escapeHtml(item.title || "Untitled thread")}</span>
          <span class="object-badges">
            ${basisChip(item)}
            <span>${evidenceCount} evidence</span>
          </span>
        </div>
        <p>${escapeHtml(clip(item.movement || item.summary || "", 260))}</p>
      </div>
    </article>
  `;
}

function threadDetailCard(item) {
  const ref = registerObject(item, item.kind || "thread");
  const evidence = item.evidence || [];
  return `
    <article class="thread-detail action-card" data-object-ref="${escapeHtml(ref)}">
      <div class="thread-detail-main">
        <div class="object-head">
          <span>Thread</span>
          <span class="object-badges">
            ${basisChip(item)}
            ${item.status ? `<span>${escapeHtml(item.status)}</span>` : ""}
          </span>
        </div>
        <h3>${escapeHtml(item.title || "Untitled thread")}</h3>
        ${item.summary ? `<p>${escapeHtml(item.summary)}</p>` : ""}
        ${item.movement ? `<div class="movement">${escapeHtml(item.movement)}</div>` : ""}
        ${tagRow(item.signals || [])}
        ${item.next_step ? `<div class="next-step">${escapeHtml(item.next_step)}</div>` : ""}
      </div>
      <aside class="thread-evidence" aria-label="Evidence trail">
        <div class="eyebrow">Evidence Trail</div>
        ${evidence.length ? evidence.slice(0, 6).map(evidencePill).join("") : `<div class="quiet-empty">No evidence notes.</div>`}
      </aside>
    </article>
  `;
}

function evidencePill(item) {
  return `
    <div class="evidence-pill">
      <strong>${escapeHtml(itemDate(item) || "undated")}</strong>
      <span>${escapeHtml(clip(itemNote(item) || "Evidence marker", 96))}</span>
    </div>
  `;
}

function questionRow(item, options = {}) {
  const ref = registerObject(item, item.kind || "question");
  const basis = normalizeObjectBasis(item.basis, item);
  return `
    <article class="question-card action-card" data-object-ref="${escapeHtml(ref)}">
      <div>
        <div class="object-head">
          <span>${escapeHtml(kindLabel(item.kind || "question"))}</span>
          <span class="object-badges">
            ${basisChip({ ...item, basis })}
            ${item.status ? `<span>${escapeHtml(item.status)}</span>` : ""}
          </span>
        </div>
        <h3>${escapeHtml(item.title || "Untitled question")}</h3>
        ${item.summary ? `<p>${escapeHtml(clip(item.summary, options.expanded ? 260 : 140))}</p>` : ""}
      </div>
      ${item.next_step ? `<div class="next-step">${escapeHtml(item.next_step)}</div>` : ""}
    </article>
  `;
}

function claimCard(claim) {
  const ref = registerObject(claimToObject(claim, "claim"), "claim");
  return `
    <article class="object-card claim action-card" data-object-ref="${escapeHtml(ref)}">
      <div class="object-head">
        <span>Claim</span>
        ${claim.confidence ? `<span>${escapeHtml(claim.confidence)}</span>` : ""}
      </div>
      <h3>${escapeHtml(claim.claim)}</h3>
      ${claim.interpretation ? `<p>${escapeHtml(claim.interpretation)}</p>` : ""}
      ${evidenceList(claim.evidence || [], 4)}
    </article>
  `;
}

function registerObject(item, kind) {
  const ref = `object-${state.nextObjectId}`;
  state.nextObjectId += 1;
  state.objectDetails.set(ref, {
    ...item,
    kind: item.kind || kind,
    basis: normalizeObjectBasis(item.basis, item),
  });
  return ref;
}

function evidenceList(items, limit) {
  const visible = (items || []).slice(0, limit);
  if (!visible.length) return `<div class="quiet-empty">No evidence notes.</div>`;
  return `
    <div class="evidence-list">
      ${visible
        .map((item) => {
          const note = itemNote(item) || "Evidence marker";
          return `
            <article class="evidence-row">
              <div class="evidence-date">${escapeHtml(itemDate(item) || "undated")}</div>
              <div>
                <p>${escapeHtml(clip(note, 210))}</p>
                ${itemEntryId(item) ? `<div class="meta-line">${escapeHtml(shortId(itemEntryId(item)))}</div>` : ""}
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function metricCell(label, value) {
  return `
    <div class="metric-cell">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `;
}

function emptyBlock(text) {
  return `<div class="quiet-empty">${escapeHtml(text)}</div>`;
}

function allEvidence(artifact) {
  if (!artifact) return [];
  return [
    ...(artifact.claims || []).flatMap((claim) => claim.evidence || []),
    ...(artifact.evidence || []),
  ];
}

function modelObjectCount(model) {
  return Object.values(model).reduce((count, items) => count + (Array.isArray(items) ? items.length : 0), 0);
}

function looksLikeTension(...parts) {
  const text = parts.join(" ").toLowerCase();
  return /vs|转向|张力|冲突|矛盾|between|from/.test(text);
}

function looksLikeDecision(...parts) {
  const text = parts.join(" ").toLowerCase();
  return /msc|phd|就业|offer|路径|申请|career|job|decision/.test(text);
}

function inferDimensionName(claim, fallback) {
  const text = String(claim || "").toLowerCase();
  if (text.includes("ai") || text.includes("token") || text.includes("技术")) return "AI and tech";
  if (text.includes("msc") || text.includes("phd") || text.includes("升学")) return "Path strategy";
  if (text.includes("职业") || text.includes("实习") || text.includes("能力")) return "Career environment";
  if (text.includes("记忆") || text.includes("memory")) return "Memory system";
  if (fallback) return fallback.replaceAll("-", " ");
  return "Self model";
}

function kindLabel(kind) {
  return {
    thread: "Thread",
    tension: "Tension",
    belief: "Belief",
    seed: "Seed",
    moment: "Moment",
    decision: "Decision",
    question: "Question",
    claim: "Claim",
  }[kind] || "Object";
}

function itemDate(item) {
  return String(item?.date || item?.entry_date || item?.entryDate || "").trim();
}

function itemEntryId(item) {
  return String(item?.entry_id || item?.entryId || item?.id || "").trim();
}

function itemNote(item) {
  return String(item?.note || item?.reason || item?.interpretation || item?.why || "").trim();
}

function tagRow(tags) {
  if (!tags || !tags.length) return "";
  return `<div class="tag-row">${tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>`;
}

function shortId(value) {
  const text = String(value || "");
  if (text.length <= 12) return text;
  return `${text.slice(0, 8)}...${text.slice(-4)}`;
}

function sourceEntryTitle(entry, index) {
  return `Reflection ${String(index + 1).padStart(2, "0")} / ${formatDate(entry.date)}`;
}

function compactDateRange(start, end) {
  if (!start && !end) return "n/a";
  if (start === end) return formatDate(start);
  return `${formatDate(start)} - ${formatDate(end)}`;
}

function monthKey(value) {
  const date = parseDateParts(value);
  if (!date) return "Undated";
  return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

function dayNumber(value) {
  const date = parseDateParts(value);
  return date ? String(date.getDate()).padStart(2, "0") : "--";
}

function weekdayLabel(value) {
  const date = parseDateParts(value);
  return date ? date.toLocaleDateString("en-US", { weekday: "short" }) : "";
}

function formatDate(value) {
  const date = parseDateParts(value);
  if (!date) return String(value || "");
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function parseDateParts(value) {
  const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return null;
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

function compactNumber(value) {
  if (Number(value) >= 1000) return `${Math.round(Number(value) / 100) / 10}k`;
  return `${value}`;
}

function clip(value, maxLength) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) return text;
  return `${text.slice(0, Math.max(0, maxLength - 1)).trim()}...`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
