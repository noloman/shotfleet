# Workarounds for the three text-recognition limits (2026-10-05)

Branch `claude/workarounds-text-recognition`. Nothing in `shotfleet.py`, `ocr.swift` or packaging was changed; the proposal lives in
`research/proposed-ocr/`. Labels: **CONFIRMED** = I ran or saw it on this Mac (M1 Pro, 10 cores, macOS 27.0 26A428, Xcode 27 SDK);
**INFERENCE** = follows from evidence but was not shown; **THIRD PARTY** = read on GitHub, not reproduced by me.

Environment while measuring: load average 550 to 890 (the release device gate), so every compile time below is a loaded-Mac time.
Experiments paused at the coordinator's request after the last one; the list of what runs after the gate is in section 9.

## 1. Verdict

**Does `usesCPUOnly` (or the compute-device API, or anything else) avoid the wedge? No. The wedge itself could not be tested.**

- **The wedge was not present.** The hung root `ANECompilerService` pid 69742 is gone (CONFIRMED: `ps -p 69742` empty at the start, uptime
  3 days 7 h, so no reboot). The service running was pid 25561, 20 minutes old, 0% CPU. Whatever cleared it, a reboot was not needed this time
  (unknown how: ask whoever ran things as root).
- **What I could produce on demand is the cold model compile**, the same service at ~100% CPU, with the same symptom (the recognition
  request does not answer for 35 to 120 s). Every configuration I tried waits for it, including CPU only (table in section 2).
- `sample` of a blocked client (CONFIRMED): `VNRecognizeTextRequest` (revision 3) -> `VNCRImageReaderDetector` -> Espresso
  `e5rt_e5_compiler_compile` -> `MILCompilerForANE::CompileUsingANEF` -> `-[_ANEClient compileModel:...]` -> `xpc_connection_send_message_with_reply_sync`
  -> `mach_msg`. That was a request with the CPU compute device assigned. The compile is requested from the service whatever device is assigned.
- **Only `recognitionLevel = .fast` answered during a compile (0.1 to 0.2 s, no service activity)**, but its text is garbage
  (section 2), so it is not a reader for `check`.
- `cancel()` does not help: it returned control only when the compile finished (cancel at 5 s, returned at 34.6 s with `CancellationError`).
  Killing the client does not cancel the compile either (kill at 15 s, rerun took 76 s).
- **What helps is patience plus a clear message**, not another API: wait while the service is working, say exactly what is happening when it
  is not, and stop retrying (section 5). `shotfleet check` today gives up after 90 s when Tesseract is installed, and a cold compile took 35 to
  122 s here: on a loaded Mac it drops to the weaker reader for no good reason.

## 2. The experiment (A)

