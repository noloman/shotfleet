# 8. The website, the worker and the claims register

Back to the [index](../ARCHITECTURE.md). The site is `https://shotfleet.com`. It is a static site plus one small Cloudflare Worker, both in `site/`.

## 8.1 Layout

```
site/
  public/            everything served as static assets (wrangler [assets] directory)
    index.html       the sale page (home: pitch, one real run, price)  docs.html   the docs page (every command and key, tested)
    alternatives.html comparison table                   demo.html   "See it work": nine real clips plus a dated evidence list
    examples.html    real apps: the four runs and the store-screenshot gallery (moved off the home page, 2026-10-30)
    privacy.html, terms.html, whats-new.html             404.html, guides.html, guides/<slug>.html (two published guides)
    llms.txt, robots.txt, sitemap.xml, install.sh, _headers
    site.css, fonts/, img/, media/demo/ (mp4, poster webp, vtt captions)
    analytics.js     first-party, cookie-free counters       ga.js     Google Analytics 4, only after "Accept analytics"
    forms.js         email forms (waitlist and "delete my email")     flow.js, reveal.js, tabs.js, zoom.js   small page behaviours
    download/        NOT in git (.gitignore): release files are staged here only by packaging/publish.sh
  worker.js          the API: /api/signup, /api/forget, /api/hit, /api/contact
  worker.test.mjs    the worker's tests (Node, no framework)
  wrangler.toml      production: assets, KV, rate limiter, email, routes shotfleet.com and www
  wrangler.staging.toml   the throwaway rehearsal worker (no routes, no bindings)
  signups.sh         read signups, messages and visit counts; --purge-waitlist deletes the waitlist (asks for the word PURGE)
  draft/             pages not served (alternatives draft, og.html); site/tools/og.swift renders the link preview image
```

There is no build step and no framework: hand-written HTML and CSS, a few small scripts, `Content-Security-Policy: default-src 'self'`.
Pages share a head pattern (canonical, Open Graph, one `<h1>`, a nav and a footer) that `tests/test_docs.py` and `tests/test_site.py` enforce. Copy rules: plain, informal English (the
author's own voice, rewritten 0.1.4), **no em dashes** (a test fails on one in any site text file), no emoji, and a banned-phrase list (`BANNED`, `tests/test_site.py:25`: "works with every",
"guarantee", "ai-powered", ...).

## 8.2 The worker (`site/worker.js`)

Static files are served by Cloudflare **before** the worker runs (`run_worker_first = ["/api/*"]` in `wrangler.toml`); only `/api/*` reaches it. Everything else 404s with `404.html`.

| Route | What it does |
|---|---|
| `POST /api/hit` `{src, ev}` | Counts one page event (`view`, `runs`, `pricing`, `cta`). KV key `hit:<day>|<source>|<language>|<event>` holds a total; nothing about the visitor. Writes are **batched per isolate** (`HIT_BATCH`, default 20, or 25 s after the first one with `waitUntil`) because KV's free tier allows 1,000 writes a day and signups share them. Runs before the rate limit so page views never use up a visitor's budget. |
| `POST /api/signup` `{email, stack?, ref, website}` | Waitlist. KV `email:<address>` with date, platform, stack, country (`cf.country`), browser language, and the referrer/utm tags. A second call with `stack` adds the answer. The honeypot field `website` makes bots get a fake success. |
| `POST /api/forget` `{email}` | Deletes the address and the contact messages left with it as the reply address (found through KV metadata). Same answer whether or not it existed. |
| `POST /api/contact` `{message, email?, website}` | A message for the owner: KV `msg:<time>-<id>`. 2 to 2,000 characters. |

Common guards: only `POST`, body size at most 4,096 bytes (header and text), an email regex, per-IP rate limit (`LIMITER` binding, 5 a minute, the IP is the limit key and is never stored),
JSON-only responses with `cache-control: no-store`. New signups also send the owner an email (the number, country, source and stack, **never the address**) through Cloudflare's `send_email`
binding to the `ALERT_TO` secret, off unless both exist, and a failed send is only logged. The sale is live and **the site has no signup form any more**; the route still exists (and the
`forms.js` markup contract), which is a mismatch noted in the appendix.

Constraints you will hit: KV `list` returns one page (first 1,000 keys; `ponytail:` comments say so); KV can lag a new key by up to a minute; the 1,000 writes a day budget is shared between hits and signups.

