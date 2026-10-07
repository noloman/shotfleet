<!-- Excerpt, copied 2026-10-06 from docs/dogfood-shotfleet-2026-10.md in the AnywhereRoles (remoti) repository, worktree handoff-shots, branch claude/store-screenshots-2026-10, commit c93d6831e: the header, Setup, Result, F1, F2, F6 and F7, unchanged. The rest of the report (other findings, frame review) is not copied. -->

# Dogfooding shotfleet on the AnywhereRoles store screenshots (2026-10)

Every entry has the exact command, what was expected, what happened, a severity (S1 blocks a listing, S2 wrong or
missing result, S3 friction) and a suggested fix. The shotfleet repository was not modified. Times are CEST,
2026-10-06, from the logs in `build/shotfleet/logs/` (gitignored; kept in the worktree).

## Setup

| | |
|---|---|
| shotfleet | **0.1.4** released signed build, by full path `~/Developer/shotfleet-rc-build/0.1.4/unpacked/shotfleet/shotfleet` (`--version`: `shotfleet 0.1.4`). The two baseline `check` runs of F1 to F4 were also made with 0.1.3, same result. Not on PATH. |
| Licence | Test licence activated by the coordinator for this macOS user (I entered nothing). No `free tier` line appeared in any run; 15 Android and 18 iOS locales were captured, so it is not limited to 2 languages. |
| Maestro | 2.0.10 from `~/.maestro/bin` (shotfleet prefers 2.11.0; it prints the note `Maestro 2.0.10 saves no per-step screen hierarchy (needs 2.7.0); Android screen text is read from pixels (OCR)`). Java 21 (sdkman). |
| Mac | Apple silicon, macOS 27, Xcode 27. Shared with other sessions: load 100 to 980, swap 10 to 30 GB for most of the day, one reboot at 13:20. |
| Builds | `shared` XCFramework 27 min 30 s (Gradle, `--max-workers=2`, nice); `assembleDevDebug` 7 min; `xcodebuild` Debug simulator with `ARCHS=arm64` (about 10 min). No Swift error on the first xcodebuild. |
| Repo | worktree `.claude/worktrees/handoff-shots`, branch `claude/store-screenshots-2026-10`, base `origin/main` b37964c84 (main later gained only a test-script change, 677252886). |

Run folders (kept where shotfleet wrote them, `/Users/manu/Developer/remoti/.claude/worktrees/handoff-shots/build/shotfleet/`):

| Folder | What |
|---|---|
| `out-android` | final Android run, 15 languages x 8, each with `raw/<lang>/*.png`, `run.json`, `check.json`, `index.html`, `maestro_*.log` |
| `out-iphone` | final iPhone run, 18 languages x 6 (+ `.texts.json` per frame), `run.json`, `check.json` |
| `out-iphone-run1-en-de-ja` | first iPhone run, 3 languages, superseded because slot 05 needed a second swipe |
| `out-android-run2..run10-*` | failed Android runs while the flow was being fixed (kept as evidence) |
| `out-ipad`, `out-ipad-run1-failed` | the two failed iPad landscape attempts |
| `check/` | `shotfleet check` of the committed result, both stores |
| `logs/` | console output of every run |

The very first Android run folder (3 of 8 frames, failed at Salary Insights) was deleted by me while moving
folders (`rm -rf` before the next run); its console log survives (`logs/and-run1.log`).

## Result (what shotfleet produced)

| Platform | Command | Languages | Per language | Device | Wall | Retries | `run` check |
|---|---|---|---|---|---|---|---|
| Android | `shotfleet run scripts/shotfleet/shotfleet.toml --platform android --parallel 1` (16:24) | 15 (de en es fr hi it ja ko nl pl pt-BR ru sv tr zh-CN) | 8 | 1 emulator (`shotfleet_android`, 1080x1920) | 1826 s capture | 0 | `checked 120 screenshots in 15 languages: 0 problem(s)` |
| iPhone | `shotfleet run scripts/shotfleet/shotfleet.toml --platform ios` (17:17) | 18 (de en es fr hi id it ja ko nl pl pt-BR ro ru sv tr uk zh-Hans) | 6 | 2 simulators (asked for 4; shotfleet lowered it to 2 for memory), iPhone 17 Pro Max, iOS 26.4 | 3420 s capture | 3 (ja, tr, zh-Hans, each OK on the second attempt) | `checked 108 screenshots in 18 languages: 0 problem(s)` |
| iPad Pro 13" landscape | `shotfleet run scripts/shotfleet/shotfleet-ipad.toml --platform ios --locales en --parallel 1` (18:20, 18:33) | 1 tried | 0 of 5 | 1 simulator, iOS 26.4 | 190 s and 548 s | 1 each | not captured, see F12 |