Tool: `research/proposed-ocr/vtest.swift` (modes below, built `swiftc -target arm64-apple-macos13.0`, no warnings), `run_modes.py` (hard 30 s
limit, kills only its own child), `patient.py` (longer limit, prints the service's CPU every 10 s). Image:
`research/real-apps-2026-10-04/wger-android-19-languages/de-02_advanced.png` (315x560, German, 379 characters when read well).
"New path" = a byte-identical copy of the binary at a new file name (see 3rd observation below).

| Configuration | Cold (service has to compile) | Warm |
|---|---|---|
| accurate, default (what `ocr.swift` does) | 3x no answer in 30 s (killed); 34.6 s (new path, cancelled by me); 76.1 s (rerun after a kill at 15 s); 64.8 s (new binary `ocr2`) | 0.3 to 0.4 s |
| accurate + `usesCPUOnly = true` (macOS 13 API) | no answer in 30 s; 62.8 s on a new path | 0.4 s |
| accurate + compute device `.cpu` via `setComputeDevice(_:for: .main)` (macOS 14+ API) | no answer in 30 s; 67.0 s (first run); 64.0 s on a new path | 0.3 to 0.5 s |
| accurate, `revision = 2` | 34.5 s on a new path (service at 95 to 100%) | 0.2 to 0.3 s |
| accurate, macOS 15 Swift API `RecognizeTextRequest` (`vtest15.swift`) | no answer in 30 s; 122 s | not measured |
| `.fast` (with or without CPU device) | **0.1 to 0.2 s, no service activity** | 0.1 to 0.2 s |

Quality of `.fast` (CONFIRMED): German screen: 178 characters, first word right, the rest junk ("Str¥rr und Aulhrfjtrt"); Arabic settings
screen: 7 characters of junk; the new-API fast request returned 0 lines. Its language list is 6 (en fr it de es pt). Unusable as evidence.
Quality of revision 2: German screen 387 characters, good; Arabic screen junk (not in its 8 languages).
Quality of default revision 3 on the Arabic settings screen (`real-apps-2026-10-03/obytes-ios/ar-03_settings.png`, 257x560): near perfect
(all 17 labels), 42 s because it queued behind a killed run.

Observations that matter for the design:

1. **Both CPU-only APIs were tested on macOS 27.** `usesCPUOnly` does not warn at `-target 13.0` (it is deprecated from 14.0, so it warns
   only if the target is 14 or later). The `#available(macOS 14, *)` branch uses the compute-device API and the `else` branch `usesCPUOnly`.
   **The macOS 13 branch ran here too, but on macOS 27**, because `usesCPUOnly` still exists there; it was not run on macOS 13 and cannot be here.
   Both took the same time as default, cold and warm.
2. `supportedComputeStageDevices` lists Neural Engine, GPU and CPU for the accurate level and CPU only for fast (CONFIRMED). That fits fast not
   needing the service; it does not make accurate-on-CPU skip the compile (CONFIRMED by the stack and the timings).
3. **The compile result seems to be kept per executable path (INFERENCE, 7 of 7 observations fit):** rebuilding `vtest` at the same path twice
   stayed warm (1.1 s); every byte-identical copy at a new path (`vtestB` to `vtestF`) and every new binary (`ocr2`) was cold. First use of
   a fresh service and of the new Swift API were cold too. Consequences: a helper path that changes (moved install, new version in a new folder)
   pays the compile again; the shipped PyInstaller helper keeps one path, so `doctor`'s warm-up pays it once. Not tested: whether it survives a reboot.
4. **The service compiles one model at a time, and a killed client does not stop it** (CONFIRMED: 92% CPU for about 20 s after the client died;
   a retry waited behind it). So kill-and-retry is worse than waiting. `read_text` retries once after 120 s; with a cold compile at 60 to 120 s
   that is usually fine, but a short timeout plus retry (TRex uses 10 s, THIRD PARTY) piles compiles up.
5. **My own runs loaded the service.** About eight cold compiles (each 35 to 120 s at ~100% CPU), all in pid 25561; no second
   `ANECompilerService` ever appeared (CONFIRMED by `ps` before and after each run). At 15:46 `ps` showed it at 0.0% CPU with 23 min of
   total CPU in 47 min of life, unchanged for several minutes after my last run.
6. The `ocr.swift` of the repo already uses the non-deprecated instance method `supportedRecognitionLanguages()`; only my first `vtest` used the
   class method (deprecated from macOS 12). The new `vtest` uses the instance method.

Third-party reports (not reproduced; fetched 2026-10-05): macshot issue 439 and TRex PR 95 (GitHub) describe macOS 27 with
`VNRecognizeTextRequest` accurate: a first request that stalls 15 to 30 s, later requests that return nothing or fail with E5RT code 13 until the
process restarts; their workarounds: the new Swift API on macOS 15+ ("unaffected"), a 10 s timeout, `.fast` retry, pinning revision 2. Here: the
new API did compile for 122 s (not unaffected), `.fast` is junk on this UI text, revision 2 compiled too. I saw no E5RT 13 on a real image;
the only Vision error was code 13 "was given zero..." on a missing file, which is a different message.

## 3. Ranked workarounds

| # | Workaround | Fixes | Effort | Risk | Verdict |
|---|---|---|---|---|---|
| 1 | **Patient warm-up**: past the 90 s, keep waiting while `ANECompilerService` uses the CPU (ceiling 6 min); say "stuck" only when it has used 2 h of CPU or the ceiling passes; exact buyer message | (1): the false fall-back to Tesseract on a loaded Mac; a silent wrong reader; a message that does not say what to do | S: about 40 lines, in `proposed-ocr/shotfleet-ocr.patch`, 16 tests pass | low: the 2 h threshold is an INFERENCE (healthy service had 23 min after eight cold compiles; the wedge had about 9 h) | **do first** |
| 2 | **Do the cold compile on an idle Mac**: `doctor` (or the installer's last step) runs `ocr --warmup` once; the compile is kept per path (INFERENCE) | the first-check wait for every buyer | XS if `doctor` is already run; M for an install step | the installer is a script a buyer runs once; needs a reboot test | do second |
| 3 | **Latin-unlisted languages judged like listed ones** on macOS (`LATIN_UNLISTED = ca hr hu sk sl`, `sl` twin of `hr`) | (2): macOS 14 skipping ca, hr, hu while 15 flags | S: 8 lines in the same patch, 5 tests | medium: NaturalLanguage's confidence is a threshold (0.862 vs 0.9 flipped the Catalan verdict); `sl` reads as `hr` | do third, after reading section 6 |
| 4 | **Tesseract tuning for Arabic**: `-l ara --psm 6` instead of `-l eng+ara` | (3): partial words | S | one sample only (below) | measure at full size first |
| 5 | Extend `OSD_SCRIPT` (script detection) to Arabic, Cyrillic, Devanagari | (3): "no language" from Tesseract | S to M | thin margins on short UI text (142 of 144 for ja ko th) | after 4 |
| 6 | A real stuck-service reset: `sudo killall ANECompilerService` (macOS restarts XPC services on demand) | (1) without a reboot | none in code: a message line | **INFERENCE, untested** (needs sudo, the coordinator forbade it) and the stuck pid vanished by itself here | test once on a real wedge, then put in the message |
| 7 | Bundle Tesseract in the release | (1)(2)(3) | L | high (section 7) | not now |
| 8 | `usesCPUOnly` / compute device `.cpu`, revision 2, `.fast`, the Swift API, `cancel()`, a helper-side timeout | nothing | S each | none worth taking | **rejected with evidence** (section 2) |

Fix 1 changes what `check` says; it does not make recognition work during a true wedge. During a true wedge the only readers that answer are
Tesseract (on PATH) or none.

## 4. Per-macOS language table

CONFIRMED on macOS 27 with the SDK's own header text and the instance method `supportedRecognitionLanguages()` per revision
(`vtest langs`; the answer differs per revision and per level):

| Reader | Languages | Count |
|---|---|---|
| revision 1 (accurate and fast) | en-US | 1 |
| revision 2, accurate | en-US fr-FR it-IT de-DE es-ES pt-BR zh-Hans zh-Hant | 8 |
| revision 2 and 3, fast | en-US fr-FR it-IT de-DE es-ES pt-BR | 6 |
| revision 3, accurate (the default) | the 8 above + yue-Hans yue-Hant ko-KR ja-JP ru-RU uk-UA th-TH vi-VT ar-SA ars-SA tr-TR id-ID cs-CZ da-DK nl-NL no-NO nn-NO nb-NO ms-MY pl-PL ro-RO sv-SE fi-FI hi-IN mr-IN | 33 |
| macOS 15 Swift API `RecognizeTextRequest`, accurate | the same 33 (as BCP 47: `ru-Cyrl-RU`, `th-Thai-TH`, ...) | 33 |

What the SDK header says (CONFIRMED, `VNRecognizeTextRequest.h`, Xcode 27 SDK): revision 2 = English, Chinese, Portuguese, French, Italian,
German, Spanish (accurate); revision 3 (macOS 13+) "all languages from previous revisions plus some new languages". Revision 2 is deprecated
from macOS 15. Apple's WWDC22 session (cited in `limits-catalan-check-macos-2026-10-05.md`): revision 3 added Korean and Japanese.

**macOS 13, 14, 15, 26: not confirmed.** I found no Apple page with a per-version list (the feature-availability page lists Live Text languages
without a version split, and no Catalan). INFERENCE: macOS 13 = revision 3 with 10 to 12 languages (the 8 + ko, ja, probably uk); 14 and 15 in
between; Catalan is on none (matches the hosted run: macOS 14.8.9 "can't read the script of ca"). The helper reports the truth at run time, so
no list is hard-coded. A hosted-runner step that prints `ocr --langs` on macos-14 and macos-15 would settle it for free (no device).

**Proposed behaviour per case** (all on macOS; Linux keeps Tesseract-only logic):

| Case | Example | What `check` does |
|---|---|---|
| Reader lists the language | de, ja, ru, ar | as today |
| Not listed, Latin script, in `LATIN_UNLISTED` | ca, hr, hu, sk, sl | judged like a listed one: exact (accent-folded) string match first, then language detection with the same 0.8 / 0.2 thresholds; accents may be lost (hu) and `norm()` already folds them |
| Not listed, non-Latin script | el, he, hy, ka, bn, ta | as today: skip with the "can't read the script of" note, Tesseract if present |
| Latin, unlisted, not in `LATIN_UNLISTED` (et, lv, lt, is, eu, sw...) | | as today (skip); extend the set only after `nlprobe` shows NaturalLanguage tells it from English |

Evidence for the Latin rule (CONFIRMED on macOS 27): `nlprobe.swift`: five short Catalan, Croatian, Hungarian, Slovak lines come back as
`ca` 1.00, `hr` 1.00, `hu` 1.00, `sk` 1.00; Slovene comes back as `hr` 1.00. English comes back `en` 0.99. Vision reads Latin text with the Latin model
(Hungarian loses accents: `all-languages.md`). Not shown: a real Catalan or Hungarian screenshot (the repo's only Catalan screen is
English, as `limits-catalan-check` found), and NaturalLanguage on messy real UI text for those languages.

## 5. The design (C): `research/proposed-ocr/`

| File | What |
|---|---|
| `ocr.swift` | the proposed helper: `--rev2` flag kept as an option (see below), exit codes 0 / 2 (Vision failed, message on stderr) / 3 / 64, no uncaught `try` (today an error crashes the helper). Compiled with `swiftc -O -target arm64-apple-macos13.0`: **no warnings**. `helper_smoke.py` ran it: `--langs` 33, `--rev2 --langs` 8, image read, exit 2 on a missing file, exit 64 without arguments |
| `shotfleet-ocr.patch` | against `shotfleet.py` (not applied): `ane_state()`, `ocr_not_answering()`, patient `warm_up_ocr(..., patience=)`, `read_text` raises on exit 2, `LATIN_UNLISTED` and `can_read()` in `judge_screen`, `TWINS` hr/sl |
| `test_proposed_ocr.py` | 16 tests with fake helper scripts and a mocked `ps`; applies the patch to a temp copy; no Vision, no Tesseract. `python3 research/proposed-ocr/test_proposed_ocr.py`: OK |
| `vtest.swift`, `vtest15.swift`, `nlprobe.swift`, `run_modes.py`, `patient.py` | the experiments |

Decisions, each with its reason:

- **No `usesCPUOnly` / compute device in the helper** (it would add a branch per macOS for nothing). If a later wedge test shows it answers
  while the service is stuck, `vtest.swift`'s `useCPUOnly()` is the code to copy: `#available(macOS 14, *)` compute device, else `usesCPUOnly`.
- **`--rev2` stays in the helper but is not used by the patch**: revision 2 compiled too (34.5 s cold), so it is no way around a stuck service. It
  is only a faster, smaller reader for en fr it de es pt zh. Remove it if nobody uses it; it costs 5 lines.
- **The timeout stays in Python**, because `cancel()` cannot interrupt the blocked compile and the helper has no other way to give up.
- **`ane_state()` uses `ps -Ao pcpu=,time=,comm=`** (read only, what `read_text` already did). "Working" = above 20% CPU. "Stuck" =
  busy and 120 CPU minutes used in all (INFERENCE) or the 6 minute ceiling passed.
- **Messages** (what the buyer reads, from `ocr_not_answering()`):
  - busy, over 120 CPU min: "macOS text recognition isn't answering: its Neural Engine compiler (ANECompilerService) is stuck (N hours of
    CPU used). Restart the Mac to clear it" + (no Tesseract) ". Or install Tesseract and shotfleet uses it automatically: brew install tesseract tesseract-lang";
    with Tesseract: "...; using Tesseract instead (it reads fewer scripts and names no language, so some screens will be reported as unverified)".
  - busy, under 120: "...didn't answer in time: ... still compiling the model, which takes up to a few minutes on a busy Mac (and is stored for next
    time). Run check again in a few minutes".
  - idle and silent: "...isn't answering (is the Mac overloaded?). Run check again in a minute; if it keeps happening, restart the Mac".
