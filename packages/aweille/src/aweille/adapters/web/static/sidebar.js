const application = document.querySelector("#application");
const content = document.querySelector("#content");
const sidebar = document.querySelector("#sidebar");
const menu = document.querySelector(".menu-control");
const close = document.querySelector("#close-navigation");
const backdrop = document.querySelector("#navigation-backdrop");
let desktopExpanded = true;
let narrow;
let drawerOpen = false;

function render() {
  const expanded = narrow ? drawerOpen : desktopExpanded;
  application.classList.toggle("drawer-mode", narrow);
  application.classList.toggle("sidebar-expanded", !narrow && desktopExpanded);
  sidebar.hidden = !expanded;
  close.hidden = !narrow;
  menu.setAttribute("aria-expanded", String(expanded));
  backdrop.hidden = !drawerOpen;
  content.inert = drawerOpen;
  document.body.classList.toggle("drawer-open", drawerOpen);
  if (drawerOpen) {
    sidebar.setAttribute("role", "dialog");
    sidebar.setAttribute("aria-modal", "true");
  } else {
    sidebar.removeAttribute("role");
    sidebar.removeAttribute("aria-modal");
  }
}

function dismiss() {
  drawerOpen = false;
  render();
  menu.focus();
}

menu.disabled = false;
menu.onclick = () => {
  if (narrow) drawerOpen = !drawerOpen;
  else desktopExpanded = !desktopExpanded;
  render();
  if (drawerOpen) close.focus();
  else menu.focus();
};
close.onclick = dismiss;
backdrop.onclick = dismiss;
document.addEventListener("keydown", event => {
  if (!drawerOpen) return;
  if (event.key === "Escape") {
    event.preventDefault();
    event.stopImmediatePropagation();
    dismiss();
  } else if (event.key === "Tab") {
    const controls = [...sidebar.querySelectorAll('a[href], button:not(:disabled)')].filter(node => !node.hidden);
    const first = controls[0];
    const last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault(); first.focus();
    }
  }
}, true);

document.querySelector("#schedule-link").onclick = event => {
  event.preventDefault();
  if (drawerOpen) dismiss();
  if (document.querySelector("#run-form")) {
    document.dispatchEvent(new CustomEvent("schedule-navigation"));
  } else {
    document.querySelector("h1").focus();
  }
};
new ResizeObserver(entries => {
  application.style.setProperty("--application-width", `${entries[0].contentRect.width}px`);
  const next = entries[0].contentRect.width < 900;
  if (narrow === next) return;
  const hadFocus = sidebar.contains(document.activeElement);
  narrow = next;
  drawerOpen = false;
  render();
  if (hadFocus && sidebar.hidden) menu.focus();
}).observe(application);
