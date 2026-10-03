# Sellable audit, 2026-10-02

Evidence behind STATUS.md, gate by gate. Method: read the repo at commit `eeb5cff` (branch `claude/integrate-on-main`), run the tests, probe the live site with `curl`, inspect the local build with `spctl` and `codesign`. Read only: no build, deploy, push, simulator, emulator, browser or purchase. Rule used: "done" needs evidence I saw; a claim that only a document makes, or that only a fake API tested, is "partial" or lower.

Other agents were editing while I worked (Gumroad migration, content-control research). At the end of the run `git status` showed uncommitted edits to `packaging/go-live.sh`, `shotfleet.py`, `tests/test_golive.py`, `tests/test_shotfleet.py`, `tests/test_site.py`, `tools/golive/smoke.sh`, plus untracked `tools/golive/storefront.sh` and `research/content-control.md`. Anything those touch is marked "in flux".

## Commands and results

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests` (clean tree, HEAD eeb5cff) | `Ran 306 tests in 26.9s`, `OK` |
| same, later, with the Gumroad edits in the tree | `Ran 295 tests`, `FAILED (failures=3, errors=3)`: in flux, not a product regression at HEAD. Re-run after the migration lands |
| `node site/worker.test.mjs` | 28 `ok`, 0 `FAIL` (signup, follow-up, honeypot, forget, rate limit, visit counting, 405/404/429) |
| `tests/claims.json` counted with python | 118 claims: partial 47, proven 28, evidence 19, fixed 14, unverifiable 6, untested 2, removed 2. By layer: unit 51, site 27, legal 15, device 13, fixture 12 |
| `df -h /System/Volumes/Data` | 926 GiB, 847 used, 33 GiB free, 97% (`/` shows 29%, which is only the sealed system volume) |
| `curl` on https://shotfleet.com | `/` 200 (29.6 KB), `/install.sh` 200, `/alternatives` 200, `/privacy` 200, `/terms` 200, `/llms.txt` 200, `/robots.txt` 200, `/sitemap.xml` 200, `/og.jpg` 200, `/analytics.js` 200; `/download/VERSION` 404, `/download/shotfleet-macos-arm64.tar.gz` 404, `/download/` 404, `/docs` 404, `/ga.js` 404 |
| redirects | `http://shotfleet.com/` 301 to https; `https://www.shotfleet.com/` 301 to the apex (one plain GET timed out once at 15 s, the retry with `-I` gave 301: treat as flaky edge, recheck) |
| headers on `/` | HTTP/2, Cloudflare, CSP `default-src 'self'; ... script-src 'self'; connect-src 'self'; frame-ancestors 'none'`, nosniff, referrer-policy, permissions-policy. No Google host allowed in the live CSP, so GA4 cannot load live yet |
| `robots.txt` live | `Allow: /`, `Disallow: /api/`, sitemap line |
| `sitemap.xml` live | 4 URLs: `/`, `/alternatives`, `/terms`, `/privacy` (no `/docs`) |
| live page vs `site/public/index.html` | differ; `alternatives`, `terms`, `privacy` also differ; `install.sh` identical. Live page: 10 "waitlist" mentions, 0 buy links, 0 Polar, 0 Gumroad. Repo is ahead by the commits since the last deploy (docs page, GA4, hero price, terms, privacy) |
| `spctl -a -vv -t exec dist/shotfleet` | `rejected, source=Unnotarized Developer ID`, origin `Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)`, hardened runtime flag set. `dist/` is git-ignored, built 10:27 today as a one-file build (older than the folder build in `build.sh`): not the release |
| `security find-identity -v -p codesigning` | the Developer ID Application identity is present |
| `maestro --version` | 2.0.10 (`~/.maestro/bin`); `shotfleet` not on the PATH; `~/Library/Application Support/shotfleet` empty (no installed copy) |
| `xcrun simctl list runtimes` (tail) | iOS 27.0 present (the list was cut; which iOS version the 2026-10-01 runs used is not recorded in the files I read) |
| `du` | Xcode DerivedData 2.1 GB, `~/Library/Android` 18 GB; 10 AVDs (Pixel 9a, Pixel Tablet, Pixel 7 Pro, ...) |
| `git log -40` | 100 commits, all in the last 7 days; last 40 are all from 2026-10-02 (08:xx to 15:16): simpler config, Polar licence, Tesseract fallback, redesign, claims audit, domain move, analytics, go-live rehearsal, agent skills, `[inputs]`, `init` discovery, site review, hello@ forwarding, Polar product, docs page, GA4 |

