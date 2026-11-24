import { calendarDate, dateString, offsetDate, containingMonday, readableWeek, montrealToday, scheduleUrl, prepareFormLink, takeScheduleReturn } from "./schedule_navigation.js";
import { setupCalendar } from "./schedule_calendar.js";

const heading = document.querySelector("#week-heading");
const exact = document.querySelector("#exact-date");
const days = document.querySelector("#days");
const status = document.querySelector("#status");
const dayAdd = document.querySelector("#day-add");
const courseTypes = { easy: "Easy course", hard: "Hard course", interval: "Interval course", long: "Long course" };
let selectedDate;
let view = "day";
let choices = { day: {}, week: {} };
let readVersion = 0;
let returnContext = takeScheduleReturn();
let pendingFocus = returnContext?.focus;
if (location.hash === "#week-heading") {
  pendingFocus ??= "week-heading";
  history.replaceState(null, "", location.pathname + location.search);
}

function monthName(date, length = "long") {
  return date.toLocaleDateString("en-US", { month: length, timeZone: "UTC" });
}
function weekTitle(monday) {
  const sunday = offsetDate(monday, 6);
  const start = `${monthName(monday)} ${monday.getUTCDate()}`;
  if (monday.getUTCFullYear() !== sunday.getUTCFullYear())
    return `${start}, ${monday.getUTCFullYear()} to ${monthName(sunday)} ${sunday.getUTCDate()}, ${sunday.getUTCFullYear()}`;
  const end = monday.getUTCMonth() === sunday.getUTCMonth() ? sunday.getUTCDate() : `${monthName(sunday)} ${sunday.getUTCDate()}`;
  return `${start} to ${end}, ${sunday.getUTCFullYear()}`;
}
function relativeTitle() {
  const today = montrealToday();
  const difference = view === "day" ? Math.round((selectedDate - today) / 86400000)
    : Math.round((containingMonday(selectedDate) - containingMonday(today)) / 604800000);
  if (view === "day") return difference === 0 ? "Today" : difference === 1 ? "Tomorrow" : difference === -1 ? "Yesterday"
    : difference > 0 ? `In ${difference} Days` : `${-difference} Days Ago`;
  return difference === 0 ? "This Week" : difference === 1 ? "Next Week" : difference === -1 ? "Last Week"
    : difference > 0 ? `In ${difference} Weeks` : `${-difference} Weeks Ago`;
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function kilometres(metres) {
  const digits = metres.padStart(4, "0");
  const fraction = digits.slice(-3).replace(/0+$/, "");
  return `${digits.slice(0, -3)}${fraction ? `.${fraction}` : ""} km`;
}
function pace(seconds) {
  const value = BigInt(seconds);
  return `${value / 60n}:${String(value % 60n).padStart(2, "0")}/km`;
}
function linkContext(link, focus) {
  prepareFormLink(link, { view, date: dateString(selectedDate), focus, choices });
}
function addCourse(date) {
  const key = dateString(date);
  const add = element("a", undefined, "add-course");
  add.append(element("span", "Add course"));
  add.id = `add-${key}`;
  add.href = `/planned-courses/new?${new URLSearchParams({ date: key, week: dateString(containingMonday(selectedDate)) })}`;
  add.setAttribute("aria-label", `Add course for ${date.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", timeZone: "UTC" })}`);
  linkContext(add, add.id);
  return add;
}
function renderCourse(course) {
  const article = element("article", undefined, "course");
  article.append(element("div", course.planned_start_time ?? "Untimed", "course-time measurement"));
  const body = element("div", undefined, "course-content");
  body.append(element("span", "Running", "activity-kind"));
  const edit = element("a", undefined, "course-summary");
  edit.id = `course-${course.id}`;
  edit.href = `/planned-courses/${encodeURIComponent(course.id)}/edit?week=${dateString(containingMonday(selectedDate))}`;
  const title = courseTypes[course.course_type];
  if (!title) throw new Error("Unreadable course type");
  edit.append(element("h3", title));
  const total = course.sections.reduce((sum, section) => sum + BigInt(section.distance_m), 0n);
  const commonPace = course.sections.every(section => section.target_pace_seconds_per_km === course.sections[0].target_pace_seconds_per_km);
  const summary = `${kilometres(String(total))} · ${course.sections.length} section${course.sections.length === 1 ? "" : "s"} · ${commonPace ? pace(course.sections[0].target_pace_seconds_per_km) : "Varied pace"}`;
  edit.append(element("span", summary, "measurement course-measurements"));
  edit.setAttribute("aria-label", `Edit ${course.course_type} course on ${course.planned_date}${course.planned_start_time ? ` at ${course.planned_start_time}` : ""}. ${summary}`);
  linkContext(edit, edit.id);
  body.append(edit);
  const details = element("details", undefined, "course-details");
  details.open = choices[view][course.id] ?? view === "day";
  const disclosure = element("summary");
  disclosure.append(element("span", "Show details", "show-details"), element("span", "Hide details", "hide-details"));
  const nameDisclosure = () => disclosure.setAttribute("aria-label", `${details.open ? "Hide" : "Show"} details for ${course.course_type} course on ${course.planned_date}${course.planned_start_time ? ` at ${course.planned_start_time}` : ""}`);
  nameDisclosure();
  details.append(disclosure);
  const layout = element("div", undefined, "course-layout");
  const sections = element("ol", undefined, "sections");
  for (const section of course.sections) {
    const row = element("li");
    row.append(element("span", kilometres(section.distance_m)), element("span", pace(section.target_pace_seconds_per_km), "pace"));
    sections.append(row);
  }
  layout.append(sections);
  const notes = element("div", undefined, "notes");
  for (const [field, label] of [["user_note", "Personal note"], ["trainer_note", "Trainer note"]]) {
    if (course[field] === null) continue;
    if (typeof course[field] !== "string") throw new Error("Unreadable note");
    const note = element("div");
    note.append(element("span", label, "note-label"), element("p", course[field]));
    notes.append(note);
  }
  if (notes.childElementCount) layout.append(notes);
  details.append(layout);
  // Ignore the initial native toggle event when applying each view's default.
  const viewChoices = choices[view];
  let initial = true;
  details.addEventListener("toggle", () => {
    nameDisclosure();
    if (!initial) viewChoices[course.id] = details.open;
    initial = false;
  });
  // Closed defaults do not emit toggle. User input marks the first change as manual.
  disclosure.addEventListener("click", () => { initial = false; });
  body.append(details); article.append(body);
  return article;
}
function renderDays(courses) {
  const monday = containingMonday(selectedDate);
  const cards = [];
  const visible = view === "day" ? [selectedDate] : Array.from({ length: 7 }, (_, offset) => offsetDate(monday, offset));
  dayAdd.replaceChildren();
  if (view === "day") dayAdd.append(addCourse(selectedDate));
  for (const date of visible) {
    const key = dateString(date);
    const day = element("section", undefined, "day");
    day.setAttribute("aria-label", `${date.toLocaleDateString("en-US", { weekday: "long", timeZone: "UTC" })} ${monthName(date, "short")} ${date.getUTCDate()}`);
    const header = element("header", undefined, "day-heading");
    const title = element("h2", `${date.toLocaleDateString("en-US", { weekday: "long", timeZone: "UTC" })} `);
    title.id = `day-${key}`;
    title.append(element("span", `${monthName(date, "short")} ${date.getUTCDate()}`, "measurement"));
    header.append(title);
    if (view === "week") header.append(addCourse(date));
    const body = element("div", undefined, "day-body");
    const planned = courses.filter(course => course.planned_date === key);
    if (planned.length > 1) title.lastElementChild.append(element("span", ` · ${planned.length} courses`, "day-count"));
    body.append(...planned.map(renderCourse));
    if (!planned.length) body.append(element("p", "No courses planned", "muted"));
    day.classList.toggle("empty-day", !planned.length);
    if (view === "week") day.append(header);
    day.append(body); cards.push(day);
  }
  days.replaceChildren(...cards);
}
async function fetchCourses(monday) {
  const query = new URLSearchParams({ start: dateString(monday), end: dateString(offsetDate(monday, 7)) });
  let response;
  try { response = await fetch(`/v1/planned-courses?${query}`, { cache: "no-store" }); }
  catch { return { error: "A network error prevented loading courses. Check your connection and try again." }; }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const explanation = typeof data?.detail === "string" ? ` ${data.detail}` : "";
    return { error: (response.status === 503 ? "The server is temporarily unavailable. Try again in a moment." : "The server could not load these courses. Try again.") + explanation };
  }
  if (!Array.isArray(data)) return { error: "The server returned an unreadable response. Try again." };
  return { courses: data };
}
function showReadError(message) {
  days.replaceChildren(); dayAdd.replaceChildren();
  status.hidden = false; status.className = "notice";
  status.setAttribute("role", "alert"); status.setAttribute("aria-live", "assertive");
  const retry = element("button", "Retry"); retry.type = "button";
  retry.onclick = () => loadSelection();
  status.replaceChildren(element("strong", "Could not load courses for this week"), element("p", message), retry);
}
async function loadSelection() {
  const version = ++readVersion;
  heading.textContent = relativeTitle();
  exact.textContent = view === "day" ? selectedDate.toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric", timeZone: "UTC" }) : weekTitle(containingMonday(selectedDate));
  days.replaceChildren(); dayAdd.replaceChildren(); days.setAttribute("aria-busy", "true");
  if (status.contains(document.activeElement)) heading.focus();
  status.hidden = false; status.className = "loading";
  status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
  status.textContent = "Loading courses...";
  const result = await fetchCourses(containingMonday(selectedDate));
  if (version !== readVersion) return;
  if (result.error) showReadError(result.error);
  else {
    try {
      renderDays(result.courses); status.hidden = true;
      if (pendingFocus) {
        (document.getElementById(pendingFocus) ?? heading).focus();
        pendingFocus = null;
      }
    } catch { showReadError("The server returned an unreadable response. Try again."); }
  }
  days.setAttribute("aria-busy", "false");
}
function showSelectionError() {
  readVersion++; selectedDate = null;
  updatePeriodNavigation();
  heading.textContent = "Choose a date"; exact.textContent = "";
  days.replaceChildren(); dayAdd.replaceChildren(); days.setAttribute("aria-busy", "false");
  status.hidden = false; status.className = "notice";
  status.setAttribute("role", "alert"); status.setAttribute("aria-live", "assertive");
  status.replaceChildren(element("strong", "Invalid week selection"), element("p", "Choose a valid calendar date for a complete Monday-to-Sunday week, or select Today."));
}
function updatePeriodNavigation() {
  for (const [direction, step, label] of [["previous", -1, "Previous"], ["next", 1, "Next"]]) {
    const button = document.querySelector(`#${direction}-period`);
    const offset = step * (view === "week" ? 7 : 1);
    button.hidden = false;
    button.setAttribute("aria-label", `${label} ${view}`);
    button.title = `${label} ${view}`;
    button.disabled = !selectedDate || !readableWeek(offsetDate(selectedDate, offset));
    button.onclick = () => select(offsetDate(selectedDate, offset));
  }
}
function select(date, nextView = view, push = true) {
  if (push) pendingFocus = null;
  if (!readableWeek(date)) { showSelectionError(); return; }
  if (selectedDate && dateString(containingMonday(selectedDate)) !== dateString(containingMonday(date))) choices = { day: {}, week: {} };
  selectedDate = date; view = nextView;
  updatePeriodNavigation();
  document.querySelector("#view-day").setAttribute("aria-pressed", String(view === "day"));
  document.querySelector("#view-week").setAttribute("aria-pressed", String(view === "week"));
  days.classList.toggle("week-view", view === "week");
  const url = scheduleUrl(view, dateString(date));
  if (url !== location.pathname + location.search) history[push ? "pushState" : "replaceState"](null, "", url);
  loadSelection();
}
function restoreSelection() {
  choices = { day: {}, week: {} };
  const params = new URLSearchParams(location.search);
  const nextView = params.get("view") ?? "day";
  const explicit = params.get("date");
  const week = params.get("week");
  let date = explicit === null ? montrealToday() : calendarDate(explicit);
  if (!["day", "week"].includes(nextView) || week !== null && !readableWeek(calendarDate(week))) { showSelectionError(); return; }
  if (week !== null && explicit === null) {
    const monday = containingMonday(calendarDate(week));
    if (dateString(monday) !== dateString(containingMonday(date))) date = monday;
  }
  if (date && week !== null && dateString(containingMonday(date)) !== dateString(containingMonday(calendarDate(week)))) { showSelectionError(); return; }
  if (returnContext) { choices = returnContext.choices; returnContext = null; }
  selectedDate = null;
  select(date, nextView, false);
}

document.querySelector("#schedule-toolbar").hidden = false;
document.querySelector("#open-calendar").hidden = false;
document.querySelector("#view-day").onclick = () => select(selectedDate ?? montrealToday(), "day");
document.querySelector("#view-week").onclick = () => select(selectedDate ?? montrealToday(), "week");
document.querySelector("#today").onclick = () => select(montrealToday(), "day");
setupCalendar(date => select(date), () => ({ view, date: selectedDate }));
window.addEventListener("popstate", () => { pendingFocus = null; restoreSelection(); });
window.addEventListener("pageshow", event => { if (event.persisted) { pendingFocus = null; restoreSelection(); } });
restoreSelection();
