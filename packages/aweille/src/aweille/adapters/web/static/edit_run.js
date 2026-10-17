import { createRunForm } from "./run_form.js";

const form = document.querySelector("#run-form");
const fields = document.querySelector("#form-fields");
const sections = document.querySelector("#section-list");
const status = document.querySelector("#save-status");
const save = document.querySelector("#save-run");
const deleteButton = document.querySelector("#delete-run");
const confirmation = document.querySelector("#delete-confirmation");
const confirmDelete = document.querySelector("#confirm-delete");
const keepRun = document.querySelector("#keep-run");
const params = new URLSearchParams(location.search);
const id = location.pathname.split("/")[2];
let writePending = false;
let loading = true;
let confirmingDelete = false;
let baseline = null;
let reloadRequired = false;
let readVersion = 0;
const { addSection, editSections, updateSections, showValidation, showBodyErrors, readPayload, populate } =
  createRunForm(form, fields, sections, () => writePending);
function calendarDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.getUTCFullYear() >= 1 &&
    date.getUTCFullYear() <= 9999 && date.toISOString().slice(0, 10) === value ? date : null;
}
function weekUrl(value) {
  const date = calendarDate(value);
  if (!date) return "/";
  date.setUTCDate(date.getUTCDate() - ((date.getUTCDay() + 6) % 7));
  const end = new Date(date);
  end.setUTCDate(end.getUTCDate() + 7);
  if (end.getUTCFullYear() > 9999) return "/";
  return `/?week=${date.toISOString().slice(0, 10)}`;
}

function showStatus(title, message) {
  status.hidden = false;
  const informational = title === "Changes saved" || title.startsWith("Loading") || title.startsWith("Reloading") || title.startsWith("Saving changes") || title.startsWith("Deleting run");
  status.setAttribute("role", informational ? "status" : "alert");
  status.setAttribute("aria-live", informational ? "polite" : "assertive");
  const heading = document.createElement("strong");
  heading.textContent = title;
  const explanation = document.createElement("p");
  explanation.textContent = message;
  status.replaceChildren(heading, explanation);
}

function editorWeek() {
  return params.has("week") && weekUrl(params.get("week")) !== "/"
    ? weekUrl(params.get("week")) : baseline ? weekUrl(baseline.planned_date) : "/";
}

function validRun(data) {
  return typeof data?.id === "string" && data.id.toLowerCase() === id.toLowerCase() &&
    typeof data.revision === "string" && /^[1-9][0-9]*$/.test(data.revision) &&
    calendarDate(data.planned_date) !== null &&
    ["easy", "hard", "interval", "long"].includes(data.run_type) &&
    Array.isArray(data.sections) && data.sections.length > 0 &&
    data.sections.every(section => section && typeof section.distance_m === "string" &&
      typeof section.target_pace_seconds_per_km === "string" &&
      /^[1-9][0-9]*$/.test(section.distance_m) &&
      /^[1-9][0-9]*$/.test(section.target_pace_seconds_per_km)) &&
    (data.planned_start_time === null || /^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(data.planned_start_time)) &&
    [data.user_note, data.trainer_note].every(note => note === null || typeof note === "string");
}

function updateControls() {
  fields.disabled = loading || writePending || confirmingDelete || !baseline;
  save.disabled = fields.disabled || reloadRequired;
  deleteButton.disabled = fields.disabled || reloadRequired;
  confirmDelete.disabled = writePending;
  keepRun.disabled = writePending;
  document.querySelector("#reload-run").disabled = loading || writePending;
  document.querySelector("#retry-load").disabled = loading || writePending;
}

function closeConfirmation() {
  confirmingDelete = false;
  confirmation.hidden = true;
}

function prefill(run) {
  baseline = run;
  populate(run);
  reloadRequired = false;
  closeConfirmation();
  status.hidden = true;
  document.querySelector("#recovery").hidden = true;
  document.querySelector("#cancel").href = editorWeek();
}

function draftChanges(payload = readPayload().payload) {
  if (!payload || !baseline) return null;
  return Object.fromEntries(Object.entries(payload).filter(([key, value]) =>
    JSON.stringify(value) !== JSON.stringify(baseline[key])));
}

function dirty() {
  if (!baseline) return false;
  const changes = draftChanges();
  return changes === null || Object.keys(changes).length > 0;
}

window.addEventListener("beforeunload", event => {
  if (dirty() && !window.leavingEditor) event.preventDefault();
});

function leave(url) {
  window.leavingEditor = true;
  location.assign(url);
}

function blockWrites(title, message) {
  reloadRequired = true;
  closeConfirmation();
  updateControls();
  document.querySelector("#recovery").hidden = false;
  document.querySelector("#retry-load").hidden = true;
  showStatus(title, message);
}

function showSaveError(response, data) {
  if (Array.isArray(data?.detail)) {
    showBodyErrors(data.detail);
    showStatus("Could not save this run", data.detail.map(problem => problem.msg).join(" "));
    form.querySelector('[aria-invalid="true"]')?.focus();
  } else showStatus("Could not save this run", "Review the entered values and try again.");
}

