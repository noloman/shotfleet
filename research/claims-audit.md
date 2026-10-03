# Public claims audit (2026-10-02)

Scope: everything shotfleet promises in `site/public/{index,privacy,terms,404}.html`, `site/draft/alternatives.html` (draft, 404 live),
`README.md`, `LAUNCH.md`, `DISTRIBUTION.md`, `marketing/launch-posts-v2.md`, `marketing/launch-email.md` and the CLI's `--help`/errors.
Registry: `tests/claims.json` (104 entries, ids C001-C104, each with `where_text` phrases a script can grep; all 104 phrases were verified to exist
in the current files). Read-only audit: no simulator, emulator, Maestro, deploy or install. Run: 135 unit tests OK, `node site/worker.test.mjs` 13 checks OK.
Live site read with `curl` (headers only) and the public Polar docs once.

The site changed under me: redesign commits d6ed578, 935500e (Cairn tab now shows Cairn's own store screenshots, click-to-enlarge) and 7f27985
(anonymous visit counter, privacy page rewritten) landed during the audit. I audited the final text and re-simulated the launch transform on it.
Both the WAITLIST and the SALE text were audited: I applied `packaging/go-live.sh`'s two regexes in memory to `index.html`; no waitlist remnant is left
(C089). Re-run that after the redesign settles.

## Counts

| status | n | meaning |
|---|---|---|
| proven | 18 | an existing test covers the whole claim |
| partial | 38 | tested in part (the gap is named per entry) |
| evidence | 15 | a dated real run, no automated test |
| untested | 11 | plausible, nothing proves it |
| false | 12 | contradicted by code, a measurement or another document |
| unverifiable | 10 | opinion, commitment or third-party fact; reword or leave to a human |

Test layers needed for the 104: unit 46, site 21, fixture 12, device 10, legal 15.

## 1. FALSE claims (fix the words now; these are cheap)

| id | where | claim | evidence | corrected wording |
|---|---|---|---|---|
| C040 | index.html:198 | Remoti/Stressi/Cairn "are their real store screenshots ... the thing every listing has to get right" | `img/remoti_ja.jpg`, `remoti_hi.jpg` (viewed): Japanese/Hindi caption over an **English** UI. `research/real-apps.md`: `check` flagged 108 of 120 Remoti listing images as exactly this. The first, default tab shows the failure the product sells against. Stressi and Cairn are localized. | Drop the Remoti tab, or label it "Remoti before shotfleet check" and replace it with a captured set |
| C008 | index.html:139, README.md:12 | sample output `checked 72 screenshots: 0 problem(s)` | `shotfleet.py:1644` prints `checked N screenshots in M languages: P problem(s)` (reproduced) | `checked 72 screenshots in 18 languages: 0 problem(s)` |
| C035 | index.html:308,311 | Flutter and React Native "tested on sample projects" | no sample project exists (`examples/` has only CrossfitTracker); only translation **files** were read (`research/frameworks.md`, SourceFiles tests). README.md:231 is accurate | "tested on real translation files; not yet run on a real Flutter or React Native app" |
| C043 | launch-email.md:5, launch-posts-v2.md:44,113 | founder price "before anyone else" / "only for the first 100 people on the list" | `go-live.sh` publishes the Buy page with FOUNDER29 applied before the email goes out (LAUNCH.md 3-4); the 100 redemptions go to whoever buys first. index.html:316 says "first 100 people", LAUNCH.md "100 redemptions" | "The first 100 buyers pay $29." everywhere; send the email before deploying, or drop "before anyone else" |
| C049 | terms.html:26 | "the licence unlocks `run` and `export`" | `run` is free for 2 languages (shotfleet.py:2250; index.html:367) | "`check` is free, `run` is free for up to 2 languages; the licence unlocks every language and `export`" |
| C053 | terms.html:31 | "you can renew for another year of updates" | no renewal product (LAUNCH.md lists one product); STRATEGY.md:56 says "later" | "I plan to offer a renewal after the first year; it is not available yet" |
| C065 | README.md:202 | "`run`, `check` and `export` take `--json`" | `export --json` -> "unrecognized arguments" (ran it). README.md:78 is right | "`run` and `check` take `--json`" |
| C066 | README.md:91 | CI recipe runs `python3 shotfleet.py check` | buyers get the signed program, not the source | `curl ... install.sh \| sh`, then `shotfleet check fastlane/ ... --json` |
| C090 | DISTRIBUTION.md:23 | check/doctor/init free, run and export need a key | stale; run is free for 2 languages | add "run free up to 2 languages" |
| C091 | DISTRIBUTION.md:24 | `--version`/`doctor` mention a newer release (GitHub API) | only `doctor`, and it asks the site's `/download/VERSION` | fix the row |
| C092 | DISTRIBUTION.md:13,17,19 | universal Intel+arm binary, `brew install noloman/...` | same file, line 61: "Apple silicon only", no public repos; `install.sh:6` refuses x86_64 | arm64 only, curl install |
| C102 | launch-posts-v2.md:119 | "Do NOT claim ... Android tablets" | the page sells Android tablet sets; ROADMAP.md:27 verified it 2026-10-02 | delete the item (or the page claim) |

## 2. UNVERIFIABLE claims (reword or hand to a human)

| id | claim | what to do |
|---|---|---|
| C014 | "It was a two-line fix in my app." (index.html:149, posts) | link the commit or say "a small fix" |
| C019 | "Quickstart (about 10 minutes)" README.md:46 | time a cold install on a clean user; cold-test-2 listed unlisted prerequisites (Java, Debug simulator build, API 33 AVD) |
| C094 | fastlane "runs one language at a time" / "Parallel: No" (posts-v2, draft table) | fastlane snapshot has `concurrent_simulators` (from memory; re-check): "one language after another on each simulator" |
| C097 | "630 lines of one-off script" (draft) | nothing in repo supports it; delete the number |
| C038, C096 | fastlane is free; "I couldn't find any tool that verifies..." | fine; absence claim is hedged |
| C055, C056, C086 | Polar merchant of record, FOUNDER29 applied automatically, what Polar sends me | human check once the Polar review passes and the checkout link exists |
| C080 | "one email, never shared" | a commitment; keep |

Misleading but not false (status `partial`, worth fixing in the same pass):
- **Apple silicon only** is stated nowhere on the page, terms or privacy (README.md:49 shell comment, `install.sh:6`). An Intel Mac owner can pay and not install (C002).
- README.md:44 puts the unreachable-Next story under "Check screenshots made by any tool". It was `run` that got stuck; `check` cannot find that (C013).
- README.md:237 omits Java 17+ that the site and `doctor` require (C033); `SHOTFLEET_KEY` (the way to use "your CI") is documented nowhere public (C045).
- `privacy.html` "nothing else" about the Polar call omits the activation id, the program version in the User-Agent and `doctor`'s request to `/download/VERSION` (C085).
- Hooks: `SHOTFLEET_BUNDLE_ID` is not set for export hooks and `SHOTFLEET_LOCALES` is empty unless the run is restricted (README.md:186-188; C068).
- Price: amounts agree everywhere ($49 / $29 / first 100 / 14 days / 30 days offline / 3 Macs). Polar sells 49 EUR with 20 off, the page shows only dollars (C042).

## 3. Biggest test-coverage gaps, ranked by risk to a paying customer

1. **The licence has never met Polar.** `PolarLicence` mocks `polar_post` itself, so request shape, 403/404/422 handling and the 3-activation limit
   (server-side only) are unproven (C045). The client treats any HTTP 200 from `validate` as valid and ignores the body's `status`
   (shotfleet.py:2216), while Polar's docs put a `status` in the 200 body: a refunded or revoked key may keep working (C047; not confirmed either way).
   `POLAR_ORG_ID = ""` in the source until `go-live.sh` edits it. Failure mode: a buyer cannot activate, or a refund does not stop the product.
2. **Release and install.** `/download/VERSION` is 404 on the live site, so `install.sh` fails today (expected pre-launch, C057). Notarization is
   evidenced only by a 2026-10-01 note; the only binary in the checkout is "Unnotarized Developer ID" and `research/pricing-2026-10.md` says "never notarized" (C058).
   No test runs `install.sh`, the checksum refusal or the Intel refusal.
3. **No end-to-end test of the product.** The 18x4 timings, "no changes to your app", status bar, iOS accessibility-text capture, iPad/Android tablet export,
   permission-prompt taps are all one-off runs. `tools/fixture-app` (iPhone+iPad, en/de/ja/ar/tr) exists but nothing drives it; there is no Android fixture.
4. **`check` core claims are not asserted at the `cmd_check` level.** Wrong language is (ExternalOcr, StuckOcr). Copies and missing screens are
   not (my snippet produced them; C025), and copies are blind below 40 characters of text. The free tier, free `check` and the 2-language cap were never
   exercised with `sys.frozen` through `main()` for check/doctor/init (C032, C048).
5. **Privacy promises with no mechanism.** "I delete the list 30 days after the launch email" has no TTL, cron or script (C081); `forget` leaves contact
   messages containing the address (C082); contact form, size limits, 405/413/429 and the rate limiter are untested (C083, C084); Workers observability is on and
   whether it retains IPs is unchecked. The no-cookie/no-external-load claim is verified only by a manual curl today.
6. **Public showcase contradicts the product** (C040, above).
7. **Framework claims** rest on synthetic and downloaded files; react-intl is untested by name (C036).
8. **Doc drift.** Four internal docs disagree with the code (C090-C092, C102). A mechanical consistency check would have caught every item in section 1 except C040 and C043.

## 4. Proposed test-layer plan (what to automate first)

1. **Claims harness (an hour).** `tests/test_claims.py`: load `tests/claims.json`; for every entry assert each `where_text` still occurs in its file (catches wording
   drift from the redesign), every `proof` test name exists in `tests/test_shotfleet.py`, `fix` is present for `false`/`unverifiable`, ids are sequential. Fails when a
   `false` claim's text is still published, which forces the fix list in section 1 to be closed before launch.
2. **Site layer, static (half a day, no devices).** Price/terms numbers extracted from all public files must be one set; the go-live transform applied to
   `index.html` leaves no waitlist remnant and exactly one install block (C089); no cross-origin resource in any page and CSP `default-src 'self'` (C076); every image in
   `index.html` exists with its declared size and 7+11=18, 72=18x4 (C005); terminal sample vs the line `cmd_check` prints (C008); internal anchors (`#price`) resolve;
   `worker.test.mjs` gains contact, 405/413/429, stored-field set, forget-removes-messages (C077-C084).
3. **Unit gaps (one day).** `cmd_check` parametrised over wrong language, copies, missing, size (and a short-screen copy documenting the blind spot); `main()` with
   `sys.frozen` for check/doctor/init/run/export (free tier end to end); an HTTP-level fake Polar that records raw bodies and returns a revoked key; `--json` matrix over
   subcommands; `write_gallery` HTML; every README config block accepted by `load_config`; hook env table; `--version` makes no network call; doctor with nothing installed.
4. **Fixture layer (a day to build, minutes to run; needs simulators, schedule when the Mac is free).** `tools/fixture-app` through `init`, `run --locales de,ja,ar,tr`, `check`, `export`:
   2 screenshots per locale, German text from the accessibility tree, planted copy/missing/wrong-language detected, iPad 13" run, free-tier cap with a frozen-style build.
   Then a tiny Android fixture APK (per-app locales, tablet 1440x2560, `tenInchScreenshots`, a non-scrolling onboarding page as the regression for C013).
5. **Device and release gates (per release, manual or scripted).** Polar sandbox: activate x4 (4th refused), refund -> validate fails, `SHOTFLEET_KEY` in CI; `release.sh`
   then `spctl -a -vv -t exec` must say "Notarized Developer ID"; `install.sh` against the local tarball under a throwaway HOME; the corrected CI recipe on a macos-15 runner; one real
   Flutter and one real Expo app; ButterKit/AppScreens round trip; `shotfleet check` on each gallery tab's images.
6. **Human/legal checklist.** Polar account approved, checkout shows $29 and flips to $49 after 100, refund path after day 14, retention purge run, the "one email" promise.
