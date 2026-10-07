import w from "./worker.js";
const kv = new Map(), meta = new Map();
const env = { WAITLIST: { get: async k => kv.get(k) ?? null, put: async (k, v, o) => (kv.set(k, v), meta.set(k, o?.metadata)), delete: async k => kv.delete(k),
                          list: async ({ prefix }) => ({ keys: [...kv.keys()].filter(k => k.startsWith(prefix)).map(name => ({ name, metadata: meta.get(name) })) }) },
              LIMITER: { limit: async () => ({ success: true }) }, HIT_BATCH: 3, FLUSH_MS: 5 };
const ctx = { waitUntil: p => (pending.push(p)) }; const pending = [];
const call = async (path, body, method = "POST") => (await w.fetch(new Request("https://x" + path, { method, body: method === "POST" ? JSON.stringify(body) : undefined, headers: { "content-length": "100" } }), env, ctx)).status;
let ok = true; const check = (name, cond) => { process.stdout.write((cond ? "ok   " : "FAIL ") + name + "\n"); ok &&= cond; };
// the old waitlist: nothing writes email: records any more, but /api/forget still removes one
kv.set("email:a@example.com", JSON.stringify({ at: "2026-10-01T00:00:00Z" }));
check("forget removes an old waitlist record", (await call("/api/forget", { email: "a@example.com" }), !kv.has("email:a@example.com")));
await call("/api/hit", { src: "Reddit.com" });
await call("/api/hit", { src: "reddit.com" });
await call("/api/hit", { src: "<script>" });
await call("/api/hit", { src: "x", ev: "pricing" }); await call("/api/hit", { src: "x", ev: "<bad>" }); await call("/api/hit", { src: "x", ev: "cta" });
await Promise.all(pending);
const hits = [...kv].filter(([k]) => k.startsWith("hit:"));
check("visits are counted per day, source and language", hits.some(([k, v]) => /^hit:\d{4}-\d\d-\d\d\|reddit.com\|xx\|view$/.test(k) && v === "2"));
check("known events are kept, unknown ones count as a view", hits.some(([k]) => k.endsWith("|x|xx|pricing")) && hits.some(([k]) => k.endsWith("|x|xx|cta")) && hits.every(([k]) => /\|(view|runs|pricing|cta)$/.test(k)));
check("source is sanitised", hits.every(([k]) => !/[<>]/.test(k)));
check("a visit stores nothing about the visitor", hits.every(([k, v]) => /^\d+$/.test(v)));
// a quiet site: one lone visit, far below HIT_BATCH, must still be written by the timer
pending.length = 0; await w.fetch(new Request("https://x/api/hit", { method: "POST", body: JSON.stringify({ src: "lonely" }) }), { ...env, HIT_BATCH: 99 }, ctx); await Promise.all(pending);
check("a single visit below the batch size is still stored", [...kv].some(([k, v]) => k.includes("|lonely|") && v === "1"));

// contact form, forget, and the error paths
const msgs = () => [...kv].filter(([k]) => k.startsWith("msg:")).map(([, v]) => JSON.parse(v));
check("contact 200", await call("/api/contact", { message: "Hello there", email: "Reply@Example.com" }) === 200);
check("message stored with a lower-cased reply address", msgs().some(m => m.message === "Hello there" && m.email === "reply@example.com"));
check("contact without a reply address is fine", await call("/api/contact", { message: "No address" }) === 200 && msgs().some(m => m.email === null));
check("contact too short 400", await call("/api/contact", { message: " x " }) === 400);
check("contact too long 400", await call("/api/contact", { message: "x".repeat(2001) }) === 400);
check("contact bad reply address 400", await call("/api/contact", { message: "Hello", email: "nope" }) === 400);
const before = msgs().length;
check("contact honeypot is not stored", await call("/api/contact", { message: "spam spam", website: "http://x" }) === 200 && msgs().length === before);
await call("/api/contact", { message: "Another one", email: "other@example.com" });
kv.set("email:reply@example.com", "{}");
await call("/api/forget", { email: "reply@example.com" });
check("forget removes the address from the list", !kv.has("email:reply@example.com"));
check("forget removes the messages left with that reply address", !msgs().some(m => m.email === "reply@example.com"));
check("forget leaves other people's messages", msgs().some(m => m.email === "other@example.com") && msgs().some(m => m.email === null));
check("GET on an api route 405", await call("/api/contact", null, "GET") === 405);
check("there is no signup route: /api/signup is a 404 and writes nothing", await call("/api/signup", { email: "s@example.com" }) === 404 && !kv.has("email:s@example.com"));
check("unknown path 404", await call("/api/nope", {}) === 404);
const limit = env.LIMITER.limit; env.LIMITER.limit = async () => ({ success: false });
check("rate limited 429", await call("/api/contact", { message: "limited" }) === 429 && !msgs().some(m => m.message === "limited"));
check("rate limit does not block visit counting", await call("/api/hit", { src: "x" }) === 200);
env.LIMITER.limit = limit;
// what is stored, and what is not (claims C077 to C084): one place that sends an IP address and a user agent with every request
const startKeys = new Set(kv.keys());
const IP = "203.0.113.77", UA = "ShotfleetTest/9.9 (secret-agent)";
const send = (path, body, extra = {}, e = env, cf = { country: "NL" }) => {
  const req = new Request("https://x" + path, { method: "POST", body: JSON.stringify(body), headers: { "content-length": "100", "cf-connecting-ip": IP, "user-agent": UA, "accept-language": "fr-FR,fr;q=0.9", ...extra } });
  Object.defineProperty(req, "cf", { value: cf });
  return w.fetch(req, e, ctx);
};
const logged = []; const realLog = console.log; console.log = (...a) => logged.push(a.join(" "));
const keysNow = () => new Set(kv.keys());
const newKeys = snap => [...kv.keys()].filter(k => !snap.has(k));

