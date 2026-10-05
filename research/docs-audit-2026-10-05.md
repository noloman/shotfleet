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