async function loadRun(reloading = false) {
  const version = ++readVersion;
  loading = true;
  if (baseline) reloadRequired = true;
  closeConfirmation();
  updateControls();
  document.querySelector("#recovery").hidden = true;
  showStatus(reloading ? "Reloading saved run..." : "Loading run...", "Please wait.");
  let response;
  let data;
  try {
    response = await fetch(`/v1/runs/${encodeURIComponent(id)}`, { cache: "no-store" });
    data = await response.json();
  } catch {
    if (version !== readVersion) return;
    loading = false;
    updateControls();
    showStatus("Could not load run", "A network error prevented loading. Retry when ready.");
    document.querySelector("#recovery").hidden = false;
    document.querySelector("#retry-load").hidden = false;
    if (baseline) fields.disabled = false;
    return;
  }
  if (version !== readVersion) return;
  loading = false;
  if (response.status === 404 || response.status === 422 && data?.detail?.some?.(problem => problem.loc?.[0] === "path")) {
    blockWrites("Run unavailable", "This planned run is unavailable. Your draft is still here.");
    document.querySelector("#recovery").hidden = true;
    fields.disabled = !baseline;
  } else if (response.ok && validRun(data)) {
    prefill(data);
    if (reloading) {
      showStatus("Saved run loaded", "Review the current values before another change.");
      document.querySelector("h1").focus();
    }
  } else {
    showStatus("Could not load run", "The server returned an unreadable response. Retry when ready.");
    document.querySelector("#recovery").hidden = false;
    document.querySelector("#retry-load").hidden = false;
    if (baseline) fields.disabled = false;
  }
  updateControls();
}

function showWriteFailure(response, data, deleting = false) {
  const action = deleting ? "Deletion" : "Saving";
  if (response.status === 404) {
    blockWrites("Run unavailable", "The run is no longer available. Your draft is still here.");
    document.querySelector("#recovery").hidden = true;
  }
  else if (response.status === 412) blockWrites("Saved run changed", "Your draft is intact. Reload the saved run before another edit or deletion.");
  else if (response.status === 428 || (response.status === 422 && data?.detail?.some?.(problem => problem.loc?.[0] === "header")))
    blockWrites("Reload required", "The revision could not be confirmed. Reload before another edit or deletion.");
  else if (response.status >= 500 || response.ok || !data)
    blockWrites(`${action} could not be confirmed`, "Your draft is intact. Reload the saved run to review the outcome.");
  else if (response.status === 413) showStatus("Could not save this run", "Reduce the notes or sections and try again.");
  else if (deleting) showStatus("Could not delete this run", "Deletion was rejected. Your draft is still here.");
  else showSaveError(response, data);
}

async function saveRun(event) {
  event.preventDefault();
  if (loading || writePending || confirmingDelete || reloadRequired || !baseline) return;
  const { payload, errors } = readPayload();
  showValidation(errors);
  const changes = payload && draftChanges(payload);
  if (!changes) {
    showStatus("Could not save this run", "Check the marked fields. Your entries are still here.");
    form.querySelector('[aria-invalid="true"]')?.focus();
    return;
  }
  writePending = true;
  updateControls();
  form.setAttribute("aria-busy", "true");
  showStatus("Saving changes...", "Please wait.");
  try {
    const response = await fetch(`/v1/runs/${encodeURIComponent(id)}`, {
      method: "PATCH", headers: { "Content-Type": "application/json", "If-Match": `"${baseline.revision}"` },
      body: JSON.stringify(changes), signal: AbortSignal.timeout(15000),
    });
    const data = await response.json().catch(() => null);
    if (response.status === 200 && validRun(data)) {
      const destination = weekUrl(data.planned_date);
      if (destination === "/") {
        prefill(data);
        showStatus("Changes saved", "This date cannot be shown in a complete week. The run remains available here.");
        return;
      }
      window.leavingEditor = true;
      location.assign(destination);
      return;
    }
    showWriteFailure(response, data);
  } catch {
    blockWrites("Saving could not be confirmed", "The response was lost or unreadable. Reload the saved run before another edit.");
  } finally {
    writePending = false;
    form.setAttribute("aria-busy", "false");
    updateControls();
    updateSections();
  }
}

async function deleteRun() {
  if (loading || writePending || reloadRequired || !baseline || !confirmingDelete) return;
  writePending = true;
  updateControls();
  form.setAttribute("aria-busy", "true");
  showStatus("Deleting run...", "Please wait. Leaving this page does not cancel deletion.");
  try {
    const response = await fetch(`/v1/runs/${encodeURIComponent(id)}`, {
      method: "DELETE", headers: { "If-Match": `"${baseline.revision}"` },
      signal: AbortSignal.timeout(15000),
    });
    if (response.status === 204) {
      leave(editorWeek());
      return;
    }
    const data = await response.json().catch(() => null);
    showWriteFailure(response, data, true);
  } catch {
    blockWrites("Deletion could not be confirmed", "Your draft is intact. Reload the saved run to review the outcome.");
  } finally {
    writePending = false;
    closeConfirmation();
    updateControls();
    form.setAttribute("aria-busy", "false");
    status.focus();
  }
}

deleteButton.onclick = () => {
  if (loading || writePending || reloadRequired || !baseline) return;
  confirmingDelete = true;
  document.querySelector("#delete-target").textContent = `${baseline.planned_date} · ${baseline.run_type[0].toUpperCase()}${baseline.run_type.slice(1)} run`;
  document.querySelector("#delete-draft-warning").hidden = !dirty();
  confirmation.hidden = false;
  updateControls();
  keepRun.focus();
};
keepRun.onclick = () => {
  closeConfirmation();
  updateControls();
  deleteButton.focus();
};
confirmDelete.onclick = deleteRun;
form.onsubmit = saveRun;
sections.onclick = editSections;
document.querySelector("#add-section").onclick = () => addSection();
document.querySelector("#cancel").onclick = event => {
  event.preventDefault();
  if (!dirty() || confirm("Discard your unsaved changes?")) leave(editorWeek());
};
function reloadRun() {
  if (!dirty() || confirm("Discard your unsaved draft and reload the saved run?")) loadRun(Boolean(baseline));
}
document.querySelector("#reload-run").onclick = reloadRun;
document.querySelector("#retry-load").onclick = reloadRun;
loadRun();