pending.length = 0; let snap = keysNow();
await send("/api/hit", { src: "News.YCombinator.com", ev: "pricing" }, {}, { ...env, HIT_BATCH: 1 }); await Promise.all(pending);
let fresh = newKeys(snap);
check("one visit writes exactly one key, a day/source/language/event total", fresh.length === 1 && /^hit:\d{4}-\d\d-\d\d\|news\.ycombinator\.com\|fr\|pricing$/.test(fresh[0]) && kv.get(fresh[0]) === "1");
check("a visit key and value hold neither the IP address nor the user agent", fresh.every(k => !(k + kv.get(k)).includes(IP) && !(k + kv.get(k)).includes("ShotfleetTest")));

snap = keysNow();
await send("/api/contact", { message: "Hi, a question", email: "Ask@Example.com", website: "" });
fresh = newKeys(snap); const mrec = JSON.parse(kv.get(fresh[0] ?? "") ?? "{}");
check("a contact message is one msg: record holding exactly message, email and country", fresh.length === 1 && fresh[0].startsWith("msg:") && Object.keys(mrec).sort().join() === "country,email,message" && mrec.country === "NL" && mrec.email === "ask@example.com");
check("a contact message never holds the IP address or the user agent", !fresh[0].includes(IP) && !kv.get(fresh[0]).includes(IP) && !kv.get(fresh[0]).includes("ShotfleetTest") && !JSON.stringify(meta.get(fresh[0])).includes(IP));
check("the only kinds of key ever written are msg: and hit:", newKeys(startKeys).every(k => /^(msg|hit):/.test(k)));

await send("/api/forget", { email: "who@example.com" });
const logText = logged.join("\n");
check("the server's own log lines name the event and country, never the IP, user agent or an address", logged.length > 0 && !logText.includes(IP) && !logText.includes("ShotfleetTest") && !/@/.test(logText) && logged.every(l => /^\{"event":"[a-z_]+"(,"(country|why)":[^,]*)?\}$/.test(l)));
console.log = realLog;

// forget: the same answer whether or not the address was on the list
const answer = async email => { const r = await send("/api/forget", { email }); return r.status + " " + await r.text(); };
kv.set("email:there@example.com", "{}");
const yes = await answer("there@example.com"), no = await answer("never-was@example.com");
check("forget answers identically whether or not the address was on the list", yes === no && yes.startsWith("200 "));
check("forget with an address that is not an address is a 400 and deletes nothing", (await send("/api/forget", { email: "nope" })).status === 400);

// contact: the remaining paths
check("a message of exactly 2,000 characters is accepted", (await send("/api/contact", { message: "m".repeat(2000) })).status === 200);
check("a message of 1 character after trimming is refused", (await send("/api/contact", { message: "  a  " })).status === 400);
check("a body over 4,096 bytes is refused with 413", (await send("/api/contact", { message: "x" }, { "content-length": "5000" })).status === 413 && (await send("/api/forget", { email: "big@example.com", pad: "x".repeat(5000) })).status === 413);
check("a body that is not JSON is a 400", (await w.fetch(new Request("https://x/api/contact", { method: "POST", body: "not json", headers: { "content-length": "8" } }), env, ctx)).status === 400);

// the rate limiter is keyed by the client IP and a refusal stops every write, on every route
const keyed = []; const realLimit = env.LIMITER.limit; env.LIMITER.limit = async o => (keyed.push(o.key), { success: false });
kv.set("email:there@example.com", "{}"); snap = keysNow(); const refused = [];
for (const [path, body] of [["/api/contact", { message: "should not be stored" }], ["/api/forget", { email: "there@example.com" }]]) refused.push((await send(path, body)).status);
check("rate limited contact and forget are both 429", refused.join() === "429,429");
check("a rate limited request writes nothing", newKeys(snap).length === 0 && kv.has("email:there@example.com"));
check("the limiter is asked about the client IP address, once per request", keyed.length === 2 && keyed.every(k => k === IP));
const hitStatus = (await send("/api/hit", { src: "z" }, {}, { ...env, HIT_BATCH: 1 })).status; await Promise.all(pending);
check("page views are not rate limited, so they never reach the limiter", hitStatus === 200 && keyed.length === 2);
env.LIMITER.limit = realLimit;
process.exit(ok ? 0 : 1);
