# Compatibility with the tools shotfleet drives

Checked 2026-10-03, with the macOS, Xcode, iOS 27 and Maestro rows added 2026-10-05. "Checked" says how: **real run** means shotfleet ran it end to end on a device, **static** means a program looked at the
tool without running an app, **suite** means the unit tests. Anything not in the table was not checked; `docs/handoff.md` lists what is
left and how to do it.

## Maestro

| Version | What was done | Result |
|---|---|---|
| 2.0.10 | every real run until 2026-10-03 (CrossfitTracker 18/18 on iOS and Android, the iOS fixture e2e 36/36, the Android fixture 29/29), plus `tools/maestro-compat.py`; the fixture e2e again on 2026-10-04 after the relative-screenshot-name change: iOS 36/36, Android 29/29 | 28/28 static checks. **Tested** (`MAESTRO_TESTED`). |
| 2.11.0 (the newest: 2.11.1, 2.12.0 and 3.0.0 do not exist as of 2026-10-03) | `tools/maestro-compat.py` on the real download (SHA-256 5384593c...e1283a, matches the release's own checksum file): 28/28. Real fixture e2e on a Mac, 2026-10-03: **failed** (iOS 25 of 36, Android 19 of 29): 2.11.0 rejects absolute `takeScreenshot` paths outside its artifact folder. After shotfleet named screenshots relative to Maestro's working directory (`collect_shots`), 2026-10-04: iOS 36/36, Android 29/29. See `research/maestro-2-11.md` | **Tested** (`MAESTRO_TESTED`); `doctor --fix` installs it. CrossfitTracker (app 55ad0975, 1.6.2) on 2.11.0, 2026-10-04: iOS, Android phone and Android tablet 19/19 languages each, 0 problems; the iOS run needed shotfleet's retry for 9 languages because two of four simulators did not start their driver in time (`research/maestro-2-11.md`). |

`tools/maestro-compat.py [folder]` checks any Maestro against `shotfleet.MAESTRO_INTERFACE`, the one list of what shotfleet relies on:
`--version` parses; `maestro --device` and `maestro test --shard-split --format --output --debug-output` exist and `--format` offers JUNIT; the
jars still hold the log line shotfleet parses to learn which emulator ran which flow (`Selected device ... using port ... with execution plan
ExecutionPlan(flowsToRun=`), `maestro.log`, the two environment variables shotfleet sets, and the thirteen flow keys it writes. A unit test
fails if that list stops matching what `shotfleet.py` passes. Run it first whenever a new Maestro appears:

```bash
python3 tools/maestro-compat.py ~/.shotfleet/maestro      # or any unpacked Maestro folder; exit 1 if something required is gone
```

What it cannot tell: whether the sharded parallel runs behave (Maestro 2.6.0 changed parallel iOS handling), whether `launchApp`/`clearState`
errors that 2.7.0 stopped swallowing now fail a flow that used to pass, or how long a run takes. Those need the device run.

**A finding worth acting on:** 2.11.0 defines `MAESTRO_DEVICE_UDID` (in `maestro/orchestra/util/Env.class`); 2.0.10 does not. shotfleet's
Android `[inputs.<locale>]` support already keys on that variable and was written for exactly this, and it works on 2.11.0: the
device run of 2026-10-04 showed `MAESTRO_DEVICE_UDID` = the adb serial (`emulator-5702`) and the German and Japanese typed values in the screenshots
(one emulator, de then ja; two at once and Arabic not run, see `research/maestro-2-11.md`).

## Other tools

| Tool | Versions | How | Result |
|---|---|---|---|
| Python | 3.11, 3.12, 3.13 | suite (658 tests on 2026-10-03, 41 skipped as Mac-only) with deprecation warnings as errors, run on each of 3.11, 3.12 and 3.13 after the docs audit; CI runs 3.11 and 3.13 on Linux, 3.12 on macOS | pass |
| Python | 3.10 | run | refuses with "shotfleet needs Python 3.11 or newer" |
| Python | 3.14.0rc2 | suite (595 tests) with deprecation warnings as errors | pass; the final 3.14 release is not out, so not in CI yet |
| Java | Temurin 21.0.12.1 (from `doctor --fix`), openjdk 21.0.11 | ran Maestro 2.0.10 and 2.11.0 and Google's sdkmanager | works |
| Android SDK | command-line tools 23.0, platform-tools 37.0.1, emulator 37.2.12, build-tools 36.0.0, API 36 `google_apis` x86_64 | installed by `doctor --fix` on Linux; `doctor` saw all of it | install and detection work; **the emulator was never started** (no hardware virtualization) |
| Flutter | 3.47.6 stable | built a 3-language app with `gen_l10n`; `init` found the APK and ARB files; wger's real ARB files read | works up to the build; no device run. 3.47 writes generated localizations next to the ARB files, not into `flutter_gen`. |
| Expo / React Native | `create-expo-app` as of 2026-10-03 (SDK number not recorded) | built a release APK with i18next + expo-localization; `init` found it | works up to the build; no device run |
| Kotlin Multiplatform | JetBrains/kotlinconf-app (clone only) | detection | works after a fix |
| Licence calls through an HTTPS-re-signing proxy | this sandbox's | real handshake, aimed at a harmless URL, no key | fails without `SSL_CERT_FILE`, works with it |
| Google Android command-line tools | 23.0 (`sdkmanager` prints "deprecated, Android CLI will be used instead"), Android CLI 1.0.16500706 | `doctor --fix` on a bare Linux machine and on a GitHub runner; `android --no-metrics sdk install` checked against the real tool | works after two fixes (dotted SDK path; usage reporting). **Risk:** `sdkmanager` is a deprecated shim; if Google removes it, `doctor --fix` and the printed `sdkmanager` commands in `doctor` need to move to `android sdk install` |
| Apple App Store screenshot sizes | Apple's specification page, read 2026-10-03 | `tools/apple-specs-watch.py` on the real page: 45 distinct sizes; table matches after adding iPhone Duo and four old-device landscape sizes | match; re-run monthly with `tools/watch-upstream.sh` |
| Xcode 27 final (Device Hub replaces Simulator.app) | read in code; run 2026-10-04 on Xcode 27.0 (27A266a), macOS 27.0 (26A428), iOS 26.4.1 runtime only (no iOS 27 runtime installed) | shotfleet itself only calls `xcrun simctl` (list, create, delete, boot, bootstatus, status_bar, install, shutdown, help, plus the user's own `[ios] simctl` commands) and never `open -a Simulator`. Maestro 2.0.10 and 2.11.0 both contain `open -a .../Simulator.app --args -CurrentDeviceUDID` in `LocalSimulatorUtils.launchSimulator`, reachable only from `DeviceService.startDevice` (`maestro start-device` and the interactive device picker); shotfleet boots its own simulators and gives Maestro their ids, so that path should not run | **works on Xcode 27.0 with the iOS 26.4 runtime, and with iOS 27 on one simulator and one language (2026-10-05); the 4-simulator iOS 27 run is untested.** `SHOTFLEET_E2E=1 tools/fixture-e2e.sh --platform-only ios` (Maestro 2.0.10): 36 of 36 assertions, 16 min 42 s. During it nothing ran `open -a Simulator`: no `open` process in the unified log (`log show --predicate 'process == "open"'`, 12:33 to 12:51) and none in a once-a-second process sample (a process shorter than 1 s could slip past the sample; the log is the backstop). `DeviceHub.app` is in `Xcode.app/Contents/Applications` and no Simulator.app exists. By hand on one throwaway iPhone 17 Pro Max / iOS 26.4 device every verb shotfleet uses returned 0: `help`, `list runtimes`, `create`, `boot`, `bootstatus -b` (34 s), `status_bar override` (time reads 09:41; OCR of the screenshot finds `09:41`), `install`, `launch`, `io screenshot` (1320x2868), `shutdown`, `delete`. `latest_ios_runtime()` picks iOS-26-4 here; `iPad Pro 13-inch (M5)` 12 GB and 16 GB and `iPhone 17 Pro Max` device types exist. Other tools broke on exactly this call (expo/expo#46671, callstackincubator/rock#731, anthropics/claude-code#95085); shotfleet does not make it. **iOS 27 on one simulator, one language: works (2026-10-05).** `tools/ios27-repro.sh` on the iOS 27.0 (24A434) runtime: build, init, doctor passed and `shotfleet run` captured 1/1 locales in 78 s, 0 problems, no `open` process in the unified log for that window (checked afterwards; load 22, swap 6.1 of 7.2 GB, Maestro 2.0.10). The same e2e with 4 simulators had not finished at its 35 min limit earlier that day at load 735 and swap 21.6 of 22.5 GB; it did not reproduce on a quiet Mac, which points at load, but **the 4-simulator iOS 27 e2e has not been rerun and is untested**; see `research/xcode-27-ios27-attempt-2026-10-05.md` |
| Tesseract | 5.3.4 | `check` on rendered screenshots on Linux (de, ja, en data) | works |
| macOS 27 | every real run to date (Maestro, simulators, emulators, `check`, the licence calls) | Mac, Apple silicon | works; the only version with simulator runs |
| macOS 14.8.9 and 15.7.9 | the live 0.1.1 on GitHub's Apple-silicon runners, 2026-10-05 (hosted runs 37303612329 and 37304115758, images macos-14 and macos-15): `install.sh`, `shotfleet --version`, `doctor` to the end, `check` on two sample PNGs (`research/limits-platform-reach-2026-10-05.md`) | **install, start, `doctor` and `check` work.** Text recognition reads Catalan on 15 and not on 14 (`research/limits-catalan-check-macos-2026-10-05.md`). No simulator or Gatekeeper run there |
| macOS 13 and 26.0 to 26.2 | not run | **untested.** The 0.1.0 folder very probably fails to start there (52 of 56 Mach-O files at macOS 27.0, and Expat symbols that macOS below 26.3 lacks; INFERRED). The 0.1.1 build declares macOS 13 (2 files at 11.0, the `ocr` helper at 13.0, none at 27.0, `tools/macho-minos.py`), which is a build fact, not proof that it runs |
| Xcode | 27.0 only (with the iOS 26.4 and 27.0 runtimes) | Xcode 26.x has not been run. Older Xcode: the default `device_type` is the iPhone 17 Pro Max, which an older Xcode does not have, so `run` should stop with "could not create simulator" and the buyer sets `device_type` (INFERRED, not run on an old Xcode) |
| Python in the release | 0.1.1 bundles a standalone Python 3.14.2; the 0.1.0 folder had Homebrew's 3.14.8 | build fact (`tools/macho-minos.py`, `research/release-0.1.1-evidence-2026-10-05.md`) |
| Maestro 2.0.10 against 2.11.0 on timing | quiet-Mac re-measure 2026-10-05 on 2.0.10 (CrossfitTracker, 19 languages, 4 devices): iOS 404 s capture, Android phone 415 s, 0 problems, no retries; on 2.11.0 (2026-10-04, loaded Mac) iOS needed shotfleet's retry for 9 of 19 languages and took 826 s of capture, Android phone 475 s | the two are not comparable (different load); the installer fetches 2.11.0 |

## When a new version of a tool appears

1. **Maestro:** `tools/watch-upstream.sh` (about monthly, and before a release) fetches the newest stable release and screens it, together with Apple's size table. By hand:
   `python3 tools/latest-maestro.py`, or `python3 tools/maestro-compat.py <folder>` for a copy you already have. All green means "worth a real run", not "supported".
2. **Python:** add it to the `linux` matrix in `.github/workflows/ci.yml` as soon as `actions/setup-python` has it.
3. **Android SDK / Java / Flutter / Expo:** `shotfleet doctor --fix` in a fresh `SHOTFLEET_HOME` and `ANDROID_HOME` fetches the current Android
   tools; `init` in a freshly built sample project shows whether the build still lands where `detect_project` looks.
4. **Promoting a Maestro version** to "tested" is a code change in several places, listed in `docs/handoff.md` under item 1.
