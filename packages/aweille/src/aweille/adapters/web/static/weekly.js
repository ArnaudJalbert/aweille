const heading = document.querySelector("#week-heading");
const days = document.querySelector("#days");
const status = document.querySelector("#status");
const navigation = document.querySelector("#week-navigation");
const runTypes = { easy: "Easy run", hard: "Hard run", interval: "Interval run", long: "Long run" };
let selectedWeek;
let readVersion = 0;

// UTC is used only for calendar arithmetic, never to interpret a run's local time.
function calendarDate(value) {
  return new Date(`${value}T00:00:00Z`);
}

function dateString(date) {
  return date.toISOString().slice(0, 10);
}

function offsetDate(date, offset) {
  const next = new Date(date);
  next.setUTCDate(next.getUTCDate() + offset);
  return next;
}

function containingMonday(date) {
  return offsetDate(date, -((date.getUTCDay() + 6) % 7));
}

function isCalendarDate(date) {
  return !Number.isNaN(date.getTime()) && date.getUTCFullYear() >= 1 && date.getUTCFullYear() <= 9999;
}

function isReadableWeek(monday) {
  return isCalendarDate(monday) && isCalendarDate(offsetDate(monday, 7));
}

function currentMonday() {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Toronto", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date());
  const value = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return containingMonday(calendarDate(`${value.year.padStart(4, "0")}-${value.month}-${value.day}`));
}

function monthName(date, length = "long") {
  return date.toLocaleDateString("en-US", { month: length, timeZone: "UTC" });
}

