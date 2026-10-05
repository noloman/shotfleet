# The wger Catalan screen on macOS 14, 15 and 27 (2026-10-05)

Research only: no code, README or site was changed. Device-free. Method: read the app's own Catalan strings, looked at the screenshot,
ran `ocr.swift` and `shotfleet.py check` on copies of two PNGs in a temp folder on this Mac (macOS 27.0), read `judge_screen`,
`read_nothing` and the `check` messages in `shotfleet.py`, and read Apple's documentation. macOS 14 and 15 were not available here;
what is said about them comes from the hosted-runner test in `research/limits-platform-reach-2026-10-05.md` (section "Hosted-runner
test of the LIVE 0.1.1 on macOS 14 and 15") and is marked as such.

Labels: **certain** = read or measured here; **inferred** = follows from code or from a measurement on another OS; **unverified** =
could not be checked.

## 1. Does the wger Catalan screen contain English?

**Yes. The screen really is in English, in the app itself. It is not a misdetection.** (certain)

- I looked at `research/real-apps-2026-10-04/wger-android-19-languages/ca-02_advanced.png` (the 315x560 copy; the full-size original
  is not in the folder, only 3 downscaled PNGs, `run.json`, `check.json`, `run.log`). It shows "Advanced", "Server and authentication
  options", "SERVER", "The official server", "Self-hosted", "Connect to your own instance", "Allow self-signed certificates",
  "Disables TLS certificate validation...", "SIGN-IN METHOD", "Username and password", "Refresh token", "Generate one on the wger
  website". All English.
- The app's strings (wger-project/flutter, `lib/l10n/*.arb`, the files that run used; still on disk in another session's scratchpad, so
  not in the repo): `app_en.arb` has 559 keys, `app_ca.arb` has 375 (67%). Every key behind this screen is missing in Catalan:
  `advanced`, `advancedSubtitle`, `serverSectionLabel`, `signInMethodSectionLabel`, `serverOptionDefaultDetail`,
  `serverOptionSelfHostedTitle`, `serverOptionSelfHostedDetail`, `allowSelfSignedCertsTitle`, `allowSelfSignedCertsDetail`,
  `authOptionPasswordTitle`, `refreshToken`, `tokenSubtitle`. German has all of them (`Erweitert`, `Selbst gehostet`, ...), which is why
  `de/02_advanced.png` is German. Flutter falls back to English for a missing key, so the screen is English. The new "Advanced" sheet
  was added to the app's English file recently and Weblate has not caught up in many languages (it, ja, pl, pt, pt-PT, ro,
  zh-Hant, ca and others lack `advanced`; ar, de, es, fr, hr, hu, id, nl, sl, uk, pt-BR have it).
