# Docs and website audit after 0.1.1 (2026-10-05)

Branch `claude/docs-audit`. Device-free. Nothing was edited except this note. Read: README.md, `site/public/*.html`, `llms.txt`, `install.sh`, `docs/*.md`, `skill/**`, CHANGELOG, STATUS, LAUNCH, `tests/claims.json` (131 rows), `shotfleet.py` where a sentence needed checking, and today's research notes. `marketing/` was read for context only; no edit is proposed there.

Marks: **CONFIRMED** = I checked the repo or the code. **INFERRED** = follows from a note or from reasoning, not checked against a device or a live system.

Facts checked first (all CONFIRMED unless marked): `shotfleet.py` VERSION is 0.1.1; the 0.1.1 CHANGELOG diff against the 0.1.0 build (081853b) shows which bullets are new; `reports_json()` (shotfleet.py ~2503) merges several reports and adds `reports`; `--json` runs `main_cmd` with stdout redirected to stderr (~3810), so the free-tier line goes to stderr; `cap_locales` (~3889) already prints "limited to 2 languages because there is no valid licence", the refusal reason and `--locales a,b`; `doctor` prints "shotfleet X is out (you have Y): curl ... | sh" (~3112); `latest_ios_runtime()` returns the last available iOS runtime (~3546); claims register: 131 rows, proven 60, fixed 22, evidence 27, partial 17, unverifiable 2, untested 1, removed 2, so 82 green and 47 not green. `python3 -m unittest tests.test_docs`: 26 tests OK on this branch.

A pointer for whoever does the refresh: **three tests pin sentences that this audit calls wrong or weak**, so they change in the same pass: `tests/test_site_audit.py:297` (asserts the "I haven't run it on a real Flutter or React Native app yet" sentence on alternatives.html), `tests/test_cli_claims.py:116-120` (the CI recipe in the README; only matters if the recipe lines change), `tests/test_docs.py:90` (the "Last checked against version" line must match VERSION and the top CHANGELOG heading).

---

## (a) STALE OR FALSE

Order inside the section: false first, then overstated, then weaker than the evidence.

**A1. alternatives.html:88 says the Flutter and React Native run never happened. FALSE today. CONFIRMED.**
- Current: `Your app is Flutter or React Native. shotfleet reads translation files from those stacks, but I haven't run it on a real Flutter or React Native app yet.`
- Why: index.html, README, docs.html, llms.txt and claim C035 say it was run end to end on wger (Flutter) and the obytes template (Expo), iOS and Android, 2026-10-03. The comparison page contradicts the home page. `docs/handoff.md:96` says it was left alone on purpose (conservative), but a false statement in the other direction is still false, and a reader who compares the two pages will trust neither.
- Replace with: `Your app is Flutter or React Native. shotfleet reads translation files from those stacks and has been run end to end on one real Flutter app (wger) and one real Expo app (the obytes template), not on other apps or on bare React Native.`
- Claims row: none quotes alternatives.html for this. Add the page to C035 `where` with that sentence in `where_text`. Test: change `tests/test_site_audit.py:297` to assert `not on other apps or on bare React Native`.

**A2. README:63 says `doctor --fix` was never run on a Mac. STALE. CONFIRMED.**
- Current (last sentence of the paragraph): `It has not been run on a Mac yet.`
- Why: STATUS.md row "D1" (UPDATE 2026-10-03, Mac, Apple silicon, macOS 27) records both Mac branches run for real in a throwaway home with this Mac's Java, SDK and Homebrew tools hidden by a `sandbox-exec` profile (no `brew`: 5 steps; with `brew`: 3 steps), ending with `doctor` reporting Maestro, Java, iOS and Android ready. Claim C126's own assertion says "Run on a Mac in a throwaway environment ... 2026-10-03; not on a separate clean user". That run installed Maestro 2.0.10; the pin is 2.11.0 now, so the Mac run did not cover the 2.11.0 download. (`research/limits-first-run-2026-10-05.md` still lists it as unverified; it was written without STATUS row D1 in view. The refresh agent should re-read the D1 row before wording this.)
- Replace with: `Run on a Mac (Apple silicon, macOS 27, 2026-10-03) in a throwaway home folder, with Maestro 2.0.10 as the pin of that day; not yet run with the 2.11.0 download, and not on a separate clean user account.`
- Claims row: C126 (README quote is the first sentence only, so the quote still matches). Update the proof with the 2.11.0 caveat. Status stays `partial`.

**A3. docs.html:259 says iOS runs are not affected by a stuck text reader. OVERSTATED, and README disagrees. CONFIRMED.**
- Current (docs.html:259, end): `iOS runs are not affected: they read the app's own text.`
- README:297 says `iOS runs mostly aren't affected: they read the app's own text, and only screens where that text proves little go to OCR.` The README is the accurate one.
- Replace docs.html with the README sentence. Claims row: none.

