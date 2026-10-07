// API for the landing page; static files in public/ are served before this runs.
//   POST /api/forget  {email}                           -> remove an address from the old waitlist (KV key "email:<address>", written before the sale opened; nothing writes it now), and the contact messages left with it as the reply address
//   POST /api/hit    {src, ev}                          -> count one page event (view, runs, pricing, cta): KV key "hit:<day>|<source>|<language>|<event>" holds a total, nothing about the visitor
//   POST /api/contact {message, email?, website}        -> a message for Manu (KV key "msg:<time>-<id>", the reply address also in its metadata so forget can find it)
// There is no signup route: the site has no signup form. Read what is stored with ./signups.sh.
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/;
const MAX_BODY = 4096;
const ROUTES = new Set(["/api/forget", "/api/contact", "/api/hit"]);

const EVENTS = new Set(["view", "runs", "pricing", "cta"]);
const pending = new Map();  // visit counts waiting to be written

export default {
  async fetch(request, env, ctx) {
    const { pathname } = new URL(request.url);
    if (!ROUTES.has(pathname)) return json({ error: "Not found" }, 404);
    if (request.method !== "POST") return json({ error: "Use POST" }, 405);

    if (pathname === "/api/hit") {  // before the rate limit so page views never use up a visitor's rate-limit budget
      let b = {}; try { b = JSON.parse((await request.text()).slice(0, 200)); } catch {}
      const slug = (s, n) => String(s || "").toLowerCase().replace(/[^a-z0-9.-]/g, "").slice(0, n);
      const src = slug(b.src, 40) || "direct", lang = slug((request.headers.get("accept-language") || "").split(/[-,;]/)[0], 3) || "xx";
      const ev = EVENTS.has(b.ev) ? b.ev : "view";
      const key = `hit:${new Date().toISOString().slice(0, 10)}|${src}|${lang}|${ev}`;
      pending.set(key, (pending.get(key) || 0) + 1);
      // KV's free tier allows 1,000 writes a day and messages share them, so counts are batched per isolate: written when
      // HIT_BATCH visits are waiting, or 25 s after the first one (waitUntil keeps the isolate alive that long), so a quiet site still records every visit.
      const flush = () => {
        const batch = [...pending]; pending.clear();
        return Promise.all(batch.map(async ([k, n]) => env.WAITLIST.put(k, String(Number(await env.WAITLIST.get(k) || 0) + n))));
      };
      if (pending.size === 1 && pending.get(key) === 1) ctx.waitUntil(new Promise(r => setTimeout(r, Number(env.FLUSH_MS ?? 25000))  /* under the 30 s waitUntil allowance */).then(() => pending.size && flush()));
      if ([...pending.values()].reduce((a, n) => a + n, 0) >= Number(env.HIT_BATCH || 20)) ctx.waitUntil(flush());
      return json({ ok: true });
    }

    const ip = request.headers.get("cf-connecting-ip") || "unknown";
    const { success } = await env.LIMITER.limit({ key: ip });
    if (!success) return json({ error: "Too many attempts. Wait a minute and try again." }, 429);

    const length = Number(request.headers.get("content-length") || 0);
    if (length > MAX_BODY) return json({ error: "Request too large" }, 413);
    const text = await request.text();
    if (text.length > MAX_BODY) return json({ error: "Request too large" }, 413);
    let body;
    try { body = JSON.parse(text); } catch { return json({ error: "Send JSON" }, 400); }

    if (pathname === "/api/contact") {
      if (body.website) return json({ ok: true });
      const message = String(body.message || "").trim();
      if (message.length < 2) return json({ error: "Write a message first." }, 400);
      if (message.length > 2000) return json({ error: "That message is too long. Keep it under 2,000 characters." }, 400);
      const reply = String(body.email || "").trim().toLowerCase();
      if (reply && (reply.length > 254 || !EMAIL.test(reply))) {
        return json({ error: "That reply address doesn't look right. Fix it or leave it empty." }, 400);
      }
      await env.WAITLIST.put(`msg:${new Date().toISOString()}-${crypto.randomUUID().slice(0, 8)}`,
        JSON.stringify({ message, email: reply || null, country: request.cf?.country || null }), { metadata: { email: reply || null } });
      console.log(JSON.stringify({ event: "contact" }));
      return json({ ok: true });
    }

    const email = String(body.email || "").trim().toLowerCase();
    if (email.length > 254 || !EMAIL.test(email)) {
      return json({ error: "That doesn't look like an email address. Check it and try again." }, 400);
    }
    const key = `email:${email}`;

    if (pathname === "/api/forget") {
      await env.WAITLIST.delete(key);
      // ponytail: first 1,000 messages only (one KV list page); add the cursor loop if the inbox ever grows that big
      const { keys } = await env.WAITLIST.list({ prefix: "msg:" });
      await Promise.all(keys.filter(k => k.metadata?.email === email).map(k => env.WAITLIST.delete(k.name)));
      console.log(JSON.stringify({ event: "forget" }));
      return json({ ok: true }); // same answer whether or not it was on the list
    }
  },
};

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } });
