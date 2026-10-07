# 3. The check pipeline

Back to the [index](../ARCHITECTURE.md). Anchors are `shotfleet.py:LINE` at `origin/main` `285e099`.

`check` answers one question for every screenshot: **does this image show the app in the language of the folder it sits in?** It also finds copies,
missing screens and store-rule violations. It runs after every `run` and, for free and with no devices, on any folder of screenshots.

The entry points are `check_any` (`:5336`, routes by folder layout) and `cmd_check` (`:3329`, does the work for one report). `main_dispatch`
(`:5378`) calls `check_any`. The MCP `check` tool calls it too.

## 3.1 Which screenshots, which app, which store

**Finding screenshots** (`find_screenshots`, `:3011`). The first pattern that matches files wins:

| Order | Pattern (relative to the folder) | Layout |
|---|---|---|
| 0 | both `screenshots/` and `metadata/android/` exist | A fastlane folder for both stores: `--app` (or run info) picks the half; with neither, `Fail` asks for one |
| 1 | `raw/*/*` | shotfleet's own output |
| 2 | `metadata/android/*/images/<play folder>/*` | fastlane supply (`phoneScreenshots`, `sevenInchScreenshots`, `tenInchScreenshots`) |
| 3 | `*/images/<play folder>/*` | supply, folder is already `metadata/android` |
| 4 | `screenshots/*/*` | fastlane deliver |
| 5 | `*/*` | plain `<locale>/` folders |
| 6 | `*` (flat) | one language's images; needs `--locale`, otherwise `Fail` says so |

PNG and JPEG count. A folder label must look like a locale (`LOCALE_LABEL`, `:2984`) or be a known alias, so `default/`, `ipad_only/`, `appleTV/` are
ignored. Names are compared across languages through `shot_key` (`:2993`): fastlane screengrab's 13-digit millisecond timestamp
(`01Home_1773697012807.png` is `01Home.png`) and supply's `_<locale>` suffix (`1_de-DE.png` is `1.png`) are dropped, the second only when
**every** file in that folder ends with that locale, so two real screens cannot merge. A language with the same screen twice under two timestamps is
reported (see rules). `check_any` (`:5336`) loops over several Play sets (phone, 7", 10" each with its own report folder) and over multi-device
sub-folders (`device_runs`), and adds the "iPad set missing" check across them.

**Which app's strings** (the language evidence). In order: `--app` (an `.app` or `.apk`; the layout must not contradict it); `--strings` globs;
`run.json` in the folder (`strings` globs if the run used them, else the build path); otherwise `check_build` (`:5307`) looks where `init` looks (newest
Debug simulator build for this folder's Xcode project, a Gradle debug APK, a Flutter or React Native project's translation files) and says in one line
what it chose or that it found nothing. With nothing at all, only language detection judges the language and the output says so. Then
`shipped_locales` filters out libraries' languages.

**Which store.** `android` is decided by `--app` suffix, then `run.json`'s `platform`, then layout (a `metadata/android` tree means Play, a
`screenshots/` folder means App Store), then the sizes (`store_from_sizes`, `:4575`: all App Store sizes means App Store, none means Play, a mix
means unknown and each screenshot is judged against both stores, a problem only when neither takes it, with a note saying so).

## 3.2 Where the text of a screenshot comes from

For each screenshot `check` wants "the lines of text that are on screen". Three sources, strongest first:

1. **The app's own text (`<shot>.texts.json`)** written during the run (iOS from the XCUITest driver, Android from Maestro's hierarchy; see
   [02](02-capture.md)). Exact Unicode, any script, no recognition errors. `screen_text` (`:3186`) loads it and returns the same dict shape OCR does with
   `"ocr": "app"`. It is only used when it proves something (`usable_text`, `:3195`): it must contain at least 2 lines that exactly equal strings of
   some language, because a screen made mostly of user content tells nothing about the language and is read by OCR as well. Games, canvases and
   unlabelled UI report no text at all and fall through to pixels.