**A4. "from any tool" overclaims (docs.html:44 and :111, llms.txt:3, skill/shotfleet/SKILL.md:10, docs/AGENTS-snippet.md:11). OVERSTATED. CONFIRMED.**
- Current: docs.html `Check screenshots from any tool` (menu entry and heading); llms.txt `It also checks screenshots made by any other tool (fastlane snapshot, screengrab, by hand) without capturing anything`; SKILL.md `It also checks screenshots made by any other tool, with no simulator.`; snippet `It also checks screenshots made by any other tool.`
- Why: CHANGELOG line 20 records that the README heading was changed because only fastlane snapshot/screengrab, plain `<locale>/` folders and `raw/` were tried; claim C031's proof says "other tools' exports were not tried" and its where_text is `works on fastlane snapshot/screengrab folders and on a plain folder per language`. The README got fixed, the four other places did not.
- Replace: docs.html `Check screenshots you already have` (both places; keep the anchor `#check`); llms.txt `It also checks screenshots you already have (fastlane snapshot, screengrab, a plain folder per language, by hand) without capturing anything.`; SKILL.md `It also checks screenshots you already have (fastlane snapshot, screengrab, a plain folder per language), with no simulator.`; snippet `It also checks screenshots you already have (fastlane, screengrab, by hand).`
- Claims row: C031 `where` could list docs.html with the new heading. Tests: `tests/test_agent_skills.py` compares skill text with README in places; run it after the edit.

**A5. README:296 and docs.html:258: "It reads 33 languages" is the macOS 27 number. STALE FOR ANY OTHER MACOS. CONFIRMED (the number) / INFERRED (older macOS reads fewer).**
- Current: `Text recognition is macOS's. It reads 33 languages, including Latin, Cyrillic, Arabic, Thai, Devanagari, Chinese, Japanese and Korean scripts. For scripts it can't read (Greek, Hebrew, ...), ...`
- Why: C071's own proof says "older releases read fewer". Catalan, Croatian, Hungarian (Latin script) are not among the 33; a hosted run showed the same Catalan screenshot skipped on macOS 14.8.9 ("macOS can't read the script of ca") and judged "looks like 'en'" on 15.7.9 (`research/limits-platform-reach-2026-10-05.md`, `research/limits-catalan-check-macos-2026-10-05.md`). The README builds the claim "built for macOS 13 or later" two bullets below it, so a buyer on macOS 14 reads 33 and gets fewer.
- Replace (keeps the quoted prefix of C071 intact): `Text recognition is macOS's. It reads 33 languages (the macOS 27 number; older macOS versions read fewer), including Latin, Cyrillic, Arabic, Thai, Devanagari, Chinese, Japanese and Korean scripts. A language outside that list is judged more weakly even when it is written in Latin script (for example Catalan, Croatian and Hungarian), so the same screenshot can get a different verdict on a different macOS version. For scripts it can't read (Greek, Hebrew, Armenian, Georgian, most Indic and Southeast Asian scripts), ...` (rest unchanged).
- Do NOT use the last sentence of the Catalan note's proposal ("Pass `--app` ... gives the same answer on every macOS"). It is not shown: on macOS 14 the reader returns no Catalan text at all, so `--app` has nothing to compare. INFERRED.
- Claims row: C071 (quote still matches; add the 14.8.9/15.7.9 runs to the proof). Status stays `evidence`.