Not run, on purpose: `xcrun notarytool history` (network), `wrangler whoami`, `go-live.sh --dry-run` (needs a checkout link and is being edited), `tools/golive/smoke.sh` (the sale is not live), any device run.

## Gate by gate

**1-3 Provider, product, checkout (blocked / in flux).** Repo facts: `shotfleet.py` has `POLAR_ORG_ID = ""` and `GUMROAD_PRODUCT_ID = ""` ("set by packaging/go-live.sh"); `go-live.sh` already accepts `[<Gumroad product URL> <Gumroad product ID>]` (from ff5cd09, now being edited again). LAUNCH.md and DISTRIBUTION.md still describe Polar as the provider, with an organization id, product, `FOUNDER29` and two buy links created 2026-10-02: all of that is obsolete now that Polar is dropped, but it is the only "payments" evidence in the repo. I found no Gumroad product, link or approval anywhere in the files, so the state is blocked on Manu. Commit 0740e23 removed an unverified tax claim about Gumroad from the terms.

**4 Tax / KvK (not started).** LAUNCH.md says to ask before submitting for review and that a merchant of record only handles sales VAT. No answer is recorded. Roadmap R7 (one person, personal liability, tax status) stands. This gate does not depend on the provider: income from sales needs an answer either way.

**5 Licence (not started).** Code paths exist for Polar, Gumroad and Lemon Squeezy keys (`is_polar_key`, `gumroad_verify`, `polar_post`; free tier `FREE_LANGUAGES = 2`, `LOCALE_CAP`). Tests: classes `Licence` (offline grace, weekly re-check, line 878), `GumroadLicence` (refunded and unknown keys refused, line 944), `PolarLicence` (activate/validate/deactivate, bad key, free tier versus export, lines 1312-1328). All use fake APIs. The only real-API contact on record is Lemon Squeezy rejecting an unknown key. Cold test 2 finding 25 says the free-tier promise "could not be exercised" because the gate was off. The gate also depends on a build where `frozen` is true, because the licence is only enforced in released builds (`shotfleet.py:2475`). So nothing here proves a buyer can pay and unlock.