- `doctor` appends the same line to its "slow to start" note.

Not in the patch (listed so nobody thinks it was forgotten): Tesseract tuning (4, 5), the sudo line (6), a hosted-runner language-list step.

## 6. What to implement first and how to test it

1. **Apply `shotfleet-ocr.patch` parts 1 and 2** (patience, messages, exit-2 handling in `read_text`) and the helper's exit codes. Gate: the 16 tests
   plus the repo's own `tests.test_first_run` and `tests.test_shotfleet` OCR tests (not run here; the patch keeps `warm_up_ocr(ocr, timeout)`
   behaviour because `patience` defaults to 0, and the existing tests pass only `timeout`). Real test: after the gate, on an idle Mac, a new-path helper
   (cold compile) under `check` with Tesseract on PATH: expect no fall-back and a Vision read.
2. Latin rule (3): apply, then on a hosted macos-14 runner run `check` on a Catalan folder where the screen is English: expect the
   "text looks like 'en', expected 'ca'" line that macOS 15 gives. Needs no device.
3. Arabic Tesseract tuning (4): measure first. One sample so far (CONFIRMED, `ar-03_settings.png`, 257x560, `OMP_THREAD_LIMIT=1`, under
   1 s each): `-l eng+ara` gave the title and a few labels plus junk; `-l ara --dpi 300 --psm 6` gave most of the 17 labels with single wrong letters (counted by eye, not scored)
   ("التطييق" for "التطبيق"). Still no exact line match for most, but the script is evidently Arabic. Real screenshots are 4x larger than these
   copies; repeat at full size and on 3 more screens before changing `TESSERACT_COMMAND`.

