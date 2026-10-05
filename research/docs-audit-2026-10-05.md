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
