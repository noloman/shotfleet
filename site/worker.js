// Serves the landing page (static assets) and stores waitlist signups in KV.
// Read signups: npx wrangler kv key list --binding WAITLIST --remote
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/api/signup") return env.ASSETS.fetch(request);
    if (request.method !== "POST") return json({ error: "Use POST" }, 405);

    let body;
    try { body = await request.json(); } catch { return json({ error: "Send JSON" }, 400); }
    // bots fill the hidden "website" field; pretend success so they don't retry
    if (body.website) return json({ ok: true });
    const email = String(body.email || "").trim().toLowerCase();
    if (email.length > 254 || !EMAIL.test(email)) return json({ error: "That email address doesn't look right" }, 400);

    const key = `email:${email}`;
    if (!(await env.WAITLIST.get(key))) {
      await env.WAITLIST.put(key, JSON.stringify({
        at: new Date().toISOString(),
        platform: String(body.platform || "").slice(0, 20),
        country: request.cf?.country || null,
        referrer: (request.headers.get("referer") || "").slice(0, 200),
      }));
    }
    return json({ ok: true });
  },
};

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json" } });