2. **macOS Vision text recognition** through the Swift helper `ocr.swift`.
3. **Tesseract**, or any command given with `--ocr-command` / `SHOTFLEET_OCR`.

`check.json` records which one each screenshot used (`evidence`: `"hierarchy"` for the app's text, `"ocr"` for the rest).

### The Swift helper (`ocr.swift`)

A 56-line command-line program, not a library. Three modes:

- `ocr <image>`: runs `VNRecognizeTextRequest` (accurate level, automatic language detection) and prints one JSON object:
  `lang` and `langs` (the top three hypotheses from `NLLanguageRecognizer`, with confidence), `chars`, `text` (one line per recognised line),
  `lines` (each with height `h` and `top` as fractions of the image), and `caption` / `caption_lang` (text in the top third at least twice as tall as
  the median line, for framed marketing screenshots; its language is only reported when it is 8 or more characters and detected at 0.8 confidence).
- `ocr --langs`: the languages this Mac's Vision can read (33 base codes on macOS 27; fewer on older macOS).
- `ocr --warmup`: draws the word "Ready" in memory and reads it. Its only purpose is to make macOS compile its text model once, in a process of its
  own, before the parallel reads start.

`ocr_tool()` (`:2763`) returns `sys._MEIPASS/ocr` in a released build (prebuilt, signed, `swiftc -target arm64-apple-macos13.0`) and otherwise
compiles `ocr.swift` on demand into `.build/ocr` (built to a temp name and renamed, so two checks at once never run a half-written file).

### Vision's waiting problem and how `check` copes

Vision on a Mac compiles a model on first use through a root service, `ANECompilerService`. Measured: 17 to 188 s on a loaded Mac, and once about 40
minutes on a quiet one. Early versions of `check` gave up after 60 to 90 s and blamed the user's Mac. The current design (all of it in the
`# ---------- check ----------` section, `:3044-3228`):

- `warm_up_ocr` (`:3126`) runs one `ocr --warmup` before anything else. It waits past its timeout as long as `ANECompilerService` is using the CPU
  (`ane_state`, `:3051`: a compile making progress, not a stuck Mac) up to `OCR_COMPILE_PATIENCE_S = 360`. A helper that exits without an answer is
  started again every `OCR_RETRY_S = 10` s.
- **One lock per Mac** (`ocr_warmup_lock`, `:3102`): an `fcntl.flock` on `/tmp/shotfleet-ocr-warmup.lock` (opened by `open_lock`, no symlink followed, 0o600). Two checks at once (another session, CI
  and your own run) take turns, so they do not pile compiles onto one service. The helper inherits the lock file descriptor, so a helper left running
  keeps the lock until its compile ends. If nothing is compiling, the waiter does not wait at all.
