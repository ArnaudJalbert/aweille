// Calendar arithmetic uses UTC; actual runs keep Montreal local dates and times.
export function calendarDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.getUTCFullYear() >= 1 &&
    date.getUTCFullYear() <= 9999 && date.toISOString().slice(0, 10) === value ? date : null;
}
export function dateString(date) { return date.toISOString().slice(0, 10); }
export function offsetDate(date, offset) {
  const next = new Date(date);
  next.setUTCDate(next.getUTCDate() + offset);
  return next;
}
export function containingMonday(date) { return offsetDate(date, -((date.getUTCDay() + 6) % 7)); }
export function readableWeek(date) {
  return date && calendarDate(dateString(containingMonday(date))) &&
    calendarDate(dateString(offsetDate(containingMonday(date), 7)));
}
export function montrealToday() {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Toronto", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return calendarDate(`${values.year.padStart(4, "0")}-${values.month}-${values.day}`);
}
export function weekUrl(value) {
  const date = calendarDate(value);
  return readableWeek(date) ? `/?week=${dateString(containingMonday(date))}` : "/";
}
export function scheduleUrl(view, value) {
  const date = calendarDate(value);
  if (!["day", "week"].includes(view) || !readableWeek(date)) return "/";
  return `/?${new URLSearchParams({ week: dateString(containingMonday(date)), view, date: value })}`;
}

const formKey = "aweille-schedule-form";
const returnKey = "aweille-schedule-return";
function take(key) {
  try {
    const value = sessionStorage.getItem(key);
    sessionStorage.removeItem(key);
    return value ? JSON.parse(value) : null;
  } catch { return null; }
}
function put(key, value) {
  try { sessionStorage.setItem(key, JSON.stringify(value)); return true; }
  catch { return false; }
}
function validContext(value) {
  return value && ["day", "week"].includes(value.view) && readableWeek(calendarDate(value.date)) &&
    typeof value.focus === "string" && /^(?:add-\d{4}-\d{2}-\d{2}|run-[0-9a-f-]{36}|week-heading)$/.test(value.focus) &&
    value.choices && ["day", "week"].every(view => value.choices[view] &&
      typeof value.choices[view] === "object" && !Array.isArray(value.choices[view]) &&
      Object.entries(value.choices[view]).every(([id, open]) => /^[0-9a-f-]{36}$/.test(id) && typeof open === "boolean"));
}

// A single-use tab handoff transports presentation only, never drafts or revisions.
export function prepareFormLink(link, context) {
  link.addEventListener("click", () => {
    const token = crypto.randomUUID();
    const target = new URL(link.href);
    target.searchParams.delete("context");
    if (put(formKey, { ...context, token, target: target.pathname + target.search })) {
      target.searchParams.set("context", token);
      link.href = target.pathname + target.search;
    }
  });
}
export function takeFormContext() {
  const value = take(formKey);
  const url = new URL(location.href);
  const token = url.searchParams.get("context");
  url.searchParams.delete("context");
  return validContext(value) && token === value.token && value.target === url.pathname + url.search ? value : null;
}
export function returnToSchedule(context, { outcome = "cancel", date, id, fallback = "/" } = {}) {
  if (!validContext(context) && outcome !== "save") {
    const url = new URL(fallback, location.origin);
    url.hash = "week-heading";
    return url.pathname + url.search + url.hash;
  }
  const selectedDate = outcome === "save" ? date : context.date;
  const view = context?.view ?? "day";
  const url = new URL(scheduleUrl(view, selectedDate), location.origin);
  if (url.pathname !== "/" || !url.searchParams.has("date")) return fallback;
  const sameWeek = context && weekUrl(context.date) === weekUrl(selectedDate);
  const value = {
    view, date: selectedDate,
    choices: sameWeek ? context.choices : { day: {}, week: {} },
    focus: outcome === "save" ? `run-${id}` : outcome === "delete" ? "week-heading" : context.focus,
    token: crypto.randomUUID(),
  };
  if (validContext(value) && put(returnKey, value)) url.searchParams.set("return", value.token);
  else url.hash = "week-heading";
  return url.pathname + url.search + url.hash;
}
export function takeScheduleReturn() {
  const value = take(returnKey);
  const url = new URL(location.href);
  const token = url.searchParams.get("return");
  url.searchParams.delete("return");
  if (token) history.replaceState(null, "", url);
  return validContext(value) && value.token === token && value.view === url.searchParams.get("view") &&
    value.date === url.searchParams.get("date") ? value : null;
}
