# GA4 shows no data for shotfleet.com: investigation, 2026-10-05

Done on 2026-10-05 between 12:03 and 12:30 UTC. Read-only: no GA4 setting, stream, filter, site file or deployment was changed. This is not legal advice.

## Verdict

1. Nothing is broken. A clean browser that accepted the banner sent a `page_view` to GA4 and it showed up in Realtime within about a minute (first_visit, page_view, session_start, 1 active user).
2. The empty property is mostly "no real traffic yet" plus the consent gate, and in your own Chrome a tracker blocker stops Google's scripts completely, so your own visits can never appear.
3. No code fix is needed. Nothing is proposed under `research/proposed-ga4-fix/` (it does not exist on purpose). The remaining items are yours (section 5).

## 1. What I checked and found

Each item is CONFIRMED (I saw it) or INFERENCE (my reading).

**Static**

1. CONFIRMED. `site/public/ga.js` has `const GA_ID = "G-6NY43DB3F4"` as its first statement and the ID appears nowhere else in the site. It is a valid ID (no typo, not the `G-XXXXXXXXXX` placeholder, passes the file's own guard regex).
2. CONFIRMED. The live site serves the same files as the repo: `/ga.js`, `/analytics.js` and `/` are byte-identical to `site/public/` (`cmp` and `diff`, 2026-10-05 12:03 UTC). `/ga.js` is served with `200`, `content-type: text/javascript`, `cache-control: public, max-age=0, must-revalidate`, `x-content-type-options: nosniff`. The worker is only run first for `/api/*` (`wrangler.toml` `run_worker_first`), so `/ga.js` is a plain static asset, not rewritten or blocked.
3. CONFIRMED. Loading is CSP-compatible: `<script src="/ga.js" defer>` (no inline script) on `/`, `/alternatives`, `/terms`, `/privacy`. `defer` means `document.body` exists when the banner is built. `/docs` and `/404` do not load ga.js and have no banner (INFERENCE: on purpose; `tests/test_consent.py` pins "ga.js and the footer link come together").
4. CONFIRMED. Live CSP equals the repo `_headers`: `script-src 'self' https://www.googletagmanager.com`, `connect-src` and `img-src` allow `https://*.google-analytics.com` (this covers `region1.google-analytics.com`, which is the host GA4 really used, see item 9). `tests/test_consent.py` pins these values.
5. CONFIRMED. Banner logic: it shows when `localStorage["shotfleet-analytics"]` is null and storage is usable. No geo, DNT or GPC condition. It is a fixed-position `div` with a `z-index`, no `display:none` anywhere except in print CSS. If storage is blocked it counts as declined and no banner appears. A visitor who declines is never measured, and nothing is requested from Google (basic consent mode).
6. CONFIRMED. GA4 stream settings match the repo (item 12). No hostname mismatch: stream URL `https://shotfleet.com`, the site canonical host is the bare domain (`www` is a second custom domain for the same site).

**Browser, real network**

7. CONFIRMED. In your signed-in Chrome (Chrome 154, via Claude in Chrome), test visit `https://shotfleet.com/?ga-test=20261005-1210` at 14:04 CEST (12:04 UTC): banner appeared; I pressed Accept analytics. `dataLayer` got `consent default`, `consent update`, `js`, `config G-6NY43DB3F4`; localStorage became `granted`. The request `GET https://www.googletagmanager.com/gtag/js?id=G-6NY43DB3F4` was listed with status 503 and no bytes (`responseStatus 0`, `transferSize 0`), no `g/collect` request was made, no CSP message in the console.
8. CONFIRMED. That is a client-side block, not the site and not Google. The same URL via `curl` returns 200 with the script. On `https://example.com` (no CSP) a `fetch` to `googletagmanager.com/gtag/js`, `google-analytics.com/analytics.js` and `googletagmanager.com/gtm.js` all failed, while `gstatic.com/generate_204` and `google.com/generate_204` worked. So your Chrome blocks Google's measurement hosts on every site. The same Chrome reports `navigator.doNotTrack = "1"` and `globalPrivacyControl = true`. INFERENCE: a privacy or ad-blocking extension (I did not open the extensions page, so I cannot name it).
9. CONFIRMED. Control test in a clean browser (the built-in browser pane, no extensions, no sign-ins) with `https://shotfleet.com/?ga-test=20261005-1225-clean` at 14:08:37 CEST (12:08:37 UTC): banner appeared, Accept pressed, `gtag/js` loaded, then a `page_view` was sent to `https://region1.google-analytics.com/g/collect` with `tid=G-6NY43DB3F4`, `gcs=G101` (ad storage denied, analytics storage granted), `gcd=13p3r3p2p7l1`, `npa=1` (no ad personalization), `dl` = the test URL, about 540 ms. Console empty: no CSP violation, no error. The request body status shows 0 only because it is cross-origin (browser hides it); item 10 proves Google accepted it.
10. CONFIRMED. GA4 Realtime in your Chrome (about a minute later): active users 1, events `first_visit`, `page_view`, `session_start`, page title "shotfleet · Localized store screenshots from one Maestro flow". The whole chain (banner, consent, CSP, Measurement ID, stream) works.

**GA4 side (read-only, signed in as the owner, property 557101981)**

11. CONFIRMED, before my test hit: Home said "No data received from your website yet", last 7 days all 0; Realtime 0 users; DebugView "No development devices have logged any debug events in the last 30 minutes".
12. CONFIRMED. Admin > Data streams: one web stream, name `shotfleet.com`, URL `https://shotfleet.com`, stream ID 15945857287, Measurement ID `G-6NY43DB3F4` (matches ga.js), Enhanced measurement ON (page views, scrolls, outbound clicks and more), banner "Data collection isn't active for your website" and in the list "No data received in past 48 hours" (that was before my test hit).
13. CONFIRMED. Data filters: one filter, "Internal Traffic", Exclude, state **Testing**. Not Active, so it excludes nothing (INFERENCE from Google's wording for the Testing state; also my clean test hit was counted). No Developer traffic filter is listed.
14. CONFIRMED. Data retention: event data 2 months, user data 14 months (reset on new activity). Retention does not hide recent data. Property details: reporting time zone Netherlands (GMT+02:00), currency USD.

**First-party counter (worker `/api/hit`, read with wrangler on the owner's existing login; only the `hit:` keys were read, no secrets, no signup emails)**

15. CONFIRMED. Page views ("view" events, counted whatever the visitor chooses about consent, no per-visitor data):

| Day (UTC) | views | notes |
|---|---|---|
| 2026-10-03 | 21 | includes one `deploy-check` source and 3 `xx` (no language, typical of scripts) |
| 2026-10-04 | 14 | 9 cta clicks, 1 `runs`, all source `direct` |
| 2026-10-05 (until about 12:25 UTC) | 9 | 8 `en`, 1 `nl`; 2 of the `en` are my two test visits |

Total 44 views in 3 days, every one with source `direct` (no referrer, no `utm_source`). INFERENCE: this is almost entirely you, test runs and deploy checks, not announcement traffic, which fits "not announced yet". The counter cannot tell a person from a script, so I cannot say how many real strangers there were (0 to a handful).

**Google documentation**

16. CONFIRMED. Standard reports: "can take 24-48 hours to process data"; Realtime shows the last 30 minutes as soon as people use the site (https://support.google.com/analytics/answer/9333790, fetched 2026-10-05; footer 2026, no page date). Consent mode: with advanced mode and `analytics_storage` denied, cookieless pings are sent and used for modeling; with basic mode (tags blocked until consent) nothing is sent before consent and there is no modeling (https://support.google.com/analytics/answer/9976101, fetched 2026-10-05, no page date). shotfleet is the basic kind: ga.js does not even load the Google script before Accept. CSP guide (https://developers.google.com/tag-platform/security/guides/csp, last updated 2026-09-18) lists `https://www.googletagmanager.com`, `https://*.google-analytics.com`, `https://*.google.com` and Google TLD hosts; `*.google-analytics.com` covers `region1`, while `analytics.google.com` would need `https://*.google.com`.

## 2. The test hits I generated

| Marker | When | Where it went |
|---|---|---|
| `?ga-test=20261005-1210` | 12:04 UTC, your Chrome, banner accepted | first-party counter only (1 view); blocked before reaching Google, so no GA4 hit |
| `?ga-test=20261005-1225-clean` | 12:08:37 UTC, clean browser, banner accepted | first-party counter (1 view) and **one real GA4 test user** (first_visit, page_view, session_start). It stays in GA4 reports (page location contains the marker). I did not delete it; user deletion is a GA4 admin action and one test user is harmless. |

I left no tabs open in Chrome. The extra empty "New Tab" in the Chrome group is the one the extension created at the start.

## 3. Causes, ranked

1. **Almost no real visitors yet (very likely).** Evidence: counter shows 44 views in 3 days, all `direct`, mostly consistent with tests; no launch announcement; GA4 first-ever data was my test. Against: none.
2. **Consent gate (very likely, adds to 1).** Only visitors who press Accept are measured, and basic mode sends nothing for the others. For an EU/NL audience with an equal-weight banner I expect most visitors to decline or ignore it; the real acceptance rate is unknown and not instrumented (INFERENCE). Even once traffic arrives, GA4 will show a fraction of the first-party counter. That is by design and matches the privacy page.
3. **Tracker blocker in your own browser (confirmed for you).** Items 7 and 8. Your own visits never reach Google, so "I visited and GA4 shows nothing" will not work from that browser. Developers (the target audience) block trackers more often than average, which will also cut real visitors (INFERENCE; I have no number).
4. **Normal reporting delay (partly applies).** Realtime works; standard reports (Reports > Acquisition, Engagement) may stay empty for the first 24 to 48 hours after the first hit, so my test hit may show in Realtime today but in standard reports only tomorrow. Not the cause of the earlier empty state.
5. **Internal-traffic filter (ruled out).** State is Testing, not Active; and nobody's data was excluded before there was any.
6. **Measurement ID, stream or hostname mismatch (ruled out).** IDs match everywhere (item 12), stream URL is the site.
7. **CSP or script not loading (ruled out for normal browsers).** Clean browser: no violation, collect accepted by Google. Small latent risk only: `analytics.google.com` is not in the CSP (GA4 falls back to it in some setups, for example when Google signals or ads features are on, which they are not). Not worth changing now.
8. **Banner never rendering, wrong content type, stale cache (ruled out).** Banner showed in both browsers; live files are identical to the repo.
9. **Privacy settings of the visitor (DNT, GPC) (not a cause).** The site ignores both; they do not stop the banner.

## 4. Recommended fixes, smallest first

1. **Nothing in the code or in GA4 needs to change.** Do not edit `ga.js`, `_headers` or the stream.
2. To prove it to yourself: open `https://shotfleet.com/?ga-test=owner` in a private window with extensions disabled (or on your phone on mobile data), press Accept, and watch GA4 Realtime. Expect 1 user within a minute.
3. Judge traffic with the first-party counter (`site/signups.sh --visits`), not GA4, until the launch is announced. GA4 will always show only the consenting, unblocked slice.
4. Optional, your decision (see section 5): the Internal Traffic filter, key events, a less strict consent setup.
5. Optional hardening, not needed: add `https://*.google.com` to `connect-src` and `img-src` to follow Google's CSP guide. It widens the policy for no observed benefit and requires changing the pinned values in `tests/test_consent.py`, so I do not recommend it now. No patch file is provided.

## 5. What you must do yourself

- **Test from a clean browser** (section 4, step 2). Also decide if you want to allow `googletagmanager.com` and `google-analytics.com` in your own blocker on the sites you test; otherwise ignore your own visits in GA4.
- **GA4 internal-traffic filter** (STATUS.md line 80, item 6): it is defined but in Testing; move it to Active only after you add your IP rule in Admin > Data streams > Configure tag settings > Define internal traffic (needs your decision and your home or office IPs). Note: the data filter permanently excludes matching data once Active. With a blocker on, it matters little for you; skip it until you see your own visits in GA4.
- **Key events**: mark `cta_click`, `pricing_view`, `signup` as key events once they have appeared in the events list (they need at least one real hit first).
- **Consent approach (a decision, not a bug).** Today: basic mode, clear and defensible, but only accepters are measured. An "advanced" mode (load the Google tag before consent with everything denied, so cookieless pings arrive) would raise the numbers, but it sends data to Google before consent, contradicts the privacy page sentence "nothing is loaded from Google" and needs your own legal view before changing the privacy page and ga.js. I do not recommend it for an EU/NL audience that the page promised consent-gated analytics. The first-party cookie-free counter is the right tool for total visits.
- **Privacy page wording**: no change needed for the current setup. If you ever change the consent mode, change the page first.

## 6. How to verify after any change

1. Private window, no extensions, open `/?ga-test=<time>`, Accept, wait 1 minute.
2. GA4 > Reports > Realtime: expect 1 active user and `page_view`. DevTools Network: `gtag/js` 200 and a `g/collect` request with `tid=G-6NY43DB3F4` and `gcs=G101`.
3. Decline path: with a fresh private window press Decline: no request to Google may appear.
4. Next day: Reports > Acquisition > Traffic acquisition shows the test visit (24 to 48 hours).
5. `python3 -m unittest tests.test_docs` and `tests.test_consent` in the repo if any file is edited.

## 7. What I could not verify

- Which extension blocks Google in your Chrome (I did not open extension settings).
- The real acceptance rate of the banner (not measured) and how many of the 44 views are real strangers.
- Whether standard (non-Realtime) reports will show my test hit; that needs 24 to 48 hours.
- Behaviour in Safari and Firefox (tracking protection blocks Google scripts differently there).
- Whether the Internal Traffic filter in Testing state is tagged but not excluded: taken from Google's general wording (the fetched page did not spell it out); my clean test hit appeared in Realtime, which is consistent but from an IP the filter might not cover anyway.
- The `region1.google-analytics.com` host is chosen by Google (EU region); if Google ever routes to a host outside the CSP, the console would show a violation; none seen today.
