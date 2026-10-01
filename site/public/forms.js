// Signup (index.html) and delete-my-email (privacy.html) forms. Same markup contract:
// form#<id> with input[type=email], button[type=submit], p.form-error, and a sibling #<id>-done shown on success.
(function () {
  // which launch post brought the visitor: external referrer and utm_* tags, sent with the signup
  var ref = [];
  try {
    if (document.referrer && new URL(document.referrer).host !== location.host) ref.push(new URL(document.referrer).host);
    new URLSearchParams(location.search).forEach(function (v, k) { if (k.indexOf("utm_") === 0) ref.push(k + "=" + v); });
  } catch (e) {}

  function wire(id, endpoint, extra, validate) {
    var form = document.getElementById(id);
    if (!form) return;
    var email = form.querySelector("input[type=email]"), btn = form.querySelector("button[type=submit]");
    var err = form.querySelector(".form-error"), done = document.getElementById(id + "-done"), label = btn.textContent;
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      err.hidden = true;
      var problem = (validate || defaultValidate)(form, email);
      if (problem) { err.textContent = problem.text; err.hidden = false; problem.field.focus(); return; }
      btn.disabled = true; btn.textContent = "Sending…";
      try {
        var r = await fetch(endpoint, { method: "POST", headers: { "content-type": "application/json" },
          body: JSON.stringify(Object.assign({ email: email.value }, extra(form))) });
        var d = await r.json().catch(function () { return {}; });
        if (!r.ok) throw new Error(d.error || "Couldn't save that. Try again in a minute.");
        form.hidden = true; done.hidden = false; done.focus();
      } catch (x) {
        err.textContent = (x && x.message && x.message !== "Failed to fetch") ? x.message : "Couldn't reach the server. Check your connection and try again.";
        err.hidden = false; btn.disabled = false; btn.textContent = label;
      }
    });
  }

  function defaultValidate(form, email) {
    if (!email.value || !email.checkValidity()) {
      email.setAttribute("aria-invalid", "true");
      return { field: email, text: "That doesn't look like an email address. Check it and try again." };
    }
    email.removeAttribute("aria-invalid");
  }

  wire("signup", "/api/signup", function (f) {
    return { platform: f.querySelector("select").value, website: f.querySelector(".trap").value, ref: ref.join(" ") };
  });
  wire("forget", "/api/forget", function () { return {}; });
  wire("contact", "/api/contact", function (f) {
    return { message: f.querySelector("textarea").value, website: f.querySelector(".trap").value };
  }, function (form, email) {
    var msg = form.querySelector("textarea");
    if (msg.value.trim().length < 2) { msg.setAttribute("aria-invalid", "true"); return { field: msg, text: "Write a message first." }; }
    msg.removeAttribute("aria-invalid");
    if (email.value && !email.checkValidity()) {
      email.setAttribute("aria-invalid", "true");
      return { field: email, text: "That reply address doesn't look right. Fix it or leave it empty." };
    }
    email.removeAttribute("aria-invalid");
  });
})();
