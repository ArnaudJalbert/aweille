// Shared form behavior for creating and editing a planned course.
export function createCourseForm(form, fields, sections, isSaving) {
  let sectionId = 0;

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

  function showValidation(errors) {
    clearFieldErrors();
    for (const [input, message] of errors) fieldError(input, message);
  }

  function showBodyErrors(problems) {
    for (const problem of problems) {
      const path = problem.loc ?? [];
      if (path[0] !== "body" || typeof problem.msg !== "string") continue;
      const input = path[1] === "sections"
        ? sections.children[path[2]]?.querySelector(`[data-field="${path[3]}"]`)
        : form.elements.namedItem(path[1]);
      fieldError(input, problem.msg);
    }
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
    if (!button || isSaving()) return;
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

  function distanceMetres(value) {
    const match = /^(\d+)(?:\.(\d+))?$/.exec(value);
    if (match && !/[1-9]/.test((match[2] ?? "").slice(3))) {
      const digits = `${match[1]}${(match[2] ?? "").slice(0, 3).padEnd(3, "0")}`.replace(/^0+/, "");
      if (digits) return digits;
    }
    return null;
  }

  function paceSeconds(value) {
    const match = /^(\d+):([0-5]\d)$/.exec(value);
    if (match) {
      const seconds = BigInt(match[1]) * 60n + BigInt(match[2]);
      if (seconds > 0n) return String(seconds);
    }
    return null;
  }

  // Reading a draft never changes validation feedback or focus.
  function readPayload() {
    const errors = [];
    for (const input of fields.querySelectorAll("[name]")) {
      if (!input.validity.valid) errors.push([input, input.validationMessage]);
    }
    const targets = [...sections.children].map(row => {
      const distance = row.querySelector('[data-field="distance_m"]');
      const pace = row.querySelector('[data-field="target_pace_seconds_per_km"]');
      const metres = distanceMetres(distance.value);
      const seconds = paceSeconds(pace.value);
      if (!metres) errors.push([distance, "Enter positive kilometres in whole metres, for example 1 or 0.001. No rounding is allowed."]);
      if (!seconds) errors.push([pace, "Enter a positive pace with seconds from 00 to 59, for example 5:45."]);
      return { distance_m: metres, target_pace_seconds_per_km: seconds };
    });
    return {
      payload: errors.length ? null : {
        planned_date: form.elements.planned_date.value,
        planned_start_time: form.elements.planned_start_time.value || null,
        course_type: form.elements.course_type.value,
        sections: targets,
        user_note: form.elements.user_note.value || null,
        trainer_note: form.elements.trainer_note.value || null,
      },
      errors,
    };
  }

  function populate(course) {
    for (const field of ["planned_date", "planned_start_time", "course_type", "user_note", "trainer_note"])
      form.elements[field].value = course[field] ?? "";
    sections.replaceChildren();
    for (const section of course.sections) {
      addSection(false);
      const row = sections.lastElementChild;
      const digits = section.distance_m.padStart(4, "0");
      const fraction = digits.slice(-3).replace(/0+$/, "");
      row.querySelector('[data-field="distance_m"]').value = `${digits.slice(0, -3)}${fraction ? `.${fraction}` : ""}`;
      const pace = BigInt(section.target_pace_seconds_per_km);
      row.querySelector('[data-field="target_pace_seconds_per_km"]').value = `${pace / 60n}:${String(pace % 60n).padStart(2, "0")}`;
    }
    clearFieldErrors();
  }

  return { addSection, editSections, updateSections, clearFieldErrors, showValidation, showBodyErrors, readPayload, populate };
}