`site/worker.test.mjs` runs the real `worker.js` against an in-memory KV (`Map`) and a stub limiter, printing `ok <name>` or `FAIL <name>`; `tools/check-claims.sh` runs it and counts the lines.

## 8.3 Headers and CSP (`site/public/_headers`)

Applied to `/*`: `Content-Security-Policy` (`default-src 'self'`; images and connect only to `self` plus Google Analytics hosts; scripts `self` plus `www.googletagmanager.com`; styles `self`;
`base-uri 'none'`; `form-action 'self'`; `frame-ancestors 'none'`), `X-Content-Type-Options: nosniff`, `Cross-Origin-Opener-Policy: same-origin`, a strict referrer policy,
`Permissions-Policy` denying camera, microphone, geolocation, `Strict-Transport-Security: max-age=15552000` (six months, no subdomains, no preload; `tests/test_site.py` `Hsts`). Because styles are
`'self'` there is no inline `<style>` and no inline handler anywhere: the page parsers in the tests fail on `onclick=` attributes. Cache rules: `/fonts/*` immutable for a year, `/img/*` and `/media/*` a week,
`/download/:file` and `/install.sh` `no-cache`, `/download/:version/*` immutable. **Any new third-party host, inline script or style needs a CSP change and the matching test and privacy-page
change**; the default is "no".

Analytics: `ga.js` loads Google Analytics 4 only after an explicit "Accept analytics" (equal-weight Accept and Decline buttons, choice kept in `localStorage` under `shotfleet-analytics`, not a
cookie; consent defaults denied, signals and ad personalization off, cookies `_ga` and `_ga_<id>` for up to 13 months). The Measurement ID lives only in `ga.js`; if it is set to the
placeholder `G-XXXXXXXXXX` the file does nothing at all. `analytics.js` is separate: a first-party, cookie-free counter that sends only an event name and the traffic source.

## 8.4 The claims register and why every public sentence is tested

**The problem it solves.** A single-person product with no sales needs its words to be right: a wrong promise ("works with any app") costs a refund or trust. The 2026-10-02 audit
(`research/claims-audit.md`) found 12 false and 38 only partly tested claims across 104. The fix was to make every promise a row in `tests/claims.json` and make the test suite fail when
the words and the proof drift apart.

**Schema** (`tests/test_claims.py`, 250 rows on main at `285e099`, ids `C001` to `C257`): `id` (`C\d{3}`), `claim` (what is promised, in plain words), `where` (files), `where_text`
(the **exact quoted words** as they appear in those files), `status`, `proof` (what shows it true), `layer` (`unit`, `site`, `fixture`, `device`, `legal`), `assertion` (what a test or
run must show), `fix`. Fixed and removed rows add `fixed_by` (`code`, `wording`, `removed`), `fixed`, and `test` for a code fix.

