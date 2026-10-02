# shotfleet roadmap, 2026-10-02

Plan for the first sale and the 60 days after it. ROADMAP.md stays the list of what is done; this file is what comes next.
Evidence key (files in research/ unless noted): CT2 cold-test-2.md, SF setup-friction.md, FW frameworks.md, LT limits-text.md,
LP limits-platforms.md, WS web-service.md, MK market-2026.md, AL all-languages.md, RA real-apps.md, AU audit.md, PR pricing-2026-10.md.
Root files: README, CHANGELOG, STRATEGY, DISTRIBUTION, LAUNCH, ROADMAP, PLAN. Effort: S < 1 day, M 1-3, L > 3 (ROADMAP.md scale).
`[proposed]` marks a threshold I chose; no data sits behind it. Gap in the evidence: research/site-critique.md is empty (0 bytes), so nothing relies on it.

## 1. Where we are

State: v0.1.0 binary signed and notarized (DISTRIBUTION.md), sale not open (site still shows the waitlist; Polar product, benefit and
FOUNDER29 exist, the account review is Manu's step: LAUNCH.md). The parallel session's items (Android tablets, device_types, in-app text
reading, signed folder) are committed (03605fc, 6d7bc2b, bdccb71, 3b9bd47); only the 7" tablet slot is left (L7).

**Proven by real runs**

| What | Evidence | Limit of the proof |
|---|---|---|
| `run`: 18 languages x 4 screens, iOS 534 s, Android 15 min 24 s, 0 check problems, exported to fastlane | README, PLAN.md | One app (CrossfitTracker), Maestro 2.0.10 only (LT intro) |
| iPhone 6.9" + iPad 13" and Android phone + tablet from one flow, exported to the right folders | ROADMAP.md, PR section 1 | iPad on Remoti and Kuokka with de + ja only |
| `check` on real fastlane folders: 252 iOS + 126 Android in about 25 s each, planted errors caught; Remoti 108 true positives of 120; MCP `check` 72 screenshots in 29 s | README, CT2 #18, RA, ROADMAP.md | Mac text recognition sometimes stuck, Tesseract fallback added (304cd1a) |
| Notarized folder build, quarantined install runs, starts in 0.1 s | DISTRIBUTION.md | Apple silicon only |
| Compose Multiplatform apps on both platforms (Kuokka, HackerNewsKMP) | PR section 1, RA | Older APKs than sources |
| Reading strings of 7 real apps matched their repos (Remoti 1194 keys exact) | RA | Reader level, not a screenshot run |

**Only coded** (no real run, or no run at all)

| What | Why it is not proof |
|---|---|
| Flutter, React Native, MAUI, Unity runs | Readers load real translation files (wger ARB, Bluesky .po, Rocket.Chat JSON: FW section 0), no real app was run; README and site say "sample projects" |
| Licence on the release build | Tested against a fake API (DISTRIBUTION.md); a real Polar key was never validated; free tier never run on a gate-ON build (CT2 #25) |
| Hooks, overrides, plugins, after_run across devices, launchApp options (shotfleet.py 717) | Unit tests only (CHANGELOG, 118e994, cbee31f) |
| Fixture app (tools/fixture-app) | Committed in 01fa67d, no test runs it |
| README CI recipe, Homebrew formula, "about 10 minutes" quickstart | README says the recipe was not run; formula tested through a local tap; time unmeasured (SF section 9.7) |
| Anything needing Maestro 2.7 or newer | Nothing was run (LT intro) |

**Known risks, ranked**

| # | Risk | Evidence |
|---|---|---|
| R1 | A new buyer installs Maestro 2.11 (published 2026-09-29); every run so far used 2.0.10; README says "2.x" | SF section 0.4, LT intro |
| R2 | Nothing sells until Polar's review passes (up to 14 days); the KvK/registration question is open | LAUNCH.md |
| R3 | No demand data: waitlist had 0 signups, and no visit counter exists (worker.js counts signups only) | PR section 3, site/worker.js |
| R4 | First-run friction causes refunds: Debug simulator build, `init` needs a path, Java and a 315 MB Maestro, silent first text-recognition compile | SF sections 0-5, CT2 |
| R5 | Copy ahead of the product: README CI recipe runs `python3 shotfleet.py` but source is private; Apple silicon only is not on the site; site says WOD Tracker, README says CrossfitTracker | README, DISTRIBUTION.md, site |
| R6 | The workers.dev URL is baked into the binary (update check, buy link, install message: shotfleet.py 1685, 2078); moving later strands installed copies | shotfleet.py |
| R7 | One person: support, tax status, personal liability | WS sections 2, 5.4 |
| R8 | ButterKit ($99, free tier, MCP) and free tools (simshot, asc, fastlane) set the price anchor | PR section 2, MK section 1 |

## 2. Roadmap

### NOW: before the first sale (Claude work about 9-13 days; fits inside Polar's 14-day review, so G0 is on or after 2026-10-16)

| # | Outcome and why | Effort | Risk | Dependency and who | Works if | Kill or skip if |
|---|---|---|---|---|---|---|
| N1 | Sale can open: Polar review submitted and passed, checkout link live, KvK/tax question asked (LAUNCH.md: a merchant of record covers sales VAT only) | S, 0.5 h + up to 14 d wait | High: nothing sells before approval; the answer may add duties | None, start today. Manu | Polar shows the account approved; link opens at $29 with FOUNDER29 | Polar rejects: Gumroad keys exist in code (DISTRIBUTION.md) but its tax handling is unverified (0740e23); decide then |
| N2 | Licence and free tier proven on the notarized gate-ON build with a real Polar key: activate, all languages, deactivate, refund, key stops validating; free tier caps at 2 and refuses export (DISTRIBUTION.md used a fake API; CT2 #25) | M, 1-1.5 d | High: a failed activate is a paying buyer's first screen | N1 (or Polar test mode if it exists), N7. Claude scripts, Manu buys and refunds | 8-step rehearsal script passes; Polar shows activations 1 then 0; `validate` fails after refund | None, blocker |
| N3 | Run works on the Maestro a buyer gets today: fixture e2e plus CrossfitTracker iOS and Android on 2.11.x and 2.0.10; README and doctor name the tested version, doctor warns outside it (SF table in section 1) | M, 2-3 d | High: 2.6.0 changed parallel iOS handling, debug layout, log lines (LT section 1e) | N7, a quiet Mac. Claude; Manu frees the Mac | 18/18 both platforms on 2.11.x, same problem count as 2.0.10, wall time within +20% [proposed] | More than 3 days of fixes: ship "Maestro 2.0.x only" with a doctor error on newer; revisit with X1 |
| N4 | Cold test 3 on the release build: fresh macOS user, `env -i`, README and site only, gate ON; real time-to-first-screenshot replaces "about 10 minutes"; CT2 findings re-checked | M, 1-2 d + outsiders | Medium: finds what N1-N3 miss | N2, N3. Claude tests; Manu finds 2-3 outside developers | 3 of 3 reach a `run --locales en` screenshot without messaging Manu; median time goes in README | None, it is gate G0 |
| N5 | Every promise on site and README true and tested: claims table (section 4), fix R5, run the CI recipe once on a throwaway public repo, redo the site critique | S-M, 1-2 d | Medium: each false line is a refund or a review | None. Claude; Manu creates the repo | 0 claims without a test or run reference; CI job green once | CI recipe cannot pass: delete it from README |
| N6 | Review grid names the problem per cell and survives being moved (CT2 #19; `write_gallery` has no reason text and uses relative image paths); also CT2 #7 (bare `sysctl`) and #21 (notice after the error) | S, 1 d | Low | None. Claude | Unit test: a size error flags only its cell; report opens after the folder moves | Skip embedded thumbnails if the report passes 5 MB [proposed] |
| N7 | Fixture end-to-end test: tools/fixture-app (iPhone + iPad, 5 languages) built, run, checked, exported by one script, with a planted wrong-language and a missing screen | M, 2 d | Low | A quiet Mac. Claude | Script exits 0 in under 10 min [proposed]; removing a detector makes it fail | None, it is the guardrail |
| N8 | Flutter/RN/MAUI buyer is told what to do: `init`, `run`, `check` detect a build with no readable translations and print the `strings =` line; warn on RN Debug builds and the Flutter debug banner (FW section 11 #4-5, bugs 5 and 7) | S, 0.5-1 d | Low | None. Claude | 3 stub bundles in unit tests produce the hint; `init` on a Flutter stub no longer prints "0 languages" alone | None |
| N9 | Domain decided before the first release, visits and downloads counted: moving the URL later breaks update checks of installed copies (R6); add cookieless visit counts, a download counter, update privacy.html | S, 0.5-1 d | Low-medium | None. Manu buys the domain; Claude edits site, binary, go-live.sh | `grep -r workers.dev` leaves only redirects; V (visitors) and D (downloads) readable | Manu keeps workers.dev: write it down as the accepted trust cost, still add counters |
| N10 | Go-live rehearsed: packaging/go-live.sh edits shotfleet.py, commits, pushes and deploys in one run; add a dry run and a post-deploy smoke test from a clean HOME | S, 0.5 d | Medium: one-shot script on the live site | N1, N9. Claude writes; Manu runs | Smoke: install.sh checksum matches, `--version` equals /download/VERSION, `check` runs on a bundled sample | None |

### NEXT: first 60 days (starts after G0; reorder by what the first 10 buyers report)

Moved up from "later" because the first buyer hits them: X4 (Flutter/RN validation), X5 (typed text), X6 (launchApp).

| # | Outcome and why | Effort | Risk | Dependency and who | Works if | Kill or skip if |
|---|---|---|---|---|---|---|
| X1 | shotfleet fetches the tested Maestro (315 MB) and a JRE (48 MB) itself, SHA-checked, from their official release pages (`doctor --fix`): removes the two biggest install steps and version drift; the Homebrew route hits Homebrew 7 trust refusals (SF sections 0.1, 1 option D; DISTRIBUTION.md chose install.sh) | M, 2-3 d | Medium: 360 MB downloads, extra update surface | N3 (which version). Claude; Manu approves | Cold test: Java and Maestro steps drop to 0; fewer than 10% of buyers write about them | N4 testers install both unaided in under 10 min and week-1 support has 0 such cases |
| X2 | `shotfleet init` with no arguments finds the newest Debug simulator build (DerivedData matched to the project folder) and the Gradle debug APK, says what it chose, prints the build command otherwise; never runs `xcodebuild -list` by default (it wrote 2.4 GB per project: SF section 0.6) | M, 2-3 d | Medium: DerivedData is volatile (SF section 0.7) | None. Claude | On CrossfitTracker, Kuokka, Remoti, Cairn `init` picks the right build; N4 median time drops | Drop `--build`, keep discovery, if fewer than 3 first-week reports concern builds |
| X3 | Android setup: SDK found in 4 places, any installed API 33+ image used, exact `sdkmanager` commands in doctor (SF section 4) | S, 1 d | Low | None. Claude | doctor on a Mac with only brew command-line tools prints a working next command | Skip until 5 Android-first buyers |
| X4 | Real-app framework validation in order wger (Flutter), obytes (Expo), kotlinconf-app (Compose), MAUI LocalizationDemo; README and site then name only what passed (FW sections 12, 14; README Limits) | L, 5-6 d + installs | Medium: each framework has a build trap (FW sections 1-5) | N7, N8. Claude; Manu approves each download (Flutter about 1.5 GB) | Per app: 0 untranslated selectors, 2-language and full run green, one German and one Arabic PNG looked at by a person | A framework that eats 1 day without a pass is listed as unsupported; start with the stack most signups chose |
| X5 | Typed text per language: `[inputs]` table written into each per-locale flow header, removes the README limit "text you type isn't translated" (LT section 2, rank 2) | S, 1 d | Low | N3, N7 (fixture gets a text field). Claude | Fixture PNG shows the Japanese value, proven by in-app text | iOS CJK/Arabic typing fails on the simulator: ship Latin-script inputs only and say so |
| X6 | launchApp options verified in a run: `permissions`, `clearState`, `arguments` in the fixture, then README Tips and Limits updated (LT section 3; code at shotfleet.py 717) | S, 0.5 d | Low | N7. Claude | Fixture with `permissions: {all: deny}` runs 5/5 and shows no dialog | None |
| X7 | Done-for-you run: page section plus Polar product at $149 per app, cap 10 orders (marketing/done-for-you.md; WS section 8). WS's $9 check-by-hand is dropped because free `check` exists (WS section 6.3) | S, 1 d + 2 h per order | Medium: Manu's time, tax status of service income; Apple licence reading "own Mac, handful of orders" is unsure (WS section 8) | N1, N9, tax answer. Claude page; Manu delivers | Gate G6 | Remove the section if G6 fails |
| X8 | Proof: timed fastlane-vs-shotfleet run on the same app, two case studies with permission, Maestro community PR, directory listings (STRATEGY section 3; PR section 4: proof is what lets the price rise) | M, 2 d + 0.5 d Manu timing fastlane | Low if only measured numbers are published | G0. Claude drafts; Manu posts | Each piece carries utm tags; visits and signups per piece | A channel is dropped after 2 posts with under 20 visits [proposed] |

### LATER: growth options, ranked by evidence (each needs its trigger, so none starts before G5)

| # | Outcome and why | Effort | Risk | Dependency and who | Works if | Kill or skip if |
|---|---|---|---|---|---|---|
| L1 | Team/CI licence (about $149) plus the CI recipe proven and a fastlane plugin: teams ask for CI first (STRATEGY sections 2.2, 4) | S-M, 0.5 d licence + 2 d plugin | Low | N5 (recipe run). Claude; Manu sets the Polar product | Trigger: 3 buyers ask; then 5 team sales in 30 days | Fewer than 3 asks in 60 days |
| L2 | Agent/MCP reach: registry and directory listings for `shotfleet mcp` and the skill (ButterKit and StoreScreens ship MCP: MK idea 7; STRATEGY section 2.4) | S, 1 d | Low | N5. Claude; Manu submits | Visits and signups with the listing's utm tag | 0 attributable installs after 30 days |
| L3 | Android `run` and `check` on Linux (largest untapped audience, Linux CI 6-10x cheaper than macOS: LP sections 2.3, 7 #2) | M, 4-6 d incl. experiments E1 and E2 (1 d) | Medium: x86 KVM speed unknown, Tesseract parity unmeasured, licence only enforced when frozen (LP section 2.2) | E1+E2 pass. Claude; Manu approves a throwaway repo | Trigger: 25% of signups Android-only or 5 Linux-CI asks; 18/18 on `ubuntu-latest` | E2 shows Tesseract verdicts differ from Vision on CJK/RTL: ship run only |
| L4 | `check --share`: expiring report link (WS section 6.2 A0, best funnel per day) | M, 2-3 d | Medium: site says "never uploaded", needs opt-in wording, privacy.html and terms | Worker route. Claude | 10 shared links by non-Manu users in 60 days | Fewer than 5 in 60 days |
| L5 | Android text from the UI hierarchy via the in-run marker (exact text in every script; LT section 1, AL A1) | M, 3-5 d + 10 min marker experiment | Medium: about 2 s per screenshot, needs Maestro 2.7+ | N3. Claude | Marker experiment yields one file per screenshot; Greek/Hebrew Android set verified | Fewer than 3 buyers with Greek, Hebrew, Georgian or Indic on Android; iOS already exact |
| L6 | More locales and OCR readers: Tesseract packs picked per locale (AL A2) | M, 2 d | Low | None | Hook proven on a rendered Greek and Hebrew screen | Fewer than 3 requests; `--ocr-command` already exists |
| L7 | 7" tablet slot (LP section 3.2) and `check`/`export` for Watch, Mac, TV, Vision screenshots made elsewhere (LP section 5) | S, 0.5 d + 0.5-1 d | Low | E3 and E4 (Play Console look by Manu) | A buyer's tablet listing validates | No buyer asks |
| L8 | Hosted variants beyond X7: Android service only after the Linux CLI sells (WS section 5.5); iOS hosted never (WS section 4) | L, 15-20 d | High | L3 sold | 3+ buyers say "no setup" | Default: do not build |
| L9 | Custom product page variant sets (LP section 5, MK idea 5) | M, 2-3 d | Low | None | 5 requests | Unproven demand: skip |
| L10 | Wear OS and Android TV capture (LP sections 3.3, 3.4) | M each | Medium | Experiment E5 | A buyer asks with an app | Skip until asked |

## 3. Decision gates (day 0 = checkout live and install.sh serving the notarized build)

Numbers: V visitors, D downloads (both from N9), S waitlist signups (site/signups.sh), A activations and P paid orders and R refunds (Polar), T support minutes per sale (Manu logs it).
Money (fees from DISTRIBUTION.md, 5% + $0.50, +1.5% international cards; $50/h is WS section 4.4's assumption): net per sale and sales needed for $3,000 a year (PLAN.md goal).

| Price | Net per sale (domestic / international card) | Sales for $3,000 | Support minutes that eat the net |
|---|---|---|---|
| $29 | $27.05 / $26.62 | 111-113 | about 32 |
| $49 | $46.05 / $45.31 | 66-67 | about 54 |
| $149 done-for-you | $141.05 | 22 | Manu's about 2 h per order is the cost |

| Gate | When | Numbers | If green | If not |
|---|---|---|---|---|
| G0 | Before day 0 | All NOW items done; 3 of 3 cold testers reach a screenshot unaided; S recorded | Open the sale | Do not open; fix the failed item |
| G1 Reach | Day 14 | V >= 400 (WS section 8's bar) | V < 400: distribution problem, no product work; post in the remaining channels. V >= 400 and P = 0: page or offer problem, change hero and pricing copy, not code | Continue |
| G2 Pace | Day 30 | P >= 20 [proposed; 50 in 60 days is 0.8 a day, launch-weighted]; 10-19 amber; < 10 red | Green: start NEXT items in order. Amber: change one variable for 2 weeks. Red: freeze features, write to buyers, refunded and non-buyers | |
| G3 Refunds | Day 30 and 60, per cohort after its 14 days | R/P <= 8% [proposed] | Over 8%: read every refund reason, fix the top one. Over 15%: pause the checkout until fixed | |
| G4 Support | Weekly | T <= 20 min per sale [proposed] | T 20-30: X1 and X2 jump the queue. T > 30 or over 30% of buyers stuck at setup: stop marketing (each buyer costs more than the $29 net) | |
| G5 Decide | Day 60 | P >= 50: invest. 15-49: extend 30 days, one variable changed, bug fixes only. < 15: free tool | Invest: pick from LATER by trigger; raise price in steps only with proof (2 case studies, a real Flutter/RN run: PR section 4), never straight to $79 | Free tool: `run` unlimited, honor the licences and the year of updates already sold, publish the benchmark (STRATEGY section 5) |
| G6 Concierge | 21 days after X7 goes up, V >= 400 | 5 paid orders or 25 checkout starts (WS section 8) | Keep as a service line | Remove the section |

Founder code limit is 100 redemptions (LAUNCH.md), so the price becomes $49 by itself after 100 sales.

## 4. Quality guardrails

Rule: an item counts as shipped when every layer listed for it is green and its claim row is updated. A claim that only passed U may be written
as "coded", never as "works".

| Layer | Proves | Where | Items |
|---|---|---|---|
| U unit | Readers, config, flow rewrite, licence against a fake API, hooks, gallery output | `python3 -m unittest discover -s tests` (135 test methods; new logic needs a test that fails without it, PLAN.md mutation style) | N6, N8, X2 rules, X5, X6 rewrite, L5 fixtures |
| S site | Signup worker, links, no `@CHECKOUT@` left, install.sh checksum equals the served build, VERSION matches, claims table, 375 px and desktop and dark screenshots | site/worker.test.mjs plus a new site check script | N5, N9, N10, X7 |
| F fixture e2e | Capture, translate, check, export on a real simulator with planted defects | tools/fixture-app plus the N7 script, quiet Mac only | N3, N7, X1, X5, X6 |
| R real-app | Languages, frameworks, versions, timings | CrossfitTracker both platforms (baseline 18/18, 72 screenshots, 0 problems; check 252 + 126), tools/langmatrix.py, Remoti iPad, Kuokka, X4 apps | N3, X4, L3, L5 |
| B release binary | Notarization, install, licence, refund, smoke | Clean user account, gate-ON build, real Polar test purchase | N2, N10, X1 |
| C cold test | Setup claims | Outsider with README and site only | N4, X2, X3 |

Claims table (research/claims.md, created in N5), first rows:

| Claim | Where | Proof layer | Status today |
|---|---|---|---|
| 18 languages x 4 screens, 9 min iOS, 15 min Android | site, README | R | Proven on one app, Maestro 2.0.10; re-measure after N3 |
| Flutter and React Native work from translation files | site, README | U now, X4 later | Honest ("sample projects") |
| Up to 3 of your Macs and your CI | site | B | 3 activations set in Polar; CI key path unrehearsed |
| Works offline for 30 days | site | U with fake API | Never run on a real clock |

Release checklist, in order:
1. Quiet Mac: no booted simulators, no other Maestro run.
2. Unit tests green; new logic has a test that fails without it.
3. Fixture e2e green, planted defects caught.
4. CrossfitTracker iOS and Android match the baseline; `tools/langmatrix.py` unchanged.
5. Tested Maestro version equals the one in README and doctor.
6. Build, sign, notarize; `spctl -a -vv` says Notarized Developer ID; quarantined install on a clean user.
7. Gate-ON build: `check` free, `run` capped at 2, `export` refused without a key, `activate` with a real key, `deactivate`.
8. Site in sale mode: links 200, checksum, VERSION, mobile and desktop screenshots looked at.
9. Every changed claim re-verified; claims table has no empty proof column.
10. CHANGELOG and README Limits match behavior.
11. Deploy, then the smoke script from a clean HOME.
12. Previous tarball kept on the site for rollback.

## 5. What not to build

| Not building | Why | Evidence | Revisit when |
|---|---|---|---|
| Hosted iOS capture or pay-per-run Macs | Apple's licence bans service-bureau use; leasing needs 24 h exclusive leases | WS section 4 | Apple's written permission |
| A credits website | Credit price beats the $49 CLI only for the first 3-4 runs; the repeat user loses | WS sections 7, 11 | After L3 sells and buyers ask for "no setup" |
| Frames, captions, store upload, web dashboard | Free or entrenched tools do it; we feed them through hooks and recipes | STRATEGY "Not building", README Extending | Never |
| Windows-native, Android below API 33, Watch/Mac/tvOS/visionOS capture | Process-control rewrite; limit is the emulator not the app; Maestro cannot drive them | LP sections 2.3, 4, 5 | Three buyers ask |
| Unity and game support claims | No text in the accessibility tree | FW sections 6, 14 | Never as a promise |
| Capacitor/Ionic claims | iOS language path unverified | FW section 7 | After a 1 h experiment |
| Bundled or cloud OCR (Tesseract, PaddleOCR, Surya, Google) | Size, Surya licence, unreleased screens uploaded | AL A2 | Opt-in `--ocr-command` is enough |
| Readers for Hermes bytecode, .NET satellite DLLs, Unity bundles | L effort; source files are cheaper | AL section E | Never |
| Out-of-run hierarchy dumps (idb, uiautomator, `maestro mcp`) | Port clash, UiAutomation conflict | LT section 1b | Never; L5 uses the in-run marker |
| Auto-translating typed text | No source for names and addresses | LT section 2c | Never |
| Dark/light capture matrix | Nobody asked | MK idea 8 | A buyer asks |
| Homebrew as the main install | Homebrew 7 trust refusals; DISTRIBUTION.md chose install.sh | SF section 0.1 | Buyers ask for `brew install` |
| A $79 price or a $9 hand-made check | Not supported by evidence; free `check` exists | PR section 3, WS section 6.3 | G5 with proof |

## 6. Three things to do this week (2026-10-02 to 2026-10-09)

1. Manu: submit Polar's account review (identity, payout, checkout) and send the KvK/tax question to the Belastingdienst or an accountant (N1, LAUNCH.md). It is the only item with a wait outside our control. Decide the domain (N9) the same day, because the binary bakes the URL in.
2. Claude, with Manu freeing the Mac for a few hours: write the fixture end-to-end script, then run it and CrossfitTracker on Maestro 2.11.x against 2.0.10 and pin the tested version (N7 then N3).
3. Claude, on work that needs no Mac: claims table and README/site fixes (N5), review grid and CT2 leftovers (N6), framework hints (N8), visit and download counters (N9).
