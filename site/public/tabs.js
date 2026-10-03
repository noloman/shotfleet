// The app switcher in the gallery: ARIA tabs with arrow keys. Without JavaScript every strip simply shows, one below the other.
(function () {
  var list = document.querySelector('[role="tablist"]');
  if (!list) return;
  var tabs = [].slice.call(list.querySelectorAll('[role="tab"]'));
  function show(tab, focus) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    });
    if (focus) tab.focus();
  }
  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { show(t); });
    t.addEventListener("keydown", function (e) {
      var to = e.key === "ArrowRight" ? (i + 1) % tabs.length : e.key === "ArrowLeft" ? (i + tabs.length - 1) % tabs.length :
               e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 : -1;
      if (to >= 0) { e.preventDefault(); show(tabs[to], true); }
    });
  });
  show(tabs[0]);
})();
