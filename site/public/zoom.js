// Click a gallery screenshot to see it at full size. Native <dialog>: Esc closes, focus returns to the thumbnail.
(function () {
  var dlg = document.getElementById("zoom");
  if (!dlg || !dlg.showModal) return;
  var img = dlg.querySelector("img");
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("button.zoom");
    if (b) {
      img.src = b.getAttribute("data-full");
      img.alt = b.querySelector("img").alt;
      dlg.showModal();
    } else if (e.target === dlg || e.target === img) dlg.close();
  });
  dlg.addEventListener("close", function () { img.removeAttribute("src"); });
})();
