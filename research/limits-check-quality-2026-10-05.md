# Quality of `shotfleet check`: false problems and missed problems (2026-10-05)

Scope: how `check` reads a screenshot and decides "right language", "blank", "wrong language" and "content missing". Method: read
`shotfleet.py` (line numbers are on branch `claude/limits-check-quality`, after the fixes below), probe `judge_screen` and
`blank_screenshot` with small made-up inputs, and run Tesseract once on real Arabic screenshots already in the repo. No device,
simulator or emulator was used, nothing was pushed. The probes are fakes: they show what the code does with an input, not how often
that input happens on real screenshots.

## How the pipeline decides (short)

1. Where the text comes from (`cmd_check`, about 2483 to 2527): the app's own text (`.texts.json`, iOS only, used when it matches at
   least 2 strings: `usable_text` 2317), else macOS Vision (`read_text` 2326, one retry after 120 s), else Tesseract
   (`TESSERACT_COMMAND`, language pack `eng+<lang>`) when Vision does not answer in `warm_up_ocr` (90 s when Tesseract exists), hangs
   mid-check, or the language is one Vision cannot read.
2. `judge_screen` (2160): counts lines equal to one of each locale's strings. 2 or more lines decide the language. Fewer than 2 falls
   back to the language guess of the reader (`lang`, `langs`) which only Vision provides.
3. `blank_screenshot` (pixels, 3516 in the old file) can override any verdict with "blank".

## Findings

"FP" = flags a good screenshot, "FN" = passes a bad one. Fixed means a commit on this branch with a test in
`tests/test_check_quality.py`.

