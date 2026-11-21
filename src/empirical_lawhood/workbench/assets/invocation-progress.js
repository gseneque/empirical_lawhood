/* SPDX-License-Identifier: MPL-2.0 */
/* Advisory display only. Original receipts and owning reads supply results. */
const element = (tag, text, className) => {
  const value = document.createElement(tag);
  if (text !== undefined) value.textContent = text;
  if (className) value.className = className;
  return value;
};
const exact = value => value === null || value === undefined ? "Unknown" :
  typeof value === "object" ? String(value.integer ?? value.decimal ?? "Unknown") : String(value);
const numeric = value => value === null || value === undefined ? NaN : Number(exact(value));
const sequence = value => {
  const text = exact(value);
  return /^[1-9][0-9]*$/.test(text) ? BigInt(text) : null;
};
const seconds = value => Number.isFinite(value) ? `${Math.max(0, value).toFixed(1)} s` : "Unknown";
const terminal = value => ["RETURNED", "LAUNCH_FAILED"].includes(value?.state);

function metric(label, value, className = "") {
  const box = element("div", undefined, `progress-metric ${className}`);
  box.append(element("dt", label), element("dd", value));
  return box;
}

function counter(label, done, total, failed, unit, percent) {
  const box = element("section", undefined, "progress-counter");
  box.append(element("h3", label));
  const count = element("p", undefined, "progress-count");
  count.append(element("strong", exact(done)), document.createTextNode(` / ${exact(total)} ${unit || "units"}`));
  box.append(count);
  const fraction = numeric(percent);
  if (total !== null && total !== undefined && numeric(total) > 0 && Number.isFinite(fraction) && fraction >= 0 && fraction <= 100) {
    const bar = element("progress");
    bar.max = 100; bar.value = fraction; bar.setAttribute("aria-label", label);
    bar.setAttribute("aria-valuetext", `${exact(done)} of ${exact(total)} ${unit || "units"}; ${exact(percent)} percent`);
    box.append(bar);
  } else box.append(element("p", total === null || total === undefined ? "Required total is unknown; no completion estimate." : "No percentage for an empty census.", "progress-note"));
  box.append(element("p", `${exact(failed)} failed`, numeric(failed) > 0 ? "progress-failures" : "progress-note"));
  return box;
}

