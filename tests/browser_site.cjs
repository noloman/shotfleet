// Drives the real pages (site/public) in Chromium with every /api/* call stubbed, to check what forms.js and analytics.js send and show.
// Run by tests/test_claims_site.py (class BrowserBehaviour). Prints "ok   <name>" or "FAIL <name>" per check; exit 0 when all pass,
// 77 when Playwright or Chromium is not installed (the Python test then skips).
const http = require("http"), fs = require("fs"), path = require("path");
let chromium;
try { ({ chromium } = require("playwright")); } catch {
  try { ({ chromium } = require(path.join(process.env.NODE_ROOT || "/opt/node22/lib/node_modules", "playwright"))); } catch { console.log("SKIP no playwright"); process.exit(77); }
}
const PUB = path.join(__dirname, "../site/public");
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".woff2": "font/woff2", ".txt": "text/plain" };
let failed = false;
const check = (name, cond) => { process.stdout.write((cond ? "ok   " : "FAIL ") + name + "\n"); if (!cond) failed = true; };

// a static server shaped like the Cloudflare assets setup: /terms is terms.html, / is index.html, unknown paths get 404.html
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  let file = path.join(PUB, p === "/" ? "index.html" : p);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = fs.existsSync(file + ".html") ? file + ".html" : null;
  if (!file || !file.startsWith(PUB)) { res.writeHead(404, { "content-type": "text/html" }); return res.end(fs.readFileSync(path.join(PUB, "404.html"))); }
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" }); res.end(fs.readFileSync(file));
});