**Statuses:** `proven` (a named test covers the whole claim), `evidence` (a dated real run, no automated test), `partial` (tested in part, the gap is named), `fixed` (was wrong, now fixed and says
how), `removed` (the sentence was taken out), `unverifiable` (opinion, third-party fact), `policy` (the owner's decision), `untested`. `false` is not allowed to exist
(`test_no_claim_is_still_false`). Counts on main: 98 proven, 95 evidence, 22 fixed, 23 partial, 3 removed, 2 policy, 2 unverifiable, 2 untested.

**What the tests enforce** (`tests/test_claims.py`):

- Every `where` file exists and every `where_text` quote is **still in the file** (except index.html while the sale page is live: its waitlist copy is dropped on purpose). Change a promise's words and this test names the row to update.
- A `removed` claim's words must not come back.
- A `proven` claim must name a test (`Class.test_name` in `proof` or `test`) and that test must exist in `tests/test_*.py`.
- Fixed and removed rows must say how and why.
- Status counts add up.

The layers that prove claims:

| Layer | Modules | Proves |
|---|---|---|
| unit | `tests/test_claims_unit.py`, `tests/test_cli_claims.py`, `tests/test_shotfleet.py` | what the program prints and accepts; free tier reaches both platform runs; hook variables; exit codes |
| site | `tests/test_site.py`, `tests/test_site_audit.py`, `tests/test_claims_site.py`, `tests/test_docs.py`, `site/worker.test.mjs`, `tests/browser_site.cjs` | structure, links, one price everywhere, privacy page lists what the worker stores, worker behaviour, form and counter behaviour in Chromium (stubbed API; skipped when Playwright is missing), wrangler config, SEO and accessibility metadata |
| fixture | `tools/fixture-e2e.sh` (device, opt-in) | the end-to-end promises on real simulators and emulators |
| device, legal | research notes, owner actions | what only a device, the live site or a real payment can show |

Specific consistency tests worth knowing: one price on every page and in the README and the launch email (`PriceAgreement`); `14` days everywhere for the refund; "up to N languages" equals
`FREE_LANGUAGES`; the docs page's every `shotfleet ...` command parses with the real parser and its config table lists exactly the real keys; the privacy page lists every KV key the worker writes;
`docs.html` "Last checked against version X" equals `VERSION`; every release in `whats-new.html` has a dated CHANGELOG heading; local links resolve; no `<!--` comments in public pages except the parked
ones.

**Adding or changing a promise:** see [10-making-changes.md](10-making-changes.md#add-or-change-a-site-claim).

## 8.5 Flag files and parked text

Some public text must not appear until a real thing exists. The pattern: the text sits in a marker comment, a test requires it to stay parked, and a **flag file** releases it:

| Flag / marker | Meaning | Guard |
|---|---|---|
| `<!-- DOCKER-PENDING ... DOCKER-PENDING -->` blocks in `docs.html` and `llms.txt` | the Linux `check` image and GitHub Action are not published yet | `tests/test_site.py` `DockerPending`: while `site/DOCKER_PUBLISHED` is absent, no uncommented mention of `ghcr.io/noloman/shotfleet-check`; once the file exists, the markers must be gone. Release step: `packaging/README.md` step 9. |
| `site/BYOC_DEVICE_PROVEN` (present since 2026-10-07) | bring-your-own-capture has run end to end on a device | `ByocPending`: while absent, every line in the README and public pages that offers "your own XCUITest" tests must contain "its device test hasn't passed yet"; once the file exists, no line may say the device test hasn't passed. Created after `tools/fixture-byoc-e2e.sh` passed. |
| `<!-- RELEASE_DATE -->` in the top CHANGELOG heading and `whats-new.html` | release not dated yet | `publish.sh` refuses the placeholder in either; `test_site.py` `WhatsNew` requires the date to match once CHANGELOG has one |
| `<!-- WAITLIST -->` | the pre-launch page | gone since go-live (`test_claims.py` `LIVE` skips quote checks on index.html then) |
| `CLIP` marker lines in `demo.html` | a demo clip whose files are not added yet | steps are in a comment at the top of the page |

## 8.6 The guides generator (`tools/build-guides.py`)

Articles are drafted as `marketing/articles/NN-*.md`. Each ends with a "TO VERIFY BEFORE PUBLISHING" list; an item is ticked when its last marker is `TICKED` (not `PARTLY TICKED`). An article is **verified**
when no item is left unticked. `python3 tools/build-guides.py` writes drafts to `site/draft/guides/` (never served). `--publish` copies only verified articles into `site/public/guides/`, writes the
hub `site/public/guides.html` and adds them to `sitemap.xml`; `--publish-unverified` is the owner's override. The hub is `guides.html`, not `guides/index.html`, because Cloudflare answers `/guides`
with a redirect to `/guides/` when an index file exists (checked with `wrangler dev` on 2026-10-06). Two guides are published; the rest wait on their open items. `tests/test_docs.py` tests the generator,
`tests/test_claims_site.py` keeps unpublished slugs out of `public/` and out of the kit's links.

## 8.7 Changing the site safely

1. Edit in `site/public/`; never put a number, price, date or capability in text without a claim row and a proof.
2. `sh tools/check-claims.sh` (about a minute of tests; see [09-testing.md](09-testing.md)).
3. Do not deploy by hand. The site ships with a release or a docs refresh through `packaging/publish.sh` (see [07](07-packaging-and-release.md), "Why there is no site-only deploy").
4. Update `sitemap.xml` and `llms.txt` when adding a page (tests check each page is in the sitemap and `llms.txt` exactly once where required), and `whats-new.html` when a release adds user-visible behaviour (it mirrors the CHANGELOG).
