import { createRunForm } from "./run_form.js";

const form = document.querySelector("#run-form");
const fields = document.querySelector("#form-fields");
const sections = document.querySelector("#section-list");
const status = document.querySelector("#save-status");
const save = document.querySelector("#save-run");
const params = new URLSearchParams(location.search);
const id = crypto.randomUUID();
let saving = false;
const uncertainWeeks = new Set();
const { addSection, editSections, updateSections, showValidation, showBodyErrors, readPayload } =
  createRunForm(form, fields, sections, () => saving);

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
      showBodyErrors(data.detail);
      showStatus("Could not save this run", data.detail.map(problem => problem.msg).join(" "));
    } else {
      showStatus("Could not save this run", explanation);
    }
  }
}

async function saveRun(event) {
  event.preventDefault();
  if (saving) return;
  const { payload: values, errors } = readPayload();
  showValidation(errors);
  const payload = values && { id, ...values };
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
      location.assign(weekUrl(data.planned_date));
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