function weekTitle(monday) {
  const sunday = offsetDate(monday, 6);
  const start = `${monthName(monday)} ${monday.getUTCDate()}`;
  if (monday.getUTCFullYear() !== sunday.getUTCFullYear()) {
    return `${start}, ${monday.getUTCFullYear()} to ${monthName(sunday)} ${sunday.getUTCDate()}, ${sunday.getUTCFullYear()}`;
  }
  const end = monday.getUTCMonth() === sunday.getUTCMonth()
    ? sunday.getUTCDate() : `${monthName(sunday)} ${sunday.getUTCDate()}`;
  return `${start} to ${end}, ${sunday.getUTCFullYear()}`;
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

function renderRun(run) {
  const article = element("article", undefined, "run");
  const title = runTypes[run.run_type] + (run.planned_start_time ? ` @ ${run.planned_start_time}` : "");
  article.append(element("h3", title));
  const layout = element("div", undefined, "run-layout");
  const sections = element("ol", undefined, "sections");
  for (const section of run.sections) {
    const row = element("li");
    row.append(element("span", kilometres(section.distance_m)));
    row.append(element("span", pace(section.target_pace_seconds_per_km), "pace"));
    sections.append(row);
  }
  layout.append(sections);
  const notes = element("div", undefined, "notes");
  for (const [field, label] of [["user_note", "Personal note"], ["trainer_note", "Trainer note"]]) {
    if (run[field] === null) continue;
    const note = element("div");
    note.append(element("span", label, "note-label"), element("p", run[field]));
    notes.append(note);
  }
  if (notes.childElementCount) layout.append(notes);
  article.append(layout);
  return article;
}

function renderDays(monday, runs) {
  const cards = [];
  for (let offset = 0; offset < 7; offset++) {
    const date = offsetDate(monday, offset);
    const key = dateString(date);
    const day = element("section", undefined, "day");
    day.setAttribute("aria-labelledby", `day-${key}`);
    const header = element("header", undefined, "day-heading");
    const weekday = date.toLocaleDateString("en-US", { weekday: "long", timeZone: "UTC" });
    const title = element("h2", `${weekday} `);
    title.id = `day-${key}`;
    title.append(element("span", `${monthName(date, "short")} ${date.getUTCDate()}`));
    header.append(title);
    const add = element("a", "Add run", "button add-run");
    add.href = `/runs/new?${new URLSearchParams({ date: key, week: dateString(monday) })}`;
    add.setAttribute("aria-label", `Add run for ${weekday}, ${monthName(date)} ${date.getUTCDate()}`);
    header.append(add);
    const body = element("div", undefined, "day-body");
    const planned = runs.filter(run => run.planned_date === key);
    body.append(...planned.map(renderRun));
    if (!planned.length) body.append(element("p", "No runs planned", "muted"));
    day.append(header, body);
    cards.push(day);
  }
  days.replaceChildren(...cards);
}

async function fetchRuns(monday) {
  const query = new URLSearchParams({ start: dateString(monday), end: dateString(offsetDate(monday, 7)) });
  let response;
  try {
    response = await fetch(`/v1/runs?${query}`, { cache: "no-store" });
  } catch {
    return { error: "A network error prevented loading runs. Check your connection and try again." };
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const explanation = typeof data?.detail === "string" ? ` ${data.detail}` : "";
    const message = response.status === 503
      ? "The server is temporarily unavailable. Try again in a moment."
      : "The server could not load these runs. Try again.";
    return { error: message + explanation };
  }
  if (!Array.isArray(data)) {
    return { error: "The server returned an unreadable response. Try again." };
  }
  return { runs: data };
}

function showReadError(message) {
  status.hidden = false;
  status.className = "notice";
  status.setAttribute("role", "alert");
  status.setAttribute("aria-live", "assertive");
  const retry = element("button", "Retry");
  retry.type = "button";
  retry.onclick = () => selectWeek(selectedWeek, false);
  status.replaceChildren(element("strong", "Could not load runs for this week"), element("p", message), retry);
}

async function loadWeek(monday) {
  const version = ++readVersion;
  heading.textContent = weekTitle(monday);
  days.replaceChildren();
  days.setAttribute("aria-busy", "true");
  if (status.contains(document.activeElement)) heading.focus();
  status.hidden = false;
  status.className = "loading";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  status.textContent = "Loading runs...";
  const result = await fetchRuns(monday);
  if (version !== readVersion) return;
  if (result.error) {
    showReadError(result.error);
  } else {
    try {
      renderDays(monday, result.runs);
      status.textContent = "Run saved.";
      status.className = "save-success";
      status.hidden = new URLSearchParams(location.search).get("saved") !== "1";
    } catch {
      showReadError("The server returned an unreadable response. Try again.");
    }
  }
  days.setAttribute("aria-busy", "false");
}

function updateNavigation() {
  navigation.hidden = false;
  document.querySelector("#previous-week").disabled = !selectedWeek || !isReadableWeek(offsetDate(selectedWeek, -7));
  document.querySelector("#next-week").disabled = !selectedWeek || !isReadableWeek(offsetDate(selectedWeek, 7));
}

function showSelectionError() {
  readVersion++;
  selectedWeek = null;
  heading.textContent = "Choose a week";
  days.replaceChildren();
  days.setAttribute("aria-busy", "false");
  status.hidden = false;
  status.className = "notice";
  status.setAttribute("role", "alert");
  status.setAttribute("aria-live", "assertive");
  status.replaceChildren(
    element("strong", "Invalid week selection"),
    element("p", "Choose a valid calendar date for a complete Monday-to-Sunday week, or select This week."),
  );
  updateNavigation();
}

function selectWeek(monday, push = true) {
  if (!isReadableWeek(monday)) {
    showSelectionError();
    return;
  }
  selectedWeek = monday;
  const url = new URL(location.href);
  if (push) url.searchParams.delete("saved");
  url.searchParams.set("week", dateString(monday));
  if (url.href !== location.href) {
    history[push ? "pushState" : "replaceState"](null, "", url);
  }
  updateNavigation();
  loadWeek(monday);
}

function restoreSelection() {
  const value = new URLSearchParams(location.search).get("week");
  if (value !== null && (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !isCalendarDate(calendarDate(value)) || dateString(calendarDate(value)) !== value)) {
    showSelectionError();
    return;
  }
  selectWeek(value === null ? currentMonday() : containingMonday(calendarDate(value)), false);
}

document.querySelector("#previous-week").onclick = () => selectWeek(offsetDate(selectedWeek, -7));
document.querySelector("#next-week").onclick = () => selectWeek(offsetDate(selectedWeek, 7));
document.querySelector("#this-week").onclick = () => selectWeek(currentMonday());
window.addEventListener("popstate", restoreSelection);
restoreSelection();
