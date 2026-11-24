import { calendarDate, weekUrl, scheduleUrl, takeFormContext, returnToSchedule } from "./schedule_navigation.js";
import { createCourseForm } from "./course_form.js";

const form = document.querySelector("#course-form");
const fields = document.querySelector("#form-fields");
const sections = document.querySelector("#section-list");
const status = document.querySelector("#save-status");
const save = document.querySelector("#save-course");
const deleteButton = document.querySelector("#delete-course");
const confirmation = document.querySelector("#delete-confirmation");
const confirmDelete = document.querySelector("#confirm-delete");
const keepCourse = document.querySelector("#keep-course");
const params = new URLSearchParams(location.search);
const id = location.pathname.split("/")[2];
const origin = takeFormContext();
let writePending = false;
let loading = true;
let confirmingDelete = false;
let baseline = null;
let reloadRequired = false;
let readVersion = 0;
const { addSection, editSections, updateSections, showValidation, showBodyErrors, readPayload, populate } =
  createCourseForm(form, fields, sections, () => writePending);
function showStatus(title, message) {
  status.hidden = false;
  const informational = title === "Changes saved" || title === "Saved course loaded" || title.startsWith("Loading") || title.startsWith("Reloading") || title.startsWith("Saving changes") || title.startsWith("Deleting course");
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

function validCourse(data) {
  return typeof data?.id === "string" && data.id.toLowerCase() === id.toLowerCase() &&
    typeof data.revision === "string" && /^[1-9][0-9]*$/.test(data.revision) &&
    calendarDate(data.planned_date) !== null &&
    ["easy", "hard", "interval", "long"].includes(data.course_type) &&
    Array.isArray(data.sections) && data.sections.length > 0 &&
    data.sections.every(section => section && typeof section.distance_m === "string" &&
      typeof section.target_pace_seconds_per_km === "string" &&
      /^[1-9][0-9]*$/.test(section.distance_m) &&
      /^[1-9][0-9]*$/.test(section.target_pace_seconds_per_km)) &&
    (data.planned_start_time === null || /^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(data.planned_start_time)) &&
    [data.user_note, data.trainer_note].every(note => note === null || typeof note === "string");
}

function updateControls() {
  fields.hidden = !baseline;
  deleteButton.hidden = !baseline;
  form.setAttribute("aria-busy", String(loading || writePending));
  document.querySelector("#reload-course").hidden = !baseline;
  fields.disabled = loading || writePending || confirmingDelete || !baseline;
  save.disabled = fields.disabled || reloadRequired;
  deleteButton.disabled = fields.disabled || reloadRequired;
  confirmDelete.disabled = writePending;
  keepCourse.disabled = writePending;
  document.querySelector("#reload-course").disabled = loading || writePending;
  document.querySelector("#retry-load").disabled = loading || writePending;
}

function closeConfirmation() {
  confirmingDelete = false;
  confirmation.hidden = true;
}

function prefill(course) {
  baseline = course;
  populate(course);
  reloadRequired = false;
  closeConfirmation();
  status.hidden = true;
  document.querySelector("#recovery").hidden = true;
  document.querySelector("#cancel").href = origin ? scheduleUrl(origin.view, origin.date) : editorWeek();
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
  if ((dirty() || writePending) && !window.leavingEditor) event.preventDefault();
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
    showStatus("Could not save this course", data.detail.map(problem => problem.msg).join(" "));
  } else showStatus("Could not save this course", "Review the entered values and try again.");
}

async function loadCourse(reloading = false) {
  const version = ++readVersion;
  loading = true;
  if (baseline) reloadRequired = true;
  closeConfirmation();
  updateControls();
  document.querySelector("#recovery").hidden = true;
  showStatus(reloading ? "Reloading saved course..." : "Loading course...", "Please wait.");
  let response;
  let data;
  try {
    response = await fetch(`/v1/planned-courses/${encodeURIComponent(id)}`, { cache: "no-store" });
    data = await response.json();
  } catch {
    if (version !== readVersion) return;
    loading = false;
    updateControls();
    showStatus("Could not load course", "A network error prevented loading. Retry when ready.");
    document.querySelector("#recovery").hidden = false;
    document.querySelector("#retry-load").hidden = false;
    if (baseline) fields.disabled = false;
    return;
  }
  if (version !== readVersion) return;
  loading = false;
  if (response.status === 404 || response.status === 422 && data?.detail?.some?.(problem => problem.loc?.[0] === "path")) {
    blockWrites("Course unavailable", baseline ? "This planned course is unavailable. Your draft is still here." : "This planned course is unavailable. Return to the schedule.");
    document.querySelector("#recovery").hidden = true;
    fields.disabled = !baseline;
  } else if (response.ok && validCourse(data)) {
    prefill(data);
    if (reloading) {
      showStatus("Saved course loaded", "Review the current values before another change.");
      document.querySelector("h1").focus();
    }
  } else {
    showStatus("Could not load course", "The server returned an unreadable response. Retry when ready.");
    document.querySelector("#recovery").hidden = false;
    document.querySelector("#retry-load").hidden = false;
    if (baseline) fields.disabled = false;
  }
  updateControls();
}