`check` of what is committed (after captions were burned over the frames), run once the Mac was quiet:

| Command | Output |
|---|---|
| `shotfleet check fastlane/metadata/android --strings 'androidApp/src/main/res/values*/strings.xml' --report build/shotfleet/check/android` (34 s) | `checked 120 screenshots in 15 languages: 16 problem(s)`: 15 are the F2 false "missing" lines and 1 is `ru-RU/8_ru-RU.png: text looks like 'kk', expected 'ru'` (F7, the frame is Russian). Before this work: 127 problems, 103 of them "the caption is in X but the app UI shows en strings". |
| `shotfleet check fastlane/screenshots --strings 'iosApp/remoti/*.lproj/*.strings' --report build/shotfleet/check/ios` (81 s) | `checked 220 screenshots in 20 languages: 0 problem(s)` (120 iPhone frames = 18 captured languages + the en-GB and es-MX copies, plus 100 iPad frames that were not recaptured). |

## Findings, ranked

### F1 (S1, product). Android listings were English UI under translated captions, and shotfleet's `check` proves it

- Command (0.1.3 and 0.1.4, same output): `shotfleet check fastlane/metadata/android --strings 'androidApp/src/main/res/values*/strings.xml' --report <dir>`
- Output: `checked 120 screenshots in 15 languages: 127 problem(s)`; 103 lines like `de-DE/1_de-DE.png: the caption is in de but the app UI shows en strings (21 lines) more than de (2)`.
- Cause: the repo kept one English capture set and burned localized captions on it. Expected result, shotfleet is right. Fixed by recapturing every language with shotfleet (127 down to 16, all 16 false, F2 and F7).

### F2 (S2, shotfleet bug). `check` reports false "missing" screenshots for the fastlane supply layout

- Same command. 15 extra problem lines, one per locale, each about 110 file names long: `de-DE: missing 1_en-US.png, 1_es-ES.png, ... 8_zh-CN.png`.
- Expected: none. In `metadata/android/<locale>/images/phoneScreenshots` the locale is part of the file name (`1_de-DE.png`), so names differ per locale by design; every locale has its 8. Unchanged in 0.1.4. Fix: compare the `<n>_` index, not the whole name. It also makes the 103 real lines hard to find.

### F6 (S2). Failed flow: no step name, no failure frame, and the retry replays the same deterministic failure

- Seen in 9 failed runs (`logs/and-run1..run10.log`, `ipad-run*.log`). Output is one line, for example `FAIL en 3/8 screenshots (retried)  Element not found: Text matching regex: Salary Insights`, or `Assertion is false: id: jobDecision.title is visible` (iPad).
- The whole language is replayed once. For an "element not found" it fails the same way, so every flow bug cost twice the time (a 15-language Android run with a flow bug took 44 min before I stopped it). The failing step number, a screenshot at the failure and the screen text would turn a 6-minute debug round into a minute. Retry only infrastructure errors (grpc `UNAVAILABLE`, `Unknown error`, `Unable to clear state`).
- I debugged on my own emulator with plain `maestro test` (needs `JAVA_HOME` to a Java 17+ and `ANDROID_HOME`; shotfleet finds its own Java, the shell did not). A `shotfleet run --debug <locale>` that keeps the emulator and prints the translated flow would remove that detour. The translated flow is in `out-*/.work/flows/` for iOS only.

### F7 (S3). Language detection false positive on a short Russian screen

- `shotfleet check` (committed Android set): `ru-RU/8_ru-RU.png: text looks like 'kk', expected 'ru'`. The frame (saved searches, mixed Russian and invented English names) is Russian. Counted as a problem, exit 1. Suggest preferring the app's own strings when `--strings` is given, as for the other 14 listings.