## 7. Is a bundled second reader (Tesseract) worth it?

Not now. Facts:

- **Licence:** Tesseract is Apache 2.0 and the Homebrew language data folder carries the Apache 2.0 text (CONFIRMED: `LICENSE` in
  `tesseract-lang/4.1.0`). Leptonica (its image library) is BSD-2-clause (INFERENCE from general knowledge; not read here). Compatible with a
  paid closed product; needs a notices file.
- **Size (CONFIRMED here):** `libtesseract` 2.7 MB, `libleptonica` 2.1 MB, the binary 72 KB, plus libarchive and Leptonica's image libraries
  (png, jpeg, tiff, webp, gif, openjp2, zlib: not measured, INFERENCE 3 to 6 MB more). Data: the fast models on this Mac are small
  (ara 1.4 MB, cat 1.1, eng 4.1, hrv 4.1, hun 5.3); the whole installed pack is 654 MB, 126 files. For the gaps only (ca hr hu sk sl + ara + a few) about 15 to 25 MB.
- **Build and notarization (INFERENCE from `packaging/build.sh`, which already signs every Mach-O with hardened runtime and a timestamp):**
  the Homebrew `tesseract` is built for macOS 27 (`minos 27.0`, CONFIRMED with `otool -l`), so it would not start on macOS 13 to 26, the
  range the helper now supports. Shipping it means building Tesseract and Leptonica from source with `-mmacosx-version-min=13.0`, static or relinked
  to `@rpath`, one signature per dylib. That is a new build stage in the release, the thing the product avoided so far.