- **One budget per check** (`OCR_BUDGET_S = 480`, `ocr_budget`, `:3093`, a context manager used as a decorator on `cmd_check` and `check_any`):
  everything that waits on Vision (the warm-up, the lock, retries inside each read) counts against 8 minutes in total. Nested checks (several
  device folders, Play's three sets) share the outer budget.
- `read_text` (`:3204`) reads one image with a 120 s timeout and retries once; a non-zero exit while a compile is running is waited for like the warm-up
  and ends as `OcrBusy` when patience or budget runs out; otherwise it is an error with the helper's stderr.
- When the budget is spent and no other reader exists, `check` **finishes anyway**: screens with the app's own text are judged from it; store
  sizes and missing screens are still checked; the screens nobody could read are marked "not verified (macOS text recognition was busy)" in the
  console, at the top of `index.html`, in `notes`, and in the `unverified` list of `--json`. That list changes nothing about the exit code unless
  `--strict` is given, in which case it exits 1. Unread screens that are byte-identical across languages get a note, not a problem, because only
  text can tell a copy from a legitimate no-text screen.
- If Tesseract (or `--ocr-command`) is installed it is used instead of waiting (`warm_up_ocr(..., timeout=90 if fallback else 600)`), and the output
  says the fallback was used and that it reads fewer scripts.

Why not a different reader: a CPU-only reader (PP-OCR through ONNX Runtime) fits, but not in the 10 MB tarball; a Tesseract build from source is the
second choice. Both are in `research/ocr-cpu-reader-2026-10-06.md`. Rebooting the Mac is explicitly not an accepted remedy
(`research/workarounds-text-recognition-2026-10-05.md`).

### Tesseract and external readers

`TESSERACT_COMMAND` is `tesseract {image} stdout -l {tesseract_with_english}`. `external_ocr` (`:3253`) fills `{image}`, `{lang}`, `{tesseract}`,
`{tesseract_with_english}` and runs the command with `OMP_THREAD_LIMIT=1` (Tesseract starts one OpenMP thread per core and four processes at once spin
against each other: 73 s for four screenshots instead of 2 s on 4 cores). `TESSERACT` (`:3231`) maps ISO codes to Tesseract's data names. Rules for
when it is used:

- On Linux it reads everything (`vision_available()` is `sys.platform == "darwin"`).
- On a Mac it reads what Vision cannot (`unreadable(label)`: a language outside `readable_languages()`), automatically when Tesseract is installed
  and the user gave no command (`auto`), measured as 84 of 85 languages verified instead of 66.
- For Japanese, Korean and Thai Tesseract's own script detection (`tesseract_script`, `:3243`, osd data, trusted only at confidence 1.0 or more; it
  was right on 142 of 144 real screenshots) is the evidence, because Tesseract names no language.
- Tesseract joins labels on one visual line ("Alle Übungen WODs"), so `judge_screen` also searches for each string inside the joined text with word
  boundaries (`v in text` first, then the regex: building a regex per string, language and screenshot cost 3 to 5 CPU minutes on 220 screenshots, fixed in 0.1.5).
- `read_nothing` (`:2884`): an empty result from Tesseract or an external reader is "unverified", never "blank" (an Arabic Android screen came back
  empty). An empty result from Vision or from the app's own text stays a finding.

## 3.3 Judging the language (`judge_screen`, `:2890`)

Generic language detection is unreliable on short UI labels (macOS read a Russian tab bar as Kazakh, a Russian screen with English job titles as
99 percent Kazakh). So the main evidence is not "which language does this look like" but **"how many recognised lines are exactly strings of the
app in language X"**:

1. `string_tables(strings)` (`:2869`) builds, for each locale, a `Table` (a frozenset of normalised strings, with fallback to parent locales) plus one
   compiled regex for its **format strings** (`Day %d of 15`). Placeholder-only formats are excluded; a text placeholder needs 8 or more letters
   around it, a number placeholder 3, so `%@ atras` cannot make Spanish look Portuguese.
2. All recognised lines are normalised by `norm()` (`:2811`: NFKD, accents removed, casefold, bidi and zero-width marks removed, native digits to ASCII,
   single spaces) so OCR and string tables agree.
3. `score[o]` = number of lines that are one of locale `o`'s strings, plus lines matching its format regex.
4. `best = max(score)`; the screen "shows" the expected locale `lp` if `lp` ties for best, else the winner.

Then the verdict:

| Situation | Verdict |
|---|---|
| no characters read, and this language is not one the reader can read | `(None, None)`: not provable, not a problem (Hebrew, Georgian, Burmese often read as nothing) |
| no characters read, language is readable | problem: "no text found (blank or still loading?)" |
| `best < 2` (one short label proves nothing: "Training starten" is German and Dutch) | fall back to detection, with guards: script check for ja, ko, th (3 or more characters in the script range passes); a Cyrillic neighbour (`CYRILLIC` set: ru, uk, be, bg, kk, mk, sr, ky, mn, tg) passes only when the one matching line belongs to the expected language and no other; `TWINS` (`ms`/`id`, `hr`/`sl`, which detection cannot tell apart) pass; otherwise a problem only if detection names another language at 0.8 or more while giving the expected one under 0.2 |
| the language cannot be read at all (Greek, Hebrew, most Indic) | only "this looks like English at over 0.9" is reported; otherwise unverified |
| `best >= 2` and another locale `got` beats `lp` by 2 lines (when `score[got] < 3`) or 1 line (with plenty of evidence, which separates `en-GB` "Colour" from `en-US` "Color") | problem: "shows `got` strings (N lines) more than `lp` (M)" |
| otherwise | pass |

`LATIN_UNLISTED` (ca, hr, hu, sk, sl) are Latin-script languages Vision lists no model for but reads with its Latin model, and NaturalLanguage tells
apart from English, so they are judged like listed ones (`can_read`, `:2797`); Hungarian loses accents, which `norm` absorbs.
`caption_problem` (`:2962`) rewrites a "shows X strings" verdict into "the caption is in X but the app UI shows ..." when a marketing caption over
the device is in the language the UI should be (a translated caption over an untranslated app). There is deliberately **no** "caption in the wrong
language" problem on its own: detection misreads short captions.