- The original run (macOS 27, full size, with the app's strings via `run.json`) already said so, by exact string match, not by
  language guess: `ca/02_advanced.png: shows en strings (13 lines) more than ca (0)` (`check.json`, `run.log`). 13 screen lines equal
  English strings and none equal a Catalan string. The same run flagged 8 other languages on this sheet for the same reason.
- So the macOS 15 result "text looks like 'en', expected 'ca'" was a **true positive**, and macOS 14's skip was a **missed true
  positive** (it said nothing about English). What is wrong is that the two Macs disagree on the same file, not that either sentence
  is false.

### Why the two OS versions disagree (inferred, not measured on 14 or 15)

Language comes from `NLLanguageRecognizer` run on the text Vision read (`ocr.swift`), not from Vision itself.

- Catalan is not in Vision's list on macOS 27 (section 2), and no Apple source I found lists it on any version. So `check` treats `ca`
  as a language its reader has no model for on all three Macs (`want not in readable_languages()` in `judge_screen`).
- For such a language `judge_screen` reports English only when the detector says `en` with **more than 0.9**
  (`ocr.get("langs").get("en") > 0.9`). For a language the reader does read, the bar is lower: the detected language needs 0.8 or
  more, and the expected language under 0.2.
- On this Mac the same PNG gives `lang=en`, `en=0.862`, 324 characters, text read correctly (including "9:41" and "DEBUG"). 0.862 is
  under 0.9, so `shotfleet check` here (no Tesseract on PATH, to mirror the hosted runner) prints exactly the macOS 14 line: "macOS can't
  read the script of ca: those screens were only checked for showing another language, copies and missing screens", and no language
  problem. (certain, run here.) With Tesseract on PATH (installed here, with `cat`) it prints the same line plus a note that Tesseract
  names no language.
- The simplest explanation of macOS 15 is that its language recognizer (or the text Vision returned) put `en` above 0.9 for this
  file. That is **inferred**: the runner logs have no `ocr` JSON, so neither 14 nor 15's confidence was recorded. A second explanation, that
  macOS 15 lists Catalan, is unlikely given Apple's sources below, but is **unverified**.

The result is a threshold effect: the verdict flips on a detector confidence of 0.86 versus 0.9 on an English screen that is certainly
English. Any OS update that moves that number moves the verdict.

## 2. Which languages can Vision read, by macOS version

**This Mac (macOS 27.0), `ocr --langs` (certain, run 2026-10-05; the same 33 codes as `research/all-languages.md` and claim C071):**
en-US, fr-FR, it-IT, de-DE, es-ES, pt-BR, zh-Hans, zh-Hant, yue-Hans, yue-Hant, ko-KR, ja-JP, ru-RU, uk-UA, th-TH, vi-VT, ar-SA,
ars-SA, tr-TR, id-ID, cs-CZ, da-DK, nl-NL, no-NO, nn-NO, nb-NO, ms-MY, pl-PL, ro-RO, sv-SE, fi-FI, hi-IN, mr-IN. That is 33 codes, about
28 base languages. **No Catalan (ca), and also no Croatian, Hungarian, Slovenian, Slovak, Greek, Hebrew** and others. Catalan,
Croatian, Hungarian and Slovenian are Latin script: Vision still reads them with the Latin model (here it read the Catalan-labelled
screen's English perfectly; `research/all-languages.md` measured accents lost on Hungarian), it just lists no model for them.

**macOS 14 and 15 (what I could and could not verify):**

| Source | What it says | Value |
|---|---|---|
| Apple, `VNRecognizeTextRequest.supportedRecognitionLanguages()` (https://developer.apple.com/documentation/vision/vnrecognizetextrequest/supportedrecognitionlanguages(), fetched 2026-10-05 through developer.apple.com/tutorials/data JSON) | Returns "the identifiers of the languages that the request supports". Available macOS 12.0+. **No list, no per-OS table.** | Says nothing per version |
| Apple, `VNRecognizeTextRequestRevision3` (https://developer.apple.com/documentation/vision/vnrecognizetextrequestrevision3, same date) | Revision 3 starts macOS 13.0 | `ocr.swift` uses the default revision, so macOS 13 and later use revision 3 (inferred) |
| Apple, WWDC22 "What's new in Vision" (https://developer.apple.com/videos/play/wwdc2022/10024/, 2026-10-05) | Revision 3 (macOS 13) added Korean and Japanese and `automaticallyDetectsLanguage` | Confirms the list grew by release |
| Apple, macOS Feature Availability, Live Text row (https://www.apple.com/macos/feature-availability/, 2026-10-05) | Lists languages with no per-version split; **Catalan is not listed** | Live Text is the same engine (`research/all-languages.md`), so supports the "no Catalan" claim, not a per-OS list |
| Apple Developer Forums thread 121048 (https://developer.apple.com/forums/thread/121048, 2026-10-05) | User tests July 2020: en fr it de es pt zh on the macOS 11 / iOS 14 generation; Apple published no official list as of November 2020 | Older versions read fewer; no Catalan |

- **Which languages macOS 14 reads, which macOS 15 adds, and what changed in 26: unverified.** I found no Apple page that gives a per-OS
  list, and this Mac cannot report another OS's list. What can be said: the list grew with releases (7, then Korean and Japanese on 13,
  33 on 27); Catalan is on no Apple list I could find. The hosted run on macOS 14.8.9 printed "can't read the script of ca", which
  fits that.
- The `check` code does not hard-code any list: `readable_languages()` runs `ocr --langs` on the buyer's Mac. So the code adapts to the
  OS; only the prose ("reads 33 languages") does not.
- To close this gap cheaply: add `ocr --langs` and the `ocr` JSON of the two sample PNGs to the next `macos-compat` run (the workflow
  already compiles `ocr`). About 4 billed macOS minutes (the same two dispatches cost roughly $0.25). Not run: the brief says no
  GitHub Actions.

## 3. What should `check` do?

### What it does today (read in `shotfleet.py`)

Three outcomes for a language the reader has no model for (`want not in readable_languages()` in `judge_screen`):

1. Another language's strings found (needs `--app` or `--strings`): problem "shows X strings (n lines) more than ca (m)". Exact, always
   reliable.
2. No strings, detector says `en` above 0.9: problem "text looks like 'en', expected 'ca'". Anything else: `(None, None)`, and `cmd_check`
   prints "macOS can't read the script of ca: those screens were only checked for showing another language, copies and missing screens"
   (Tesseract's name when Vision is not the reader).
3. If the reader read nothing, `read_nothing(ocr)` is true only for Tesseract/`--ocr-command`/no reader; an empty Vision read of an
   unreadable language is `(None, None)`, otherwise a "no text found" problem (and "could not read this screenshot" note when the
   picture is not blank).

When no `--app`, `--strings` or `run.json` exists, `check_any` prints once at the top: "no --app given: checking by language detection
only, which can misjudge short screens; treat a language problem as a hint (pass --app to compare with your app's strings)".

### Is "treat a language problem as a hint" enough? No, for three reasons

1. It is printed once at the top, before the report; the problem line itself reads as a finding, counts in "N problem(s)" and makes the exit code 1
   (the hosted macOS 15 job failed on it). A CI user reads the problem list, not the first line.
2. The wording "can misjudge short screens" does not describe this case: the Catalan screen has 327 characters and 13 lines, the opposite of
   short, and the verdict was correct. The real weakness is the confidence threshold (above), not length.
3. "can't read the script of ca" is wrong for Catalan. The script is Latin, which macOS reads fine (it read all 324 characters);
   what is missing is a Catalan model. The message was written for Greek, Hebrew and Georgian. A buyer reading it may think the
   screenshot is unreadable and ignore the English.

### Should a language problem on a short or low-character screen be downgraded to a note?

**Not by character count.** Evidence: the true positive here has 327 characters, and in `check.json` the lowest `chars` of the 60 real
screens is 115 (zh-Hant login). A cut-off such as "under 60
characters" would not have changed this case and I have no real screenshot where it would remove a false positive. Short, language-neutral
screens are already handled by the dominance guards in `judge_screen` (the detected language needs 0.8 or more and the expected one under 0.2).
Keep as is; revisit only if a measured false positive appears. (inferred; the 60-screenshot sample is a single app.)

### Recommendation, smallest change first

| # | Change | Fixes | Cost |
|---|---|---|---|
| A | Say what happened for a Latin-script language with no model: in `cmd_check` print "macOS has no text model for ca (Latin script, read with the generic one): those screens were only checked for showing another language, copies and missing screens" when the language's script is Latin, and keep "can't read the script of" for Greek, Hebrew and so on | The misleading message (reason 3) | A small set of Latin-script base languages Vision lacks (ca, hr, hu, sl, sk, ...) plus one string. About 6 lines. Updates the assertion in `tests/test_shotfleet.py:2407` only if the `el` case wording changes (it can stay as is) and adds one test. No behaviour change, no new false positives |
| B | Give Latin-script languages Vision reads with the generic model (ca, hr, hu, sl, sk, pt, es...) the same "readable" bar (0.8, expected under 0.2) as listed languages, instead of 0.9 and English only | The OS disagreement: macOS 27 and 14 would then flag this file like 15 does (here en=0.862 is above 0.8, ca under 0.2) | About 3 lines in `judge_screen` (same set as A). Risk: a false positive on a short Catalan screen the detector calls English at 0.8 to 0.9; must be measured first on the saved real-app screenshots under `research/real-apps-*/` (device-free, `check` only; about 1 h). Do not ship without that run |
| C | Put the reader and OS in the report: `check.json` gets `"reader": {"name": "macOS text recognition", "macos": "<platform.mac_ver()>", "languages": N}` (or the Tesseract version), and the unreadable-language note adds "(macOS 14.8 reads N languages)" | Reproducing and comparing results across Macs; makes this kind of disagreement self-explaining | About 6 lines (`platform.mac_ver()`, `len(readable_languages())`) and one test that the key exists. Do not print it on every problem line (noise) |
| D | Append "(language detection only; pass --app to confirm)" to each language problem when no strings were given, so it travels into `check.json`, the gallery and CI logs | Reason 1 | 2 lines in `cmd_check` where `problem` is built. Tests that assert the exact text (`tests/test_agent_skills.py:157` lists the fragment "text looks like") use `in`, so low risk; check `tests/test_claims_unit.py` |
| E | Downgrade to a note under a character floor | nothing proven | Skip |

**Recommended order: A (certain value, no risk) and D, then C; B only after the measurement.** B is the real fix for the disagreement but
changes what gets flagged, so it needs the measurement; A, C and D only change words and the report. If only one thing is done, do A
plus D: it makes the 14 line truthful and the 15 line self-qualifying.

## 4. README and site: is a caveat needed?

**Yes, a small one.** The check's behaviour on other OS versions has been run only for installing and starting (hosted run), and the one
claim about readable languages is a macOS 27 number.

Exact sentences (README.md line 296 and `site/public/docs.html` line 258; claim C071 in `tests/claims.json` line 1225):

> "Text recognition is macOS's. It reads 33 languages, including Latin, Cyrillic, Arabic, Thai, Devanagari, Chinese, Japanese and Korean scripts. For scripts it can't read (Greek, Hebrew, Armenian, Georgian, most Indic and Southeast Asian scripts), `check` still catches screens in another language, copies and missing screens, and says which screens it couldn't read."

and (README.md line 301, `site/public/docs.html` line 60; claim C131):

> "Built for macOS 13 or later on Apple silicon; tested on macOS 27."

What is wrong or unsaid:

1. "33" is what macOS 27 reports; older releases read fewer (claim C071's proof already admits "older releases read fewer"; the README does not).
2. It says "scripts it can't read" but the list that matters is languages: Catalan, Croatian, Hungarian, Slovenian, Slovak are Latin script and
   are not among the 33, so `check` skips or weakens the language test for them (and the Catalan result already differed between macOS 14
   and 15). The sentence implies every Latin-script language is covered.
3. Nothing says a language problem found without `--app` is a hint (only line 299 says "can't judge short screens"; the log line is
   printed once).

Proposed caveat (replace nothing, add after the first sentence of that bullet):

> "The 33 is what macOS 27 reports; older macOS versions read fewer, and a language outside the list (for example Catalan, Croatian,
> Hungarian) is judged more weakly even though it uses the Latin script, so the same screenshot can get a different verdict on a different
> macOS. Pass `--app` to compare with your app's own strings, which
> gives the same answer on every macOS."

(`shotfleet doctor` does not print the list of languages today: it only says text recognition is ready, so I did not point at it; change C would make `check.json` show the count.) `tests/claims.json` C071 needs its `where_text` to still match, and C131 needs
its proof updated to mention the 14 and 15 hosted runs if the caveat quotes them. Not edited, per the brief.

## What is unverified

- The text and NaturalLanguage confidences on macOS 14.8.9 and 15.7.9 for the Catalan file (the runner logs have none); the explanation
  in section 1 is the likely one, not a measurement.
- Which languages macOS 14 and 15 read, exactly; Apple publishes no per-OS table that I could find. Whether macOS 15 lists Catalan
  (assumed not).
- The 315x560 downscale's effect: the hosted runs used the downscaled copy; the original full-size result is the macOS 27 run
  with strings, which agrees (exact string match).
- The false-positive rate of change B on other apps' Latin-script languages; (`doctor` does not print the language list; checked in the code).
- macOS 13 and 26 behaviour (no runner).
