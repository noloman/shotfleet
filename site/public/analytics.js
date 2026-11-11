// First-party, cookie-free funnel counts. Each call sends only an event name and the traffic source
// (utm_source or the referring site); the server adds the day and the browser language and keeps totals, nothing per visitor.
// Events: view, pricing (the free section scrolled into view), cta (a button or link to the signup area clicked), runs (the real run section seen).
(function () {
  var src = "";
  try {
    var q = new URLSearchParams(location.search), host = document.referrer && new URL(document.referrer).host;
    src = q.get("utm_source") || (host && host !== location.host ? host : "");
  } catch (e) {}
  function send(ev) {
    try { fetch("/api/hit", { method: "POST", keepalive: true, headers: { "content-type": "application/json" }, body: JSON.stringify({ src: src, ev: ev }) }); } catch (e) {}
  }
  send("view");
  if ("IntersectionObserver" in window) {
    [["free", "pricing"], ["run", "runs"]].forEach(function (p) {
      var el = document.getElementById(p[0]);
      if (!el) return;
      var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { send(p[1]); io.disconnect(); } }, { threshold: 0.25 });
      io.observe(el);
    });
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a.btn, button.btn");
    if (a) send("cta");
  });
})();