Measuring this: `tools/langmatrix.py` renders real UI strings for every language AndroidX is translated into (about 85) and asks `judge_screen`
three questions per language (right screen filed right passes; English screen filed as L is flagged; a close language's screen filed as L is flagged).
`research/e2-tesseract-parity.md` and `research/limits-check-quality-2026-10-05.md` record the false-positive and false-negative hunting.

## 3.4 The rules, in the order `cmd_check` applies them

Each rule appends a line to `problems` (fails the check) or `notes` (does not). Exact wording matters: the review skill
(`skill/shotfleet-review`) tabulates these lines and `tests/test_agent_skills.py` keeps the table in step with the code.

| Rule | Condition | Line (fixed part) | Kind |
|---|---|---|---|
| App has no translation for a listing | the folder's locale maps to no language in the app's strings (`app_locale`, `:3034`) | `<l>: the app has no <l> translation, so this listing shows another language; ...` | problem |
| Wrong language | `judge_screen` | `shows <x> strings (N lines) more than <y> (M)`; `text looks like '<x>', expected '<y>'`; `text looks like the <script> script, expected '<y>'`; `the caption is in <x> but the app UI shows ...` | problem |
| No text | `judge_screen`, reader can read | `no text found (blank or still loading?)` | problem |
| Blank frame | `blank_screenshot` (`:4643`): the middle band (rows 12 to 88 percent) has 3 or fewer distinct rows; PNG only, pixels not OCR | `blank: nothing is drawn on it yet ...` | problem |
| Unreadable, not blank | reader found nothing but the picture is not flat | `could not read this screenshot ..., so its language is unverified` | note |
| Not verified (OCR busy) | budget spent, no other reader | `not verified (macOS text recognition was busy)` | note and `unverified` |
| Android system dialog | recognised text has "isn't responding" / "keeps stopping" / "has stopped" **and** a Close app / Wait / App info button (`system_dialog`, `:2949`; English only) | `an Android system dialog covers the screen` | problem |
| System banner | a recognised line in the top 20 percent matches "Ready for Apple Intelligence" (`system_banner`, `:2956`; needs Vision's line positions, so not for app-text or Tesseract reads) | `a system notification banner covers the top of the screen` | problem |
| `[expect]` content | `check_content` (`:3297`), rules from `content_rules` (`:3285`) | `expected "t" on screen`, `expected one of ...`, `"t" must not be on screen` | problem |
| `[expect]` cannot verify | text in a script the reader cannot read (`ocr_can_read`) and evidence not from the app | `could not verify, ...` | note |
| `[expect.X]` typo | no screenshot named `X` | `[expect.X] matches no screenshot; did you mean ...?` | problem |
| Identical images | same sha256 prefix, 40 or more characters read, in two or more **different** app locales (`en-GB` and `en-US` both showing English is fine) | `identical image in N languages: a, b` | problem |
| Missing screen | the union of screen names across languages minus this language's | `<l>: missing a.png, b.png` | problem |
| Same screen saved twice | two files with one `shot_key` (screengrab timestamps) | `<l>: a_<t1>.png, a_<t2>.png are the same screen saved 2 times ...` | problem |
| Store size, count, alpha | `store_rules` | see [04](04-export-and-store-rules.md) | problems and notes |
| Folders not from this run | `run.json` lists the languages captured; other folders exist | `<l> is not from this run ...` | note |

`caption`, `expect` and the rest depend on the evidence type: **the app's own text is exact** (a missing `all` text is a real problem), OCR may miss
characters (a missing text it cannot be sure about is only "could not verify").

Blank and copy detection use pixels and hashes, not OCR, on purpose: "only a flat frame is provably blank" and "a copy is a copy".

Run-side counterparts: during `run`, `blank_note` (`:4666`) makes a language **fail** (and be retried once) when any of its screenshots is blank,
because a first paint that comes after the flow's wait (Flutter debug builds, Compose) usually heals on a second attempt; the message tells the user
to `extendedWaitUntil` visible text before `takeScreenshot`.

## 3.5 Output of a check

- **Console:** `checked N screenshots in M languages: P problem(s)`, the problem lines, up to 12 notes (`... N more in check.json`), the report
  path, and, when screens are not verified, a loud `NOT VERIFIED:` line with what to do.
- **`check.json`:** see [01](01-code-layout.md#output-folders-and-files). Report folder: `--report`, else the run folder when it has `run.json`, else
  `./shotfleet-check`. A report is never written into the folder being checked unless that is the run folder.
- **`index.html`** (`write_gallery`, `:3557`): one row per language, one column per screen, flagged screenshots outlined in red **and** marked
  "problem" in words with the reason under the cell, alt text on every image, `lang` attributes, light and dark contrast that passes WCAG AA, keyboard
  focus rings. Images are referenced relatively (an absolute `file:` URL when they live outside the report).
- **`--json`:** stdout is exactly one JSON object `{"exit": N, "screenshots": [...], "problems": [...], "notes": [...], "unverified": [...]}`
  (`reports_json`, `:3318`). With several reports (several device types, both platforms, Play phone and tablet sets) the lists are merged and a
  `reports` array of `{"report", "problems"}` is added. With `exit` 2 the object has only `exit`.
- **Exit code:** 1 if there are problems, or if `--strict` and some screens are unverified; else 0.

## 3.6 Extending the check

- **A new rule:** add the condition inside the loop in `cmd_check` (or a pure helper next to `system_dialog`), append to `problems` or `notes`, and
  add a unit test in `tests/test_check_quality.py` or `tests/test_shotfleet.py` that feeds `cmd_check` a small folder with a faked reader
  (`fake_vision()` in `tests/test_cli_claims.py` is the pattern). If the rule is a public promise, add or update a claim row. Update
  `skill/shotfleet-review/SKILL.md` (the line table) in the same change; the skill tests will tell you if you forget.
- **A new language the reader cannot read:** add its code to `TESSERACT` (`:3231`), to `OSD_SCRIPT` if Tesseract needs script detection for it, and
  see whether the Docker image's `LANGS` (Dockerfile) should include the data.
- **A language detection confusion:** add the pair to `TWINS` (symmetric; detection cannot tell them apart) or, for a script family, to `CYRILLIC`
  style handling, with the measurement that justifies it in a research note. Do not loosen `judge_screen`'s thresholds without re-running
  `tools/langmatrix.py` and a real screenshot set.
