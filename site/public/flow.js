// "Your flow says Next": pick a language and see what the English flow line becomes. The four boxes in index.html stay the source;
// without JavaScript they simply show, side by side. With it they are replaced by one line in, one line out.
(function () {
  var dl = document.querySelector(".flowrow");
  if (!dl) return;
  var cells = [].slice.call(dl.querySelectorAll(".cell"));
  if (cells.length < 2) return;

  function el(tag, cls) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    return n;
  }
  // copy a node's children (text and <em>) into target
  function fill(target, source, skip) {
    target.replaceChildren.apply(target, [].filter.call(source.childNodes, function (n) { return n !== skip; }).map(function (n) { return n.cloneNode(true); }));
    return target;
  }

  var live = el("div", "flowlive");
  var inRow = el("div", "flowline");
  inRow.appendChild(fill(el("span", "flowtag"), cells[0].querySelector("dt")));
  inRow.appendChild(fill(el("code", "flowcode"), cells[0].querySelector("dd")));

  var pick = el("div", "flowpick");
  pick.setAttribute("role", "group");
  pick.setAttribute("aria-label", "Language to rewrite the flow for");
  var lead = el("span", "flowarrow");
  lead.textContent = "shotfleet rewrites it for";
  pick.appendChild(lead);

  var outRow = el("div", "flowline out");
  var outTag = el("span", "flowtag"), outCode = el("code", "flowcode"), outNote = el("p", "flownote");
  outCode.setAttribute("aria-live", "polite");
  outRow.appendChild(outTag); outRow.appendChild(outCode); outRow.appendChild(outNote);

  var buttons = cells.slice(1).map(function (cell, i) {
    var b = fill(el("button", "flowbtn"), cell.querySelector("dt"));
    b.type = "button";
    b.addEventListener("click", function () { show(i, true); });
    pick.appendChild(b);
    return b;
  });

  function show(i, animate) {
    var cell = cells[i + 1], dd = cell.querySelector("dd"), warn = dd.querySelector(".warn");
    buttons.forEach(function (b, j) { b.setAttribute("aria-pressed", j === i ? "true" : "false"); });
    fill(outTag, cell.querySelector("dt"));
    fill(outCode, dd, warn);
    outNote.textContent = warn ? warn.textContent : "";
    outNote.hidden = !warn;
    if (animate) { outRow.classList.remove("swap"); void outRow.offsetWidth; outRow.classList.add("swap"); }
  }

  live.appendChild(inRow); live.appendChild(pick); live.appendChild(outRow);
  dl.parentNode.insertBefore(live, dl);
  dl.hidden = true;
  show(0, false);
})();