| # | Kind | What happens | Evidence | Input that triggers it | Status |
|---|---|---|---|---|---|
| 1 | FP | A fallback reader (Tesseract, `--ocr-command`) that returns nothing for a real screen is reported as "no text found (blank or still loading?)", a problem that fails the run. This is the 2026-10-05 Arabic fixture case. | `judge_screen` 2175 | Vision wedged, Arabic Android screenshot, Tesseract returns "" | Fixed (dbcea42): note "could not read this screenshot", exit 0. Still a problem when the pixels are flat |
| 2 | FP | Same family, other route: the fallback has no data pack for the language (`redo` skips it), so the result stays `{}` and also became "no text found" | `redo` 2522 | Vision wedged, Tesseract installed without `ara` | Fixed with 1 |
| 3 | FP | A screen Vision read fine before it hung is read again by Tesseract and its good text replaced by Tesseract's (possibly empty) text | `redo` 2522 (old condition `not use_vision`) | Vision answers for screenshot A, hangs on B | Fixed (9ed2015): a read that finished stands |
| 4 | FP | `[expect]` "all" lists: an empty read makes every expected text "missing", a problem | `check_content` 2411, called in `cmd_check` | `[expect.01_welcome] all = ["Next"]` and an unreadable screenshot | Fixed (033481a): unverified note |
| 5 | FP | Android dialog words in the app's own text: "Server isn't responding", "Your workout has stopped" were reported as an Android system dialog | `SYSTEM_DIALOG` 2211 | A network error screen in English | Fixed (c1374ad): needs a "Close app", "Wait" or "App info" line too. Cost: a dialog whose buttons OCR misses is no longer found |
| 6 | FN | Tesseract names no language, so `lang` is `None`; with fewer than 2 matching strings (or no `--app` at all) the screen passes as the right language | `judge_screen` 2194 to 2206 (`return lp, None`) | No `--app`, German text in the `en` folder, read by Tesseract (Linux, or Vision stuck): `('de', None)` pass | Partly fixed (813d8b1): without `--app` a note says the language was not checked. With `--app` and fewer than 2 matching strings it still passes silently (see "what remains") |
| 7 | FN | Tesseract on Arabic gives partial text mixed with Latin junk. It is "text", so the screen counts as verified Arabic. Measured once: `eng+ara` on the obytes iOS `ar-01_onboarding.png` and `ar-03_settings.png` gave a mix of correct Arabic words and noise | research/real-apps-2026-10-03/obytes-ios | Any Arabic screen on the fallback | Open, same cause as 6 |
| 8 | FP (theory) | `blank_screenshot` compares raw PNG rows, so a screen of a few vertical colour bars has identical rows and counts as blank | `blank_screenshot` (docstring says "horizontal stripes", the real weak spot is vertical) | 60x300 PNG, three vertical bars: `True` | Open. Never seen on a real screenshot |
| 9 | FN | `blank_screenshot` returns False for palette PNGs, interlaced PNGs, JPEGs and anything under 200 px tall, and a gradient or spinner screen has many distinct rows. "Still loading" screens with a spinner are not flat | same function | A splash with a spinner and no text | Open by design. Vision still says "no text found" for it, the fallback now only notes it |
| 10 | FP (unmeasured) | Nynorsk: the listing is `nn`, language detection says `nb`. `TWINS` only knows `ms` and `id` | `TWINS` 2060, `judge_screen` | `judge_screen("nn", nb text with lang nb 0.95, no strings)` gives "text looks like 'nb', expected 'nn'" | Open. Needs the real Vision language list and one Nynorsk screenshot before touching |
| 11 | FP (unmeasured) | Scripts Vision cannot read come out as Latin or other-script garbage. If detection says English at 0.9 or more, the screen is called English | `judge_screen` 2186 | Greek or Armenian screen on a Mac without Tesseract data | Open. all-languages.md measured Greek as `hu` and Armenian as `tr`, not `en`, so it is not shown to happen |
| 12 | FN | A flaky or slow Vision start (first compile after a restart) over 90 s drops the whole check to Tesseract when Tesseract is installed, which makes findings 1, 6 and 7 more likely | `warm_up_ocr(timeout=90 if fallback else 600)` | Mac just restarted, Tesseract installed | Open. Trade-off: waiting longer costs time |
| 13 | FN | Identical images across languages are only compared when the screen has 40 or more characters, so a short untranslated screen copied into another language is not found | `cmd_check` 2534 | 30 character screen identical in `de` and `fr` | Open by design (a Watch button can legitimately match) |
| 14 | FN | One-character lines (single Han characters, tab icons) are dropped from the string match | `judge_screen` 2165 | A CJK tab bar of single characters | Open, low impact: the longer lines still count |
| 15 | note | Languages Vision cannot read are skipped when Tesseract has no pack. The map `TESSERACT` has about 80 codes; a code not in it is passed through as a two letter code and never matches a pack | `tesseract_code` 2306, `TESSERACT` | `yi`, `cy`, `ga`, `mt`, `bs` and others | Open, only means "unverified" |

## What was fixed

Five commits, all on `claude/limits-check-quality`, each with tests (9 tests in `tests/test_check_quality.py`, fakes for the readers,
no OCR, no device):

