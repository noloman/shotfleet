// API for the landing page; static files in public/ are served before this runs.
//   POST /api/signup  {email, platform, ref, website}  -> join the waitlist (KV key "email:<address>")
//   POST /api/forget  {email}                           -> remove an address from the waitlist
//   POST /api/contact {message, email?, website}        -> a message for Manu (KV key "msg:<time>-<id>")
// Read signups: ./signups.sh
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/;
const MAX_BODY = 4096;
const ROUTES = new Set(["/api/signup", "/api/forget", "/api/contact"]);

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (!ROUTES.has(pathname)) return json({ error: "Not found" }, 404);
    if (request.method !== "POST") return json({ error: "Use POST" }, 405);

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
        JSON.stringify({ message, email: reply || null, country: request.cf?.country || null }));
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
      console.log(JSON.stringify({ event: "forget" }));
      return json({ ok: true }); // same answer whether or not it was on the list
    }

    // bots fill the hidden "website" field; answer like a success so they don't adapt
    if (body.website) return json({ ok: true });
    if (!(await env.WAITLIST.get(key))) {
      await env.WAITLIST.put(key, JSON.stringify({
        at: new Date().toISOString(),
        platform: ["ios", "android", "both"].includes(body.platform) ? body.platform : "unknown",
        country: request.cf?.country || null,
        ref: String(body.ref || "").slice(0, 300),   // external referrer + utm_* tags, sent by the page
      }));
      console.log(JSON.stringify({ event: "signup", country: request.cf?.country || null }));
    }
    return json({ ok: true });
  },
};

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } });
