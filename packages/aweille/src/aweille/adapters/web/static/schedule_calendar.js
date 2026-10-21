import { calendarDate, dateString, offsetDate, containingMonday, readableWeek, montrealToday } from "./schedule_navigation.js";

export function setupCalendar(select, selection) {
  const dialog = document.querySelector("#calendar");
  const grid = document.querySelector("#calendar-grid");
  const opener = document.querySelector("#open-calendar");
  let cursor;
  let month;
  let view;
  let selected;
  function render() {
    document.querySelector("#calendar-title").textContent = view === "day" ? "Choose day" : "Choose week";
    document.querySelector("#calendar-context").textContent = view === "day" ? "Choose the day you want to see." : "Choose any date in the week you want to see.";
    document.querySelector("#calendar-heading").textContent = month.toLocaleDateString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
    grid.replaceChildren();
    const labels = document.createElement("div");
    labels.setAttribute("role", "row");
    for (const day of ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]) {
      const label = document.createElement("span");
      label.setAttribute("role", "columnheader"); label.textContent = day; labels.append(label);
    }
    grid.append(labels);
    const start = containingMonday(month);
    for (let row = 0; row < 6; row++) {
      const week = document.createElement("div"); week.setAttribute("role", "row");
      for (let col = 0; col < 7; col++) {
        const date = offsetDate(start, row * 7 + col);
        const value = dateString(date);
        const button = document.createElement("button");
        button.type = "button"; button.setAttribute("role", "gridcell");
        button.textContent = date.getUTCDate(); button.dataset.date = value;
        button.setAttribute("aria-label", value);
        button.setAttribute("aria-selected", String(view === "day" ? value === dateString(selected) : dateString(containingMonday(date)) === dateString(containingMonday(selected))));
        button.classList.toggle("other-month", date.getUTCMonth() !== month.getUTCMonth());
        button.disabled = !calendarDate(value) || !readableWeek(date);
        button.tabIndex = value === dateString(cursor) ? 0 : -1;
        button.onclick = () => { dialog.close(); select(date); };
        week.append(button);
      }
      grid.append(week);
    }
    const previous = offsetDate(month, -1);
    const next = new Date(month); next.setUTCMonth(next.getUTCMonth() + 1);
    document.querySelector("#previous-month").disabled = !calendarDate(dateString(previous));
    document.querySelector("#next-month").disabled = !calendarDate(dateString(next));
    document.querySelector("#calendar-shortcut").textContent = view === "day" ? "Today" : "This Week";
  }
  function focusCursor() { grid.querySelector(`[data-date="${dateString(cursor)}"]`)?.focus(); }
  function changeMonth(delta) {
    month.setUTCMonth(month.getUTCMonth() + delta);
    cursor = new Date(month);
    render(); focusCursor();
  }
  opener.onclick = () => {
    const state = selection();
    view = state.view; selected = state.date ?? montrealToday(); cursor = new Date(selected);
    month = new Date(cursor); month.setUTCDate(1);
    render(); dialog.showModal(); focusCursor();
  };
  document.querySelector("#previous-month").onclick = () => changeMonth(-1);
  document.querySelector("#next-month").onclick = () => changeMonth(1);
  document.querySelector("#calendar-shortcut").onclick = () => { dialog.close(); select(montrealToday()); };
  document.querySelector("#cancel-calendar").onclick = () => dialog.close();
  dialog.addEventListener("close", () => opener.focus());
  grid.addEventListener("keydown", event => {
    const deltas = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
    if (!(event.key in deltas)) return;
    event.preventDefault();
    const next = offsetDate(calendarDate(event.target.dataset.date) ?? cursor, deltas[event.key]);
    if (!calendarDate(dateString(next)) || !readableWeek(next)) return;
    cursor = next; month = new Date(next); month.setUTCDate(1);
    render(); focusCursor();
  });
}