1. dbcea42: the Arabic false problem. New `read_nothing(ocr)`: true when the reader was Tesseract or `--ocr-command` (`ocr: "external"`)
   or no reader had data. In `cmd_check`, "no text found" from such a reader becomes a note ("could not read this screenshot ...
   language is unverified") unless `blank_screenshot` (pixels) says the frame is flat, which is still a problem. A healthy macOS read
   that finds nothing stays a problem: that is the one case where the reader did look and the language is one it reads. The
   "macOS can't read the script of ar" line is not printed for these, because the script is readable and the reader failed.
2. 9ed2015: finding 3.
3. 813d8b1: finding 6, first half (a note when no strings are given).
4. c1374ad: finding 5.
5. 033481a: finding 4.

Decision to look at: finding 1 keeps "no text found" as a problem for a healthy macOS read of an unflat image. The task text says
"never a problem unless provably blank". I kept the macOS case because Vision looked at the pixels and found no text on a language
it reads, which is what a loading spinner screen is. If you would rather have it a note too, change `read_nothing` to
`return not ocr.get("chars")`; the cost is that loading screens with a spinner then pass, and the test
`test_macos_text_recognition_finding_nothing...` would flip.

## What remains and what it would take

- **Language proof on Tesseract (findings 6 and 7).** Tesseract gives words, not a language. Options: (a) Tesseract script models
  (`tessdata_best` `script/Arabic` and the like) plus `--psm 0` script detection, already used for ja, ko and th (`tesseract_script`,
  measured in research/e2-tesseract-parity.md: 142 of 144 right, thin margins); extend `OSD_SCRIPT` to Arabic, Cyrillic, Devanagari,
  Greek, Hebrew. That proves the script, not the language (Russian vs Ukrainian stay twins). (b) Run Python language detection on
  the Tesseract text: no stdlib option, a new dependency, and the README says short UI text defeats it anyway. (c) Hierarchy text.
- **Hierarchy text on Android (PR #44, branch `claude/android-hierarchy-text`).** If an Android run leaves `.texts.json` next to each
  screenshot as iOS does, Android takes the exact path (`screen_text`), OCR is only used where the tree is empty, and findings 1, 2,
  6, 7 mostly stop mattering for Android. It does not help Canvas, games, Flutter screens with no semantics, or screenshots from other
  tools (a folder with no run). It needs real runs on the branch to show the pairing of screenshot and text is right (review
  finding 4 is still open).
- **Blank detection (8, 9).** Needs real unfiltering of the PNG rows (about 25 lines) and a rule for spinner screens. Only worth it if
  the experiment below shows real frames that are wrongly judged.
- **Nynorsk and other twins (10).** Read `ocr --langs` on the Mac, put one Nynorsk screenshot through `ocr`, then decide whether `nn`
  and `nb` are twins.
- **A "verified by reading" count.** `check` now has three outcomes for a screenshot: judged, unverified by script (existing line),
  and could not read (new note). The summary line counts none of them. A line such as "judged 70, unverified 6" would let a user see
  at a glance how much of a clean run was actually proven.

## What to measure on real screenshots (not run)

Needs a Mac with Tesseract and the Android fixture or real-app screenshots already on disk (the 72 CrossfitTracker Android
screenshots, the obytes and wger sets in `research/real-apps-2026-10-0*`). No device is needed, only `check` on saved PNGs.

1. **Reader failure rate.** For every saved PNG, run Vision (`.build/ocr`) and `tesseract <png> stdout -l eng+<lang>`; record chars
   from each. Report per language: how often Tesseract returns under 10 characters when Vision returns 40 or more, and how often
   Tesseract returns junk (under half of Vision's lines equal to the app's strings). This says how common findings 1 and 7 are.
2. **Wrong-language detection on Tesseract.** Take each real set, file one language's screenshots under another's folder, and run
   `check --app` once with Vision and once with Vision forced off (stub `warm_up_ocr` to False). Count the planted mistakes found
   each way. Expect the two to differ for screens with fewer than 2 string matches (finding 6). Use at least 3 closely related pairs
   (de/nl, es/pt, nb/da) and 2 distant ones.
3. **Blank detector.** Run `blank_screenshot` over every saved PNG of the four real-app sets plus the fixture app (iOS and Android),
   plus a few frames taken on purpose with the app still loading. Expect 0 on finished screens; list any hit. Also list loading
   frames it misses (spinner, logo only), which sets whether finding 9 deserves a fix.
4. **Dialog words.** Grep the saved OCR text of all real screenshots for "isn't responding", "has stopped", "keeps stopping" and see
   whether any is app text (finding 5 says some can be) and whether any real emulator dialog lacks a "Close app" or "Wait" line.
5. **Nynorsk.** One `nn` screenshot of any app through `ocr`: the `lang` and `langs` it reports.

## Files

- `shotfleet.py`: `read_nothing`, `cmd_check` loop and `redo`, `system_dialog`.
- `tests/test_check_quality.py`: new, 9 tests.
- Not changed: README Limits and CHANGELOG. The README sentence about Tesseract ("verified by reading") is still accurate; a line
  in CHANGELOG under Unreleased for the five fixes is for whoever merges.