- **Accuracy on the repo's screenshots (CONFIRMED, small sample, 257 to 315 px wide copies):** German settings sheet: Tesseract `eng+deu` 8 lines,
  several wrong ("Valierung des TLS-Zertikate"), Vision 17 lines correct. Arabic: section 6. Tesseract is the worse reader on UI text everywhere
  I looked, and the README already says so. A bundled Tesseract would fix coverage of unlisted Latin languages only if the Latin rule (3) were not enough,
  and it is the weaker reader in a wedge, where its job is to answer at all.
- Cheaper: keep "install Tesseract" as the documented fall-back (already automatic) and make the message say how. Revisit if the Latin rule fails on real
  screens, or if buyers ask for el, he, hy, ka.

## 8. What I could not verify

- **Anything while the service is truly wedged.** The 10 hour state could not be produced (and should not be); the cold compile is a proxy
  (same service, same symptom, but it ends). That the stuck state also blocks CPU-only, revision 2, the new API, and answers `.fast` is INFERENCE.
- The macOS 13 and 14+ branches on their own macOS; `usesCPUOnly` and the compute device on a Mac without a Neural Engine path.
- Languages of macOS 13, 14, 15, 26 (INFERENCE only); NaturalLanguage on real Catalan, Hungarian, Croatian, Slovak UI screens.
- Why a first Arabic image took 42 s on a warm path (queued behind a killed run, or a per-script model: not separated).
- The per-path cache theory beyond 7 observations; whether it survives a reboot; whether a cold helper in a signed, notarized bundle behaves the same.
- Whether `sudo killall ANECompilerService` clears a stuck service (nobody ran it); how pid 69742 disappeared.
- The third-party E5RT code 13 reports (summaries from GitHub, not reproduced; the macshot and TRex claim that the new API is unaffected
  contradicts my 122 s).
