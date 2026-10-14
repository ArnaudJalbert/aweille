const form = document.querySelector("#run-form");
const fields = document.querySelector("#form-fields");
const sections = document.querySelector("#section-list");
const status = document.querySelector("#save-status");
const save = document.querySelector("#save-run");
const params = new URLSearchParams(location.search);
const id = crypto.randomUUID();
let sectionId = 0;
let saving = false;
const uncertainWeeks = new Set();

function weekUrl(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value ?? "")) return "/";
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value) return "/";
  date.setUTCDate(date.getUTCDate() - ((date.getUTCDay() + 6) % 7));
  return `/?week=${date.toISOString().slice(0, 10)}`;
}

function showStatus(title, message, inspectWeeks = []) {
  status.hidden = false;
  status.setAttribute("role", saving ? "status" : "alert");
  status.setAttribute("aria-live", saving ? "polite" : "assertive");
  const heading = document.createElement("strong");
  heading.textContent = title;
  const explanation = document.createElement("p");
  explanation.textContent = message;
  status.replaceChildren(heading, explanation);
  for (const week of inspectWeeks) {
    const link = document.createElement("a");
    link.className = "button";
    link.href = week;
    link.textContent = `View submitted week${inspectWeeks.size > 1 ? ` (${new URLSearchParams(week.split("?")[1]).get("week")})` : ""}`;
    status.append(link);
  }
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
    id,
    planned_date: form.elements.planned_date.value,
    planned_start_time: form.elements.planned_start_time.value || null,
    run_type: form.elements.run_type.value,
    sections: targets,
    user_note: form.elements.user_note.value || null,
    trainer_note: form.elements.trainer_note.value || null,
  };
}

function showSaveError(response, data, submittedDate) {
  const explanation = typeof data?.detail === "string" ? data.detail : "The server could not save this run. Try again.";
  if (response.status === 503 || response.status >= 500) {
    uncertainWeeks.add(weekUrl(submittedDate));
    showStatus("Saving could not be confirmed", `${explanation} Retrying the same run with unchanged values is safe.`, uncertainWeeks);
  } else if (response.status === 409) {
    showStatus("This run ID belongs to different saved data", `${explanation} Your earlier save may have succeeded. Check the submitted week.`, uncertainWeeks.size ? uncertainWeeks : new Set([weekUrl(submittedDate)]));
  } else if (response.status === 413) {
    showStatus("Could not save this run", `The request exceeds the 1 MiB (1,048,576 bytes) limit. Reduce the notes or sections and try again. ${explanation}`);
  } else {
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
    } else {
      showStatus("Could not save this run", explanation);
    }
  }
}

async function saveRun(event) {
  event.preventDefault();
  if (saving) return;
  const payload = creationPayload();
  if (!payload) {
    showStatus("Could not save this run", "Check the marked fields. All your entries are still here.");
    form.querySelector('[aria-invalid="true"]').focus();
    return;
  }
  saving = true;
  fields.disabled = true;
  save.disabled = true;
  form.setAttribute("aria-busy", "true");
  showStatus("Saving run...", "Your entries are being saved.");
  try {
    const response = await fetch("/v1/runs", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload), signal: AbortSignal.timeout(15000),
    });
    const data = await response.json().catch(() => null);
    saving = false;
    if ((response.status === 201 || response.status === 200) && data?.id === id && data?.planned_date === payload.planned_date) {
      location.assign(`${weekUrl(data.planned_date)}&saved=1`);
      return;
    }
    if (response.ok) throw new Error("Unreadable save response");
    showSaveError(response, data, payload.planned_date);
  } catch {
    saving = false;
    uncertainWeeks.add(weekUrl(payload.planned_date));
    showStatus("Saving could not be confirmed", "The connection was interrupted or the response was unreadable. Retrying the same run with unchanged values is safe.", uncertainWeeks);
  } finally {
    saving = false;
    fields.disabled = false;
    save.disabled = false;
    form.setAttribute("aria-busy", "false");
    updateSections();
  }
}

form.elements.planned_date.value = params.get("date") ?? "";
document.querySelector("#cancel").href = weekUrl(params.get("week"));
document.querySelector("#add-section").onclick = () => addSection();
sections.onclick = editSections;
form.onsubmit = saveRun;
addSection(false);
fields.disabled = false;
save.disabled = false;
status.hidden = true;