function showWriteFailure(response, data, deleting = false) {
  const action = deleting ? "Deletion" : "Saving";
  if (response.status === 404) {
    blockWrites("Course unavailable", "The course is no longer available. Your draft is still here.");
    document.querySelector("#recovery").hidden = true;
  }
  else if (response.status === 412) blockWrites("Saved course changed", "Your draft is intact. Reload the saved course before another edit or deletion.");
  else if (response.status === 428 || (response.status === 422 && data?.detail?.some?.(problem => problem.loc?.[0] === "header")))
    blockWrites("Reload required", "The revision could not be confirmed. Reload before another edit or deletion.");
  else if (response.status >= 500 || response.ok || !data)
    blockWrites(`${action} could not be confirmed`, "Your draft is intact. Reload the saved course to review the outcome.");
  else if (response.status === 413) showStatus("Could not save this course", "Reduce the notes or sections and try again.");
  else if (deleting) showStatus("Could not delete this course", "Deletion was rejected. Your draft is still here.");
  else showSaveError(response, data);
}

async function saveCourse(event) {
  event.preventDefault();
  if (loading || writePending || confirmingDelete || reloadRequired || !baseline) return;
  const { payload, errors } = readPayload();
  showValidation(errors);
  const changes = payload && draftChanges(payload);
  if (!changes) {
    showStatus("Could not save this course", "Check the marked fields. Your entries are still here.");
    form.querySelector('[aria-invalid="true"]')?.focus();
    return;
  }
  writePending = true;
  updateControls();
  form.setAttribute("aria-busy", "true");
  showStatus("Saving changes...", "Please wait.");
  try {
    const response = await fetch(`/v1/planned-courses/${encodeURIComponent(id)}`, {
      method: "PATCH", headers: { "Content-Type": "application/json", "If-Match": `"${baseline.revision}"` },
      body: JSON.stringify(changes), signal: AbortSignal.timeout(15000),
    });
    const data = await response.json().catch(() => null);
    if (response.status === 200 && validCourse(data)) {
      const destination = weekUrl(data.planned_date);
      if (destination === "/") {
        prefill(data);
        showStatus("Changes saved", "This date cannot be shown in a complete week. The course remains available here.");
        return;
      }
      window.leavingEditor = true;
      location.assign(returnToSchedule(origin, { outcome: "save", date: data.planned_date, id: data.id, fallback: destination }));
      return;
    }
    showWriteFailure(response, data);
  } catch {
    blockWrites("Saving could not be confirmed", "The response was lost or unreadable. Reload the saved course before another edit.");
  } finally {
    writePending = false;
    form.setAttribute("aria-busy", "false");
    updateControls();
    updateSections();
    form.querySelector('[aria-invalid="true"]')?.focus();
  }
}

async function deleteCourse() {
  if (loading || writePending || reloadRequired || !baseline || !confirmingDelete) return;
  writePending = true;
  updateControls();
  form.setAttribute("aria-busy", "true");
  showStatus("Deleting course...", "Please wait. Leaving this page does not cancel deletion.");
  status.focus();
  try {
    const response = await fetch(`/v1/planned-courses/${encodeURIComponent(id)}`, {
      method: "DELETE", headers: { "If-Match": `"${baseline.revision}"` },
      signal: AbortSignal.timeout(15000),
    });
    if (response.status === 204) {
      leave(returnToSchedule(origin, { outcome: "delete", fallback: editorWeek() }));
      return;
    }
    const data = await response.json().catch(() => null);
    showWriteFailure(response, data, true);
  } catch {
    blockWrites("Deletion could not be confirmed", "Your draft is intact. Reload the saved course to review the outcome.");
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
  document.querySelector("#delete-target").textContent = `${baseline.planned_date} · ${baseline.course_type[0].toUpperCase()}${baseline.course_type.slice(1)} course`;
  document.querySelector("#delete-draft-warning").hidden = !dirty();
  confirmation.hidden = false;
  updateControls();
  keepCourse.focus();
};
keepCourse.onclick = () => {
  closeConfirmation();
  updateControls();
  deleteButton.focus();
};
confirmDelete.onclick = deleteCourse;
form.onsubmit = saveCourse;
sections.onclick = editSections;
document.querySelector("#add-section").onclick = () => addSection();
document.querySelector("#cancel").onclick = event => {
  event.preventDefault();
  guardedLeave();
};
function reloadCourse() {
  if (!dirty() || confirm("Discard your unsaved draft and reload the saved course?")) loadCourse(Boolean(baseline));
}
document.querySelector("#reload-course").onclick = reloadCourse;
document.querySelector("#retry-load").onclick = reloadCourse;
loadCourse();

function guardedLeave() {
  const message = writePending ? "Leave while a write is pending? Leaving does not cancel the request, which may still complete." : "Discard your unsaved changes?";
  if ((!dirty() && !writePending) || confirm(message)) leave(returnToSchedule(origin, { fallback: editorWeek() }));
}
document.addEventListener("schedule-navigation", event => {
  event.preventDefault();
  guardedLeave();
});