function invocationCard(row, read, isCurrent) {
  const card = element("section", undefined, "panel invocation-card");
  card.dataset.handle = row.handle;
  const head = element("div", undefined, "panel-head");
  const state = element("span", "Awaiting state", "badge unresolved");
  head.append(element("h2", row.operation), state);
  const identity = element("p", row.handle, "small-note invocation-handle");
  const freshness = element("p", "No progress report received.", "progress-freshness");
  // Ages change every second; announce status transitions without a countdown.
  freshness.setAttribute("aria-live", "off");
  const liveStatus = element("span", "Awaiting invocation state.", "progress-live-status");
  liveStatus.setAttribute("role", "status");
  const notice = element("p", "", "progress-notice"); notice.hidden = true;
  notice.setAttribute("role", "status");
  const receipt = element("p", "", "small-note invocation-receipt");
  const body = element("div", undefined, "progress-body");
  const refreshButton = element("button", "Refresh invocation", "secondary"); refreshButton.type = "button";
  const actions = element("div", undefined, "progress-actions"); actions.append(refreshButton);
  const details = element("details", undefined, "details");
  const raw = element("pre", "No invocation observation received.", "exact");
  details.append(element("summary", "Exact invocation and progress values"), raw);
  card.append(head, identity, freshness, liveStatus, notice, receipt, body, actions, details);
  let disposed = false, pending = null, controller = null, poll = null, tick = null;
  let observed = null, progress = null, observedAt = 0, ageAtRead = 0, lastSequence = null, binding = null;
  let elapsedLabel = null, phaseLabel = null, workLabel = null, availability = "NOT_OBSERVED", rendering = null;
  const current = () => !disposed && isCurrent();
  const age = () => ageAtRead + Math.max(0, performance.now() - observedAt) / 1000;
  const announce = text => { notice.textContent = text; notice.hidden = !text; };
  function updateAge() {
    if (!current()) return;
    const reportAge = age();
    const isTerminal = terminal(observed);
    const stale = !!progress && reportAge > 10 && !isTerminal;
    card.classList.toggle("progress-stale", stale);
    card.dataset.stale = String(stale);
    const statusText = `${observed?.state || "Awaiting state"}. ${stale ? "Progress report is stale." : progress ? "Progress report received." : "No bound progress report."}`;
    if (liveStatus.textContent !== statusText) liveStatus.textContent = statusText;
    freshness.textContent = progress ? `${stale ? "Stale report · " : isTerminal ? "Last report · " : "Report age · "}${seconds(reportAge)}${availability !== "OBSERVED" ? " · Showing last bound report" : ""}` :
      ({NOT_SELECTED: "Progress was not selected for this invocation.", NOT_OBSERVED: "No progress report received.", UPDATING_OR_UNBOUND: "Progress is being published or could not be bound. Retrying.", UNAVAILABLE: "Progress is unavailable. Retrying."}[availability] || "Progress is unavailable.");
    if (progress) {
      // Only age advances between reports. Counters and elapsed work stay observed.
      elapsedLabel.textContent = seconds(numeric(progress.snapshot.elapsed_seconds));
      phaseLabel.textContent = seconds(numeric(progress.snapshot.phase_elapsed_seconds));
      workLabel.textContent = seconds(numeric(progress.snapshot.activity_age_seconds) + (isTerminal ? 0 : reportAge));
      body.querySelector(".progress-heartbeat").textContent = progress.snapshot.heartbeat ? "Controller heartbeat observed. Native or remote work advancement remains unknown between work reports." : "Counters describe reported work. A local controller observation does not establish remote engine liveness.";
    }
  }
  function renderProgress() {
    if (!progress) return;
    const snapshot = progress.snapshot;
    const content = JSON.stringify(Object.fromEntries(Object.entries(snapshot).filter(([key]) => !["sequence", "updated_at_utc", "elapsed_seconds", "phase_elapsed_seconds", "activity_age_seconds", "heartbeat"].includes(key))));
    if (content === rendering) return;
    rendering = content;
    const previousSteps = body.querySelector(".progress-steps");
    const historyOpen = previousSteps?.open, historyFocus = previousSteps?.querySelector("summary") === document.activeElement;
    body.replaceChildren(); elapsedLabel = phaseLabel = workLabel = null;
    const phase = element("div", undefined, "progress-phase");
    phase.append(element("span", "Reported phase", "progress-label"), element("h3", snapshot.phase), element("p", snapshot.detail || "No additional detail.", "progress-note"));
    if (snapshot.task_id) phase.append(element("p", `Task · ${snapshot.task_id}`, "progress-task"));
    body.append(phase);
    const counters = element("div", undefined, "progress-counters");
    counters.append(counter("Current phase", snapshot.done, snapshot.total, snapshot.failed, snapshot.unit, snapshot.percent));
    if (snapshot.workflow_done !== null && snapshot.workflow_done !== undefined) counters.append(counter("Whole workflow · terminal work", snapshot.workflow_done, snapshot.workflow_total, snapshot.workflow_failed, snapshot.workflow_unit, snapshot.workflow_percent));
    body.append(counters);
    const timing = element("dl", undefined, "progress-timing");
    const elapsed = metric("Elapsed at report", ""), phaseTime = metric("Phase time at report", ""), work = metric("Since work report", "");
    elapsedLabel = elapsed.querySelector("dd"); phaseLabel = phaseTime.querySelector("dd"); workLabel = work.querySelector("dd");
    timing.append(elapsed, phaseTime, work); body.append(timing);
    body.append(element("p", snapshot.heartbeat ? "Controller heartbeat observed. Native or remote work advancement remains unknown between work reports." : "Counters describe reported work. A local controller observation does not establish remote engine liveness.", "progress-note progress-heartbeat"));
    const steps = element("details", undefined, "progress-steps");
    const history = (snapshot.completed_steps || []).slice(-64);
    steps.append(element("summary", `Recent steps · ${history.length} shown · ${exact(snapshot.completed_steps_omitted)} omitted from ${exact(snapshot.completed_steps_total)} total`));
    const list = element("ol");
    for (const step of history) {
      const item = element("li");
      item.append(element("span", step.phase, "progress-step-name"), element("span", `${exact(step.done)} / ${exact(step.total)} ${step.unit} · ${seconds(numeric(step.elapsed_seconds))}`, "progress-note"), element("span", step.status, `badge${["FAILED", "INTERRUPTED"].includes(step.status) ? " adverse" : ""}`));
      list.append(item);
    }
    steps.append(list); steps.open = !!historyOpen; body.append(steps);
    if (historyFocus) steps.querySelector("summary").focus();
  }
  function accept(value, transitSeconds) {
    if (value.handle !== row.handle || value.context_id !== row.context_id || !/^[0-9a-f]{64}$/.test(value.binding_sha256) || (binding && value.binding_sha256 !== binding)) throw new Error("Invocation identity changed. The last bound observation is retained.");
    binding = value.binding_sha256;
    // Progress order and invocation return are separate. A receipt can arrive
    // with an older advisory file, but an observed terminal state cannot regress.
    if (!terminal(observed) || terminal(value)) observed = value;
    state.textContent = observed.state;
    state.className = `badge${["UNCERTAIN", "ACCEPTED"].includes(observed.state) ? " unresolved" : observed.state === "LAUNCH_FAILED" ? " adverse" : ""}`;
    receipt.textContent = observed.state === "RETURNED" ? `Invocation returned · ${observed.return?.status || "See original return"}. Reopen the original result for scientific findings.` :
      observed.state === "LAUNCH_FAILED" ? "Worker launch failed. Inspect the retained failure before selecting another operation." :
      observed.state === "UNCERTAIN" ? "Process state is uncertain. Inspect the original invocation before selecting recovery." :
      observed.process_live === true ? "Invocation process observed alive. Scientific completion requires original receipts." : "Current process liveness is unknown.";
    const next = value.progress;
    availability = next?.availability || "UNAVAILABLE";
    if (availability === "OBSERVED") {
      const nextSequence = sequence(next.binding?.sequence);
      if (!nextSequence || next.binding?.handle !== row.handle || next.binding?.binding_sha256 !== binding || !next.snapshot || next.snapshot.operation !== value.operation) throw new Error("Progress identity is unbound. The last bound observation is retained.");
      if (lastSequence !== null && nextSequence < lastSequence) announce("An older progress report was ignored. The last bound report is retained.");
      else if (lastSequence === nextSequence) {
        if (next.binding.snapshot_sha256 !== progress.binding.snapshot_sha256) throw new Error("Progress bytes changed within one sequence. The last bound observation is retained.");
        ageAtRead = Math.max(age(), Math.max(0, numeric(next.age_seconds) || 0) + transitSeconds); observedAt = performance.now();
      } else {
        lastSequence = nextSequence; progress = next; observedAt = performance.now();
        ageAtRead = Math.max(0, numeric(next.age_seconds) || 0) + transitSeconds;
        renderProgress();
      }
    }
    raw.textContent = JSON.stringify({invocation: observed, displayed_progress: progress}, null, 2);
    updateAge();
  }
  function refresh() {
    if (!current()) return Promise.resolve();
    if (pending) return pending;
    clearTimeout(poll); controller = new AbortController();
    const signal = controller.signal;
    const startedAt = performance.now();
    const timeout = setTimeout(() => controller?.abort(), 8000);
    refreshButton.disabled = true;
    pending = (async () => {
      try {
        const value = await read(row, signal);
        if (!current() || signal.aborted) return;
        announce(""); accept(value, Math.max(0, performance.now() - startedAt) / 1000);
      } catch (error) {
        if (current()) announce(signal.aborted ? "State request timed out. Retrying; the last report continues to age." : `${error.message} Retrying; the last report continues to age.`);
      } finally {
        clearTimeout(timeout); pending = null; controller = null;
        if (current()) {
          refreshButton.disabled = false;
          if (terminal(observed)) { clearInterval(tick); tick = null; }
          else { if (!tick) tick = setInterval(updateAge, 1000); poll = setTimeout(refresh, 2000); }
        }
      }
    })();
    return pending;
  }
  refreshButton.addEventListener("click", refresh);
  tick = setInterval(updateAge, 1000);
  return {card, refresh, dispose() { disposed = true; clearTimeout(poll); clearInterval(tick); controller?.abort(); }};
}

export function mountInvocationProgress(root, rows, read, isCurrent) {
  const cards = rows.toReversed().map(row => invocationCard(row, read, isCurrent));
  for (const item of cards) root.append(item.card);
  for (const item of cards) item.refresh();
  return () => { for (const item of cards) item.dispose(); };
}
