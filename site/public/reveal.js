// Scroll choreography: sections ease in once as they enter the viewport (heavy fade, short travel, one curve).
// Loaded before first paint; it only adds a class, and nothing is hidden without JavaScript or with reduced motion.
(function () {
  var root = document.documentElement;
  if (!("IntersectionObserver" in window) || (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
  root.classList.add("js-reveal");
  document.addEventListener("DOMContentLoaded", function () {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });
    [].forEach.call(document.querySelectorAll(".reveal"), function (el) { io.observe(el); });
  });
})();