**6 Release build (partial).** What is true: signing identity present; `build.sh` builds a folder, re-signs every Mach-O deepest first, signs with hardened runtime and entitlements, submits to `notarytool` and fails unless `status: Accepted`; `release.sh` runs the claims gate first, copies the tarball, writes the `.sha256` and `VERSION`, deploys. DISTRIBUTION.md records Apple accepting 0.1.0 and a quarantined copy running without a prompt (2026-10-01): a document, not re-run today. What is missing: nothing is published (`site/public/download` absent; live 404s), so `install.sh` (checksum check, installs into Application Support, links onto the PATH, refuses Intel) has never run against a real download; `doctor` reads `/download/VERSION` (`shotfleet.py:1831`) and will say nothing until it exists; there is no staple step (a tarball of a bare folder cannot carry a ticket, so the first launch relies on Gatekeeper's online check: not tested offline). The Homebrew formula is kept but unused.

**7 Cold install (not started).** `research/cold-test-2.md` (25 findings) used the repo's own dev Mac, `env -i`, gate off, a stub Maestro and no devices. Many of its findings were fixed afterwards (unknown config keys refused, Java check, `sysctl` path, review grid, `doctor` exit code, `init` discovery), but no re-test exists. The README "about 10 minutes" is claim C019, unverifiable; the roadmap's own N4 needs outsiders.

**8 Maestro version (not started).** README line 261: "Maestro 2.x and Java 17+"; `shotfleet.py:1875`: "needs Maestro 2.x". Roadmap R1/N3: 2.6.0 changed parallel iOS handling and logs; 2.11.0 was published 2026-09-29; all real runs used 2.0.10, the version installed here. Nothing pins, prints or warns.

**9 Fixture e2e (not started).** `tools/fixture-app/` holds `App.swift`, `Resources`, `build.sh`, README (commit 01fa67d). No test or script runs it; claims.json entries with layer `fixture` (12) are 8 partial and 4 evidence. C001's assertion asks for an Android APK that does not exist.

**10 Real app runs (partial).** Recorded: CrossfitTracker iOS 18/18 in 8m54s, Android 18/18 in 15m24s, 0 problems, exported to fastlane (PLAN.md, 2026-10-01); tablets and iPad on Remoti, Kuokka, CrossfitTracker (ROADMAP.md 2026-10-02); `check` on 252 + 126 real images in about 25 s; MCP `check` 72 screenshots in 29 s. Limits: one primary app, Maestro 2.0.10; the code was changed substantially after (config rewrite bdac95c, retry 483ae6c, `[inputs]` 9a4fb1f, `init` 5044800) with only unit tests. Flutter/React Native/MAUI/Unity: translation files read, no app run (roadmap "Only coded"; README says so honestly).

**11 Claims register (partial).** 118 rows (the claims-audit of the morning had 104 and 12 false; all 12 are now fixed or removed and `test_no_claim_is_still_false` enforces it). Counting strictly only `proven` and `fixed` as green gives 42 of 116 live claims; 74 remain. The six `unverifiable` are legal/third-party statements (C038, C055, C056, C080, C086, C096): C055, C056 and C086 name Polar and must be reworded with the migration.

**12 Website (partial / in flux).** Live checks above. Repo-ahead items: `/docs`, GA4 banner, 4-link sitemap vs repo sitemap, hero price text. The deploy goes through `go-live.sh`, which also flips the waitlist to a buy page; deploying the site alone would be off-plan and was not done. `tests/test_site.py` guards links, alt text, banned phrases and the go-live transform (offline). Comparison page `/alternatives` is live and has a verified-facts basis (6ff199b).

**13 Support (done).** d1ec2a9 states forwarding was verified; privacy page names Cloudflare Email Routing. I did not send mail. One person answers it.

**14 Measurement (partial).** First-party counter (daily visits by source and language, events) is coded and covered by `worker.test.mjs`; I did not read live counts (needs KV or the Cloudflare dashboard). GA4: `G-6NY43DB3F4` in `ga.js` behind a consent banner; `test_consent.py` exists; live `/ga.js` 404 and the CSP has no Google hosts, so nothing is collecting yet. `research/ga-setup.md` sections 3-6 are Google-UI steps that only Manu can confirm.

**15 Marketing (partial).** `marketing/kit` has 9 files, 3 article drafts and an ideas file, `launch-email.md`, `done-for-you.md`. Article 1 and 2 list TO VERIFY items; some need the live installer (article 1 item 2) and article 2 says every snippet is unrun. `tools/build-guides.py` writes only drafts and refuses unverified articles. `demo-video.md` is a script; no video exists. "Manu posts" is written into the kit README and launch-day checklist.

**16 Dev Mac (partial).** 33 GiB free is healthy against the earlier 0.9 GB but is 97% used; Android SDK/AVDs alone are 18 GB. A Flutter validation run (about 1.5 GB) and two emulator rounds fit, a full benchmark may not.

## Where I disagree with research/roadmap-2026-10.md

1. It names Polar throughout (N1, N2, risks R2, kill criteria). Polar is dropped; N1 and N2 now mean Gumroad, and the Polar review is not on the critical path. The 14-day review buffer behind "G0 on or after 2026-10-16" no longer applies; the new timing depends on Gumroad's approval, which nothing in the repo shows.
2. It lists N9 (domain, counters) as open. The domain is live with the binary, installer and docs moved (e752a52), so that half is done. The download counter I could not find; I call N9 mostly done, not fully.
3. N10 "go-live rehearsed" looks complete on paper (c69b4b1) but the rehearsal and smoke test only ran against fakes, and both are being rewritten for Gumroad: partial, in flux.
4. N6 (review grid) and N8 (framework hints) are shipped by their commits (e752a52, 2a3b850) and unit-tested; the roadmap still lists them as next. I count them done, with a unit test as the only proof.
5. It sets the test count at 135; it is 306 plus 28 worker checks now. Good news for the guardrails, but the roadmap's own rule is that unit tests do not prove device behaviour, so this does not move gates 5-10.
6. Its "Proven by real runs" table is from before today's code changes. I do not treat those runs as covering the current build.
7. Its G0 asks for "S recorded" (waitlist signups). Nothing in the repo shows a signup number; I could not read the KV, so I left it as "last known 0".
8. Where it says the licence "was tested against a fake API", I add that the Gumroad path (the new one) additionally rests on a fake built from Gumroad's source, and that Gumroad refund and use-count semantics are therefore unverified end to end.

## Re-verify after the Gumroad migration lands

- `python3 -m unittest discover -s tests` and `node site/worker.test.mjs` green again; claims register rows C055, C056, C086, C049 and the terms/privacy text.
- `go-live.sh --dry-run` clean, with the real Gumroad link and product id.
- Live `/download/VERSION` 200 and `tools/golive/smoke.sh` clean after the real go-live.