- Tesseract at real screenshot size; more than one Arabic sample; the repo's own test suites against the patch.
- Leptonica's licence and the sizes of its image libraries.

## 9. Experiments to run after the gate (file `/tmp/shotfleet-rc-gate-done` exists)

One at a time, each under a 30 s hard timeout (`run_modes.py`; a cold compile may not finish in 30 s, so a run that times out is repeated once
with `patient.py` and a 150 s limit only if the coordinator agrees), and `ps -axo pid,user,pcpu,etime,command | grep ANECompilerService` before and after each.

| # | Experiment | Expect | Records |
|---|---|---|---|
| 1 | idle check: `ps` for the service, 1 min apart | 0% | pid, CPU time |
| 2 | new-path copy, `default` (control) | cold, 30 to 60 s on an idle Mac | seconds, service pid, CPU peak |
| 3 | new-path copy, `cpu14` | same as 2 if the stack finding holds | the same, and "new pid?" |
| 4 | new-path copy, `cpuold` | same | the same |
| 5 | new-path copy, `fast` | 0.2 s, no service CPU | the same |
| 6 | new-path copy, `rev2` | cold (34.5 s under load) | the same |
| 7 | new path, `vtest15 default` | cold | the same |
| 8 | same cold state, `default+cancel` | returns only when the compile ends | seconds |
| 9 | warm-up of a new-path copy, then `ocr2 --warmup` at the same path: warm after reboot? (needs a reboot: later) | | |
| 10 | if the service is at 90%+ with no client for 10 min (a real wedge): `default`, `cpu14`, `fast`, `rev2`, 30 s each | which answer | seconds |
| 11 | proposed `ocr.swift` built to a new path; `patient.py` through patched `check` on 3 screenshots with Tesseract on PATH | Vision read, no fall-back | log of the message text |
| 12 | `tesseract -l ara --psm 6` against `eng+ara` on 3 full-size Arabic screens | better | lines matched |
| 13 | hosted macos-14 and macos-15: print `ocr --langs` | settles section 4 | the two lists |

The coordinator's question "does a new `ANECompilerService` appear": during all runs so far, no (every cold compile ran in pid 25561).

## 10. Post-gate experiments (2026-10-05)

Run 16:26 to 16:31 by the coordinator's device-slot runner (no device lock: no simulator or emulator), after the gate (`/tmp/shotfleet-rc-gate-done`
present), quiet Mac (free memory 56 %, load 17 at the start; 10 cores, 32 GB, macOS 27.0 26A428). Binaries built from `research/proposed-ocr/`
(`vtest.swift` with `-target arm64-apple-macos13.0`, `vtest15.swift` with `-target arm64-apple-macos15.0`); every experiment ran a fresh
byte-identical copy at a new path (cold by the per-path theory) through `run_modes.py` (hard 30 s, kills only its own child), image
`real-apps-2026-10-04/wger-android-19-languages/de-02_advanced.png`. `ps -axo pid,user,pcpu,etime,time,command` for `ANECompilerService`
before, every 2 s during, and after; between experiments the driver waited until the service was under 5 % CPU (max 120 s).
`patient.py` (150 s) was not run: the note asks for the coordinator's OK first, and none was given for this slot.

