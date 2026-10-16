const form = document.querySelector("#run-form");
const fields = document.querySelector("#form-fields");
const sections = document.querySelector("#section-list");
const status = document.querySelector("#save-status");
const save = document.querySelector("#save-run");
const params = new URLSearchParams(location.search);
const id = location.pathname.split("/")[2];
let sectionId = 0;
let saving = false;
let baseline = null;
let reloadRequired = false;
let readVersion = 0;
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
  const informational = title === "Changes saved" || title.startsWith("Loading") || title.startsWith("Reloading") || title.startsWith("Saving changes");
  status.setAttribute("role", informational ? "status" : "alert");
  status.setAttribute("aria-live", informational ? "polite" : "assertive");
  const heading = document.createElement("strong");
  heading.textContent = title;
  const explanation = document.createElement("p");
  explanation.textContent = message;
  status.replaceChildren(heading, explanation);
}

function clearFieldErrors() {
  for (const input of form.querySelectorAll('[aria-invalid="true"]')) input.removeAttribute("aria-invalid");
  for (const error of form.querySelectorAll(".field-error")) {
    error.hidden = true;
    error.textContent = "";
  }
}

function fieldError(input, message) {
  if (!input) return;
  input.setAttribute("aria-invalid", "true");
  const error = document.getElementById(input.getAttribute("aria-describedby"));
  error.textContent += `${error.textContent ? " " : ""}${message}`;
  error.hidden = false;
}

function updateSections() {
  const rows = [...sections.children];
  rows.forEach((row, index) => {
    row.querySelector("legend").textContent = `Section ${index + 1}`;
    for (const [action, label] of [["remove", "Remove"], ["up", "Move"], ["down", "Move"]]) {
      const button = row.querySelector(`[data-action="${action}"]`);
      button.setAttribute("aria-label", `${label} section ${index + 1}${action === "remove" ? "" : ` ${action}`}`);
      button.disabled = action === "remove" ? rows.length === 1 : action === "up" ? index === 0 : index === rows.length - 1;
    }
  });
}

function addSection(focus = true) {
  const row = document.querySelector("#section-template").content.firstElementChild.cloneNode(true);
  for (const input of row.querySelectorAll("input")) {
    const field = input.dataset.field;
    input.id = `section-${sectionId}-${field}`;
    row.querySelector(`[data-label="${field}"]`).htmlFor = input.id;
    const error = row.querySelector(`[data-error="${field}"]`);
    error.id = `${input.id}-error`;
    input.setAttribute("aria-describedby", error.id);
  }
  sectionId++;
  sections.append(row);
  updateSections();
  if (focus) row.querySelector("input").focus();
}

function editSections(event) {
  const button = event.target.closest("button[data-action]");
  if (!button || saving) return;
  const row = button.closest(".section-editor");
  const action = button.dataset.action;
  if (action === "remove" && sections.children.length > 1) {
    const next = row.nextElementSibling ?? row.previousElementSibling;
    row.remove();
    next.querySelector("input").focus();
  } else if (action === "up" && row.previousElementSibling) {
    sections.insertBefore(row, row.previousElementSibling);
  } else if (action === "down" && row.nextElementSibling) {
    sections.insertBefore(row.nextElementSibling, row);
  }
  clearFieldErrors();
  updateSections();
  if (row.isConnected) {
    // A move can disable its own button at the boundary. Keep keyboard focus in the row.
    (button.disabled ? row.querySelector("input") : button).focus();
  }
}

function distanceMetres(input) {
  const match = /^(\d+)(?:\.(\d+))?$/.exec(input.value);
  if (match && !/[1-9]/.test((match[2] ?? "").slice(3))) {
    const digits = `${match[1]}${(match[2] ?? "").slice(0, 3).padEnd(3, "0")}`.replace(/^0+/, "");
    if (digits) return digits;
  }
  fieldError(input, "Enter positive kilometres in whole metres, for example 1 or 0.001. No rounding is allowed.");
}

function paceSeconds(input) {
  const match = /^(\d+):([0-5]\d)$/.exec(input.value);
  if (match) {
    const seconds = BigInt(match[1]) * 60n + BigInt(match[2]);
    if (seconds > 0n) return String(seconds);
  }
  fieldError(input, "Enter a positive pace with seconds from 00 to 59, for example 5:45.");
}

