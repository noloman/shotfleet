// Google Analytics 4, loaded only after an explicit "Accept analytics". Until then nothing is requested from Google and no cookie is set.
// The Measurement ID lives here and nowhere else (GA4 > Admin > Data streams). If it is ever set back to the placeholder G-XXXXXXXXXX, this file does nothing at all:
// no banner, no script from Google. The choice is kept in localStorage; if storage is blocked it counts as declined and no banner is forced.
// The first-party, cookie-free counter in analytics.js is separate and unchanged.
const GA_ID = "G-6NY43DB3F4";

(function () {
  if (!/^G-(?!X+$)[A-Z0-9]{6,12}$/.test(GA_ID)) return;

  var KEY = "shotfleet-analytics", started = false, on = false, bar = null, opener = null;

  function gtag() { window.dataLayer.push(arguments); }
  function event(name, params) {
    if (on) gtag("event", name, params || {});
  }

  // The only place that talks to Google. Called after Accept, or on a later visit when "granted" is stored.
  function start() {
    if (started) { on = true; gtag("consent", "update", { analytics_storage: "granted" }); return; }
    started = on = true;
    window.dataLayer = window.dataLayer || [];
    gtag("consent", "default", { ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied", analytics_storage: "denied" });
    gtag("consent", "update", { analytics_storage: "granted" });
    gtag("js", new Date());
    gtag("config", GA_ID, { allow_google_signals: false, allow_ad_personalization_signals: false, cookie_flags: "SameSite=Lax;Secure", cookie_expires: 34128000 });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA_ID);
    document.head.appendChild(s);
    funnel();
  }

  // Declined or withdrawn: stop sending and remove the _ga cookies Google set (also after "clear localStorage only").
  function stop() {
    if (started) { on = false; gtag("consent", "update", { analytics_storage: "denied" }); }
    var host = location.hostname, root = host.split(".").slice(-2).join(".");
    document.cookie.split(";").forEach(function (c) {
      var name = c.split("=")[0].trim();
      if (/^_ga(_|$)/.test(name)) ["", ";domain=" + host, ";domain=." + root].forEach(function (d) { document.cookie = name + "=;path=/;max-age=0" + d; });
    });
  }

  // The same moments analytics.js counts first-party, plus signup (forms.js dispatches shotfleet:signup on success).
  function funnel() {
    if ("IntersectionObserver" in window) {
      [["free", "pricing_view"], ["run", "runs_view"]].forEach(function (p) {
        var el = document.getElementById(p[0]);
        if (!el) return;
        var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { event(p[1]); io.disconnect(); } }, { threshold: 0.25 });
        io.observe(el);
      });
    }
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a.btn, button.btn");
      if (a && !a.closest("#forget, #contact")) event("cta_click", { cta_text: (a.textContent || "").trim().slice(0, 40) });
    });
    document.addEventListener("shotfleet:signup", function () { event("signup"); });
  }

  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (k) { n.appendChild(typeof k === "string" ? document.createTextNode(k) : k); });
    return n;
  }

  function choose(value) {
    try { localStorage.setItem(KEY, value); } catch (e) {}
    if (value === "granted") start(); else stop();
    bar.remove(); bar = null;
    if (opener) { opener.focus(); opener = null; }
  }

  // Two buttons built by the same function: same class, same size, no default, no Escape, closes only by choosing.
  function ask(fromLink) {
    if (bar) { bar.querySelector("button").focus(); return; }
    function button(label) { return el("button", { type: "button", "class": "consent-btn" }, [label]); }
    var yes = button("Accept analytics"), no = button("Decline");
    yes.addEventListener("click", function () { choose("granted"); });
    no.addEventListener("click", function () { choose("denied"); });
    bar = el("div", { id: "consent", "class": "consent", role: "region", "aria-label": "Analytics choice" }, [
      el("p", {}, ["May I count visits with Google Analytics? If you accept, Google sets two cookies in your browser and receives data about your visit. If you decline, nothing is loaded from Google and no cookie is set."]),
      el("div", { "class": "consent-actions" }, [yes, no, el("a", { href: "/privacy#analytics" }, ["What this means"])])
    ]);
    document.body.insertBefore(bar, document.body.firstChild);
    if (fromLink) { opener = document.activeElement; yes.focus(); }
  }

  var saved = null, usable = true;
  try { saved = localStorage.getItem(KEY); } catch (e) { usable = false; }
  if (saved === "granted") start();
  else if (saved === null && usable) ask(false);

  var link = document.getElementById("analytics-settings");
  if (link) link.addEventListener("click", function (e) { e.preventDefault(); ask(true); });
})();