| # | Config | Answered | Time | ANECompilerService | Load (1/5/15 min) before -> after |
|---|---|---|---|---|---|
| 1 | idle check, 60 s apart | n/a | n/a | pid 25561 (root), 0.0 %, CPU time 27:52.66 both times, no other pid | 16.4 / 17.5 / 92.8 -> 18.8 / 17.5 / 87.6 |
| 2 | `default` (accurate), new path | **no** (killed at 30 s) | >30 s | same pid 25561, busy: peak 100 %, +26.6 s CPU | 18.8 -> 19.7 |
| 3 | `cpu14` (compute device `.cpu`) | **no** | >30 s | 25561, peak 99.9 %, +26.6 s CPU | 19.7 -> 14.8 |
| 4 | `cpuold` (`usesCPUOnly`) | **no** | >30 s | 25561, peak 100 %, +27.0 s CPU | 14.8 -> 12.8 |
| 5 | `fast` | **yes**, 178 chars, the known junk ("Str¥rr und Aulhrfjtrt") | 0.3 s wall, 165 ms in Vision | 25561, **0.0 %**, CPU time unchanged | 12.8 -> 12.3 |
| 6 | `rev2` (revision 2) | **no** | >30 s | 25561, peak 100 %, +26.9 s CPU | 12.3 -> 13.7 |
| 7 | `vtest15 default` (macOS 15 Swift API) | **no** | >30 s | 25561, peak 98.7 %, +25.0 s CPU | 13.7 -> 13.4 |
| 8 | `default+cancel` (`cancel()` after 5 s) | **no**: `cancel()` did not make `perform` return | >30 s | 25561, peak 96.7 %, +20.6 s CPU | 13.5 -> 19.2 |

Findings:

- **No new `ANECompilerService` appeared** in any experiment; every compile ran in the existing root pid 25561 (alive 1 h 21 min at the end,
  30:29 CPU total). This extends the earlier "no" to 7 more cold compiles on a quiet Mac.
- **On a quiet Mac a cold accurate request still does not answer in 30 s**, for every accurate configuration: CPU-only (both APIs),
  revision 2 and the new Swift API all start the same compile (service at 97 to 100 % within 2 s). Only `.fast` skips the service. This
  confirms on an idle machine what section 2 saw under load: none of the cheap knobs avoids the cold compile.
- `cancel()` after 5 s does not interrupt a request that is waiting on the compile (experiment 8).
- New: after the client was killed, the service fell under 5 % CPU within 3 to 13 s (settle waits: 3, 3, 3, 0, 0, 6, 13 s). Section 2
  observation 4 saw about 20 s of compiling after a kill; here the compile seems to stop soon after its client dies (INFERENCE from 7
  samples at 3 s resolution). Each killed attempt cost about 21 to 27 s of service CPU and left no warm cache behind (the next new path
  was cold again).
- Not run: 9 (needs a reboot), 10 (no wedge: the service idled at 0 %), 11 (needs `patient.py` with the longer limit), 13 (hosted
  runners: no GitHub Actions in this slot).

Experiment 12 (Tesseract 5, `--psm 6`, 30 s limit each; the repo has no full-size Arabic screens, so the three 257x560 `obytes-ios` screens):

| Screen | `-l ara`: lines / Arabic letters | `-l eng+ara`: lines / Arabic letters | Time |
|---|---|---|---|
| `ar-01_onboarding` | 9 / 109 | 9 / 10 | 0.3 s / 0.5 s |
| `ar-02_login` | 5 / 14 | 5 / 3 (but reads the English "Sign In") | 0.1 s / 0.2 s |
| `ar-03_settings` | 18 / 124 (`إعدادات`, `عام` right) | 18 / 85 (same two labels right) | 0.2 s / 0.5 s |

`ara` alone returns far more Arabic text than `eng+ara`, which reads Arabic glyphs as Latin; `eng+ara` is only better for English left in the
UI. Line accuracy against the real labels was not scored (no ground truth file); at this resolution both are well below Vision's revision 3
(section 2: all 17 labels of `ar-03_settings`).