function creationPayload() {
  clearFieldErrors();
  for (const input of fields.querySelectorAll("[name]")) {
    if (!input.validity.valid) fieldError(input, input.validationMessage);
  }
  const targets = [...sections.children].map(row => ({
    distance_m: distanceMetres(row.querySelector('[data-field="distance_m"]')),
    target_pace_seconds_per_km: paceSeconds(row.querySelector('[data-field="target_pace_seconds_per_km"]')),
  }));
  if (form.querySelector('[aria-invalid="true"]')) return null;
  return {
    planned_date: form.elements.planned_date.value,
    planned_start_time: form.elements.planned_start_time.value || null,
    run_type: form.elements.run_type.value,
    sections: targets,
    user_note: form.elements.user_note.value || null,
    trainer_note: form.elements.trainer_note.value || null,
  };
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

function sectionDistance(metres) {
  const digits = metres.padStart(4, "0");
  const fraction = digits.slice(-3).replace(/0+$/, "");
  return `${digits.slice(0, -3)}${fraction ? `.${fraction}` : ""}`;
}

function prefill(run) {
  baseline = run;
  for (const field of ["planned_date", "planned_start_time", "run_type", "user_note", "trainer_note"])
    form.elements[field].value = run[field] ?? "";
  sections.replaceChildren();
  for (const section of run.sections) {
    addSection(false);
    const row = sections.lastElementChild;
    row.querySelector('[data-field="distance_m"]').value = sectionDistance(section.distance_m);
    const pace = BigInt(section.target_pace_seconds_per_km);
    row.querySelector('[data-field="target_pace_seconds_per_km"]').value = `${pace / 60n}:${String(pace % 60n).padStart(2, "0")}`;
  }
  clearFieldErrors();
  reloadRequired = false;
  fields.disabled = false;
  save.disabled = false;
  status.hidden = true;
  document.querySelector("#recovery").hidden = true;
  document.querySelector("#cancel").href = editorWeek();
}

function draftChanges() {
  const payload = creationPayload();
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
  save.disabled = true;
  document.querySelector("#recovery").hidden = false;
  document.querySelector("#retry-load").hidden = true;
  showStatus(title, message);
}

function showSaveError(response, data) {
  if (Array.isArray(data?.detail)) {
    for (const problem of data.detail) {
      const path = problem.loc ?? [];
      if (path[0] !== "body" || typeof problem.msg !== "string") continue;
      const input = path[1] === "sections"
        ? sections.children[path[2]]?.querySelector(`[data-field="${path[3]}"]`)
        : form.elements.namedItem(path[1]);
      fieldError(input, problem.msg);
    }
    showStatus("Could not save this run", data.detail.map(problem => problem.msg).join(" "));
    form.querySelector('[aria-invalid="true"]')?.focus();
  } else showStatus("Could not save this run", "Review the entered values and try again.");
}

async function loadRun(reloading = false) {
  const version = ++readVersion;
  fields.disabled = true;
  save.disabled = true;
  document.querySelector("#recovery").hidden = true;
  showStatus(reloading ? "Reloading saved run..." : "Loading run...", "Please wait.");
  let response;
  let data;
  try {
    response = await fetch(`/v1/runs/${encodeURIComponent(id)}`, { cache: "no-store" });
    data = await response.json();
  } catch {
    if (version !== readVersion) return;
    showStatus("Could not load run", "A network error prevented loading. Retry when ready.");
    document.querySelector("#recovery").hidden = false;
    document.querySelector("#retry-load").hidden = false;
    if (baseline) fields.disabled = false;
    return;
  }
  if (version !== readVersion) return;
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
}

async function saveRun(event) {
  event.preventDefault();
  if (saving || reloadRequired || !baseline) return;
  const changes = draftChanges();
  if (!changes) {
    showStatus("Could not save this run", "Check the marked fields. Your entries are still here.");
    form.querySelector('[aria-invalid="true"]')?.focus();
    return;
  }
  saving = true;
  fields.disabled = true;
  save.disabled = true;
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
    if (response.status === 404) {
      blockWrites("Run unavailable", "The run is no longer available. Your draft is still here.");
      document.querySelector("#recovery").hidden = true;
    }
    else if (response.status === 412) blockWrites("Saved run changed", "Your draft is intact. Reload the saved run before another edit.");
    else if (response.status === 428 || (response.status === 422 && data?.detail?.some?.(problem => problem.loc?.[0] === "header")))
      blockWrites("Reload required", "The revision could not be confirmed. Reload before editing.");
    else if (response.status >= 500 || response.ok) blockWrites("Saving could not be confirmed", "Your draft is intact. Reload the saved run to review the outcome.");
    else if (response.status === 413) showStatus("Could not save this run", "Reduce the notes or sections and try again.");
    else showSaveError(response, data, changes.planned_date ?? baseline.planned_date);
  } catch {
    blockWrites("Saving could not be confirmed", "The response was lost or unreadable. Reload the saved run before another edit.");
  } finally {
    saving = false;
    form.setAttribute("aria-busy", "false");
    fields.disabled = !baseline;
    save.disabled = reloadRequired || !baseline;
    updateSections();
  }
}

form.onsubmit = saveRun;
sections.onclick = editSections;
document.querySelector("#add-section").onclick = () => addSection();
document.querySelector("#cancel").onclick = event => {
  event.preventDefault();
  if (!dirty() || confirm("Discard your unsaved changes?")) leave(editorWeek());
};
document.querySelector("#reload-run").onclick = () => {
  if (!dirty() || confirm("Discard your unsaved draft and reload the saved run?")) loadRun(true);
};
document.querySelector("#retry-load").onclick = () => loadRun(Boolean(baseline));
loadRun();
