import { weekUrl, scheduleUrl, takeFormContext, returnToSchedule } from "./schedule_navigation.js";
import { createCourseForm } from "./course_form.js";
import { randomUUID } from "./random_uuid.js";

const form = document.querySelector("#course-form");
const fields = document.querySelector("#form-fields");
const sections = document.querySelector("#section-list");
const status = document.querySelector("#save-status");
const save = document.querySelector("#save-course");
const params = new URLSearchParams(location.search);
const id = randomUUID();
const origin = takeFormContext();
let saving = false;
let leaving = false;
let initialDraft;
const uncertainWeeks = new Set();
const { addSection, editSections, updateSections, showValidation, showBodyErrors, readPayload } =
  createCourseForm(form, fields, sections, () => saving);

function inspectionUrl(value) {
  const url = weekUrl(value);
  return url === "/" ? url : `${url}&view=week`;
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

function showSaveError(response, data, submittedDate) {
  const explanation = typeof data?.detail === "string" ? data.detail : "The server could not save this course. Try again.";
  if (response.status === 503 || response.status >= 500) {
    uncertainWeeks.add(inspectionUrl(submittedDate));
    showStatus("Saving could not be confirmed", `${explanation} Retrying the same course with unchanged values is safe.`, uncertainWeeks);
  } else if (response.status === 409) {
    showStatus("This course ID belongs to different saved data", `${explanation} Your earlier save may have succeeded. Check the submitted week.`, uncertainWeeks.size ? uncertainWeeks : new Set([inspectionUrl(submittedDate)]));
  } else if (response.status === 413) {
    showStatus("Could not save this course", `The request exceeds the 1 MiB (1,048,576 bytes) limit. Reduce the notes or sections and try again. ${explanation}`);
  } else {
    if (Array.isArray(data?.detail)) {
      showBodyErrors(data.detail);
      showStatus("Could not save this course", data.detail.map(problem => problem.msg).join(" "));
    } else {
      showStatus("Could not save this course", explanation);
    }
  }
}

async function saveCourse(event) {
  event.preventDefault();
  if (saving) return;
  const { payload: values, errors } = readPayload();
  showValidation(errors);
  const payload = values && { id, ...values };
  if (!payload) {
    showStatus("Could not save this course", "Check the marked fields. All your entries are still here.");
    form.querySelector('[aria-invalid="true"]').focus();
    return;
  }
  saving = true;
  fields.disabled = true;
  save.disabled = true;
  form.setAttribute("aria-busy", "true");
  showStatus("Saving course...", "Your entries are being saved.");
  try {
    const response = await fetch("/v1/planned-courses", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload), signal: AbortSignal.timeout(15000),
    });
    const data = await response.json().catch(() => null);
    saving = false;
    if ((response.status === 201 || response.status === 200) && data?.id === id && data?.planned_date === payload.planned_date) {
      leaving = true;
      location.assign(returnToSchedule(origin, { outcome: "save", date: data.planned_date, id, fallback: weekUrl(data.planned_date) }));
      return;
    }
    if (response.ok) throw new Error("Unreadable save response");
    showSaveError(response, data, payload.planned_date);
  } catch {
    saving = false;
    uncertainWeeks.add(inspectionUrl(payload.planned_date));
    showStatus("Saving could not be confirmed", "The connection was interrupted or the response was unreadable. Retrying the same course with unchanged values is safe.", uncertainWeeks);
  } finally {
    saving = false;
    fields.disabled = false;
    save.disabled = false;
    form.setAttribute("aria-busy", "false");
    updateSections();
  }
  form.querySelector('[aria-invalid="true"]')?.focus();
}

form.elements.planned_date.value = params.get("date") ?? "";
document.querySelector("#cancel").href = origin ? scheduleUrl(origin.view, origin.date) : weekUrl(params.get("week"));
document.querySelector("#add-section").onclick = () => addSection();
sections.onclick = editSections;
form.onsubmit = saveCourse;
addSection(false);
fields.disabled = false;
save.disabled = false;
status.hidden = true;

function draft() {
  return JSON.stringify([...form.querySelectorAll("input, select, textarea")].map(input => input.value));
}
function navigate(url, returnOrigin = false) {
  const message = saving ? "Leave while saving? Leaving does not cancel the request, which may still complete." : "Discard your unsaved changes?";
  if ((saving || draft() !== initialDraft) && !confirm(message)) return;
  leaving = true;
  location.assign(returnOrigin ? returnToSchedule(origin, { fallback: url }) : url);
}
initialDraft = draft();
document.querySelector("#cancel").onclick = event => {
  event.preventDefault();
  navigate(event.currentTarget.href, true);
};
document.addEventListener("schedule-navigation", event => {
  event.preventDefault();
  navigate(document.querySelector("#cancel").href, true);
});
status.addEventListener("click", event => {
  const link = event.target.closest("a");
  if (link) { event.preventDefault(); navigate(link.href); }
});
window.addEventListener("beforeunload", event => {
  if (!leaving && (saving || draft() !== initialDraft)) event.preventDefault();
});