(async () => {
  await new Promise(r => server.listen(0, "127.0.0.1", r));
  const base = "http://127.0.0.1:" + server.address().port;
  let browser;
  try { browser = await chromium.launch(); }
  catch { try { browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" }); } catch { console.log("SKIP no chromium"); server.close(); process.exit(77); } }

  // one page with the API stubbed: `reply(url, body)` returns {status, json|text} or "abort"; every API call is recorded
  async function open(url, { reply = () => ({ status: 200, json: { ok: true } }), referer, storage } = {}) {
    const ctx = await browser.newContext({ viewport: { width: 1200, height: 900 } });
    const page = await ctx.newPage();
    const calls = [], hits = [], external = [];
    if (storage) await page.addInitScript(s => { try { localStorage.setItem("shotfleet-analytics", s); } catch {} }, storage);
    await page.route("**/*", route => {
      const u = new URL(route.request().url());
      if (u.origin !== base) { external.push(u.href); return route.abort(); }
      if (u.pathname.startsWith("/api/")) {
        let body = null; try { body = JSON.parse(route.request().postData()); } catch {}
        (u.pathname === "/api/hit" ? hits : calls).push({ path: u.pathname, body, method: route.request().method(), type: route.request().headers()["content-type"] });
        if (u.pathname === "/api/hit") return route.fulfill({ status: 200, contentType: "application/json", body: '{"ok":true}' });
        const r = reply(u.pathname, body, calls.length);
        if (r === "abort") return route.abort();
        return route.fulfill({ status: r.status, contentType: "application/json", body: r.json ? JSON.stringify(r.json) : (r.text ?? "") });
      }
      return route.continue();
    });
    await page.goto(base + url, referer ? { referer, waitUntil: "load" } : { waitUntil: "load" });
    return { page, ctx, calls, hits, external };
  }
  const visible = (page, sel) => page.locator(sel).first().isVisible();
  const text = (page, sel) => page.locator(sel).first().innerText();
  const waived = new Set();

  const waitlist = fs.readFileSync(path.join(PUB, "index.html"), "utf8").includes("<!-- WAITLIST -->");
  if (waitlist) {
    // ---- signup (C088): success, then the optional question
    {
      const { page, ctx, calls } = await open("/?utm_source=hn&utm_medium=post", { referer: "https://news.ycombinator.com/item?id=1" });
      await page.fill("#signup-top-email", "Reader@Example.com");
      await page.click("#signup-top button[type=submit]");
      await page.waitForSelector("#signup-top-done", { state: "visible" });
      check("signup success shows You're on the list and hides the form", (await text(page, "#signup-top-done")).includes("You’re on the list.") && !(await visible(page, "#signup-top")));
      check("signup sends one POST to /api/signup as JSON", calls.length === 1 && calls[0].path === "/api/signup" && calls[0].method === "POST" && /json/.test(calls[0].type));
      check("signup sends exactly email, the honeypot as website, and the referrer with utm tags", Object.keys(calls[0].body).sort().join() === "email,ref,website" && calls[0].body.email === "Reader@Example.com" && calls[0].body.website === "" && calls[0].body.ref === "news.ycombinator.com utm_source=hn utm_medium=post");
      check("the optional question is shown after the signup, not before", (await text(page, "#signup-top-done")).includes("One more thing, if you like: what do you build with?") && calls.length === 1);
      await page.selectOption("#stack-top-stack", "flutter");
      await page.click("#stack-top button");
      await page.waitForSelector("#signup-top-done .followup-thanks", { state: "visible" });
      check("answering sends the same address with the stack and shows thanks", calls.length === 2 && calls[1].body.email === "Reader@Example.com" && calls[1].body.stack === "flutter" && calls[1].body.website === "" && (await text(page, ".followup-thanks")).includes("Thanks"));
      await ctx.close();
    }
    {
      const { page, ctx, calls } = await open("/");
      await page.fill("#signup-email", "skip@example.com"); await page.click("#signup button[type=submit]");
      await page.waitForSelector("#signup-done", { state: "visible" });
      await page.selectOption("#stack-card-stack", ""); await page.click("#stack-card button");
      check("skipping the question costs nothing: the signup was already sent and an empty answer sends nothing more", calls.length === 1 && !(await page.locator("#signup-done .followup-thanks").isVisible()));
      await ctx.close();
    }
    // ---- errors
    for (const [name, rep, want] of [
      ["429 shows the server's own wait message", () => ({ status: 429, json: { error: "Too many attempts. Wait a minute and try again." } }), "Too many attempts. Wait a minute and try again."],
      ["500 without a message shows the generic retry text", () => ({ status: 500, text: "boom" }), "Couldn't save that. Try again in a minute."],
      ["400 shows the server's own text", () => ({ status: 400, json: { error: "That doesn't look like an email address. Check it and try again." } }), "That doesn't look like an email address. Check it and try again."],
      ["a network failure shows the connection text", () => "abort", "Couldn't reach the server. Check your connection and try again."],
    ]) {
      const { page, ctx, calls } = await open("/", { reply: rep });
      await page.fill("#signup-top-email", "a@example.com"); await page.click("#signup-top button[type=submit]");
      await page.waitForSelector("#signup-top-error", { state: "visible" });
      check("signup: " + name, (await text(page, "#signup-top-error")) === want && (await visible(page, "#signup-top")) && !(await visible(page, "#signup-top-done")) && await page.locator("#signup-top button[type=submit]").isEnabled());
      await ctx.close();
    }
    {
      const { page, ctx, calls } = await open("/");
      await page.click("#signup-top button[type=submit]");
      const empty = await text(page, "#signup-top-error");
      await page.fill("#signup-top-email", "not an address"); await page.click("#signup-top button[type=submit]");
      const bad = await text(page, "#signup-top-error");
      check("an empty or malformed address is stopped in the page with a message and no request", empty === "Enter your email address." && bad.startsWith("That doesn't look like an email address") && calls.length === 0);
      await ctx.close();
    }
    {
      const { page, ctx, calls } = await open("/");
      await page.evaluate(() => { document.querySelector("#signup .trap").value = "http://spam.example"; });
      await page.fill("#signup-email", "bot@example.com"); await page.click("#signup button[type=submit]");
      await page.waitForSelector("#signup-done", { state: "visible" });
      check("the hidden honeypot field is sent as website, so the server can drop it", calls[0].body.website === "http://spam.example");
      check("the honeypot is out of sight and out of the tab order", !(await page.locator("#signup .trap").isVisible()) || (await page.locator("#signup .trap").evaluate(e => e.tabIndex)) === -1);
      await ctx.close();
    }
    // ---- analytics.js (C077): what the counter sends, with analytics declined
    for (const choice of ["declined", "undecided"]) {
      const storage = choice === "declined" ? "denied" : null;  // second run: no choice made at all (banner showing)
      const { page, ctx, hits: calls, external } = await open("/?utm_source=Reddit", { storage, referer: "https://www.reddit.com/r/x" });
      await page.waitForTimeout(200);
      check(`the counter sends a view with analytics ${choice}`, calls.length >= 1 && calls[0].path === "/api/hit" && calls[0].body.ev === "view");
      await page.evaluate(() => document.getElementById("run").scrollIntoView()); await page.waitForTimeout(150);
      await page.evaluate(() => document.getElementById("price").scrollIntoView()); await page.waitForTimeout(150);
      await page.evaluate(() => document.querySelector("a.btn, button.btn").click());
      await page.waitForTimeout(150);
      const evs = calls.map(c => c.body.ev);
      check(`views, reaching the run and pricing sections and a button click are each sent (${choice})`, ["view", "runs", "pricing", "cta"].every(e => evs.includes(e)));
      check(`every counter call sends only src and ev, to /api/hit (${choice})`, calls.length >= 4 && calls.every(c => c.path === "/api/hit" && Object.keys(c.body).sort().join() === "ev,src"));
      check(`the source is the utm_source (${choice})`, calls.every(c => c.body.src === "Reddit"));
      check(`the counter sets no cookie and loads nothing from another server (${choice})`, (await ctx.cookies()).length === 0 && external.length === 0);
      await ctx.close();
    }
    {
      const { page, ctx, hits: calls } = await open("/", { referer: "https://lobste.rs/s/abc" });
      await page.waitForTimeout(200);
      check("without utm_source the source is the referring site's host", calls[0].body.src === "lobste.rs");
      await ctx.close();
    }
  }

  // ---- privacy.html: delete my email and the contact form
  {
    const { page, ctx, calls } = await open("/privacy");
    await page.fill("#forget-email", "Gone@Example.com"); await page.click("#forget button[type=submit]");
    await page.waitForSelector("#forget-done", { state: "visible" });
    check("delete-my-email sends only the address to /api/forget and says Done", calls.length === 1 && calls[0].path === "/api/forget" && Object.keys(calls[0].body).join() === "email" && (await text(page, "#forget-done")).includes("Done."));
    await page.fill("#contact-message", "x"); await page.click("#contact button[type=submit]");
    check("a one-character message is stopped in the page", (await text(page, "#contact .form-error")) === "Write a message first." && calls.length === 1);
    await page.fill("#contact-message", "Hello there"); await page.fill("#contact-email", "nope"); await page.click("#contact button[type=submit]");
    check("a malformed reply address is stopped in the page", (await text(page, "#contact .form-error")).startsWith("That reply address doesn't look right") && calls.length === 1);
    await page.fill("#contact-email", "Reply@Example.com"); await page.click("#contact button[type=submit]");
    await page.waitForSelector("#contact-done", { state: "visible" });
    check("the contact form sends message, reply address and honeypot to /api/contact and says Sent", calls.length === 2 && calls[1].path === "/api/contact" && Object.keys(calls[1].body).sort().join() === "email,message,website" && calls[1].body.message === "Hello there" && calls[1].body.website === "" && (await text(page, "#contact-done")).includes("Sent."));
    await ctx.close();
  }

  await browser.close(); server.close();
  process.exit(failed ? 1 : 0);
})().catch(e => { console.log("FAIL crashed: " + (e && e.stack || e)); process.exit(1); });