**A6. docs.html:224 gives the `--json` shape of 0.1.0. STALE against README and the code. CONFIRMED.**
- Current: `... the result goes to stdout as JSON (exit, screenshots, problems for run and check; exit, exported, skipped for export) and progress goes to stderr.`
- README:92 (changed by #68) adds `merged over every device or platform checked, plus reports (one {report, problems} each) when there are several`. The code adds `notes` too (all three lists merged).
- Replace docs.html:224 with the README sentence and add `notes`: `... (exit, screenshots, problems and notes for run and check, merged over every device or platform checked, plus reports (one {report, problems} each) when there are several; exit, exported, skipped for export) ...`. Same `notes` addition in README:92 (its list also omits `notes`).
- Claims row: C064 and C065 quote README only; check their where_text still match after the README edit (`tests/test_claims.py` tells).

**A7. README:94, docs.html:225, skill/shotfleet/references/ci.md:12 say the CI recipe never ran on GitHub. WEAKER THAN THE EVIDENCE. CONFIRMED.**
- Current: `(This recipe hasn't been run on GitHub yet; the command itself is the one tested above.)` (docs.html: `This recipe has not been run on GitHub yet; ...`).
- Why: on 2026-10-05 two manual runs installed the live 0.1.1 on GitHub's Apple-silicon `macos-14` (14.8.9) and `macos-15` (15.7.9) runners: `install.sh`, `shotfleet --version`, `doctor` (ran to the end) and `check` on two sample screenshots all worked. The recipe as written (an `xcodebuild` step, then `check --app ... --json`) still did not run, so "not run as written" stays true, but the sentence now hides what was shown, and the recipe's `runs-on: macos-15` is one of the two tested images.
- Replace: `The recipe as written (the build step, then check with --app) has not been run on GitHub yet. The installer, shotfleet --version, doctor and check on sample screenshots did run on GitHub's macos-14 and macos-15 runners (2026-10-05).` Same sentence in the three places.
- Claims row: C066 (where_text is the `check` line, unaffected; update the proof; stays `fixed`). `tests/test_cli_claims.py:116` only reads the recipe block, unaffected.

**A8. llms.txt:26 and :34 are generic about a state that is over. LOW. CONFIRMED.**
- Current: `The home page says whether shotfleet is on sale yet or still on an early-access list.` and `what the site stores and what is kept when you buy or join the list`.
- Not false (written to work both before and after launch) but the site is on sale and has no list. Check `go-live.sh` and `tests/test_site_audit.py:336-338` before editing: they expect the pre-launch markers to be removed on go-live, and this text is not one of them.
- Replace: `The home page links to the checkout; shotfleet is on sale.` and `what the site stores and what is kept when you buy or write to me`. The second one waits on D1 (privacy waitlist text).

**A9. README:161 and docs.html:151 give `iOS-26-5` as the example runtime without saying that the default changes once an iOS 27 runtime exists. INCOMPLETE rather than false. CONFIRMED (`latest_ios_runtime()` takes the last available iOS runtime).** See B2 for the text; nothing in the current sentence is wrong.

(No other sentence in the six public pages contradicts a fact above. Checked and fine: minimum macOS line (README:301, docs.html:60), Maestro versions (README:302; docs.html:62 says only "Maestro 2.x", see B7), prices and "once per developer", 3 Macs plus CI, 14-day refund, "about weekly, 30 days offline" (applies to an activated Mac; the CI key fails open, see D6), 9 and 15 minutes (conservative, C007 stays `evidence`), Apple silicon only.)

Items in (a): 9 (A1 to A9).

---

## (b) MISSING

What a buyer needs and does not find. Each item: where it belongs, proposed text, mark. Wording that touches price, refund or licence terms is listed again in (d) and is not for the refresh agent to decide.

**B1. How to update. CONFIRMED gap; proposed text CONFIRMED against `install.sh` and `shotfleet.py`.**
- Nothing in README, docs.html or terms.html says how to get a newer version. The only signal is `shotfleet doctor` printing `shotfleet X is out (you have Y): curl -fsSL https://shotfleet.com/install.sh | sh` (shotfleet.py ~3112). 0.1.0 buyers, who very probably cannot start it below macOS 26.3, have the most to gain (`research/0.1.2-plan.md` lists this as a 0.1.1 leftover).
- Where: README after the Quickstart install block; docs.html "Install"; `skill/shotfleet/SKILL.md` (agents get asked).
- Text: `Update: run the install line again. It replaces the program and keeps your licence (the key is stored outside the program folder). shotfleet doctor tells you when a newer version is out. A year of updates is included.` (INFERRED: the installer package installs over an older copy; mention only the curl line.)
- Claims row: none today. Optional new `evidence` row (`tests/test_release_candidate.py` covers "update over an installed copy works").

**B2. The iOS runtime pin and iOS 27. CONFIRMED gap.**
- README:161 and docs.html:151 say `runtime` defaults to "newest installed". True, and it now matters: on 2026-10-05 an iOS 27.0 runtime was installed on the dev Mac by an unknown session, `latest_ios_runtime()` picked it, and the 0.1.1 gate had to pin iOS 26.4 (`research/release-0.1.1-evidence-2026-10-05.md`). Shown on iOS 27: ONE simulator and ONE language, 78 s, 0 problems, Maestro 2.0.10, quiet Mac (`research/xcode-27-ios27-attempt-2026-10-05.md`). An earlier 4-simulator run stalled for 35 minutes under load 735 and 21.6 GB of swap (memory thrash; not proven to be iOS 27). A 4-simulator iOS 27 run is untested.
- Where: README Config (below the `runtime` line) and Limits; docs.html Config table row `runtime` and Limits; `skill/shotfleet/references/config.md:46` and `troubleshooting.md` (a row for "run behaves differently after installing an iOS 27 runtime"). `docs/handoff.md:139` already says it for agents.
- Text (config row): `The simulator runtime. Default: the newest one installed, so installing an iOS 27 runtime changes what run uses. To stay on a runtime you have tested, pin it: runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4" (xcrun simctl list runtimes shows the ids).`
- Text (Limits): `iOS 27: one simulator and one language ran with 0 problems (2026-10-05). A run on four simulators at once has not been tried on iOS 27; pin an older runtime if you need a tested setup.`
- Claims row: new row `evidence`, or extend C131's proof; no existing row quotes this.

**B3. The minimum macOS (and Xcode) outside README and docs.html. CONFIRMED gap.**
- `Built for macOS 13 or later on Apple silicon; tested on macOS 27.` is in README:301, docs.html:60 (C131) and on the Gumroad page. It is missing on index.html (price lede line 305, "Not for you if", JSON-LD `softwareRequirements` line 37), alternatives.html:89, llms.txt:16-18, SKILL.md:11 and AGENTS-snippet:12. The owner note asks to decide when the home page carries it (D3).
- Xcode has no version anywhere except README:286 (building on Xcode 27). Shown: Xcode 27.0 with the iOS 26.4 and 27.0 runtimes. Not shown: Xcode 26.x. Older Xcode: the default `device_type` is the iPhone 17 Pro Max, which an older Xcode does not have, so `run` stops with "could not create simulator" and the buyer sets `device_type` (INFERRED from the platform note and shotfleet.py:1217; not run on an old Xcode).
- Text for README Limits and docs.html Requirements: `Tested with Xcode 27.0. The default simulator is the iPhone 17 Pro Max, which needs Xcode 26 or newer; with an older Xcode set device_type in the config. Xcode 26.x has not been run.`
- Text for the other places once the owner agrees (D3): the same sentence, verbatim, so C131 keeps matching; in JSON-LD `softwareRequirements` prefix `macOS 13 or later on an Apple silicon Mac, `.

**B4. What a free-tier `run` prints, and which two languages. CONFIRMED (code); the order is INFERRED.**
- README:51, docs.html:73, terms.html and index say `run` is free for up to 2 languages. None says which two. Since #69 the program prints: `free tier: capturing 2 of N languages (a, b). This run is limited to 2 languages because there is no valid licence[: the key was not accepted, <reason>]. --locales a,b picks which ones; shotfleet activate <key> unlocks every language (<buy url>)`. The two are the first two of the app's languages in list order (the product note calls it alphabetical; the code takes `locales[:2]`).
- Where: README "Free and paid" and "In CI" (the sentence ending `run captures only 2 languages`); docs.html Install paragraph and In CI; skill `references/licence.md` already names `free tier: capturing`.
- Text: `Without a valid licence, run captures only 2 languages (the first two of your app's languages unless you pick them with --locales de,ja) and says so on a line that starts with "free tier:"; the exit code is 0 if those two pass. If SHOTFLEET_KEY is set but refused, that line says why. check, doctor and init are always free.`
- Claims rows: C049 and C032 quote existing sentences (unaffected). `tests/test_free_tier_message.py` proves the wording; a new row is optional.

**B5. A licence section in the docs page. CONFIRMED gap.**
- docs.html has no licence section: activation, `shotfleet deactivate`, the 3 activations, what a refused key prints, the 30-day offline limit and the CI key are spread over the install paragraph, the CI paragraph, terms.html and `skill/shotfleet/references/licence.md`. README never mentions `deactivate`.
- Text (new `<h2 id="licence">Licence</h2>`; README "Free and paid" gets the first three sentences): `shotfleet activate <key> stores your key on this Mac. The key from your Gumroad receipt works on 3 Macs, and activating again on a Mac that already holds it counts nothing. shotfleet deactivate removes it from this Mac but does not give the activation back; email hello@shotfleet.com to move to a fourth Mac. The licence is checked online when you activate and about once a week after; if the server cannot be reached, the Mac keeps working for up to 30 days after the last good check. A refunded or disabled key is refused at its next check; check and the 2 free languages keep working and nothing you made is deleted. In CI, set SHOTFLEET_KEY (no activation is used).` Every clause is already public on terms.html, index.html or privacy.html; nothing is new policy. Messages to quote: `the key was disabled, as Gumroad does after a full refund`, `this licence is no longer valid`, `that key didn't activate`.
- Do not state "0 to 7 days" or "a refunded key is refused" as something seen on a live key: STATUS gate 5 says it is unproven (D2).
- Claims rows: C046, C047, C050 quote terms or index only; a docs.html quote is a new `where` entry, not a change.

**B6. The `--json` traps. CONFIRMED (code); skill-only today.**
- `skill/shotfleet/references/ci.md` lines 59-62: several reports give one merged document plus `reports`; a missing or invalid `SHOTFLEET_KEY` does not fail `run` (2 languages, exit 0, and the "free tier" line goes to stderr because `--json` redirects stdout). README says the second half in one clause; docs.html not at all.
- Text for README and docs.html In CI: `With --json, progress goes to stderr, including the "free tier:" line, so a CI job that must capture every language should fail when that line appears, or compare the language count in run.json.`

**B7. Tested Maestro versions, and what the timings were measured on. CONFIRMED.**
- docs.html:62 says only `Maestro 2.x and Java 17+`; README:302 says tested with 2.0.10 and 2.11.0 and that `doctor --fix` installs 2.11.0.
- The quiet-Mac re-measure of 2026-10-05 (iOS 404 s capture, Android phone 415 s, 0 problems, 4 devices, 19 languages) ran on Maestro **2.0.10**, load 86 at the start and 497 at the end of the iOS part (C007 proof: "not perfectly quiet"). `doctor --fix` installs 2.11.0, where the only iOS run (2026-10-04, loaded Mac) needed shotfleet's own retry for 9 of 19 languages and took 826 s of capture; Android phone on 2.11.0 took 475 s. So "9 minutes on iOS" was measured on the other version than the one the installer fetches. Not false (C007 says 4 simulators, 32 GB M1 Pro, 2026-10-01; it stays `evidence`), but unqualified.
- Where: docs.html Requirements and a Limits bullet.
- Text: `Maestro 2.x (tested with 2.0.10 and 2.11.0) and Java 17+.` and `Run times depend on the Mac and on Maestro: 18 languages took 9 minutes on iOS and 15 on Android on a 4-simulator M1 Pro with Maestro 2.0.10; on Maestro 2.11.0 shotfleet retried some iOS languages because a simulator's driver started slowly.`
- Claims rows: C007, C105 (where_text unchanged; add the facts to the proof). The home-page wording is D5.

**B8. Free memory before a run (Gradle daemons). CONFIRMED event; the advice is INFERRED to help.**
- Today's lesson (`docs/owner-note-0.1.1.md`): idle Gradle daemons from several projects held about 21 GB; four simulators then thrashed (the 0.1.1 gate took 55 minutes instead of about 25 until seven daemons were stopped; the iOS 27 e2e stalled 35 minutes). A buyer building an Android app next to a four-simulator iOS run is in the same position. `run` already cuts the device count under memory pressure (STATUS row 10), and `troubleshooting.md:71` has the "critical memory pressure" row.
- Where: README Tips; `skill/shotfleet/references/troubleshooting.md`.
- Text: `Free memory before a run: idle Gradle daemons can hold gigabytes. Run ./gradlew --stop (once per Gradle version you use) before shotfleet run, and close apps you do not need. Four simulators on a loaded Mac can take many times longer.`

**B9. First-run order and what to expect. CONFIRMED (the note exists); claim impact INFERRED.**
- `research/limits-first-run-2026-10-05.md` ("Proposed README Quickstart"): README puts `activate` before `doctor`, assumes Maestro exists, and says nothing about `xcode-select -p`, a first `doctor` that can take a minute (text recognition compiles: 30 s quiet, 127 s measured loaded) or that the Android block can be ignored by iOS-only apps. The messages were fixed in 0.1.1; the README quickstart was not.
- Text: the note's proposed block and its "Notes to add". Claims that quote quickstart lines may break: check with `python3 -m unittest tests.test_claims tests.test_cli_claims tests.test_first_run` (targeted). Changing the order of `activate` is setup advice in a public page: D7.

**B10. docs.html lacks what README has. CONFIRMED (grep).**
- README items with no counterpart on docs.html: Tips "Flutter rows and cards are one label", "A language the app only half translates", "Building the app on Xcode 27" (`expo run:ios` cannot find Simulator.app; `IPHONEOS_DEPLOYMENT_TARGET=15.1`; `ARCHS=arm64` for Kotlin Multiplatform), "Typing a password on iOS in Arabic", the Linux limit. The docs page is what a search lands on.
- Text: copy those README sentences into docs.html "Limits" unchanged (so C121 and neighbours stay valid), and mirror A5 and B3 wording into both.

Items in (b): 10 (B1 to B10).

---

## (c) INTERNAL DOCS

None of these is read by buyers; they steer the next agent, so a wrong line costs a session. "Replace" gives the fact to put in, not always a full sentence.

**C1. CHANGELOG.md files 0.1.0's changes under 0.1.1. CONFIRMED.**
- The 0.1.0 build (081853b) carried an `## Unreleased` section of 9 bullets plus the older ones. The 0.1.1 release renamed `Unreleased` to `## 0.1.1 (2026-10-05)` wholesale, so every bullet from line 18 ("CrossfitTracker passes on Maestro 2.11.0") to line 63 ("Site: redesigned") except line 43 is a 0.1.0 change shown as 0.1.1, while `## 0.1.0` (lines 65-69) is a four-line stub. I diffed the bullets against `git show 081853b:CHANGELOG.md`; a code check agrees: `stall_s`, the blank-screenshot check, the `Self-hosted.*` translation and `isn't a valid licence` handling are absent from 0.1.0's `shotfleet.py` and present now.
- Replace: lines 7 to 12 and 43 are 0.1.1 (macOS 13 build, first-run, refunds, capture reliability, "could not read", "Found by running real apps", "Flutter and merged labels"). Move lines 18 to 63 except 43 under `## 0.1.0 (2026-10-05)` and drop the stub's duplicate summary or keep it as the first line.

**C2. CHANGELOG.md contradicts itself on Polar and the Maestro pin. CONFIRMED.**
- Line 24: Polar and Lemon Squeezy code removed. Line 50 (older bullet, same section): `Polar and Lemon Squeezy keys still work.` Line 54: `Polar added as a store`. Line 36: `doctor --fix` installs `Maestro 2.0.10 pinned by SHA-256`; line 22 says 2.11.0 is installed.
- Replace: append `(changed later: see the Polar bullet above)` or edit the three bullets to past tense. Lines 19 and 20 quote claims counts (`46 of 126`, `48 of 126`) that were true on the day; add "on that day".

**C3. CHANGELOG.md `Unreleased` is missing #68. CONFIRMED.**
- Only #69 is listed. README:92, SKILL.md:76 and `skill/shotfleet/references/ci.md:61` already describe #68 (`--json` prints one merged document plus `reports`).
- Add: `- **--json covers every report:** with several reports (several device_types, both platforms, Play phone and tablet sets) the document merges screenshots, problems and notes and adds reports, one {report, problems} each; with one report nothing changes. #68.` Optional tool lines: `tools/macho-minos.py`, `tools/ios27-repro.sh`, the manual `macos-compat` workflow.

**C4. CHANGELOG.md 0.1.1 line 7 is out of date and the section lacks three facts. CONFIRMED.**
- Line 7: `not run on a Mac older than macOS 27`; since then the live 0.1.1 ran on macOS 14.8.9 and 15.7.9 runners (install, `--version`, `doctor`, `check`). It also says "minimum macOS 11" for the standalone Python; the declared minimum is 13.0 (two files at 11.0, the `ocr` helper at 13.0).
- Missing from 0.1.1: the Catalan difference between macOS 14 and 15 (`research/limits-catalan-check-macos-2026-10-05.md`), iOS 27 on one simulator (78 s, 0 problems), the line `Built for macOS 13 or later on Apple silicon; tested on macOS 27.` in README and docs.

**C5. STATUS.md says 0.1.0 is the live release. STALE. CONFIRMED.**
- Line 7: `As of 2026-10-05 (main 533299e): shotfleet 0.1.0 is LIVE`; line 13: `/download/VERSION` = 0.1.0, tarball 9.7 MB; line 14: `Built from main 081853b`; line 16: gate evidence for 0.1.0 only.
- Replace with: 0.1.1 live since 13:27 (Cloudflare version 65c62221, rollback 609fa866), tarball 10,705,287 B sha256 6f6b5bfc..., pkg 10,723,486 B, built from commit e2e1998 (main 2ccda21) with standalone Python 3.14.2, minimum macOS 13; gate 65 of 65 in 54 min 57 s (iOS pinned to 26.4); smoke 36/0; macOS 14.8.9 and 15.7.9 hosted runs; main at 44cd5f2. Pointer: `research/release-0.1.1-evidence-2026-10-05.md`. Keep the 0.1.0 text as history ("live 08:02 to 13:27").

**C6. STATUS.md "Next release, 0.1.1" is done. STALE. CONFIRMED.**
- Lines 31 to 35: `Open PRs that change shotfleet.py: #29, #31, #44, #37`, and the "known issue" that `check` reports a false "no text found" for the Arabic screen. #31 and #37 are merged (git log; #29 was stacked under #31, INFERRED merged with it), #51 fixed the false "blank", 0.1.1 shipped. Only #44 is open (Android UI-tree text, conflicts with main).
- Replace with the 0.1.2 pointer: `research/0.1.2-plan.md` (pipeline A1 to A6, then B1 to B4 where B1 `--json` is merged (#68) and B2 is half done (#69 is wording; an invalid key still runs 2 languages and exits 0), PR #44 last) and the unproven list: macOS 13 and 26.0 to 26.2, a clean Mac, a refunded key on the real API, 4 simulators on iOS 27.

**C7. STATUS.md claim counts. STALE. CONFIRMED.**
- Line 34 and 69 (R6) and 106 (G1 row): `46 of 126 claims`. Register today: 131 rows; proven 60, fixed 22, evidence 27, partial 17, unverifiable 2, untested 1, removed 2; green 82, not green 47. Row 11 (line 53) ends at 126. Refresh with `tools/status.sh --quick`.

**C8. STATUS.md "What is left to do" and the file's own changelog. STALE. CONFIRMED.**
- Add to "Manu only": email the 0.1.0 and 0.1.1 buyers one update line (0.1.2 plan, C); an older-Mac or VM test for macOS 13 and 26.0 to 26.2 (`docs/device-wishlist.md` row 1); the owner items of `docs/owner-note-0.1.1.md` (who makes the paid test sale, a postal address, the policy after 14 days); the privacy waitlist text (D1).
- Line 123 (`Changelog of this file`) ends at "0.1.0 live"; add a 2026-10-05 line for 0.1.1.

**C9. docs/handoff.md section 13 and neighbours. STALE. CONFIRMED.**
- Lines 155 to 161 say 0.1.0 is live and that 0.1.1 is "next release" with PRs #29, #31, #44, #37 open; line 158 lists the iOS 27 runtime as an open item although one simulator passed (line 139 says so). Add a section "State after 0.1.1": the paragraph of C5, the hosted-runner result, the Catalan finding, the Gradle-daemon lesson (`gradle --stop` per version), pointer to `research/0.1.2-plan.md` and `docs/refund-runbook.md`.
- Line 96 says the marketing and `site/public/alternatives.html` pages "still say not yet run on a real Flutter or React Native app" and were left alone on purpose. alternatives.html is public and wrong (A1): reword the line to say it was fixed once A1 is done.

**C10. docs/compat.md: header date and missing platform rows. STALE. CONFIRMED.**
- Line 3 `Checked 2026-10-03`; line 49 `Xcode, iOS Simulator runtimes, macOS | not checked in this environment` is wrong now. The Result cell of the Xcode 27 row (line 47) opens with "iOS 27 not run" and a few sentences later says iOS 27 works on one simulator and one language; make the cell say the second.
- Add rows: macOS 27 (every run to date), macOS 14.8.9 and 15.7.9 (live 0.1.1: install, `--version`, `doctor`, `check` on 2 PNGs, hosted runner 2026-10-05; Catalan read on 15, not on 14), macOS 13 and 26.0 to 26.2 (untested; 0.1.0 very probably fails to start there: 52 of 56 Mach-O files at macOS 27.0 and Expat symbols that macOS below 26.3 lacks, INFERRED), Xcode 27.0 only (26.x unknown, 16 and older need `device_type`), Python (0.1.1 bundles standalone 3.14.2; 0.1.0 had Homebrew 3.14.8), and under Maestro 2.0.10 the quiet re-measure of 2026-10-05 (iOS 404 s, Android phone 415 s, no retries) next to the 2.11.0 retry result.

**C11. docs/linux.md:68. STALE. CONFIRMED.** `Maestro 2.0.10: the tested version` becomes `Maestro 2.0.10 and 2.11.0 are tested; doctor --fix installs 2.11.0`. (`tests/test_handoff_docs.py` only checks paths in backticks, so no test pins this line.)

**C12. docs/device-wishlist.md row 1 and the sources line. STALE. CONFIRMED.**
- Row 1 asks "Does the 0.1.0 folder start?" and says "the site names no minimum". README and docs now name it, and macOS 14.8.9 and 15.7.9 are answered for 0.1.1. Left: macOS 13, macOS 26.0 to 26.2, Gatekeeper on a browser download, a clean user account, `flock` on `/tmp` under the hardened runtime. Line 5 `all on origin branches until merged`: the platform, capture, check, first-run and refund notes are in `research/` on main now (INFERRED for the refund note; check `ls research`).

**C13. docs/agent-tasks/README.md. STALE. CONFIRMED.**
- Tasks 01 (Maestro 2.11.0), 03 (real framework apps) and 04 (Xcode 27) are done (`docs/handoff.md` items 1, 3, 12); the README table still lists them as open "why it is open". The line about a "Team and CI interest block ... site has WAITLIST/SALE markup that `packaging/go-live.sh` rewrites" is moot: go-live ran. Mark done tasks with a date and the evidence file.

**C14. LAUNCH.md is a pre-go-live runbook. STALE AS A STATUS, USEFUL AS A RUNBOOK. CONFIRMED.**
- Sections 4 to 7 ("Check the live product, then rehearse", "Go live (the one-shot)") describe steps that ran on 2026-10-05; line 83 says "the waitlist page is still what visitors see". Put one status line at the top: `Go-live ran 2026-10-05 (5fa4f7c, 5bbec86); sections 4 to 6 are the record and the template for the next release; section 8 (purge the waitlist 30 days after the launch email) is still live and is a promise on the privacy page.`

**C15. research/ has no index, and three notes carry their own stale status. CONFIRMED.**
- `ls research` lists about 60 files, 14 of them dated 2026-10-05, and no README. Add `research/README.md`: one line per note, with its date, what it decided and whether it was applied (for example: `limits-platform-reach-2026-10-05.md` applied by 0.1.1 and #55; `limits-catalan-check-macos-2026-10-05.md` caveat NOT applied; `limits-first-run-2026-10-05.md` messages applied, README quickstart NOT applied; `refund-process-2026-10-05.md` terms applied, runbook in docs/, postal address and consumer-rights lines NOT applied; `0.1.2-plan.md` B1 done).
- `docs/owner-note-0.1.1.md` last line says the notes are "on their draft PR branches until merged": merged now (INFERRED for each; `git log` shows #55, #56, #57, #58).
- `research/0.1.2-plan.md` "Known small defects: --json prints only the last report": fixed by #68; the "invalid SHOTFLEET_KEY silently runs 2 languages" line: only the wording is fixed (#69), the behaviour is not.

**C16. tests/claims.json proof text to refresh (read-only for this audit; a refresh agent edits it with the sentences). CONFIRMED.**
- C071 proof (33 is macOS 27; hosted 14 and 15 runs); C131 proof (already cites the hosted runs; add which runner images); C126 proof (Mac run 2026-10-03 on Maestro 2.0.10, not 2.11.0); C066 proof (hosted installs, A7); C007 and C105 proof (the re-measure ran on 2.0.10, B7); C035 `where` (alternatives.html, A1); C031 `where` (docs.html heading, A4). No status needs to move: nothing here becomes `proven` without a device or a second person.

**C17. Low: dated planning files. INFERRED.**
- `DISTRIBUTION.md:50` ("Only needed once the founder sale opens ... Until then the waitlist is enough"), `PLAN.md:35` (`Cloudflare Worker + KV waitlist`), `MARKETING.md:41` (`email the waitlist`) describe a pre-sale state. Add "history" to their first line or leave them; they do not steer anything today. `MARKETING.md` and `marketing/` are the owner's; no edit proposed.

Items in (c): 17 (C1 to C17).

---

## (d) NEEDS THE OWNER'S SAY

Public-facing legal, price, refund, licence and marketing wording. Listed, not changed. A refresh agent must not touch these without a yes in chat.

**D1. privacy.html still describes a waitlist. CONFIRMED text; whether it is still true is INFERRED.**
- Lines 36, 54-61, 64 and 67: `the only things stored are ... what you send when you join the waitlist`, a "When you join the waitlist" section, `To send you one email when shotfleet is available to buy`, and the promise `I will delete the waitlist within 30 days after I send the launch email`. The live page has no signup form (`LAUNCH.md` smoke check "no waitlist form"; index.html has none), but `forms.js` and the worker still carry the endpoints and the KV data exists until `site/signups.sh --purge-waitlist` runs (LAUNCH.md section 8). I do not know whether the launch email went out, so I cannot say whether the 30-day clock is running.
- Options for the owner: (1) leave it while the list exists and purge on schedule, then remove the sections in the same commit as the purge; (2) rewrite now in the past tense ("people who joined the list before the launch"). Claims C078, C086 quote this page; `tests/test_claims_site.py` and the worker tests pin parts of it.

**D2. terms.html states the refund behaviour as fact; it is inferred from Gumroad's source. CONFIRMED.**
- Line 52 area: `A refund ends the licence. The key stops unlocking every language and export the next time shotfleet checks it with Gumroad, about once a week (up to 30 days later if the Mac is offline)`. STATUS gate 5 and claim C047 (`partial`): "a refunded key being refused" has not been seen on a live key (needs a paid sale by a second person, `docs/refund-runbook.md`). The full-refund-disables-the-key rule is read from Gumroad's published code. Options: keep (the direction is the honest one for the buyer), or add "should"/"as far as I know" until the first real refund. Also open from `research/refund-process-2026-10-05.md` (lawyer or owner): a postal address on terms and privacy (Dutch civil code 6:230m), the EU withdrawal sentence, the "nothing here limits your statutory rights" line near "No warranty", and what happens after day 14 (only Gumroad's own 90-day discretion is stated).

**D3. Putting the macOS line on the home page, JSON-LD, llms.txt and alternatives.html. CONFIRMED gap; the decision is the owner's.**
- `docs/owner-note-0.1.1.md` item 1: "decide when it goes up". README, docs.html and the Gumroad page carry `Built for macOS 13 or later on Apple silicon; tested on macOS 27.` Adding it to index.html (price lede, "Not for you if"), the JSON-LD `softwareRequirements` and llms.txt is a public change on the sales page, so it waits for the OK (B3).

**D4. The range stays "13 or later; tested on macOS 27". Recorded, not reopened.**
- Decided today not to widen. What the hosted runs support at most: "installs, starts, runs doctor and check on macOS 14.8.9 and 15.7.9" (not simulators, Gatekeeper, macOS 13 or 26.0 to 26.2). If the owner later wants a sentence like that on the site, C131 and its test (`tests/test_platform_reach.py`) change with it.

**D5. Home-page numbers and the claims behind them. CONFIRMED facts; wording is the owner's.**
- index.html:144, :155 and alternatives.html "9 minutes on iOS and 15 on Android" (C007, C105, also quoted in `marketing/launch-posts-v2.md`). They are conservative against the 2026-10-05 re-measure (iOS 404 s, Android phone 415 s, 19 languages, Maestro 2.0.10, load 86 to 497) but the app now ships 19 languages, the run is "18 x 4" and the installer fetches Maestro 2.11.0 (B7). Options: leave as is (my reading: safest, C007 stays `evidence`), or add "Maestro 2.0.10" to the "Measured on my own apps" line. No marketing post is touched either way.

**D6. The licence fails open when `SHOTFLEET_KEY` is set and Gumroad is unreachable. EXISTING DESIGN; nothing proposed. CONFIRMED that no document claims otherwise.**
- README:116 and docs.html:243 say "if the licence server cannot be reached the job is not failed". The 30-day offline limit (index.html:319, terms.html, `references/licence.md:36`) is described for an activated Mac and never promised for a CI key. If the owner ever changes the design, README:116, docs.html:243, terms.html and `references/ci.md` change together.

**D7. Public setup advice that changes order (B9).** Moving `activate` after `doctor` and `init` in the README quickstart is the owner's call because it changes how the first five minutes read; the note it comes from is `research/limits-first-run-2026-10-05.md`.

**D8. Founder price mechanics. CONFIRMED text; mechanics need the owner.**
- Public pages say "$29 for the first 100 buyers, then $49" and "the first 100 buyers pay the founder price" (C042, C056); CHANGELOG line 20 says the sentence was kept free of a code on purpose. The Gumroad side is FOUNDER29 ($20 off, limit 100); STATUS says it applies by itself even with the discount-code box set to "Never", but the brief for this audit calls it "code FOUNDER29". The owner should confirm that a buyer never has to type a code, because if one is needed the pages promise something the checkout does not do. No edit proposed.

**D9. Email to 0.1.0 and 0.1.1 buyers with the update line (`research/0.1.2-plan.md` C).** The owner sends it; the same line goes in the docs (B1).

**D10. Competitor facts on alternatives.html are dated 2026-10-02. LOW. INFERRED.**
- `Checked on 2026-10-02 from each tool's own pages`: prices of ButterKit ($99 once) and AppScreens ($99 or $180 a year) are third-party facts that can move. Not stale today; recheck before the first launch post is read widely. Marketing posts: no edit proposed, and `marketing/` was only read for context.

Items in (d): 10 (D1 to D10).

---

## (e) RECOMMENDED ORDER AND FILES

**Order for one agent in one pass (device-free, targeted tests only, `[skip ci]`, no deploy):**

1. **Remove what is false or overstated** (public, small, no owner decision): A1 (alternatives.html:88 plus `tests/test_site_audit.py:297` plus C035 `where`), A2 (README:63, C126 proof), A3 (docs.html:259), A4 (four files and the docs.html heading), A6 (docs.html:224 and `notes` in README:92), A7 (three places, C066 proof). Run `python3 -m unittest tests.test_docs tests.test_claims tests.test_site_audit tests.test_agent_skills tests.test_cli_claims`.
2. **Platform and version truth** (README, docs.html, skill, with claim proofs): A5 and C071, B2, B3 (README and docs.html only; the home page waits for D3), B7 (docs.html versions and the timing sentence), C131 and C007/C105 proofs.
3. **What is missing**: B1, B4, B5, B6, B8, B10, then B9 if D7 is a yes. Mirror every README sentence in docs.html and in the skill; do not paraphrase a quoted claim sentence (`tests/test_claims.py` tells which row broke).
4. **Internal docs**: C1 to C4 (CHANGELOG), C5 to C8 (STATUS), C9 to C15, C17; `research/README.md` last, because it lists what steps 1 to 3 applied.
5. **Then the coordinator**: one full local gate when the Mac is quiet (`tools/check-claims.sh`; this audit did not run it), the owner's yes on (d), and a site deploy only by the owner's approval, from a tree that holds `site/public/download` (a deploy from a tree without it can delete the downloads: `research/release-0.1.1-evidence-2026-10-05.md`). Edits to `site/public/*` do nothing until deployed; README and docs are what the next release tarball and the skill ship.

**Files a refresh touches**

Public: `README.md`, `site/public/docs.html`, `site/public/alternatives.html`, `site/public/llms.txt`, `skill/shotfleet/SKILL.md`, `skill/shotfleet/references/ci.md`, `config.md`, `licence.md`, `troubleshooting.md`, `docs/AGENTS-snippet.md`. Only with the owner's yes: `site/public/index.html` (D3, D5), `site/public/privacy.html` (D1), `site/public/terms.html` (D2).

Tests and register: `tests/claims.json` (rows C031, C035, C066, C071, C126, C131, C007, C105; optional new rows for B1, B2, B4), `tests/test_site_audit.py` (line 297 and any llms.txt or alternatives asserts), `tests/test_docs.py` (only if the "Last checked" line changes; it must match VERSION 0.1.1 and the top CHANGELOG heading), `tests/test_agent_skills.py` and `tests/test_cli_claims.py` (run, edit only if a README quote moves).

Internal: `CHANGELOG.md`, `STATUS.md`, `docs/handoff.md`, `docs/compat.md`, `docs/linux.md`, `docs/device-wishlist.md`, `docs/agent-tasks/README.md`, `LAUNCH.md`, `docs/owner-note-0.1.1.md` (last line), `research/0.1.2-plan.md` (two statuses), new `research/README.md`.

Not touched by anyone: `marketing/**`, `site/draft/**`, `shotfleet.py`, `packaging/**`.

**Counts:** (a) 9, (b) 10, (c) 17, (d) 10.

**Not checked (so nobody assumes it was):** the Gumroad product page itself (not in the repo); any live page (I read the repo copies; the live site equals the repo at the 0.1.1 deploy plus nothing since, INFERRED from the evidence note); the `site/draft/` pages; claims rows other than the ones named; whether `tools/status.sh` numbers match today (not run).
